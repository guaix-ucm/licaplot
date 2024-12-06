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
* `licaplot-filters`. Process filter data from LICA optical bench

# Usage examples

Plots and exports to ESCV the original manufacturer's TSL237 spectral response from the datasheet. The input example CSV has been previosly digitized from the original PDF by a digitizer tool. The input file is resampled (cubic interpolation) to a 5nm step resolution and triimmed to the LICA testbench optical range of [350nm - 1050nm]. The title and label is used both in the plot graphics and also stored as ECSV metadata. The label can be used as a graphics label when overlapping plots.

## Reducing Filters data

Two Use Cases:

### Simple case

In the simple case, we hace one filter CSV and one clear photodiode CSV. Setting the wavelength limits is optional.
Setting the photodiode model is optional unless you are using the Hamamatsu S2281-01.

```bash
licaplot-filters --console one -t Z -l Green -p data/filters/photodiode.txt -m PIN-10D -i data/filters/green.txt -wl 350 -wh 800
```

* Several filters being processes by different photometer readings

In this case two UV/IR cut filters were measured with the clear photodiode readings between the two, thus sharing the same clear photodiode file. The photodiode model used was the OSI PIN-10D.

First we tag all the clear photodiode readings. The tag is a string (i.e. `X`) we use to match which filters are being paired with this clear photodidoe reading.

If we need to trim the bandwith of the whole set (photodiode + associated filter readings) *this is the time to do it*. The bandwith trimming will be carried over from the photodiode to the associated filters.

```bash
licaplot-filters --console classif photod --tag X -p data/filters/photodiode.txt
```

The output of this command is an ECSV file with the same information plus metadata needed for further processing.

Then we tag both filter files with the same tag (`X` in this case), as they share the same photodiode file.

```bash
licaplot-filters --console classif filter --tag X -i data/filters/green.txt -l Green
licaplot-filters --console classif filter --tag X -i data/filters/red.txt -l Red
licaplot-filters --console classif filter --tag X -i data/filters/blue.txt -l Blue
```

The output of these commands are the ECSV files with the same data but additional metadata for further processing
We review the process:

```bash
licaplot-filters --console classif review -d data/filters/
```

The we do the processing. The optional flag allows to control the overriting of the input ECSV files with more columns and metadata.

```bash
licaplot-filters --console process -d data/filters --save
```

After this step both filter ECSV files contains additional columns with the clear photodiode readings, the photodiode model QE and the final transmission curve as the last column.

We can plot our results using `licaplot-csv`. The column to be plotted is the fourth column (transmission) against the wavelenght column which happens to be the first.

```bash
licaplot-csv --console multi -i data/filters/blue.ecsv data/filters/red.ecsv data/filters/green.ecsv --overlap -wc 1 -yc 4  --filters --lines
```


## Generating LICA photodiodes reference data

### Hamamatsu S2281-01 diode

#### Stage 1

Convert NPL CSV data into a ECSV file with added metadata and plot it.

```bash
licaplot-hama --console stage1 --plot -i data/hamamatsu/S2281-01-Responsivity-NPL.csv
```
It produces a file with the same name as the input file with `.ecsv` extension

#### Stage 2

Plot and merge NPL data with S2281-04 (yes, -04!) datasheet points.

With no alignment

```bash
licaplot-hama --console stage2 --plot --save -i data/hamamatsu/S2281-01-Responsivity-NPL.ecsv -d data/hamamatsu/S2281-04-Responsivity-Datasheet.csv
```

With good alignment (x = 16, y = 0.009)

```bash
licaplot-hama --console stage2 --plot --save -i data/hamamatsu/S2281-01-Responsivity-NPL.ecsv -d data/hamamatsu/S2281-04-Responsivity-Datasheet.csv -x 16 -y 0.009
```
It produces a file whose name is the same as the input file plus "+Datasheet.ecsv" appended, in the same folder.
(i.e `S2281-01-Responsivity-NPL+Datasheet.ecsv`)

#### Stage 3

Interpolates input ECSV file to a 1 nm resolution with cubic interplolator.

```bash
licaplot-hama --console stage3 --plot -i data/hamamatsu/S2281-01-Responsivity-NPL+Datasheet.ecsv -m cubic -r 1
```

#### Pipeline

The complete pipeline in one command

```bash
licaplot-hama --console pipeline --plot -i data/hamamatsu/S2281-01-Responsivity-NPL.csv -d data/hamamatsu/S2281-04-Responsivity-Datasheet.csv -x 16 -y 0.009 -m cubic -r 1
```
### OSI PIN-10D photodiode

By using the scanned datasheet
```bash
licaplot-osi --console datasheet -i csv/calibration/osi/PIN-10D-Responsivity-Datasheet.csv -m cubic -r 1 --plot --save
```

By using a cross calibration with the Hamamatsu photodiode. The Hamamtsu ECSV file is the one obtained in the section above. It does nota appear in the command line as it is embedded in a Python package that automatically retrieves it.

```bash
licaplot-osi --console cross --osi data/osi/QEdata_PIN-10D.txt --hama data/osi/QEdata_S2201-01.txt --plot --save
```

Compare both methods
```bash
licaplot-osi --console compare -c data/osi/OSI\ PIN-10D+Cross-Calibrated@1nm.ecsv -d data/osi/OSI\ PIN-10D-Responsivity-Datasheet+Interpolated@1nm.ecsv --plot
```
## Plot the packaged ECSV file

```bash
licaplot-photod --console plot -m S2281-01
licaplot-photod --console plot -m PIN-10D
```
