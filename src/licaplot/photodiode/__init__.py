# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from enum import IntEnum
from importlib.resources import files

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------

from .. import StrEnum


# ----------------
# Module constants
# ----------------


# Photodiode record
class Hamamatsu:
    MANUF = "Hamamatsu"
    MODEL = "S2281-04"
    SERIAL = "1097"
    WINDOW = "Quartz Glass"
    PHS_SIZE = 7.98 * u.mm  # Photosensitive size (diameter)
    PHS_AREA = 50 * (u.mm**2)  # Photosensitive area
    DARK = {
        "typ": {
            "Value": 50 * (u.pA),
            "Temp": 25 * u.deg_C,
        },
        "max": {  # Dark current at given room Temp
            "Value": 500 * (u.pA),
            "Temp": 25 * u.deg_C,
        },
    }
    # responsivity peak
    PEAK = {
        "typ": {
            "Wave": 960 * (u.nm),
            "Resp": 0.5 * (u.A / u.W),
            "Temp": 25 * u.deg_C,
        }
    }


# Photodiode record
class OSI:
    MANUF = "OSI"
    MODEL = "PIN-10D"
    SERIAL = "OSI-11-01-004-10D"
    WINDOW = "Quartz Glass"
    PHS_SIZE = 11.28 * u.mm  # Photosensitive size (diameter)
    PHS_AREA = 100 * (u.mm**2)  # Photosensitive area
    DARK = {
        "typ": {
            "Value": 2 * (u.nA),
            "Temp": 23 * u.deg_C,
        },
        "max": {  # Dark current at given room Temp
            "Value": 25 * (u.nA),
            "Temp": 23 * u.deg_C,
        },
    }
    # responsivity peak
    PEAK = {
        "typ": {
            "Wave": 970 * (u.nm),
            "Resp": 0.6 * (u.A / u.W),
            "Temp": 25 * u.deg_C,
        },
        "max": {
            "Wave": 970 * (u.nm),
            "Resp": 0.65 * (u.A / u.W),
            "Temp": 25 * u.deg_C,
        },
    }


class COL(StrEnum):
    """Calibration Table Columns"""

    WAVE = "Wavelength"
    RESP = "Responsivity"
    QE = "QE"


class BENCH(IntEnum):
    """LICA Optical bench Wavelength range"""

    WAVE_START = 350
    WAVE_END = 1050


class PhotodiodeModel(StrEnum):
    HAMAMATSU = f"{Hamamatsu.MODEL}"
    OSI = f"{OSI.MODEL}"


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ------------------
# Auxiliary fnctions
# ------------------

def export(model: PhotodiodeModel, resolution: int, path: str) -> None:
    """Make a copy of the proper ECSV Astropy Table"""
    log.info("Exporting model %s, resolution %d nm to file %s", model, resolution, path)
    name = f"{model}-Responsivity-Interpolated@1nm.ecsv"
    in_path = files("licaplot.photodiode").joinpath(name)
    t1 = astropy.io.ascii.read(in_path, format="ecsv")
    if resolution == 1:
         t1.write(path, delimiter=",", overwrite=True)
    else:
        # Subsamples the table
        t2 = Table(
            [t1[COL.WAVE][::resolution], t1[COL.RESP][::resolution], t1[COL.QE][::resolution]],
            names=[n for n in COL],
        )
        t2.meta = t1.meta
        history = {
            "Description": f"Subsampled calibration from {name}",
            "Resolution": resolution * u.nm,
            "Start wavelength": np.min(t2[COL.WAVE]) * u.nm,
            "End wavelength": np.max(t2[COL.WAVE]) * u.nm,
        }
        t2.meta["History"].append(history)
        t2.write(path, delimiter=",", overwrite=True)


def load(model: PhotodiodeModel, resolution: int) -> Table:
    """Return a ECSV as as Astropy Table"""
    log.info("Reading LICA photodiode model %s, resolution %d nm", model, resolution)
    name = f"{model}-Responsivity-Interpolated@1nm.ecsv"
    in_path = files("licaplot.photodiode").joinpath(name)
    t = astropy.io.ascii.read(in_path, delimiter=";")
    return Table(
        [t[COL.WAVE][::resolution], t[COL.RESP][::resolution], t[COL.QE][::resolution]],
        names=[n for n in COL],
    )
