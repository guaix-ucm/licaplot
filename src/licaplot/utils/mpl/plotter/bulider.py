from abc import ABC, abstractmethod
from itertools import batched

from astropy.table import Table
from .types import Markers, ColNum, ColNums, Legends, Tables, Titles, LegendsGroup, MarkersGroup


class IBuilder(ABC):
    @abstractmethod
    def build_legends_grp(self) -> LegendsGroup:
        pass

    @abstractmethod
    def build_markers_grp(self) -> MarkersGroup:
        pass

    @abstractmethod
    def build_titles(self) -> Titles:
        pass


class Base(IBuilder):
    # -------------------------------------------------
    # Useful methods to reuse / override in sublclasses
    # -------------------------------------------------

    @abstractmethod
    def check(self) -> None:
        pass

    def default_table_legends(self) -> Legends:
        return (
            self.args_legends
            if self.args_legends is not None
            else [self.table.columns[y - 1].name[:6] + "." for y in self.ycols]
        )

    def default_table_markers(self) -> Markers:
        return self.args_markers

    def build_legends_grp(self) -> LegendsGroup:
        return (
            list(batched(self.legends, self.ncol))
            if self.legends is not None
            else [[None] * self.ncol] * self.ntab
        )

    def build_markers_grp(self) -> MarkersGroup:
        return (
            list(batched(self.markers, self.ncol))
            if self.markers is not None
            else [[None] * self.ncol] * self.ntab
        )

    def default_single_title(self) -> Titles:
        return [
            " ".join(self.args_title) if self.args_title is not None else self.table.meta["title"]
        ]


class SingleTableColumnBuilder(Base):
    def __init__(
        self,
        args_title: str | None,
        args_label: str | None,
        args_marker: str | None,
        table: Table,
        ycol: ColNum,
    ):
        self.args_marker = args_marker
        self.args_legend = args_label
        self.args_title = args_title
        self.table = table
        self.ycol = ycol
        self.ncol = 1
        self.ntab = 1

    def build_titles(self) -> Titles:
        return self.default_single_title()

    def build_legends_grp(self) -> LegendsGroup:
        return [[self.args_legend]] if self.args_legend is not None else [[None]]

    def build_markers_grp(self) -> MarkersGroup:
        return [[self.args_marker]] if self.args_marker is not None else [[None]]


class SingleTableColumnsBuilder(Base):
    def __init__(
        self,
        args_title: str | None,
        args_labels: str | None,
        args_markers: str | None,
        table: Table,
        ycols: ColNums,
    ):
        self.args_markers = args_markers
        self.args_legends = args_labels
        self.args_title = args_title
        self.table = table
        self.ycols = ycols
        self.ncol = len(ycols)
        self.ntab = 1
        self.check()
        self.legends = self.default_table_legends()
        self.markers = self.default_table_markers()

    def check(self) -> None:
        if self.args_labels is not None and len(self.args_labels) != len(self.ycols):
            raise ValueError(
                "number of labels (%d) should match number of y-columns (%d)"
                % (len(self.args_labels), len(self.ycols)),
            )
        if self.args_markers is not None and len(self.args_markers) != len(self.ycols):
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d)"
                % (
                    len(self.args_markers),
                    len(self.ycols),
                )
            )

    def build_titles(self) -> Titles:
        return self.default_single_title()

class SingleTablesColumnBuilder(Base):
    def __init__(
        self,
        args_title: str | None,
        args_labels: str | None,
        args_markers: str | None,
        tables: Table,
        ycol: ColNums,
    ):
        self.args_markers = args_markers
        self.args_legends = args_labels
        self.args_title = args_title
        self.tables = tables
        self.ycol = ycol
        self.ncol = 1
        self.ntab = len(tables)
        self.check()
        self.legends = self.default_table_legends()
        self.markers = self.default_table_markers()

    def check(self) -> None:
        raise NotImplementedError()
        
    def default_tables_legends(self) -> Legends:
        return [table.meta["label"] for table in self.tables]

    def default_tables_markers(self) -> Legends:
        return self.args_markers






def single_tables_column_markers(
    args_marker: str, tables: Sequence[Table], col: int
) -> Sequence[str]:
    if args_marker is not None and len(args_marker) != len(tables):
        raise ValueError(
            "number of markers (%d) should match number of tables (%d)"
            % (len(args_marker), len(tables)),
        )
    return args_marker


def single_tables_column_title(args_title: str, tables: Sequence[Table], col: int) -> str | None:
    return " ".join(args_title) if args_title is not None else tables[0].meta["title"]


