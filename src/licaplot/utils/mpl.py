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
from typing import Iterable, Sequence, Optional, Tuple

# ---------------------
# Thrid-party libraries
# ---------------------

from astropy.table import Table
import astropy.units as u
import matplotlib.pyplot as plt

from lica import StrEnum

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

MONOCROMATOR_FILTERS_LABELS = (
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)

# Cycles through the markers enum for overlapping plots
markers = itertools.cycle([marker for marker in Markers])

def get_labels(table: Table, x: int, y: int) -> Tuple[str, str]:
    """Get the labels for a table, using units if necessary"""
    xlabel = table.columns[x].name
    xunit = table.columns[x].unit
    ylabel = table.columns[y].name
    yunit = table.columns[y].unit
    xlabel = xlabel + f" [{xunit}]" if xunit != u.dimensionless_unscaled else xlabel
    ylabel = ylabel + f" [{yunit}]" if yunit != u.dimensionless_unscaled else ylabel
    return xlabel, ylabel


def plot_overlapped(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    linewidth: Optional[int] = 0,
    box: Optional[Tuple[str, float, float]] = None,
) -> None:
    """Plot all datasets in the same Axes using different markers"""
    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    xlabel, ylabel = get_labels(tables[0], x, y)
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    for table, label, marker in zip(tables, labels, markers):
        axes.plot(table.columns[x], table.columns[y], marker=marker, linewidth=linewidth, label=label)
    if filters:
        for filt in MONOCROMATOR_FILTERS_LABELS:
            axes.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
    if box:
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        axes.text(x=box[1], y=box[2], s=box[0], transform=axes.transAxes, va="top", bbox=props)
    axes.grid(True, which="major", color="silver", linestyle="solid")
    axes.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
    axes.minorticks_on()
    axes.legend()
    plt.show()


def plot_grid(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    nrows: int,
    ncols: int,
    x: int,
    y: int,
    marker: str,
    linewidth: Optional[int] = 0,
) -> None:
    """Plot datasets in a grid of axes"""
    marker = marker or next(markers)
    N = len(tables)
    if nrows * ncols < N:
        raise ValueError(f"{nrows} x {ncols} Grid can't accomodate {N} graphics")
    indexes = list(range(nrows * ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    # From a numpy bidimensional array to a list if len(indexes) > 1
    axes = axes.flatten() if len(indexes) > 1 else [axes]
    if title is not None:
        fig.suptitle(title)
    for i, ax, table, label in zip(indexes, axes, tables, labels):
        ax.set_title(label)
        xlabel, ylabel = get_labels(table, x, y)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.plot(table.columns[x], table.columns[y], marker=marker, linewidth=linewidth)
        if filters:
            for filt in MONOCROMATOR_FILTERS_LABELS:
                ax.axvline(filt["wavelength"], linestyle=filt["style"], label=filt["label"])
        ax.grid(True, which="major", color="silver", linestyle="solid")
        ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
        ax.minorticks_on()
        if filters:
            ax.legend()
    # Do not draw in unusued axes
    for ax in axes[N:]:
        ax.set_axis_off()
    plt.show()


def plot_cols(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    marker:  Optional[str] = None,
    linewidth: Optional[int] = 1,
) -> None:
    """Plot datasets as columns of axes"""
    plot_grid(
        title=title,
        tables=tables,
        labels=labels,
        filters=filters,
        nrows=1,
        ncols=len(tables),
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
    )


def plot_single(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    marker: Optional[str] = None,
    linewidth: Optional[int] = 1,
) -> None:
    """Plot a single dataset"""
    plot_grid(
        title=title,
        tables=tables,
        labels=labels,
        filters=filters,
        nrows=1,
        ncols=1,
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
    )


def plot_rows(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    filters: Optional[bool],
    x: int,
    y: int,
    marker: Optional[str] = None,
    linewidth: Optional[int] = 1,
) -> None:
    """Plot datasets as rows of axes"""
    plot_grid(
        title=title,
        tables=tables,
        labels=labels,
        filters=filters,
        nrows=len(tables),
        ncols=1,
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
    )
