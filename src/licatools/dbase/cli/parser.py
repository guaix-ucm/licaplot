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
from lica.validators import vnat, vdate

def idir() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-id",
        "--input-dir",
        type=str,
        default=os.getcwd(),
        help="Base directory to scan, defaults to %(default)s",
    )
    return parser

def depth() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-de",
        "--depth",
        type=vnat,
        default=1,
        help="Directory scanning depth %(default)s",
    )
    return parser


def tstamp() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-ts",
        "--timestamp",
        type=vdate,
        default=None,
        help="Event local time , defaults to %(default)s = now",
    )
    return parser

def comment() -> ArgumentParser:
    """Common options for plotting"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-co",
        "--comment",
        type=str,
        nargs="+",
        default=None,
        help="Event coment, defaults to %(default)s",
    )
    return parser
