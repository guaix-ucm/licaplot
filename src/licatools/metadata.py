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
import logging
from datetime import datetime
from argparse import ArgumentParser, Namespace


# ---------------------
# Third-party libraries
# ---------------------

from lica.cli import execute
from lica.validators import vfile

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import parser as prs
from .dbase import api
from .dbase.api import Extension, metadata  # noqa: F401


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

def vdate(datestr: str|list[str]) -> datetime:
    """Date & time validator for the command line interface"""
    if datestr.lower() == "now":
        date = datetime.now()  # Naive date, current Local date no tzinfo
    else:
        # These are all naive dates after all, the user may be specifingu UTC or Local Time
        # Except for the last one ...
        date = None
        formats = ("%Y-%m", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ")
        for fmt in formats:
            try:
                date = datetime.strptime(datestr, fmt)
            except ValueError:
                pass
        if date is None:
            raise ValueError(f"{datestr} is not a valid date format ({formats})")
    return date

# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------

def cli_file_time(args: Namespace):
    log.info(args)
    if args.from_date:
        modif_time =  args.from_date.timestamp()
        access_time = modif_time
    else:
        stats = os.stat(args.from_file)
        modif_time = stats.st_mtime
        access_time = stats.st_atime
    log.info("Setting '%s' modification time to %s", args.to_file, datetime.fromtimestamp(modif_time))
    timestamps = (access_time, modif_time)
    os.utime(args.to_file, timestamps)


def cli_generate(args: Namespace) -> None:
    output_path = args.output_file or os.path.join(args.input_dir, "metadata.csv")
    log.info("Generating metadata for %s", args.input_dir)
    exported = api.metadata.export(args.input_dir, args.glob_pattern, output_path)
    if exported:
        log.info("Output metadata file is %s", output_path)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================

def from_source() -> ArgumentParser:
    """Common Options for subparsers"""
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-ff",
        "--from-file",
        type=vfile,
        help="File to copy modification time  (defaults to %(default)s)",
    )
    group.add_argument(
        "-fd",
        "--from-date",
        type=vdate,
        help="Date modification time (defaults to %(default)s = current date)",
    )
    return parser


def to_file() -> ArgumentParser:
    """Common Options for subparsers"""
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-tf",
        "--to-file",
        required=True,
        type=vfile,
        help="File to overwrite modification time",
    )
    return parser

def globpat() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-gp",
        "--glob-pattern",
        choices=Extension,
        default=Extension.TXT,
        help="Glob pattern to scan, defaults to %(default)s",
    )
    return parser


def ofile() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default = None,
        metavar="<File>",
        help="metadata output file, defaults to %(default)s",
    )
    return parser


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    parser_scan = subparser.add_parser(
        "generate",
        parents=[prs.idir(), ofile(), globpat()],
        help="Generates a metadata file for the acquistion files in this directory",
    )
    parser_scan.set_defaults(func=cli_generate)
    parser_touch = subparser.add_parser(
        "touch", parents=[to_file(), from_source()], help="Set file modification time"
    )
    parser_touch.set_defaults(func=cli_file_time)


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
        description="LICA acquistion files metadata maganement",
    )
