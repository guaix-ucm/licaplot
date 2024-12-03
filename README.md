# rawplot
 
 Collection of plotting commands to analyze sensors and filters using the LICA Optical Test Bench.

 This is a simpler counterpart for sensors of [rawplot](https://guaix.ucm.es/rawplot).

 # Installation

```bash
pip install licaplot
```

# Available utilities
* `licaplot-csv`. Plot CSV files and optionally converts CSV into ECSV files
* `licaplot-photod`. Plot and export LICA photodiodes spectral response curves.
* `licaplot-hama`. Build LICA's Hamamtsu S2281-04 photodiode spectral response curve in ECSV format to be used for other calibration purposes elsewhere.
* `licaplot-osi` = Build LICA's OSI PIN-10D photodiode spectral response curve un ECSV format to be used for other calibration purposes elsewhere.
* `licaplot-filters`

# Usage examples

Plots and exports to ESCV the original manufacturer's TSL237 spectral response from the datasheet. The input example CSV has been previosly digitized from the original PDF by a digitizer tool. The input file is resampled (cubic interpolation) to a 5nm step resolution and triimmed to the LICA testbench optical range of [350nm - 1050nm]. The title and label is used both in the plot graphics and also stored as ECSV metadata. The label can be used as a graphics label when overlapping plots.

```bash 
licaplot-csv --console single -i examples/TSL237_responsivity_manufacturer.csv --title TSL237 Responsivity from manufacturer --label TSL237 -r 5  --lica --export TSL237_manuf.ecsv
```

Ditto for another light sensor.

```bash 
licaplot-csv --console single -i examples/S9705-01DT_responsivity_manufacturer.csv --title S9705-01DT Responsivity from manufacturer --label S9705-01DT -r 5  --lica --export S9705-01DT_manuf.ecsv
```

## Generating LICA photodiodes reference data
```bash
licaplot-hama --console pipeline -p -t S2281-01 -n csv/calibration/hamamatsu/Hama-S2281-01-Responsivity-NPL.csv -i csv/calibration/hamamatsu/Hama-S2281-04-Responsivity-Datasheet.csv -x 16 -y 0.009 -m cubic -r 1
```

## Plot the packaged ECSV file

```bash
licaplot-photod --console plot -m S2281-01
```
