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

import re
import csv
import logging
import argparse

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

from lica.cli import execute
from lica.validators import vfile

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.validators import vsequences

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# ------------------
# Auxiliary fnctions
# ------------------


def mpl_filters_plot_loop(title, x, y, xtitle, ytitle, plot_func, ylabels, **kwargs):
    fig, axes = plt.subplots(nrows=1, ncols=1)
    fig.suptitle(title)
    axes.set_xlabel(xtitle)
    axes.set_ylabel(ytitle)
    filters = kwargs.get("filters")
    diode = kwargs.get("diode")
    model = kwargs.get("model")
    # labels = kwargs.get('labels')
    Z, _ = y.shape
    for i in range(Z):
        plot_func(axes, i, x, y, ylabels, **kwargs)
    if filters is not None:
        for filt in filters:
            axes.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
    if diode is not None:
        axes.plot(x, diode, marker="o", linewidth=0, label=model)
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


# This is incomplete for 5 filter banks
def guess_color(label):
    label = label.lower()
    red = re.compile(r"red")
    green = re.compile(r"green")
    blue = re.compile(r"blue")
    if red.search(label):
        return "red"
    if green.search(label):
        return "green"
    if blue.search(label):
        return "blue"
    return "magenta"


def plot_filter_spectrum(axes, i, x, y, ylabels, **kwargs):
    wavelength = x
    signal = y[i]
    marker = "o"
    color = guess_color(ylabels[i])
    axes.plot(wavelength, signal, marker=marker, color=color, linewidth=1, label=ylabels[i])


def csv_readings_to_array(csv_path):
    log.info("reading CSV file %s", csv_path)
    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter="\t")
        contents = {int(round(float(row[1]), 0)): float(row[2]) for row in reader}
    wavelength = np.array(sorted(contents.keys()))
    signal = np.array(tuple(contents[key] for key in sorted(contents.keys())))
    return wavelength, signal


def validate_lists(args):
    if len(args.filters) != len(args.labels):
        raise ValueError("Number of labels must match number of filter files")
    if len(args.filters) < 1:
        raise ValueError("Missing filter CSV files")
    if len(args.diodes) < 1:
        raise ValueError("Missing calibration diode CSV files")


def get_info_from(args):
    accum = list()
    labels = list()
    diodes = list()
    for filt, label in zip(args.filters, args.labels):
        wavelength, signal = csv_readings_to_array(filt)
        accum.append(signal)
        labels.append(label)
    signal = np.vstack(accum)
    for diode in args.diodes:
        _, diode = csv_readings_to_array(diode)
        diodes.append(diode)
    # diode = np.vstack(diodes)
    # log.info("Before: Diode shapes is %s", diode.shape)
    diode = np.mean(np.vstack(diodes), axis=0)
    log.info("Diode shapes is %s", diode.shape)
    return wavelength, signal, labels, diode, args.model


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def raw_spectrum(args):
    log.info(" === DRAFT SPECTRAL RESPONSE PLOT === ")
    vsequences(4, args.filters, args.labels, args.diodes)
    tables = [astropy.io.ascii.read(f) for f in args.filters]
    for table in tables:
        table[""]


def corrected_spectrum(args):
    log.info(" === COMPLETE SPECTRAL RESPONSE PLOT === ")
    vsequences(4, args.filters, args.labels, args.diodes)
    return

    wavelength, signal, labels, diode, model = get_info_from(args)
    log.info
    responsivity, qe = photodiode_load(args.model, args.resolution)
    log.info(
        "Read %s reference responsivity values at %d nm resolution from %s",
        len(responsivity),
        args.resolution,
        args.model,
    )
    qe = np.array(
        [qe[w] for w in wavelength]
    )  # Only use those wavelenghts actually used in the CSV sequence
    diode = diode / np.max(diode)  # Normalize photodiode current
    signal = qe * signal / diode
    signal = signal / np.max(signal)  # Normalize signal to its absolute maxímun for all channels

    if args.export:
        log.info("exporting to CSV file(s)")
        export_spectra_to_csv(
            labels=labels,
            wavelength=wavelength,
            signal=signal,
            mode=args.export,
            units=args.units,
            wave_last=args.wavelength_last,
        )

    mpl_filters_plot_loop(
        title=f"Corrected response for {args.title}",
        plot_func=plot_filter_spectrum,
        xtitle="Wavelength [nm]",
        ytitle="Normalized signal level",
        ylabels=labels,
        x=wavelength,
        y=signal,
        filters=[
            {"label": r"$BG38 \Rightarrow OG570$", "wave": 570, "style": "--"},
            {"label": r"$OG570\Rightarrow RG830$", "wave": 860, "style": "-."},
        ],  # where filters were changesd
    )


COMMAND_TABLE = {
    "raw": raw_spectrum,
    "corrected": corrected_spectrum,
}


def filters(args):
    command = args.command
    func = COMMAND_TABLE[command]
    func(args)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================

def common_options():
    """Common command line arguments for raw and corrected plots"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        help='Filters set model (ie. "Astronomik L-RGB Type 2c"',
    )
    parser.add_argument(
        "-f",
        "--filters",
        required=True,
        metavar="<CSV>",
        nargs="+",
        type=vfile,
        help="Filter CSV files",
    )
    parser.add_argument(
        "-l",
        "--labels",
        required=True,
        metavar="<LABEL>",
        nargs="+",
        type=str,
        help="CSV file labels",
    )
    parser.add_argument(
        "-d",
        "--diodes",
        required=True,
        metavar="<CSV>",
        nargs="+",
        type=vfile,
        help="photodiode readings CSV files",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=Photodiode.OSI.value,
        choices=[p.value for p in Photodiode],
        help="Photodiode model. (default: %(default)s)",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_raw = subparser.add_parser("raw", help="Raw spectrum", parents=[common_options()])
    parser_corr = subparser.add_parser("corrected", help="Correced spectrum", parents=[common_options()])
   
    # ---------------------------------------------------------------------------------------------------------------

    parser_corr.add_argument(
        "-r",
        "--resolution",
        type=int,
        default=5,
        choices=(1, 5),
        help="Wavelength resolution (nm). (default: %(default)s nm)",
    )
    parser_corr.add_argument(
        "-x",
        "--export",
        type=str,
        choices=("combined", "individual"),
        help="Export to CSV file(s)",
    )
    parser_corr.add_argument(
        "-u",
        "--units",
        type=str,
        choices=("nm", "angs"),
        default="nm",
        help="Exported wavelength units. (default: %(default)s)",
    )
    parser_corr.add_argument(
        "-wl",
        "--wavelength-last",
        action="store_true",
        help="Wavelength is last column in exported file",
    )

    # ---------------------------------------------------------------------------------------------------------------


# ================
# MAIN ENTRY POINT
# ================


def main():
    execute(
        main_func=filters,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Filters spectral response",
    )
