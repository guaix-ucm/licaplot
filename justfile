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
publish pkg="licatools": build
    twine upload -r pypi dist/*
    uv run --no-project --with {{pkg}} --refresh-package {{pkg}} \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Publish to Test PyPi server
test-publish pkg="licatools": build
    twine upload --verbose -r testpypi dist/*
    uv run --no-project  --with {{pkg}} --refresh-package {{pkg}} \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Uploads tags to public repo
tags:
    git push --tags origin main

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
lica-rel:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv remove lica
    echo "Adding release version of LICA library";
    uv add --refresh-package lica lica[lab];
    uv remove rawpy exifread


# Backup .env to storage unit
env-bak drive=def_drive: (check_mnt drive) (env-backup join(drive, project))

# Restore .env from storage unit
env-rst drive=def_drive: (check_mnt drive) (env-restore join(drive, project))

# Launches Jupyter notebook
notebook:
    uv run jupyter notebook

# -----------------
# Database metadata
# -----------------

# This is the current drive Id for the USB stick I am using
usb_drive_uuid := "D12B-14FD"
usb_stick := join("/media", user, usb_drive_uuid)


# Initializes the LICA database
dbase-init:
    uv run lica-db --console schema
    uv run lica-db --console populate

slurp depth="10":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="{{usb_stick}}/LICA"
    uv run lica-db --console --log-file lica-db.log slurp --input-dir ${dir} --depth {{depth}}

# -------------------------------------------
# Anotate metadata for the different projects
# -------------------------------------------

# generated metadata file for NDF filters
meta-ndf:
    uv run lica-meta --console generate -i data/ndfilters/ndf0.5 -gp *.txt
    uv run lica-meta --console generate -i data/ndfilters/ndf1.0 -gp *.txt

# generated metadata file for TESSW
meta-tess:
    uv run lica-meta --console generate -i data/tessw -gp *.csv
  
# generated metadata file for Eclipse glasses
meta-eclipse:
    uv run lica-meta --console generate -i data/eclipse -gp *.csv

# generated metadata file forEysdon RGB filter set
meta-eysdon:
    uv run lica-meta --console generate -i data/filters/Eysdon_RGB -gp *.txt 

# generated metadata file forEysdon RGB filter set
meta-IR_cut:
    uv run lica-meta --console generate -i data/filters/IR_cut -gp *.txt 

# generated metadata file forEysdon RGB filter set
meta-omega:
    uv run lica-meta --console generate -i data/filters/IR_cut -gp *.txt 

meta:
    #!/usr/bin/env bash
    set -exuo pipefail
    for item in ndf tess eclipse eysdon IR_cut omega
    do
        just meta-${item}
    done

# -----------
# PSU project
# -----------

psu-ecsv:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/psu"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41
    do
        uv run lica-filters --console classif photod -l $i -t "Photodiode sample $i" -g $i -p ${dir}/${i}.txt -m PIN-10D
    done

# -------------------------
# Hamamatsu utility testing
# -------------------------

hama1:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/hamamatsu"
    uv run lica-hama --console --trace stage1 --plot -i ${dir}/S2281-01-Responsivity-NPL.csv

hama2:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/hamamatsu"
    uv run lica-hama --console --trace stage2 --plot --save -i ${dir}/S2281-01-Responsivity-NPL.ecsv -d ${dir}/S2281-04-Responsivity-Datasheet.csv -x 16 -y 0.009

hama3:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/hamamatsu"
    uv run lica-hama --console --trace stage3 --plot -i ${dir}/S2281-01-Responsivity-NPL+Datasheet.ecsv -m cubic -r 1 --revision 2024-12 -x 16 -y 0.009

# Plot lica stored resource: Hamamatsu calibration curve
hama-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run lica-photod --console plot -m S2281-01

# -------------------
# OSI utility testing
# -------------------

# OSI Pĥotodiode calibration by scanned datasheet
osi-sheet:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run lica-osi --console datasheet -i data/osi/PIN-10D-Responsivity-Datasheet.csv -m cubic -r 1 --plot --save --revision 2024-12

# OSI Pĥotodiode calibration by cross calibration
osi-cross:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run lica-osi --console cross --osi data/osi/QEdata_PIN-10D.txt --hama data/osi/QEdata_S2201-01.txt --plot --save --revision 2024-12
# OSI Pĥotodiode: comparison of methods
osi-cmp:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run lica-osi --console compare -c data/osi/OSI\ PIN-10D+Cross-Calibrated@1nm.ecsv -d data/osi/OSI\ PIN-10D-Responsivity-Datasheet+Interpolated@1nm.ecsv --plot

# Plot lica stored resource: OSI calibration curve
osi-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run lica-photod --console plot -m PIN-10D

# ---------------------------------------
# Neutral Density filters utility testing
# ---------------------------------------
 

# Calibrates a NDF filter
ndf-reduce tag="0.5" i="0":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/ndfilters/ndf{{tag}}"
    photodiodes=( $(ls -1 ${dir}/??_osi_clear.txt) )
    filters=( $(ls -1 ${dir}/??_osi_nd*.txt) )
    uv run lica-ndf --console --trace calib -n ND-{{tag}} -m PIN-10D -i ${filters[0]} -p ${photodiodes[{{i}}]} -o ${dir} 


# Plot NDF calibration curve
ndf-plot tag="0.5":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/ndfilters/ndf{{tag}}"
    uv run lica-plot --console --trace single table column -t NDF-{{tag}} -ycn 2 -i ${dir}/ND-{{tag}}-Transmittance@1nm.ecsv --changes

# --------------------------
# Eclipse sunglasses testing
# --------------------------

[private]
eclipse-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-filters --console one -l $i -g $i -p ${dir}/${i}_osi_nd0.5.txt -m PIN-10D -i ${dir}/${i}_eg.txt --ndf ND-0.5
    done

[private]
nasa-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-filters --console --trace one -l $i -g $i -p ${dir}/${i}_osi_nd0.5.txt -m PIN-10D -i ${dir}/${i}_eg.txt --ndf ND-0.5
        uv run lica-eclip --console --trace inverse -ycn 5 -i ${dir}/${i}_eg.ecsv --save
    done

# Single linear graphs for all glasses
eclipse-plot-all:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-plot --console --trace single table columns -ycn 5 -t Eclipse Glasses $i -i ${dir}/${i}_eg.ecsv  --lines --changes
    done

# Single linear graphs for all glasses with & without ND correction
eclipse-plot-all-nd:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-plot --console --trace single table columns -ycn 4 5 -l Raw ND-Corr -t Eclipse Glasses $i -i ${dir}/${i}_eg.ecsv --lines --changes
    done

# save NASA style plot of glasses for all glasses
eclipse-plot-all-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 --t 'Transmittance vs Wavelength' -yl '$log_{10}(\frac{1}{Transmittance})$' --lines --marker None -i $file_accum 

# logaritmic style plotting for group 1
eclipse-plot-g1-log:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 02 03 04 06 10
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "
    done
    uv run lica-plot --console --trace single tables column -ycn 5 -t Group 1 -i $file_accum -m None --lines --log-y


# NASA style plotting of glasses for group 1
eclipse-plot-g1-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in  02 03 04 06 10
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 --t Group 1 -yl '$log_{10}(\frac{1}{Transmittance})$' -i $file_accum --lines -m None

# logaritmic style plotting for group 1
eclipse-plot-g2-log:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "
    done
    uv run lica-plot --console --trace single tables column -ycn 5 -t Group 2 -i $file_accum -m None --lines --log-y -sd 300

# NASA style plotting of glasses for group 2
eclipse-plot-g2-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 --t Group 2 -yl '$log_{10}(\frac{1}{Transmittance})$' -i $file_accum -m None --lines


# Save lingle linear plots for all glasses
eclipse-save-plot-all:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-plot --console --trace single table columns -ycn 5 -t Eclipse Glasses $i -i ${dir}/${i}_eg.ecsv -sf ${dir}/${i}_eg.png --lines --changes -sd 300
    done

# Single linear graphs for all glasses with & without ND correction
eclipse-save-plot-all-nd:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        uv run lica-plot --console --trace single table columns -ycn 4 5 -l Raw ND-Corr -t Eclipse Glasses $i -i ${dir}/${i}_eg.ecsv -sf ${dir}/${i}_eg.png --lines --changes -sd 300
    done

# save NASA style plot of glasses for all glasses
eclipse-save-plot-all-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 01 02 03 04 05 06 07 08 09 10 11 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 -t 'Transmittance vs Wavelength' -yl '$log_{10}(\frac{1}{Transmittance})$' --lines -m None -i $file_accum -sf ${dir}/Transmittance_vs_Wavelength_log101_Transmittance.png -sd 300


# save logaritmic style plotting for group 1
eclipse-save-plot-g1-log:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 02 03 04 06 10
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "
    done
    uv run lica-plot --console --trace single tables column -ycn 5 -t Group 1 -m None --lines -i $file_accum -sf ${dir}/group1_eg.png  --log-y -sd 300


# Save NASA style plotting of glasses for group 1
eclipse-save-plot-g1-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in  02 03 04 06 10
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 --t Group 1 -yl '$log_{10}(\frac{1}{Transmittance})$' --lines -m None -i $file_accum -sf ${dir}/inv_log_group_a.png -sd 300

# Save logaritmic style plotting for group 1
eclipse-save-plot-g2-log:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "
    done
    uv run lica-plot --console --trace single tables column -ycn 5 -t Group 2 -i $file_accum -m None --lines --log-y  -sf ${dir}/group2_eg.png -sd 300

# Save NASA style plotting of glasses for group 2
eclipse-save-plot-g2-nasa:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    file_accum=""
    for i in 12 13
    do
        file_accum="${file_accum}${dir}/${i}_eg.ecsv "   
    done
    uv run lica-eclip --console --trace plot -ycn 6 --t Group 2 -yl '$log_{10}(\frac{1}{Transmittance})$' -i $file_accum -sf ${dir}/inv_log_group_b.png --lines -m None


# ------------------------------------
# Neutral Density Filters Transmitance
# ------------------------------------


# ----------------------------------
# Omega Nebular Filter Transmittance
# ----------------------------------

[private]
omega-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Omega_NPB"
    uv run lica-filters --console --trace one -l OMEGA NPB -p ${dir}/QEdata_diode_2nm.txt -m PIN-10D -i ${dir}/QEdata_filter_2nm.txt

# Plot single axes, 3 table, 1 column each
omega-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Omega_NPB"
    uv run lica-plot --console --trace single table column -% -i ${dir}/QEdata_filter_2nm.ecsv -ycn 4 --changes --lines


# --------------
# Eysdon Filters
# --------------

[private]
eysdon-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Eysdon_RGB"
    uv run lica-filters --console --trace classif photod -g X -p ${dir}/photodiode.txt
    uv run lica-filters --console --trace classif filter -g X -i ${dir}/green.txt -l Green
    uv run lica-filters --console --trace classif filter -g X -i ${dir}/red.txt -l Red
    uv run lica-filters --console --trace classif filter -g X -i ${dir}/blue.txt -l Blue
    uv run lica-filters --console --trace process -d ${dir} --save


# Plot Eysdon Filter set
eysdon-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Eysdon_RGB"
    uv run lica-plot --console --trace single tables column -% -i ${dir}/blue.ecsv ${dir}/red.ecsv ${dir}/green.ecsv -ycn 4 --changes --lines


# --------------------------------
# TESS W spectral response utility
# --------------------------------

# TESS-W sensor spectral response reduction
tessw-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/tessw"
    uv run lica-tessw --console --trace classif photod -g A -p ${dir}/stars1277-photodiode.csv
    uv run lica-tessw --console --trace classif sensor -g A -i ${dir}/stars1277-frequencies.csv -l TSL237
    uv run lica-tessw --console --trace classif photod -g B -p ${dir}/stars6502-photodiode.csv 
    uv run lica-tessw --console --trace classif sensor -g B -i ${dir}/stars6502-frequencies.csv -l OTHER
    uv run lica-tessw --console --trace process  -d ${dir} --save

tessw-plot-raw:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/tessw
    uv run lica-plot --console single tables column -i ${dir}/stars1277-frequencies.ecsv  ${dir}/stars6502-frequencies.ecsv  -ycn 2  --changes --lines

tessw-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/tessw
    uv run lica-plot --console single tables column -i ${dir}/stars1277-frequencies.ecsv  ${dir}/stars6502-frequencies.ecsv  -ycn 5  --changes --lines


# TESS-W IV/IR-cut filter data reduction
sp750-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/IR_cut"
    uv run lica-filters --console --trace one -l SP750 -p ${dir}/SP750_Photodiode_QEdata.txt -m PIN-10D -i ${dir}/SP750_QEdata.txt

sp750-plot:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/IR_cut"
    uv run lica-plot --console --trace single tables column -% -i ${dir}/SP750_QEdata.ecsv -ycn 4 --changes --lines

# =============================
# Generic data reduction recipe
# =============================

# reduce LICA data [tessw|eclipse|nasa|eysdon|omega|sp750|ndf|all]
reduce what:
    #!/usr/bin/env bash
    set -exuo pipefail
    just {{what}}-reduce

# reduce LICA data [tessw|eclipse|nasa|eysdon|omega|sp750|ndf|all]
plot what:
    #!/usr/bin/env bash
    set -exuo pipefail
    just {{what}}-plot
    
[private]
all-reduce:
    #!/usr/bin/env bash
    set -exuo pipefail
    for item in eclipse eysdon omega sp750 ndf tessw
    do
        just ${item}-reduce
    done

# -----------------------------
# Plotting utility test drivers
# -----------------------------

# Plot single axes, 1 table and 1 column
plot-s-t-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Omega_NPB"
    lica-plot --console --trace single table column -% -t Omega Nebula Band Pass Filter -i ${dir}/QEdata_filter_2nm.ecsv -ycn 4 --changes --lines {{args}}

# Plot single axes, 1 table and 2 columns
plot-s-t-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/eclipse"
    lica-plot --console --trace single table columns -% -i ${dir}/02_eg.ecsv -xcn 1 -ycn 4 5 --changes --lines {{args}}

# Plot single axes, 3 tables, 1 column each
plot-s-tt-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="data/filters/Eysdon_RGB"
    lica-plot --console --trace single tables column -% -i ${dir}/blue.ecsv ${dir}/red.ecsv ${dir}/green.ecsv -ycn 4 --changes --lines {{args}}

# Plot single Axes, 3 table per axes, 2 column per table
plot-s-tt-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace single tables columns -% -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -ycn 4 5 --changes --lines {{args}}

# Plot single Axes, 1 table per axes, 1 column per table
plot-s-tt-cx args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace single tables mixed -% -i ${dir}/03_eg.ecsv ${dir}/04_eg.ecsv -ycn 2 2 --changes --lines {{args}}


# Plot multiple Axes, one table per axes, one column per table
plot-m-tt-c args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace multi tables column -% -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -ycn 5 --changes --lines {{args}}


# Plot multiple Axes, one table per axes, several column per table
plot-m-tt-cc args="":
    #!/usr/bin/env bash
    set -exuo pipefail
    dir=data/eclipse
    lica-plot --console --trace multi tables columns -% -i ${dir}/01_eg.ecsv ${dir}/02_eg.ecsv ${dir}/03_eg.ecsv -ycn 4 5 --changes --lines {{args}}

# run unut test on [table|element]
test what:
    #!/usr/bin/env bash
    set -exuo pipefail
    uv run python -m unittest -v test.{{what}}

# --------------------
# Timestamp manamement
# --------------------

scan:
    #!/usr/bin/env bash
    set -exuo pipefail
    dir="/media/rafa/D12B-14FD/Gafas Eclipse Solar/20250219"
    uv run lica-tstamp --console --trace scan --input-dir "$dir" --output-file timestamps.txt

# ===================
# OTHER PRIVATE STUFF
# ===================

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
    cp lica.db {{ bak_dir }}
  
[private]
env-restore bak_dir:
    #!/usr/bin/env bash
    set -euxo pipefail
    if [[ ! -f  {{ bak_dir }}/.env ]]; then
        echo "Can't restore: {{ bak_dir }}/.env doesn't exists"
        exit 1 
    fi
    cp {{ bak_dir }}/.env {{ local_env }}
    cp {{ bak_dir }}/lica.db .
