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

# Typing hints
from typing import Iterable, Any
from argparse import ArgumentParser, Namespace

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

from lica.cli import execute
from lica.validators import vfile

import astropy.io.ascii
from astropy.table import Table

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

MONOCROMATOR_CUTOFF_FILTERS = [
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
]

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# -------------------
# Auxiliary functions
# -------------------


def mpl_plot_single(
    table: Table,
    title: str,
    filters: Iterable[dict[str, Any]],
) -> None:
    fig, axes = plt.subplots(nrows=1, ncols=1)
    # fig.suptitle("Corrected Spectral Response plot")
    axes.set_xlabel(table.columns[0].name)
    axes.set_ylabel(table.columns[1].name)
    axes.plot(table.columns[0], table.columns[1], marker="+", linewidth=1)
    axes.set_title(title)
    for filt in filters:
        axes.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


def mpl_plot_overlapped() -> None:
    pass


def mpl_plot_dual() -> None:
    pass


def mpl_plot_quad() -> None:
    pass


def validate_inputs(*args):
    bounded = all(len(arg) <= 4 for arg in args)
    if not bounded:
        raise ValueError("An input argument list exceeds 4")
    same_length = all(len(arg) == len(args[0]) for arg in args)
    if not same_length:
        raise ValueError("Not all input argument lists have the same length")


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def csvs(args: Namespace) -> None:
    validate_inputs(args.input_files)
    tables = [astropy.io.ascii.read(f) for f in args.input_files]
    mpl_plot_single(table=tables[0], title="Hello", filters=MONOCROMATOR_CUTOFF_FILTERS)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-i", "--input-files", type=vfile, required=True, nargs="+", help="CSV input file(s) [1-4]"
    )
    parser.add_argument("-o", "--overlap", action="store_true", help="Overlap Plots")
    parser.add_argument("-t", "--title", type=str, help="Overall plot title")


# ================
# MAIN ENTRY POINT
# ================


def main():
    execute(
        main_func=csvs,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Plot 2-column CSV files",
    )
