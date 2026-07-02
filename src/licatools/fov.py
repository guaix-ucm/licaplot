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

import csv
import logging
from argparse import Namespace, ArgumentParser
from enum import StrEnum
from importlib.resources import files
from functools import lru_cache
from typing import TypeAlias, Sequence, Dict, Tuple, Optional

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy
from astropy.table import Table
from scipy import integrate
from lica.cli import execute

from lica.lab.photodiode import COL
from lica.validators import vfile

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import parser as prs

# --------------
# New Type Hints
# --------------

FloatSeq: TypeAlias = Sequence[float]
FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

# ----------------
# Module constants
# ----------------

LICA_PKG = "licatools.resources.data"


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licatools.resources.global")
mpl.rcParams["legend.fontsize"] = "xx-small"


# -----
# Enums
# -----


class Col(StrEnum):
    ANGLE_UP = "Angle [up] (º)"
    FREQ_UP = "Light [up] (Hz)"
    MAG_UP = "Light [up] (mag)"
    NOTES_UP = "Notes [up]"
    DARK_FREQ_UP = "Dark [up] (Hz)"
    DARK_MAG_UP = "Dark [up] (mag)"
    ANGLE_SIDE = "Angle [side] (º)"
    FREQ_SIDE = "Light [side] (Hz)"
    MAG_SIDE = "Light [side] (mag)"
    NOTES_SIDE = "Notes [side] "
    DARK_FREQ_SIDE = "Dark [side] (Hz)"
    DARK_MAG_SIDE = "Dark [side] (mag)"


# -------------------
# Auxiliary functions
# -------------------


# He probado con scipy find_peaks y peaks_width y no me ha funcionado bien
# porque la curva tiene maximos locales por oscilaciones en la parte de arriba.
# Asi que esta funcion mas manual funciona mejor
def get_fwhm(x: FloatArray, y: FloatArray) -> Tuple[float, float, float]:
    """
    Calcula el Full Width Half Maximum (FWHM) y los puntos x donde una curva
    cruza la mitad del máximo.

    Parámetros:
        x: array numpy con los valores del eje X
        y: array numpy con los valores del eje Y (la curva)

    Devuelve:
        fwhm: ancho completo a mitad del máximo
        x_left: punto x donde la curva cruza half_max por la izquierda
        x_right: punto x donde la curva cruza half_max por la derecha
    """
    # Encontrar el máximo de la curva
    half_max = np.max(y) / 2.0
    # Encontrar el índice del máximo
    peak_idx = np.argmax(y)
    # Buscar el cruce por la izquierda (antes del pico)
    # Encontrar donde y pasa de estar <= half_max a > half_max
    y_left = y[0 : peak_idx + 1]
    x_left_arr = x[0 : peak_idx + 1]
    # Encontrar los dos puntos vecinos al cruce
    left_above = np.where(y_left >= half_max)[0]
    if len(left_above) == 0:
        raise ValueError("No se encontró cruce por la izquierda")
    i_left = left_above[0]  # primer punto >= half_max
    if i_left == 0:
        x_left = x_left_arr[0]
    else:
        # Interpolación lineal entre i_left-1 e i_left
        y1, y2 = y_left[i_left - 1], y_left[i_left]
        x1, x2 = x_left_arr[i_left - 1], x_left_arr[i_left]
        x_left = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1)
    # Buscar el cruce por la derecha (despues del pico)
    y_right = y[peak_idx:-1]
    x_right_arr = x[peak_idx:-1]
    # Encontrar donde y pasa de estar >= half_max a < half_max
    right_above = np.where(y_right >= half_max)[0]
    if len(right_above) == 0:
        raise ValueError("No se encontró cruce por la derecha")
    i_right = right_above[-1]  # último punto >= half_max
    if i_right == len(y_right) - 1:
        x_right = x_right_arr[-1]
    else:
        # Interpolación lineal entre i_right e i_right+1
        y1, y2 = y_right[i_right], y_right[i_right + 1]
        x1, x2 = x_right_arr[i_right], x_right_arr[i_right + 1]
        x_right = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1)
    # Calculo del FWHM
    fwhm = x_right - x_left
    return fwhm, x_left, x_right


# ------------------
# Plotting functions
# ------------------


def plot_box(
    axes,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    axes.text(
        x=box[1],
        y=box[2],
        s=box[0],
        transform=axes.transAxes,
        va="top",
        bbox=props,
        fontsize="x-small",
    )


def plot_fov_single(
    phot_name: str,
    table: Table,
    freq_up: bool,
    freq_side: bool,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    # response_plot = axes.plot(wavelength, response, label=f"{label} spectral resp.")
    # color = response_plot[0].get_color()
    if freq_up:
        mask = ~(table[Col.FREQ_UP].mask)
        axes.plot(
            table[Col.ANGLE_UP][mask], table[Col.FREQ_UP][mask], marker="o", label=f"{phot_name} up"
        )
        axes.plot(
            table[Col.ANGLE_UP],
            table[Col.DARK_FREQ_UP],
            marker="v",
            label=f"{phot_name} up [dark]",
            alpha=0.5,
        )
    if freq_side is not None:
        mask = ~(table[Col.FREQ_SIDE].mask)
        axes.plot(
            table[Col.ANGLE_SIDE][mask],
            table[Col.FREQ_SIDE][mask],
            marker="o",
            label=f"{phot_name} side",
        )
        axes.plot(
            table[Col.ANGLE_SIDE],
            table[Col.DARK_FREQ_SIDE],
            marker="^",
            label=f"{phot_name} side [dark]",
            alpha=0.5,
        )
    xlow = np.floor(min(np.min(table[Col.ANGLE_UP]), np.min(table[Col.ANGLE_SIDE])))
    xhigh = np.ceil(max(np.max(table[Col.ANGLE_UP]), np.max(table[Col.ANGLE_SIDE])))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Angle (Deg)")
    axes.set_ylabel("Signal (Hz)")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{phot_name} Field of View")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


def plot_fov_stacked(
    phot_names: Sequence[str],
    fov_tables: Sequence[Table],
    save_path: Optional[str] = None,
) -> None:
    N = 2
    cols_up = (Col.ANGLE_UP, Col.FREQ_UP, Col.DARK_FREQ_UP)
    cols_side = (Col.ANGLE_SIDE, Col.FREQ_SIDE, Col.DARK_FREQ_SIDE)
    fig, axes = plt.subplots(N, 1, figsize=(12, 4 * N))
    for axe, cols, tag in zip(axes, (cols_up, cols_side), ("up", "side")):
        for phot_name, table in zip(phot_names, fov_tables):
            mask = ~(table[cols[1]].mask)
            axe.plot(
                table[cols[0]][mask], table[cols[1]][mask], marker="o", label=f"{phot_name} {tag}"
            )
            axe.plot(
                table[cols[0]],
                table[cols[2]],
                marker="v",
                label=f"{phot_name} {tag} [dark]",
                alpha=0.5,
            )
        xlow = np.floor(min(np.min(table[Col.ANGLE_UP]), np.min(table[Col.ANGLE_SIDE])))
        xhigh = np.ceil(max(np.max(table[Col.ANGLE_UP]), np.max(table[Col.ANGLE_SIDE])))
        axe.set_xlim(xlow, xhigh)
        axe.set_xlabel("Angle (Deg)")
        axe.set_ylabel("Signal (Hz)")
        axe.legend()
        axe.grid(True, alpha=0.3)
        axe.set_title(f"{tag.title()} Field of View")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def cli_plot_fov_single(args: Namespace) -> None:
    log.info("reading filter data %s", args.input_file)
    table: Table = astropy.io.ascii.read(args.input_file, format="csv")
    freq_up = False if args.side else True
    freq_side = False if args.up else True
    plot_fov_single(
        phot_name=" ".join(args.label),
        table=table,
        freq_up=freq_up,
        freq_side=freq_side,
    )


def cli_plot_fov_stacked(args: Namespace) -> None:
    log.info("reading FoV data from files %s", args.input_file)
    tables = [astropy.io.ascii.read(path, format="csv") for path in args.input_file]
    plot_fov_stacked(
        phot_names=args.labels,
        fov_tables=tables,
    )


def cli_plot_fov_multi(args: Namespace) -> None:
    pass


def choices3() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--up", action="store_true", help="Up FoV curve only")
    group.add_argument("--side", action="store_true", help="Side FoV curve only")
    group.add_argument("--both", action="store_true", help="Both [up] & [side]  FoV curves")
    return parser


def ifiles() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        nargs="+",
        metavar="<File>",
        help="CSV/ECSV input files",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        default=",",
        help="CSV column delimiter. (defaults to %(default)s)",
    )
    parser.add_argument(
        "-c",
        "--columns",
        type=str,
        default=None,
        nargs="+",
        metavar="<NAME>",
        help="Optional ordered list of CSV column names, if necessary (default %(default)s)",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.ifile(),
            prs.label("plotting"),
            prs.savefig(),
            choices3(),
        ],
        help="Plot single TESS-W FoV curves",
    )
    parser_single.set_defaults(func=cli_plot_fov_single)
    parser_combi = subparser.add_parser(
        "stacked",
        parents=[
            ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
        ],
        help="Plot several TESS-W Fov curves in diifferent graphics",
    )
    parser_combi.set_defaults(func=cli_plot_fov_stacked)


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
        description="Plot TESS-W field of view",
    )
