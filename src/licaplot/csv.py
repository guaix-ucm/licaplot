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

import logging

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
from lica.photodiode import BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import plot_overlapped, plot_single, plot_rows, plot_grid
from .utils.validators import vsequences, vecsv, vecsvfile

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


def multi(args: Namespace) -> None:
    vsequences(4, args.input_files)
    N = len(args.input_files)
    tables = [astropy.io.ascii.read(f, format="ecsv") for f in args.input_files]
    labels = [t.meta["label"] for t in tables]
    title = " ".join(args.title) if args.title else None
    if args.overlap:
        plot_overlapped(
            tables=tables,
            title=title,
            labels=labels,
            filters=args.filters,
            x=args.wave_col_order-1,
            y=args.y_col_order-1,
            linewidth=args.lines or 0
        )
    elif N == 1:
        plot_single(
            tables=tables,
            title=title,
            labels=args.labels,
            filters=args.filters,
            x=args.wave_col_order-1,
            y=args.y_col_order-1,
            marker=args.marker,
            linewidth=args.lines or 0
        )
    elif N == 2:
        plot_rows(
            tables=tables,
            title=title,
            labels=labels,
            filters=args.filters,
            x=args.wave_col_order-1,
            y=args.y_col_order-1,
            marker=args.marker,
            linewidth=args.lines or 0
        )
    else:
        plot_grid(
            title=title,
            tables=tables,
            labels=labels,
            filters=args.filters,
            nrows=2,
            ncols=2,
            x=args.wave_col_order-1,
            y=args.y_col_order-1,
            marker=args.marker,
            linewidth=args.lines or 0
        )


def read_csv(path: str, columns: Optional[Iterable[str]], delimiter: Optional[str]) -> Table:
    if columns:
        table = astropy.io.ascii.read(
            path,
            delimiter=delimiter,
            data_start=1,
            names=columns,
        )
    else:
        table = astropy.io.ascii.read(path, delimiter)
    return table


def trim_table(
    table: Table,
    wave_idx: int,
    wave_unit: u.Unit,
    wave_low: Optional[float],
    wave_high: Optional[float],
    wl_unit: u.Unit,
    lica: Optional[bool],
) -> None:
    x = table.columns[wave_idx]
    xmax = np.max(x) * wave_unit if wave_high is None else wave_high * wl_unit
    xmin = np.min(x) * wave_unit if wave_low is None else wave_low * wl_unit
    if lica:
        xmax, xmin = (
            min(xmax, BENCH.WAVE_END.value * u.nm),
            max(xmin, BENCH.WAVE_START.value * u.nm),
        )
    table = table[x * wave_unit <= xmax]
    x = table.columns[wave_idx]
    table = table[x * wave_unit >= xmin]
    log.info("Trimmed table to wavelength [%s - %s] range", xmin, xmax)
    return table


def resample_column(
    table: Table, resolution: int, wave_idx: int, wave_unit: u.Unit, y_idx: int, lica: bool
) -> Table:
    x = table.columns[wave_idx]
    y = table.columns[y_idx]
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


def build_table(
    path: str,
    wave_idx: int,
    wave_unit: u.Unit,
    y_idx: int,
    y_unit: u.Unit,
    description: str,
    label: str,
    columns: Optional[Iterable[str]],
    delimiter: Optional[str],
    wave_low: Optional[float],
    wave_high: Optional[float],
    wl_unit: u.Unit,
    resolution: Optional[int],
    lica_trim: Optional[bool], 
) -> Table:
    table = read_csv(path, columns, delimiter)
    # Prefer resample before trimming to avoid generating extrapolation NaNs
    if resolution is None:
        log.info("Not resampling table")
        table = trim_table(table, wave_idx, wave_unit, wave_low, wave_high, wl_unit, lica_trim)
    else:
        wavelength, resampled_col = resample_column(
            table, resolution, wave_idx, wave_unit, y_idx, lica_trim
        )
        names = [c for c in table.columns]
        values = [None, None]
        units = [None, None]
        values[wave_idx] = wavelength
        values[y_idx] = resampled_col
        units[wave_idx] = wave_unit
        units[y_idx] = y_unit
        table = Table(data=values, names=names)
        table = trim_table(table, wave_idx, wave_unit, wave_low, wave_high, wl_unit, lica_trim)
    table[table.columns[y_idx].name] = table[table.columns[y_idx].name] * y_unit
    table[table.columns[wave_idx].name] = table[table.columns[wave_idx].name] * wave_unit
    table.meta = {"description": description, "label": label}
    log.info(table.info)
    return table


def single(args: Namespace) -> None:
    table = build_table(
        path=args.input_file,
        columns=args.columns,
        delimiter=args.delimiter,
        wave_idx=args.wave_col_order - 1,
        wave_unit=args.wave_unit,
        y_idx=args.y_col_order - 1,
        y_unit=args.y_unit,
        wave_low=args.wave_low,
        wave_high=args.wave_high,
        wl_unit=args.wave_limit_unit,
        resolution=args.resample,
        lica_trim=args.lica,
        description=" ".join(args.title),
        label=args.label,
    )
    if args.export:
        log.info("exporting to %s", args.export)
        table.write(args.export, delimiter=",", overwrite=True)
    with visualization.quantity_support():
        plot_single(
            tables=[table],
            title=" ".join(args.title),
            labels=[None],
            filters=None,
            x=args.wave_col_order - 1,
            y=args.y_col_order - 1,
            marker=None,
            linewidth=0,
        )


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def columns_parser() -> ArgumentParser:
    """Generic parse option for CSV input files"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV input file",
    )
    parser.add_argument(
        "-c",
        "--columns",
        type=str,
        default=None,
        nargs="+",
        metavar="<NAME>",
        help="Ordered list of CSV Column names. Use CSV column names by default (default %(default)s)",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        default=",",
        help="CSV column delimiter. (defaults to %(default)s)",
    )
    return parser


def column_plot_parser() -> ArgumentParser:
    """Generic parse options dealing with Y versus wavelength tables and its units"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        nargs="+",
        help="Plot title",
    )
    parser.add_argument(
        "--label",
        type=str,
        required=True,
        help="Label for legends",
    )
    parser.add_argument(
        "-wc",
        "--wave-col-order",
        type=int,
        metavar="<N>",
        default=1,
        help="Wavelength column order in CSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-wu",
        "--wave-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Wavelength units string (ie. nm, AA) %(default)s",
    )
    parser.add_argument(
        "-yc",
        "--y-col-order",
        type=int,
        metavar="<N>",
        default=2,
        help="Column order for Y magnitude in CSV, defaults tp %(default)d",
    )
    parser.add_argument(
        "-yu",
        "--y-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.dimensionless_unscaled,
        help="Astropy Unit string (ie. nm, A/W, etc.) %(default)s",
    )
   
    return parser


def wave_parser() -> ArgumentParser:
    """Generic options dealing with wavelength trimming & resampling and its units"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-wl",
        "--wave-low",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength lower limit, (if not specified, taken from CSV), defaults to %(default)s",
    )
    parser.add_argument(
        "-wh",
        "--wave-high",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength upper limit, (if not specified, taken from CSV), defaults to %(default)s",
    )
    parser.add_argument(
        "-wlu",
        "--wave-limit-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Wavelength limits unit string (ie. nm, AA) %(default)s",
    )
    parser.add_argument(
        "-r",
        "--resample",
        choices=tuple(range(1, 11)),
        type=int,
        metavar="<N nm>",
        default=None,
        help="Resample wavelength to N nm step size, defaults to %(default)s",
    )
    parser.add_argument(
        "--lica",
        action="store_true",
        help="Trims wavelength to LICA Optical Bench range [350nm-1050nm]",
    )
    return parser


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[columns_parser(), column_plot_parser(), wave_parser()],
        help="Plot single CSV file",
    )
    parser_single.set_defaults(func=single)
    parser_multi = subparser.add_parser(
        "multi",
        help="Plot multiple CSV files",
    )
    parser_multi.set_defaults(func=multi)
    # --------------------------------------------------------------------------------------------------
    parser_single.add_argument(
        "--export",
        type=vecsv,
        metavar="<FILE>",
        default=None,
        help="Export to ECSV",
    )

    # --------------------------------------------------------------------------------------------------
    parser_multi.add_argument(
        "-i",
        "--input-files",
        type=vecsvfile,
        required=True,
        nargs="+",
        metavar="<File>",
        help="ECSV input file(s) [1-4]",
    )
    parser_multi.add_argument("-o", "--overlap", action="store_true", help="Overlap Plots")
    parser_multi.add_argument(
        "-t", "--title", nargs="+", type=str, default=None, help="Overall plot title, defaults to %(default)s"
    )
    parser_multi.add_argument(
        "-f", "--filters", action="store_true", help="Plot Monocromator filter changes"
    )
    parser_multi.add_argument(
        "-wc",
        "--wave-col-order",
        type=int,
        metavar="<N>",
        default=1,
        help="Wavelength column order in CSV, defaults to %(default)d",
    )
    parser_multi.add_argument(
        "-yc",
        "--y-col-order",
        type=int,
        metavar="<N>",
        default=2,
        help="Column order for Y magnitude in CSV, defaults tp %(default)d",
    )
    parser_multi.add_argument(
        "--lines",
        action="store_true",
        help="Connect dots with lines %(default)s",
    )
   

# ================
# MAIN ENTRY POINT
# ================


def csvs(args):
    args.func(args)


def main():
    execute(
        main_func=csvs,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Plot CSV files",
    )
