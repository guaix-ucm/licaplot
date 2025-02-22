# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment


drive_uuid := "77688511-78c5-4de3-9108-b631ff823ef4"
user :=  file_stem(home_dir())
def_drive := join("/media", user, drive_uuid, "env")
project := file_stem(justfile_dir())
local_env := join(justfile_dir(), ".env")


# list all recipes
default:
    just --list

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff

# Add conveniente development dependencies
dev:
    uv add --dev pytest

# Build the package
build:
    rm -fr dist/*
    uv build

# Publish the package to PyPi
publish pkg="licaplot": build
    twine upload -r pypi dist/*
    uv run --no-project --with {{pkg}} --refresh-package {{pkg}} \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Publish to Test PyPi server
test-publish pkg="licaplot": build
    twine upload --verbose -r testpypi dist/*
    uv run --no-project  --with {{pkg}} --refresh-package {{pkg}} \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Adds lica source library as dependency. 'version' may be a tag or branch
lica-dev version="main":
    #!/usr/bin/env bash
    set -exuo pipefail
    echo "Removing previous LICA dependency"
    uv add rawpy exifread
    uv remove lica
    if [[ "{{ version }}" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
        echo "Adding LICA source library --tag {{ version }}"; 
        uv add git+https://github.com/guaix-ucm/lica --tag {{ version }};
    else
        echo "Adding LICA source library --branch {{ version }}";
        uv add git+https://github.com/guaix-ucm/lica --branch {{ version }};
    fi

# Adds lica release library as dependency with a given version
lica-rel version="":
    #!/usr/bin/env bash
    set -exuo pipefail
    uv remove lica
    echo "Adding LICA library {{ version }}";
    uv add --refresh-package lica lica[lab] {{ version }};
    uv remove rawpy exifread


# Backup .env to storage unit
env-bak drive=def_drive: (check_mnt drive) (env-backup join(drive, project))

# Restore .env from storage unit
env-rst drive=def_drive: (check_mnt drive) (env-restore join(drive, project))

plotsin dir="data/filters/Eysdon_RGB": (anew dir)
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console one -l Green -p {{dir}}/photodiode.txt -m PIN-10D -i {{dir}}/green.txt
    lica-plot --console single -i {{dir}}/green.ecsv --title Green filter -yc 4 --label G --lines --filters


plotmul dir="data/filters/Eysdon_RGB": (anew dir)
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console multi -i {{dir}}/blue.ecsv {{dir}}/red.ecsv {{dir}}/green.ecsv --overlap -wc 1 -yc 4  --filters --lines

# Plot CLI test driver
test_s_t_c dir="data/filters/Eysdon_RGB" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console --trace single table column  --title Filtro Verde -i {{dir}}/green.ecsv -xc 1 -yc 4 --changes --lines {{args}}

test_s_t_cc dir="data/filters/Eysdon_RGB" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console --trace single table columns   -i {{dir}}/blue.ecsv -xc 1 -yc 2 3 --changes --lines {{args}}

test_s_tt_c dir="data/filters/Eysdon_RGB" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console --trace single tables column -i {{dir}}/blue.ecsv {{dir}}/red.ecsv {{dir}}/green.ecsv  -xc 1 -yc 4 --changes --lines {{args}}


[private]
anew dir:
    #!/usr/bin/env bash
    set -exuo pipefail
    rm {{dir}}/*.ecsv

[private]
check_mnt mnt:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ ! -d  {{ mnt }} ]]; then
        echo "Drive not mounted: {{ mnt }}"
        exit 1 
    fi

[private]
env-backup bak_dir:
    #!/usr/bin/env bash
    set -exuo pipefail
    if [[ ! -f  {{ local_env }} ]]; then
        echo "Can't backup: {{ local_env }} doesn't exists"
        exit 1 
    fi
    mkdir -p {{ bak_dir }}
    cp {{ local_env }} {{ bak_dir }}
    mkdir -p {{ bak_dir }}/csv
    cp -r csv {{ bak_dir }}
  
[private]
env-restore bak_dir:
    #!/usr/bin/env bash
    set -euxo pipefail
    if [[ ! -f  {{ bak_dir }}/.env ]]; then
        echo "Can't restore: {{ bak_dir }}/.env doesn't exists"
        exit 1 
    fi
    cp {{ bak_dir }}/.env {{ local_env }}
    mkdir -p csv
    cp -r {{ bak_dir }}/csv .
