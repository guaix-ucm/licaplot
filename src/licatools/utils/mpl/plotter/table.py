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
from typing import Iterable, Tuple, Union, Optional
from abc import ABC, abstractmethod

# ---------------------
# Third-party libraries
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

from .types import Tables, ColNum, ColNums
from ...table import tcn, tcu

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ---------
# Own stuff
# ---------


def read_csv(path: str, columns: Optional[Iterable[str]], delimiter: Optional[str]) -> Table:
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
    xcn: int,
    xlow: Optional[float],
    xhigh: Optional[float],
    xlunit: u.Unit,
    lica: bool,
) -> None:
    x = table.columns[xcn]
    xunit = tcu(table, xcn)
    xmax = np.max(x) * xunit if xhigh is None else xhigh * xlunit
    xmin = np.min(x) * xunit if xlow is None else xlow * xlunit
    if lica:
        xmax, xmin = (
            min(xmax, BENCH.WAVE_END.value * u.nm),
            max(xmin, BENCH.WAVE_START.value * u.nm),
        )
    table = table[x <= xmax]
    x = table.columns[xcn]
    table = table[x >= xmin]
    log.debug("Trimmed table to wavelength [%s - %s] range", xmin, xmax)
    return table


def resample_column(
    table: Table, resolution: int, xcn: ColNum, xunit: u.Unit, ycn: ColNum, lica: bool
) -> Table:
    x = table.columns[xcn]
    y = table.columns[ycn]
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

    def ncols(self):
        return len(self._ycn) if (isinstance(self._ycn, list) or isinstance(self._ycn, tuple)) else 1

    def ntab(self):
        """Ugly code that does the trick because there are no more choices"""
        if hasattr(self, "_path") or hasattr(self, "_paths"):
            result = len(self._paths) if hasattr(self, "_paths") else 1
        else:
            result = len(self._tables) if hasattr(self, "_tables") else 1
        return result
       

    def _check_col_range(self, table: Table, ccnn: Iterable[ColNum|ColNums], tag: str) -> None:
        ncols = len(table.columns)
        for cn in ccnn:
            if isinstance(cn, int):
                if not (0 <= cn < ncols):
                    raise ValueError(
                        "%s column number (%d) should be 1 <= Y <= (%d)" % (tag, cn + 1, ncols)
                    )
            else:
                for ycn in cn:
                    if not (0 <= ycn < ncols):
                        raise ValueError(
                        "%s column number (%d) should be 1 <= Y <= (%d)" % (tag, ycn + 1, ncols)
                    )

    def _build_one_table(self, path) -> Table:
        log.debug("Not resampling table")
        table = read_csv(path, self._columns, self._delim)
        table = trim_table(table, self._xcn, self._xl, self._xh, self._xu, self._lica_trim)
        log.debug(table.info)
        log.debug(table.meta)
        return table

    def _build_one_resampled_table(self, path: str, ycn: ColNum) -> Table:
        log.debug("resampling table to %s", self._resol)
        table = read_csv(path, self._columns, self._delim)
        xunit = tcu(table, self._xcn)
        wavelength, resampled_col = resample_column(
            table, self._resol, self._xcn, xunit, ycn, self._lica_trim
        )
        names = [c for c in table.columns]
        values = [None,] * len(names)
        values[self._xcn] = wavelength
        values[ycn] = resampled_col
        log.info("NAMES = %s", names)
        log.info("VALUES = %s", values)
        new_table = Table(data=values, names=names)
        new_table.meta = table.meta
        new_table = trim_table(
            new_table, self._xcn, self._xl, self._xh, self._xu, self._lica_trim
        )
        table = new_table
        col_x_unit = tcu(table, self._xcn)
        col_y_unit = tcu(table,ycn)
        if col_y_unit is None:
            col_y_name = tcn(table, ycn)
            table[col_y_name] = table[col_y_name] * u.dimensionless_unscaled
        if col_x_unit is None:
            col_x_name = tcn(table, self._xcn)
            table[col_x_name] = table[col_x_name] * u.dimensionless_unscaled
        log.debug(table.info)
        log.debug(table.meta)
        return table


class TableFromFile(TableBase):
    def __init__(
        self,
        path: str,
        columns: Optional[Iterable[str]],
        delimiter: Optional[str],
        xcn: ColNum,
        ycn: Union[ColNum,ColNums],
        xlow: Optional[float],
        xhigh: Optional[float],
        resolution: Optional[int],
        lica_trim: Optional[bool],
        xlunit: u.Unit = u.dimensionless_unscaled,
    ):
        self._path = path
        self._ycn = ycn - 1 if isinstance(ycn, ColNum) else [cn - 1 for cn in ycn]
        self._xcn = xcn - 1
        self._xl = xlow
        self._xh = xhigh
        self._xu = xlunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim

    def build_tables(self) -> Tuple[Table, ColNum, ColNum]:
        table = (
            self._build_one_table(self._path)
            if self._resol is None
            else self._build_one_resampled_table(self._path, self._ycn)
        )
        self._check_col_range(table, [self._xcn], tag="X")
        self._check_col_range(table, [self._ycn], tag="Y")
        return table, self._xcn, self._ycn


class TablesFromFiles(TableBase):
    def __init__(
        self,
        paths: Iterable[str],
        columns: Optional[Iterable[str]],
        delimiter: Optional[str],
        xcn: ColNum,
        ycn: Union[ColNum,ColNums],
        xlow: Optional[float],
        xhigh: Optional[float],
        xlunit: u.Unit,
        resolution: Optional[int],
        lica_trim: Optional[bool],
    ):
        self._paths = paths
        self._ycn = ycn - 1 if isinstance(ycn, int) else [y - 1 for y in ycn]
        self._xcn = xcn - 1
        self._xl = xlow
        self._xh = xhigh
        self._xu = xlunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim

    def build_tables(self) -> Tuple[Tables, ColNum,  Union[ColNum, ColNums]]:
        tables = list()
        yc = [self._ycn] if isinstance(self._ycn, int) else self._ycn
        for path in self._paths:
            if self._resol is None:
                table = self._build_one_table(path)
            else:
                assert isinstance(self._ycn, int), "Y Column only"
                table = self._build_one_resampled_table(path, self._ycn)
            self._check_col_range(table, [self._xcn], tag="X")
            self._check_col_range(table, yc, tag="Y")
            tables.append(table)
        return tables, self._xcn, self._ycn


class TableWrapper(TableBase):
    def __init__(
        self,
        table: Table,
        xcn: ColNum,
        ycn: Union[ColNum, ColNums],
    ):
        self._table = table
        self._xcn = xcn - 1
        self._ycn = ycn - 1 if isinstance(ycn, ColNum) else [cn - 1 for cn in ycn]

    def build_tables(self) -> Tuple[Table, ColNum, Union[ColNum, ColNums]]:
        self._check_col_range(self._table, [self._xcn], tag="X")
        if isinstance(self._ycn, int):
            self._check_col_range(self._table, [self._ycn], tag="Y")
        else:
            self._check_col_range(self._table, self._ycn, tag="Y")
        return self._table, self._xcn, self._ycn


class TablesWrapper(TableBase):
    def __init__(
        self,
        tables: Tables,
        xcn: ColNum,
        ycn: Union[ColNum, ColNums],
    ):
        self._xcn = xcn - 1
        self._ycn = ycn - 1 if isinstance(ycn, ColNum) else [cn - 1 for cn in ycn]
        self._tables = tables

    def build_tables(self) -> Tuple[Tables, ColNum, Union[ColNum, ColNums]]:
        return self._tables, self._xcn, self._ycn


__all__ = [
    "read_csv",
    "trim_table",
    "resample_column",
    "ITableBuilder",
    "TableFromFile",
    "TablesFromFiles",
]
