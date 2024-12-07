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

from argparse import ArgumentParser

# ---------------------
# Thrid-party libraries
# ---------------------

from lica.validators import vfile, vdir
from lica.photodiode import PhotodiodeModel, BENCH

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
        help="Label for plotting purposes",
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