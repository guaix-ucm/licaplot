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
import csv
import glob
import hashlib
import logging
from datetime import datetime
from argparse import ArgumentParser, Namespace
from typing import Dict

# ---------------------
# Third-party libraries
# ---------------------

import pytz
from astropy.time import Time

from lica.cli import execute


# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import parser as prs



digest.hexdigest()
# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)
madrid = pytz.timezone("Europe/Madrid")

# -------------------
# Auxiliary functions
# -------------------


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------

def get_timestamp(root_dir: str, filename: str) -> str:
    path = os.path.join(root_dir, filename)
    tstamp = datetime.fromtimestamp(os.path.getmtime(path))
    tstamp = madrid.localize(tstamp)
    tstamp = tstamp.astimezone(pytz.utc)
    result = tstamp.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    return result

def get_hash(root_dir: str, filename: str) -> str:
    path = os.path.join(root_dir, filename)
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, "md5")
    return digest.hexdigest()

def read_timestamps(path: str) -> Dict[str,str]:
    try:
        with open(path, 'r', newline='') as fd:
            reader = csv.reader(fd, delimiter=';')
            result = set((row[0], row[1], row[2]) for row in reader)
    except FileNotFoundError:
        result = set()
    return result


def cli_scan(args: Namespace) -> None:
    iterator = glob.iglob(args.glob_pattern, root_dir=args.input_dir)
    result = set((name, get_timestamp(args.input_dir, name)) for name in iterator)
    existing = read_timestamps(args.output_file)
    existing = existing.union(result)
    with open(args.output_file, 'w', newline='') as fd:
        writer = csv.writer(fd, delimiter=';')
        for item in sorted(existing, key=lambda x: x[0]):
            writer.writerow(item)



# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================

def globpat() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-gp",
        "--glob-pattern",
        type=str,
        default="*.txt",
        help="Glob pattern to scan, defaults to %(default)s",
    )
    return parser

def ofile() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        required=True,
        metavar="<File>",
        help="Timestamp output file",
    )
    return parser

def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    parser_scan = subparser.add_parser(
        "scan", parents=[prs.idir(), ofile(), globpat()], help="Directory to scan files for file creation time"
    )
    parser_scan.set_defaults(func=cli_scan)
    


# ================
# MAIN ENTRY POINT
# ================

def _main(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="LICA acquistion timestamps management",
    )
