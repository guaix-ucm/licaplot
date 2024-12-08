# --------------------
# System wide imports
# -------------------

import os
import logging
from collections import defaultdict
from typing import Tuple, Iterable, Dict, DefaultDict

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table

import lica.photodiode
from lica.photodiode import COL, BENCH

# ------------------------
# Own modules and packages
# ------------------------

from .. import TBCOL, PROCOL, PROMETA, TWCOL


DiodeDict = Dict[str, Table]
DeviceDict = DefaultDict[str, Table]

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)


def equivalent_ecsv(path: str) -> str:
    """Keeps the same name and directory but changes extesion to ECSV"""
    output_path, _ = os.path.splitext(path)
    return output_path + ".ecsv"


def name_from_file(path: str) -> str:
    """Keeps the same name and directory but changes extesion to ECSV"""
    path = os.path.basename(path)
    path, _ = os.path.splitext(path)
    return path


def read_tess_csv(path: str, delimiter=";", data_start=1) -> Table:
    """Load CSV files produced by textual-spectess"""
    table = astropy.io.ascii.read(
        path,
        delimiter=delimiter,
        data_start=data_start,
        names=(TWCOL.TIME, TWCOL.SEQ, COL.WAVE, TWCOL.FREQ, TWCOL.FILT),
        converters={
            TWCOL.TIME: str,
            TWCOL.SEQ: np.int32,
            COL.WAVE: np.float64,
            TWCOL.FREQ: np.float64,
            TWCOL.FILT: str,
        },
    )
    table[COL.WAVE] = table[COL.WAVE] * u.nm
    table[TWCOL.FREQ] = table[TWCOL.FREQ] * u.Hz
    return table


def read_scan_csv(path: str, delimiter="\t", data_start=0) -> Table:
    """Load CSV files produced by LICA Scan.exe (QEdata.txt files)"""
    table = astropy.io.ascii.read(
        path,
        delimiter=delimiter,
        data_start=data_start,
        names=(TBCOL.INDEX, COL.WAVE, TBCOL.CURRENT),
        converters={TBCOL.INDEX: np.float64, COL.WAVE: np.float64, TBCOL.CURRENT: np.float64},
    )
    table[TBCOL.INDEX] = table[TBCOL.INDEX].astype(np.int32)
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[TBCOL.CURRENT] = table[TBCOL.CURRENT] * u.A
    return table


def read_manual_csv(path: str, delimiter=";", data_start=1) -> Table:
    """Load CSV files produced by LICA Scan.exe (QEdata.txt files)"""
    table = astropy.io.ascii.read(
        path,
        delimiter=delimiter,
        data_start=data_start,
        names=(COL.WAVE, TBCOL.CURRENT, TBCOL.READ_NOISE),
        converters={COL.WAVE: np.float64, TBCOL.CURRENT: np.float64, TBCOL.READ_NOISE: np.float64},
    )
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[TBCOL.CURRENT] = table[TBCOL.CURRENT] * u.A
    table[TBCOL.READ_NOISE] = table[TBCOL.READ_NOISE] * u.A
    return table


def photodiode_table(
    path: str, tag: str, model: str, wave_low: int, wave_high: int, manual: bool
) -> Table:
    """Converts CSV file from photodiode into ECSV file"""

    table = read_manual_csv(path) if manual else read_scan_csv(path)
    resolution = np.ediff1d(table[COL.WAVE])
    assert all([r == resolution[0] for r in resolution])
    if not (wave_low == BENCH.WAVE_START and wave_high == BENCH.WAVE_END):
        history = f"Trimmed to [{wave_low:04d}-{wave_high:04d}] nm wavelength range"
    else:
        history = None
    name = name_from_file(path)
    table.meta = {
        "label": model,  # label used for display purposes
        "Processing": {
            "type": PROMETA.PHOTOD.value,
            "model": model,
            "tag": tag,
            "name": name,
            "resolution": resolution[0],
        },
        "History": [],
    }
    if history:
        log.info("Trinming %s to [%d-%d] nm", name, wave_low, wave_high)
        table.meta["History"].append(history)
        table.meta["Processing"]["wave_low"] = wave_low
        table.meta["Processing"]["wave_high"] = wave_high
    if not manual:
        table.remove_column(TBCOL.INDEX)
    table = table[(table[COL.WAVE] >= wave_low) & (table[COL.WAVE] <= wave_high)]
    log.info("Processing metadata is added: %s", table.meta)
    return table


def photodiode_ecsv(
    path: str, tag: str, model: str, wave_low: int, wave_high: int, manual=False
) -> None:
    table = photodiode_table(path, tag, model, wave_low, wave_high, manual)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy photodiode table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


def filter_table(path: str, tag: str, label: str) -> Table:
    table = read_scan_csv(path)
    resolution = np.ediff1d(table[COL.WAVE])
    table.meta = {
        "label": label,  # label used for display purposes
        "Processing": {
            "type": PROMETA.FILTER.value,
            "tag": tag,
            "name": name_from_file(path),
            "resolution": resolution[0],
        },
        "History": [],
    }
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    return table


def filter_ecsv(path: str, tag: str, label: str) -> None:
    table = filter_table(path, tag, label)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy device table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


def tessw_table(path: str, tag: str, label: str) -> Table:
    raw_table = read_tess_csv(path)
    raw_table.remove_column(TWCOL.TIME)
    raw_table.remove_column(TWCOL.SEQ)
    raw_table.remove_column(TWCOL.FILT)
    table = raw_table.group_by(COL.WAVE).groups.aggregate(np.mean)
    resolution = np.ediff1d(table[COL.WAVE])
    table.meta = {
        "label": label,  # label used for display purposes
        "Processing": {
            "type": PROMETA.SENSOR.value,
            "tag": tag,
            "name": name_from_file(path),
            "resolution": resolution[0],
        },
        "History": [
            f"Dropped columns {TWCOL.TIME}, {TWCOL.SEQ} and {TWCOL.FILT}",
            f"Averaged readings grouping by {COL.WAVE}",
        ],
    }
    log.info("Processing metadata is added: %s", table.meta)
    return table


def tessw_ecsv(path: str, tag: str, label: str) -> None:
    table = tessw_table(path, tag, label)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy device table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


# ====================
# HIGH LEVEL PROCESSES
# ====================


def classify(dir_iterable: Iterable, device_name: str = None) -> Tuple[DiodeDict, DeviceDict]:
    """Classifies ECSV files in two dictionaries, one with Photodiode readings and one with the rest"""
    photodiode_dict = dict()
    other_dict = defaultdict(list)
    for path in dir_iterable:
        table = astropy.io.ascii.read(path, format="ecsv")
        key = table.meta["Processing"]["tag"]
        name = table.meta["Processing"]["name"]
        if table.meta["Processing"]["type"] == PROMETA.PHOTOD:
            if photodiode_dict.get(key):
                msg = (
                    f'Another photodiode table has the same tag: {table.meta["Processing"]["name"]}',
                )
                log.critical(msg)
                raise RuntimeError(msg)
            else:
                photodiode_dict[key] = table
        elif device_name is None or (device_name is not None and name == device_name):
            other_dict[key].append(table)
        else:
            log.info("Ignoring %s file in the same directory", name)
    for k, tables in other_dict.items():
        for t in tables:
            log.info("Returning %s", t.meta["Processing"]["name"])
    return photodiode_dict, other_dict


def review(photodiode_dict: DiodeDict, filter_dict: DeviceDict) -> None:
    for key, table in photodiode_dict.items():
        name = table.meta["Processing"]["name"]
        model = table.meta["Processing"]["model"]
        diode_resol = table.meta["Processing"]["resolution"]
        filters = filter_dict[key]
        names = [t.meta["Processing"]["name"] for t in filters]
        log.info("[tag=%s] (%s) %s, used by %s", key, model, name, names)
        for t in filters:
            filter_resol = t.meta["Processing"]["resolution"]
            if filter_resol != diode_resol:
                msg = f"Filter resoultion {filter_resol} does not match photodiode readings resolution {diode_resol}"
                log.critical(msg)
                raise RuntimeError(msg)
    photod_tags = set(photodiode_dict.keys())
    filter_tags = set(filter_dict.keys())
    excludeddevice_ecsv = filter_tags - photod_tags
    excluded_photod = photod_tags - filter_tags
    for key in excludeddevice_ecsv:
        names = [t.meta["Processing"]["name"] for t in filter_dict[key]]
        log.warn("%s do not match a photodiode tag", names)
    for key in excluded_photod:
        name = photodiode_dict[key].meta["Processing"]["name"]
        log.warn("%s do not match an input file tag", names)
    log.info("Review step ok.")


def save(device_dict: DeviceDict, dir_path: str) -> None:
    for tag, devices in device_dict.items():
        for dev_table in devices:
            name = dev_table.meta["Processing"]["name"] + ".ecsv"
            out_path = os.path.join(dir_path, name)
            log.info("Updating ECSV file %s", out_path)
            dev_table.write(out_path, delimiter=",", overwrite=True)


def active_process(
    photodiode_dict: DiodeDict, sensor_dict: DeviceDict, sensor_column=TBCOL.CURRENT
) -> DeviceDict:
    """
    Process Device ECSV files in a given directory.
    As the device is optically active (i.e. TSL237) we must correct by the photodiode QE
    """
    for key, photod_table in photodiode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        resolution = photod_table.meta["Processing"]["resolution"]
        qe = lica.photodiode.load(model=model, resolution=int(resolution))[COL.QE]
        for i, sensor_table in enumerate(sensor_dict[key]):
            name = sensor_table.meta["Processing"]["name"]
            processed = sensor_table.meta["Processing"].get("processed")
            if processed:
                log.warn("Skipping %s. Already been processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            wave_low = photod_table.meta["Processing"].get("wave_low")
            wave_high = photod_table.meta["Processing"].get("wave_high")
            rows_photod = len(photod_table)
            rows_sensor = len(sensor_table)
            if wave_low:
                log.info("Trimming %s to [%d-%d] nm", name, wave_low, wave_high)
                sensor_table = sensor_table[
                    (sensor_table[COL.WAVE] >= wave_low) & (sensor_table[COL.WAVE] <= wave_high)
                ]
                sensor_table.meta["History"].append(
                    f"Trimmed to [{wave_low:04d}-{wave_high:04d}] nm wavelength range"
                )
                sensor_dict[key][i] = sensor_table  # Necessary to capture the new table in the dict
            # drop end rows due to different +-1 different length
            rows_photod = len(photod_table)
            rows_sensor = len(sensor_table)
            log.info("ROWS PHOTOD = %d, ROWS SENSOR = %d", rows_photod, rows_sensor)
            if rows_photod > rows_sensor:
                log.warn("Dropping last row of reference photodiode QE array to match length of sensor data")
                assert rows_photod - rows_sensor == 1
                photod_table = photod_table[-1]
                photodiode_dict[key] = photod_table # modifies itself
            else:
                log.warn("Dropping last row of sensor data to match length of reference photodiode QE array")
                assert rows_sensor - rows_photod == 1
                sensor_table = sensor_table[-1]
                sensor_dict[key][i] = sensor_table # modifies itself

            # Now do the math
            spectral_resp = (sensor_table[sensor_column] / photod_table[TBCOL.CURRENT]) * qe
            sensor_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            sensor_table[PROCOL.PHOTOD_QE] = qe
            sensor_table[PROCOL.SPECTRAL] = (
                np.round(spectral_resp, decimals=5) * u.dimensionless_unscaled
            )
            sensor_table.meta["Processing"]["using photodiode"] = model
            sensor_table.meta["Processing"]["processed"] = True
            sensor_table.meta["History"].append(
                "Scaled and QE-weighted readings wrt photodiode readings"
            )
    return sensor_dict


def passive_process(photodiode_dict: DiodeDict, filter_dict: DeviceDict) -> DeviceDict:
    """
    Process Device ECSV files in a given directory.
    As the device is optically passive (i.e. filters) we do not correct by photodiode QE
    """
    for key, photod_table in photodiode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        for i, filter_table in enumerate(filter_dict[key]):
            name = filter_table.meta["Processing"]["name"]
            processed = filter_table.meta["Processing"].get("processed")
            if processed:
                log.warn("Skipping %s. Already been processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            wave_low = photod_table.meta["Processing"].get("wave_low")
            wave_high = photod_table.meta["Processing"].get("wave_high")
            if wave_low:
                log.info("Trinming %s to [%d-%d] nm", name, wave_low, wave_high)
                filter_table = filter_table[
                    (filter_table[COL.WAVE] >= wave_low) & (filter_table[COL.WAVE] <= wave_high)
                ]
                filter_table.meta["History"].append(
                    f"Trimmed to [{wave_low:04d}-{wave_high:04d}] nm wavelength range"
                )
                filter_dict[key][i] = filter_table  # Necessary to capture the new table in the dict
            transmission = filter_table[TBCOL.CURRENT] / photod_table[TBCOL.CURRENT]
            filter_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            filter_table[PROCOL.TRANS] = (
                np.round(transmission, decimals=5) * u.dimensionless_unscaled
            )
            filter_table.meta["Processing"]["using photodiode"] = model
            filter_table.meta["Processing"]["processed"] = True
            filter_table.meta["History"].append("Scaled readings wrt photodiode readings")
    return filter_dict
