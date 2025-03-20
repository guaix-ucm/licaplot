# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# -------------------
# System wide imports
# -------------------

from typing import Tuple, Optional, Sequence

# ---------------------
# Third-party libraries
# ---------------------


from astropy import visualization
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------

from .plotter import (
    Marker,
    Markers,
    Label,
    Legend,
    Legends,
    LineStyle,
    LineStyles,
    Tables,
    Title,
    Director,
    SingleTableColumnBuilder,
    SingleTableColumnsBuilder,
    SingleTablesColumnBuilder,
    SingleTablesMixedColumnsBuilder,
    TableWrapper,
    TablesWrapper,
    BasicPlotter,
    BoxPlotter,
)


def offset_box(x_offset: float, y_offset: float, x: float = 0.5, y: float = 0.2):
    return ("\n".join((f"x offset= {x_offset:.1f}", f"y offset = {y_offset:0.3f}")), x, y)


def plot_single_table_column(
    table: Table,
    xcolname: str,
    ycolname: str,
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    marker: Optional[Marker] = None,
    legend: Optional[Legend] = None,
    linestyle: Optional[LineStyle] = None,
    changes: bool = False,
) -> None:
    xcn = table.colnames.index(xcolname) + 1
    ycn = table.colnames.index(ycolname) + 1
    tb_builder = TableWrapper(
        table=table,
        xcn=xcn,
        ycn=ycn,
    )
    builder = SingleTableColumnBuilder(
        builder=tb_builder,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        legend=legend,
        marker=marker,
        linestyle=linestyle,
    )
    director = Director(builder)

    xcn, ycns_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BasicPlotter(
            xcn=xcn,
            ycns_grp=ycns_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=changes,
        )
        plotter.plot()


def plot_single_table_columns(
    table: Table,
    xcolname: str,
    ycolnames: Sequence[str],
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    markers: Optional[Markers] = None,
    legends: Optional[Legends] = None,
    linestyles: Optional[LineStyles] = None,
    changes: bool = False,
) -> None:
    if not (type(ycolnames) is list or type(ycolnames) is tuple):
        raise ValueError("ycolnames should be a tuple or list")
    xcn = table.colnames.index(xcolname) + 1
    ycns = [table.colnames.index(name) + 1 for name in ycolnames]
    tb_builder = TableWrapper(table=table, xcn=xcn, ycn=ycns)
    builder = SingleTableColumnsBuilder(
        builder=tb_builder,
        title=title,
        ylabel=ylabel,
        legends=legends,
        linestyles=linestyles,
    )
    director = Director(builder)
    xcn, ycns_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BasicPlotter(
            xcn=xcn,
            ycns_grp=ycns_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=changes,
        )
        plotter.plot()


def plot_single_tables_columns(
    tables: Tables,
    xcolname: str,
    ycolnames: Sequence[str],
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    legends: Optional[Legends] = None,
    markers: Optional[Markers] = None,
    linestyles: Optional[LineStyle] = None,
    changes: bool = False,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    if not (type(ycolnames) is list or type(ycolnames) is tuple):
        raise ValueError("ycolnames should be a tuple or list")
    if len(ycolnames) != len(tables):
        raise ValueError(
            "number of column names (%d) should mathc number of tables (%d)"
            % (len(ycolnames), len(tables))
        )
    xcn = tables[0].colnames.index(xcolname) + 1
    ycns = [table.colnames.index(name) + 1 for table, name in zip(tables, ycolnames)]
    if all(ycn == ycns[0] for ycn in ycns):
        tb_builder = TablesWrapper(tables=tables, xcn=xcn, ycn=ycns[0])
        builder = SingleTablesColumnBuilder(
            builder=tb_builder,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            legends=legends,
            markers=markers,
            linestyles=linestyles,
        )
    else:
        tb_builder = TablesWrapper(tables=tables, xcn=xcn, ycn=ycns)
        builder = SingleTablesMixedColumnsBuilder(
            builder=tb_builder,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            legends=legends,
            markers=markers,
            linestyles=linestyles,
        )
    director = Director(builder)
    xcn, ycns_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BoxPlotter(
            xcn=xcn,
            ycns_grp=ycns_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=changes,
            box=box,
        )
        plotter.plot()
