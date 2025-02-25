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
from typing import Optional, Iterable, Sequence

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table
from astropy import visualization
import scipy.interpolate

from lica.cli import execute
from lica.lab import BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import (
    plot_single_table_column,
    plot_single_table_columns,
    plot_single_tables_column,
    plot_single_tables_columns,
    plot_multi_tables_columns,
    plot_multi_tables_column,
    plot_multi_table_columns,
)

from .utils import parser as prs

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------


# -------------------
# Auxiliary functions
# -------------------


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
    log.debug("Trimmed table to wavelength [%s - %s] range", xmin, xmax)
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
    log.debug("Wavelengh grid to resample is\n%s", wavelength)
    interpolator = scipy.interpolate.Akima1DInterpolator(x, y)
    log.debug(
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
        log.debug("Not resampling table")
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
    log.debug(table.info)
    log.debug(table.meta)
    return table


def build_table_yycc(
    path: str,
    xc: int,
    xu: u.Unit,
    columns: Optional[Iterable[str]],
    delimiter: Optional[str],
    xl: Optional[float],
    xh: Optional[float],
    lu: u.Unit,
    lica_trim: Optional[bool],
) -> Table:
    table = read_csv(path, columns, delimiter)
    table = trim_table(table, xc, xu, xl, xh, lu, lica_trim)
    log.debug(table.info)
    log.debug(table.meta)
    return table


def single_table_column_markers(args_marker: str, table: Table, ycol: int) -> str | None:
    return args_marker


def single_table_column_title(args_title: str, table: Table, ycol: int) -> str | None:
    return " ".join(args_title) if args_title is not None else table.meta["title"]


def single_table_columns_legends(
    args_label: Sequence[str], table: Table, ycols: Sequence[int]
) -> Sequence[str]:
    if args_label is not None and len(args_label) != len(ycols):
        raise ValueError(
            "number of labels (%d) should match number of y-columns (%d)"
            % (len(args_label), len(ycols)),
        )
    return (
        args_label
        if args_label is not None
        else [table.columns[y - 1].name[:6] + "." for y in ycols]
    )


def single_table_columns_markers(
    args_marker: Sequence[str], table: Table, ycols: Sequence[int]
) -> Sequence[str]:
    if args_marker is not None and len(args_marker) != len(ycols):
        raise ValueError(
            "number of markers (%d) should match number of y-columns (%d)"
            % (
                len(args_marker),
                len(ycols),
            )
        )
    return args_marker


def single_table_columns_title(
    args_title: Sequence[str], table: Table, ycols: Sequence[int]
) -> str | None:
    return " ".join(args_title) if args_title is not None else table.meta["title"]


def single_tables_column_legends(
    args_label: str, tables: Sequence[Table], col: int
) -> Sequence[str]:
    return [table.meta["label"] for table in tables]


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


def single_tables_columns_legends(
    args_label: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> Sequence[str]:
    NT = len(tables)
    NC = len(ycols)
    if args_label is not None:
        NARGS = len(args_label)
        if NARGS == NC:
            result = args_label * NT
        elif NARGS == NC * NT:
            result = args_label
        else:
            raise ValueError(
                "number of labels (%d) should match number of y-columns (%d)  or tables x y-columns (%d)"
                % (NARGS, NC, NC * NT),
            )
        return result
    else:
        return [
            table.meta["label"] + "-" + table.columns[y - 1].name[0:6] + "."
            for table in tables
            for y in ycols
        ]


def single_tables_columns_markers(
    args_marker: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> Sequence[str]:
    NT = len(tables)
    NC = len(ycols)
    if args_marker is not None:
        NARGS = len(args_marker)
        if NARGS == NC:
            result = args_marker * NT
        elif NARGS == NC * NT:
            result = args_marker
        else:
            raise ValueError(
                "number of markers (%d) should match number of y-columns (%d) or tables x y-columns (%d)"
                % (NARGS, NC, NC * NT)
            )
        return result
    else:
        return None


def single_tables_columns_title(
    args_title: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> str | None:
    return " ".join(args_title) if args_title is not None else tables[0].meta["title"]


def mult_tables_columns_title(
    args_title: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> str | None:
    NT = len(tables)
    if args_title is not None:
        NARGS = len(args_title)
        if NARGS != NT:
            raise ValueError(
                "number of titles (%d) should match number of tables (%d)" % (NARGS, NT)
            )
    return " ".join(args_title) if args_title is not None else [t.meta["title"] for t in tables]

def multi_tables_columns_legends(
    args_label: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> Sequence[str]:
    return single_tables_columns_markers(args_label, tables, ycols)

def multi_tables_columns_markers(
    args_marker: Sequence[str], tables: Sequence[Table], ycols: Sequence[int]
) -> Sequence[str]:
    return single_tables_columns_markers(args_marker, tables, ycols)

# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def cli_single_table_column(args: Namespace):
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
    )
    title = single_table_column_title(args.title, table, args.y_column)
    markers = single_table_column_markers(args.marker, table, args.y_column)
    with visualization.quantity_support():
        plot_single_table_column(
            table=table,
            x=args.x_column - 1,
            y=args.y_column - 1,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            marker=markers,
            save_path=args.save_figure_path,
        )


def cli_single_table_columns(args: Namespace):
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
    )
    title = single_table_columns_title(args.title, table, args.y_column)
    legends = single_table_columns_legends(args.label, table, args.y_column)
    markers = single_table_columns_markers(args.marker, table, args.y_column)
    with visualization.quantity_support():
        plot_single_table_columns(
            table=table,
            x=args.x_column - 1,
            yy=[y - 1 for y in args.y_column],
            legends=legends,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            markers=markers,
            save_path=args.save_figure_path,
        )


def cli_single_tables_column(args: Namespace):
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
        )
        tables.append(table)
    title = single_tables_column_title(args.title, tables, args.y_column)
    legends = single_tables_column_legends(args.label, tables, args.y_column)
    markers = single_tables_column_markers(args.marker, tables, args.y_column)
    with visualization.quantity_support():
        plot_single_tables_column(
            tables=tables,
            x=args.x_column - 1,
            y=args.y_column - 1,
            legends=legends,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            markers=markers,
            save_path=args.save_figure_path,
        )


def cli_single_tables_columns(args: Namespace):
    tables = list()
    for path in args.input_file:
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
        )
        tables.append(table)
    title = single_tables_columns_title(args.title, tables, args.y_column)
    legends = single_tables_columns_legends(args.label, tables, args.y_column)
    markers = single_tables_columns_markers(args.marker, tables, args.y_column)
    with visualization.quantity_support():
        plot_single_tables_columns(
            tables=tables,
            x=args.x_column - 1,
            yy=[y - 1 for y in args.y_column],
            legends=legends,
            title=title,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            markers=markers,
            save_path=args.save_figure_path,
        )


def cli_multi_tables_column(args: Namespace):
    titles = list()
    tables = list()
    N = len(args.input_file)
    args_title = args.title or [None] * N
    for path, title in zip(args.input_file, args_title):
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
        tables.append(table)
        titles.append(table.meta["title"])
    ncols = args.num_cols if args.num_cols is not None else int(ceil(sqrt(len(tables))))
    nrows = int(ceil(len(tables) / ncols))
    with visualization.quantity_support():
        plot_multi_tables_column(
            nrows=nrows,
            ncols=ncols,
            tables=tables,
            x=args.x_column - 1,
            y=args.y_column - 1,
            titles=titles,  # ESTOOO REVISAR
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            marker=args.marker,
            save_path=args.save_figure_path,
    )


def cli_multi_tables_columns(args: Namespace):
    tables = list()
    for path in args.input_file:
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
        )
        tables.append(table)
    titles = mult_tables_columns_title(args.title, tables, args.y_column)
    legends = multi_tables_columns_legends(args.label, tables, args.y_column)
    markers = multi_tables_columns_markers(args.marker, tables, args.y_column)
    log.info("TITLE = %s", titles)
    log.info("LEGENDS = %s", legends)
    log.info("MARKERS = %s", legends)
    ncols = args.num_cols if args.num_cols is not None else int(ceil(sqrt(len(tables))))
    nrows = int(ceil(len(tables) / ncols))
    with visualization.quantity_support():
        plot_multi_tables_columns(
            nrows=nrows,
            ncols=ncols,
            tables=tables,
            x=args.x_column - 1,
            yy=[y - 1 for y in args.y_column],
            legends=legends,
            titles=titles,
            changes=args.changes,
            percent=args.percent,
            linewidth=args.lines or 0,
            markers=markers,
            save_path=args.save_figure_path,
    )


def add_args(parser: ArgumentParser):
    sub_s = parser.add_subparsers(required=True)
    p_s = sub_s.add_parser("single", help="Single Axes plot")
    p_m = sub_s.add_parser("multi", help="Multiple Axes plot")

    # ================
    # Single Axes case
    # ================

    sub_s_t = p_s.add_subparsers(required=True)

    # ---------------------------------------------
    # Single Axes, Single Table, Single Column case
    # ---------------------------------------------
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
            prs.label("plotting"),
            prs.auxlines(),
            prs.percent(),
            prs.marker(),
            prs.savefig(),
        ],
        help="Single Axes, single table, single column plot",
    )
    par_s_t_c.set_defaults(func=cli_single_table_column)

    # ------------------------------------------------
    # Single Axes, Single Table, Multiple Columns case
    # ------------------------------------------------
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
            prs.markers(),
            prs.savefig(),
        ],
        help="Single Axes, single table, multiple columns plot",
    )
    par_s_t_cc.set_defaults(func=cli_single_table_columns)

    p_s_tt = sub_s_t.add_parser("tables", help="Single Axes, multiple tables plot")
    sub_s_tt = p_s_tt.add_subparsers(required=True)

    # ------------------------------------------------
    # Single Axes, Multiple Tables, Single Column case
    # ------------------------------------------------
    par_s_tt_c = sub_s_tt.add_parser(
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
            prs.markers(),
            prs.savefig(),
        ],
        help="Single Axes, multiple tables, single column plot",
    )
    par_s_tt_c.set_defaults(func=cli_single_tables_column)

    # ---------------------------------------------------
    # Single Axes, Multiple Tables, Multiple Columns case
    # ---------------------------------------------------
    par_s_tt_cc = sub_s_tt.add_parser(
        "columns",
        parents=[
            prs.ifiles(),
            prs.xlim(),
            prs.lica(),
            prs.xc(),
            prs.yycc(),
            prs.title(None, "Plotting"),
            prs.labels("plotting"),  # Column labels
            prs.auxlines(),
            prs.percent(),
            prs.markers(),
            prs.savefig(),
        ],
        help="Single Axes, multiple tables, multiple columns plot",
    )
    par_s_tt_cc.set_defaults(func=cli_single_tables_columns)

    # =============
    # Multiple Axes
    # =============

    sub_m_t = p_m.add_subparsers(required=True)

    p_m_tt = sub_m_t.add_parser("tables", help="Mulitple Axes, multiple tables plot")
    sub_m_tt_c = p_m_tt.add_subparsers(required=True)

    # ---------------------------------------------------
    # Multiplea Axes, Multiple Tables, Single Column case
    # ---------------------------------------------------
    par_m_tt_c = sub_m_tt_c.add_parser(
        "column",
        parents=[
            prs.ncols(),
            prs.ifiles(),
            prs.xlim(),
            prs.lica(),
            prs.xc(),
            prs.yc(),
            prs.title(None, "Plotting"),
            prs.label("plotting"),
            prs.resample(),
            prs.auxlines(),
            prs.percent(),
            prs.markers(),
            prs.savefig(),
        ],
        help="Mulitple Axes, multiple tables, single column plot",
    )
    par_m_tt_c.set_defaults(func=cli_multi_tables_column)

    # ------------------------------------------------------
    # Multiplea Axes, Multiple Tables, Multiple Columns case
    # ------------------------------------------------------
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
            prs.markers(),
            prs.savefig(),
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
