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
from typing import TypeAlias, Sequence, Dict, Tuple

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy
from astropy.table import Table
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
TSL237_QE = "TSL237_QE.tsv"

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------


# Load global style sheets
plt.style.use("licatools.resources.global")

mpl.rcParams["legend.fontsize"] = "small"

# -------------------
# Auxiliary functions
# -------------------


@lru_cache(maxsize=None)
def resource(resource_name: str) -> dict[str, FloatArray]:
    """
    Transforma todos los arrays en una estructura de datos conveniente y la cachea
    """
    reso = files(LICA_PKG).joinpath(resource_name).read_text(encoding="utf-8").splitlines()
    rows = csv.DictReader(reso, delimiter="\t")
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
    return {k: np.array(v, dtype=np.float64) for k, v in cols.items()}


def get_emissions(filename: str) -> Tuple[FloatArray, FloatArray]:
    """
    Obtiene el array numpy correspondiente con las lineas de emision del cielo nocturno deseado
    """
    result = resource(filename)
    return result["Wavelength"], result["Irradiance"]

def get_tsl237_qe() -> Tuple[FloatArray, FloatArray]:
    """
    Obtiene el array numpy de la QE del TSL237 (medida en laboratorio)
    """
    result = resource(TSL237_QE)
    return result["Wavelength"], result["QE"]

# -----------------
# Auxiliary classes
# -----------------


class NightSky(StrEnum):
    CAHA = "Calar Alto"


# -------------------
# Auxiliary functions
# -------------------


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
        label=label,
    )
    axes.plot(wavelength, irradiance, label=site, alpha=0.3)
    axes.plot(wavelength, qe, label="TSL237 QE",linestyle="-.", color="black", alpha=0.5)
    for x, color in ((740, "red"), (750,"black")):
        axes.axvline(x, linestyle=":", label=f"{x} nm", color=color)
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Transmittance")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{label} filter transmittance and natural sky emissions")
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
    axes.plot(wavelength, qe, label="TSL237 QE",linestyle="-.", color="black", alpha=0.5)

    for x, color in ((740, "red"), (750,"black")):
        axes.axvline(x, linestyle=":", label=f"{x} nm", color=color)
    xlow = np.floor(np.min(wavelength))
    xhigh = np.ceil(np.max(wavelength))
    axes.set_xlim(xlow, xhigh)
    axes.set_xlabel("Wavelength (nm)")
    axes.set_ylabel("Transmittance")
    axes.legend()
    axes.grid(True, alpha=0.3)
    axes.set_title(f"{", ".join(labels)} filter transmittances and natural sky emissions")
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
    wavelength = table[COL.WAVE] # Common wavelength array for all
    log.info("reading night sky emissions from %s", CAHA_NIGHT_SKY_FILE)
    wave_caha, irrad_caha = get_emissions(CAHA_NIGHT_SKY_FILE)
    wave_caha = wave_caha / 10  # from Amstrongs to nanomenters
    # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
    irrad_caha = np.interp(x=wavelength, xp=wave_caha, fp=irrad_caha, left=0, right=0)
    irrad_caha = irrad_caha / np.max(irrad_caha)  # Normalize
    log.info("reading TSL237 sensor QE")
    wave_tsl237, qe_tsl237 =  get_tsl237_qe()
    qe_tsl237 = np.interp(x=wavelength, xp=wave_tsl237, fp=qe_tsl237, left=0, right=0)

    plot_filter(
        wavelength=wavelength,
        transmittance=table["Transmittance"],
        label=" ".join(args.label),
        irradiance=irrad_caha,
        site="CAHA night sky",
        qe=qe_tsl237,
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
        wave_site, irrad_site = get_emissions(site)
        if site == CAHA_NIGHT_SKY_FILE:
            wave_site = wave_site / 10  # from Amstrongs to nanomenters
        # Interpola la respuesta espectral del cielo al rango donde se ha medido el filtro
        irrad_site = np.interp(x=wavelength, xp=wave_site, fp=irrad_site, left=0, right=0)
        irrad_site = irrad_site / np.max(irrad_site)  # Normalize
        irradiances.append(irrad_site)
    log.info("reading TSL237 sensor QE")
    wave_tsl237, qe_tsl237 =  get_tsl237_qe()
    qe_tsl237 = np.interp(x=wavelength, xp=wave_tsl237, fp=qe_tsl237, left=0, right=0)
    plot_filters(
        wavelength=wavelength,
        transmittances=[t["Transmittance"] for t in tables],
        labels=args.labels,
        irradiances=irradiances,
        sites=("CAHA night sky",),
        qe=qe_tsl237,
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
