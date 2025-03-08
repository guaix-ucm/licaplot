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

from typing import Tuple, Optional

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
    ColNum,
    ColNums,
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
    x: ColNum,
    y: ColNum,
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    marker: Optional[Marker] = None,
    legend: Optional[Legend] = None,
    linestyle: Optional[LineStyle] = None,
    changes: bool = False,
) -> None:
    tb_builder = TableWrapper(table=table, xcol=x, ycol=y)
    builder = SingleTableColumnBuilder(
        builder=tb_builder,
        title=title,
        ylabel=ylabel,
        legend=legend,
        linestyle=linestyle,
    )
    director = Director(builder)
    xc, yc_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yc_grp=yc_grp,
            tables=tables,
            titles=titles,
            xlabels=ylabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=changes,
        )
        plotter.plot()


def plot_single_table_columns(
    table: Table,
    x: ColNum,
    yy: ColNums,
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    markers: Optional[Markers] = None,
    legends: Optional[Legends] = None,
    linestyles: Optional[LineStyles] = None,
    changes: bool = False,
) -> None:
    tb_builder = TableWrapper(table=table, xcol=x, ycol=yy)
    builder = SingleTableColumnsBuilder(
        builder=tb_builder,
        title=title,
        ylabel=ylabel,
        legends=legends,
        linestyles=linestyles,
    )
    director = Director(builder)
    xc, yc_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yc_grp=yc_grp,
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


def plot_single_tables_column(
    tables: Tables,
    x: ColNum,
    y: ColNum,
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    legends: Optional[Legends] = None,
    markers: Optional[Markers] = None,
    linestyles: Optional[LineStyle] = None,
    changes: bool = False,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    tb_builder = TablesWrapper(tables=tables, xcol=x, ycol=y)
    builder = SingleTablesColumnBuilder(
        builder=tb_builder,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        legends=legends,
        markers=markers,
        linestyles=linestyles,
    )
    director = Director(builder)
    xc, yc_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BoxPlotter(
            x=xc,
            yc_grp=yc_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            box=box,
        )
        plotter.plot()


def plot_single_tables_mixed_columns(
    tables: Tables,
    x: ColNum,
    yy: ColNums,
    title: Optional[Title] = None,
    xlabel: Optional[Label] = None,
    ylabel: Optional[Label] = None,
    legends: Optional[Legends] = None,
    markers: Optional[Markers] = None,
    linestyles: Optional[LineStyle] = None,
    changes: bool = False,
) -> None:
    tb_builder = TablesWrapper(tables=tables, xcol=x, ycol=yy)
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
    xc, yc_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = (
        director.build_elements()
    )
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yc_grp=yc_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
        )
        plotter.plot()
