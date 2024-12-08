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
from typing import Tuple

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
from lica.photodiode import COL, BENCH, Hamamatsu

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


def offset_box(x_offset: float, y_offset: float, x: float = 0.5, y: float = 0.2):
    return ("\n".join((f"x offset= {x_offset:.1f}", f"y offset = {y_offset:0.3f}")), x, y)


def quantum_efficiency(wavelength: np.ndarray, responsivity: np.ndarray) -> np.ndarray:
    """Computes the Quantum Efficiency given the Responsivity in A/W"""
    K = (const.h * const.c) / const.e
    return np.round(K * responsivity / wavelength.to(u.m), decimals=5) * u.dimensionless_unscaled


def create_npl_table(npl_path: str) -> Table:
    log.info("Converting NPL Calibration CSV to Astropy Table: %s", npl_path)
    table = astropy.io.ascii.read(
        npl_path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE, COL.RESP),
        converters={COL.WAVE: np.float64, COL.RESP: np.float64},
    )
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[COL.RESP] = table[COL.RESP] * (u.A / u.W)
    table[COL.QE] = quantum_efficiency(table[COL.WAVE], table[COL.RESP])
    table.meta = {
        "Manufacturer": Hamamatsu.MANUF,
        "Model": Hamamatsu.MODEL,
        "Serial": Hamamatsu.SERIAL,
        "Window": Hamamatsu.WINDOW,
        "Photosensitive size diameter": Hamamatsu.PHS_SIZE,
        "Photosensitive area": Hamamatsu.PHS_AREA,
        "Dark current": Hamamatsu.DARK,
        "Peak responsivity": Hamamatsu.PEAK,
        "History": [],
    }
    history = {
        "Description": "National Physical Laboratory (NPL) Calibration",
        "Date": "2010-10-08",
        "Resolution": 20 * u.nm,
        "Comment": "Resolution is constant except for the last data point",
        "Start wavelength": np.min(table[COL.WAVE]) * u.nm,
        "End wavelength": np.max(table[COL.WAVE]) * u.nm,
    }
    table.meta["History"].append(history)
    log.info("Generated table is\n%s", table.info)
    return table


def create_datasheet_table(path: str, x: float, y: float, threshold: float) -> Tuple[Table, Table]:
    """Returns the original NPL Table, the Datasheet"""
    log.info("Converting Datasheet CSV to Astropy Table: %s", path)
    table = astropy.io.ascii.read(
        path,
        delimiter=";",
        data_start=1,
        names=(COL.WAVE, COL.RESP),
        converters={COL.WAVE: np.float64, COL.RESP: np.float64},
    )
    table[COL.WAVE] = (table[COL.WAVE] + x) * u.nm
    table[COL.RESP] = np.round(table[COL.RESP] + y, decimals=5) * (u.A / u.W)
    table[COL.QE] = quantum_efficiency(table[COL.WAVE], table[COL.RESP])
    log.info("Selecting new datapoints outside the initial NPL data")
    mask = table[COL.WAVE] >= (threshold + 1.0)
    return table, table[mask]


def combine_tables(table1: Table, table2: Table, x: float, y: float) -> Table:
    log.info("Combining tables")
    table = astropy.table.vstack([table1, table2])
    history = {
        "Description": "Datasheet with PlotDigitizer extraction",
        "Date": "2024-01-01",
        "Start wavelength": np.min(table2[COL.WAVE]) * u.nm,
        "End wavelength": np.max(table2[COL.WAVE]) * u.nm,
        "Additional Processing": {
            "Comment": "Added offset to match input datasheet curve to NPL Calibration curve",
            "X offset": x * u.nm,
            "Y offset": y * (u.A / u.W),
        },
    }
    table.meta["History"].append(history)
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


def cli_stage1(args: Namespace) -> None:
    table = create_npl_table(npl_path=args.input_file)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += ".ecsv"
    log.info("Generating %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)
    if args.plot:
        x = table.colnames.index(COL.WAVE)
        y = table.colnames.index(COL.RESP)
        plot_overlapped(
            title=f"{args.title} #{table.meta['Serial']}",
            tables=[table],
            labels=["NPL Calib."],
            filters=False,
            x=x,
            y=y,
            linewidth=0,
        )


def cli_stage2(args: Namespace) -> None:
    """Iterative merge curves and saves the combined results"""
    log.info("Loading NPL ECSV calibration File: %s", args.input_file)
    npl_table = astropy.io.ascii.read(args.input_file, format="ecsv")
    threshold = np.max(npl_table[COL.WAVE]) + 1
    x = npl_table.colnames.index(COL.WAVE)
    y = npl_table.colnames.index(COL.RESP)
    datasheet_table, sliced_table = create_datasheet_table(
        path=args.datasheet_file,
        x=args.x,
        y=args.y,
        threshold=threshold,
    )
    plot_overlapped(
        title=f"{args.title} #{npl_table.meta['Serial']} overlapped curves",
        tables=[npl_table, datasheet_table],
        labels=["NPL Calib", "Datasheet"],
        filters=False,
        x=x,
        y=y,
        linewidth=0,
        box=offset_box(x_offset=args.x, y_offset=args.y, x=0.02, y=0.8),
    )
    plot_overlapped(
        title=f"{args.title} #{npl_table.meta['Serial']} combined curves",
        tables=[npl_table, sliced_table],
        labels=["NPL Calib", "Datasheet"],
        filters=False,
        x=x,
        y=y,
        linewidth=0,
        box=offset_box(x_offset=args.x, y_offset=args.y, x=0.02, y=0.8),
    )
    if args.save:
        merged_table = combine_tables(npl_table, sliced_table, args.x, args.y)
        output_path, _ = os.path.splitext(args.input_file)
        output_path += "+Datasheet.ecsv"
        log.info("Generating %s", output_path)
        merged_table.write(output_path, delimiter=",", overwrite=True)


def cli_stage3(args: Namespace) -> None:
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
        x = interpolated_table.colnames.index(COL.WAVE)
        y = interpolated_table.colnames.index(COL.RESP)
        plot_overlapped(
            title=f"{args.title} #{table.meta['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[interpolated_table, table],
            labels=["Interp.", "NPL+Datasheet"],
            filters=False,
            x=x,
            y=y,
            linewidth=0,
        )


def cli_pipeline(args: Namespace) -> None:
    npl_table = create_npl_table(npl_path=args.input_file)
    threshold = np.max(npl_table[COL.WAVE]) + 1
    datasheet_table, sliced_table = create_datasheet_table(
        path=args.datasheet_file,
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
        x = interpolated_table.colnames.index(COL.WAVE)
        y = interpolated_table.colnames.index(COL.RESP)
        plot_overlapped(
            title=f"{args.title} #{npl_table.meta['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[interpolated_table, npl_table, sliced_table],
            labels=["Interp.", "NPL Calib.", "Datasheet"],
            filters=False,
            x=x,
            y=y,
            linewidth=0,
            box=offset_box(x_offset=args.x, y_offset=args.y, x=0.02, y=0.8),
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
        default=f"{Hamamatsu.MANUF} {Hamamatsu.MODEL}",
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
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<NPL ECSV>",
        help="ECSV with NPL calibration",
    )
    parser.add_argument(
        "-d",
        "--datasheet-file",
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
    parser_stage1.set_defaults(func=cli_stage1)
    parser_stage2 = subparser.add_parser(
        "stage2",
        parents=[combi_parser(), plot_parser()],
        help="Merges datasheet data to NPL calibration data and convert to ECSV",
    )
    parser_stage2.set_defaults(func=cli_stage2)
    parser_stage3 = subparser.add_parser(
        "stage3",
        parents=[plot_parser(), interp_parser()],
        help="Resamples calibration data to uniform 1nm wavelength step and convert to ECSV",
    )
    parser_stage3.set_defaults(func=cli_stage3)
    parser_pipe = subparser.add_parser(
        "pipeline",
        parents=[plot_parser(), combi_parser(), interp_parser()],
        help="Pipleines all 3 stages",
    )
    parser_pipe.set_defaults(func=cli_pipeline)
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


def cli_main(args: Namespace):
    args.func(args)


def main():
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="All about obtaining LICA's Hamamatsu photodiode calibration data and curves",
    )
