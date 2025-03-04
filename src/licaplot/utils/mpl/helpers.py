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

from typing import Tuple

# ---------------------
# Third-party libraries
# ---------------------

from astropy import visualization
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------

from .plotter import (
    Tables,
    ColNum,
    Title,
    Legends,
    Director,
    SingleTableColumnBuilder,
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
) -> None:
    tb_builder = TableWrapper(table=table, xcol=x, ycol=y)
    builder = SingleTableColumnBuilder(
        builder=tb_builder,
        title=title,
        label=None,
    )
    director = Director(builder)
    
    xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
    with visualization.quantity_support():
        plotter = BasicPlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=labels_grp,
            markers_grp=markers_grp,
        )
        plotter.plot()


def plot_single_tables_column(
    tables: Tables,
    x: ColNum,
    y: ColNum,
    title: Title,
    legends: Legends,
    box: Tuple[str, float, float],
) -> None:
    tb_builder = TablesWrapper(tables=tables, xcol=x, ycol=y)
    builder = SingleTablesColumnBuilder(
        builder=tb_builder,
        title=title,
        labels=legends,
    )
    director = Director(builder)
    
    xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
    with visualization.quantity_support():
        plotter = BoxPlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=labels_grp,
            markers_grp=markers_grp,
            box=box,
        )
        plotter.plot()

