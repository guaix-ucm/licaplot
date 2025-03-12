# --------------------
# System wide imports
# -------------------

import os
import random
import logging
import itertools
from collections import defaultdict
from datetime import datetime
from typing import Tuple, Iterable, Dict, DefaultDict

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.time import Time
from astropy.units import Quantity
from astropy.table import Table, Column
from astropy.constants import astropyconst20 as const
import scipy.interpolate

import lica.lab
from lica.lab.photodiode import COL, BENCH
from lica.lab.ndfilters import NDFilter

# ------------------------
# Own modules and packages
# ------------------------

from .. import TBCOL, PROCOL, PROMETA, TWCOL, META

from ..dbase.api.metadata import db_lookup

DiodeDict = Dict[str, Table]
DeviceDict = DefaultDict[str, Table]

# ----------------
# Module constants
# ----------------


TSL237_FICT_GAIN = 1 * (u.pA / u.Hz)
TSL237_AREA = 0.92 * u.mm**2
TSL237_REF_WAVE = 532 * u.nm
TSL237_REF_RESP = 2.3 * u.kHz / (u.uW / u.cm**2)

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)
tags = list(itertools.product("ABCDEFGHYJKLMNOPQRSTUVWXYZ", repeat=2))

# ------------------
# Auxiliar functions
# ------------------


def random_tag() -> str:
    return "".join(random.choice(tags))


def quantum_efficiency(wavelength: Column, responsivity: Column) -> Column:
    """Computes the Quantum Efficiency given the Responsivity in A/W"""
    K = (const.h * const.c) / const.e
    return np.round(K * responsivity / wavelength.to(u.m), decimals=5) * u.dimensionless_unscaled


def equivalent_ecsv(path: str) -> str:
    """Keeps the same name and directory but changes extesion to ECSV"""
    output_path, _ = os.path.splitext(path)
    return output_path + ".ecsv"


def name_from_file(path: str) -> str:
    """Keeps the same name and directory but changes extesion to ECSV"""
    path = os.path.basename(path)
    path, _ = os.path.splitext(path)
    return path


def read_ecsv(path: str) -> Table:
    return astropy.io.ascii.read(path, format="ecsv")


def read_tess_csv(path: str) -> Table:
    """Load CSV files produced by textual-spectess"""
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
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
    table.meta[META.PHAREA] = 0.92 * u.mm**2
    return table


def add_lica_metadata(path: str, table: Table) -> None:
    log.info("Looking up LICA database for more metadata of %s", path)
    metadata = db_lookup(path)
    if metadata:
        timestamp = datetime.strptime(metadata["timestamp"], "%Y-%m-%d %H:%M:%S")
        #timestamp = Time(timestamp, scale='utc')
        table.meta["timestamp"] = timestamp
        table.meta["original_name"] = metadata["original_name"]
        monochromator_slit = metadata.get("monochromator_slit")
        if monochromator_slit:
            table.meta["monochromator_slit"] = monochromator_slit * u.mm
        input_slit = metadata.get("input_slit")
        if input_slit:
            table.meta["input_slit"] = input_slit * u.mm
        psu_current = metadata.get("psu_current")
        if psu_current:
            table.meta["psu_current"] = psu_current * u.A


def read_scan_csv(path: str) -> Table:
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


def read_manual_csv(path: str) -> Table:
    """Load CSV files produced by manually copying LICA TestBench.exe into a CSV file"""
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE, TBCOL.CURRENT, TBCOL.READ_NOISE),
        converters={COL.WAVE: np.float64, TBCOL.CURRENT: np.float64, TBCOL.READ_NOISE: np.float64},
    )
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[TBCOL.CURRENT] = np.abs(table[TBCOL.CURRENT]) * u.A
    table[TBCOL.READ_NOISE] = table[TBCOL.READ_NOISE] * u.A


def read_tsl237_datasheet_csv(path: str) -> Table:
    table = astropy.io.ascii.read(
        path,
        delimiter=",",
        data_start=1,
        names=(COL.WAVE, TWCOL.NORM),
        converters={COL.WAVE: np.float64, TWCOL.NORM: np.float64},
    )
    table[COL.WAVE] = table[COL.WAVE] * u.nm
    table[TWCOL.NORM] = table[TWCOL.NORM] * u.dimensionless_unscaled
    return table


def photodiode_table(
    path: str,
    model: str,
    tag: str,
    title: str,
    x_low: int,
    x_high: int,
    manual: bool = False,
) -> Table:
    """Converts CSV file from photodiode into ECSV file"""
    table = read_manual_csv(path) if manual else read_scan_csv(path)
    resolution = np.ediff1d(table[COL.WAVE])
    assert all([r == resolution[0] for r in resolution])
    if not (x_low == BENCH.WAVE_START and x_high == BENCH.WAVE_END):
        history = f"Trimmed to [{x_low:04d}-{x_high:04d}] nm wavelength range"
    else:
        history = None
    name = name_from_file(path)
    title = title or f"{model} reference measurements"
    title = " ".join(title) if not isinstance(title, str) else title
    table.meta = {
        "label": model,  # label used for display purposes
        "title": title,
        "Processing": {
            "type": PROMETA.PHOTOD.value,
            "model": model,
            "tag": tag,
            "name": name,
            "resolution": resolution[0],
        },
        "History": [],
    }
    add_lica_metadata(path, table)
    if history:
        log.info("Trinming %s to [%d-%d] nm", name, x_low, x_high)
        table.meta["History"].append(history)
        table.meta["Processing"]["x_low"] = x_low
        table.meta["Processing"]["x_high"] = x_high
    if not manual:
        table.remove_column(TBCOL.INDEX)
    table = table[(table[COL.WAVE] >= x_low) & (table[COL.WAVE] <= x_high)]
    log.info("Processing metadata is added: %s", table.meta)
    return table


def photodiode_ecsv(
    path: str,
    model: str,
    tag: str,
    title: str,
    x_low: int,
    x_high: int,
    manual=False,
) -> str:
    table = photodiode_table(
        path=path, model=model, tag=tag, title=title, x_low=x_low, x_high=x_high, manual=manual
    )
    output_path = str(equivalent_ecsv(path))
    log.info("Saving Astropy photodiode table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)
    return path


def filter_table(path: str, label: str, title: str, tag: str) -> Table:
    table = read_scan_csv(path)
    resolution = np.ediff1d(table[COL.WAVE])
    title = title or f"{label} filter Measurements"
    title = " ".join(title) if not isinstance(title, str) else title
    table.meta = {
        "label": label,  # label used for display purposes
        "title": title or f"{label} filter measurements",
        "Processing": {
            "type": PROMETA.FILTER.value,
            "tag": tag,
            "name": name_from_file(path),
            "resolution": resolution[0],
        },
        "History": [],
    }
    add_lica_metadata(path, table)
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    return table


def filter_ecsv(path: str, label: str, title: str = None, tag: str = "") -> str:
    table = filter_table(path=path, label=label, title=title, tag=tag)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy device table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)
    return output_path


def tessw_table(path: str, label: str, title: str = None, tag: str = "") -> Table:
    raw_table = read_tess_csv(path)
    raw_table.remove_column(TWCOL.TIME)
    raw_table.remove_column(TWCOL.SEQ)
    raw_table.remove_column(TWCOL.FILT)
    table = raw_table.group_by(COL.WAVE).groups.aggregate(np.mean)
    resolution = np.ediff1d(table[COL.WAVE])
    table.meta = {
        "label": label,  # label used for display purposes
        "title": title or f"{label} measurements",
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
    add_lica_metadata(path, table)
    log.info("Processing metadata is added: %s", table.meta)
    return table


def tessw_ecsv(path: str, label: str, title: str = None, tag: str = "") -> str:
    table = tessw_table(path=path, label=label, title=title, tag=tag)
    output_path = equivalent_ecsv(path)
    log.info("Saving Astropy device table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)
    return output_path


def tsl237_table(
    path: str,
    label: str,
    resolution: int,
    tag: str = "",
    gain: Quantity = TSL237_FICT_GAIN,
    sensor_area: Quantity = TSL237_AREA,
    ref_point: Tuple[Quantity, Quantity] = (TSL237_REF_WAVE, TSL237_REF_RESP),
) -> Table:
    """Obtained by reading a digitized CSV from the datasheet"""
    table = read_tsl237_datasheet_csv(path)
    wavelength = np.arange(BENCH.WAVE_START, BENCH.WAVE_END + 1, resolution) * u.nm
    interpolator = scipy.interpolate.Akima1DInterpolator(table[COL.WAVE], table[TWCOL.NORM])
    norm_responsivity = interpolator(wavelength)
    ref_norm_resp = norm_responsivity[wavelength == ref_point[0]]
    denormal_factor = (gain * ref_point[1] / (sensor_area * ref_norm_resp)).to(u.A / u.W)
    responsivity = norm_responsivity * denormal_factor
    qe = quantum_efficiency(wavelength, responsivity)
    responsivity = np.round(responsivity, decimals=5)
    table = Table(
        data=[wavelength, responsivity, qe],
        names=[COL.WAVE, COL.RESP, COL.QE],
        meta={
            META.GAIN.value: gain,
            META.REF_WAVE.value: ref_point[0],
            META.REF_RESP.value: ref_point[1],
            META.PHAREA.value: sensor_area,
        },
    )
    return table


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
                    f"Another photodiode table has the same tag: {table.meta['Processing']['name']}",
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
    photodiode_dict: DiodeDict,
    sensor_dict: DeviceDict,
    sensor_column=TBCOL.CURRENT,
    gain=u.dimensionless_unscaled,
    sensor_area=1 * u.mm**2,
) -> DeviceDict:
    """
    Process Device ECSV files in a given directory.
    As the device is optically active (i.e. TSL237) we must correct by the photodiode QE
    """
    for key, photod_table in photodiode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        resolution = photod_table.meta["Processing"]["resolution"]
        ref_table = lica.lab.photodiode.load(model=model, resolution=int(resolution))
        photod_qe = ref_table[COL.QE]
        photod_area = ref_table.meta[META.PHAREA]
        for i, sensor_table in enumerate(sensor_dict[key]):
            name = sensor_table.meta["Processing"]["name"]
            processed = sensor_table.meta["Processing"].get("processed")
            if processed:
                log.warn("Skipping %s. Already been processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            x_low = photod_table.meta["Processing"].get("x_low")
            x_high = photod_table.meta["Processing"].get("x_high")
            if x_low:
                log.info("Trimming %s to [%d-%d] nm", name, x_low, x_high)
                sensor_table = sensor_table[
                    (sensor_table[COL.WAVE] >= x_low) & (sensor_table[COL.WAVE] <= x_high)
                ]
                sensor_table.meta["History"].append(
                    f"Trimmed to [{x_low:04d}-{x_high:04d}] nm wavelength range"
                )
                sensor_dict[key][i] = sensor_table  # Necessary to capture the new table in the dict
            # Now do the math
            sensor_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            sensor_table[PROCOL.PHOTOD_QE] = photod_qe
            sensor_qe = (
                photod_qe
                * (photod_area / sensor_area)
                * (sensor_table[sensor_column] * gain)
                / photod_table[TBCOL.CURRENT]
            ).decompose()
            sensor_table[COL.QE] = np.round(sensor_qe, decimals=5) * u.dimensionless_unscaled
            sensor_table.meta["Processing"]["using photodiode"] = model
            sensor_table.meta["Processing"]["processed"] = True
            sensor_table.meta["History"].append(
                "Scaled and QE-weighted readings wrt photodiode readings"
            )
    return sensor_dict


def passive_process(
    photodiode_dict: DiodeDict, filter_dict: DeviceDict, ndf: NDFilter = None
) -> DeviceDict:
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
            x_low = photod_table.meta["Processing"].get("x_low")
            x_high = photod_table.meta["Processing"].get("x_high")
            if x_low:
                log.info("Trinming %s to [%d-%d] nm", name, x_low, x_high)
                filter_table = filter_table[
                    (filter_table[COL.WAVE] >= x_low) & (filter_table[COL.WAVE] <= x_high)
                ]
                filter_table.meta["History"].append(
                    f"Trimmed to [{x_low:04d}-{x_high:04d}] nm wavelength range"
                )
                filter_dict[key][i] = filter_table  # Necessary to capture the new table in the dict
            filter_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            filter_table[COL.TRANS] = (filter_table[TBCOL.CURRENT]) / (photod_table[TBCOL.CURRENT])
            filter_table[COL.TRANS] /= (
                u.A
            )  # Hack. Apparently the op. above doesn't make it adimensional
            if ndf is not None:
                resolution = np.ediff1d(filter_table[COL.WAVE])[0]
                ndf_table = lica.lab.ndfilters.load(model=ndf, resolution=int(resolution))
                log.info("Correcting %s %s by %s spectral response", name, COL.TRANS, ndf)
                column = f"{ndf} Corrected {COL.TRANS}"
                filter_table[column] = filter_table[COL.TRANS] * ndf_table[COL.TRANS]
            filter_table.meta["Processing"]["using photodiode"] = model
            filter_table.meta["Processing"]["processed"] = True
            filter_table.meta["History"].append("Scaled readings wrt photodiode readings")
    return filter_dict
