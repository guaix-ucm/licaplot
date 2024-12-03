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
import scipy.interpolate

from lica.cli import execute
from lica.validators import vfile
from lica.photodiode import COL, BENCH, OSI as PHD

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


# -------------------
# Auxiliary functions
# -------------------


def quantum_efficiency(wavelength: np.ndarray, responsivity: np.ndarray) -> np.ndarray:
    """Computes the Quantum Efficiency given the Responsivity in A/W"""
    K = (const.h * const.c) / const.e
    return np.round(K * responsivity / wavelength.to(u.m), decimals=5) * u.dimensionless_unscaled


def create_osi_table(path: str) -> Table:
    log.info("Converting OSI Datasheet CSV to Astropy Table: %s", path)
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
        "Manufacturer": PHD.MANUF,
        "Model": PHD.MODEL,
        "Serial": PHD.SERIAL,
        "Window": PHD.WINDOW,
        "Photosensitive size diameter": PHD.PHS_SIZE,
        "Photosensitive area": PHD.PHS_AREA,
        "Dark current": PHD.DARK,
        "Peak responsivity": PHD.PEAK,
        "History": [],
    }
    history = {
        "Description": "Loaded Calibration Table from Datasheet",
        "Date": None,
        "Resolution": {
            "mean": np.round(np.mean(resolution),decimals=2) * u.mm,
            "sigma": np.round(np.std(resolution, ddof=1),decimals=1) * u.mm,
            "median": np.round(np.median(resolution),decimals=2) * u.mm,
        },
        "Comment": "Variable resolution",
        "Start wavelength": np.min(table[COL.WAVE]) * u.nm,
        "End wavelength": np.max(table[COL.WAVE]) * u.nm,
    }
    table.meta["History"].append(history)
    log.info("Generated table is\n%s", table.info)
    return table


def interpolate_table(table: Table, method: str, resolution: int) -> Table:
    wavelength = np.arange(BENCH.WAVE_START, BENCH.WAVE_END + 1, resolution) * u.nm
    if method == "linear":
        responsivity = np.round(
            np.interp(wavelength, table[COL.WAVE], table[COL.RESP]), decimals=5
        ) * (u.A / u.W)
    else:
        interpolator = scipy.interpolate.Akima1DInterpolator(table[COL.WAVE], table[COL.RESP])
        responsivity = np.round(interpolator(wavelength), decimals=5) * (u.A / u.W)
    qe = quantum_efficiency(wavelength, responsivity)
    qtable = Table([wavelength, responsivity, qe], names=(COL.WAVE, COL.RESP, COL.QE))
    qtable.meta = table.meta
    history = {
        "Description": "Resampled calibration data at regular intervals",
        "Resolution": resolution * u.nm,
        "Method": "linear interpolation"
        if method == "linear"
        else "Akima piecewise cubic polynomials",
        "Start wavelength": np.min(qtable[COL.WAVE]) * u.nm,
        "End wavelength": np.max(qtable[COL.WAVE]) * u.nm,
    }
    qtable.meta["History"].append(history)
    return qtable


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def method1(args: Namespace) -> None:
    raise NotImplementedError("Not yet available")


def method2(args: Namespace) -> None:
    datasheet_table = create_osi_table(path=args.input_file)
    interpolated_table = interpolate_table(datasheet_table, args.method, args.resolution)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += f"+Interpolated@{args.resolution}nm.ecsv"
    log.info("Generating %s", output_path)
    interpolated_table.write(output_path, delimiter=",", overwrite=True)
    log.info(interpolated_table.info)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{datasheet_table.meta['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[datasheet_table, interpolated_table, ],
            labels=["Datasheet","Interp.", ],
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
        help="Plot the result",
    )
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default=f"{PHD.MANUF} {PHD.MODEL}",
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
        help="Interpolation method (defaults to %(default)s)",
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
        "-rf",
        "--ref-file",
        type=vfile,
        required=True,
        metavar="<ECSV>",
        help="ECSV with Hamamatsu reference calibration",
    )
    parser.add_argument(
        "-os",
        "--osi-readings",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with OSI photodiode readings",
    )
    parser.add_argument(
        "-ha",
        "--hama-readings",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with Hamamatsu photodiode readings",
    )
    return parser


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_m1 = subparser.add_parser(
        "method1",
        parents=[combi_parser(), plot_parser()],
        help="By cross-calibration with Hamamatsu S2281",
    )
    parser_m1.set_defaults(func=method1)
    parser_m2 = subparser.add_parser(
        "method2",
        parents=[interp_parser(), plot_parser()],
        help="By digitizing the datasheet",
    )
    parser_m2.set_defaults(func=method2)
    # ------------------------------------------------------------------------
    parser_m1.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save resulting file to ECSV",
    )
    # ------------------------------------------------------------------------
    parser_m2.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV file with datasheet points",
    )
    parser_m2.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save resulting file to ECSV",
    )
    # ------------------------------------------------------------------------


# ================
# MAIN ENTRY POINT
# ================

def osi(args: Namespace) -> None:
    args.func(args)
  
def main():
    execute(
        main_func=osi,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="All about obtaining LICA's OSI photodiode calibration data and curves",
    )
