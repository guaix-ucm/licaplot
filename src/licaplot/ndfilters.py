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
from typing import Optional, Tuple

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt
import astropy.io.ascii
import astropy.units as u
from astropy.constants import astropyconst20 as const
from astropy.table import Table, Column
import scipy.interpolate


from lica.cli import execute
from lica.validators import vfile, vmonth

from lica.lab import  COL, BENCH
from lica.lab.photodiode import PhotodiodeModel, Hamamatsu, OSI
import lica.lab.photodiode

# ------------------------
# Own modules and packages
# ------------------------

from . import TBCOL
from ._version import __version__
from .utils.mpl import plot_overlapped
from .utils.validators import vecsvfile
from .utils.processing import read_scan_csv

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



def create_nd_table(path: str) -> Table:
    log.info("Converting input CSV to Astropy Table: %s", path)
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE, COL.RESP),
        converters={COL.WAVE: np.float64, COL.RESP: np.float64},
    )
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=5) * u.nm
    table[COL.RESP] = table[COL.RESP] * (u.A / u.W)
    table[COL.QE] = quantum_efficiency(table[COL.WAVE], table[COL.RESP])
    resolution = np.ediff1d(table[COL.WAVE])
    table.meta = {
        "Manufacturer": OSI.MANUF,
        "Model": OSI.MODEL,
        "Serial": OSI.SERIAL,
        "Window": OSI.WINDOW,
        "Photosensitive size diameter": OSI.PHS_SIZE,
        "Photosensitive area": OSI.PHS_AREA,
        "Dark current": OSI.DARK,
        "Peak responsivity": OSI.PEAK,
        "History": [],
    }
    history = {
        "Description": "Loaded Calibration Table from Datasheet",
        "Date": None,
        "Resolution": {
            "mean": np.round(np.mean(resolution), decimals=2) * u.mm,
            "sigma": np.round(np.std(resolution, ddof=1), decimals=1) * u.mm,
            "median": np.round(np.median(resolution), decimals=2) * u.mm,
        },
        "Comment": "Variable resolution",
        "Start wavelength": np.min(table[COL.WAVE]) * u.nm,
        "End wavelength": np.max(table[COL.WAVE]) * u.nm,
    }
    table.meta["History"].append(history)
    log.info("Generated table is\n%s", table.info)
    return table


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def cli_calibrate(args: Namespace) -> None:
    pass

def cli_plot(args: Namespace) -> None:
    pass


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================



def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    # ---------------------------------------------------------------
    parser = subparser.add_parser(
        "calib",
        parents=[],
        help="Calibrate a Neutral Density Filter",
    )
    parser.set_defaults(func=cli_calibrate)
    
    # ---------------------------------------------------------------
    parser = subparser.add_parser(
        "plot",
        parents=[],
        help="Plot Neutral Density Filter response",
    )
    parser.set_defaults(func=cli_plot)
    

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
