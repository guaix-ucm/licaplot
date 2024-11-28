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
import astropy.units as u
from astropy.constants import astropyconst20 as const
from astropy.table import Table

from lica.cli import execute
from lica.validators import vfile


# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.mpl import plot_overlapped
# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

METADATA = {
    "Global": {
        "Manufacturer": "Hamamatsu",
        "Model": "S2281-04",
        "Serial": 1097,
        "Photosensitive area": 50 * (u.mm**2),
        "Dark current": 50 * (u.pA),
    },
    "Processing": [
        {
            "Label": "NPL",
            "Description": "NPL Calibration",
            "Date": None,
            "from_index": 0,
            "to_index": 33,
            "Start Wavelength": 350 * u.nm,
            "End Wavelength": 1000 * u.nm,
            "Additional Processing": None,
        },
        {
            "Label": "datasheet",
            "Description": "Datasheet + PlotDigitizer extraction",
            "Date": "2024-01-01",
            "from_index": 34,
            "to_index": 74,
            "Start Wavelength": 1002.18231 * u.nm,
            "End Wavelength": 1111.56568 * u.nm,
            "Additional Processing": {
                "Comment": "Added offset to match datasheet curve to NPL Calibration",
                "X Offset": 18 * u.nm,
                "Y Offset": 0.009 * (u.A / u.W),
            },
        },
    ],
}

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


def quantum_efficiency(table: Table) -> np.ndarray:
    """Computes the Quantum Efficiency given the Responsivity in A/W"""
    K = (const.h * const.c) / const.e
    return (K * table["Responsivity"] / table["Wavelength"].to(u.m)).to(u.dimensionless_unscaled)


def stage1(args: Namespace) -> None:
    path = args.input_file
    log.info("Converting CSV to Astropy Table")
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
        names=("Wavelength", "Responsivity"),
        converters={"Wavelength": np.float64, "Responsivity": np.float64},
    )
    table["Wavelength"] = np.round(table["Wavelength"], 0) * u.nm
    table["Responsivity"] = table["Responsivity"] * (u.A / u.W)
    table["QE"] = table["QE"] = quantum_efficiency(table)
    table.meta = METADATA
    log.info("Generated table is\n%s", table.info)
    output_path, _ = os.path.splitext(path)
    output_path += ".ecsv"
    log.info("Generating %s", output_path)
    table.write(output_path, overwrite=True)
    if args.plot:
        npl_mask = table["Wavelength"] <= METADATA["Processing"][0]["End Wavelength"]
        datasheet_mask = table["Wavelength"] > METADATA["Processing"][0]["End Wavelength"]
        plot_overlapped(
            title="Hamamatsu S2281-04",
            tables=[table[npl_mask], table[datasheet_mask]],
            labels=[METADATA["Processing"][0]["Label"],  METADATA["Processing"][1]["Label"]],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_stage1 = subparser.add_parser(
        "stage1", help="Load primary source CSV and convert to ECSV"
    )
    parser_stage1.add_argument(
        "-i",
        "--input_file",
        type=vfile,
        metavar="<CSV>",
        help="Manually generated input CSV from NPL calibration & Datasheet",
    )
    parser_stage1.add_argument(
        "-p",
        "--plot",
        action="store_true",
        help="Plot file too",
    )


# ================
# MAIN ENTRY POINT
# ================


COMMAND_TABLE = {
    "stage1": stage1,
}


def hama(args: Namespace):
    COMMAND_TABLE[args.command](args)


def main():
    execute(
        main_func=hama,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="All about obtaining LICA's Hamamatsu photodiode calibration data and curves",
    )
