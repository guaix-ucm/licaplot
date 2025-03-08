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
# Third-party libraries
# ---------------------

import matplotlib.pyplot as plt

from lica.cli import execute
from lica.lab import BENCH, COL
from lica.lab.photodiode import PhotodiodeModel
import lica

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import plot_single_table_column
from .utils.mpl.plotter import Marker
from .utils.validators import vecsv


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
plt.style.use("licatools.resources.global")

# ------------------
# Auxiliary fnctions
# ------------------


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def export(args):
    log.info(" === PHOTODIODE RESPONSIVITY & QE EXPORT === ")
    lica.lab.photodiode.export(
        args.ecsv_file, args.model, args.resolution, args.wave_start, args.wave_end
    )


def plot(args):
    log.info(" === PHOTODIODE RESPONSIVITY & QE PLOT === ")
    table = lica.lab.photodiode.load(args.model, args.resolution, args.wave_start, args.wave_end)
    log.info("Table info is\n%s", table.info)
    plot_single_table_column(
        table=table,
        xcolname=COL.WAVE,
        ycolname=COL.RESP,
        title=f"{args.model} characteristics @ {args.resolution} nm",
    )


def photod(args) -> None:
    args.func(args)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def vbench(x: str) -> float:
    x = float(x)
    if not (BENCH.WAVE_START <= x <= BENCH.WAVE_END):
        raise ValueError(f"{x} outside LICA Optical Test Bench range")
    return x


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
    parser.add_argument(
        "-w1",
        "--wave-start",
        type=vbench,
        metavar="<W1 nm>",
        default=BENCH.WAVE_START,
        help="Start wavelength in nm (defaults to %(default)d)",
    )
    parser.add_argument(
        "-w2",
        "--wave-end",
        type=vbench,
        metavar="<W2 nm>",
        default=BENCH.WAVE_END,
        help="End wavelength in nm (defaults to %(default)d)",
    )

    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_plot = subparser.add_parser(
        "plot", parents=[common_parser()], help="Plot Responsivity & Quantum Efficiency"
    )
    parser_plot.set_defaults(func=plot)
    parser_expo = subparser.add_parser(
        "export",
        parents=[common_parser()],
        help="Export Responsivity & Quantum Efficiency to CSV file",
    )
    parser_expo.set_defaults(func=export)

    # ------------------------------------------------------------------------------------
    parser_plot.add_argument(
        "--marker",
        type=Marker,
        choices=Marker,
        default=Marker.Circle,
        help="Plot Marker",
    )
    # ------------------------------------------------------------------------------------
    parser_expo.add_argument(
        "-f", "--ecsv-file", type=vecsv, required=True, help="ECSV file name to export"
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
