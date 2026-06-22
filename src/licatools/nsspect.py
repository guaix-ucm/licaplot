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
CAHA_NIGHT_SKY_FILE = "caha_night_spec.tsv"
MADRID_2014_SKY_FILE = "UCM-SAND_1_2_spectra_201404.csv"
MADRID_2020_SKY_FILE = "Madrid_sky_spectrum_alpy_20200518.csv"
TSL237_RESP_LICA = "TSL237_responsivity_LICA.tsv"
TSL237_RESP_DATA = "TSL237_responsivity_datasheet.csv"

REF_CUTOFF = 740  # theoretical UV/IR cutoff filter

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


class NightSky(StrEnum):
    CAHA = "CAHA"
    MADRID_OLD = "Madrid (2014)"
    MADRID_NEW = "Madrid (2020)"


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
def resource(resource_name: str, delimiter: str) -> dict[str, FloatArray]:
    """
    Transforma todos los arrays en una estructura de datos conveniente y la cachea
    """
    reso = files(LICA_PKG).joinpath(resource_name).read_text(encoding="utf-8").splitlines()
    rows = csv.DictReader(reso, delimiter=delimiter)
    cols: Dict[str, list] = {}
    for row in rows:
        # inicualizar listas de valores la primera vez
        if not cols:
            cols = {k: [] for k in row.keys()}
        # Añadir cada valor convertido a float
        for k, v in row.items():
            if v.strip():  # Solo si hay un valor
                cols[k].append(float(v))
    # Convertir cada lista a np.ndarray[float64]
    return {k.strip(): np.array(v, dtype=np.float64) for k, v in cols.items()}


def get_tsl237_responsivity_resource(lica: bool = False) -> Tuple[FloatArray, FloatArray]:
    """
    Obtiene el array numpy de la QE del TSL237
    """
    if lica:
        result = resource(TSL237_RESP_LICA, delimiter="\t")  # Medida en laboratorio
        return result["Wavelength [nm]"], result["Responsivity (normalized)"]
    else:
        result = resource(TSL237_RESP_DATA, delimiter=",")
        return result["Wavelength [nm]"], result["Responsivity (normalized)"]


def caha_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", CAHA_NIGHT_SKY_FILE)
    result = resource(CAHA_NIGHT_SKY_FILE, delimiter="\t")
    wave, irrad = result["Wavelength"], result["Irradiance"]
    wave = wave / 10  # from Amstrongs to nanomenters
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad = np.interp(x=wavelength, xp=wave, fp=irrad, left=0, right=0)
    irrad = normalize(irrad)  # Normalize
    return irrad


def madrid_old_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", MADRID_2014_SKY_FILE)
    result = resource(MADRID_2014_SKY_FILE, delimiter=",")
    wave, irrad = result["Wavelength [nm]"], result["Irradiance (before midnight)"]
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad = np.interp(x=wavelength, xp=wave, fp=irrad, left=0, right=0)
    irrad = normalize(irrad)  # Normalize
    return irrad


def madrid_new_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", MADRID_2020_SKY_FILE)
    result = resource(MADRID_2020_SKY_FILE, delimiter=",")
    log.info(result)
    wave, irrad = result["Wavelength [nm]"], result["Irradiance"]
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad = np.interp(x=wavelength, xp=wave, fp=irrad, left=0, right=0)
    log.info(irrad)
    irrad = normalize(irrad)  # Normalize
    return irrad


def night_sky(wavelength: FloatArray, selector: NightSky) -> FloatArray:
    if selector == NightSky.CAHA:
        irrad = caha_night_sky(wavelength)
    elif selector == NightSky.MADRID_OLD:
        irrad = madrid_old_night_sky(wavelength)
    elif selector == NightSky.MADRID_NEW:
        irrad = madrid_new_night_sky(wavelength)
    else:
        raise NotImplementedError(f"{selector} not yet available")
    return irrad


def tsl237_qe(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading TSL237 sensor QE")
    wave_tsl237, responsivity = get_tsl237_responsivity_resource()
    responsivity = np.interp(x=wavelength, xp=wave_tsl237, fp=responsivity, left=0, right=0)
    qe = normalize(responsivity / wavelength)
    return qe


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
    sky_label: NightSky,
    qe: FloatArray,
    save_path: str = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    axes.plot(
        wavelength,
        transmittance,
        marker="o",
        label=label,
    )
    axes.plot(wavelength, irradiance, label=sky_label, alpha=0.3)
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
    sky_label: NightSky,
    output: FloatArray,
    mag: float,
    fwhm: Tuple[float, float, float],
    save_path: str = None,
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
    sky_label: NightSky,
    outputs: Sequence[FloatArray],
    mags: Sequence[FloatArray],
    fwhms: Sequence[Tuple[float, float, float]],
    save_path: str = None,
) -> None:
    N = len(labels)
    fig, axes = plt.subplots(N, 1, figsize=(12, 4 * N))
    for axe, response, output, label, mag, fwhm in zip(
        axes, responses, outputs, labels, mags, fwhms
    ):
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
        if mag == 0:
            plot_box(axe, (f"mag = {mag:0.2f}\nFWHM = {fwhm:0.0f} nm", 0.83, 0.40))
        else:
            plot_box(axe, (f"\u0394mag = {mag:0.2f}\nFWHM = {fwhm:0.0f} nm", 0.83, 0.40))
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
    irradiances: Sequence[FloatArray],
    sky_labels: Sequence[str],
    qe: FloatArray,
    save_path: str = None,
) -> None:
    fig, axes = plt.subplots(1, 1)

    for transmittance, label in zip(transmittances, labels):
        axes.plot(
            wavelength,
            transmittance,
            label=label,
        )
    for irradiance, sky_label in zip(irradiances, sky_labels):
        axes.plot(wavelength, irradiance, label=sky_label, alpha=0.3)
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
    axes.set_title(f"{', '.join(labels)} response and natural sky emissions")
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def cli_plot_filter(args: Namespace) -> None:
    log.info("reading filter data %s", args.input_file)
    table: Table = astropy.io.ascii.read(args.input_file, format="ecsv")
    mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
    table = table[mask]
    wavelength = table[COL.WAVE]  # Common wavelength array for all
    irrad = night_sky(wavelength, args.sky)
    qe = tsl237_qe(wavelength)
    plot_filter(
        wavelength=wavelength,
        transmittance=table[COL.TRANS],
        label=" ".join(args.label),
        irradiance=irrad,
        sky_label=f"{args.sky}",
        qe=qe,
        save_path=args.save_figure_path,
    )


def cli_plot_filters(args: Namespace) -> None:
    tables = list()
    for input_file in args.input_file:
        table: Table = astropy.io.ascii.read(input_file, format="ecsv")
        mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
        table = table[mask]
        tables.append(table)
    log.info("read %d tables", len(tables))
    wavelength = tables[0][COL.WAVE]
    irradiances = list()
    for sky_label in (CAHA_NIGHT_SKY_FILE,):
        wave_sky_label, irrad_sky_label = get_night_sky_resource(sky_label)
        if sky_label == CAHA_NIGHT_SKY_FILE:
            wave_sky_label = wave_sky_label / 10  # from Amstrongs to nanomenters
        # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
        irrad_sky_label = np.interp(
            x=wavelength, xp=wave_sky_label, fp=irrad_sky_label, left=0, right=0
        )
        irrad_sky_label = normalize(irrad_sky_label)
        irradiances.append(irrad_sky_label)
    qe_tsl237 = tsl237_qe(wavelength)
    plot_filters(
        wavelength=wavelength,
        transmittances=[t[COL.TRANS] for t in tables],
        labels=args.labels,
        irradiances=irradiances,
        sky_labels=(f"{args.sky}",),
        qe=qe_tsl237,
        save_path=args.save_figure_path,
    )


def cli_plot_combi(args: Namespace) -> None:
    log.info("reading filter data %s", args.input_file)
    table: Table = astropy.io.ascii.read(args.input_file, format="ecsv")
    mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
    table = table[mask]
    wavelength = table[COL.WAVE]  # Common wavelength array for all
    irrad = night_sky(wavelength, args.sky)
    qe = tsl237_qe(wavelength)
    response = table[COL.TRANS] * qe
    output = irrad * response
    flux = integrate.simpson(output, x=wavelength)
    mag = 20.50 - 2.5 * np.log10(flux)
    log.info(
        "Integrated flux over [%d nm-%d nm] interval gives %e (m=%0.3f)",
        args.x_low,
        args.x_high,
        flux,
        mag,
    )
    fwhm, xfw1, xfw2 = get_fwhm(wavelength, response)
    log.info("FWHM = %0.2f, from x1 = %0.2f to x2 = %0.2f", fwhm, xfw1, xfw2)
    plot_combi(
        wavelength=wavelength,
        response=response,
        label=" ".join(args.label),
        input_signal=irrad,
        sky_label=f"{args.sky}",
        output=output,
        mag=mag,
        fwhm=(fwhm, xfw1, xfw2),
        save_path=args.save_figure_path,
    )


def cli_plot_combi_stacked(args: Namespace) -> None:
    tables = list()
    for input_file in args.input_file:
        log.info("reading filter data %s", input_file)
        table: Table = astropy.io.ascii.read(input_file, format="ecsv")
        mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
        table = table[mask]
        tables.append(table)
    wavelength = tables[0][COL.WAVE]  # Common wavelength array for all
    irrad = night_sky(wavelength, args.sky)
    qe = tsl237_qe(wavelength)
    outputs, responses, magnitudes, fwhms = list(), list(), list(), list()
    for table in tables:
        response = table[COL.TRANS] * qe
        output = irrad * response
        flux = integrate.simpson(output, x=wavelength)
        mag = 20.50 - 2.5 * np.log10(flux)
        log.info(
            "Integrated flux over [%d nm-%d nm] interval gives %e (m=%0.3f)",
            args.x_low,
            args.x_high,
            flux,
            mag,
        )
        fwhm, xfw1, xfw2 = get_fwhm(wavelength, response)
        log.info("FWHM = %0.2f, from x1 = %0.2f to x2 = %0.2f", fwhm, xfw1, xfw2)
        outputs.append(output)
        responses.append(response)
        magnitudes.append(mag)
        fwhms.append((fwhm, xfw1, xfw2))
    # convert to delta magnitudes wrt. the first item in the list
    magnitudes = [m - magnitudes[0] for m in magnitudes]
    plot_combi_stacked(
        wavelength=wavelength,
        responses=responses,
        labels=args.labels,
        input_signal=irrad,
        sky_label=f"{args.sky}",
        outputs=outputs,
        mags=magnitudes,
        fwhms=fwhms,
        save_path=args.save_figure_path,
    )


def sky() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--sky",
        type=NightSky,
        default=NightSky.CAHA,
        help="Night Sky to load, defaults to %(default)s",
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
            prs.xlim(),
            sky(),
        ],
        help="Plot Filter trasmittance alongside with Night Sky spectra",
    )
    parser_single.set_defaults(func=cli_plot_filter)
    parser_multi = subparser.add_parser(
        "multi",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot Filters trasmittances alongside with Night Sky spectra",
    )
    parser_multi.set_defaults(func=cli_plot_filters)

    parser_combi = subparser.add_parser(
        "combi",
        parents=[
            prs.ifile(),
            prs.label("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot single TESS-W effects on Night Sky spectra",
    )
    parser_combi.set_defaults(func=cli_plot_combi)

    parser_combi = subparser.add_parser(
        "stacked",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot 2 TESS-W effects on Night Sky spectra",
    )
    parser_combi.set_defaults(func=cli_plot_combi_stacked)


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
        description="Plot filter transmittance with night sky emissions superimposed ",
    )
