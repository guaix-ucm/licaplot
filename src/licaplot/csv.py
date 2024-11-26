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

from argparse import ArgumentParser, Namespace

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

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# -------------------
# Auxiliary functions
# -------------------

def mpl_plot_single() -> None:
    pass

def mpl_plot_overlapped() -> None:
    pass

def mpl_plot_dual() -> None:
    pass

def mpl_plot_quad() -> None:
    pass

# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def csvs(args: Namespace) -> None:
    log.info(args)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser: ArgumentParser) -> None:
    parser.add_argument("-i", "--input-file", type=vfile, nargs="+", help="CSV input file(s)")


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
