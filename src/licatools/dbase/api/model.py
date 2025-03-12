# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------

import logging

from typing import Optional, List
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
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


class Setup(Model):
    __tablename__ = "setup_t"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Unique name identifying the setup
    name: Mapped[str] = mapped_column(String(64), unique=True)
    # Power Supply Current in amperes
    psu_current: Mapped[Optional[float]]
    # Monocromator slit micrometer apertue, in mm
    monochromator_slit: Mapped[Optional[float]]
    # General input flux microemeter slit, inmmm
    input_slit: Mapped[Optional[float]]
    # This is not a real column, it s meant for the ORM
    files: Mapped[List["LicaFile"]] = relationship(back_populates="setup")

    def __repr__(self) -> str:
        return f"File(Setup={self.name}, psu={self.psu_current}, slit={self.monochromator_slit}, input={self.input_slit})"



class LicaFile(Model):
    __tablename__ = "lica_file_t"

    id: Mapped[int] = mapped_column(primary_key=True)
    setup_id: Mapped[Optional[int]] = mapped_column(ForeignKey("setup_t.id"))
    original_name: Mapped[str] = mapped_column(String(65))
    original_dir: Mapped[str] = mapped_column(String(256))
    creation_tstamp: Mapped[datetime] = mapped_column(DateTime)
    # Creation date as YYYYMMDD for easy day filtering
    creation_date: Mapped[int]
    digest: Mapped[str] = mapped_column(String(128), unique=True)
    contents: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    # This isnot a real column, it is meant for the ORM
    setup: Mapped[Optional["Setup"]] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"File(name={self.original_name}, tstamp={datestr(self.creation_tstamp)})"
