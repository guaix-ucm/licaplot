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

# -----------------
# Auxiliary parsers
# -----------------


def ifile() -> ArgumentParser:
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


def xlim() -> ArgumentParser:
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


def wave_limits() -> ArgumentParser:
    """Generic options dealing with wavelength trimming & resampling and its units"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-wl",
        "--wave-low",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength lower limit, (if not specified, taken from CSV), defaults to %(default)s",
    )
    parser.add_argument(
        "-wh",
        "--wave-high",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength upper limit, (if not specified, taken from CSV), defaults to %(default)s",
    )
    parser.add_argument(
        "-wlu",
        "--wave-limit-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Wavelength limits unit string (ie. nm, AA) %(default)s",
    )
    return parser

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

def lica() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--lica",
        action="store_true",
        help="Trims wavelength to LICA Optical Bench range [350nm-1050nm]",
    )
    return parser