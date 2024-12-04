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
from lica.validators import vfile
from lica.photodiode import PhotodiodeModel, COL, BENCH, Hamamatsu, OSI
import lica.photodiode

# ------------------------
# Own modules and packages
# ------------------------

from . import TBCOL
from ._version import __version__
from .utils.mpl import plot_overlapped
from .utils.validators import vecsvfile

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


def plot_cross(
    title: Optional[str],
    cross_resp: np.ndarray,
    datasheet_resp: np.ndarray,
    linewidth: Optional[int] = 0,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    """Plot all datasets in the same Axes using different markers"""

    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    axes.set_xlabel(f"{COL.RESP} Datasheet method")
    axes.set_ylabel(f"{COL.RESP} Cross calibration method")
    axes.plot(cross_resp, datasheet_resp, linewidth=linewidth, marker="o", label="Data points")
    axes.axline((0, 0), slope=1)
    if box:
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        axes.text(x=box[1], y=box[2], s=box[0], transform=axes.transAxes, va="top", bbox=props)
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


def scan_csv_to_table(path):
    table = astropy.io.ascii.read(
        path,
        delimiter="\t",
        data_start=0,
        names=("Index", COL.WAVE, "Current"),
        converters={"Index": np.float64, COL.WAVE: np.float64, COL.RESP: np.float64},
    )
    table[TBCOL.INDEX] = table[TBCOL.INDEX].astype(np.int32)
    table[COL.WAVE] = np.round(table[COL.WAVE], decimals=0) * u.nm
    table[TBCOL.CURRENT] = table[TBCOL.CURRENT] * u.A
    return table


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


def cross_calibrate(
    osi_readings: Table, hama_readings: Table, hama_reference: Table, resolution: int
) -> Table:
    osi_responsivity = hama_reference[COL.RESP] * (
        osi_readings[TBCOL.CURRENT] / hama_readings[TBCOL.CURRENT]
    )
    osi_qe = Column(quantum_efficiency(osi_readings[COL.WAVE], osi_responsivity), name=COL.QE)
    osi_responsivity = Column(np.round(osi_responsivity, decimals=5) * (u.A / u.W), name=COL.RESP)
    table = Table([hama_reference[COL.WAVE], osi_responsivity, osi_qe])
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
        "Description": f"Cross calibrated with {PhotodiodeModel.HAMAMATSU}",
        "Resolution": resolution * u.nm,
        "Start wavelength": np.min(table[COL.WAVE]) * u.nm,
        "End wavelength": np.max(table[COL.WAVE]) * u.nm,
    }
    table.meta["History"].append(history)
    log.info(table.info)
    return table


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def method1(args: Namespace) -> None:
    log.info("reads the reference calibration photodiode data %s", PhotodiodeModel.HAMAMATSU)
    hama_reference = lica.photodiode.load(
        PhotodiodeModel.HAMAMATSU,
        args.resolution,
        BENCH.WAVE_START,
        BENCH.WAVE_END - 1,  # ScanExe alwais skips the end wavelength :-(
    )
    osi_readings = scan_csv_to_table(args.osi_readings)
    hama_readings = scan_csv_to_table(args.hama_readings)
    osi_reference = cross_calibrate(osi_readings, hama_readings, hama_reference, args.resolution)
    output_path = f"{PhotodiodeModel.OSI}+Cross-Calibrated@{args.resolution}nm.ecsv"
    if args.save:
        osi_reference.write(output_path, delimiter=",", overwrite=True)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{osi_reference.meta['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[osi_reference, hama_reference],
            labels=[
                "OSI",
                "Hamamatsu.",
            ],
            filters=True,
            x=0,
            y=1,
            linewidth=0,
        )


def method2(args: Namespace) -> None:
    datasheet_table = create_osi_table(path=args.input_file)
    interpolated_table = interpolate_table(datasheet_table, args.method, args.resolution)
    output_path, _ = os.path.splitext(args.input_file)
    output_path += f"+Interpolated@{args.resolution}nm.ecsv"
    log.info("Generating %s", output_path)
    if args.save:
        interpolated_table.write(output_path, delimiter=",", overwrite=True)
    log.info(interpolated_table.info)
    if args.plot:
        plot_overlapped(
            title=f"{args.title} #{datasheet_table.meta['Serial']} interpolated curves @ {args.resolution} nm",
            tables=[
                datasheet_table,
                interpolated_table,
            ],
            labels=[
                "Datasheet",
                "Interp.",
            ],
            filters=False,
            x=0,
            y=1,
            linewidth=0,
        )


def compare(args: Namespace) -> None:
    table1 = astropy.io.ascii.read(args.cross_file, format="ecsv")
    table2 = astropy.io.ascii.read(args.datasheet_file, format="ecsv")[0:-1]
    hama_reference = lica.photodiode.load(
        PhotodiodeModel.HAMAMATSU,
        1,
        BENCH.WAVE_START,
        BENCH.WAVE_END - 1,  # ScanExe alwais skips the end wavelength :-(
    )
    osi = f"{OSI.MANUF} {OSI.MODEL}"
    hama = f"{Hamamatsu.MANUF} {Hamamatsu.MODEL}"
    log.info(table1.colnames.index(COL.WAVE))
    x = table1.colnames.index(COL.WAVE)
    y = table1.colnames.index(COL.QE) if args.qe else table1.colnames.index(COL.RESP)
    if args.plot:
        plot_overlapped(
            title=args.title,
            tables=[table1, table2, hama_reference],
            labels=[f"{osi} Cross Calibrated", f"{osi} From Datasheet", f"{hama} (Ref.)"],
            filters=True,
            x=x,
            y=y,
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
        default=f"{OSI.MANUF} {OSI.MODEL}",
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
        "--osi",
        dest="osi_readings",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with OSI photodiode readings",
    )
    parser.add_argument(
        "--hama",
        dest="hama_readings",
        type=vfile,
        required=True,
        metavar="<CSV>",
        help="CSV with Hamamatsu photodiode readings",
    )
    return parser


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command")
    # ---------------------------------------------------------------
    parser_m1 = subparser.add_parser(
        "cross",
        parents=[combi_parser(), plot_parser()],
        help="By cross-calibration with Hamamatsu S2281",
    )
    parser_m1.set_defaults(func=method1)
    parser_m1.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save resulting file to ECSV",
    )
    # ---------------------------------------------------------------
    parser_m2 = subparser.add_parser(
        "datasheet",
        parents=[interp_parser(), plot_parser()],
        help="By digitizing the datasheet",
    )
    parser_m2.set_defaults(func=method2)
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        choices=tuple(range(1, 11)),
        default=1,
        metavar="<N nm>",
        help="Interpolate at equal resolution (defaults to %(default)d nm)",
    )
    parser_m2.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save resulting file to ECSV",
    )
    # ------------------------------------------------------------------------
    parser_comp = subparser.add_parser(
        "compare",
        parents=[plot_parser()],
        help="Comparing between cross calibration and datasheet methods",
    )
    parser_comp.set_defaults(func=compare)
    parser_comp.add_argument(
        "-q",
        "--qe",
        action="store_true",
        help="Plot Quantum Eficiency instead of Responsivity",
    )
    parser_comp.add_argument(
        "-c",
        "--cross-file",
        type=vecsvfile,
        required=True,
        metavar="<ECSV FILE>",
        help="OSI ECSV file obtained by cross-calibration",
    )
    parser_comp.add_argument(
        "-d",
        "--datasheet-file",
        type=vecsvfile,
        required=True,
        metavar="<ECSV FILE>",
        help="OSI ECSV file obtained by digitizing datasheet",
    )


# ================
# MAIN ENTRY POINT
# ================


def osi(args: Namespace):
    args.func(args)


def main():
    execute(
        main_func=osi,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="All about obtaining LICA's OSI photodiode calibration data and curves",
    )
