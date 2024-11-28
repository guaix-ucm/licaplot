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
    # stage1 processing
    "Processing": [
        {
            "Label": "NPL",
            "Description": "NPL Calibration",
            "Date": None,
            "Start Wavelength": 350 * u.nm,
            "End Wavelength": 1000 * u.nm,
            "Additional Processing": None,
        },
    ],
}

STAGE_2_PROCESSING = {
    "Label": "datasheet",
    "Description": "Datasheet + PlotDigitizer extraction",
    "Date": "2024-01-01",
    "Start Wavelength": 1002.18231 * u.nm,
    "End Wavelength": 1111.56568 * u.nm,
    "Additional Processing": {
        "Comment": "Added offset to match datasheet curve to NPL Calibration",
        "X Offset": 0 * u.nm,
        "Y Offset": 0 * (u.A / u.W),
    },
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
    table["QE"] = quantum_efficiency(table)
    table.meta = METADATA
    log.info("Generated table is\n%s", table.info)
    output_path, _ = os.path.splitext(path)
    output_path += ".ecsv"
    log.info("Generating %s", output_path)
    table.write(output_path, overwrite=True)
    if args.plot:
        plot_overlapped(
            title=args.title,
            tables=[table],
            labels=[METADATA["Processing"][0]["Label"]],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )

def stage2(args: Namespace) -> None:
    log.info("Loading NPL ECSV calibration File: %s", args.npl_file)
    npl_table = astropy.io.ascii.read(args.npl_file, format="ecsv")
    log.info("Loading datasheet CSV calibration File: %s", args.input_file)
    dsht_table = astropy.io.ascii.read(
        args.input_file,
        delimiter=";",
        data_start=1,
        names=("Wavelength", "Responsivity"),
        converters={"Wavelength": np.float64, "Responsivity": np.float64},
    )
    dsht_table["Wavelength"] = (dsht_table["Wavelength"] + args.x )* u.nm
    dsht_table["Responsivity"] = (dsht_table["Responsivity"] +args.y ) * (u.A / u.W)
    dsht_table["QE"] = quantum_efficiency(dsht_table)
    plot_overlapped(
            title=args.title,
            tables=[npl_table, dsht_table],
            labels=[METADATA["Processing"][0]["Label"], STAGE_2_PROCESSING["Label"]],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )

    if args.save:
        astropy.table.join(npl_table, dsht_table, keys="Wavelength")
        log.info("Generating %s", output_path)
        table.write(output_path, overwrite=True)

# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_stage1 = subparser.add_parser(
        "stage1", help="Load NPL calibration CSV and convert to ECSV"
    )
    parser_stage2 = subparser.add_parser(
        "stage2", help="Merges datasheet data to NPL calibration data"
    )
    parser_stage1.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="input CSV with NPL calibration",
    )
    parser_stage1.add_argument(
        "-p",
        "--plot",
        action="store_true",
        help="Plot file too",
    )
    parser_stage1.add_argument(
        "-t",
        "--title",
        type=str,
        default="Hamamatsu S2281-04",
        help="Plot title",
    )

    parser_stage2.add_argument(
        "-n",
        "--npl-file",
        type=vfile,
        required=True,
        metavar="<NPL ECSV>",
        help="ECSV with NPL calibration",
    )
    parser_stage2.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="aditions CSV with datasheet calibration values",
    )
    parser_stage2.add_argument(
        "-x",
        "--x",
        type=np.float64,
        default = 0.0,
        metavar="<X offset>",
        help="X (wavelength) offset to apply to input CSV file (defaults to %(default)f)",
    )
    parser_stage2.add_argument(
        "-y",
        "--y",
        type=np.float64,
        default = 0.0,
        metavar="<Y offset>",
        help="Y (responsivity) offset to apply to input CSV file (defaults to %(default)f)",
    )
    parser_stage2.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save combined file to ECSV",
    )
    parser_stage2.add_argument(
        "-t",
        "--title",
        type=str,
        default="Hamamatsu S2281-04",
        help="Plot title",
    )


# ================
# MAIN ENTRY POINT
# ================


COMMAND_TABLE = {
    "stage1": stage1,
    "stage2": stage2,
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
