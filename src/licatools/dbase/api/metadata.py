# --------------------
# System wide imports
# -------------------
import os
import csv
import glob
import hashlib
import logging
from collections import OrderedDict
from typing import Optional, Dict, Any

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


def _db_lookup(path: str, session: Session) -> Optional[Dict[str, Any]]:
    with session.begin():
        with open(path, "rb") as fd:
            contents = fd.read()
        digest = hashlib.md5(contents).hexdigest()
        q = select(LicaFile).where(LicaFile.digest == digest)
        existing = session.scalars(q).one_or_none()
        if not existing:
            result = None
        else:
            result = OrderedDict()
            result["timestamp"] = existing.creation_tstamp.strftime("%Y-%m-%d %H:%M:%S")
            result["name"] = os.path.basename(path)
            result["original_name"] = existing.original_name
            setup = existing.setup
            if setup:
                if setup.monochromator_slit:
                    result["monochromator_slit"] = setup.monochromator_slit
                if setup.input_slit:
                    result["input_slit"] = setup.input_slit
                if setup.psu_current:
                    result["psu_current"] = setup.input_slit
               
    return result


def db_lookup(path: str) -> Optional[Dict[str, Any]]:
    """Indiviudla file metadata lookup"""
    with Session() as session:
        return _db_lookup(path, session)

def remove_original_name(item: Dict[str, Any]) -> Dict[str, Any]:
    del item["original_name"]
    return item

def export(input_dir: str, output_path: str) -> bool:
    """Exports metradata for all LICA acquistion files in the given input directory"""
    iterator = glob.iglob(Extension.TXT, root_dir=input_dir)
    metadata = list()
    missing = list()
    with Session() as session:
        for name in iterator:
            path = os.path.join(input_dir, name)
            individual_metadata = _db_lookup(path, session)
            if individual_metadata:
                metadata.append(individual_metadata)
            else:
                missing.append(name)
    metadata = sorted(metadata, key=lambda x: x["timestamp"])
    log.info("found %d entries in the database, %d files are missing", len(metadata), len(missing))
    if metadata:
        metadata = list(map(remove_original_name, metadata))
        with open(output_path, "w", newline="") as fd:
            fieldnames =metadata[0].keys()
            writer = csv.DictWriter(fd, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for row in metadata:
                writer.writerow(row)
    return len(metadata) > 0
