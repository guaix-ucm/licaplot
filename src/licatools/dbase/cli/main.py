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
from typing import Sequence, Optional

# ------------------
# SQLAlchemy imports
# -------------------

import pytz
import sqlalchemy
from sqlalchemy import select

from lica.cli import execute
from lica.sqlalchemy import sqa_logging

# --------------
# local imports
# -------------

from ... import __version__ as __version__

from ..api import Extension, Subject, Event, engine, Session
from ..api import Model, Config, LicaFile, LicaSetup, LicaEvent
from . import parser as prs


# ----------------
# Module constants
# ----------------

DESCRIPTION = "LICA acqusition files database management tool"

MADRID = pytz.timezone("Europe/Madrid")


# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


def get_timestamp(path) -> datetime:
    tstamp = datetime.fromtimestamp(os.path.getmtime(path))
    tstamp = MADRID.localize(tstamp)
    return tstamp.astimezone(pytz.utc)


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
        for extension in Extension:
            alist = glob.glob(os.path.join(directory, extension))
            if alist:
                log.info(
                    "Scanning directory %s. Found %d files matching '%s'",
                    directory,
                    len(alist),
                    extension,
                )
            paths_set = paths_set.union(alist)
    return sorted(paths_set)


def create_lica_file(path: str, session: Session) -> Optional[LicaFile]:
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    timestamp = get_timestamp(path)
    date = int(timestamp.strftime("%Y%m%d"))
    with open(path, "rb") as fd:
        contents = fd.read()
    digest = hashlib.md5(contents).hexdigest()
    q = select(LicaFile).where(LicaFile.digest == digest)
    existing = session.scalars(q).one_or_none()
    if existing:
        result = None
        if filename != existing.original_name:
            log.warn(
                "File being loaded exists with another name %s under %s",
                existing.original_name,
                existing.original_dir,
            )
        elif dirname != existing.original_dir:
            log.warn(
                "File being loaded (%s) exists in another original directory: %s",
                existing.original_name,
                existing.original_dir,
            )
        else:
            log.debug("Skipping already loade file")

    else:
        result = LicaFile(
            original_name=filename,
            original_dir=dirname,
            creation_tstamp=timestamp,
            creation_date=date,
            digest=digest,
            contents=contents,
        )
    return result


# =============
# CLI FUNCTIONS
# =============


def cli_event_lamp_change(args: Namespace) -> None:
    tstamp = args.timestamp or datetime.now()
    tstamp = MADRID.localize(tstamp).astimezone(pytz.utc)
    comment = " ".join(args.comment) if args.comment else None
    with Session() as session:
        with session.begin():
            event = LicaEvent(
                subject=Subject.LAMP, timestamp=tstamp, event=Event.CHANGE, comment=comment
            )
            session.add(event)


def cli_event_lamp_on(args: Namespace) -> None:
    tstamp = args.timestamp or datetime.now()
    tstamp = MADRID.localize(tstamp).astimezone(pytz.utc)
    with Session() as session:
        with session.begin():
            event = LicaEvent(subject=Subject.LAMP, timestamp=tstamp, event=Event.ON)
            session.add(event)


def cli_event_lamp_off(args: Namespace) -> None:
    tstamp = args.timestamp or datetime.now()
    tstamp = MADRID.localize(tstamp).astimezone(pytz.utc)
    with Session() as session:
        with session.begin():
            event = LicaEvent(subject=Subject.LAMP, timestamp=tstamp, event=Event.OFF)
            session.add(event)


def cli_slurp(args: Namespace) -> None:
    file_paths = get_file_paths(args.input_dir, args.depth)
    with Session() as session:
        with session.begin():
            for path in file_paths:
                lica_file = create_lica_file(path, session)
                if lica_file:
                    session.add(lica_file)


def cli_populate(args: Namespace) -> None:
    with Session() as session:
        try:
            with session.begin():
                ancient = LicaSetup(name="ancient", psu_current=8.20, monochromator_slit=1.26)
                log.info("Populating with %s", ancient)
                session.add(ancient)
                eclipse = LicaSetup(name="eclipse", psu_current=8.20, monochromator_slit=2.5)
                log.info("Populating with %s", eclipse)
                session.add(eclipse)
                ndfilters = LicaSetup(name="ndfilters", psu_current=8.20, monochromator_slit=1.04)
                log.info("Populating with %s", ndfilters)
                session.add(ndfilters)
        except sqlalchemy.exc.IntegrityError:
            log.warn("LicaSetup data was already populated")


def cli_schema(args: Namespace) -> None:
    with engine.begin():
        log.info("Dropping previous schema")
        Model.metadata.drop_all(bind=engine)
        log.info("Create new schema")
        Model.metadata.create_all(bind=engine)
    engine.dispose()


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    args.func(args)


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(required=True)
    parser = subparser.add_parser("schema", help="Slurps files into the database")
    parser.set_defaults(func=cli_schema)
    parser = subparser.add_parser("populate", help="Populate setup with initial values")
    parser.set_defaults(func=cli_populate)
    parser = subparser.add_parser(
        "slurp", parents=[prs.idir(), prs.depth()], help="Slurps files into the database"
    )
    parser.set_defaults(func=cli_slurp)
    # ================
    # Event subparsers
    # ================
    parser_event = subparser.add_parser("event", help="Slurps files into the database")
    sub_event = parser_event.add_subparsers(required=True)
    # ---------------------
    # Lamp Events subparser
    # ---------------------
    prs_lamp = sub_event.add_parser("lamp", help="Lamp events")
    sub_lamp = prs_lamp.add_subparsers(required=True)
    prs_lamp_change = sub_lamp.add_parser(
        "change", parents=[prs.tstamp(), prs.comment()], help="Lamp change event"
    )
    prs_lamp_change.set_defaults(func=cli_event_lamp_change)
    prs_lamp_on = sub_lamp.add_parser("on", parents=[prs.tstamp()], help="Power on lamp event")
    prs_lamp_on.set_defaults(func=cli_event_lamp_on)
    prs_lamp_off = sub_lamp.add_parser("off", parents=[prs.tstamp()], help="Power off lamp event")
    prs_lamp_off.set_defaults(func=cli_event_lamp_off)


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
