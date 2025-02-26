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
from abc import ABC, abstractmethod

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table
from lica.lab import BENCH
import scipy.interpolate

# ---------
# Own stuff
# ---------

from .types import Tables, ColNum

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


class ITableBuilder(ABC):
    @abstractmethod
    def build_tables(self) -> Tables:
        pass


class TableBase(ITableBuilder):
    def _build_one_table(self, path) -> Table:
        log.debug("Not resampling table")
        table = read_csv(path, self._columns, self._delim)
        table = trim_table(table, self._xc, self._xu, self._xl, self._xh, self._lu, self._lica_trim)
        log.debug(table.info)
        log.debug(table.meta)
        return table

    def _build_one_resampled_table(self, path: str, yc: ColNum, yu: u.Unit) -> Table:
        log.debug("resampling table to %s", self._resol)
        table = read_csv(path, self._columns, self._delim)
        # Prefer resample before trimming to avoid generating extrapolation NaNs
        wavelength, resampled_col = resample_column(
            table, self._resol, self._xc, self._xu, yc, self._lica_trim
        )
        names = [c for c in table.columns]
        values = [None, None]
        values[self._xc] = wavelength
        values[yc] = resampled_col
        new_table = Table(data=values, names=names)
        new_table.meta = table.meta
        new_table = trim_table(
            new_table, self._xc, self._xu, self._xl, self._xh, self._lu, self._lica_trim
        )
        table = new_table
        col_x = table.columns[self._xc]
        col_y = table.columns[yc]
        if col_y.unit is None:
            table[col_y.name] = table[col_y.name] * yu
        if col_x.unit is None:
            table[col_x.name] = table[col_x.name] * self._xu
        log.debug(table.info)
        log.debug(table.meta)
        return table


class TableFromFile(TableBase):
    def __init__(
        self,
        path: str,
        columns: Iterable[str] | None,
        delimiter: str | None,
        xcol: ColNum,
        xunit: u.Unit,
        yunit: u.Unit,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        resolution: int | None,
        lica_trim: bool | None,
        ycol: ColNum | None = None,
    ):
        self._path = path
        self._yc = ycol - 1 if ycol is not None else None
        self._xc = xcol - 1
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim

    def build_tables(self) -> Table:
        return (
            self._build_one_table(self._path)
            if self._yc is None
            else self._build_one_resampled_table(self._path, self._yc, self._yu)
        )


class TablesFromFiles(TableBase):
    def __init__(
        self,
        paths: Iterable[str],
        columns: Iterable[str] | None,
        delimiter: str | None,
        xcol: ColNum,
        xunit: u.Unit,
        yunit: u.Unit,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        resolution: int | None,
        lica_trim: bool | None,
        ycol: ColNum | None = None,
    ):
        self._paths = paths
        self._yc = ycol - 1 if ycol is not None else None
        self._xc = xcol - 1
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim

    def build_tables(self) -> Tables:
        tables = list()
        for path in self._paths:
            if self._yc is None:
                table = self._build_one_table(path)
            else:
                table = self._build_one_resampled_table(path, self._yc, self._yu)
            tables.append(table)
        return tables


class TableWrapper(ITableBuilder):
    def __init__(
        self,
        table: Table,
    ):
        self._table = table

    def build_tables(self) -> Table:
        return self._table


class TablesWrapper(ITableBuilder):
    def __init__(
        self,
        tables: Tables,
    ):
        self._tables = tables

    def build_tables(self) -> Tables:
        return self._tables


__all__ = [
    "read_csv",
    "trim_table",
    "resample_column",
    "ITableBuilder",
    "TableFromFile",
    "TablesFromFiles",
]
