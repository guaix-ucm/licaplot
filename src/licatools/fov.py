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

import logging
from argparse import Namespace, ArgumentParser
from enum import StrEnum
from typing import TypeAlias, Sequence, Tuple, Dict, Optional
from dataclasses import dataclass

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
from numpy.polynomial.polynomial import Polynomial
import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy
from astropy.table import Table

from lica.cli import execute
from lica.validators import vfile

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import parser as prs
from .utils.fitting import get_fwhm, detect_peaks, gauss_hermite_fit, gauss_fit

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
    NOTES_SIDE = "Notes [side]"
    DARK_FREQ_SIDE = "Dark [side] (Hz)"
    DARK_MAG_SIDE = "Dark [side] (mag)"


@dataclass
class FovParams:
    pls_angle: FloatArray  # Point Light Source angles in degrees
    pls_freq: FloatArray  # Point Light Source frequencies
    dk_angle: FloatArray  # Dark room angles in degrees
    dk_freq: FloatArray  # Dark room frequencies
    peak: float | None  # FoV peak array position index
    fwhm: float
    fit_pls_freq: FloatArray  # Fitted Point Light Source frequencies
    fit_dk_freq: FloatArray  # Fitted Dark room frequencies


# --------------------
# Processing functions
# --------------------


def dark_fit(
    angle: FloatArray, freq: FloatArray, deg: int
) -> Tuple[FloatArray, float, Sequence[float]]:
    """hace una estimacion polinomica de la señal de oscuridad total de la habitacion"""
    log.info("Dark fitting to a polynomial of degree %d", deg)
    P = Polynomial.fit(angle, freq, deg=deg)
    fit_freq = P(angle)
    sum_resid = np.sum((freq - fit_freq) ** 2)
    sum_total = np.sum((freq - freq.mean()) ** 2)
    r2 = 1 - sum_resid / sum_total
    # dense_angle = np.linspace(np.min(angle), np.max(angle))
    return fit_freq, r2, P.coef.tolist()


def process_fov(table: Table, gauss_hermite: bool, deg: int) -> Dict[str, FovParams]:
    """Do all processing and fitting before plotting"""
    fov_specs = dict()
    for orientation, cols in zip(
        ("up", "side"),
        (
            (Col.ANGLE_UP, Col.FREQ_UP, Col.DARK_FREQ_UP),
            (Col.ANGLE_SIDE, Col.FREQ_SIDE, Col.DARK_FREQ_SIDE),
        ),
    ):
        mask = ~(table[cols[1]].mask)
        pls_angle = table[cols[0]][mask]
        pls_freq = table[cols[1]][mask]
        mask = ~(table[cols[2]].mask)
        dk_angle = table[cols[0]][mask]
        dk_freq = table[cols[2]][mask]
        fit_dk_freq, r2, p0 = dark_fit(dk_angle, dk_freq, deg=deg)
        log.info("Fitted R^2 = %f", r2)
        peaks = detect_peaks(pls_angle, pls_freq, height=1.5, distance=10.0)
        assert len(peaks) == 1
        peak = peaks[0]
        fwhm, _, _ = get_fwhm(pls_angle, pls_freq)  # initail FWHM guess to input fit params
        if gauss_hermite:
            fit_pls_freq, _ = gauss_hermite_fit(
                pls_angle,
                pls_freq,
                p0_bg=p0,
                p0_peaks=[pls_freq[peak], pls_angle[peak], fwhm / 2.355, 0, 0],
                h3=0,
                h4=0,
            )
        else:
            fit_pls_freq, _ = gauss_fit(
                pls_angle,
                pls_freq,
                p0_bg=p0,
                p0_peaks=[pls_freq[peak], pls_angle[peak], fwhm / 2.355, 0, 0],
            )
        fwhm, _, _ = get_fwhm(pls_angle, pls_freq)  # compute final FWHM
        log.info("FWHM = %f", fwhm)
        fov_specs[orientation] = FovParams(
            pls_angle,
            pls_freq,
            dk_angle,
            dk_freq,
            peak,
            fwhm,
            fit_pls_freq,
            fit_dk_freq,
        )
    return fov_specs


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
    plot_specs: Dict[str, FovParams],
    plot_axis: bool,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    for orient, s in plot_specs.items():
        axes.plot(
            s.pls_angle,
            s.pls_freq,
            marker="o",
            linewidth=0,
            label=f"light data, {orient} position",
        )
        # Plot the Dark room FoV
        result = axes.plot(
            s.dk_angle,
            s.dk_freq,
            marker="v",
            label=f"dark data, {orient} position",
            alpha=0.5,
            linewidth=0,
        )
        # Plot the fitted model
        axes.plot(s.pls_angle, s.fit_pls_freq, label=f"fitted model, {orient} position")
        # Plot the dark fitted line
        axes.plot(s.dk_angle, s.fit_dk_freq, alpha=0.5, linewidth=0.5, color=result[0].get_color())
        # Optionally, plot the peak
        if plot_axis:
            axes.axvline(s.pls_angle[s.peak], linestyle=":", label=f"peak, {orient} position")
    s = plot_specs  # alias to shorten sentences below
    if len(s) == 2:
        plot_box(
            axes,
            (
                f"FWHM({'up'})={s['up'].fwhm:0.0f}\nFWHM(side)={s['side'].fwhm:0.0f}",
                0.1,
                0.8,
            ),
        )
    elif s.get("up"):
        plot_box(axes, (f"FWHM(up)={s['up'].fwhm:0.0f}", 0.1, 0.8))
    else:
        plot_box(axes, (f"FWHM(side)={s['side'].fwhm:0.0f}", 0.1, 0.8))
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
    fov_specs: Sequence[FovParams],
    save_path: Optional[str] = None,
) -> None:
    N = 2
    fig, axes = plt.subplots(N, 1, figsize=(12, 4 * N))
    for axe, tag in zip(axes, ("up", "side")):
        fwhm_lst = list()
        for phot_name, s in zip(phot_names, fov_specs):
            # Plot the light FoV points
            result = axe.plot(
                s[tag].pls_angle,
                s[tag].pls_freq,
                marker="o",
                linewidth=0,
                label=f"{phot_name} {tag}",
            )
            # Plot the ligh FoV fitting
            result = axe.plot(
                s[tag].pls_angle,
                s[tag].fit_pls_freq,
                label=f"fitted {phot_name} {tag}",
                color=result[0].get_color(),
            )

            # Plot the dark Room FoV points
            result = axe.plot(
                s[tag].dk_angle,
                s[tag].dk_freq,
                marker="v",
                label=f"{phot_name} {tag} [dark]",
                alpha=0.5,
            )
            # Plot the dark fitted line
            axe.plot(
                s[tag].dk_angle,
                s[tag].fit_dk_freq,
                alpha=0.5,
                linewidth=0.5,
                color=result[0].get_color(),
            )
            fwhm_lst.append(f"FWHM({phot_name})={s[tag].fwhm:0.0f}")
        plot_box(axe, ("\n".join(fwhm_lst), 0.1, 0.8))
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
    fov_specs = process_fov(table, args.gauss_hermite, args.poly)
    if args.up and not args.both:
        del fov_specs["side"]
    elif args.side and not args.both:
        del fov_specs["up"]
    else:
        pass
    plot_fov_single(
        phot_name=" ".join(args.label),
        plot_specs=fov_specs,
        plot_axis=args.axis,
        save_path=args.save_figure_path,
    )


def cli_plot_fov_stacked(args: Namespace) -> None:
    if len(args.labels) != len(args.input_file):
        raise ValueError("Labels must match the number of input files")
    log.info("reading FoV data from files %s", args.input_file)
    tables = [astropy.io.ascii.read(path, format="csv") for path in args.input_file]
    fov_specs = [process_fov(table, args.gauss_hermite, args.poly) for table in tables]
    plot_fov_stacked(
        phot_names=args.labels,
        fov_specs=fov_specs,
        save_path=args.save_figure_path,
    )


def choices3() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--up", action="store_true", default=False, help="Up FoV curve only")
    group.add_argument("--side", action="store_true", default=False, help="Side FoV curve only")
    group.add_argument(
        "--both", action="store_true", default=False, help="Both [up] & [side]  FoV curves"
    )
    parser.add_argument(
        "-ax", "--axis", action="store_true", default=False, help="Plot optical axis"
    )
    return parser


def fit() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-gs", "--gauss", action="store_true", default=False, help="Gauss fitting + poly backround"
    )
    group.add_argument(
        "-gh",
        "--gauss-hermite",
        action="store_true",
        default=False,
        help="Gauss-Hermite fitting + poly backround",
    )
    parser.add_argument("--poly", type=int, default=1, help="polynomial degree")
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
        parents=[prs.ifile(), prs.label("plotting"), prs.savefig(), choices3(), fit()],
        help="Plot single TESS-W FoV curves",
    )
    parser_single.set_defaults(func=cli_plot_fov_single)
    parser_combi = subparser.add_parser(
        "stacked",
        parents=[
            ifiles(),
            prs.labels("plotting"),
            prs.savefig(),
            fit(),
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
