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
import glob
import logging
from argparse import Namespace, ArgumentParser
import functools
import collections


# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

import astropy.io.ascii
from astropy.table import Table

from lica.cli import execute
from lica.validators import vfile, vdir
from lica.photodiode import PhotodiodeModel
import lica.photodiode
from .utils.table import scan_csv_to_table

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------
# Matplotlib styles
# -----------------

# Load global style sheets
plt.style.use("licaplot.resources.global")

# ------------------
# Auxiliary fnctions
# ------------------


def only_change_extension(path: str) -> str:
    """Keeps the same name and directory but changes extesion to ECSV"""
    output_path, _ = os.path.splitext(path)
    return output_path + ".ecsv"


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def process(args: Namespace):
    log.info(args)


def photodiode(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    table = scan_csv_to_table(args.input_file)
    output_path = only_change_extension(args.input_file)
    table.meta = {
        "Processing": {
            "type": "diode",
            "model": args.model,
            "tag": args.tag,
            "name": os.path.basename(output_path),
        }
    }
    log.info("Processing metadata is added: %s", table.meta)
    log.info("Saving Astropy table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


def filters(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    table = scan_csv_to_table(args.input_file)
    output_path = only_change_extension(args.input_file)
    table.meta = {
        "Processing": {"type": "filter", "tag": args.tag},
        "name": os.path.basename(output_path),
    }
    log.info("Processing metadata is added: %s", table.meta)
    log.info("Saving Astropy table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)

def review(args: Namespace):
    log.info("Reviewing Tables in: %s", args.directory)
    photodiode_table = dict()
    filter_table = collections.defaultdict(list)
    pattern = os.path.join(args.directory, "*.ecsv")
    for path in glob.iglob(pattern):
        log.info(path)
        table = astropy.io.ascii.read(path, format="ecsv")
        key = table.meta["Processing"]["tag"]
        if table.meta["Processing"]["type"] == "diode":
            other = photodiode_table.get(key)
            if other:
                log.error(
                    "Another photodiode table has the same tag: %s",
                    table.meta["Processing"]["name"],
                )
            else:
                photodiode_table[key] = table
        else:
            filter_table[key].append(table)
    for key, table in photodiode_table.items():
        name = table.meta["Processing"]["name"]
        model = table.meta["Processing"]["model"]
        clients=filter_table[key]
        names = [t.meta  for t in filter_table[key]]
        log.info("Photodiode %s (%s), tag = %s, used by %s", name, model, key, names)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def input_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        metavar="<tag>",
        default="A",
        help="Photodiode file tag, defaults to %(default)s",
    )
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV input file",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_classif = subparser.add_parser("classif", help="Classification commands")
    parser_process = subparser.add_parser("process", help="Process command")
    parser_process.set_defaults(func=process)

    subsubparser = parser_classif.add_subparsers(dest="subcommand")
    parser_photod = subsubparser.add_parser(
        "photod", parents=[input_parser()], help="photodiode subcommand"
    )
    parser_photod.set_defaults(func=photodiode)
    parser_filter = subsubparser.add_parser(
        "filter", parents=[input_parser()], help="filter subcommand"
    )
    parser_filter.set_defaults(func=filters)
    parser_review = subsubparser.add_parser("review", help="review classification subcommand")
    parser_review.set_defaults(func=review)

    # ---------------------------------------------------------------------------------------------------------------
    parser_photod.add_argument(
        "-m",
        "--model",
        type=str,
        choices=[model for model in PhotodiodeModel],
        default=PhotodiodeModel.OSI,
        help="Photodiode model, defaults to %(default)s",
    )

    # ---------------------------------------------------------------------------------------------------------------
    parser_review.add_argument(
        "-d",
        "--directory",
        type=vdir,
        required=True,
        metavar="<Dir>",
        help="CSV input file",
    )


# ================
# MAIN ENTRY POINT
# ================


def main_filters(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=main_filters,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Filters spectral response",
    )
