# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import os
import glob
import hashlib
import logging

from datetime import datetime
from argparse import ArgumentParser, Namespace
from typing import Sequence

# ---------------------
# Third party libraries
# ---------------------

import pytz
import sqlalchemy
from sqlalchemy import select

from lica.cli import execute
from lica.sqlalchemy import sqa_logging
from lica.sqlalchemy.dbase import Session

# --------------
# local imports
# -------------

from licatools import __version__ as __version__

from .common import parser as prs

# We must pull one model to make it work
from .common.model import LicaFile  # noqa: F401

# ----------------
# Module constants
# ----------------

DESCRIPTION = "LICA database initial schema generation tool"
EXTENSIONS = ("*.txt",)

MADRID = pytz.timezone("Europe/Madrid")

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


def scan_non_empty_dirs(root_dir: str, depth: int = None):
    if os.path.basename(root_dir) == "":
        root_dir = root_dir[:-1]
    dirs = set(dirpath for dirpath, dirs, files in os.walk(root_dir) if files)
    dirs.add(root_dir)  # Add it for images just under the root_dir folder
    if depth is None:
        return list(dirs)
    L = len(root_dir.split(sep=os.sep))
    return list(filter(lambda d: len(d.split(sep=os.sep)) - L <= depth, dirs))


def get_file_paths(root_dir: str, depth: int) -> Sequence[str]:
    directories = scan_non_empty_dirs(root_dir, depth)
    paths_set = set()
    for directory in directories:
        for extension in EXTENSIONS:
            alist = glob.glob(os.path.join(directory, extension))
            paths_set = paths_set.union(alist)
        N = len(paths_set)
        if N:
            log.info("Scanning directory %s. Found %d images matching '%s'", directory, N, EXTENSIONS)
    return sorted(paths_set)


def get_timestamp(path) -> datetime:
    tstamp = datetime.fromtimestamp(os.path.getmtime(path))
    tstamp = MADRID.localize(tstamp)
    return tstamp.astimezone(pytz.utc)


def process_file(path: str) -> None:
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    timestamp = get_timestamp(path)
    date = int(timestamp.strftime("%Y%m%d"))
    with open(path, "rb") as fd:
        contents = fd.read()
    digest = hashlib.md5(contents).hexdigest()
    with Session() as session:
        with session.begin():
            q = select(LicaFile).where(LicaFile.digest == digest)
            existing = session.scalars(q).one_or_none()
            if existing:
                if filename != existing.original_name:
                    log.warn(
                        "File being loaded exists with another name %s under %s",
                        existing.original_name,
                        existing.original_dir,
                    )
                elif dirname != existing.original_dir:
                    log.warn(
                        "File being loaded (%s) exists in another original directory: %s",
                        existing.original_name, existing.original_dir,
                    )
                else:
                    log.debug("Skipping already loade file")
            else:
                file = LicaFile(
                    original_name=filename,
                    original_dir=dirname,
                    creation_tstamp=timestamp,
                    creation_date=date,
                    digest=digest,
                    contents=contents,
                )
                session.add(file)


def slurp(args: Namespace) -> None:
    file_paths = get_file_paths(args.input_dir, args.depth)
    for path in file_paths:
        process_file(path)


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    slurp(args)


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(required=True)
    parser = subparser.add_parser(
        "files", parents=[prs.idir(), prs.depth()], help="Slurps files into the database"
    )
    parser.set_defaults(func=slurp)


def main():
    """The main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
