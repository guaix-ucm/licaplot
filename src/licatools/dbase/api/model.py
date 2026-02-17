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
    Enum,
    String,
    DateTime,
    LargeBinary,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from lica.sqlalchemy.noasync.model import Model

from .constants import Subject, Event

# ================
# Module constants
# ================


SubjectType: Enum = Enum(
    Subject,
    name="subject_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.upper() for e in x],
)

EventType: Enum = Enum(
    Event,
    name="event_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.upper() for e in x],
)


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


class LicaEvent(Model):
    __tablename__ = "lica_event_t"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Timestamp in UTC
    timestamp: Mapped[datetime] = mapped_column(DateTime, unique=True)
    subject: Mapped[SubjectType] = mapped_column(SubjectType)
    event: Mapped[EventType] = mapped_column(EventType)
    comment: Mapped[Optional[str]] = mapped_column(String(512))

    def __repr__(self) -> str:
        return f"LicaEvent(tstamp={self.timestamp}, subject={self.subject}, event={self.event})"


class LicaSetup(Model):
    __tablename__ = "lica_setup_t"

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
        return f"LicaSetup(name={self.name}, psu={self.psu_current}, slit={self.monochromator_slit}, input={self.input_slit})"


class LicaFile(Model):
    __tablename__ = "lica_file_t"

    id: Mapped[int] = mapped_column(primary_key=True)
    setup_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lica_setup_t.id"))
    original_name: Mapped[str] = mapped_column(String(65))
    original_dir: Mapped[str] = mapped_column(String(256))
    # Timestamp in UTC
    creation_tstamp: Mapped[datetime] = mapped_column(DateTime)
    # Creation date as YYYYMMDD (UTC) for easy day filtering
    creation_date: Mapped[int]
    digest: Mapped[str] = mapped_column(String(128), unique=True)
    contents: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    # This isnot a real column, it is meant for the ORM
    setup: Mapped[Optional["LicaSetup"]] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"LicaFile(name={self.original_name}, tstamp={datestr(self.creation_tstamp)})"
