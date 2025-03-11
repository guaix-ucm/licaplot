# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from argparse import ArgumentParser, Namespace

# ------------------
# SQLAlchemy imports
# -------------------

from lica.cli import execute
from lica.sqlalchemy import sqa_logging
from lica.sqlalchemy.dbase import engine, Model

# --------------
# local imports
# -------------

from licatools import __version__ as __version__

# We must pull one model to make it work
from .common.model import Config  # noqa: F401

# ----------------
# Module constants
# ----------------

DESCRIPTION = "LICA database initial schema generation tool"

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


def schema() -> None:
    with engine.begin():
        log.info("Dropping previous schema")
        Model.metadata.drop_all(bind=engine)
        log.info("Create new schema")
        Model.metadata.create_all(bind=engine)
    engine.dispose()


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    schema()


def add_args(parser: ArgumentParser) -> None:
    pass


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
