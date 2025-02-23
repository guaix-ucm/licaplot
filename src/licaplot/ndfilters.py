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

# Typing hints
from argparse import ArgumentParser, Namespace

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt
import astropy.io.ascii

from lica.cli import execute
from lica.lab import COL

# ------------------------
# Own modules and packages
# ------------------------

from . import TBCOL, PROCOL
from ._version import __version__
from .utils import parser as prs
from .utils.mpl import plot_single_table_column
from .filters import one_filter
from .plot import cli_single_table_column


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


# ------------------
# Auxiliary fnctions
# ------------------


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def cli_calibrate(args: Namespace) -> None:
    one_filter(
        input_path=args.input_file,
        photod_path=args.photod_file,
        model=args.model,
        label=args.ndf.value,
        title=None,
        tag=args.tag,
        x_low=args.x_low,
        x_high=args.x_high,
        ndf=args.ndf,
    )
    ecsv_path, _ = os.path.splitext(args.input_file)
    ecsv_path += ".ecsv"
    log.info("Reading back ECSV file %s", ecsv_path)
    table = astropy.io.ascii.read(ecsv_path, format="ecsv")
    table.remove_columns([TBCOL.CURRENT, PROCOL.PHOTOD_CURRENT])
    table.meta["History"].append(f"Master {args.ndf} transmission file")
    resolution = np.ediff1d(table[COL.WAVE])[0]
    name = f"{args.ndf}-Transmission@{int(resolution)}nm.ecsv"
    master_path = os.path.join(args.output_dir, name)
    log.info("Producing Master ECSV file %s", master_path)
    table.write(master_path, delimiter=",", overwrite=True)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    # ---------------------------------------------------------------
    parser = subparser.add_parser(
        "calib",
        parents=[prs.ifile(), prs.photod(), prs.tag(), prs.xlim(), prs.ndf(), prs.odir()],
        help="Calibrate a Neutral Density Filter",
    )
    parser.set_defaults(func=cli_calibrate)


# ================
# MAIN ENTRY POINT
# ================


def cli_main(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="LICA's optical testbench Neutral Density filters calibration and plotting",
    )
