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
from lica.cli import execute

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from . import TWCOL, PROCOL
from .utils import parser as prs
from .utils import processing
from .utils.processing import DeviceDict

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


def to_Hz_per_nA(sensor_dict: DeviceDict) -> None:
    """Better suited for display and proceeesing"""
    for tag, sensors in sensor_dict.items():
        for table in sensors:
            table[PROCOL.SPECTRAL] = table[PROCOL.SPECTRAL].to(u.Hz / u.nA)


# --------------------------------------------------
# Python API
#
# The Python API can be used within Jupyter Notebook
# --------------------------------------------------


def process(dir_path: str, save_flag: bool) -> None:
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    sensor_dict = processing.active_process(photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ)
    to_Hz_per_nA(sensor_dict)
    if save_flag:
        processing.save(sensor_dict, dir_path)


def photodiode(photod_path: str, model: str, tag: str, wave_low: int, wave_high: int) -> None:
    log.info("Converting to an Astropy Table: %s", photod_path)
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    processing.photodiode_ecsv(photod_path, tag, model, wave_low, wave_high, manual=True)


def sensor(input_path: str, tag: str, label: str) -> None:
    log.info("Converting to an Astropy Table: %s", input_path)
    label = " ".join(label) if label else ""
    processing.tessw_ecsv(input_path, tag, label)


def one_tessw(
    input_path: str,
    photod_path: str,
    model: str,
    tag: str,
    label: str,
    wave_low: int,
    wave_high: int,
) -> None:
    wave_low, wave_high = min(wave_low, wave_high), max(wave_low, wave_high)
    processing.photodiode_ecsv(photod_path, tag, model, wave_low, wave_high)
    label = " ".join(label) if label else ""
    processing.tessw_ecsv(input_path, tag, label)
    dir_path = os.path.dirname(input_path)
    just_name = processing.name_from_file(input_path)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable, just_name)
    processing.review(photodiode_dict, sensor_dict)
    sensor_dict = processing.active_process(photodiode_dict, sensor_dict, sensor_column=TWCOL.FREQ)
    to_Hz_per_nA(sensor_dict)
    processing.save(sensor_dict, dir_path)


# -------
# CLI API
# -------


def cli_process(args: Namespace) -> None:
    process(args.directory, args.save)


def cli_photodiode(args: Namespace) -> None:
    photodiode(args.photod_file, args.model, args.tag, args.wave_low, args.wave_high)


def cli_sensor(args: Namespace) -> None:
    sensor(args.input_file, args.tag, args.label)


def cli_one_tessw(args: Namespace) -> None:
    one_tessw(
        args.input_file,
        args.photod_file,
        args.model,
        args.tag,
        args.label,
        args.wave_low,
        args.wave_high,
    )


def cli_review(args: Namespace) -> None:
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, sensor_dict = processing.classify(dir_iterable)
    processing.review(photodiode_dict, sensor_dict)


# Soon to be moved to Jupyter ...
def theory_tessw(args: Namespace) -> None:
    table = processing.tsl237_table(args.input_file, tag="", label="TSL237 Dataseet", resolution=5)
    filter_table = processing.read_ecsv(args.uvir_file)
    table["Corrected by Filter"] = table[PROCOL.SPECTRAL] * filter_table[PROCOL.TRANS]
    out_path = processing.equivalent_ecsv(args.input_file)
    if args.save:
        table.write(out_path, delimiter=",", overwrite=True)
    log.info(table.info)


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
