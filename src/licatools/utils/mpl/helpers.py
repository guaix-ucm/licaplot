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
    title: Title,
    marker: Optional[Marker] = None,
    legend: Optional[Legend] = None,
    linestyle: Optional[LineStyle] = None,
    changes: bool = False
) -> None:
    tb_builder = TableWrapper(table=table, xcol=x, ycol=y)
    builder = SingleTableColumnBuilder(
        builder=tb_builder,
        title=title,
        legend=legend,
        linestyle=linestyle,
    )
    director = Director(builder)
    xc, yc, tables, titles, legends_grp, markers_grp, linestyl_grp = director.build_elements()
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyl_grp,
            changes=changes,
        )
        plotter.plot()

def plot_single_table_columns(
    table: Table,
    x: ColNum,
    yy: ColNums,
    title: Title,
    markers: Optional[Markers] = None,
    legends: Optional[Legends] = None,
    linestyles: Optional[LineStyles] = None,
    changes: bool = False
) -> None:
    tb_builder = TableWrapper(table=table, xcol=x, ycol=yy)
    builder = SingleTableColumnsBuilder(
        builder=tb_builder,
        title=title,
        legends=legends,
        linestyles=linestyles,
    )
    director = Director(builder)
    xc, yc, tables, titles, legends_grp, markers_grp, linestyl_grp = director.build_elements()
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyl_grp,
            changes=changes,
        )
        plotter.plot()



def plot_single_tables_column(
    tables: Tables,
    x: ColNum,
    y: ColNum,
    title: Title,
    legends: Legends,
    markers: Optional[Markers] = None,
    linestyles: Optional[LineStyle] = None,
    changes: bool = False,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    tb_builder = TablesWrapper(tables=tables, xcol=x, ycol=y)
    builder = SingleTablesColumnBuilder(
        builder=tb_builder,
        title=title,
        legends=legends,
        markers=markers,
        linestyles=linestyles,
    )
    director = Director(builder)
    xc, yc, tables, titles, legends_grp, markers_grp, linestyl_grp = director.build_elements()
    with visualization.quantity_support():
        plotter = BoxPlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyl_grp,
            box=box,
        )
        plotter.plot()

