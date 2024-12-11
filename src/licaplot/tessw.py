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

import astropy.units as u
from astropy.units import Quantity
from lica.cli import execute
from lica.photodiode import BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from . import TWCOL
from .utils import parser as prs
from .utils import processing

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# --------------------------------------------------
# Python API
#
# The Python API can be used within Jupyter Notebook
# --------------------------------------------------


def process(dir_path: str, save_flag: bool, gain: Quantity = 1 * u.nA / u.Hz) -> None:
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    sensor_dict = processing.active_process(
        photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ, gain=gain
    )
    if save_flag:
        processing.save(sensor_dict, dir_path)


def photodiode(
    photod_path: str,
    model: str,
    tag: str,
    wave_low: int = BENCH.WAVE_START,
    wave_high: int = BENCH.WAVE_END,
) -> str:
    """Returns the path of the newly created ECSV"""
    log.info("Converting to an Astropy Table: %s", photod_path)
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    return processing.photodiode_ecsv(photod_path, model, tag, wave_low, wave_high, manual=True)


def sensor(input_path: str, label: str, tag: str = "") -> None:
    """Returns the path of the newly created ECSV"""
    log.info("Converting to an Astropy Table: %s", input_path)
    return processing.tessw_ecsv(input_path, label, tag)


def one_tessw(
    input_path: str,
    photod_path: str,
    model: str,
    label: str = "",
    tag: str = "",
    wave_low: int = BENCH.WAVE_START,
    wave_high: int = BENCH.WAVE_END,
    gain: Quantity = 1 * u.nA / u.Hz,
) -> str:
    """Returns the path of the updated, reduced ECSV"""
    tag = tag or processing.random_tag()
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    processing.photodiode_ecsv(photod_path, model, tag, wave_low, wave_high, manual=True)
    result = processing.tessw_ecsv(input_path, label, tag)
    dir_path = os.path.dirname(input_path)
    just_name = processing.name_from_file(input_path)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable, just_name)
    processing.review(photodiode_dict, sensor_dict)
    sensor_dict = processing.active_process(
        photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ, gain=gain
    )
    processing.save(sensor_dict, dir_path)
    return result


# -------
# CLI API
# -------


def cli_process(args: Namespace) -> None:
    process(args.directory, args.save)


def cli_photodiode(args: Namespace) -> None:
    photodiode(args.photod_file, args.model, args.tag, args.wave_low, args.wave_high)


def cli_sensor(args: Namespace) -> None:
    label = " ".join(args.label) if args.label else ""
    sensor(args.input_file, label, args.tag)


def cli_one_tessw(args: Namespace) -> None:
    label = " ".join(args.label) if args.label else ""
    one_tessw(
        args.input_file,
        args.photod_file,
        args.model,
        label,
        args.tag,
        args.wave_low,
        args.wave_high,
    )


def cli_review(args: Namespace) -> None:
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    processing.review(photodiode_dict, sensor_dict)


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
    parser_one.set_defaults(func=cli_one_tessw)

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
    parser_sensor = subsubparser.add_parser(
        "sensor", parents=[prs.inputf(), prs.tag()], help="sensor subcommand"
    )
    parser_sensor.set_defaults(func=cli_sensor)
    parser_review = subsubparser.add_parser(
        "review", parents=[prs.folder()], help="review classification subcommand"
    )
    parser_review.set_defaults(func=cli_review)


# ================
# MAIN ENTRY POINT
# ================


def cli_main(args: Namespace) -> None:
    args.func(args)


def main() -> None:
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="TESS-W spectral response",
    )
