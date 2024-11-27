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
from enum import Enum
from importlib.resources import files

# ---------------------
# Thrid-party libraries
# ---------------------

import astropy.io.ascii
import astropy.units as u
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------



# ----------------
# Module constants
# ----------------

class Photodiode(Enum):
    # Photodiode models
    OSI = "OSI-11-01-004-10D"
    HAMAMATSU = "Ham-S2281-04"

class Column(Enum):
    WAVELENGTH = "Wavelength [nm]"
    RESPONSIVITY = "Responsivity [A/W]"
    QE = "Quantum Efficiency"

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ------------------
# Auxiliary fnctions
# ------------------

def export(model: Photodiode, resolution: int, path: str) -> None:
    log.info("Exporting model %s, resolution %d nm to file %s", model, resolution, path)
    f = files("licaplot.photodiode").joinpath(model + ".csv")
    with f.open("r") as csvfile:
        lines = csvfile.readlines()
    with open(path, "w") as f:
        f.writelines(lines[0:1])
        f.writelines(lines[1::resolution])


def load(model: Photodiode, resolution: int) -> Table:
    """Return dictionaries whose keys are the wavelengths"""
    log.info("Reading LICA photodiode model %s, resolution %d nm", model, resolution)
    f = files("licaplot.photodiode").joinpath(model + ".csv")
    table = astropy.io.ascii.read(f, delimiter=";")
    # Add units
    table[Column.WAVELENGTH.value] =  table[Column.WAVELENGTH.value] * u.nm
    table[Column.RESPONSIVITY.value] =  table[Column.RESPONSIVITY.value] * u.ampere / u.watt
    table[Column.RESPONSIVITY.value] =  table[Column.RESPONSIVITY.value] * u.dimensionless_unscaled
    mask = (table.columns[0].astype(int) % resolution) == 0
    return table[mask]
