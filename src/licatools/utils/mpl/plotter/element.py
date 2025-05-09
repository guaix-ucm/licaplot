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
from typing import Sequence, Any, Optional

# ---------------------
# Third-party libraries
# ---------------------

from astropy.table import Table

# ---------
# Own stuff
# ---------

from .types import (
    ColNum,
    Title,
    Titles,
    Label,
    Labels,
    Legend,
    Legends,
    Marker,
    Markers,
    LineStyle,
    LineStyles,
    Tables,
    LegendsGroup,
    MarkersGroup,
    LineStylesGroup,
    Elements,
)

from .table import ITableBuilder
from ...table import tcn

# -----------------------
# Module global variables
# -----------------------


log = logging.getLogger(__name__)

class Director:
    """
    Ensures the differenct elements are constructed in a given order
    """

    def __init__(self, builder: IElementsBuilder) -> None:
        self._builder = builder

    def build_elements(self) -> Elements:
        self._builder.build_tables()
        self._builder.build_titles()
        self._builder.build_xlabels()
        self._builder.build_ylabels()
        self._builder.build_legends_grp()
        self._builder.build_markers_grp()
        self._builder.build_linestyles_grp()
        return self._builder.elements


class IElementsBuilder(ABC):
    @abstractmethod
    def build_titles(self) -> None:
        pass

    @abstractmethod
    def build_xlabels(self) -> None:
        pass

    @abstractmethod
    def build_ylabels(self) -> None:
        pass

    @abstractmethod
    def build_legends_grp(self) -> None:
        pass

    @abstractmethod
    def build_markers_grp(self) -> None:
        pass

    @abstractmethod
    def build_linestyles_grp(self) -> None:
        pass

    @abstractmethod
    def build_tables(self) -> None:
        pass


class ElementsBase(IElementsBuilder):
    """
    Useful methods to reuse in subclasses
    very simple constructor, just take advamntage of attributes late binding.
    """

    def __init__(self, builder: ITableBuilder):
        """
        A fresh builder instance should contain a blank elements object, which is
        used in further assembly.
        """
        self._elements = list()
        self._tb_builder = builder
        self._ncol = self._tb_builder.ncols()
        self._ntab = self._tb_builder.ntab()
        log.info("Using %s", self.__class__.__name__)

    @property
    def elements(self) -> Elements:
        """Convenient for the Director based building process"""
        elements = self._elements
        self._reset()
        return elements

    def _reset(self) -> None:
        self._elements = list()

    def _default_title(self, table: Table) -> Titles:
        if self._title is not None:
            result = self._title if isinstance(self._title, str) else " ".join(self._title)
        else:
            result = table.meta["title"]
        part = [result] * self._ntab
        self._elements.append(part)
        return part

    def _default_xlabel(self, table: Table) -> Labels:
        if self._xlabel is not None:
            result = self._xlabel if isinstance(self._xlabel, str) else " ".join(self._xlabel)
        else:
            result = tcn(table, self._xcn)
        part = [result] * self._ntab
        self._elements.append(part)
        return part

    def _default_ylabel(self, table: Table, y: ColNum) -> Labels:
        if self._ylabel is not None:
            result = self._ylabel if isinstance(self._ylabel, str) else " ".join(self._ylabel)
        else:
            result = tcn(table,y)
        part = [result] * self._ntab
        self._elements.append(part)
        return part

    def _default_tables_titles(self) -> Titles:
        if self._titles is not None:
            result = [self._titles] * self._ntab if isinstance(self._titles, str) else self._titles
        else:
            result = [table.meta["title"] for table in self._tables]
        part = result
        self._elements.append(part)
        return part

    def _default_tables_xlabels(self) -> Labels:
        if self._xlabels is not None:
            result = (
                [self._xlabels] * self._ntab if isinstance(self._xlabels, str) else self._xlabels
            )
        else:
            result = [tcn(table, self._xcn) for table in self._tables]
        part = result
        self._elements.append(part)
        return part

    def _default_tables_ylabels(self, ycn: ColNum) -> Labels:
        if self._ylabels is not None:
            result = (
                [self._ylabels] * self._ntab if isinstance(self._ylabels, str) else self._ylabels
            )
        else:
            result = [tcn(table, ycn) for table in self._tables]
        part = result
        self._elements.append(part)
        return part

    def _grouped(self, sequence: Sequence[Any], n: int) -> Sequence[Sequence[Any]]:
        return list(batched(sequence, n)) if sequence is not None else [(None,) * n] * self._ntab


class SingleTableColumnBuilder(ElementsBase):
    """
    Produces plotting elements to plot one Table in a single Axes.
    One X, one Y column to plot.

    TITLE
    Optional title can be specified and will be shown as the Figure title.
    If title is not specified, it is taken from the "title" Table metadata.

    Y-LABEL
    Optional Y label can be specified and will be shown as the Figure Y axes.
    If Y label is not specified, it is taken from the Y column name.

    LEGEND
    An optional legend can be specified and will be shown as legend in the plot.
    If a legend is not specified, it is is taken from the Y column name.

    MARKER
    An optional marker can be passed.
    """

    def __init__(
        self,
        builder: ITableBuilder,
        title: Optional[Title] = None,
        xlabel: Optional[Label] = None,
        ylabel: Optional[Label] = None,
        legend: Optional[Legend] = None,
        marker: Optional[Marker] = None,
        linestyle: LineStyle | None = None,
    ):
        super().__init__(builder)
        self._marker = marker
        self._linestyle = linestyle
        self._legend = legend
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        assert self._ncol == 1
        assert self._ntab == 1

    def _check_title(self) -> None:
        pass

    def _check_xlabel(self) -> None:
        pass

    def _check_ylabel(self) -> None:
        pass

    def _check_legends(self) -> None:
        if self._legend is not None and not isinstance(self._legend, str):
            raise ValueError(
                "legends be a simple string instead of %s" % type(self._legend),
            )

    def _check_markers(self) -> None:
        if self._marker is not None and not isinstance(self._marker, str):
            raise ValueError(
                "legends be a simple string instead of %s" % type(self._marker),
            )

    def _check_linestyles(self) -> None:
        if self._linestyle is not None and not isinstance(self._linestyle, str):
            raise ValueError(
                "legends be a simple string instead of %s" % type(self._linestyle),
            )

    def build_tables(self) -> Tables:
        self._table, self._xcn, self._ycn = self._tb_builder.build_tables()
        tables = [self._table]
        self._elements.extend([self._xcn, [(self._ycn,)], tables])
        return tables

    def build_titles(self) -> Titles:
        self._check_title()
        return self._default_title(self._table)

    def build_xlabels(self) -> Labels:
        self._check_xlabel()
        return self._default_xlabel(self._table)

    def build_ylabels(self) -> Labels:
        self._check_ylabel()
        return self._default_ylabel(self._table, self._ycn)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        part = [(self._legend,)] if self._legend is not None else [(None,)]
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        part = [(self._marker,)] if self._marker is not None else [(None,)]
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        part = [(self._linestyle,)] if self._linestyle is not None else [(None,)]
        self._elements.append(part)
        return part


class SingleTableColumnsBuilder(ElementsBase):
    """
    Produces plotting elements to plot one Table in a single Axes.
    One X, several Y columns to plot.

    TITLE
    Optional title can be specified and will be shown as the Figure title.
    If title is not specified, it is taken from the "title" Table metadata.

    Y-LABEL
    Optional Y label can be specified and will be shown as the Figure Y axes.
    If Y label is not specified, it is taken from the first Y column name.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from the Y column names.
    The number of legends must match the number of Y columns.

    MARKERS
    Optional markers can be passed.
    The number of markers must match the number of Y columns,
    """

    def __init__(
        self,
        builder: ITableBuilder,
        title: Optional[Title] = None,
        xlabel: Optional[Label] = None,
        ylabel: Optional[Label] = None,
        legends: Optional[Legends] = None,
        markers: Optional[Markers] = None,
        linestyles: Optional[LineStyles] = None,
        legend_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._linestyles = linestyles
        self._legends = legends
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._trim = legend_length
        assert self._ntab == 1

    def _check_title(self) -> None:
        pass

    def _check_xlabel(self) -> None:
        pass

    def _check_ylabel(self) -> None:
        pass

    def _check_legends(self) -> None:
        if self._legends is not None and len(self._legends) != self._ncol:
            raise ValueError(
                "number of legends (%d) should match number of y-columns (%d)"
                % (len(self._legends), self._ncol),
            )

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != self._ncol:
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d)"
                % (len(self._markers), self._ncol)
            )

    def _check_linestyles(self) -> None:
        if self._linestyles is not None and len(self._linestyles) != self._ncol:
            raise ValueError(
                "number of linestyles (%d) should match number of y-columns (%d)"
                % (len(self._linestyles), self._ncol)
            )

    def build_tables(self) -> Tables:
        self._table, self._xcn, self._ycns = self._tb_builder.build_tables()
        tables = [self._table]
        ycns_group = [tuple(ycn for ycn in self._ycns)]
        self._elements.extend([self._xcn, ycns_group, tables])
        return tables

    def build_titles(self) -> Titles:
        self._check_title()
        return self._default_title(self._table)

    def build_xlabels(self) -> Labels:
        self._check_xlabel()
        return self._default_xlabel(self._table)

    def build_ylabels(self) -> Labels:
        self._check_ylabel()
        return self._default_ylabel(self._table, self._ycns[0])

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            self._legends
            if self._legends is not None
            else [tcn(self._table, ycn)[: self._trim] + "." for ycn in self._ycns]
        )
        part = self._grouped(flat_legends, n=self._ncol)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        part = self._grouped(self._markers, n=self._ncol)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        part = self._grouped(self._linestyles, n=self._ncol)
        self._elements.append(part)
        return part


class SingleTablesColumnBuilder(ElementsBase):
    """
    Produces plotting elements to plot several Tables in a single Axes.
    One X, one Y column per table to plot.

    TITLE
    Optional title can be specified and will be shown as the Figure title.
    If title is not specified, it is taken from the first table "title" metadata.

    Y-LABEL
    Optional Y label can be specified and will be shown as the Figure Y axes.
    If Y label is not specified, it is taken from the Y column name of the first table.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from each table "label" metadata and Y column name.
    The number of passed legends must match:
        - either the number the number of tables
        - or simply the number of columns (=1). In this case, the legends will be replicated across tables.

    MARKERS
    Optional markers can be passed.
    The number of passed markers must match:
        - either the number of Y columns (=1) times the number of tables
        - or simply the number of columns. In this case, the legends will be replicated across tables.
    """

    def __init__(
        self,
        builder: ITableBuilder,
        title: Optional[Title] = None,
        xlabel: Optional[Label] = None,
        ylabel: Optional[Label] = None,
        legends: Optional[Legends] = None,
        markers: Optional[Markers] = None,
        linestyles: Optional[LineStyles] = None,
    ):
        super().__init__(builder)
        self._markers = markers
        self._linestyles = linestyles
        self._legends = legends
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        assert self._ncol == 1

    def _check_title(self) -> None:
        pass

    def _check_xlabel(self) -> None:
        pass

    def _check_ylabel(self) -> None:
        pass

    def _check_legends(self) -> None:
        if self._legends is not None and not (
            len(self._legends) == self._ntab or len(self._legends) == 1
        ):
            raise ValueError(
                "number of legends (%d) should either match number of tables (%d) or be 1"
                % (len(self._legends), self._ntab),
            )

    def _check_markers(self) -> None:
        if self._markers is not None and not (
            len(self._markers) == self._ntab or len(self._markers) == 1
        ):
            raise ValueError(
                "number of markers (%d) should either match number of tables (%d) or be 1"
                % (len(self._markers), self._ntab)
            )

    def _check_linestyles(self) -> None:
        if self._linestyles is not None and not (
            len(self._linestyles) == self._ntab or len(self._linestyles) == 1
        ):
            raise ValueError(
                "number of linestyles (%d) should either match number of tables (%d) or be 1"
                % (len(self._linestyles), self._ntab)
            )

    def build_tables(self) -> Tables:
        self._tables, self._xcn, self._ycn = self._tb_builder.build_tables()
        ycns_group = [(self._ycn,) for t in self._tables]
        self._elements.extend([self._xcn, ycns_group, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_title()
        return self._default_title(self._tables[0])

    def build_xlabels(self) -> Labels:
        self._check_xlabel()
        return self._default_xlabel(self._tables[0])

    def build_ylabels(self) -> Labels:
        self._check_ylabel()
        return self._default_ylabel(self._tables[0], self._ycn)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        if self._legends is not None:
            N = len(self._legends)
            flat_legends = self._legends * self._ntab if N == 1 else self._legends
        else:
            flat_legends = [table.meta["label"] for table in self._tables]
        part = self._grouped(flat_legends, n=self._ncol)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        if self._markers is not None:
            N = len(self._markers)
            flat_markers = self._markers * self._ntab if N == 1 else self._markers
        else:
            flat_markers = [None] * self._ntab
        part = self._grouped(flat_markers, n=self._ncol)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        if self._linestyles is not None:
            N = len(self._linestyles)
            flat_linestyles = self._linestyles * self._ntab if N == 1 else self._linestyles
        else:
            flat_linestyles = [None] * self._ntab
        part = self._grouped(flat_linestyles, n=self._ncol)
        self._elements.append(part)
        return part


# Less useful variant
class SingleTablesColumnsBuilder(ElementsBase):
    """
    Produces plotting elements to plot several Tables in a single Axes.
    One X, several Y columns per table to plot.

    TITLE
    Optional title can be specified and will be shown as the Figure title.
    If title is not specified, it is taken from the first table "title" metadata.

    Y-LABEL
    Optional Y label can be specified and will be shown as the Figure Y axes.
    If Y label is not specified, it is taken from the firs tY column name of the first table.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from each table "label" metadata and Y column names.
    The number of passed legends must match:
        - either the number of Y columns times the number of tables
        - or simply the number of columns. In this case, the legends will be replicated across tables.
    On output, they:
        - will passed back grouped by tables if they are NTAB x NCOL
        - Will be replicated across tables

    MARKERS
    Optional markers can be passed.
    The number of passed markers must match:
        - either the number of Y columns times the number of tables
        - or simply the number of columns. In this case, the legends will be replicated across tables.
    On output, they:
        - will passed back grouped by tables if they are NTAB x NCOL
        - Will be replicated across tables
    """

    def __init__(
        self,
        builder: ITableBuilder,
        title: Optional[Title] = None,
        xlabel: Optional[Label] = None,
        ylabel: Optional[Label] = None,
        legends: Optional[Legends] = None,
        markers: Optional[Markers] = None,
        linestyles: Optional[LineStyles] = None,
        legend_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._linestyles = linestyles
        self._legends = legends
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._trim = legend_length

    def _check_title(self) -> None:
        pass

    def _check_xlabel(self) -> None:
        pass

    def _check_ylabel(self) -> None:
        pass

    def _check_legends(self) -> None:
        if self._legends is not None:
            nargs = len(self._legends)
            if not ((nargs == self._ncol) or (nargs == self._ntab * self._ncol)):
                raise ValueError(
                    "number of legends (%d) should match number of tables x Y-columns (%d) or the number of Y-columns (%d)"
                    % (nargs, self._ncol * self._ntab, self._ncol)
                )

    def _check_markers(self) -> None:
        if self._markers is not None:
            nargs = len(self._markers)
            if not ((nargs == self._ncol) or (nargs == self._ntab * self._ncol)):
                raise ValueError(
                    "number of markers (%d) should match number of tables x Y-columns (%d) or the number of Y-columns (%d)"
                    % (nargs, self._ncol * self._ntab, self._ncol)
                )

    def _check_linestyles(self) -> None:
        if self._linestyles is not None:
            nargs = len(self._linestyles)
            if not ((nargs == self._ncol) or (nargs == self._ntab * self._ncol)):
                raise ValueError(
                    "number of linestyles (%d) should match number of tables x Y-columns (%d) or the number of Y-columns (%d)"
                    % (nargs, self._ncol * self._ntab, self._ncol)
                )

    def build_tables(self) -> Tables:
        self._tables, self._xcn, self._ycns = self._tb_builder.build_tables()
        ycns_group = [tuple(self._ycns) for t in self._tables]
        self._elements.extend([self._xcn, ycns_group, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_title()
        return self._default_title(self._tables[0])

    def build_xlabels(self) -> Labels:
        self._check_ylabel()
        return self._default_xlabel(self._tables[0])

    def build_ylabels(self) -> Labels:
        self._check_ylabel()
        return self._default_ylabel(self._tables[0], self._ycns[0])

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        if self._legends is not None:
            N = len(self._legends)
            flat_legends = self._legends * self._ntab if N == self._ncol else self._legends
        else:
            flat_legends = [
                table.meta["label"] + "-" + tcn(table, ycn)[: self._trim] + "."
                for table in self._tables
                for ycn in self._ycns
            ]
        part = self._grouped(flat_legends, n=self._ncol)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        if self._markers is not None:
            N = len(self._markers)
            flat_markers = self._markers * self._ntab if N == self._ncol else self._markers
        else:
            flat_markers = (None,) * (self._ntab * self._ncol)
        part = self._grouped(flat_markers, n=self._ncol)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        if self._linestyles is not None:
            N = len(self._linestyles)
            flat_linestyles = self._linestyles * self._ntab if N == self._ncol else self._linestyles
        else:
            flat_linestyles = (None,) * (self._ntab * self._ncol)
        part = self._grouped(flat_linestyles, n=self._ncol)
        self._elements.append(part)
        return part


class SingleTablesMixedColumnsBuilder(ElementsBase):
    """
    Produces plotting elements to plot several Tables in a single Axes.
    One X, several Y columns (one Y columns pe table) to plot.

    TABLES & COLUMNS
    A spe cial check is made to ensure that the numbr of columns passed
    equals the number of tables

    TITLE
    Optional title can be specified and will be shown as the Figure title.
    If title is not specified, it is taken from the first table "title" metadata.

    Y-LABEL
    Optional Y label can be specified and will be shown as the Figure Y axes.
    If Y label is not specified, it is taken from the first Y column name of the first table.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from each table "label" metadata and Y column names.
    The number of passed legends must match:
        - the number of tables
    On output, they:
        - will passed back grouped by tables, one element each

    MARKERS
    Optional markers can be passed.
    The number of passed markers must match:
        - the number of tables
    On output, they:
        - will passed back grouped by tables, one element each
    """

    def __init__(
        self,
        builder: ITableBuilder,
        title: Optional[Title] = None,
        xlabel: Optional[Label] = None,
        ylabel: Optional[Label] = None,
        legends: Optional[Legends] = None,
        markers: Optional[Markers] = None,
        linestyles: Optional[LineStyles] = None,
        legend_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._linestyles = linestyles
        self._legends = legends
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._trim = legend_length

    def _check_title(self) -> None:
        pass

    def _check_xlabel(self) -> None:
        pass

    def _check_ylabel(self) -> None:
        pass

    def _check_legends(self) -> None:
        if self._legends is not None:
            nargs = len(self._legends)
            if not (nargs == self._ntab):
                raise ValueError(
                    "number of legends (%d) should match number of tables (%d)"
                    % (nargs, self._ntab)
                )

    def _check_markers(self) -> None:
        if self._markers is not None:
            nargs = len(self._markers)
            if not (nargs == self._ntab):
                raise ValueError(
                    "number of markers (%d) should match number of tables (%d)"
                    % (nargs, self._ntab)
                )

    def _check_linestyles(self) -> None:
        if self._linestyles is not None:
            nargs = len(self._linestyles)
            if not (nargs == self._ntab):
                raise ValueError(
                    "number of linestyles (%d) should match number of tables (%d)"
                    % (nargs, self._ntab)
                )

    def build_tables(self) -> Tables:
        self._tables, self._xcn, self._ycns = self._tb_builder.build_tables()
        if self._ntab != self._ncol:
            raise ValueError(
                "number of Y columns (%d) should match number of tables (%d)"
                % (self._ncol, self._ntab)
            )
        ycns_group = [(y,) for y in self._ycns]
        self._elements.extend([self._xcn, ycns_group, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_title()
        return self._default_title(self._tables[0])

    def build_xlabels(self) -> Labels:
        self._check_xlabel()
        return self._default_xlabel(self._tables[0])

    def build_ylabels(self) -> Labels:
        self._check_ylabel()
        return self._default_ylabel(self._tables[0], self._ycns[0])

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        if self._legends is not None:
            flat_legends = self._legends
        else:
            flat_legends = [
                f"{table.meta['label']}-{tcn(table,ycn)[: self._trim]}."
                for table, ycn in zip(self._tables, self._ycns)
            ]
        part = self._grouped(flat_legends, n=1)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        flat_markers = self._markers if self._markers is not None else (None,) * self._ntab
        part = self._grouped(flat_markers, n=1)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        flat_linestyles = self._linestyles if self._linestyles is not None else (None,) * self._ntab
        part = self._grouped(flat_linestyles, n=1)
        self._elements.append(part)
        return part


class MultiTablesColumnBuilder(ElementsBase):
    """
    Produces plotting elements to plot several Tables in a several Axes, one table per Axes.
    One X, one Y column per table to plot in each Axes.

    TITLES
    Optional titles can be specified and will be shown as Axes titles.
    If titles are not specified, they are taken from the each table "title" metadata.
    If titles are specified, they must match the number of tables.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from each table Y column names.
    The number of passed legends must match the number of Y columns.
    On output, they will be replicated for each table

    MARKERS
    Optional markers can be passed.
    The number of passed markers must match the number of Y columns.
    On output, they will be replicated for each table
    """

    def __init__(
        self,
        builder: ITableBuilder,
        titles: Optional[Titles] = None,
        xlabels: Optional[Labels] = None,
        ylabels: Optional[Labels] = None,
        legend: Optional[Legend] = None,
        marker: Optional[Marker] = None,
        linestyle: LineStyle | None = None,
        legend_length: int = 6,
    ):
        super().__init__(builder)
        self._tb_builder = builder
        self._marker = marker
        self._linestyle = linestyle
        self._legend = legend
        self._titles = titles
        self._xlabels = xlabels
        self._ylabels = ylabels
        self._trim = legend_length

    def _check_titles(self) -> None:
        if self._titles is not None and len(self._titles) != self._ntab:
            raise ValueError(
                "number of titles (%d) should match number of tables (%d)"
                % (len(self._titles), self._ntab),
            )

    def _check_xlabels(self) -> None:
        if self._xlabels is not None and len(self._xlabels) != self._ntab:
            raise ValueError(
                "number of X labels (%d) should match number of tables (%d)"
                % (len(self._xlabels), self._ntab),
            )

    def _check_ylabels(self) -> None:
        if self._ylabels is not None and len(self._ylabels) != self._ntab:
            raise ValueError(
                "number of Y labels (%d) should match number of tables (%d)"
                % (len(self._ylabels), self._ntab),
            )

    def _check_legends(self) -> None:
        if self._legend is not None and not isinstance(self._legend, str):
            raise ValueError(
                "legends be a simple string instead of %s" % type(self._legend),
            )

    def _check_markers(self) -> None:
        pass

    def _check_linestyles(self) -> None:
        pass

    def build_tables(self) -> Tables:
        self._tables, self._xcn, self._ycn = self._tb_builder.build_tables()
        ycns_group = [(self._ycn,) for t in self._tables]
        self._elements.extend([self._xcn, ycns_group, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_titles()
        return self._default_tables_titles()

    def build_xlabels(self) -> Labels:
        self._check_xlabels()
        return self._default_tables_xlabels()

    def build_ylabels(self) -> Labels:
        self._check_ylabels()
        return self._default_tables_ylabels(self._ycn)

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            [tcn(table, self._ycn)[: self._trim] + "." for table in self._tables]
            if self._legend is None
            else [self._legend] * self._ntab
        )
        part = self._grouped(flat_legends, n=self._ncol)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        flat_markers = [self._marker] * self._ntab
        part = self._grouped(flat_markers, n=self._ncol)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        flat_linestyles = [self._linestyle] * self._ntab
        part = self._grouped(flat_linestyles, n=self._ncol)
        self._elements.append(part)
        return part


class MultiTablesColumnsBuilder(ElementsBase):
    """
    Produces plotting elements to plot several Tables in a several Axes, one table per Axes.
    One X, several Y columns per table to plot in each Axes.

    TITLES
    Optional titles can be specified and will be shown as Axes titles.
    If titles are not specified, they are taken from the each table "title" metadata.
    If titles are specified, they must match the number of tables.

    LEGENDS
    Optional legends can be specified and will be shown as legends in the plot.
    If legends are not specified, they are taken from each table Y column names.
    The number of passed legends must match the number of tables.
    On output, they will be replicated for each table

    MARKERS
    Optional markers can be passed.
    The number of passed markers must match the number of tables.
    On output, they will be replicated for each table
    """

    def __init__(
        self,
        builder: ITableBuilder,
        titles: Optional[Titles] = None,
        xlabels: Optional[Label] = None,
        ylabels: Optional[Labels] = None,
        legends: Optional[Legends] = None,
        markers: Optional[Markers] = None,
        linestyles: Optional[LineStyles] = None,
        legend_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._linestyles = linestyles
        self._legends = legends
        self._titles = titles
        self._xlabels = xlabels
        self._ylabels = ylabels
        self._trim = legend_length

    def _check_titles(self) -> None:
        if self._titles is not None and len(self._titles) != self._ntab:
            raise ValueError(
                "number of titles (%d) should match number of tables (%d)"
                % (len(self._titles), self._ntab),
            )

    def _check_xlabels(self) -> None:
        if self._xlabels is not None and len(self._xlabels) != self._ntab:
            raise ValueError(
                "number of X labels (%d) should match number of tables (%d)"
                % (len(self._xlabels), self._ntab),
            )

    def _check_ylabels(self) -> None:
        if self._ylabels is not None and len(self._ylabels) != self._ntab:
            raise ValueError(
                "number of Y labels (%d) should match number of tables (%d)"
                % (len(self._ylabels), self._ntab),
            )

    def _check_legends(self) -> None:
        if self._legends is not None and len(self._legends) != self._ncol:
            raise ValueError(
                "number of legends (%d) should match number of y-columns (%d)"
                % (len(self._legends), self._ncol),
            )

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != self._ncol:
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d)"
                % (len(self._markers), self._ncol)
            )

    def _check_linestyles(self) -> None:
        if self._linestyles is not None and len(self._linestyles) != self._ncol:
            raise ValueError(
                "number of linestyles (%d) should match number of y-columns (%d)"
                % (len(self._linestyles), self._ncol)
            )

    def build_tables(self) -> Tables:
        self._tables, self._xcn, self._ycns = self._tb_builder.build_tables()
        ycns_group = [tuple(self._ycns) for t in self._tables]
        self._elements.extend([self._xcn, ycns_group, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_titles()
        return self._default_tables_titles()

    def build_xlabels(self) -> Labels:
        self._check_xlabels()
        return self._default_tables_xlabels()

    def build_ylabels(self) -> Labels:
        self._check_ylabels()
        return self._default_tables_ylabels(self._ycns[0])

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            [
                tcn(table,ycn)[: self._trim] + "."
                for table in self._tables
                for ycn in self._ycns
            ]
            if self._legends is None
            else self._legends * self._ntab
        )
        part = self._grouped(flat_legends, n=self._ncol)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        flat_markers = [None, None] if self._markers is None else self._markers
        flat_markers = flat_markers * self._ntab
        part = self._grouped(flat_markers, n=self._ncol)
        self._elements.append(part)
        return part

    def build_linestyles_grp(self) -> LineStylesGroup:
        self._check_linestyles()
        flat_linestyles = [None, None] if self._linestyles is None else self._linestyles
        flat_linestyles = flat_linestyles * self._ntab
        part = self._grouped(flat_linestyles, n=self._ncol)
        self._elements.append(part)
        return part
