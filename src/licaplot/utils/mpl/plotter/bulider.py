# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# -------------------
# System wide imports
# -------------------

from __future__ import annotations  # lazy evaluations of annotations

import logging
from abc import ABC, abstractmethod
from itertools import batched
from typing import Sequence, Iterable, Any

# ---------------------
# Thrid-party libraries
# ---------------------

import astropy.units as u
from astropy.table import Table

# ---------
# Own stuff
# ---------

from .types import (
    Markers,
    ColNum,
    ColNums,
    MarkerSeq,
    Legends,
    Tables,
    Titles,
    LegendsGroup,
    MarkersGroup,
)
from .table import read_csv, trim_table, resample_column

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)


class IBuilder(ABC):
    @property
    @abstractmethod
    def product(self) -> None:
        pass

    @abstractmethod
    def build_tables(self) -> Tables:
        pass

    @abstractmethod
    def build_titles(self) -> Titles:
        pass

    @abstractmethod
    def build_legends_grp(self) -> LegendsGroup:
        pass

    @abstractmethod
    def build_markers_grp(self) -> MarkersGroup:
        pass


class Director:
    """
    Responsible for executing the building steps in a particular sequence.
    """

    def __init__(self) -> None:
        self._builder = None

    @property
    def builder(self) -> IBuilder:
        return self._builder

    @builder.setter
    def builder(self, builder: IBuilder) -> None:
        self._builder = builder


class Base(IBuilder):
    # -------------------------------------------------
    # Useful methods to reuse / override in sublclasses
    # -------------------------------------------------

    def __init__(self) -> None:
        """
        A fresh builder instance should contain a blank product object, which is
        used in further assembly.
        """
        self.reset()

    def reset(self) -> None:
        self._product = (None, None, None, None)

    def _default_table_title(self) -> Titles:
        return [" ".join(self._title) if self._title is not None else self._table.meta["title"]]

    def _default_tables_title(self) -> Titles:
        return [" ".join(self._title) if self._title is not None else self._tables[0].meta["title"]]

    def _build_one_table(self, path: str) -> Table:
        log.debug("Not resampling table")
        table = read_csv(path, self._columns, self._delimiter)
        table = trim_table(table, self._xc, self._xu, self._xl, self._xh, self._lu, self._lica_trim)
        log.debug(table.info)
        log.debug(table.meta)
        return table

    def _build_one_resampled_table(self, path: str, yc: ColNum, yu: u.Unit) -> Table:
        if self._resol is None:
            return self._build_one_table(path)
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
        new_table.meta = table.neta
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

    def check_legends(self) -> None:
        if self._legends is not None and len(self._legends) != self._ncol:
            raise ValueError(
                "number of labels (%d) should match number of y-columns (%d)"
                % (len(self._legends), self._ncol),
            )

    def check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != self._ncol:
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d)"
                % (len(self._markers), self._ncols)
            )

    ########################
    def build(self):
        self.check()
        self.build_titles()
        self.build_legends_grp()
        self.build_markers_grp()

    def default_table_legends(self) -> Legends:
        return (
            self.args_legends
            if self.args_legends is not None
            else [self.table.columns[y - 1].name[:6] + "." for y in self.ycols]
        )

    def default_table_markers(self) -> Markers:
        return self.args_markers

    def _get_legends_grp(self) -> LegendsGroup:
        return (
            list(batched(self.legends, self.ncol))
            if self.legends is not None
            else [[None] * self.ncol] * self.ntab
        )

    def _get_markers_grp(self) -> MarkersGroup:
        return (
            list(batched(self.markers, self.ncol))
            if self.markers is not None
            else [[None] * self.ncol] * self.ntab
        )


class SingleTableColumnBuilder(Base):
    def __init__(
        self,
        path: str,
        xcol: ColNum,
        xunit: u.Unit,
        ycol: ColNum,
        yunit: u.Unit,
        title: str | None,
        label: str | None,
        marker: str | None,
        columns: Iterable[str] | None,
        delimiter: str | None,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        resolution: int | None,
        lica_trim: bool | None,
    ):
        self._marker = marker
        self._legend = label
        self._title = title
        self._path = path
        self._yc = ycol
        self._xc = xcol
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim
        self._ncol = 1
        self._ntab = 1

    def build_tables(self) -> Tables:
        table = self._build_one_resampled_table(self, self._path, self._yc, self._yu, self._resol)
        self._table = table
        return [table]

    def build_titles(self) -> Titles:
        return self._default_table_title()

    def build_markers_grp(self) -> LegendsGroup:
        return [[self._marker]] if self._marker is not None else [[None]]

    def build_legends_grp(self) -> LegendsGroup:
        return [[self._legend]] if self._legend is not None else [[None]]

    def group(self, sequence: Sequence[Any]) -> Sequence[Sequence[Any]]:
        return (
            list(batched(sequence, self._ncol))
            if sequence is not None
            else [[None] * self._ncol] * self._ntab
        )


class SingleTableColumnsBuilder(Base):
    def __init__(
        self,
        path: str,
        xcol: ColNum,
        xunit: u.Unit,
        ycols: ColNums,
        yunit: u.Unit,
        title: str | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
        columns: Iterable[str] | None,
        delimiter: str | None,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        lica_trim: bool | None,
    ):
        self._markers = markers
        self._legends = labels
        self._title = title
        self._path = path
        self._yycc = ycols
        self._xc = xcol
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._lica_trim = lica_trim
        self._ncol = len(ycols)
        self._ntab = 1

    def build_tables(self) -> Tables:
        table = self._build_one_table(self._path)
        self._table = table
        return [table]

    def build_titles(self) -> Titles:
        return self._default_table_title()

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        return self.group(self._markers)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            self._legends
            if self._legends is not None
            else [self._table.columns[y].name[:6] + "." for y in self._yycc]
        )
        return self.group(flat_legends)


class SingleTablesColumnBuilder(Base):
    def __init__(
        self,
        paths: Sequence[str],
        xcol: ColNum,
        xunit: u.Unit,
        ycol: ColNum,
        yunit: u.Unit,
        columns: Iterable[str] | None,
        delimiter: str | None,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        resolution: int | None,
        lica_trim: bool | None,
        title: str | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
    ):
        self._markers = markers
        self._legends = labels
        self._title = title
        self._paths = paths
        self._yc = ycol
        self._xc = xcol
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._resol = resolution
        self._lica_trim = lica_trim
        self._ncol = 1
        self._ntab = len(paths)

    def build_tables(self) -> Tables:
        tables = list()
        for path in self._paths:
            table = self._build_one_resampled_table(path=path, yc=self._yc, yu=self._yunit)
            tables.append(table)
        self._tables = tables
        return tables

    def build_titles(self) -> Titles:
        return self._default_tables_title()

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        return self.group(self._markers)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = [table.meta["label"] for table in self._tables]
        return self.group(flat_legends)


class SingleTablesColumnsBuilder(Base):
    def __init__(
        self,
        paths: Sequence[str],
        xcol: ColNum,
        xunit: u.Unit,
        ycols: ColNums,
        yunit: u.Unit,
        title: str | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
        columns: Iterable[str] | None,
        delimiter: str | None,
        xlow: float | None,
        xhigh: float | None,
        lunit: u.Unit,
        lica_trim: bool | None,
    ):
        self._markers = markers
        self._legends = labels
        self._title = title
        self._paths = paths
        self._yycc = ycols
        self._xc = xcol
        self._xu = xunit
        self._yu = yunit
        self._xl = xlow
        self._xh = xhigh
        self._lu = lunit
        self._columns = columns
        self._delim = delimiter
        self._lica_trim = lica_trim
        self._ncol = len(ycols)
        self._ntab = len(paths)

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != len(self._tables):
            raise ValueError(
                "number of markers (%d) should match number of tables (%d)"
                % (len(self._markers), len(self._tables)),
            )

    def _check_legends(self) -> None:
        if self._legends is not None:
            nargs = len(self._legends)
            if not ((nargs == self._ncols) or (nargs == self._ntab)):
                raise ValueError(
                    "number of legends (%d) should match number of y-columns (%d)  or tables x y-columns (%d)"
                    % (nargs, self._ncols, self._ncols * self._ntab)
                )

    def build_tables(self) -> Tables:
        tables = list()
        for path in self._paths:
            table = self._build_one_table(path=path)
            tables.append(table)
        self._tables = tables
        return tables

    def build_titles(self) -> Titles:
        return self._default_tables_title()

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        return self.group(self._markers)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = [
            table.meta["label"] + "-" + table.columns[y].name[0:6] + "."
            for table in self._tables
            for y in self._yycc
        ]
        return self.group(flat_legends)
