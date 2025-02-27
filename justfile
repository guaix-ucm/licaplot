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
    lica-plot --console --trace single table column -t NDF-0.5 -yc 2 -i data/ndfilters/ND-0.5-Transmission@5nm.ecsv --changes

# Plot lica stored resource: Hamamatsu calibration curve
hama-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-photod --console plot -m S2281-01

# Plot lica stored resource: OSI calibration curve
osi-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    lica-photod --console plot -m PIN-10D

eclipse-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10
    do
        lica-plot --console --trace single table columns -yc 4 5 -t Eclipse Glasses $i -i ${dir}/${i}_eg.ecsv -sf ${dir}/${i}_eg.png --changes --lines 
    done

# reduce LICA data [tessw|eclipse|eysdon|omega|sp750|ndf]
reduce what:
    #!/usr/bin/env bash
    set -exuo pipefail
    just {{what}}-reduce
    

[private]
tessw-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/tessw"
    lica-tessw --console --trace classif photod -p ${dir}/stars1277-photodiode.csv --tag A
    lica-tessw --console classif sensor -i ${dir}/stars1277-frequencies.csv -l TSL237 --tag A
    lica-tessw --console classif photod -p ${dir}/stars6502-photodiode.csv --tag B
    lica-tessw --console classif sensor -i ${dir}/stars6502-frequencies.csv -l OTHER --tag B
    lica-tessw --console process  -d ${dir} --save

[private]
eysdon-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Eysdon_RGB"
    lica-filters --console --trace  classif photod --tag X -p ${dir}/photodiode.txt
    lica-filters --console --trace classif filter --tag X -i ${dir}/green.txt -l Green
    lica-filters --console --trace classif filter --tag X -i ${dir}/red.txt -l Red
    lica-filters --console --trace classif filter --tag X -i ${dir}/blue.txt -l Blue
    lica-filters --console --trace process -d ${dir} --save


[private]
omega-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Omega_NPB"
    lica-filters --console --trace one -l OMEGA NPB -p ${dir}/QEdata_diode_2nm.txt -m PIN-10D -i ${dir}/QEdata_filter_2nm.txt

[private]
sp750-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/IR_cut"
    lica-filters --console --trace one -l SP750 -p ${dir}/SP750_Photodiode_QEdata.txt -m PIN-10D -i ${dir}/SP750_QEdata.txt

[private]
ndf-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/ndfilters/ndf0.5"
    lica-filters --console --trace one -l ND 0.5 -p ${dir}/osi_clear1.txt -m PIN-10D -i ${dir}/osi_nd0.5.txt


[private]
eclipse-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10
    do
        lica-filters --console one -l $i -t $i -p ${dir}/${i}_osi_nd0.5.txt -m PIN-10D -i ${dir}/${i}_eg.txt --ndf ND-0.5
    done

tessw-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/tessw
    lica-plot --console single tables column -i ${dir}/stars1277-frequencies.ecsv  ${dir}/stars6502-frequencies.ecsv  -yc 2  --changes --lines

# Plot single axes, table and column
plot-s-t-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Omega_NPB"
    lica-plot --console --trace single table column  -t Omega Nebula Band Pass Filter -i ${dir}/QEdata_filter_2nm.ecsv -yc 4 --changes --lines {{args}}

# Plot single axes, table and 2 columns
plot-s-t-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    lica-plot --console --trace single table columns -% -i ${dir}/02_eg.ecsv -xc 1 -yc 4 5 --changes --lines {{args}}

# Plot single axes, 3 table, 1 column each
plot-s-tt-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Eysdon_RGB"
    lica-plot --console --trace single tables column -i ${dir}/blue.ecsv ${dir}/red.ecsv ${dir}/green.ecsv -yc 4 --changes --lines {{args}}


# Plot multiple Axes, one table per axes, several column per table
plot-s-tt-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace single tables columns -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -yc 4 5 --changes --lines {{args}}


# Plot multiple Axes, one table only, one column per axes
plot-m-t-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace multi table columns -i ${dir}/01_eg.ecsv -yc 4 5 --changes --lines {{args}}


# Plot multiple Axes, one table per axes, one column per table
plot-m-tt-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace multi tables column -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -yc 5 --changes --lines {{args}}


# Plot multiple Axes, one table per axes, several column per table
plot-m-tt-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace multi tables columns -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -yc 4 5 --changes --lines {{args}}

# run unut test on [table|element]
test what:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run python -m unittest -v test.{{what}}
   

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
