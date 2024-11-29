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
from enum import Enum

# Typing hints
from argparse import ArgumentParser, Namespace
from typing import Tuple

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt
import astropy.io.ascii
import astropy.units as u
from astropy.constants import astropyconst20 as const
from astropy.table import Table, QTable
from astropy.units import Quantity

import scipy.interpolate
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

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")


class COL(Enum):
    """Calibration Table Columns"""

    WAVE = "Wavelength"
    RESP = "Responsivity"
    QE = "QE"


# -------------------
# Auxiliary functions
# -------------------


def quantum_efficiency(wavelength: np.ndarray, responsivity: np.ndarray) -> np.ndarray:
    """Computes the Quantum Efficiency given the Responsivity in A/W"""
    K = (const.h * const.c) / const.e
    return np.round(K * responsivity / wavelength.to(u.m), decimals=5) * u.dimensionless_unscaled


def save_table(path: str, table: Table) -> None:
    output_path, _ = os.path.splitext(path)
    output_path += ".ecsv"
    log.info("Generating %s", output_path)
    table.write(output_path, format="ecsv", overwrite=True)


def create_npl_table(npl_path: str) -> Table:
    log.info("Converting NPL Calibration CSV to Astropy Table: %s", npl_path)
    table = astropy.io.ascii.read(
        npl_path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE.value, COL.RESP.value),
        converters={COL.WAVE.value: np.float64, COL.RESP.value: np.float64},
    )
    table[COL.WAVE.value] = np.round(table[COL.WAVE.value], decimals=0) * u.nm
    table[COL.RESP.value] = table[COL.RESP.value] * (u.A / u.W)
    table[COL.QE.value] = quantum_efficiency(table[COL.WAVE.value], table[COL.RESP.value])
    table.meta = {
        "Global": {
            "Manufacturer": "Hamamatsu",
            "Model": "S2281-04",
            "Serial": 1097,
            "Photosensitive area": 50 * (u.mm**2),
            "Dark current": 50 * (u.pA),
        },
        # stage1 processing
        "History": [
            {
                "Description": "Created NPL Calibration Table",
                "Date": None,
                "Start Wavelength": np.min(table[COL.WAVE.value]) * u.nm,
                "End Wavelength": np.max(table[COL.WAVE.value]) * u.nm,
            },
        ],
    }
    log.info("Generated table is\n%s", table.info)
    return table


def create_datasheet_table(path: str, x: float, y: float, threshold: float) -> Tuple[Table, Table]:
    """Returns the original NPL Table, the Datasheet"""
    log.info("Converting Datasheet CSV to Astropy Table: %s", path)
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE.value, COL.RESP.value),
        converters={COL.WAVE.value: np.float64, COL.RESP.value: np.float64},
    )
    table[COL.WAVE.value] = (table[COL.WAVE.value] + x) * u.nm
    table[COL.RESP.value] = np.round(table[COL.RESP.value] + y, decimals=5) * (u.A / u.W)
    table[COL.QE.value] = quantum_efficiency(table[COL.WAVE.value], table[COL.RESP.value])
    log.info("Selecting new datapoints outside the initial NPL data")
    mask = table[COL.WAVE.value] >= (threshold + 1.0)
    return table, table[mask]


def combine_tables(table1: Table, table2: Table, x: float, y: float) -> Table:
    log.info("Combining tables")
    table = astropy.table.vstack([table1, table2])
    history = {
        "Description": "Datasheet + PlotDigitizer extraction",
        "Date": "2024-01-01",
        "Start Wavelength": np.min(table2[COL.WAVE.value]) * u.nm,
        "End Wavelength": np.max(table2[COL.WAVE.value]) * u.nm,
        "Additional Processing": {
            "Comment": "Added offset to match input datasheet curve to NPL Calibration curve",
            "X Offset": x * u.nm,
            "Y Offset": y * (u.A / u.W),
        },
    }
    table.meta["History"].append(history)
    return table


def interpolate_table(table: Table, method: str, resolution: int) -> Table:
    wavelength = np.arange(350.0, 1051.0, resolution) * u.nm
    if method == "linear":
        responsivity = np.round(
            np.interp(wavelength, table[COL.WAVE.value], table[COL.RESP.value]), decimals=5
        ) * (u.A / u.W)
    else:
        interpolator = scipy.interpolate.Akima1DInterpolator(
            table[COL.WAVE.value], table[COL.RESP.value]
        )
        responsivity = np.round(interpolator(wavelength), decimals=5) * (u.A / u.W)
    qe = quantum_efficiency(wavelength, responsivity)
    qtable = Table(
        [wavelength, responsivity, qe], names=(COL.WAVE.value, COL.RESP.value, COL.QE.value)
    )
    qtable.meta = table.meta
    history = {
        "Description": "Resampled calibration data at regular intervals",
        "Resolution": resolution * u.nm,
        "Method": "linear"
        if method == "linear interpolation"
        else "Akima piecewise cubic polynomials",
        "Start Wavelength": np.min(qtable[COL.WAVE.value]) * u.nm,
        "End Wavelength": np.max(qtable[COL.WAVE.value]) * u.nm,
    }
    qtable.meta["History"].append(history)
    return qtable


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def stage1(args: Namespace) -> None:
    table = create_npl_table(npl_path=args.input_file)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += ".ecsv"
    log.info("Generating %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{table.meta['Global']['Serial']}",
            tables=[table],
            labels=["NPL Calib."],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )


def stage2(args: Namespace) -> None:
    """Iterative merge curves and saves the combined results"""
    log.info("Loading NPL ECSV calibration File: %s", args.npl_file)
    npl_table = astropy.io.ascii.read(args.npl_file, format="ecsv")
    threshold = np.max(npl_table[COL.WAVE.value]) + 1
    datasheet_table, sliced_table = create_datasheet_table(
        path=args.input_file,
        x=args.x,
        y=args.y,
        threshold=threshold,
    )
    plot_overlapped(
        title=f"{args.title} #{npl_table.meta['Global']['Serial']} overlapped curves",
        tables=[npl_table, datasheet_table],
        labels=["NPL Calib", "Datasheet"],
        filters=False,
        x=0,
        y=1,
        linewidth=0,
    )
    plot_overlapped(
        title=f"{args.title} #{npl_table.meta['Global']['Serial']} combined curves",
        tables=[npl_table, sliced_table],
        labels=["NPL Calib", "Datasheet"],
        filters=False,
        x=0,
        y=1,
        linewidth=0,
    )
    if args.save:
        merged_table = combine_tables(npl_table, sliced_table, args.x, args.y)
        output_path, _ = os.path.splitext(args.npl_file)
        output_path += "+Datasheet.ecsv"
        log.info("Generating %s", output_path)
        merged_table.write(output_path, delimiter=",", overwrite=True)


def stage3(args: Namespace) -> None:
    log.info("Loading NPL + Datasheet ECSV calibration File: %s", args.input_file)
    table = astropy.io.ascii.read(args.input_file, format="ecsv")
    log.info(table.info)
    interpolated_table = interpolate_table(table, args.method, args.resolution)
    log.info(interpolated_table.info)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += f"´+Interpolated@{args.resolution}nm.ecsv"
    log.info("Generating %s", output_path)
    interpolated_table.write(output_path, delimiter=",", overwrite=True)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{table.meta['Global']['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[interpolated_table, table],
            labels=["Interp.","NPL+Datasheet"],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )

def pipeline(args: Namespace) -> None:
    npl_table = create_npl_table(npl_path=args.npl_file)
    threshold = np.max(npl_table[COL.WAVE.value]) + 1
    datasheet_table, sliced_table = create_datasheet_table(
        path=args.input_file,
        x=args.x,
        y=args.y,
        threshold=threshold,
    )
    combined_table = combine_tables(npl_table, sliced_table, args.x, args.y)
    interpolated_table = interpolate_table(combined_table, args.method, args.resolution)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += f"+Datasheet+Interpolated@{args.resolution}nm.ecsv"
    log.info("Generating %s", output_path)
    interpolated_table.write(output_path, delimiter=",", overwrite=True)
    log.info(interpolated_table.info)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{npl_table.meta['Global']['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[interpolated_table, npl_table, sliced_table],
            labels=["Interp.","NPL Calib.", "Datasheet"],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )

# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def plot_parser() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-p",
        "--plot",
        action="store_true",
        help="Plot file",
    )
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default="Hamamatsu S2281-04",
        help="Plot title",
    )
    return parser


def interp_parser() -> ArgumentParser:
    """Common options for interpolation"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-m",
        "--method",
        type=str,
        choices=("linear", "cubic"),
        default="linear",
        help="Interpolation method (defaults to %(default)d nm)",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        choices=tuple(range(1, 11)),
        default=1,
        metavar="<N nm>",
        help="Interpolate at equal resolution (defaults to %(default)d nm)",
    )
    return parser


def combi_parser() -> ArgumentParser:
    """Common options to combine tables"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-n",
        "--npl-file",
        type=vfile,
        required=True,
        metavar="<NPL ECSV>",
        help="ECSV with NPL calibration",
    )
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with datasheet calibration values",
    )
    parser.add_argument(
        "-x",
        "--x",
        type=float,
        default=0.0,
        metavar="<X offset>",
        help="X (wavelength) offset to apply to input CSV file (defaults to %(default)f)",
    )
    parser.add_argument(
        "-y",
        "--y",
        type=float,
        default=0.0,
        metavar="<Y offset>",
        help="Y (responsivity) offset to apply to input CSV file (defaults to %(default)f)",
    )
    return parser


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_stage1 = subparser.add_parser(
        "stage1",
        parents=[
            plot_parser(),
        ],
        help="Load NPL calibration CSV and convert to ECSV",
    )
    parser_stage2 = subparser.add_parser(
        "stage2",
        parents=[combi_parser(), plot_parser()],
        help="Merges datasheet data to NPL calibration data and convert to ECSV",
    )
    parser_stage3 = subparser.add_parser(
        "stage3",
        parents=[plot_parser(), interp_parser()],
        help="Resamples calibration data to uniform 1nm wavelength step and convert to ECSV",
    )
    subparser.add_parser(
        "pipeline",
        parents=[plot_parser(), combi_parser(), interp_parser()],
        help="Pipleines all 3 stages",
    )
    # ------------------------------------------------------------------------
    parser_stage1.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with NPL calibration",
    )
    # ------------------------------------------------------------------------
    parser_stage2.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save combined file to ECSV",
    )
    # ------------------------------------------------------------------------
    parser_stage3.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<NPL ECSV>",
        help="ECSV with NPL + Datasheet calibration",
    )
    # ------------------------------------------------------------------------


# ================
# MAIN ENTRY POINT
# ================

COMMAND_TABLE = {
    "stage1": stage1,
    "stage2": stage2,
    "stage3": stage3,
    "pipeline": pipeline,
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
