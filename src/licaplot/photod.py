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

import argparse
import logging

# ---------------------
# Thrid-party libraries
# ---------------------

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from astropy.table import Table
from lica.cli import execute

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import Markers
from .utils.validators import vecsv

import licaplot.photodiode
from .photodiode import PhotodiodeModel, COL, BENCH

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# ------------------
# Auxiliary fnctions
# ------------------


def plot_photodiode(title: str, table: Table, marker: str):
    fig, axes = plt.subplots(nrows=1, ncols=1)
    fig.suptitle(title)
    plot_single_photodiode(axes, table, marker)
    plt.show()


def plot_single_photodiode(axes: Axes, table: Table, marker: str):
    axes.set_xlabel(COL.WAVE)
    axes.set_ylabel(COL.RESP + " & " + COL.QE)
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.plot(table[COL.WAVE], table[COL.RESP], marker=marker, linewidth=0, label=COL.RESP)
    axes.plot(table[COL.WAVE], table[COL.QE], marker=marker, linewidth=0, label=COL.QE)
    axes.minorticks_on()
    axes.legend()


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def export(args):
    log.info(" === PHOTODIODE RESPONSIVITY & QE EXPORT === ")
    licaplot.photodiode.export(
        args.model, args.resolution, args.ecsv_file, args.wave_start, args.wave_end
    )


def plot(args):
    log.info(" === PHOTODIODE RESPONSIVITY & QE PLOT === ")
    table = licaplot.photodiode.load(args.model, args.resolution)
    log.info("Table info is\n%s", table.info)
    plot_photodiode(
        title=f"{args.model} characteristics",
        table=table,
        marker=args.marker,
    )


COMMAND_TABLE = {
    "plot": plot,
    "export": export,
}


def photod(args):
    COMMAND_TABLE[args.command](args)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def common_parser():
    """Common Options for subparsers"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-m",
        "--model",
        default=PhotodiodeModel.OSI,
        choices=[p for p in PhotodiodeModel],
        help="Photodiode model. (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        default=5,
        choices=tuple(range(1, 11)),
        help="Wavelength resolution (nm). (default: %(default)s nm)",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_plot = subparser.add_parser(
        "plot", parents=[common_parser()], help="Plot Responsivity & Quantum Efficiency"
    )
    parser_expo = subparser.add_parser(
        "export",
        parents=[common_parser()],
        help="Export Responsivity & Quantum Efficiency to CSV file",
    )

    parser_plot.add_argument(
        "--marker",
        type=str,
        choices=[m for m in Markers],
        default=Markers.Circle,
        help="Plot Marker",
    )

    parser_expo.add_argument(
        "-f", "--ecsv-file", type=vecsv, required=True, help="ECSV file name to export"
    )
    parser_expo.add_argument(
        "-w1",
        "--wave-start",
        type=float,
        default=BENCH.WAVE_START,
        help="Starting wavelength in nm (defaults to %(default)d)",
    )
    parser_expo.add_argument(
        "-w2",
        "--wave-end",
        type=float,
        default=BENCH.WAVE_END,
        help="End wavelength in nm (defaults to %(default)d)",
    )


# ================
# MAIN ENTRY POINT
# ================


def main():
    execute(
        main_func=photod,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="LICA reference photodiodes characteristics",
    )
