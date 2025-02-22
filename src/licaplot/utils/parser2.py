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

import os
from argparse import ArgumentParser

# ---------------------
# Thrid-party libraries
# ---------------------

import astropy.units as u

from lica.validators import vfile, vdir
from lica.lab import BENCH
from lica.lab.photodiode import PhotodiodeModel
from lica.lab.ndfilters import NDFilter

# ------------------------
# Own modules and packages
# ------------------------

from .validators import vsequences,  vecsvfile

# ------------------------
# Plotting Related parsers
# ------------------------


def title(title: str, purpose: str) -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        nargs="+",
        default=title,
        help=f"{purpose} title",
    )
    return parser


def titles(title: str, purpose: str) -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        nargs="+",
        default=title,
        help=f"{purpose} title",
    )
    return parser


def label(purpose: str) -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-l",
        "--label",
        type=str,
        nargs="+",
        help=f"Label for {purpose} purposes",
    )
    return parser


def labels(purpose: str) -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-l",
        "--label",
        type=str,
        nargs="+",
        help=f"One or more labels for {purpose} purposes",
    )
    return parser

def ncols()  -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-nc",
        "--num-cols",
        type=int,
        default=1,
        help="Number of plotting Axes",
    )
    return parser

def xc() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-xc",
        "--x-column",
        type=int,
        metavar="<N>",
        default=1,
        help="Abcissa axes column number in CSV/ECSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-xu",
        "--x-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Abcissa axes units string (ie. nm, AA), defaults to %(default)s",
    )
    return parser


def yc() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-yc",
        "--y-column",
        type=int,
        metavar="<N>",
        default=2,
        help="Ordinate axis column number in CSV/ECSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-yu",
        "--y-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.dimensionless_unscaled,
        help="Ordinate axis string (ie. nm, A/W, etc.), defaults to %(default)s",
    )
    return parser


def yycc() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-yc",
        "--y-column",
        type=int,
        nargs="+",
        metavar="<N>",
        help="Ordinate axes column numbers in CSV/ECSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-yu",
        "--y-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Ordinate axis units string (ie. nm, AA) %(default)s",
    )
    return parser


def auxlines() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--changes",
        action="store_true",
        default=False,
        help="Plot Monocromator filter changes (default: %(default)s)",
    )
    parser.add_argument(
        "--lines",
        default=False,
        action="store_true",
        help="Connect dots with lines (default: %(default)s)",
    )
    return parser


def percent() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-%",
        "--percent",
        action="store_true",
        default=False,
        help="Display adimensional Y as a percent (default: %(default)s)",
    )
    return parser


# ----------------------
# Building Table parsers
# ----------------------


def ifile() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV/ECSV input file",
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


def ifiles() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vecsvfile,
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


def xlim() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-xl",
        "--x-low",
        type=int,
        metavar="<LOW>",
        default=BENCH.WAVE_START.value,
        help="Abcissa axes lower limit, defaults to %(default)s",
    )
    parser.add_argument(
        "-xh",
        "--x-high",
        type=int,
        metavar="<HIGH>",
        default=BENCH.WAVE_END.value,
        help="Abcissa axes upper limit, defaults to %(default)s",
    )
    parser.add_argument(
        "-lu",
        "--limits-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Abscissa limits units (ie. nm, A/W, etc.), defaults to %(default)s",
    )
    return parser


def lica() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--lica",
        action="store_true",
        help="Trims wavelength to LICA Optical Bench range [350nm-1050nm]",
    )
    return parser

### ONLY USED IN THE CASE OF  SINGLE COLUMN PLOTS
def resample() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-r",
        "--resample",
        choices=tuple(range(1, 11)),
        type=int,
        metavar="<N nm>",
        default=None,
        help="Resample wavelength to N nm step size, defaults to %(default)s",
    )
    return parser


# -------------
# Other parsers
# -------------


def idir() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-dir",
        type=vdir,
        default=os.getcwd(),
        metavar="<Dir>",
        help="Input ECSV directory (default %(default)s)",
    )
    return parser


def odir() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-o",
        "--output-dir",
        type=vdir,
        default=os.getcwd(),
        metavar="<Dir>",
        help="Output ECSV directory (default %(default)s)",
    )
    return parser


def tag() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        metavar="<tag>",
        default="A",
        help="File tag. Sensor/filter tags should match a photodiode tag, defaults value = '%(default)s'",
    )
    return parser


def photod() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=[model for model in PhotodiodeModel],
        default=PhotodiodeModel.OSI,
        help="Photodiode model, defaults to %(default)s",
    )
    parser.add_argument(
        "-p",
        "--photod-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV photodiode input file",
    )
    return parser


def save() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save processing file to ECSV",
    )
    return parser


def ndf() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-n",
        "--ndf",
        type=NDFilter,
        choices=NDFilter,
        default=None,
        help="Neutral Density Filter model, defaults to %(default)s",
    )
    return parser
