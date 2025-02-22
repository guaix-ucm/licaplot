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


MONOCROMATOR_CHANGES_LABELS = (
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)

# Cycles through the markers enum for overlapping plots
markers = itertools.cycle([marker for marker in Markers])


def get_labels(table: Table, x: int, y: int, percent: bool) -> Tuple[str, str]:
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
    return xlabel, ylabel


def plot_table_columns(
    table: Table,
    x: int,
    y: Sequence[int],
    labels: Sequence[str],
    title: Optional[str],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    box: Optional[Tuple[str, float, float]] = None,
    
) -> None:
    """Plot some columns of the same table in the same Axes using different markers"""
    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    # Take the Y legend form the first Y column in the list
    xlabel, ylabel = get_labels(table, x, y[0], percent)
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    for yy, label, marker in zip(y, labels, markers):
        xcol = table.columns[x]
        ycol = (
            table.columns[yy] * 100 * u.pct
            if percent and table.columns[yy].unit == u.dimensionless_unscaled
            else table.columns[yy]
        )
        axes.plot(xcol, ycol, marker=marker, linewidth=linewidth, label=label)
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


def plot_overlapped(
    tables: Sequence[Table],
    x: int,
    y: int,
    labels: Sequence[str],
    title: Optional[str],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],
    box: Optional[Tuple[str, float, float]] = None,
   
) -> None:
    """Plot the same columns of differnet tables in the same Axes using different markers"""
    fig, axes = plt.subplots(nrows=1, ncols=1)
    if title is not None:
        fig.suptitle(title)
    # Take the X, Y legends from the first table
    xlabel, ylabel = get_labels(tables[0], x, y, percent)
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    for table, label, marker in zip(tables, labels, markers):
        xcol = table.columns[x]
        ycol = (
            table.columns[y] * 100 * u.pct
            if percent and table.columns[y].unit == u.dimensionless_unscaled
            else table.columns[y]
        )
        axes.plot(xcol, ycol, marker=marker, linewidth=linewidth, label=label)
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


def plot_grid(
    tables: Sequence[Table],
    x: int,
    y: int,
    labels: Iterable[str],
    nrows: int,
    ncols: int,
    marker: str,
    title: Optional[str],
    changes: Optional[bool],
    percent: Optional[bool],
    linewidth: Optional[int],   
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
        xcol = table.columns[x]
        ax.set_title(label)
        xlabel, ylabel = get_labels(table, x, y, percent)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ycol = (
            table.columns[y] * 100 * u.pct
            if percent and table.columns[y].unit == u.dimensionless_unscaled
            else table.columns[y]
        )
        ax.plot(xcol, ycol, marker=marker, linewidth=linewidth)
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


def plot_cols(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    changes: Optional[bool],
    x: int,
    y: int,
    marker: Optional[str] = None,
    linewidth: Optional[int] = 1,
    percent: Optional[bool] = False,
) -> None:
    """Plot datasets as columns of axes"""
    plot_tables_grid(
        title=title,
        tables=tables,
        labels=labels,
        changes=changes,
        nrows=1,
        ncols=len(tables),
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
        percent=percent,
    )


def plot_single(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    changes: Optional[bool],
    x: int,
    y: int,
    marker: Optional[str] = None,
    linewidth: Optional[int] = 1,
    percent: Optional[bool] = False,
) -> None:
    """Plot a single dataset"""
    plot_tables_grid(
        title=title,
        tables=tables,
        labels=labels,
        changes=changes,
        nrows=1,
        ncols=1,
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
        percent=percent,
    )


def plot_rows(
    title: Optional[str],
    tables: Sequence[Table],
    labels: Iterable[str],
    changes: Optional[bool],
    x: int,
    y: int,
    marker: Optional[str] = None,
    linewidth: Optional[int] = 1,
    percent: Optional[bool] = False,
) -> None:
    """Plot datasets as rows of axes"""
    plot_tables_grid(
        title=title,
        tables=tables,
        labels=labels,
        changes=changes,
        nrows=len(tables),
        ncols=1,
        x=x,
        y=y,
        marker=marker,
        linewidth=linewidth,
        percent=percent,
    )
