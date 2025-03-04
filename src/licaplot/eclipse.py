# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import itertools
import logging
from argparse import Namespace, ArgumentParser
from typing import Sequence, Tuple

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

import astropy.units as u
from astropy.table import Table
from astropy import visualization
from lica.cli import execute


# ------------------------
# Own modules and packages
# ------------------------

from ._version import __version__
from .utils import parser as prs
from .utils.processing import read_ecsv
from .utils.mpl.plotter import (
    Marker,
    ColNum,
    BasicPlotter,
    TablesFromFiles,
    SingleTablesColumnBuilder,
    Director,
)


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

plt.rcParams["legend.fontsize"] = "10"


UVA_RANGE = (430, 400)
VIS_RANGE = (380, 780)
IR_RANGE = (780, 1040)

Y_LABEL = r"$log_{10}(\frac{1}{Transmittance})$"
REF_LINES = [
    {
        "label": "Max. luminous trans. (τv)",
        "value": 0.000032,
        "range": VIS_RANGE,
        "linestyle": "--",
    },
    {
        "label": "Min. luminous trans. (τv)",
        "value": 0.00000061,
        "range": VIS_RANGE,
        "linestyle": "-.",
    },
    {
        "label": "Max. solar UVA trans. (τSUVA)",
        "value": 0.000032,
        "range": UVA_RANGE,
        "linestyle": "--",
    },
    {
        "label": "Maxi. solar infrared trans. (τSIR)",
        "value": 0.03,
        "range": IR_RANGE,
        "linestyle": "-.",
    },
]

# -----------------
# Matplotlib styles
# -----------------

# -----------------
# Auxiliary classes
# -----------------


class EclipsePlotter(BasicPlotter):

    def plot(self):
        self.plot_start_hook()
        self.load_mpl_resources()
        self.configure_axes()
        N = len(self.tables)
        single_plot = self.nrows * self.ncols == 1
        if single_plot:
            self.fig.suptitle(self.titles[0])
        for i, t in enumerate(self.get_outer_iterable_hook()):
            first_pass = i == 0
            self.unpack_outer_tuple_hook(t)
            self.outer_loop_hook(single_plot, first_pass)
            self.xcol = self.table.columns[self.x]
            if not single_plot:
                self.ax.set_title(self.title)
            if self.log_y:
                self.ax.set_yscale("log")
            self.set_axes_labels(self.yy[0])
            for y, legend, marker in zip(self.yy, self.legends, self.get_markers()):
                ycol = (
                    self.table.columns[y] * 100 * u.pct
                    if self.percent and self.table.columns[y].unit == u.dimensionless_unscaled
                    else self.table.columns[y]
                )
                self.ax.plot(self.xcol, ycol, marker=marker, linewidth=self.linewidth, label=legend, linestyle=self.linestyle)
                self.inner_loop_hook(legend, marker)  
            self.ax.grid(True, which="major", color="silver", linestyle="solid")
            self.ax.grid(True, which="minor", color="silver", linestyle=(0, (1, 10)))
            self.ax.minorticks_on()
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=5, frameon=True)
        # Do not draw in unusued axes
        N = len(self.tables)
        for ax in self.axes[N:]:
            ax.set_axis_off()
        self.plot_end_hook()
        if self.save_path is not None:
            log.info("Saving to %s", self.save_path)
            plt.savefig(self.save_path, bbox_inches="tight", dpi=self.save_dpi)
        else:
            plt.show()

    def outer_loop_hook(self, single_plot: bool, first_pass: bool):
        """
        single_plot : Flag, single_plot Axis only
        first_pass: First outer loop pass (in case of multiple tables)
        """
        if (single_plot and first_pass) or not single_plot:
            # Dibujar líneas de referencia
            for ref in REF_LINES:
                label = ref["label"]
                y_value = ref["value"]
                ls = ref["linestyle"]
                x_min, x_max = ref["range"]
                y_val_ref = -np.log10(y_value)
                self.ax.hlines(
                    y=y_val_ref,
                    xmin=x_min,
                    xmax=x_max,
                    color="gray",
                    linestyle=ls,
                    label=f"{label}: {y_value:.8f}",
                )
        

    def get_outer_iterable_hook(self):
        """Should be overriden if extra arguments are needed."""
        log.debug("configuring the outer loop")
        log.debug("there are %d axes, %d tables, %d titles, %d legenda groups & %d markers group", 
            len(self.axes), len(self.tables), len(self.titles), len(self.legends_grp), len(self.markers_grp))
        titles = self.titles * len(self.tables) if len(self.titles) == 1 else self.titles
        return zip(self.axes, self.tables, titles, self.legends_grp, self.markers_grp, self.get_linestyles())

    def unpack_outer_tuple_hook(self, t: Tuple):
        """Should be overriden if extra arguments are needed."""
        self.ax, self.table, self.title, self.legends, self.markers, self.linestyle = t

    def get_markers(self) -> Sequence[str]:
        markers = (
            [marker for marker in self.markers_type if marker != Marker.Nothing]
            if all(m is None for m in self.markers)
            else self.markers
        )
        return itertools.cycle(markers)

    def get_linestyles(self) -> Sequence[str]:
        linestyles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 2))]
        return itertools.cycle(linestyles)

    def set_axes_labels(self, y: int) -> None:
        """Get the labels for a table, using units if necessary"""
        xlabel = self.table.columns[self.x].name
        xunit = self.table.columns[self.x].unit
        xlabel = xlabel + f" [{xunit}]" if xunit != u.dimensionless_unscaled else xlabel
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(Y_LABEL)


# -------------------
# Auxiliary functions
# -------------------


def colname() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--column-name",
        type=str,
        default=None,
        help="New column name with the processing (default %(default)s)",
    )
    return parser


def inverse(table: Table, yc: ColNum, col_name: str = None) -> None:
    ycol = table.columns[yc]
    yname = col_name or f"Inverse Log10 of {ycol.name}"
    log_ycol = -np.log10(ycol)
    table[yname] = log_ycol
    table.meta["History"].append(f"Added new f{yname} column")


def cli_inverse(args: Namespace):
    log.info("Processing %s", args.input_file)
    path = args.input_file
    table = read_ecsv(path)
    inverse(table, args.y_column - 1)
    if args.save:
        table.write(path, delimiter=",", overwrite=True)


def cli_single_plot_tables_column(args: Namespace):
    tb_builder = TablesFromFiles(
        paths=args.input_file,
        delimiter=args.delimiter,
        columns=args.columns,
        xcol=args.x_column,
        xunit=args.x_unit,
        ycol=args.y_column,
        yunit=args.y_unit,
        xlow=args.x_low,
        xhigh=args.x_high,
        lunit=args.limits_unit,
        resolution=args.resample,
        lica_trim=args.lica,
    )
    builder = SingleTablesColumnBuilder(
        builder=tb_builder,
        title=args.title,
        labels=args.labels,
        markers=args.markers,
    )
    director = Director(builder)
    
    elements = director.build_elements()
    log.debug(elements)
    xc, yc, tables, titles, labels_grp, markers_grp = elements
    with visualization.quantity_support():
        plotter = EclipsePlotter(
            x=xc,
            yy=yc,
            tables=tables,
            titles=titles,
            legends_grp=labels_grp,
            markers_grp=markers_grp,
            changes=args.changes,
            percent=args.percent,
            linewidth=1 if args.lines else 0,
            nrows=1,
            ncols=1,
            save_path=args.save_figure_path,
            save_dpi=args.save_figure_dpi,
            # markers_type: EnumType = Marker
        )
        plotter.plot()


# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser):
    subparser = parser.add_subparsers(dest="command")
    parser_inv = subparser.add_parser(
        "inverse",
        parents=[
            prs.ifile(),
            prs.yc(),
            colname(),
            prs.save(),
        ],
        help="Calculates -log10(Y) of a given column number",
    )
    parser_inv.set_defaults(func=cli_inverse)

    parser_plot = subparser.add_parser(
        "plot",
        parents=[
            prs.ifiles(),
            prs.xlim(),
            prs.resample(),
            prs.lica(),
            prs.xc(),
            prs.yc(),
            prs.title(None, "plotting"),
            prs.labels("plotting"),
            prs.auxlines(),
            prs.percent(),
            prs.markers(),
            prs.linstyls(),
            prs.savefig(),
            prs.dpifig(),
        ],
        help="Plot Eclipse Glasses with limits",
    )
    parser_plot.set_defaults(func=cli_single_plot_tables_column)


# ================
# MAIN ENTRY POINT
# ================


def cli_main(args: Namespace) -> None:
    args.func(args)


def main():
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description="Specific eclipse glasses processing",
    )
