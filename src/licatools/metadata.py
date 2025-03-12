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
from argparse import ArgumentParser, Namespace


# ---------------------
# Third-party libraries
# ---------------------

from lica.cli import execute

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


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def cli_generate(args: Namespace) -> None:
    output_path = args.output_file or os.path.join(args.input_dir, "metadata.csv")
    log.info("Generating metadata for %s", args.input_dir)
    exported = api.metadata.export(args.input_dir, output_path)
    if exported:
        log.info("Output metadata file is %s", output_path)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


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
