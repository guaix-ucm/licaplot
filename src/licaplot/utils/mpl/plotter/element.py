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
from typing import Sequence, Any

# ---------------------
# Third-party libraries
# ---------------------

# ---------
# Own stuff
# ---------

from .types import (
    Title,
    Titles,
    Legend,
    Legends,
    Markers,
    MarkerSeq,
    Tables,
    LegendsGroup,
    MarkersGroup,
    Elements,
)

from .table import ITableBuilder

# -----------------------
# Module global variables
# -----------------------


log = logging.getLogger(__name__)


class Director:
    """
    Ensures the differenct elements are constructed in a given order
    """

    def __init__(self) -> None:
        self._builder = None

    @property
    def builder(self) -> IElementsBuilder:
        return self._builder

    @builder.setter
    def builder(self, builder: IElementsBuilder) -> None:
        self._builder = builder

    def build_elements(self) -> Elements:
        self._builder.build_tables()
        self._builder.build_titles()
        self._builder.build_legends_grp()
        self._builder.build_markers_grp()
        return self._builder.elements


class IElementsBuilder(ABC):
    @abstractmethod
    def build_titles(self) -> None:
        pass

    @abstractmethod
    def build_legends_grp(self) -> None:
        pass

    @abstractmethod
    def build_markers_grp(self) -> None:
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

    @property
    def elements(self) -> Elements:
        """Convenient for the Director based building process"""
        elements = self._elements
        self._reset()
        return elements

    def _reset(self) -> None:
        self._elements = list()

    def _default_table_title(self) -> Titles:
        if self._title is not None:
            result = self._title if isinstance(self._title, str) else " ".join(self._title)
        else:
            result = self._table.meta["title"]
        part = [result]
        self._elements.append(part)
        return part

    def _default_tables_title(self) -> Titles:
        if self._title is not None:
            result = self._title if isinstance(self._title, str) else " ".join(self._title)
        else:
            result = self._tables[0].meta["title"]
        part = [result]
        self._elements.append(part)
        return part

    def _default_tables_titles(self) -> Titles:
        if self._titles is not None:
            result = (
                [self._titles] * self._ntab
                if isinstance(self._default_tables_titles, str)
                else self._titles
            )
        else:
            result = [table.meta["title"] for table in self._tables]
        part = result
        self._elements.append(part)
        return part

    def _check_titles(self) -> None:
        if self._titles is not None and len(self._titles) != self._ntab:
            raise ValueError(
                "number of titles (%d) should match number of tables (%d)"
                % (len(self._titles), self._ntab),
            )

    def _check_legends(self) -> None:
        if self._legends is not None and len(self._legends) != self._ncol:
            raise ValueError(
                "number of labels (%d) should match number of y-columns (%d)"
                % (len(self._legends), self._ncol),
            )

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != self._ncol:
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d)"
                % (len(self._markers), self._ncol)
            )

    def _grouped(self, sequence: Sequence[Any]) -> Sequence[Sequence[Any]]:
        return (
            list(batched(sequence, self._ncol))
            if sequence is not None
            else [[None] * self._ncol] * self._ntab
        )

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        part = self._grouped(self._markers)
        self._elements.append(part)
        return part


class SingleTableColumnBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        title: Title | None,
        label: Legend | None,
        marker: Markers | None,
    ):
        super().__init__(builder)
        self._marker = marker
        self._legend = label
        self._title = title
        assert self._ncol == 1
        assert self._ntab == 1

    def build_tables(self) -> Tables:
        self._table, self._xcol, self._ycol = self._tb_builder.build_tables()
        tables = [self._table]
        self._elements.extend([self._xcol, [self._ycol], tables])
        return tables

    def build_titles(self) -> Titles:
        return self._default_table_title()

    def build_markers_grp(self) -> MarkersGroup:
        part = [[self._marker]] if self._marker is not None else [[None]]
        self._elements.append(part)
        return part

    def build_legends_grp(self) -> LegendsGroup:
        part = [[self._legend]] if self._legend is not None else [[None]]
        self._elements.append(part)
        return part


class SingleTableColumnsBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        title: Title | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
        label_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._legends = labels
        self._title = title
        self._trim = label_length
        assert self._ntab == 1

    def build_tables(self) -> Tables:
        self._table, self._xcol, self._ycols = self._tb_builder.build_tables()
        tables = [self._table]
        self._elements.extend([self._xcol, self._ycols, tables])
        return tables

    def build_titles(self) -> Titles:
        return self._default_table_title()

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            self._legends
            if self._legends is not None
            else [self._table.columns[y].name[: self._trim] + "." for y in self._ycols]
        )
        part = self._grouped(flat_legends)
        self._elements.append(part)
        return part


class SingleTablesColumnBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        title: Title | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
    ):
        super().__init__(builder)
        self._markers = markers
        self._legends = labels
        self._title = title
        assert self._ncol == 1

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != self._ntab:
            raise ValueError(
                "number of markers (%d) should match number of tables (%d)"
                % (len(self._markers), self._ntab)
            )

    def _check_legends(self) -> None:
        if self._legends is not None and len(self._legends) != self._ntab:
            raise ValueError(
                "number of labels (%d) should match number of tables (%d)"
                % (len(self._legends), self._ntab),
            )

    def build_tables(self) -> Tables:
        self._tables, self._xcol, self._ycol = self._tb_builder.build_tables()
        self._elements.extend([self._xcol, [self._ycol], self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        return self._default_tables_title()

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            self._legends
            if self._legends is not None
            else [table.meta["label"] for table in self._tables]
        )
        part = self._grouped(flat_legends)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        flat_markers = self._markers if self._markers is not None else [None] * self._ntab
        part = self._grouped(flat_markers)
        self._elements.append(part)
        return part


# Less usefull variant
class SingleTablesColumnsBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        title: Title | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
        label_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._legends = labels
        self._title = title
        self._trim = label_length

    def _check_markers(self) -> None:
        if self._markers is not None and len(self._markers) != len(self._tables):
            raise ValueError(
                "number of markers (%d) should match number of tables (%d)"
                % (len(self._markers), len(self._tables)),
            )

    def _check_legends(self) -> None:
        if self._legends is not None:
            nargs = len(self._legends)
            if not ((nargs == self._ncol) or (nargs == self._ntab)):
                raise ValueError(
                    "number of legends (%d) should match number of y-columns (%d)  or tables x y-columns (%d)"
                    % (nargs, self._ncol, self._ncol * self._ntab)
                )

    def build_tables(self) -> Tables:
        self._tables, self._xcol, self._ycols = self._tb_builder.build_tables()
        self._elements.extend([self._xcol, self._ycols, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        return self._default_tables_title()

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        part = self._grouped(self._markers)
        self._elements.append(part)
        return part

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = [
            table.meta["label"] + "-" + table.columns[y].name[: self._trim] + "."
            for table in self._tables
            for y in self._ycols
        ]
        part = self._grouped(flat_legends)
        self._elements.append(part)
        return part


class MultiTablesColumnBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        titles: Titles | None,
        label: Legend | None,
        marker: Markers | None,
        label_length: int = 6,
    ):
        super().__init__(builder)
        self._tb_builder = builder
        self._marker = marker
        self._legend = label
        self._titles = titles
        self._trim = label_length

    def build_tables(self) -> Tables:
        self._tables, self._xcol, self._ycol = self._tb_builder.build_tables()
        self._elements.extend([self._xcol, [self._ycol], self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_titles()
        return self._default_tables_titles()

    def build_markers_grp(self) -> MarkersGroup:
        part = self._grouped(self._marker)
        self._elements.append(part)
        return part

    def build_legends_grp(self) -> LegendsGroup:
        flat_legends = (
            [table.columns[self._ycol].name[: self._trim] + "." for table in self._tables]
            if self._legend is None
            else [self._legend] * self._ntab
        )
        part = self._grouped(flat_legends)
        self._elements.append(part)
        return part


class MultiTablesColumnsBuilder(ElementsBase):
    def __init__(
        self,
        builder: ITableBuilder,
        titles: Titles | None,
        labels: Legends | None,
        markers: MarkerSeq | None,
        label_length: int = 6,
    ):
        super().__init__(builder)
        self._markers = markers
        self._legends = labels
        self._titles = titles
        self._trim = label_length

    def build_tables(self) -> Tables:
        self._tables, self._xcol, self._ycols = self._tb_builder.build_tables()
        self._elements.extend([self._xcol, self._ycols, self._tables])
        return self._tables

    def build_titles(self) -> Titles:
        self._check_titles()
        return self._default_tables_titles()

    def build_legends_grp(self) -> LegendsGroup:
        self._check_legends()
        flat_legends = (
            [
                table.columns[y].name[: self._trim] + "."
                for table in self._tables
                for y in self._ycols
            ]
            if self._legends is None
            else self._legends * self._ntab
        )
        part = self._grouped(flat_legends)
        self._elements.append(part)
        return part

    def build_markers_grp(self) -> MarkersGroup:
        self._check_markers()
        part = self._grouped(self._markers)
        self._elements.append(part)
        return part
