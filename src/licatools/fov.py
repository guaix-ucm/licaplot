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
import itertools
from argparse import Namespace, ArgumentParser
from enum import StrEnum
from typing import TypeAlias, Sequence, Tuple, Optional

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
from numpy.polynomial.polynomial import Polynomial
from numpy.polynomial.polynomial import polyval
import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy
from astropy.table import Table, Column
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit

from lica.cli import execute
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


def detect_peaks(
    x: FloatArray,
    y: FloatArray,
    prominence=None,
    distance=None,
    width=None,
    height=None,
    window_length: int = 9,
    polyorder: int = 2,  # smoothing polynomial order
) -> IntArray:
    """
    Detecta picos automáticamente y estima parámetros iniciales.

    La estructura de los parametros iniciales p0 del ajuste multigaussiano que devuelve es
    p0 = [
      b0 (fondo global), b1 (pendiente)=0.0,

    ]
    Devuelve un array de indices dende estan los picos asi como parametros iniciales para gaussian fitting
    """
    smoothed_y = savgol_filter(y, window_length=window_length, polyorder=polyorder)
    peaks, _ = find_peaks(
        smoothed_y,
        prominence=prominence,
        distance=distance,
        width=width,  #
        height=height,  # Umbral mínimo
    )
    log.info("Found %d peaks", len(peaks))
    for peak in peaks:
        log.info("Detected peak at x = %.2f", x[peak])
    return peaks


def gauss_hermite_fit(
    x: FloatArray,
    y: FloatArray,
    p0_bg: Sequence[float],  # backgroud polynomial coeffs in increasing order
    p0_peaks: Sequence[float],  # GH initial estimation [A1, mu1, sigma1, h3_1, h4_1, ...]
    h3: float = 0.0,
    h4: float = 0.0,
    error_y: FloatArray = None,
    maxfev: int = 25000,
) -> tuple[FloatArray, FloatArray]:
    """
    Ajuste de fondo polinomico + suma de perfiles Gauss-Hermite.

    Cada componente se parametriza como:
        A * exp(-0.5 * u^2) * [1 + h3*H3(u) + h4*H4(u)]

    donde:
        u = (x - mu) / sigma
        H3(u) = (1 / sqrt(6)) * (2*sqrt(2)*u^3 - 3*sqrt(2)*u)
        H4(u) = (1 / sqrt(24)) * (4*u^4 - 12*u^2 + 3)

    Si h3 = h4 = 0, el perfil se reduce a una gaussiana.
    """

    def gauss_hermite(
        x: FloatArray,
        A: float,
        mu: float,
        sigma: float,
        h3: float,
        h4: float,
    ) -> FloatArray:
        """Single Gauss-Hermite function"""
        u = (x - mu) / sigma
        H3 = (2 * np.sqrt(2) * u**3 - 3 * np.sqrt(2) * u) / np.sqrt(6)
        H4 = (4 * u**4 - 12 * u**2 + 3) / np.sqrt(24)
        return A * np.exp(-0.5 * u**2) * (1.0 + h3 * H3 + h4 * H4)

    def model_gh(x: FloatArray, *params: float) -> FloatArray:
        bg = np.asarray(params[: p0_bg.size], dtype=float)
        peak_params = params[p0_bg.size :]
        y_fit = polyval(x, bg)
        for A, mu, sigma, h3i, h4i in itertools.batched(peak_params, 5):
            y_fit += gauss_hermite(x, A, mu, sigma, h3i, h4i)
        return y_fit

    log.info("Fitting Gauss-Hermite models + background %s", Polynomial(p0_bg))
    if len(p0_peaks) % 5 != 0:
        raise ValueError("p0_peaksmust be multple of 5: [A, mu, sigma, h3, h4] per peak.")
    p0 = np.concatenate([p0_bg, p0_peaks]).tolist()
    log.info("p0 = %s", p0)
    p0_bg = np.asarray(p0_bg, dtype=float)
    p0_peaks = np.asarray(p0_peaks, dtype=float)
    try:
        popt_gh, _ = curve_fit(
            model_gh,
            x,
            y,
            sigma=error_y,
            p0=p0,
            maxfev=maxfev,
            bounds=(-np.inf, np.inf),
        )
        log.info("popt_gh = %s", popt_gh)
        y_fit_gh = model_gh(x, *popt_gh)
        residuals = y - y_fit_gh
    except Exception as e:
        log.error("Gauss-Hermite fit error: %s", e)
        raise

    bg_opt = popt_gh[: p0_bg.size]
    peak_opt = popt_gh[p0_bg.size :]
    log.info("Background coefficients: %s", Polynomial(bg_opt))
    for A, mu, sigma, h3, h4 in itertools.batched(peak_opt, 5):
        log.info(
            "Component at λ=%.2f: sigma=%.3f, h3=%.3f, h4=%.3f",
            mu,
            sigma,
            h3,
            h4,
        )
    log.info(f"RMS residuals: {np.sqrt(np.mean(residuals**2)):.3e}")
    log.info(f"Residuals lineal drift: {np.polyfit(x, residuals, 2)[0]:.3e}")
    if error_y is not None:
        """
        If χ²/dof ≈1 then reasonable fit 
        If χ²/dof >> 1 model doesn't explain well the observed data
        If χ²/dof << 1 model then probably error overstimation.
        """
        dof = len(x) - len(popt_gh)
        log.info(f"χ²/DoF: {np.sum((residuals / error_y) ** 2) / dof:.3e}")

    return y_fit_gh, residuals


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
        y_fit, _ = gauss_hermite_fit(
            x,
            y1,
            p0_bg=p0.tolist()[:2],
            p0_peaks=[y1[peak], x[peak], fwhm / 2.355, 0, 0],
            h3=0,
            h4=0,
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
