# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import os
import logging
from math import ceil, sqrt

# Typing hints
from argparse import ArgumentParser, Namespace
from typing import Optional, Iterable

# ---------------------
# Thrid-party libraries
# ---------------------

import matplotlib.pyplot as plt
import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table
from astropy import visualization
import scipy.interpolate

from lica.cli import execute
from lica.validators import vfile
from lica.lab import BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import (
    plot_single_table_column,
    plot_single_table_columns,
    plot_single_tables_column,
    plot_multi_tables_columns,
    plot_multi_tables_column,
    plot_multi_table_columns,
)
from .utils.validators import vsequences, vecsv, vecsvfile
from .utils import parser2 as prs

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# -------------------
# Auxiliary functions
# -------------------


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


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
    xc: int,
    xu: u.Unit,
    xl: Optional[float],
    xh: Optional[float],
    lu: u.Unit,
    lica: Optional[bool],
) -> None:
    x = table.columns[xc]
    xmax = np.max(x) * xu if xh is None else xh * lu
    xmin = np.min(x) * xu if xl is None else xl * lu
    if lica:
        xmax, xmin = (
            min(xmax, BENCH.WAVE_END.value * u.nm),
            max(xmin, BENCH.WAVE_START.value * u.nm),
        )
    table = table[x <= xmax]
    x = table.columns[xc]
    table = table[x >= xmin]
    log.info("Trimmed table to wavelength [%s - %s] range", xmin, xmax)
    return table


def resample_column(
    table: Table, resolution: int, xc: int, xu: u.Unit, yc: int, lica: bool
) -> Table:
    x = table.columns[xc]
    y = table.columns[yc]
    if lica:
        xmin = BENCH.WAVE_START.value
        xmax = BENCH.WAVE_END.value
    else:
        xmax = np.floor(np.max(x))
        xmin = np.ceil(np.min(x))
    wavelength = np.arange(xmin, xmax + resolution, resolution)
    log.info("Wavelengh grid to resample is\n%s", wavelength)
    interpolator = scipy.interpolate.Akima1DInterpolator(x, y)
    log.info(
        "Resampled table to wavelength [%s - %s] range with %s resolution",
        xmin,
        xmax,
        resolution,
    )
    return wavelength, interpolator(wavelength)


def build_table_yc(
    path: str,
    xc: int,
    xu: u.Unit,
    yc: int,
    yu: u.Unit,
    title: str,
    label: str,
    columns: Optional[Iterable[str]],
    delimiter: Optional[str],
    xl: Optional[float],
    xh: Optional[float],
    lu: u.Unit,
    resolution: Optional[int],
    lica_trim: Optional[bool],
) -> Table:
    table = read_csv(path, columns, delimiter)
    # Prefer resample before trimming to avoid generating extrapolation NaNs
    if resolution is None:
        log.info("Not resampling table")
        table = trim_table(table, xc, xu, xl, xh, lu, lica_trim)
    else:
        wavelength, resampled_col = resample_column(table, resolution, xc, xu, yc, lica_trim)
        names = [c for c in table.columns]
        values = [None, None]
        values[xc] = wavelength
        values[yc] = resampled_col
        new_table = Table(data=values, names=names)
        new_table.meta = table.neta
        new_table = trim_table(new_table, xc, xu, xl, xh, lu, lica_trim)
        table = new_table
    col_x = table.columns[xc]
    col_y = table.columns[yc]
    if col_y.unit is None:
        table[col_y.name] = table[col_y.name] * yu
    if col_x.unit is None:
        table[col_x.name] = table[col_x.name] * xu
    table.meta["label"] = table.meta.get("label") or label
    table.meta["title"] = table.meta.get("title") or title or table.meta["label"]
    log.info(table.meta)
    return table


def build_table_yycc(
    path: str,
    xc: int,
    xu: u.Unit,
    title: str,
    label: str,
    columns: Optional[Iterable[str]],
    delimiter: Optional[str],
    xl: Optional[float],
    xh: Optional[float],
    lu: u.Unit,
    lica_trim: Optional[bool],
) -> Table:
    table = read_csv(path, columns, delimiter)
    table = trim_table(table, xc, xu, xl, xh, lu, lica_trim)
    table.meta["label"] = table.meta.get("label") or label
    table.meta["title"] = table.meta.get("title") or title or table.meta["label"]
    log.info(table.info)
    log.info(table.meta)
    return table


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def cli_single_table_column(args: Namespace):
    title = " ".join(args.title) if args.title else None
    table = build_table_yc(
        path=args.input_file,
        delimiter=args.delimiter,
        columns=args.columns,
        xc=args.x_column - 1,
        xu=args.x_unit,
        yc=args.y_column - 1,
        yu=args.y_unit,
        xl=args.x_low,
        xh=args.x_high,
        lu=args.limits_unit,
        resolution=args.resample,
        lica_trim=args.lica,
        title=title,
        label=None,
    )
    title = table.meta["title"] or table.meta["label"]
    with visualization.quantity_support():
        plot_single_table_column(
            table=table,
            x=args.x_column - 1,
            y=args.y_column - 1,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
        )


def cli_single_table_columns(args: Namespace):
    title = " ".join(args.title) if args.title else None
    table = build_table_yycc(
        path=args.input_file,
        delimiter=args.delimiter,
        columns=args.columns,
        xc=args.x_column - 1,
        xu=args.x_unit,
        xl=args.x_low,
        xh=args.x_high,
        lu=args.limits_unit,
        lica_trim=args.lica,
        title=title,
        label=args.label,
    )
    title = table.meta["title"]
    yy = [y - 1 for y in args.y_column]
    labels = args.label or [table.columns[y].name[:5] + "." for y in yy]
    with visualization.quantity_support():
        plot_single_table_columns(
            table=table,
            x=args.x_column - 1,
            yy=yy,
            legends=labels,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
        )


def cli_single_tables_column(args: Namespace):
    title = " ".join(args.title) if args.title else None
    labels = list()
    tables = list()
    for path in args.input_file:
        table = build_table_yc(
            path=path,
            delimiter=args.delimiter,
            columns=args.columns,
            xc=args.x_column - 1,
            xu=args.x_unit,
            yc=args.y_column - 1,
            yu=args.y_unit,
            xl=args.x_low,
            xh=args.x_high,
            lu=args.limits_unit,
            resolution=args.resample,
            lica_trim=args.lica,
            title=title,
            label=None,
        )
        labels.append(table.meta["label"])
        tables.append(table)
    title = title or tables[0].meta["title"]
    with visualization.quantity_support():
        plot_single_tables_column(
            tables=tables,
            x=args.x_column - 1,
            y=args.y_column - 1,
            legends=labels,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
        )


def cli_multi_table_columns(args: Namespace):
    raise NotImplementedError("Not very useful use case")


def cli_multi_tables_column(args: Namespace):
    pass


def cli_multi_tables_columns(args: Namespace):
    titles = list()
    tables = list()
    N = len(args.input_file)
    args_titles = args.title or [None] * N
    for path, title in zip(args.input_file, args_titles):
        table = build_table_yycc(
            path=path,
            delimiter=args.delimiter,
            columns=args.columns,
            xc=args.x_column - 1,
            xu=args.x_unit,
            xl=args.x_low,
            xh=args.x_high,
            lu=args.limits_unit,
            lica_trim=args.lica,
            title=title,
            label=args.label,
        )
        tables.append(table)
        titles.append(table.meta["title"])
    yy = [y - 1 for y in args.y_column]
    labels = args.label or [table[0].columns[y].name[:5] + "." for y in yy]
    ncols = args.num_cols if args.num_cols is not None else int(ceil(sqrt(len(tables))))
    nrows = int(ceil(len(tables) / ncols))
    plot_multi_tables_columns(
        nrows=nrows,
        ncols=ncols,
        tables=tables,
        x=args.x_column - 1,
        yy=yy,
        legends=labels,
        titles=titles,
        changes=args.changes,
        percent=args.percent,
        linewidth=args.lines or 0,
    )


def add_args(parser: ArgumentParser):
    sub_s = parser.add_subparsers(required=True)
    p_s = sub_s.add_parser("single", help="Single Axes plot")
    p_m = sub_s.add_parser("multi", help="Multiple Axes plot")

    # ================
    # Single Axes case
    # ================

    sub_s_t = p_s.add_subparsers(required=True)

    p_s_t = sub_s_t.add_parser("table", help="Single Axes, single table plot")
    sub_s_t_c = p_s_t.add_subparsers(required=True)
    par_s_t_c = sub_s_t_c.add_parser(
        "column",
        parents=[
            prs.ifile(),
            prs.xlim(),
            prs.resample(),
            prs.lica(),
            prs.xc(),
            prs.yc(),
            prs.title(None, "plotting"),
            prs.auxlines(),
            prs.percent(),
        ],
        help="Single Axes, single table, single column plot",
    )
    par_s_t_c.set_defaults(func=cli_single_table_column)
    par_s_t_cc = sub_s_t_c.add_parser(
        "columns",
        parents=[
            prs.ifile(),
            prs.xlim(),
            prs.lica(),
            prs.xc(),
            prs.yycc(),
            prs.title(None, "Plotting"),
            prs.labels("plotting"),  # Column labels
            prs.auxlines(),
            prs.percent(),
        ],
        help="Single Axes, single table, multiple columns plot",
    )
    par_s_t_cc.set_defaults(func=cli_single_table_columns)

    p_s_tt = sub_s_t.add_parser("tables", help="Single Axes, multiple tables plot")
    sub_s_tt_c = p_s_tt.add_subparsers(required=True)
    par_s_tt_c = sub_s_tt_c.add_parser(
        "column",
        parents=[
            prs.ifiles(),
            prs.xlim(),
            prs.resample(),
            prs.lica(),
            prs.xc(),
            prs.yc(),
            prs.title(None, "plotting"),
            prs.labels("plotting"),
            prs.auxlines(),
            prs.percent(),
        ],
        help="Single Axes, multiple tables, single column plot",
    )
    par_s_tt_c.set_defaults(func=cli_single_tables_column)

    # =============
    # Multiple Axes
    # =============
    sub_m_t = p_m.add_subparsers(required=True)

    p_m_t = sub_m_t.add_parser("table", help="Multiple Axes, single table plot")
    sub_m_t_c = p_m_t.add_subparsers(required=True)
    par_m_t_cc = sub_m_t_c.add_parser(
        "columns", parents=[], help="Multiple Axes, single table, multiple columns plot"
    )
    par_m_t_cc.set_defaults(func=cli_multi_table_columns)

    p_m_tt = sub_m_t.add_parser("tables", help="Mulitple Axes, multiple tables plot")
    sub_m_tt_c = p_m_tt.add_subparsers(required=True)
    par_m_tt_c = sub_m_tt_c.add_parser(
        "column", parents=[], help="Mulitple Axes, multiple tables, single column plot"
    )
    par_m_tt_c.set_defaults(func=cli_multi_tables_column)
    par_m_tt_cc = sub_m_tt_c.add_parser(
        "columns",
        parents=[
            prs.ncols(),
            prs.ifiles(),
            prs.xlim(),
            prs.lica(),
            prs.xc(),
            prs.yycc(),
            prs.title(None, "Plotting"),
            prs.labels("plotting"),  # Column labels
            prs.auxlines(),
            prs.percent(),
        ],
        help="Mulitple Axes, multiple tables, multiple columns plot",
    )
    par_m_tt_cc.set_defaults(func=cli_multi_tables_columns)


# ================
# MAIN ENTRY POINT
# ================


def cli_plot(args):
    args.func(args)


def main():
    execute(
        main_func=cli_plot,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Plot CSV/ECSV files",
    )
