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

from lica.validators import vfile, vdir
from lica.lab import BENCH
from lica.lab.photodiode import PhotodiodeModel
from lica.lab.ndfilters import NDFilter

# ------------------------
# Own modules and packages
# ------------------------

# -----------------
# Auxiliary parsers
# -----------------


def inputf() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV sensor/filter input file",
    )
    parser.add_argument(
        "-l",
        "--label",
        type=str,
        nargs="+",
        help="Label for metadata purposes",
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


def limits() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-wl",
        "--wave-low",
        type=int,
        metavar="\u03bb",
        default=BENCH.WAVE_START.value,
        help="Wavelength lower limit (nm), defaults to %(default)s",
    )
    parser.add_argument(
        "-wh",
        "--wave-high",
        type=int,
        metavar="\u03bb",
        default=BENCH.WAVE_END.value,
        help="Wavelength upper limit (nm), defaults to %(default)s",
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


def folder() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-d",
        "--directory",
        type=vdir,
        required=True,
        metavar="<Dir>",
        help="ECSV input directory",
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


def auxlines() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--filters",
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


def plot_parser(title: str) -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default=title,
        help="Plot title",
    )
    return parser


def ipath() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV sensor/filter input file",
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

def resol() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        choices=tuple(range(1, 11)),
        default=1,
        metavar="<N nm>",
        help="Resolution (defaults to %(default)d nm)",
    )
    return parser