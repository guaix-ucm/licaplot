# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------


# -------------------
# System wide imports
# -------------------

import itertools
import logging
from enum import EnumType
from abc import ABC
from typing import Optional, Tuple

# ---------------------
# Third-party libraries
# ---------------------

import astropy.units as u
import matplotlib.pyplot as plt

from .types import Markers, ColNum, ColNums, Tables, Titles, MarkersT, LegendsGroup, MarkersGroup


# ----------------
# Global variables
# ----------------


MONOCROMATOR_CHANGES_LABELS = (
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)

log = logging.getLogger(__name__)


class PlotterBase(ABC):
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
        nrows: int = 1,
        ncols: int = 1,
        save_path: Optional[str] = None,
        markers_type: EnumType = Markers,
    ):
        self.x = x
        self.yy = yy
        self.tables = tables
        self.titles = titles
        self.legends_grp = legends_grp
        self.markers_grp = markers_grp
        self.changes = changes
        self.percent = percent
        self.linewidth = linewidth
        self.nrows = nrows
        self.ncols = ncols
        self.single = nrows * ncols == 1
        # --------------------------------------------------
        # This context is created during the plot outer loop
        # --------------------------------------------------
        self.xcol = None  # Current Column object
        self.ax = None  # Current Axes object
        self.table = None  # Current Table object
        self.yy = None  # Current column number list
        self.title = None  # Current title
        self.markers = None  # current markers list
        self.legends = None  # current legends list
        self.ycol = None
        log.info("yy = %s", yy)
        log.info("legends_grp = %s", legends_grp)
        log.info("markers_grp = %s", markers_grp)

    def plot(self):
        self.plot_start_hook()
        self.load_mpl_resources()
        self.configure_axes()
        N = len(self.tables)
        if self.single:
            self.fig.suptitle(self.titles[0])
        for t in self.get_outer_iterable_hook():
            self.unpack_outer_tuple_hook(t)
            self.outer_loop_start()
            self.xcol = self.table.columns[self.x]
            if not self.single:
                self.ax.set_title(self.title)
            self.set_axes_labels(self.yy[0])
            log.info("title = %s", self.title)
            log.info("markers = %s", self.markers)
            log.info("legends = %s", self.legends)
            for y, legend, marker in zip(self.yy, self.legends, self.get_markers()):
                ycol = (
                    self.table.columns[y] * 100 * u.pct
                    if self.percent and self.table.columns[y].unit == u.dimensionless_unscaled
                    else self.table.columns[y]
                )
                self.ax.plot(self.xcol, ycol, marker=marker, linewidth=self.linewidth, label=legend)
                self.inner_loop_hook(legend, marker)
            if self.changes:
                for change in MONOCROMATOR_CHANGES_LABELS:
                    self.ax.axvline(
                        change["wavelength"], linestyle=change["style"], label=change["label"]
                    )
            self.outer_loop_hook()
            self.ax.grid(True, which="major", color="silver", linestyle="solid")
            self.ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
            self.ax.minorticks_on()
            if self.changes:
                self.ax.legend()
        self.outer_loop_end()
        # Do not draw in unusued axes
        N = len(self.tables)
        for ax in self.axes[N:]:
            ax.set_axis_off()
        self.plot_end_hook()
        if self.save_path is not None:
            log.info("Saving to %s", self.save_path)
            plt.savefig(self.save_path, bbox_inches="tight")
        else:
            plt.show()

    # =====
    # Hooks
    # =====

    def get_outer_iterable_hook(self):
        """Should be overriden if extra arguments are needed. i.e. a box per axes"""
        return zip(self.axes, self.tables, self.titles, self.legends_grp, self.markers_grp)

    def unpack_outer_tuple_hook(self, t: Tuple):
        """Should be overriden if extra arguments are needed. i.e. a box per axes"""
        self.ax, self.table, self.title, self.legends, self.markers = t

    def plot_start_hook(self):
        pass

    def outer_loop_round(self):
        pass

    def outer_loop_end(self):
        pass

    # ==============
    # Helper methods
    # ==============

    def get_markers(self) -> MarkersT:
        markers = (
            [marker for marker in self.markers_type]
            if all(m is None for m in self.markers)
            else self.markers
        )
        return itertools.cycle(markers)

    def set_axes_labels(self, y: int) -> None:
        """Get the labels for a table, using units if necessary"""
        xlabel = self.table.columns[self.x].name
        xunit = self.table.columns[self.x].unit
        xlabel = xlabel + f" [{xunit}]" if xunit != u.dimensionless_unscaled else xlabel
        ylabel = self.table.columns[y].name
        yunit = (
            u.pct
            if self.percent and self.table.columns[y].unit == u.dimensionless_unscaled
            else self.table.columns[y].unit
        )
        ylabel = ylabel + f" [{yunit}]" if yunit != u.dimensionless_unscaled else ylabel
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

    def load_mpl_resources(self):
        resource = "licaplot.resources.single" if self.single else "licaplot.resources.multi"
        log.info("Loading Matplotlib resources from %s", resource)
        plt.style.use(resource)

    def configure_axes(self):
        self.fig, axes = plt.subplots(nrows=self.nrows, ncols=self.ncols)
        self.axes = axes.flatten() if not self.single else [axes] * len(self.tables)

    def plot_init_inner_loop_hook(self):
        return zip(self.axes, self.tables, self.titles, self.legends_grp, self.markers_grp)
