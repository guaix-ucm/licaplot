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
from typing import Optional, Tuple

# ---------------------
# Third-party libraries
# ---------------------

# ------------------------
# Own modules and packages
# ------------------------

from .types import ColNum, ColNums, Tables, Titles, Labels, LegendsGroup, MarkersGroup, LineStylesGroup

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
        ylabels: Labels,
        legends_grp: LegendsGroup,
        markers_grp: MarkersGroup,
        linestyles_grp: LineStylesGroup,
        box: Tuple[str, float, float],
        changes: bool = True,
        percent: bool = False,
        linewidth: int = 1,
        nrows: int = 1,
        ncols: int = 1,
        save_path: Optional[str] = None,
        save_dpi: Optional[int] = None,
    ):
        super().__init__(
            x=x,
            yy=yy,
            tables=tables,
            titles=titles,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=changes,
            percent=percent,
            linewidth=linewidth,
            nrows=nrows,
            ncols=ncols,
            save_path=save_path,
            save_dpi=save_dpi,
        )
        self.box = box

    # =====
    # Hooks
    # =====

    def outer_loop_start_hook(self, single: bool, first_pass: bool):
        """
        single : Flag, single Axis only
        first_pass: First outer loop pass (in case of multiple tables)
        """
        if self.box is not None and ((single and first_pass) or not single):
            props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
            self.ax.text(
                x=self.box[1],
                y=self.box[2],
                s=self.box[0],
                transform=self.ax.transAxes,
                va="top",
                bbox=props,
            )
