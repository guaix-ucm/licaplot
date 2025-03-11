# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------

import logging

from typing import Optional
from datetime import datetime

# =====================
# Third party libraries
# =====================

from sqlalchemy import (
    select,
    func,
    Enum,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    LargeBinary,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from lica.sqlalchemy.dbase import Model


# ================
# Module constants
# ================

# =======================
# Module global variables
# =======================

# get the module logger
log = logging.getLogger(__name__)


def datestr(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z%z") if dt is not None else None


# =================================
# Data Model, declarative ORM style
# =================================

# --------
# Entities
# --------


class Config(Model):
    __tablename__ = "config_t"

    section: Mapped[str] = mapped_column(String(32), primary_key=True)
    prop: Mapped[str] = mapped_column("property", String(255), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"Config(section={self.section!r}, prop={self.prop!r}, value={self.value!r})"


class LicaFile(Model):
    __tablename__ = "lica_file_t"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str] = mapped_column(String(256))
    creation_tstamp: Mapped[datetime] = mapped_column(DateTime)
    digest: Mapped[str] = mapped_column(String(128), unique=True)
    contents: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    def __repr__(self) -> str:
        return f"File(name={self.original_name}, tstamp={datestr(self.creation_tstamp)})"
