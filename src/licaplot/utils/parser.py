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
from lica.validators import vfile
import astropy.units as u

# -----------------
# Auxiliary parsers
# -----------------

def csv_parser() -> ArgumentParser:
    """Generic parse option for CSV input files"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV input file",
    )
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        nargs="+",
        help="Dataset title/description",
    )
    parser.add_argument(
        "--label",
        type=str,
        required=True,
        help="Dataset short tag",
    )
    parser.add_argument(
        "-c",
        "--columns",
        type=str,
        default=None,
        nargs="+",
        metavar="<NAME>",
        help="Ordered list of CSV Column names. If not specified, uses the columm names inside the CSV (default %(default)s)",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        default=",",
        help="CSV column delimiter. (defaults to %(default)s)",
    )
    return parser

def wave_parser() -> ArgumentParser:
    """Parser options dealing with Wavelengths"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-wc",
        "--wave-col-order",
        type=int,
        metavar="<N>",
        default=1,
        help="Wavelength column order in CSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-wu",
        "--wave-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.nm,
        help="Wavelength units string (ie. nm, AA) %(default)s",
    )
    parser.add_argument(
        "-wl",
        "--wave-low",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength lower limit, defaults to %(default)s",
    )
    parser.add_argument(
        "-wh",
        "--wave-high",
        type=float,
        metavar="\u03bb",
        default=None,
        help="Wavelength upper limit, defaults to %(default)s",
    )
    return parser

def y_parser()-> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-yc",
        "--y-col-order",
        type=int,
        metavar="<N>",
        default=2,
        help="Column order for Y magnitude in CSV, defaults to %(default)d",
    )
    parser.add_argument(
        "-yu",
        "--y-unit",
        type=u.Unit,
        metavar="<Unit>",
        default=u.dimensionless_unscaled,
        help="Astropy Unit string (ie. nm, A/W, etc.), defaults to %(default)s",
    )
    return parser