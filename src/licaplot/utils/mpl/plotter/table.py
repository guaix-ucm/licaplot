# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# -------------------
# System wide imports
# -------------------

import os
import logging
from typing import Iterable

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table
from lica.lab import BENCH
import scipy.interpolate

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ---------
# Own stuff
# ---------


def read_csv(path: str, columns: Iterable[str] | None, delimiter: str | None) -> Table:
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext == ".csv":
        table = (
            astropy.io.ascii.read(
                path,
                delimiter=delimiter,
                data_start=1,
                names=columns,
            )
            if columns
            else astropy.io.ascii.read(path, delimiter)
        )
    elif ext == ".ecsv":
        table = astropy.io.ascii.read(path, format="ecsv")
    else:
        table = astropy.io.ascii.read(path, delimiter)
    return table


def trim_table(
    table: Table,
    xcol: int,
    xunit: u.Unit,
    xlow: float | None,
    xhigh: float | None,
    lunit: u.Unit,
    lica: bool,
) -> None:
    x = table.columns[xcol]
    xmax = np.max(x) * xunit if xhigh is None else xhigh * lunit
    xmin = np.min(x) * xunit if xlow is None else xlow * lunit
    if lica:
        xmax, xmin = (
            min(xmax, BENCH.WAVE_END.value * u.nm),
            max(xmin, BENCH.WAVE_START.value * u.nm),
        )
    table = table[x <= xmax]
    x = table.columns[xcol]
    table = table[x >= xmin]
    log.debug("Trimmed table to wavelength [%s - %s] range", xmin, xmax)
    return table


def resample_column(
    table: Table, resolution: int, xcol: int, xunit: u.Unit, ycol: int, lica: bool
) -> Table:
    x = table.columns[xcol]
    y = table.columns[ycol]
    if lica:
        xmin = BENCH.WAVE_START.value
        xmax = BENCH.WAVE_END.value
    else:
        xmax = np.floor(np.max(x))
        xmin = np.ceil(np.min(x))
    wavelength = np.arange(xmin, xmax + resolution, resolution)
    log.debug("Wavelengh grid to resample is\n%s", wavelength)
    interpolator = scipy.interpolate.Akima1DInterpolator(x, y)
    log.debug(
        "Resampled table to wavelength [%s - %s] range with %s resolution",
        xmin,
        xmax,
        resolution,
    )
    return wavelength, interpolator(wavelength)