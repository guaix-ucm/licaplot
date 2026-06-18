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
from argparse import Namespace
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
TSL237_RESP_LICA = "TSL237_responsivity_LICA.tsv"
TSL237_RESP_DATA = "TSL237_responsivity_datasheet.csv"

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


# -------------------
# Auxiliary functions
# -------------------


def normalize(x: FloatArray) -> FloatArray:
    """Normalize an array wrt its max value."""
    return x / np.max(x)


@lru_cache(maxsize=None)
def resource(resource_name: str, delimiter="\t") -> dict[str, FloatArray]:
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


def get_night_sky_resource(filename: str) -> Tuple[FloatArray, FloatArray]:
    """
    Obtiene el array numpy correspondiente con las lineas de emision del cielo nocturno deseado
    """
    result = resource(filename)
    return result["Wavelength"], result["Irradiance"]


def get_tsl237_responsivity_resource(lica: bool = True) -> Tuple[FloatArray, FloatArray]:
    """
    Obtiene el array numpy de la QE del TSL237
    """
    if lica:
        result = resource(TSL237_RESP_LICA)  # Medida en laboratorio
        return result["Wavelength [nm]"], result["Responsivity (normalized)"]
    else:
        result = resource(TSL237_RESP_DATA, delimiter=",")
        return result["Wavelength [nm]"], result["Responsivity (normalized)"]


def caha_night_sky(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading night sky emissions from %s", CAHA_NIGHT_SKY_FILE)
    wave_caha, irrad_caha = get_night_sky_resource(CAHA_NIGHT_SKY_FILE)
    wave_caha = wave_caha / 10  # from Amstrongs to nanomenters
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad_caha = np.interp(x=wavelength, xp=wave_caha, fp=irrad_caha, left=0, right=0)
    irrad_caha = normalize(irrad_caha)  # Normalize
    return irrad_caha


def tsl237_qe(wavelength: FloatArray) -> FloatArray:
    """
    Lee el recurso y lo remuestrea a las longitudes de onda de trabajo
    """
    log.info("reading TSL237 sensor QE")
    wave_tsl237, responsivity = get_tsl237_responsivity_resource(lica=False)
    responsivity = np.interp(x=wavelength, xp=wave_tsl237, fp=responsivity, left=0, right=0)
    qe = normalize(responsivity / wavelength)
    return qe


# -----------------
# Auxiliary classes
# -----------------


class NightSky(StrEnum):
    CAHA = "Calar Alto"


# ------------------
# Plotting functions
# ------------------


def plot_filter(
    wavelength: FloatArray,
    transmittance: FloatArray,
    label: str,
    irradiance: FloatArray,
    site: str,
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
    axes.plot(wavelength, irradiance, label=site, alpha=0.3)
    axes.plot(wavelength, qe, label="TSL237 QE", linestyle="-.", color="black", alpha=0.5)
    for x, color in ((740, "red"), (720, "black")):
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
    site: str,
    output: FloatArray,
    mag: float,
    save_path: str = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    axes.plot(wavelength, response, label=f"{label} response")
    axes.plot(wavelength, input_signal, label=site, alpha=0.3)
    axes.plot(wavelength, output, label=f"{site} by {label}", alpha=0.5)
    for x, color in ((740, "red"), (720, "black")):
        axes.axvline(x, linestyle=":", label=f"{x} nm", color=color)
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Response (norm.)")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{label} response and natural sky emissions")
    plot_box(axes, (f"mag = {mag:0.2f}", 0.8, 0.5))
    plt.tight_layout()
    if save_path is not None:
        log.info("saving figure to %s", save_path)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()


def plot_combi_duo(
    wavelength: FloatArray,
    responses: Sequence[FloatArray],
    labels: Sequence[str],
    input_signal: FloatArray,
    site: str,
    outputs: Sequence[FloatArray],
    mags: Sequence[FloatArray],
    save_path: str = None,
) -> None:
    fig, axes = plt.subplots(2, 1)
    for axe, response, output, label, mag in zip(axes, responses, outputs, labels, mags):
        axe.plot(wavelength, response, label=f"{label} response")
        axe.plot(wavelength, input_signal, label=site, alpha=0.3)
        axe.plot(wavelength, output, label=f"{site} by {label}", alpha=0.5)
        for x, color in ((740, "red"), (720, "black")):
            axe.axvline(x, linestyle=":", label=f"{x} nm", color=color)
        xlow = np.floor(np.min(wavelength))
        xhigh = np.ceil(np.max(wavelength))
        axe.set_xlim(xlow, xhigh)
        axe.set_xlabel("Wavelength (nm)")
        axe.set_ylabel("Response (norm.)")
        axe.legend()
        axe.grid(True, alpha=0.3)
        axe.set_title(f"{label} response and natural sky emissions")
        plot_box(axe, (f"mag = {mag:0.2f}", 0.8, 0.5))
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
    sites: Sequence[str],
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
    for irradiance, site in zip(irradiances, sites):
        axes.plot(wavelength, irradiance, label=site, alpha=0.3)
    axes.plot(wavelength, qe, label="TSL237 QE", linestyle="-.", color="black", alpha=0.5)

    for x, color in ((740, "red"), (720, "black")):
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
    irrad_caha = caha_night_sky(wavelength)
    qe = tsl237_qe(wavelength)
    plot_filter(
        wavelength=wavelength,
        transmittance=table[COL.TRANS],
        label=" ".join(args.label),
        irradiance=irrad_caha,
        site="CAHA night sky",
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
    for site in (CAHA_NIGHT_SKY_FILE,):
        wave_site, irrad_site = get_night_sky_resource(site)
        if site == CAHA_NIGHT_SKY_FILE:
            wave_site = wave_site / 10  # from Amstrongs to nanomenters
        # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
        irrad_site = np.interp(x=wavelength, xp=wave_site, fp=irrad_site, left=0, right=0)
        irrad_site = normalize(irrad_site)
        irradiances.append(irrad_site)
    qe_tsl237 = tsl237_qe(wavelength)
    plot_filters(
        wavelength=wavelength,
        transmittances=[t[COL.TRANS] for t in tables],
        labels=args.labels,
        irradiances=irradiances,
        sites=("CAHA night sky",),
        qe=qe_tsl237,
        save_path=args.save_figure_path,
    )


def cli_plot_combi(args: Namespace) -> None:
    log.info("reading filter data %s", args.input_file)
    table: Table = astropy.io.ascii.read(args.input_file, format="ecsv")
    mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
    table = table[mask]
    wavelength = table[COL.WAVE]  # Common wavelength array for all
    irrad_caha = caha_night_sky(wavelength)
    qe = tsl237_qe(wavelength)
    response = table[COL.TRANS] * qe
    output = irrad_caha * response
    flux = integrate.simpson(output, x=wavelength)
    mag = 20.50 - 2.5 * np.log10(flux)
    log.info(
        "Integrated flux over [%d nm-%d nm] interval gives %e (m=%0.3f)",
        args.x_low,
        args.x_high,
        flux,
        mag,
    )
    plot_combi(
        wavelength=wavelength,
        response=response,
        label=" ".join(args.label),
        input_signal=irrad_caha,
        site="CAHA night sky",
        output=output,
        mag=mag,
        save_path=args.save_figure_path,
    )


def cli_plot_combi_duo(args: Namespace) -> None:
    assert len(args.input_file) == 2, "only two input files allowed"
    tables = list()
    for input_file in args.input_file:
        log.info("reading filter data %s", input_file)
        table: Table = astropy.io.ascii.read(input_file, format="ecsv")
        mask = (args.x_low <= table[COL.WAVE]) & (table[COL.WAVE] <= args.x_high)
        table = table[mask]
        tables.append(table)
    wavelength = tables[0][COL.WAVE]  # Common wavelength array for all
    irrad_caha = caha_night_sky(wavelength)
    qe = tsl237_qe(wavelength)
    outputs = list()
    responses = list()
    magnitudes = list()
    for table in tables:
        response = table[COL.TRANS] * qe
        output = irrad_caha * response
        outputs.append(output)
        flux = integrate.simpson(output, x=wavelength)
        mag = 20.50 - 2.5 * np.log10(flux)
        log.info(
            "Integrated flux over [%d nm-%d nm] interval gives %e (m=%0.3f)",
            args.x_low,
            args.x_high,
            flux,
            mag,
        )
        responses.append(response)
        magnitudes.append(mag)
    plot_combi_duo(
        wavelength=wavelength,
        responses=responses,
        labels=args.labels,
        input_signal=irrad_caha,
        site="CAHA night sky",
        outputs=outputs,
        mags=magnitudes,
        save_path=args.save_figure_path,
    )


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.ifile(),
            prs.label("plotting"),
            prs.savefig(),
            prs.xlim(),
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
        ],
        help="Plot single TESS-W effects on Night Sky spectra",
    )
    parser_combi.set_defaults(func=cli_plot_combi)

    parser_combi = subparser.add_parser(
        "duo",
        parents=[
            prs.ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            prs.xlim(),
        ],
        help="Plot 2 TESS-W effects on Night Sky spectra",
    )
    parser_combi.set_defaults(func=cli_plot_combi_duo)


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
