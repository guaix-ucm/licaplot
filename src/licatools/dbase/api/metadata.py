# --------------------
# System wide imports
# -------------------
import os
import csv
import glob
import hashlib
import logging

from typing import Optional

# ------------------
# SQLAlchemy imports
# -------------------

from sqlalchemy import select

from lica.sqlalchemy.dbase import Session

# --------------
# local imports
# -------------

from ... import __version__ as __version__

# We must pull one model to make it work
from ..api.model import Config, LicaFile, Setup  # noqa: F401
from ..api import Extension
# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])


def export(input_dir: str, output_path: str) -> bool:
    """Exports metradata for all LICA acquistion files in the given input directory"""
    iterator = glob.iglob(Extension.TXT, root_dir=input_dir)
    metadata = list()
    missing = list()
    with Session() as session:
        with session.begin():
            for name in iterator:
                path = os.path.join(input_dir, name)
                with open(path, "rb") as fd:
                    contents = fd.read()
                digest = hashlib.md5(contents).hexdigest()
                q = select(LicaFile).where(LicaFile.digest == digest)
                existing = session.scalars(q).one_or_none()
                if not existing:
                    missing.append(name)
                    log.debug("%s does not exists in database, skipping ...")
                    continue
                setup = existing.setup
                if setup:
                    metadata.append(
                        (
                            existing.creation_tstamp.strftime("%Y-%m-%d %H:%M:%S"),
                            name,
                            setup.monocromator_slit,
                            setup.input_slit,
                            setup.psu_current,
                        )
                    )
                else:
                    metadata.append((existing.creation_tstamp.strftime("%Y-%m-%d %H:%M:%S"), name, None, None, None))
    metadata = sorted(metadata, key=lambda x: x[0])
    log.info("found %d entries in the database, %d files are missing", len(metadata), len(missing))
    if metadata:
        with open(output_path, "w") as fd:
            writer = csv.writer(fd, delimiter=";")
            writer.writerow(("creation_time", "name", "monocromator_slit", "input_slit", "psu_current"))
            for row in metadata:
                writer.writerow(row)
    return len(metadata) > 0
