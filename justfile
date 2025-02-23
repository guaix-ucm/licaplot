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

hama1:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-hama --console --trace stage1 --plot -i data/hamamatsu/S2281-01-Responsivity-NPL.csv

hama2:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-hama --console --trace stage2 --plot --save -i data/hamamatsu/S2281-01-Responsivity-NPL.ecsv -d data/hamamatsu/S2281-04-Responsivity-Datasheet.csv -x 16 -y 0.009

hama3:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-hama --console --trace stage3 --plot -i data/hamamatsu/S2281-01-Responsivity-NPL+Datasheet.ecsv -m cubic -r 1 --revision 2024-12

# OSI Pĥotodiode calibration by scanned datasheet
osi-sheet:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-osi --console datasheet -i data/osi/PIN-10D-Responsivity-Datasheet.csv -m cubic -r 1 --plot --save --revision 2024-12

# OSI Pĥotodiode calibration by cross calibration
osi-cross:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-osi --console cross --osi data/osi/QEdata_PIN-10D.txt --hama data/osi/QEdata_S2201-01.txt --plot --save --revision 2024-12
# OSI Pĥotodiode: comparison of methods
osi-cmp:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-osi --console compare -c data/osi/OSI\ PIN-10D+Cross-Calibrated@1nm.ecsv -d data/osi/OSI\ PIN-10D-Responsivity-Datasheet+Interpolated@1nm.ecsv --plot

# Calibrates a NDF filter
ndf-calib:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-ndf --console --trace calib -n ND-0.5 -m PIN-10D -i data/ndfilters/osi_nd0.5.txt -p data/ndfilters/osi_clear1.txt -o data/ndfilters 


# Plot NDF calibration curve
ndf-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-ndf --console --trace plot -n ND-0.5 -i data/ndfilters/ND-0.5-Transmission@5nm.ecsv



plotsin dir="data/filters/Eysdon_RGB": (anew dir)
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console --trace one -l Green -p {{dir}}/photodiode.txt -m PIN-10D -i {{dir}}/green.txt
    lica-plot --console --trace single table column -i {{dir}}/green.ecsv --title Green filter -yc 4 --lines --changes


plotmul dir="data/filters/Eysdon_RGB": (anew dir)
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console single tables column -i {{dir}}/blue.ecsv {{dir}}/red.ecsv {{dir}}/green.ecsv -yc 4  --changes --lines

# Plot CLI test driver
test_s_t_c dir="data/filters/Eysdon_RGB" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    rm {{dir}}/*.ecsv
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console --trace single table column  --title Filtro Verde -i {{dir}}/green.ecsv -xc 1 -yc 4 --changes --lines {{args}}

test_s_tt_c dir="data/filters/Eysdon_RGB" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    rm {{dir}}/*.ecsv
    lica-filters --console classif photod --tag X -p {{dir}}/photodiode.txt
    lica-filters --console classif filter --tag X -i {{dir}}/green.txt -l Green
    lica-filters --console classif filter --tag X -i {{dir}}/red.txt -l Red
    lica-filters --console classif filter --tag X -i {{dir}}/blue.txt -l Blue
    lica-filters --console process -d {{dir}} --save
    lica-plot --console --trace single tables column -i {{dir}}/blue.ecsv {{dir}}/red.ecsv {{dir}}/green.ecsv  -xc 1 -yc 4 --changes --lines {{args}}

t_dir := "data/sunglasses"
test_s_t_cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-plot --console --trace single table columns -% -i {{t_dir}}/02_sg.ecsv -xc 1 -yc 4 5 --changes --lines {{args}}


test_m_tt_cc dir="data/sunglasses" args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-plot --console --trace multi tables columns -i {{dir}}/01_sg.ecsv {{dir}}/02_sg.ecsv {{dir}}/03_sg.ecsv -xc 1 -yc 4 5 --changes --lines {{args}}

# Reduce all sunglasses data
sunglasses dir="data/sunglasses":
    #!/usr/bin/env bash
    set -exuo pipefail
    for i in 01 02 03 04 05 06 07 08 09 10
    do
        lica-filters --console one -l $i -t $i -p {{dir}}/${i}_osi_nd0.5.txt -m PIN-10D -i {{dir}}/${i}_sg.txt --ndf ND-0.5
    done

[private]
anew dir:
    #!/usr/bin/env bash
    set -exuo pipefail
    rm {{dir}}/*.ecsv || exit 0

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
