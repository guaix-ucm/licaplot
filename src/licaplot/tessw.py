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

from collections import defaultdict

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import astropy.io.ascii
import astropy.units as u
from astropy.table import Table

from lica import StrEnum
from lica.cli import execute

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.processing import (
    name_from_file,
    classify,
    active_process,
    photodiode_ecsv,
    filter_ecsv,
)

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


class TWCOL(StrEnum):
    """TESS-W columns as expoerted by textual-spectess"""

    TIME = "timestamp"
    SEQ = "udp_message"
    WAVE = "wavelength (nm)"
    FREQ = "frequency (Hz)"
    FILT = "filter"


def tess_csv_to_table(path: str, delimiter=";", data_start=1) -> Table:
    """Load CSV files produced by LICA Scan.exe (QEdata.txt files)"""
    table = astropy.io.ascii.read(
        path,
        delimiter=delimiter,
        data_start=data_start,
        names=(TWCOL.TIME, TWCOL.SEQ, TWCOL.WAVE, TWCOL.FREQ, TWCOL.FILT),
        converters={
            TWCOL.TIME: str,
            TWCOL.SEQ: np.int32,
            TWCOL.WAVE: np.float64,
            TWCOL.FREQ: np.float64,
            TWCOL.FILT: str,
        },
    )
    table[TWCOL.WAVE] = table[TWCOL.WAVE] * u.nm
    table[TWCOL.FREQ] = table[TWCOL.FREQ] * u.Hz
    return table


def _save(filter_dict: defaultdict, dir_path: str) -> None:
    for tag, filters in filter_dict.items():
        for filter_table in filters:
            name = filter_table.meta["Processing"]["name"] + ".ecsv"
            out_path = os.path.join(dir_path, name)
            log.info("Updating ECSV file %s", out_path)
            filter_table.write(out_path, delimiter=",", overwrite=True)


def _review(photodiode_dict: dict, filter_dict: defaultdict) -> None:
    for key, table in photodiode_dict.items():
        name = table.meta["Processing"]["name"]
        model = table.meta["Processing"]["model"]
        diode_resol = table.meta["Processing"]["resolution"]
        filters = filter_dict[key]
        names = [t.meta["Processing"]["name"] for t in filters]
        log.info("[tag=%s] (%s) %s, used by %s", key, model, name, names)
        for t in filters:
            filter_resol = t.meta["Processing"]["resolution"]
            if filter_resol != diode_resol:
                msg = f"Filter resoultion {filter_resol} does not match photodiode readings resolution {diode_resol}"
                log.critical(msg)
                raise RuntimeError(msg)
    photod_tags = set(photodiode_dict.keys())
    filter_tags = set(filter_dict.keys())
    excludeddevice_ecsv = filter_tags - photod_tags
    excluded_photod = photod_tags - filter_tags
    for key in excludeddevice_ecsv:
        names = [t.meta["Processing"]["name"] for t in filter_dict[key]]
        log.warn("%s do not match a photodiode tag", names)
    for key in excluded_photod:
        name = photodiode_dict[key].meta["Processing"]["name"]
        log.warn("%s do not match an input file tag", names)
    log.info("Review step ok.")


# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------


def process(args: Namespace) -> defaultdict:
    log.info("Classifying files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, filter_dict = classify(dir_iterable)
    filter_dict = active_process(photodiode_dict, filter_dict)
    if args.save:
        _save(filter_dict, args.directory)


def photodiode(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.photod_file)
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    photodiode_ecsv(args.photod_file, args.tag, args.model, args.wave_low, args.wave_high)


def sensor(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    label = " ".join(args.label) if args.label else ""
    filter_ecsv(args.input_file, args.tag, label)


def review(args: Namespace):
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, filter_dict = classify(dir_iterable)
    _review(photodiode_dict, filter_dict)


def one_tessw(args: Namespace):
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    photodiode_ecsv(args.photod_file, args.tag, args.model, args.wave_low, args.wave_high)
    label = " ".join(args.label) if args.label else ""
    filter_ecsv(args.input_file, args.tag, label)
    dir_path = os.path.dirname(args.input_file)
    just_name = name_from_file(args.input_file)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, filter_dict = classify(dir_iterable, just_name)
    _review(photodiode_dict, filter_dict)
    filter_dict = active_process(photodiode_dict, filter_dict)
    _save(filter_dict, dir_path)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser):
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
        "sensor", parents=[prs.input(), prs.tag()], help="sensor subcommand"
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


def main():
    execute(
        main_func=tessw,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="TESS-W spectral response",
    )
