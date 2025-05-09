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

from .types import (
    Marker,
    LineStyle,
    ColNum,
    ColNums,
    Tables,
    Titles,
    Labels,
    LegendsGroup,
    MarkersGroup,
    LineStylesGroup,
)

from ...table import tcu

# ----------------
# Global variables
# ----------------


MONOCROMATOR_CHANGES_LABELS = (
    {"legend": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"legend": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)

log = logging.getLogger(__name__)


class PlotterBase(ABC):
    default_markers = [marker for marker in Marker if marker != Marker.Nothing]
    default_linestyles = [linestyle for linestyle in LineStyle if linestyle != LineStyle.Nothing]

    def __init__(
        self,
        xcn: ColNum,
        ycns_grp: ColNums,
        tables: Tables,
        titles: Titles,
        xlabels: Labels,
        ylabels: Labels,
        legends_grp: LegendsGroup,
        markers_grp: MarkersGroup,
        linestyles_grp: LineStylesGroup,
        changes: bool = False,
        percent: bool = False,
        log_y: bool = False,
        linewidth: int = 1,
        nrows: int = 1,
        ncols: int = 1,
        save_path: Optional[str] = None,
        save_dpi: Optional[int] = None,
    ):
        self.xcn = xcn
        self.ycns_grp = ycns_grp
        self.tables = tables
        self.titles = titles
        self.xlabels = xlabels
        self.ylabels = ylabels
        self.legends_grp = legends_grp
        self.markers_grp = markers_grp
        self.linestyles_grp = linestyles_grp
        self.changes = changes
        self.percent = percent
        self.linewidth = linewidth
        self.nrows = nrows
        self.ncols = ncols
        self.save_path = save_path
        self.save_dpi = save_dpi
        self.log_y = log_y
        # --------------------------------------------------
        # This context is created during the plot outer loop
        # --------------------------------------------------
        self.xcol = None  # Current Column object
        self.ax = None  # Current Axes object
        self.table = None  # Current Table object
        self.title = None  # Current title
        self.ycns = None # Current Y column list
        self.markers = None  # current markers list
        self.linestyles = None  # current linestyles list
        self.legends = None  # current legends list
        # --------------------------------------------------------
        # These variables are created during the inner loop unpack
        # --------------------------------------------------------
        self.ycn = None
        self.legend = None
        self.marker = None
        self.linestyle = None

        log.info("titles = %s", titles)
        log.info("xlabels = %s", xlabels)
        log.info("ylabels = %s", ylabels)
        log.info("ycns grp = %s", ycns_grp)
        log.info("legends grp = %s", legends_grp)
        log.info("markers grp = %s", markers_grp)
        log.info("linestyles grp = %s", linestyles_grp)

    def plot(self):
        self.plot_start_hook()
        self.load_mpl_resources()
        self.configure_axes()
        single_plot = self.nrows * self.ncols == 1
        for i, t in enumerate(self.get_outer_iterable_hook()):
            first_pass = i == 0
            self.unpack_outer_tuple_hook(t)
            self.outer_loop_start_hook(single_plot, first_pass)
            self.plot_monochromator_filter_changes(single_plot, first_pass)
            self.set_title(single_plot)
            self.set_log_scales()
            self.set_axes_labels(self.ycns[0])
            self.xcol = self.table.columns[self.xcn]
            for t in self.get_inner_iterable_hook():
                self.unpack_inner_tuple_hook(t)
                ycol = (
                    self.table.columns[self.ycn] * 100 * u.pct
                    if self.percent and tcu(self.table, self.ycn) == u.dimensionless_unscaled
                    else self.table.columns[self.ycn]
                )
                self.ax.plot(
                    self.xcol,
                    ycol,
                    marker=self.marker,
                    linewidth=self.linewidth,
                    linestyle=self.linestyle,
                    label=self.legend,
                )
                self.inner_loop_hook()
            self.set_grid()
            self.set_legends()
            self.outer_loop_end_hook(single_plot, first_pass)
        self.clear_unusued_axes()
        self.plot_end_hook()
        self.save_or_show()

    # =====
    # Hooks
    # =====

    def get_outer_iterable_hook(self):
        """Should be overriden if extra arguments are needed."""
        log.debug("configuring the outer loop")
        log.info(
            "there are %d axes, %d tables, %d titles, %d x-labels, %d y-labels, %d ycns groups, %d legenda groups, %d markers group & %d linestyles group",
            len(self.axes),
            len(self.tables),
            len(self.titles),
            len(self.xlabels),
            len(self.ylabels),
            len(self.ycns_grp),
            len(self.legends_grp),
            len(self.markers_grp),
            len(self.linestyles_grp),
        )
        # This is not to exhaust the zip iterator
        return zip(
            self.axes,
            self.tables,
            self.titles,
            self.xlabels,
            self.ylabels,
            self.ycns_grp,
            self.legends_grp,
            self.markers_grp,
            self.linestyles_grp,
        )

    def unpack_outer_tuple_hook(self, t: Tuple):
        """Should be overriden if extra arguments are needed."""
        (
            self.ax,
            self.table,
            self.title,
            self.xlabel,
            self.ylabel,
            self.ycns,
            self.legends,
            self.markers,
            self.linestyles,
        ) = t

    def get_inner_iterable_hook(self):
        return zip(self.ycns, self.legends, self.get_markers(), self.get_linestyles())

    def unpack_inner_tuple_hook(self, t: Tuple):
        """Should be overriden if extra arguments are needed."""
        self.ycn, self.legend, self.marker, self.linestyle = t

    def plot_start_hook(self):
        pass

    def plot_end_hook(self):
        pass

    def outer_loop_start_hook(self, single_plot: bool, first_pass: bool):
        """
        single_plot : Flag, single_plot Axis only
        first_pass: First outer loop pass (in case of multiple tables)
        """
        pass

    def outer_loop_end_hook(self, single_plot: bool, first_pass: bool):
        """
        single_plot : Flag, single_plot Axis only
        first_pass: First outer loop pass (in case of multiple tables)
        """
        pass

    def inner_loop_hook(self):
        pass

    # ==============
    # Helper methods
    # ==============

    def save_or_show(self):
        if self.save_path is not None:
            log.info("Saving to %s", self.save_path)
            plt.savefig(self.save_path, bbox_inches="tight", dpi=self.save_dpi)
        else:
            plt.show()

    def clear_unusued_axes(self):
        N = len(self.tables)
        for ax in self.axes[N:]:
            ax.set_axis_off()

    def set_log_scales(self):
        if self.log_y:
            self.ax.set_yscale("log")

    def set_title(self, single_plot: bool):
        if single_plot:
            self.fig.suptitle(self.titles[0])
        else:
            self.ax.set_title(self.title)

    def set_legends(self):
        self.ax.legend()

    def set_grid(self):
        self.ax.grid(True, which="major", color="silver", linestyle="solid")
        self.ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
        self.ax.minorticks_on()

    def plot_monochromator_filter_changes(self, single_plot: bool, first_pass: bool):
        if self.changes and (single_plot and first_pass) or not single_plot:
            for change in MONOCROMATOR_CHANGES_LABELS:
                self.ax.axvline(
                    change["wavelength"], linestyle=change["style"], label=change["legend"]
                )


    def get_markers(self) -> EnumType:
        markers = self.default_markers if all(m is None for m in self.markers) else self.markers
        return itertools.cycle(markers)

    def get_linestyles(self) -> EnumType:
        linestyles = (
            self.default_linestyles
            if all(ll is None for ll in self.linestyles)
            else self.linestyles
        )
        return itertools.cycle(linestyles)

    def set_axes_labels(self, y: int) -> None:
        """Get the labels for a table, using units if necessary"""
        xunit = tcu(self.table, self.xcn)
        xlabel = self.xlabel + f" [{xunit}]" if xunit != u.dimensionless_unscaled else self.xlabel
        # ylabel = self.table.columns[y].name
        yunit = (
            u.pct
            if self.percent and tcu(self.table, y) == u.dimensionless_unscaled
            else tcu(self.table, y)
        )
        ylabel = self.ylabel + f" [{yunit}]" if yunit != u.dimensionless_unscaled else self.ylabel
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

    def load_mpl_resources(self):
        single_plot = self.nrows * self.ncols == 1
        resource = "licatools.resources.single" if single_plot else "licatools.resources.multi"
        log.info("Loading Matplotlib resources from %s", resource)
        plt.style.use(resource)

    def configure_axes(self):
        single_plot = self.nrows * self.ncols == 1
        self.fig, axes = plt.subplots(nrows=self.nrows, ncols=self.ncols)
        self.axes = axes.flatten() if not single_plot else [axes] * len(self.tables)


class BasicPlotter(PlotterBase):
    pass
