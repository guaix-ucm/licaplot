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
from typing import Sequence, Optional, Tuple

# ---------------------
# Thrid-party libraries
# ---------------------

from astropy.table import Table
import astropy.units as u
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from lica import StrEnum

# --------------
# Types and such
# --------------


class Markers(StrEnum):
    Circle = "o"
    Square = "s"
    Star = "*"
    Diamond = "d"
    TriUp = "2"
    TriDown = "1"
    Point = "."
    X = "x"
    Plus = "+"


# ----------------
# Global variables
# ----------------

log = logging.getLogger(__name__)


MONOCROMATOR_CHANGES_LABELS = (
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)


def markers_grp(
    flat_markers: Sequence[Markers], ntab: int, ncol: int
) -> Sequence[Sequence[Markers]]:
    return (
        list(itertools.batched(flat_markers, ncol))
        if flat_markers is not None
        else [[None] * ncol] * ntab
    )


def legends_grp(flat_labels: Sequence[str], ntab: int, ncol: int) -> Sequence[Sequence[str]]:
    return (
        list(itertools.batched(flat_labels, ncol))
        if flat_labels is not None
        else [[None] * ncol] * ntab
    )


def set_axes_labels(axes: Axes, table: Table, x: int, y: int, percent: bool) -> None:
    """Get the labels for a table, using units if necessary"""
    xlabel = table.columns[x].name
    xunit = table.columns[x].unit
    xlabel = xlabel + f" [{xunit}]" if xunit != u.dimensionless_unscaled else xlabel
    ylabel = table.columns[y].name
    yunit = (
        u.pct
        if percent and table.columns[y].unit == u.dimensionless_unscaled
        else table.columns[y].unit
    )
    ylabel = ylabel + f" [{yunit}]" if yunit != u.dimensionless_unscaled else ylabel
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)


def _plot_single_tables_columns(
    tables: Sequence[Table],
    x: int,
    yy: Sequence[int],
    legends_grp: Sequence[Sequence[str]],
    title: Optional[str],
    changes: Optional[bool] = False,
    percent: Optional[bool] = False,
    linewidth: Optional[int] = 0,
    markers_grp: Optional[Sequence[Sequence[Markers]]] = None,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    log.info("yy = %s", yy)
    log.info("legends_grp = %s", legends_grp)
    log.info("markers_grp = %s", markers_grp)

    # Load global style sheets
    resource = "licaplot.resources.single"
    log.info("Loading Matplotlib resources from %s", resource)
    plt.style.use(resource)

    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    for table, legends, markers in zip(tables, legends_grp, markers_grp):
        set_axes_labels(axes, table, x, yy[0], percent)
        xcol = table.columns[x]
        log.info("markers = %s", markers)
        log.info("legends = %s", legends)
        markers = [marker for marker in Markers] if all(m is None for m in markers) else markers
        markers = itertools.cycle(markers)
        for y, legend, marker in zip(yy, legends, markers):
            ycol = (
                table.columns[y] * 100 * u.pct
                if percent and table.columns[y].unit == u.dimensionless_unscaled
                else table.columns[y]
            )
            axes.plot(xcol, ycol, marker=marker, linewidth=linewidth, label=legend)
    if changes:
        for change in MONOCROMATOR_CHANGES_LABELS:
            axes.axvline(change["wavelength"], linestyle=change["style"], label=change["label"])
    if box:
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        axes.text(x=box[1], y=box[2], s=box[0], transform=axes.transAxes, va="top", bbox=props)
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


def plot_single_table_column(
    table: Table,
    x: int,
    y: int,
    title: Optional[str],
    changes: Optional[bool] = False,
    percent: Optional[bool] = False,
    linewidth: Optional[int] = 0,
    marker: Optional[Markers] = None,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    _plot_single_tables_columns(
        tables=[table],
        x=x,
        yy=[y],
        legends_grp=legends_grp(None, ntab=1, ncol=1),
        title=title,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(marker, ntab=1, ncol=1),
        box=box,
    )

def plot_single_table_columns(
    table: Table,
    x: int,
    yy: Sequence[int],
    legends: Sequence[str],
    title: Optional[str],
    changes: Optional[bool] = False,
    percent: Optional[bool] = False,
    linewidth: Optional[int] = 0,
    markers: Optional[Sequence[Markers]] = None,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    _plot_single_tables_columns(
        tables=[table],
        x=x,
        yy=yy,
        legends_grp=legends_grp(legends, ntab=1, ncol=len(yy)),
        title=title,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(markers, ntab=1, ncol=len(yy)),
        box=box,
    )


def plot_single_tables_column(
    tables: Sequence[Table],
    x: int,
    y: int,
    legends: Sequence[str],
    title: Optional[str],
    changes: Optional[bool] = False,
    percent: Optional[bool] = False,
    linewidth: Optional[int] = 0,
    markers: Optional[Sequence[Markers]] = None,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    _plot_single_tables_columns(
        tables=tables,
        x=x,
        yy=[y],
        legends_grp=legends_grp(legends, ntab=len(tables), ncol=1),
        title=title,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(markers, ntab=len(tables), ncol=1),
        box=box,
    )


def plot_single_tables_columns(
    tables: Sequence[Table],
    x: int,
    yy: Sequence[int],
    legends: Sequence[str],
    title: Optional[str],
    changes: Optional[bool] = False,
    percent: Optional[bool] = False,
    linewidth: Optional[int] = 0,
    markers: Optional[Sequence[Markers]] = None,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    _plot_single_tables_columns(
        tables=tables,
        x=x,
        yy=yy,
        legends_grp=legends_grp(legends, ntab=len(tables), ncol=len(yy)),
        title=title,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(markers, ntab=len(tables), ncol=len(yy)),
        box=box,
    )

# =================== #
# MULTI AXES PLOTTING #
# =================== #

def _plot_multi_tables_columns(
    nrows: int,
    ncols: int,
    tables: Sequence[Table],
    x: int,
    yy: Sequence[int],
    legends_grp: Sequence[Sequence[str]],
    titles: Optional[Sequence[str]],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    markers_grp: Optional[Sequence[Markers]],
    boxes: Optional[Sequence[Tuple[str, float, float]]] = None,
) -> None:
    log.info("yy = %s", yy)
    log.info("legends_grp = %s", legends_grp)
    log.info("markers_grp = %s", markers_grp)
    # Load global style sheets
    resource = "licaplot.resources.multi"
    log.info("Loading Matplotlib resources from %s", resource)
    plt.style.use(resource)
    N = len(tables)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    boxes = [None]*N if boxes is None else boxes
    # From a numpy bidimensional array to a list if len(indexes) > 1
    axes = axes.flatten() if nrows*ncols > 1 else [axes]
    for ax, table, title, legends, markers, box in zip(axes, tables, titles, legends_grp, markers_grp, boxes):
        xcol = table.columns[x]
        ax.set_title(title)
        set_axes_labels(ax, table, x, yy[0], percent)
        log.info("markers = %s", markers)
        log.info("legends = %s", legends)
        markers = [marker for marker in Markers] if all(m is None for m in markers) else markers
        markers = itertools.cycle(markers)
        for y, legend, marker in zip(yy, legends, markers):
            ycol = (
                table.columns[y] * 100 * u.pct
                if percent and table.columns[y].unit == u.dimensionless_unscaled
                else table.columns[y]
            )
            ax.plot(xcol, ycol, marker=marker, linewidth=linewidth, label=legend)
        if changes:
            for change in MONOCROMATOR_CHANGES_LABELS:
                ax.axvline(change["wavelength"], linestyle=change["style"], label=change["label"])
        if box:
            props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
            axes.text(x=box[1], y=box[2], s=box[0], transform=axes.transAxes, va="top", bbox=props)
        ax.grid(True, which="major", color="silver", linestyle="solid")
        ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
        ax.minorticks_on()
        if changes:
            ax.legend()
    # Do not draw in unusued axes
    for ax in axes[N:]:
        ax.set_axis_off()
    plt.show()



def plot_multi_tables_column(
    nrows: int,
    ncols: int,
    tables: Sequence[Table],
    x: int,
    y: int,
    titles: Optional[Sequence[str]],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    marker: Optional[Markers],
    boxes: Optional[Sequence[Tuple[str, float, float]]] = None,
) -> None:
    _plot_multi_tables_columns(
        nrows=nrows,
        ncols=nrows,
        tables=tables,
        x=x,
        yy=[y],
        legends_grp=legends_grp(None, ntab=len(tables), ncol=1),
        titles=titles,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(marker, ntab=len(tables), ncol=1),
        boxes=boxes,
    )


def plot_multi_tables_columns(
    nrows: int,
    ncols: int,
    tables: Sequence[Table],
    x: int,
    yy: Sequence[int],
    legends: Sequence[str],
    titles: Optional[Sequence[str]],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    markers: Optional[Sequence[Markers]],
    boxes: Optional[Sequence[Tuple[str, float, float]]] = None,
) -> None:
     _plot_multi_tables_columns(
        nrows=nrows,
        ncols=nrows,
        tables=tables,
        x=x,
        yy=yy,
        legends_grp=legends_grp(legends, ntab=len(tables), ncol=len(yy)),
        titles=titles,
        changes=changes,
        percent=percent,
        linewidth=linewidth,
        markers_grp=markers_grp(markers, ntab=len(tables), ncol=len(yy)),
        boxes=boxes,
    )


# This is a rare cas, not being used for the time being
def plot_multi_table_columns(
    nrows: int,
    ncols: int,
    table: Table,
    x: int,
    yy: Sequence[int],
    legends: Sequence[str],
    titles: Optional[Sequence[str]],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    """
    A strange use case with each column of a table plotted in a single axes.
    Not being used for the time being.
    """
    assert (nrows * ncols) >= len(yy)
    assert len(legends) == len(yy)
    assert len(titles) == len(yy)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    # From a numpy bidimensional array to a list if len(indexes) > 1
    indexes = list(range(nrows * ncols))
    axes = axes.flatten() if len(indexes) > 1 else [axes]
    xcol = table.columns[x]
    markers = itertools.cycle([marker for marker in Markers])
    marker = next(markers)
    N = len(yy)
    for i, ax, title, legend, y in zip(indexes, axes, titles, legends, yy):
        set_axes_labels(ax, table, x, y, percent)
        ycol = (
            table.columns[y] * 100 * u.pct
            if percent and table.columns[y].unit == u.dimensionless_unscaled
            else table.columns[y]
        )
        ax.plot(xcol, ycol, marker=marker, linewidth=linewidth, label=legend)
        if changes:
            for change in MONOCROMATOR_CHANGES_LABELS:
                ax.axvline(change["wavelength"], linestyle=change["style"], label=change["label"])
        ax.grid(True, which="major", color="silver", linestyle="solid")
        ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
        ax.minorticks_on()
        if changes:
            ax.legend()
    # Do not draw in unusued axes
    for ax in axes[N:]:
        ax.set_axis_off()
    plt.show()
