"""
This test module only test the Command Line Interface, with its various options.
The command output is written to a separate log file so that stdout is clean for unittest.

From the project base dir dir, run as:

    python -m unittest -v test.builder.TestSingleTableColumn
    <etc>

or the complete suite:

    python -m unittest -v test.builder

"""

import os
import unittest


import astropy.units as u

from licatools.utils.mpl.plotter import (
    Director,
    SingleTableColumnBuilder,
    SingleTableColumnsBuilder,
    SingleTablesColumnBuilder,
    SingleTablesColumnsBuilder,
    MultiTablesColumnBuilder,
    MultiTablesColumnsBuilder,
    TableFromFile,
    TablesFromFiles,
)


# =============================================================================
#                                TEST CASE 1
# =============================================================================


class TestSingleTableColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        cls.path = os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv")
        cls.xcol = 1
        cls.ycol = 3
        cls.ntab = 1
        cls.tb_builder = TableFromFile(
            path=cls.path,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            ycol=cls.ycol,
            xunit=u.nm,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_table_column_default(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the table title.
        self.assertEqual(titles, ["Blue filter Measurements"])
        # Chooses the Y label
        self.assertEqual(ylabels, ["Photodiode Electrical Current"])
        # Table label +  Table column abbreviatted
        self.assertEqual(legends_grp, [(None,)])
        self.assertEqual(markers_grp, [(None,)])
        self.assertEqual(linestyl_grp, [(None,)])

    def test_single_table_column_title_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_title_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=["Eysdon", "RGB", "Filter", "set"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_ylabel_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            ylabel="Electrical Current",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Electrical Current"])

    def test_single_table_column_ylabel_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            ylabel=["Electrical", "Current"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Electrical Current"])
     

    def test_single_table_columns_label(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            legend="label 1",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(legends_grp, [("label 1",)])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_column_marker(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            marker="o",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o",)])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_column_linestyle(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            linestyle="-",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [("-",)])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_column_range_1(self):
        tb_builder = TableFromFile(
            path=self.path,
            delimiter=None,
            columns=None,
            xcol=1,
            ycol=8,
            xunit=u.nm,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )
        builder = SingleTableColumnBuilder(
            builder=tb_builder,
            marker="o",
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "Y column number (8) should be 1 <= Y <= (4)")


# =============================================================================
#                                TEST CASE 2
# =============================================================================


class TestSingleTableColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        cls.path = os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv")
        cls.xcol = 1
        cls.ycol = [2, 3]
        cls.ntab = 1
        cls.tb_builder = TableFromFile(
            path=cls.path,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            ycol=cls.ycol,
            xunit=u.nm,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_table_columns_default(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
        )

        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the table title.
        self.assertEqual(titles, ["Blue filter Measurements"])
        self.assertEqual(legends_grp, [("Electr.", "Photod.")])
        self.assertEqual(markers_grp, [(None, None)])
        self.assertEqual(linestyl_grp, [(None, None)])

    def test_single_table_columns_title(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Title 1",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Title 1"])

    def test_single_table_columns_ylabel(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            ylabel="Y-label 1",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Y-label 1"])

    def test_single_table_columns_legends_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            legends=["label 1", "label 2"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(legends_grp, [("label 1", "label 2")])

    def test_single_table_columns_legends_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            legends=("Foo", "Bar", "Baz"),
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of legends (3) should match number of y-columns (2)")

    def test_single_table_columns_markers_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [(None, None)])

    def test_single_table_columns_markers_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            markers=("o", "."),
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o", ".")])

    def test_single_table_columns_markers_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            markers=["o", "+", "."],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of markers (3) should match number of y-columns (2)")

    def test_single_table_columns_linestyles_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [(None, None)])

    def test_single_table_columns_linestyles_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            linestyles=(":", "-"),
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [(":", "-")])

    def test_single_table_columns_linestyles_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            linestyles=["o", "+", "."],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of linestyles (3) should match number of y-columns (2)")


# =============================================================================
#                                TEST CASE 3
# =============================================================================


class TestSingleTablesColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        paths = (
            os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "green.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "red.ecsv"),
        )
        cls.xcol = 1
        cls.ycol = 3
        cls.ntab = len(paths)
        cls.tb_builder = TablesFromFiles(
            paths=paths,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            xunit=u.nm,
            ycol=cls.ycol,
            yunit=u.A,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_tables_column_default(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Blue filter Measurements"])
        self.assertEqual(ylabels, ["Photodiode Electrical Current"])
        self.assertEqual(legends_grp, [("Blue",), ("Green",), ("Red",)])
        self.assertEqual(markers_grp, [(None,), (None,), (None,)])
        self.assertEqual(linestyl_grp, [(None,), (None,), (None,)])

    def test_single_tables_column_title(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_tables_column_ylabel(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            ylabel="Y-Label 1",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Y-Label 1"])

    def test_single_tables_column_legends_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            legends=["Verde"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(legends_grp, [("Verde",), ("Verde",), ("Verde",)])

    def test_single_tables_column_legends_2(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            legends=["Azul", "Verde"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg, "number of legends (2) should either match number of tables (3) or be 1"
        )

    def test_single_tables_column_legends_3(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            legends=["Azul", "Verde", "Rojo"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(legends_grp, [("Azul",), ("Verde",), ("Rojo",)])

    def test_single_tables_column_markers_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            markers=["+"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("+",), ("+",), ("+",)])

    def test_single_tables_column_markers_2(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            markers=["*", "-"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg, "number of markers (2) should either match number of tables (3) or be 1"
        )

    def test_single_tables_column_markers_3(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            markers=["*", "+", "-"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("*",), ("+",), ("-",)])

    def test_single_tables_column_linestyles_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            linestyles=[":"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [(":",), (":",), (":",)])

    def test_single_tables_column_linestyles_2(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            linestyles=[":", "-"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg, "number of linestyles (2) should either match number of tables (3) or be 1"
        )

    def test_single_tables_column_linestyles_3(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            linestyles=["-", "-.", ":"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [("-",), ("-.",), (":",)])


# =============================================================================
#                                TEST CASE 4
# =============================================================================


class TestSingleTablesColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        paths = (
            os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "green.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "red.ecsv"),
        )
        cls.xcol = 1
        cls.ycol = [2, 3]
        cls.ntab = len(paths)
        cls.tb_builder = TablesFromFiles(
            paths=paths,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            xunit=u.nm,
            ycol=cls.ycol,
            yunit=u.A,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_tables_columns_default(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the first title in the sequence of tables.
        self.assertEqual(titles, ["Blue filter Measurements"])
        self.assertEqual(ylabels, ["Electrical Current"])
        # Table label +  Table column abbreviatted
        self.assertEqual(
            legends_grp,
            [
                ("Blue-Electr.", "Blue-Photod."),
                ("Green-Electr.", "Green-Photod."),
                ("Red-Electr.", "Red-Photod."),
            ],
        )
        self.assertEqual(markers_grp, [(None, None), (None, None), (None, None)])

    def test_single_tables_columns_title(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_tables_columns_ylabel(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            ylabel="Y-Label 1",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Y-Label 1"])
        

    def test_single_tables_columns_label_trimm(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            legend_length=3,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Table label +  Table column abbreviatted
        self.assertEqual(
            legends_grp,
            [
                ("Blue-Ele.", "Blue-Pho."),
                ("Green-Ele.", "Green-Pho."),
                ("Red-Ele.", "Red-Pho."),
            ],
        )

    def test_single_tables_columns_legends_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            legends=["label_1", "label_2"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [tables[0].meta["title"]])
        self.assertEqual(
            legends_grp, [("label_1", "label_2"), ("label_1", "label_2"), ("label_1", "label_2")]
        )

    def test_single_tables_columns_legends_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            legends=["label_1", "label_2", "label_3"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg,
            "number of legends (3) should match number of tables x Y-columns (6) or the number of Y-columns (2)",
        )

    def test_single_tables_columns_legends_3(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            legends=["label_1", "label_2", "label_3", "label_4", "label_5", "label_6"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [tables[0].meta["title"]])
        self.assertEqual(
            legends_grp, [("label_1", "label_2"), ("label_3", "label_4"), ("label_5", "label_6")]
        )

    def test_single_tables_columns_markers_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "-"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "-")])

    def test_single_tables_columns_markers_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "+", "."],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg,
            "number of markers (3) should match number of tables x Y-columns (6) or the number of Y-columns (2)",
        )

    def test_single_tables_columns_markers_3(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "-", "+", ".", "v", "^"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("+", "."), ("v", "^")])

    def test_single_tables_columns_linestyles_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            linestyles=[":", "-."],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(linestyl_grp, [(":", "-."), (":", "-."), (":", "-.")])

    def test_single_tables_columns_linestyles_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            linestyles=[":", "-.", "--"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg,
            "number of linestyles (3) should match number of tables x Y-columns (6) or the number of Y-columns (2)",
        )

    def test_single_tables_columns_linestyles_3(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            linestyles=[":", "-.", "--", ".", "v", "^"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(linestyl_grp, [(":", "-."), ("--", "."), ("v", "^")])

# =============================================================================
#                                TEST CASE 5
# =============================================================================


class TestMultiTablesColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        paths = (
            os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "green.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "red.ecsv"),
        )
        cls.xcol = 1
        cls.ycol = 3
        cls.ntab = len(paths)
        cls.tb_builder = TablesFromFiles(
            paths=paths,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            xunit=u.nm,
            ycol=cls.ycol,
            yunit=u.A,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_multi_tables_column_default(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(ylabels, [t.columns[self.ycol-1].name for t in tables])
        self.assertEqual(legends_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [(None,), (None,), (None,)])
        self.assertEqual(linestyl_grp, [(None,), (None,), (None,)])

    def test_multi_tables_column_title_1(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])
      

    def test_multi_tables_column_title_2(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of titles (2) should match number of tables (3)")

    def test_multi_tables_column_ylabel_1(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            ylabels=["Y-label 1", "Y-label 2", "Y-label 3"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Y-label 1", "Y-label 2", "Y-label 3"])
      

    def test_multi_tables_column_ylabel_2(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            ylabels=["Y-label 1", "Y-label 2"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of Y labels (2) should match number of tables (3)")

    def test_multi_tables_column_label(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            legend="Intens.",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(legends_grp, [("Intens.",), ("Intens.",), ("Intens.",)])

    def test_multi_tables_column_marker(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            marker="o",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o",), ("o",), ("o",)])

    def test_multi_tables_column_linestyle(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            linestyle=":",
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [(":",), (":",), (":",)])


# =============================================================================
#                                TEST CASE 6
# =============================================================================


class TestMultiTablesColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        paths = (
            os.path.join("data", "filters", "Eysdon_RGB", "blue.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "green.ecsv"),
            os.path.join("data", "filters", "Eysdon_RGB", "red.ecsv"),
        )
        cls.xcol = 1
        cls.ycol = [2, 3]
        cls.ntab = len(paths)
        cls.tb_builder = TablesFromFiles(
            paths=paths,
            delimiter=None,
            columns=None,
            xcol=cls.xcol,
            xunit=u.nm,
            ycol=cls.ycol,
            yunit=u.A,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_multi_tables_columns_default(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
        )
        director = Director(builder)

        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(ylabels, [t.columns[self.ycol[0]-1].name for t in tables])
        self.assertEqual(
            legends_grp, [("Electr.", "Photod."), ("Electr.", "Photod."), ("Electr.", "Photod.")]
        )
        self.assertEqual(markers_grp, [(None, None), (None, None), (None, None)])
        self.assertEqual(linestyl_grp, [(None, None), (None, None), (None, None)])

    def test_multi_tables_columns_titles_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])

    def test_multi_tables_columns_titles_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of titles (2) should match number of tables (3)")

    def test_multi_tables_columns_ylabels_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            ylabels=["Y-label 1", "Y-label 2", "Y-label 3"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(ylabels, ["Y-label 1", "Y-label 2", "Y-label 3"])

    def test_multi_tables_columns_ylabels_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            ylabels=["Y-label 1", "Y-label 2"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of Y labels (2) should match number of tables (3)")

    def test_multi_tables_columns_legends_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            legends=["Intens.", "Tran."],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(
            legends_grp, [("Intens.", "Tran."), ("Intens.", "Tran."), ("Intens.", "Tran.")]
        )

    def test_multi_tables_columns_legends_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            legends=["label_1"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of legends (1) should match number of y-columns (2)")

    def test_multi_tables_columns_markers_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "-"],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "-")])

    def test_multi_tables_columns_markers_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of markers (1) should match number of y-columns (2)")

    def test_multi_tables_columns_linestyles_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            linestyles=[":", "-."],
        )
        director = Director(builder)
        xc, yc, tables, titles, ylabels, legends_grp, markers_grp, linestyl_grp = director.build_elements()
        self.assertEqual(linestyl_grp, [(":", "-."), (":", "-."), (":", "-.")])

    def test_multi_tables_columns_linestyles_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            linestyles=[":"],
        )
        director = Director(builder)
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of linestyles (1) should match number of y-columns (2)")


if __name__ == "__main__":
    unittest.main()
