# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------


# -------------------
# System wide imports
# -------------------


import logging
from enum import EnumType
from typing import Optional, Tuple

# ---------------------
# Third-party libraries
# ---------------------

from .types import Marker, ColNum, ColNums, Tables, Titles, LegendsGroup, MarkersGroup

from .base import BasicPlotter

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)


class BoxPlotter(BasicPlotter):
    def __init__(
        self,
        x: ColNum,
        yy: ColNums,
        tables: Tables,
        titles: Titles,
        legends_grp: LegendsGroup,
        markers_grp: MarkersGroup,
        changes: bool,
        percent: bool,
        linewidth: int,
        box: Tuple[str, float, float],
        nrows: int = 1,
        ncols: int = 1,
        save_path: Optional[str] = None,
        save_dpi: Optional[int] = None,
        markers_type: EnumType = Marker,
    ):
        super().__init__(
            x=x,
            yy=yy,
            tables=tables,
            titles=titles,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            changes=changes,
            percent=percent,
            linewidth=linewidth,
            nrows=nrows,
            ncols=ncols,
            save_path=save_path,
            save_dpi=save_dpi,
            markers_type=markers_type,
        )
        self.box = box

    # =====
    # Hooks
    # =====

    def outer_loop_hook(self, single: bool, first_pass: bool):
        """
        single : Flag, single Axis only
        first_pass: First outer loop pass (in case of multiple tables)
        """
        if (single and first_pass) or not single:
            props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
            self.ax.text(
                x=self.box[1],
                y=self.box[2],
                s=self.box[0],
                transform=self.ax.transAxes,
                va="top",
                bbox=props,
            )
