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

class FovColumns(Enum):
    ANGLE_UP = "Angle up(º)"
    FREQ_UP ="up light (Hz)"
    MAG_UP="up light (mag)"
    NOTES_UP="Notas up"
    DARK_FREQ_UP="up dark (Hz)"
    DARK_MAG_UP="up dark (mag)"
    ANGLE_SIDE="Angle side(º)"
    FREQ_SIDE="side light (Hz)"
    MAG_SIDE="light mag"
    NOTES_SIDE="Notas side"
    DARK_FREQ_SIDE="side dark (Hz)"
    DARK_MAG_SIDE="side dark (mag)"

# -------------------
# Auxiliary functions
# -------------------


def normalize(x: FloatArray) -> FloatArray:
    """Normalize an array wrt its max value."""
    maxi = np.max(x)
    if maxi == 0.0:
        raise ValueError("array full of zeros")
    return x / np.max(x)


@lru_cache(maxsize=None)
def fov_dataset(path: str, delimiter: str) -> dict[str, FloatArray]:
    """
    Transforma todos los arrays en una estructura de datos conveniente y la cachea
    """
    with open(path, "r", newline='') as csvfile:
        rows = csv.DictReader(csvfile, delimiter=delimiter)
        cols: Dict[str, list] = {}
        for row in rows:
            # inicualizar listas de valores la primera vez
            if not cols:
                cols = {k: [] for k in row.keys()}
            # Añadir cada valor convertido a float
            for k, v in row.items():
                if v.strip():  # Solo si hay un valor
                    cols[k].append(float(v))
                else:
                    cols[k].append(np.nan)
    # Convertir cada lista a np.ndarray[float64]
    return {k.strip(): np.array(v, dtype=np.float64) for k, v in cols.items()}


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


def plot_filter(
    wavelength: FloatArray,
    transmittance: FloatArray,
    label: str,
    irradiance: FloatArray,
    sky_label: str,
    qe: Optional[FloatArray] = None,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    axes.plot(
        wavelength,
        transmittance,
        marker="o",
        label=label,
    )
    axes.plot(wavelength, irradiance, label=sky_label, alpha=0.3)
    if qe is not None:
        axes.plot(wavelength, qe, label="TSL237 QE", linestyle="-.", color="black", alpha=0.5)
    for x, color in ((REF_CUTOFF, "red"), (720, "black")):
        axes.axvline(x, linestyle=":", label=f"{x} nm", color=color)
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Transmittance")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{label} response and natural sky emissions")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


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


def plot_combi(
    wavelength: FloatArray,
    response: FloatArray,
    label: str,
    input_signal: FloatArray,
    sky_label: str,
    output: FloatArray,
    mag: float,
    fwhm: Tuple[float, float, float],
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    # Respuesta espectral del sensor TSL237
    response_plot = axes.plot(wavelength, response, label=f"{label} spectral resp.")
    color = response_plot[0].get_color()
    # sobreimpone la curva de FWHM sobre la respuesta espectral, mismo color
    fwhm, xfw1, xfw2 = fwhm  # unpack tuple
    mask = (xfw1 <= wavelength) & (wavelength <= xfw2)
    ww = np.insert(wavelength[mask], 0, xfw1)
    ww = np.insert(ww, -1, xfw2)
    rr = np.insert(response[mask], 0, 0.5)
    rr = np.insert(rr, -1, 0.5)
    axes.plot(ww, rr, linewidth=5, color=color, label="FWHM line", alpha=0.5)
    # Señal de entrada y salida
    axes.plot(wavelength, input_signal, label=f"{sky_label} night sky", alpha=0.3)
    axes.plot(wavelength, output, label=f"{sky_label} by {label}", alpha=0.5)
    # pinta lineas verticales interesantes
    xfw2 = int(round(xfw2, 0))
    if xfw2 != REF_CUTOFF:
        axes.axvline(REF_CUTOFF, linestyle=":", label=f"{REF_CUTOFF} nm (ref.)", color="red")
        axes.axvline(xfw2, linestyle=":", label=f"{xfw2} nm (fwhm boundary)", color="black")
    else:
        axes.axvline(
            REF_CUTOFF, linestyle=":", label=f"{REF_CUTOFF} nm (ref. + fwhm boundary)", color="red"
        )
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Response (norm.)")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{label} response and natural sky emissions")
    plot_box(axes, (f"mag = {mag:0.2f}\nFWHM = {fwhm:0.0f} nm", 0.83, 0.45))
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


def plot_combi_stacked(
    wavelength: FloatArray,
    responses: Sequence[FloatArray],
    labels: Sequence[str],
    input_signal: FloatArray,
    sky_label: str,
    outputs: Sequence[FloatArray],
    mag_diffs: Sequence[FloatArray],
    base_magnitude: float,
    fwhms: Sequence[Tuple[float, float, float]],
    save_path: Optional[str] = None,
) -> None:
    N = len(labels)
    fig, axes = plt.subplots(N, 1, figsize=(12, 4 * N))
    for axe, response, output, label, mag_diff, fwhm in zip(
        axes, responses, outputs, labels, mag_diffs, fwhms
    ):
        mag = base_magnitude + mag_diff
        # Respuesta espectral del sensor TSL237
        axe.plot(wavelength, response, label=f"{label} spectral resp.")
        # Señal de entrada y salida
        axe.plot(wavelength, input_signal, label=f"{sky_label} night sky", alpha=0.3)
        axe.plot(wavelength, output, label=f"{sky_label} by {label}", alpha=0.5)
        fwhm, xfw1, xfw2 = fwhm  # unpack tuple
        xfw2 = int(round(xfw2, 0))
        if xfw2 != REF_CUTOFF:
            axe.axvline(REF_CUTOFF, linestyle=":", label=f"{REF_CUTOFF} nm (ref.)", color="red")
            axe.axvline(xfw2, linestyle=":", label=f"{xfw2} nm (fwhm boundary)", color="black")
        else:
            axe.axvline(
                REF_CUTOFF,
                linestyle=":",
                label=f"{REF_CUTOFF} nm (ref. + fwhm boundary)",
                color="red",
            )
        xlow = np.floor(np.min(wavelength))
        xhigh = np.ceil(np.max(wavelength))
        axe.set_xlim(xlow, xhigh)
        axe.set_xlabel("Wavelength (nm)")
        axe.set_ylabel("Response (norm.)")
        axe.legend()
        axe.grid(True, alpha=0.3)
        axe.set_title(f"{label} response and natural sky emissions")
        if mag_diff == 0:
            plot_box(axe, (f"mag = {mag:0.2f}\nFWHM = {fwhm:0.0f} nm", 0.83, 0.40))
        else:
            plot_box(axe, (f"\u0394mag = {mag_diff:0.2f}\nFWHM = {fwhm:0.0f} nm", 0.83, 0.40))
        plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


def plot_filters(
    wavelength: FloatArray,
    transmittances: Sequence[FloatArray],
    labels: Sequence[str],
    irradiance: FloatArray,
    sky_label: Sequence[str],
    qe: Optional[FloatArray] = None,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    for transmittance, label in zip(transmittances, labels):
        axes.plot(
            wavelength,
            transmittance,
            label=label,
        )
    axes.plot(wavelength, irradiance, label=sky_label, color="black", alpha=0.3)
    if qe is not None:
        axes.plot(wavelength, qe, label="TSL237 QE", linestyle="-.", color="black", alpha=0.5)

    for x, color in ((REF_CUTOFF, "red"), (720, "black")):
        axes.axvline(x, linestyle=":", label=f"{x} nm", color=color)
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Transmittance")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title("several TESS-W filters response and natural sky emissions")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

def plot_filters_skies(
    wavelength: FloatArray,
    transmittances: Sequence[FloatArray],
    labels: Sequence[str],
    irradiances: Sequence[FloatArray],
    sky_labels: Sequence[str],
    qe: Optional[FloatArray] = None,
    save_path: Optional[str] = None,
) -> None:
    N = len(sky_labels)
    fig, axes = plt.subplots(N, 1, figsize=(12, 4 * N))
    for axe, irradiance, sky_label in zip(axes, irradiances, sky_labels):
        for transmittance, label in zip(transmittances, labels):
            axe.plot(wavelength, transmittance,label=label)
        if qe is not None:
            axe.plot(wavelength, qe, label="TSL237 QE", linestyle="-.", color="black", alpha=0.5)
        for x, color in ((REF_CUTOFF, "red"), (720, "black")):
            axe.axvline(x, linestyle=":", label=f"{x} nm", color=color)
        axe.plot(wavelength, irradiance, label=sky_label, color="black", alpha=0.3)
        xlow = np.floor(np.min(wavelength))
        xhigh = np.ceil(np.max(wavelength))
        axe.set_xlim(xlow, xhigh)
        axe.set_xlabel("Wavelength (nm)")
        axe.set_ylabel("Transmittance")
        axe.legend()
        axe.grid(True, alpha=0.3)
        axe.set_title(f"TESS-W filters response and {sky_label} sky emissions")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()
    


def plot_alpy_sky(
    wavelength: FloatArray,
    sky_data: FloatArray,
    sky_label: str,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    # datos del cielo nocturno
    axes.plot(wavelength, sky_data, label=f"ALPY {sky_label}", alpha=0.5)
    # pinta lineas verticales interesantes
    axes.axvline(REF_CUTOFF, linestyle=":", label=f"{REF_CUTOFF} nm (ref.)", color="red")
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Night sky")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{sky_label} natural sky emissions")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


def plot_sand_sky(
    wavelength: FloatArray,
    sky_data_bfr: FloatArray,
    sky_data_aft: FloatArray,
    sky_label: str,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    # datos del cielo nocturno
    axes.plot(wavelength, sky_data_bfr, label=f"SAND (before midnight) {sky_label}", alpha=0.5)
    axes.plot(wavelength, sky_data_aft, label=f"SAND (after midnight) {sky_label}", alpha=0.5)
    # pinta lineas verticales interesantes
    axes.axvline(REF_CUTOFF, linestyle=":", label=f"{REF_CUTOFF} nm (ref.)", color="red")
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Night sky")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{sky_label} natural sky emissions")
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
    dataset = fov_dataset(args.input_file, delimiter=",")


def cli_plot_fov_multi(args: Namespace) -> None:
    pass


def cli_plot_fov_stacked(args: Namespace) -> None:
    pass



def choices3() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--up', action='store_true', help="Up FoV curve only")
    group.add_argument('--side', action='store_true', help="Side FoV curve only")
    group.add_argument('--both', action='store_true', help="Both up & side FoV curves")
    return parser

def choices2() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--up', action='store_true', help="Up FoV curve only")
    group.add_argument('--side', action='store_true', help="Side FoV curve only")
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
    parser_multi = subparser.add_parser(
        "multi",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            choices2(),
        ],
        help="Plot several TESS-W Fov curves in the same graphics",
    )
    parser_multi.set_defaults(func=cli_plot_fov_multi)

    parser_combi = subparser.add_parser(
        "stacked",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            choices2(),
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
