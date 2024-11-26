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

# ---------------------
# Thrid-party libraries
# ---------------------

import matplotlib.pyplot as plt

from lica.cli import execute
from lica.validators import vfile

import astropy.io.ascii

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import Markers, mpl_plot_overlapped, mpl_plot_single, mpl_plot_rows, mpl_plot_grid


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


def validate_inputs(*args):
    bounded = all(len(arg) <= 4 for arg in args)
    if not bounded:
        raise ValueError("An input argument list exceeds 4")
    same_length = all(len(arg) == len(args[0]) for arg in args)
    if not same_length:
        raise ValueError("Not all input argument lists have the same length")


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def csvs(args: Namespace) -> None:
    validate_inputs(args.input_files, args.labels)
    N = len(args.input_files)
    tables = [astropy.io.ascii.read(f) for f in args.input_files]
    if args.overlap:
        mpl_plot_overlapped(
            tables=tables,
            title=args.title,
            labels=args.labels,
            filters=args.filters,
            x=args.x_index,
            y=args.y_index,
        )
    elif N == 1:
        mpl_plot_single(
            tables=tables,
            title=args.title,
            labels=args.labels,
            filters=args.filters,
            x=args.x_index,
            y=args.y_index,
            marker=args.marker,
        )
    elif N == 2:
        mpl_plot_rows(
            tables=tables,
            title=args.title,
            labels=args.labels,
            filters=args.filters,
            x=args.x_index,
            y=args.y_index,
            marker=args.marker,
        )
    else:
        mpl_plot_grid(
            title=args.title,
            tables=tables,
            labels=args.labels,
            filters=args.filters,
            nrows=2,
            ncols=2,
            x=args.x_index,
            y=args.y_index,
            marker=args.marker,
        )


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-i",
        "--input-files",
        type=vfile,
        required=True,
        nargs="+",
        metavar="<File>",
        help="CSV input file(s) [1-4]. X axis is the first column",
    )
    parser.add_argument(
        "-l",
        "--labels",
        type=str,
        nargs="+",
        required=True,
        metavar="<Label>",
        help="input labels [1-4]",
    )
    parser.add_argument("-o", "--overlap", action="store_true", help="Overlap Plots")
    parser.add_argument(
        "-t", "--title", type=str, default=None, help="Overall plot title, defaults to %(default)s"
    )
    parser.add_argument(
        "-f", "--filters", action="store_true", help="Plot Monocromator filter changes"
    )
    parser.add_argument(
        "-x",
        "--x-index",
        type=int,
        metavar="<N>",
        default=0,
        help="Column index for X axis in CSV file, defaults tp %(default)d",
    )
    parser.add_argument(
        "-y",
        "--y-index",
        type=int,
        metavar="<N>",
        default=1,
        help="Column index for Y axis in CSV file, defaults tp %(default)d",
    )
    parser.add_argument(
        "-m",
        "--marker",
        type=str,
        choices=[m.value for m in Markers],
        default=Markers.Circle.value,
        help="Plot Marker",
    )


# ================
# MAIN ENTRY POINT
# ================


def main():
    execute(
        main_func=csvs,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Plot CSV files",
    )
