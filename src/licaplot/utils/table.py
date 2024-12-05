# --------------------
# System wide imports
# -------------------

import logging

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table
from lica.photodiode import COL

# ------------------------
# Own modules and packages
# ------------------------

from .. import TBCOL

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)


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
