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

from collections import defaultdict

# ---------------------
# Thrid-party libraries
# ---------------------

from lica.cli import execute
from lica.validators import vfile, vdir
from lica.photodiode import PhotodiodeModel, BENCH

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils.table import (
    name_from_file,
    classify,
    passive_process,
    photodiode_ecsv,
    device_ecsv,
)


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
    filter_dict = passive_process(photodiode_dict, filter_dict)
    if args.save:
        _save(filter_dict, args.directory)


def photodiode(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.photod_file)
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    photodiode_ecsv(args.photod_file, args.tag, args.model, args.wave_low, args.wave_high)


def filters(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    label = " ".join(args.label) if args.label else ""
    device_ecsv(args.input_file, args.tag, label)


def review(args: Namespace):
    log.info("Reviewing files in directory %s", args.directory)
    dir_iterable = glob.iglob(os.path.join(args.directory, "*.ecsv"))
    photodiode_dict, filter_dict = classify(dir_iterable)
    _review(photodiode_dict, filter_dict)


def one_filter(args: Namespace):
    args.wave_low, args.wave_high = (
        min(args.wave_low, args.wave_high),
        max(args.wave_low, args.wave_high),
    )
    photodiode_ecsv(args.photod_file, args.tag, args.model, args.wave_low, args.wave_high)
    label = " ".join(args.label) if args.label else ""
    device_ecsv(args.input_file, args.tag, label)
    dir_path = os.path.dirname(args.input_file)
    just_name = name_from_file(args.input_file)
    log.info("Classifying files in directory %s", dir_path)
    dir_iterable = glob.iglob(os.path.join(dir_path, "*.ecsv"))
    photodiode_dict, filter_dict = classify(dir_iterable, just_name)
    _review(photodiode_dict, filter_dict)
    filter_dict = passive_process(photodiode_dict, filter_dict)
    _save(filter_dict, dir_path)


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def input_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV filter input file",
    )
    parser.add_argument(
        "-l",
        "--label",
        type=str,
        nargs="+",
        help="label for plotting purposes",
    )
    return parser


def tag_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        metavar="<tag>",
        default="A",
        help="File tag, A Filter tag should match a Photodiode tag, defaults value = '%(default)s'",
    )
    return parser


def limits_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-wl",
        "--wave-low",
        type=int,
        metavar="\u03bb",
        default=BENCH.WAVE_START.value,
        help="Wavelength lower limit, defaults to %(default)s",
    )
    parser.add_argument(
        "-wh",
        "--wave-high",
        type=int,
        metavar="\u03bb",
        default=BENCH.WAVE_END.value,
        help="Wavelength upper limit, defaults to %(default)s",
    )
    return parser


def photod_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=[model for model in PhotodiodeModel],
        default=PhotodiodeModel.OSI,
        help="Photodiode model, defaults to %(default)s",
    )
    parser.add_argument(
        "-p",
        "--photod-file",
        type=vfile,
        required=True,
        metavar="<File>",
        help="CSV photodiode input file",
    )
    return parser


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_one = subparser.add_parser(
        "one",
        parents=[photod_parser(), input_parser(), tag_parser(), limits_parser()],
        help="Process one CSV filter file with one CSV photodiode file",
    )
    parser_one.set_defaults(func=one_filter)

    parser_classif = subparser.add_parser("classif", help="Classification commands")
    parserpassive_process = subparser.add_parser("process", help="Process command")
    parserpassive_process.set_defaults(func=process)

    subsubparser = parser_classif.add_subparsers(dest="subcommand")
    parser_photod = subsubparser.add_parser(
        "photod",
        parents=[photod_parser(), tag_parser(), limits_parser()],
        help="photodiode subcommand",
    )
    parser_photod.set_defaults(func=photodiode)
    parser_filter = subsubparser.add_parser(
        "filter", parents=[input_parser(), tag_parser()], help="filter subcommand"
    )
    parser_filter.set_defaults(func=filters)
    parser_review = subsubparser.add_parser("review", help="review classification subcommand")
    parser_review.set_defaults(func=review)
    # ---------------------------------------------------------------------------------------------------------------
    parser_review.add_argument(
        "-d",
        "--directory",
        type=vdir,
        required=True,
        metavar="<Dir>",
        help="ECSV input directory",
    )
    # ---------------------------------------------------------------------------------------------------------------
    parserpassive_process.add_argument(
        "-d",
        "--directory",
        type=vdir,
        required=True,
        metavar="<Dir>",
        help="ECSV input directory",
    )
    parserpassive_process.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save processing file to ECSV",
    )


# ================
# MAIN ENTRY POINT
# ================


def maindevice_ecsv(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=maindevice_ecsv,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Filters spectral response",
    )
