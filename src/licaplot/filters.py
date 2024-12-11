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
from argparse import Namespace

# ---------------------
# Thrid-party libraries
# ---------------------

from lica.cli import execute
from lica.photodiode import BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import processing
from .utils import parser as prs

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

# ------------------
# Auxiliary fnctions
# ------------------

# --------------------------------------------------
# Python API
#
# The Python API can be used within Jupyter Notebook
# --------------------------------------------------


def process(dir_path: str, save_flag: bool) -> None:
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, filter_dict = processing.classify(dir_iterable)
    filter_dict = processing.passive_process(photodiode_dict, filter_dict)
    if save_flag:
        processing.save(filter_dict, dir_path)


def photodiode(
    photod_path: str,
    model: str,
    tag: str,
    wave_low: int = BENCH.WAVE_START,
    wave_high: int = BENCH.WAVE_END,
) -> None:
    """Returns the path of the newly created ECSV"""
    log.info("Converting to an Astropy Table: %s", photod_path)
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    return processing.photodiode_ecsv(photod_path, model, tag, wave_low, wave_high)


def filters(input_path: str, label: str = "", tag: str = "",) -> None:
    """Returns the path of the newly created ECSV"""
    log.info("Converting to an Astropy Table: %s", input_path)
    return processing.filter_ecsv(input_path, label, tag)


def one_filter(
    input_path: str,
    photod_path: str,
    model: str,
    label: str = "",
    tag: str = "",
    wave_low: int = BENCH.WAVE_START,
    wave_high: int = BENCH.WAVE_END,
) -> str:
    tag = tag or processing.random_tag()
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    processing.photodiode_ecsv(photod_path, model, tag, wave_low, wave_high)
    result = processing.filter_ecsv(input_path, label, tag)
    dir_path = os.path.dirname(input_path)
    just_name = processing.name_from_file(input_path)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, filter_dict = processing.classify(dir_iterable, just_name)
    processing.review(photodiode_dict, filter_dict)
    filter_dict = processing.passive_process(photodiode_dict, filter_dict)
    processing.save(filter_dict, dir_path)
    return result


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def cli_process(args: Namespace) -> None:
    process(args.directory, args.save)


def cli_photodiode(args: Namespace) -> None:
    photodiode(args.photod_file, args.model, args.tag, args.wave_low, args.wave_high)


def cli_filters(args: Namespace) -> None:
    label = " ".join(args.label) if args.label else ""
    filters(args.input_file, label, args.tag)


def cli_one_filter(args: Namespace) -> None:
    label = " ".join(args.label) if args.label else ""
    one_filter(
        args.input_file,
        args.photod_file,
        args.model,
        label,
        args.tag,
        args.wave_low,
        args.wave_high,
    )


def cli_review(args: Namespace):
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, filter_dict = processing.classify(dir_iterable)
    processing.review(photodiode_dict, filter_dict)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_one = subparser.add_parser(
        "one",
        parents=[prs.photod(), prs.inputf(), prs.tag(), prs.limits()],
        help="Process one CSV filter file with one CSV photodiode file",
    )
    parser_one.set_defaults(func=cli_one_filter)

    parser_classif = subparser.add_parser("classif", help="Classification commands")
    parser_passive = subparser.add_parser(
        "process", parents=[prs.folder(), prs.save()], help="Process command"
    )
    parser_passive.set_defaults(func=cli_process)

    subsubparser = parser_classif.add_subparsers(dest="subcommand")
    parser_photod = subsubparser.add_parser(
        "photod",
        parents=[prs.photod(), prs.tag(), prs.limits()],
        help="photodiode subcommand",
    )
    parser_photod.set_defaults(func=cli_photodiode)
    parser_filter = subsubparser.add_parser(
        "filter", parents=[prs.inputf(), prs.tag()], help="filter subcommand"
    )
    parser_filter.set_defaults(func=cli_filters)
    parser_review = subsubparser.add_parser(
        "review", parents=[prs.folder()], help="review classification subcommand"
    )
    parser_review.set_defaults(func=cli_review)


# ================
# MAIN ENTRY POINT
# ================


def cli_main(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Filters spectral response",
    )
