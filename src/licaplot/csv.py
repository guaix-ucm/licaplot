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
from typing import Iterable, Sequence, Optional
from argparse import ArgumentParser, Namespace

# ---------------------
# Thrid-party libraries
# ---------------------

import matplotlib.pyplot as plt

from lica.cli import execute
from lica.validators import vfile

import astropy.io.ascii
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from . import Markers, MONOCROMATOR_FILTERS_LABELS


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)
MARKERS = ["+", ".", "o", "x"]

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# -------------------
# Auxiliary functions
# -------------------

def markers() -> str:
    """Cilces throigh the markers enum for overlapping plots"""
    values = [marker.value for marker in Markers]
    i = 0
    N = len(values)
    while True:
        yield values[i]
        i = (i + 1) % N


def mpl_plot_overlapped(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
) -> None:
    """Plot up to 4 datasets in the same axes"""
    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    axes.set_xlabel(tables[0].columns[x].name)
    axes.set_ylabel(tables[0].columns[y].name)
    for table, label, marker in zip(tables, labels, markers()):
        axes.plot(table.columns[x], table.columns[y], marker=marker, linewidth=1, label=label)
    if filters:
        for filt in MONOCROMATOR_FILTERS_LABELS:
            axes.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


def mpl_plot_grid(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    nrows: int,
    ncols: int,
    x: int,
    y: int,
    marker: str,
) -> None:
    """Plot in different axes rows"""
    N = len(tables)
    if nrows * ncols < N:
        raise ValueError(f"{nrows} x {ncols} Grid can't accomodate {N} graphics")
    indexes = list(range(nrows * ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    axes = axes.flatten()  # From a numpy bidimensional array to a list
    if title is not None:
        fig.suptitle(title)
    for i, ax, table, label in zip(indexes, axes, tables, labels):
        ax.set_title(label)
        ax.set_xlabel(table.columns[x].name)
        ax.set_ylabel(table.columns[y].name)
        ax.plot(table.columns[x], table.columns[y], marker=marker, linewidth=1)
        if filters:
            for filt in MONOCROMATOR_FILTERS_LABELS:
                ax.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
        ax.grid(True, which="major", color="silver", linestyle="solid")
        ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
        ax.minorticks_on()
        if filters:
            ax.legend()
    # Do not draw in unusued axes
    for ax in axes[N:]:
        ax.set_axis_off()
    plt.show()


def mpl_plot_cols(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    marker: str,
) -> None:
    mpl_plot_grid(
        title=title,
        tables=tables,
        labels=labels,
        filters=filters,
        nrows=1,
        ncols=len(tables),
        x=x,
        y=y,
        marker=marker,
    )


def mpl_plot_rows(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    marker: str,
) -> None:
    mpl_plot_grid(
        title=title,
        tables=tables,
        labels=labels,
        filters=filters,
        nrows=len(tables),
        ncols=1,
        x=x,
        y=y,
        marker=marker,
    )


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
    elif len(args.input_files) == 2:
        mpl_plot_cols(
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
        choices=(m.value for m in Markers),
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
