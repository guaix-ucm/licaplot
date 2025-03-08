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

# ---------------------
# Third-party libraries
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

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

plt.rcParams["legend.fontsize"] = "12"


UVA_RANGE = (430, 400)
VIS_RANGE = (380, 780)
IR_RANGE = (780, 1040)

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
    default_linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]

    def plot_start_hook(self):
        linestyles = itertools.cycle(self.default_linestyles)
        self.linestyles_grp = list(map(lambda x: (next(linestyles),), self.linestyles_grp))

    def outer_loop_start_hook(self, single_plot: bool, first_pass: bool):
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

    def outer_loop_end_hook(self, single_plot: bool, first_pass: bool):
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=5, frameon=True)

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
    inverse(table, args.y_column - 1, args.column_name)
    if args.save:
        table.write(path, delimiter=",", overwrite=True)


def cli_single_plot_tables_column(args: Namespace):
    tb_builder = TablesFromFiles(
        paths=args.input_file,
        delimiter=args.delimiter,
        columns=args.columns,
        xcol=args.x_column,
        ycol=args.y_column,
        xlow=args.x_low,
        xhigh=args.x_high,
        xlunit=args.x_limits_unit,
        resolution=args.resample,
        lica_trim=args.lica,
    )
    builder = SingleTablesColumnBuilder(
        builder=tb_builder,
        title=args.title,
        xlabel=args.x_label,
        ylabel=args.y_label,
        legends=args.labels,
        markers=args.markers,
        linestyles=args.line_styles,
    )
    director = Director(builder)
    elements = director.build_elements()
    log.debug(elements)
    xc, yc_grp, tables, titles, xlabels, ylabels, legends_grp, markers_grp, linestyles_grp = elements
    with visualization.quantity_support():
        plotter = EclipsePlotter(
            x=xc,
            yc_grp=yc_grp,
            tables=tables,
            titles=titles,
            xlabels=xlabels,
            ylabels=ylabels,
            legends_grp=legends_grp,
            markers_grp=markers_grp,
            linestyles_grp=linestyles_grp,
            changes=args.changes,
            percent=args.percent,
            linewidth=1 if args.lines else 0,
            nrows=1,
            ncols=1,
            save_path=args.save_figure_path,
            save_dpi=args.save_figure_dpi,
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
            prs.xlabel(),
            prs.ylabel(),
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
