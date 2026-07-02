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
from typing import TypeAlias, Sequence, Tuple

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
from numpy.typing import NDArray
from numpy.polynomial.polynomial import Polynomial
from numpy.polynomial.polynomial import polyval

from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit


# --------------
# New Type Hints
# --------------

FloatSeq: TypeAlias = Sequence[float]
FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

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
    Devuelve un array de indices dende estan los picos
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
        bg = np.asarray(params[: len(p0_bg)], dtype=float)
        peak_params = params[len(p0_bg) :]
        y_fit = polyval(x, bg)
        for A, mu, sigma, h3i, h4i in itertools.batched(peak_params, len(p0_peaks)):
            y_fit += gauss_hermite(x, A, mu, sigma, h3i, h4i)
        return y_fit

    log.info("Fitting Gauss-Hermite models + background %s", Polynomial(p0_bg))
    if len(p0_peaks) % 5 != 0:
        raise ValueError("p0_peaksmust be multple of 5: [A, mu, sigma, h3, h4] per peak.")
    p0 = p0_bg + p0_peaks
    log.info("p0 = %s", p0)
    try:
        popt, _ = curve_fit(
            model_gh,
            x,
            y,
            sigma=error_y,
            p0=p0,
            maxfev=maxfev,
            bounds=(-np.inf, np.inf),
        )
        log.info("popt = %s", popt)
        y_fit = model_gh(x, *popt)
        residuals = y - y_fit
    except Exception as e:
        log.error("Gauss-Hermite fit error: %s", e)
        raise

    bg_opt = popt[: len(p0_bg)]
    peak_opt = popt[len(p0_bg) :]
    log.info("Background coefficients: %s", Polynomial(bg_opt))
    for A, mu, sigma, h3, h4 in itertools.batched(peak_opt, len(p0_peaks)):
        log.info(
            "Component at x=%.2f: sigma=%.3f, h3=%.3f, h4=%.3f",
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
        dof = len(x) - len(popt)
        log.info(f"χ²/DoF: {np.sum((residuals / error_y) ** 2) / dof:.3e}")

    return y_fit, residuals


def gauss_fit(
    x: FloatArray,
    y: FloatArray,
    p0_bg: Sequence[float],  # backgroud polynomial coeffs in increasing order
    p0_peaks: Sequence[float],  # GH initial estimation [A1, mu1, sigma1, h3_1, h4_1, ...]
    error_y: FloatArray = None,
    maxfev: int = 25000,
) -> tuple[FloatArray, FloatArray]:
    """
    Ajuste de fondo polinomico + suma de perfiles Gauss.

    Cada componente se parametriza como:
        A * exp(-0.5 * u^2)

    donde:
        u = (x - mu) / sigma
    """

    def gauss(x: FloatArray, A: float, mu: float, sigma: float) -> FloatArray:
        """Single Gauss-Hermite function"""
        u = (x - mu) / sigma
        return A * np.exp(-0.5 * u**2)

    def model_gs(x: FloatArray, *params: float) -> FloatArray:
        bg = np.asarray(params[: len(p0_bg)], dtype=float)
        peak_params = params[len(p0_bg) :]
        y_fit = polyval(x, bg)
        for A, mu, sigma in itertools.batched(peak_params, len(p0_peaks)):
            y_fit += gauss(x, A, mu, sigma)
        return y_fit

    log.info("Fitting Gauss models + background %s", Polynomial(p0_bg))
    if len(p0_peaks) % 3 != 0:
        raise ValueError("p0_peaks must be multple of 3: [A, mu, sigma] per peak.")
    p0 = p0_bg + p0_peaks
    log.info("p0 = %s", p0)
    try:
        popt, _ = curve_fit(
            model_gs,
            x,
            y,
            sigma=error_y,
            p0=p0,
            maxfev=maxfev,
            bounds=(-np.inf, np.inf),
        )
        log.info("popt = %s", popt)
        y_fit = model_gs(x, *popt)
        residuals = y - y_fit
    except Exception as e:
        log.error("Gauss fit error: %s", e)
        raise

    bg_opt = popt[: len(p0_bg)]
    peak_opt = popt[len(p0_bg) :]
    log.info("Background coefficients: %s", Polynomial(bg_opt))
    for A, mu, sigma in itertools.batched(peak_opt, len(p0_peaks)):
        log.info("Component at x=%.2f: sigma=%.3f", mu, sigma)
    log.info(f"RMS residuals: {np.sqrt(np.mean(residuals**2)):.3e}")
    log.info(f"Residuals lineal drift: {np.polyfit(x, residuals, 2)[0]:.3e}")
    if error_y is not None:
        """
        If χ²/dof ≈1 then reasonable fit 
        If χ²/dof >> 1 model doesn't explain well the observed data
        If χ²/dof << 1 model then probably error overstimation.
        """
        dof = len(x) - len(popt)
        log.info(f"χ²/DoF: {np.sum((residuals / error_y) ** 2) / dof:.3e}")

    return y_fit, residuals
