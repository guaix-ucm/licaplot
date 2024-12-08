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

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__

from .utils import parser as prs
from .utils import processing
from . import TWCOL

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

# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def process(args: Namespace) -> None:
    log.info("Classifying files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    sensor_dict = processing.active_process(photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ)
    if args.save:
        processing.save(sensor_dict, args.directory)


def photodiode(args: Namespace) -> None:
    log.info("Converting to an Astropy Table: %s", args.photod_file)
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    processing.photodiode_ecsv(
        args.photod_file, args.tag, args.model, args.wave_low, args.wave_high, manual=True
    )


def sensor(args: Namespace) -> None:
    log.info("Converting to an Astropy Table: %s", args.input_file)
    label = " ".join(args.label) if args.label else ""
    processing.tessw_ecsv(args.input_file, args.tag, label)


def review(args: Namespace) -> None:
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    processing.review(photodiode_dict, sensor_dict)


def one_tessw(args: Namespace) -> None:
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    processing.photodiode_ecsv(
        args.photod_file, args.tag, args.model, args.wave_low, args.wave_high
    )
    label = " ".join(args.label) if args.label else ""
    processing.tessw_ecsv(args.input_file, args.tag, label)
    dir_path = os.path.dirname(args.input_file)
    just_name = processing.name_from_file(args.input_file)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable, just_name)
    processing.review(photodiode_dict, sensor_dict)
    sensor_dict = processing.active_process(photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ)
    processing.save(sensor_dict, dir_path)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser) -> None:
    subparser = parser.add_subparsers(dest="command")
    parser_one = subparser.add_parser(
        "one",
        parents=[prs.photod(), prs.inputf(), prs.tag(), prs.limits()],
        help="Process one CSV TESS-W file with one CSV photodiode file",
    )
    parser_one.set_defaults(func=one_tessw)

    parser_classif = subparser.add_parser("classif", help="Classification commands")
    parser_passive = subparser.add_parser(
        "process", parents=[prs.folder(), prs.save()], help="Process command"
    )
    parser_passive.set_defaults(func=process)

    subsubparser = parser_classif.add_subparsers(dest="subcommand")
    parser_photod = subsubparser.add_parser(
        "photod",
        parents=[prs.photod(), prs.tag(), prs.limits()],
        help="photodiode subcommand",
    )
    parser_photod.set_defaults(func=photodiode)
    parser_sensor = subsubparser.add_parser(
        "sensor", parents=[prs.inputf(), prs.tag()], help="sensor subcommand"
    )
    parser_sensor.set_defaults(func=sensor)
    parser_review = subsubparser.add_parser(
        "review", parents=[prs.folder()], help="review classification subcommand"
    )
    parser_review.set_defaults(func=review)


# ================
# MAIN ENTRY POINT
# ================


def tessw(args: Namespace) -> None:
    args.func(args)


def main() -> None:
    execute(
        main_func=tessw,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="TESS-W spectral response",
    )
