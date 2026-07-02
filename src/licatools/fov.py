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
from typing import TypeAlias, Sequence, Tuple, Optional

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
from numpy.polynomial.polynomial import Polynomial
import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy
from astropy.table import Table, Column

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


def dark_fit(x: Column, y: Column, deg: int) -> Tuple[FloatArray, FloatArray, float]:
    """hace una estimacion polinomica (grado2)de la señal de oscuridad total de la habitacion"""
    # quita los puntos (x,y) cuyas medidas y estan vacias
    mask = ~(y.mask)
    x = x[mask]
    y = y[mask]
    # Crea un polinomio por ajuste de minimos cuadrados
    P = Polynomial.fit(x, y, deg=deg)
    y_pred = P(x)
    sum_resid = np.sum((y - y_pred) ** 2)
    sum_total = np.sum((y - y.mean()) ** 2)
    r2 = 1 - sum_resid / sum_total
    xx = np.linspace(np.min(x), np.max(x))
    return xx, P(xx), r2, P.coef


def plot_fov_single(
    phot_name: str,
    table: Table,
    freq_up: bool,
    freq_side: bool,
    bg_poly_order: int,
    gauss_hermite: bool = False,
    save_path: Optional[str] = None,
) -> None:
    fig, axes = plt.subplots(1, 1)
    # response_plot = axes.plot(wavelength, response, label=f"{label} spectral resp.")
    # color = response_plot[0].get_color()q
    if freq_up:
        angles, fitted_dark, r2, p0 = dark_fit(table[Col.ANGLE_UP], table[Col.DARK_FREQ_UP], deg=2)
        log.info("Fitted R^2 = %f", r2)
        # Plot the FoV
        mask = ~(table[Col.FREQ_UP].mask)
        x = table[Col.ANGLE_UP][mask]
        y1 = table[Col.FREQ_UP][mask]
        y2 = table[Col.DARK_FREQ_UP][mask]
        axes.plot(x, y1, marker="o", linewidth=0, label="light data, up position")
        # Plot the Dark room FoV
        result = axes.plot(
            x, y2, marker="v", label="dark data, up position", alpha=0.5, linewidth=0
        )
        # Plot the dark fitted line
        axes.plot(angles, fitted_dark, alpha=0.5, linewidth=0.5, color=result[0].get_color())
        # detect peak
        peaks = detect_peaks(x, y1, height=1.5, distance=10.0)
        assert len(peaks) == 1
        peak = peaks[0]
        axes.axvline(x[peak], linestyle=":", label="peak, up position")
        fwhm, _, _ = get_fwhm(x, y1)
        y_fit, _ = gauss_hermite_fit(
            x,
            y1,
            p0_bg=p0.tolist()[:2],
            p0_peaks=[y1[peak], x[peak], fwhm / 2.355, 0, 0],
            h3=0,
            h4=0,
        )
        axes.plot(x, y_fit, label="fitted model, up position")
        fwhm_up, _, _ = get_fwhm(x, y1)
        log.info("FWHM = %f", fwhm_up)

    if freq_side:
        angles, fitted_dark, r2, p0 = dark_fit(
            table[Col.ANGLE_SIDE], table[Col.DARK_FREQ_SIDE], deg=2
        )
        log.info("Fitted R^2 = %f", r2)
        mask = ~(table[Col.FREQ_SIDE].mask)
        x = table[Col.ANGLE_SIDE][mask]
        y1 = table[Col.FREQ_SIDE][mask]
        y2 = table[Col.DARK_FREQ_SIDE][mask]
        # Plot the FoV
        axes.plot(x, y1, marker="o", linewidth=0, label="light data, side position")
        # Plot the Dark room FoV
        result = axes.plot(
            x, y2, marker="^", label="dark data, side position", alpha=0.5, linewidth=0
        )
        # Plot the dark fitted line
        axes.plot(angles, fitted_dark, alpha=0.5, linewidth=0.5, color=result[0].get_color())
        # detect peak
        peaks = detect_peaks(x, y1, height=1.5, distance=10.0)
        for peak in peaks:
            axes.axvline(x[peak], linestyle=":", label="peak, side position")
        fwhm, _, _ = get_fwhm(x, y1)
        if gauss_hermite:
            y_fit, residuals = gauss_hermite_fit(
                x,
                y1,
                p0_bg=p0.tolist()[: bg_poly_order + 1],
                p0_peaks=[y1[peak], x[peak], fwhm / 2.355, 0, 0],
                h3=0,
                h4=0,
            )
        else:
            y_fit, residuals = gauss_fit(
                x,
                y1,
                p0_bg=p0.tolist()[: bg_poly_order + 1],
                p0_peaks=[y1[peak], x[peak], fwhm / 2.355],
            )

        axes.plot(x, y_fit, label="fitted model, side position")
        fwhm_side, _, _ = get_fwhm(x, y1)
        log.info("FWHM = %f", fwhm_side)
    if freq_up and freq_side:
        plot_box(axes, (f"FWHM(up)={fwhm_up:0.1f}\nFWHM(side)={fwhm_side:0.1f}", 0.1, 0.8))
    elif freq_up:
        plot_box(axes, (f"FWHM(up)={fwhm_up:0.1f}", 0.1, 0.8))
    elif freq_side:
        plot_box(axes, (f"FWHM(side)={fwhm_side:0.1f}", 0.1, 0.8))

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
            angles, fitted_dark, r2 = dark_fit(table[cols[0]], table[cols[2]])
            mask = ~(table[cols[1]].mask)
            axe.plot(
                table[cols[0]][mask], table[cols[1]][mask], marker="o", label=f"{phot_name} {tag}"
            )
            result = axe.plot(
                table[cols[0]],
                table[cols[2]],
                marker="v",
                label=f"{phot_name} {tag} [dark]",
                alpha=0.5,
            )
            # Plot the dark fitted line
            axe.plot(angles, fitted_dark, alpha=0.5, linewidth=0.5, color=result[0].get_color())
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
    # freq_up = False if args.side else True
    # freq_side = False if args.up else True
    log.info("args.up = %s, args.side = %s, args.both=%s", args.up, args.side, args.both)
    freq_up = True if args.up or args.both else False
    freq_side = True if args.side or args.both else False
    log.info("freq_up = %s, freq_side = %s", freq_up, freq_side)
    plot_fov_single(
        phot_name=" ".join(args.label),
        table=table,
        freq_up=freq_up,
        freq_side=freq_side,
        bg_poly_order=args.poly,
        gauss_hermite=True if args.gauss_hermite else False,
    )


def cli_plot_fov_stacked(args: Namespace) -> None:
    log.info("reading FoV data from files %s", args.input_file)
    tables = [astropy.io.ascii.read(path, format="csv") for path in args.input_file]
    plot_fov_stacked(
        phot_names=args.labels,
        fov_tables=tables,
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
    parser.add_argument("--poly", type=int, default=2, help="polynomial degree")
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
