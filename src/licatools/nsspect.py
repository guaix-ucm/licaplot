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
    log.info("[CAHA] Original wavelength range = [%0.2f nm - %0.2f nm]", np.min(wave), np.max(wave))
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad = np.interp(x=wavelength, xp=wave, fp=irrad, left=0, right=0)
    log.info(
        "[CAHA] Resampled wavelength range = [%0.2f nm - %0.2f nm]",
        np.min(wavelength),
        np.max(wavelength),
    )
    irrad = normalize(irrad)  # Normalize
    return irrad


def madrid_old_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", MADRID_2014_SKY_FILE)
    result = resource(MADRID_2014_SKY_FILE, delimiter=",")
    wave, irrad = result["Wavelength [nm]"], result["Irradiance (before midnight)"]
    log.info(
        "[MADRID] Original wavelength range = [%0.2f nm - %0.2f nm]", np.min(wave), np.max(wave)
    )
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad = np.interp(x=wavelength, xp=wave, fp=irrad, left=0, right=0)
    log.info(
        "[MADRID] Resampled wavelength range = [%0.2f nm - %0.2f nm]",
        np.min(wavelength),
        np.max(wavelength),
    )
    irrad = normalize(irrad)  # Normalize
    return irrad


def madrid_new_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", MADRID_2020_SKY_FILE)
    result = resource(MADRID_2020_SKY_FILE, delimiter=",")
    wave, irrad = result["Wavelength [nm]"], result["Irradiance"]
    log.info(
        "[MADRID] Original wavelength range = [%0.2f nm - %0.2f nm]", np.min(wave), np.max(wave)
    )
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    idx = np.argsort(wave)  # ahy que ordenar por orden ascendente de wavelenght
    xp = result["Wavelength [nm]"][idx]
    fp = irrad[idx]
    irrad = np.interp(x=wavelength, xp=xp, fp=fp, left=0, right=0)
    log.info(
        "[MADRID] Resampled wavelength range = [%0.2f nm - %0.2f nm]",
        np.min(wavelength),
        np.max(wavelength),
    )
    irrad = normalize(irrad)  # Normalize
    return irrad


def sand_night_sky(wavelength=None) -> FloatArray:
    """
    Lee el recurso, sin normalizar
    """
    log.info("reading Madrid (SAND) sky emissions from %s", MADRID_2014_SKY_FILE)
    result = resource(MADRID_2014_SKY_FILE, delimiter=",")
    wave, irrad_bfr, irrad_aft = (
        result["Wavelength [nm]"],
        result["Irradiance (before midnight)"],
        result["Irradiance (after midnight)"],
    )
    log.info("[SAND] Original wavelength range = [%0.2f nm - %0.2f nm]", np.min(wave), np.max(wave))
    if wavelength is None:
        return (
            wave,
            irrad_bfr,
            irrad_aft,
        )
    else:
        irrad_bfr = np.interp(
            x=wavelength,
            xp=wave,
            fp=irrad_bfr,
            left=0,
            right=0,
        )
        irrad_aft = np.interp(
            x=wavelength,
            xp=wave,
            fp=irrad_aft,
            left=0,
            right=0,
        )
        log.info(
            "[SAND] Resampled wavelength range = [%0.2f nm - %0.2f nm]",
            np.min(wavelength),
            np.max(wavelength),
        )
        return wavelength, irrad_bfr, irrad_aft


def alpy_night_sky(wavelength=None) -> FloatArray:
    """
    Lee el recurso, sin normalizar
    """
    log.info("reading Madrid (ALPY) sky emissions from %s", MADRID_2020_SKY_FILE)
    result = resource(MADRID_2020_SKY_FILE, delimiter=",")
    wave, irr = result["Wavelength [nm]"], result["Irradiance"]
    log.info("[ALPY] Original wavelength range = [%0.2f nm - %0.2f nm]", np.min(wave), np.max(wave))
    if wavelength is None:
        return wave, irr
    else:
        # El fichero viene ordenado por longitud de onda descendiente
        idx = np.argsort(result["Wavelength [nm]"])
        xp = result["Wavelength [nm]"][idx]
        fp = result["Irradiance"][idx]
        irrad = np.interp(x=wavelength, xp=xp, fp=fp, left=0, right=0)
        log.info(
            "[ALPY] Resampled wavelength range = [%0.2f nm - %0.2f nm]",
            np.min(wavelength),
            np.max(wavelength),
        )
        return wavelength, irrad


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
    sky_label: NightSky,
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
    sky_label: NightSky,
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
    for path in args.input_file:
        log.info("reading filter data %s", args.input_file)
        table: Table = astropy.io.ascii.read(path, format="ecsv")
        mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
        table = table[mask]
        tables.append(table)
    wavelength = tables[0][COL.WAVE]  # Common wavelength array for all
    irrad = night_sky(wavelength, args.sky)
    qe = tsl237_qe(wavelength)
    plot_filters(
        wavelength=wavelength,
        transmittances=[t[COL.TRANS] for t in tables],
        labels=args.labels,
        irradiance=irrad,
        sky_label=f"{args.sky}",
        qe=None,
        save_path=args.save_figure_path,
    )


def cli_plot_filters_skies(args: Namespace) -> None:
    tables = list()
    for path in args.input_file:
        log.info("reading filter data %s", args.input_file)
        table: Table = astropy.io.ascii.read(path, format="ecsv")
        mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
        table = table[mask]
        tables.append(table)
    wavelength = tables[0][COL.WAVE]  # Common wavelength array for all
    qe = tsl237_qe(wavelength)
    irrads = [night_sky(wavelength, sky) for sky in args.sky]   
    plot_filters_skies(
        wavelength=wavelength,
        transmittances=[t[COL.TRANS] for t in tables],
        labels=args.labels,
        irradiances=irrads,
        sky_labels=args.sky,
        qe=None,
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
    mag_diffs = [m - magnitudes[0] for m in magnitudes]
    plot_combi_stacked(
        wavelength=wavelength,
        responses=responses,
        labels=args.labels,
        input_signal=irrad,
        sky_label=f"{args.sky}",
        outputs=outputs,
        mag_diffs=mag_diffs,
        base_magnitude=args.magnitude,
        fwhms=fwhms,
        save_path=args.save_figure_path,
    )


def cli_plot_sky(args: Namespace) -> None:
    if args.sky is not None:
        log.info("reading %s sky data", args.sky)
        wavelength = np.arange(args.x_low, args.x_high + 2, 2)
        if args.sky == NightSky.MADRID_OLD:
            wavelength, sky_bfr, skyd_aft = sand_night_sky(wavelength=wavelength)
            plot_sand_sky(
                wavelength=wavelength,
                sky_data_bfr=sky_bfr,
                sky_data_aft=skyd_aft,
                sky_label=f"{args.sky}",
                save_path=args.save_figure_path,
            )
        else:
            wavelength, sky = alpy_night_sky(wavelength=wavelength)
            plot_alpy_sky(
                wavelength=wavelength,
                sky_data=sky,
                sky_label=f"{args.sky}",
                save_path=args.save_figure_path,
            )
    else:
        log.info("reading %s raw sky data", args.raw_sky)
        if args.raw_sky == NightSky.MADRID_OLD:
            wavelength, sky_bfr, skyd_aft = sand_night_sky()
            plot_sand_sky(
                wavelength=wavelength,
                sky_data_bfr=sky_bfr,
                sky_data_aft=skyd_aft,
                sky_label=f"{args.raw_sky}",
                save_path=args.save_figure_path,
            )
        else:
            wavelength, sky = alpy_night_sky()
            plot_alpy_sky(
                wavelength=wavelength,
                sky_data=sky,
                sky_label=f"{args.raw_sky}",
                save_path=args.save_figure_path,
            )


def sky() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sky",
        type=NightSky,
        default=None,
        help="Night Sky to load (interpolated to monochormator range), defaults to %(default)s",
    )
    group.add_argument(
        "--raw-sky",
        type=NightSky,
        default=None,
        help="Night Sky to load (not interpolated to monochromator range), defaults to %(default)s",
    )
    return parser

def skies() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sky",
        type=NightSky,
        nargs="+",
        default=None,
        help="Night Skies to load (interpolated to monochormator range), defaults to %(default)s",
    )
    group.add_argument(
        "--raw-sky",
        type=NightSky,
        nargs="+",
        default=None,
        help="Night Sky to load (not interpolated to monochromator range), defaults to %(default)s",
    )
    return parser

def mag() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--mag",
        dest="magnitude",
        type=float,
        default=21.5,
        help="Typical base NSB, defaults to %(default)s",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_sky = subparser.add_parser(
        "sky",
        parents=[
            prs.label("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot selected Night Sky spectrum",
    )
    parser_sky.set_defaults(func=cli_plot_sky)
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.ifile(),
            prs.label("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot filter trasmittance alongside with Night Sky spectrum",
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
        help="Plot several filter trasmittances alongside with Night Sky spectrum",
    )
    parser_multi.set_defaults(func=cli_plot_filters)

    parser_multiskies = subparser.add_parser(
        "multiskies",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            prs.xlim(),
            skies(),
        ],
        help="Plot several filter trasmittances alongside with several Night Sky spectra",
    )
    parser_multiskies.set_defaults(func=cli_plot_filters_skies)

    parser_combi = subparser.add_parser(
        "combi",
        parents=[
            prs.ifile(),
            prs.label("plotting"),
            prs.savefig(),
            prs.xlim(),
            sky(),
        ],
        help="Plot single TESS-W effects on a selected Night Sky spectrum",
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
            mag(),
        ],
        help="Plot several TESS-W effects on a selected Night Sky spectrum",
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
