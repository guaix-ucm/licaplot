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
from typing import Tuple

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

import astropy.io.ascii
import astropy.units as u

from lica.cli import execute
from lica.validators import vfile, vdir
from lica.photodiode import PhotodiodeModel, COL
import lica.photodiode

# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__

from .utils.table import scan_csv_to_table
from . import TBCOL, PROCOL, PROMETA

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


def _classify(path: str) -> Tuple[dict, defaultdict]:
    photodiode_dict = dict()
    filter_dict = defaultdict(list)
    for path in glob.iglob(os.path.join(path, "*.ecsv")):
        table = astropy.io.ascii.read(path, format="ecsv")
        key = table.meta["Processing"]["tag"]
        if table.meta["Processing"]["type"] == PROMETA.PHOTOD:
            if photodiode_dict.get(key):
                msg = f'Another photodiode table has the same tag: {table.meta["Processing"]["name"]}',
                log.critical(msg)
                raise RuntimeError(msg)
            else:
                photodiode_dict[key] = table
        else:
            filter_dict[key].append(table)
    return photodiode_dict, filter_dict

def _process(path: str) -> defaultdict:
    """Process Filter ECSV files in a given directory"""
    photodidode_dict, filter_dict = _classify(path)
    for key, photod_table in photodidode_dict.items():
        model = photod_table.meta["Processing"]["model"]
        resolution = photod_table.meta["Processing"]["resolution"]
        qe = lica.photodiode.load(model = model, resolution = int(resolution))[COL.QE]
        for filter_table in filter_dict[key]:
            name = filter_table.meta["Processing"]["name"]
            processed = filter_table.meta["Processing"].get("processed")
            if processed:
                log.warn("%s: Already being processed with %s", name, model)
                continue
            log.info("Processing %s with photodidode %s", name, model)
            transmission = (filter_table[TBCOL.CURRENT] / photod_table[TBCOL.CURRENT]) * qe
            filter_table[PROCOL.PHOTOD_CURRENT] = photod_table[TBCOL.CURRENT]
            filter_table[PROCOL.PHOTOD_QE] = qe
            filter_table[PROCOL.TRANS] = np.round(transmission, decimals=5) * u.dimensionless_unscaled
            filter_table.meta["Processing"]["using photodiode"] = model
            filter_table.meta["Processing"]["processed"] = True
    return filter_dict


def _save(filter_dict: defaultdict, path: str) -> None:
    for tag, filters in filter_dict.items():
        for filter_table in filters:
            name = filter_table.meta["Processing"]["name"]
            out_path = os.path.join(path, name)
            log.info("Updating ECSV file %s", out_path)
            filter_table.write(out_path, delimiter=",", overwrite=True)


def _photodiode(path: str, tag: str, model) -> None:
    """Converts CSV file from photodiode into ECSV file"""
    table = scan_csv_to_table(path)
    output_path = only_change_extension(path)
    resolution = np.ediff1d(table[COL.WAVE])
    assert all([r == resolution[0] for r in resolution])
    table.meta = {
        "Processing": {
            "type": PROMETA.PHOTOD.value,
            "model": model,
            "tag": tag,
            "name": os.path.basename(output_path),
            "resolution": resolution[0]
        }
    }
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    log.info("Saving Astropy table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)


def _filters(path: str, tag: str) -> None:
    table = scan_csv_to_table(path)
    resolution = np.ediff1d(table[COL.WAVE])
    output_path = only_change_extension(path)
    table.meta = {
        "Processing": {
            "type": PROMETA.FILTER.value,
            "tag": tag,
            "name": os.path.basename(output_path),
            "resolution": resolution[0]
        }
    }
    table.remove_column(TBCOL.INDEX)
    log.info("Processing metadata is added: %s", table.meta)
    log.info("Saving Astropy table to ECSV file: %s", output_path)
    table.write(output_path, delimiter=",", overwrite=True)  


def _review(dir_path: str) -> None:
    photodidode_dict, filter_dict = _classify(dir_path)
    for key, table in photodidode_dict.items():
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
    log.info("Review step ok.")

# -----------------------
# AUXILIARY MAIN FUNCTION
# -----------------------

def process(args: Namespace) -> defaultdict:
    log.info("Procesing Tables in: %s", args.directory)
    filter_dict = _process(args.directory)
    if args.save:
        _save(filter_dict, args.directory)

def photodiode(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    _photodiode(args.input_file, args.tag, args.model)



def filters(args: Namespace):
    log.info("Converting to an Astropy Table: %s", args.input_file)
    _filters(args.input_file, args.tag)


def review(args: Namespace):
    _review(args.directory)


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
        help="ECSV input directory",
    )
    # ---------------------------------------------------------------------------------------------------------------
    parser_process.add_argument(
        "-d",
        "--directory",
        type=vdir,
        required=True,
        metavar="<Dir>",
        help="ECSV input directory",
    )
    parser_process.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save processing file to ECSV",
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
