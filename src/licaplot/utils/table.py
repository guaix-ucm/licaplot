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
from lica.photodiode import COL

# ------------------------
# Own modules and packages
# ------------------------

from .. import TBCOL, PROCOL, PROMETA


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

def scan_csv_to_table(path: str) -> Table:
    """Load CSV files produced by LICA Scan.exe (QEdata.txt files)"""
    table = astropy.io.ascii.read(
        path,
        delimiter="\t",
        data_start=0,
        names=(TBCOL.INDEX, COL.WAVE, TBCOL.CURRENT),
        converters={TBCOL.INDEX: np.float64, COL.WAVE: np.float64, TBCOL.CURRENT: np.float64},
    )
    table[TBCOL.INDEX] = table[TBCOL.INDEX].astype(np.int32)
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[TBCOL.CURRENT] = table[TBCOL.CURRENT] * u.A
    return table


def photodiode_table(path: str, tag: str, model: str) -> Table:
    """Converts CSV file from photodiode into ECSV file"""
    table = scan_csv_to_table(path)
    resolution = np.ediff1d(table[COL.WAVE])
    assert all([r == resolution[0] for r in resolution])
    table.meta = {
        "label": model,  # label used for display purposes
        "Processing": {
            "type": PROMETA.PHOTOD.value,
            "model": model,
            "tag": tag,
            "name": name_from_file(path),
            "resolution": resolution[0],
        },
    }
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    return table


def photodiode_ecsv(path: str, tag: str, model: str) -> None:
    table = photodiode_table(path, tag, model)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy photodiode table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)

def device_table(path: str, tag: str, label: str) -> Table:
    table = scan_csv_to_table(path)
    resolution = np.ediff1d(table[COL.WAVE])
    table.meta = {
        "label": label,  # label used for display purposes
        "Processing": {
            "type": PROMETA.FILTER.value,
            "tag": tag,
            "name":  name_from_file(path),
            "resolution": resolution[0],
        },
    }
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    return table

def device_ecsv(path: str, tag: str, label: str) -> None:
    table = device_table(path, tag, label)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy device table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


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


def active_process(photodiode_dict: DiodeDict, filter_dict: DeviceDict) -> DeviceDict:
    """
    Process Device ECSV files in a given directory.
    As the device is optically active (i.e. TSL237) we must correct by the photodiode QE
    """
    for key, photod_table in photodiode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        resolution = photod_table.meta["Processing"]["resolution"]
        qe = lica.photodiode.load(model=model, resolution=int(resolution))[COL.QE]
        for filter_table in filter_dict[key]:
            name = filter_table.meta["Processing"]["name"]
            processed = filter_table.meta["Processing"].get("processed")
            if processed:
                log.warn("Skipping %s. Already been processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            transmission = (filter_table[TBCOL.CURRENT] / photod_table[TBCOL.CURRENT]) * qe
            filter_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            filter_table[PROCOL.PHOTOD_QE] = qe
            filter_table[PROCOL.SPECTRAL] = (
                np.round(transmission, decimals=5) * u.dimensionless_unscaled
            )
            filter_table.meta["Processing"]["using photodiode"] = model
            filter_table.meta["Processing"]["processed"] = True
    return filter_dict


def passive_process(photodiode_dict: DiodeDict, filter_dict: DeviceDict) -> DeviceDict:
    """
    Process Device ECSV files in a given directory.
    As the device is optically passive (i.e. filters) we do not correct by photodiode QE
    """
    for key, photod_table in photodiode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        for filter_table in filter_dict[key]:
            name = filter_table.meta["Processing"]["name"]
            processed = filter_table.meta["Processing"].get("processed")
            if processed:
                log.warn("Skipping %s. Already been processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            transmission = (filter_table[TBCOL.CURRENT] / photod_table[TBCOL.CURRENT])
            filter_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            filter_table[PROCOL.TRANS] = (
                np.round(transmission, decimals=5) * u.dimensionless_unscaled
            )
            filter_table.meta["Processing"]["using photodiode"] = model
            filter_table.meta["Processing"]["processed"] = True
    return filter_dict