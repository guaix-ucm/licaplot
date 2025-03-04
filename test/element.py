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

from licaplot.utils.mpl.plotter import (
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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the table title.
        self.assertEqual(titles, ["Blue filter Measurements"])
        # Table label +  Tablle collumn abbreviatted
        self.assertEqual(labels_grp, [(None,)])
        self.assertEqual(markers_grp, [(None,)])

    def test_single_table_column_title_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_title_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=["Eysdon", "RGB", "Filter", "set"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_columns_label(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            label="label 1",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(labels_grp, [("label 1",)])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_column_marker(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            marker="o",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o",)])
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
        director = Director()
        director.builder = builder
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

        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the table title.
        self.assertEqual(titles, ["Blue filter Measurements"])
        self.assertEqual(labels_grp, [("Electr.", "Photod.")])
        self.assertEqual(markers_grp, [(None, None)])

    def test_single_table_columns_title(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Title 1",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Title 1"])

    def test_single_table_columns_labels_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            labels=["label 1", "label 2"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(labels_grp, [("label 1", "label 2")])

    def test_single_table_columns_labels_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=("Foo", "Bar", "Baz"),
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of labels (3) should match number of y-columns (2)")

    def test_single_table_columns_markers_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [(None, None)])

    def test_single_table_columns_markers_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            markers=("o", "."),
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", ".")])

    def test_single_table_columns_markers_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            markers=["o", "+", "."],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of markers (3) should match number of y-columns (2)")


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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Blue filter Measurements"])
        self.assertEqual(labels_grp, [("Blue",), ("Green",), ("Red",)])
        self.assertEqual(markers_grp, [(None,), (None,), (None,)])

    def test_single_tables_column_title(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_tables_column_labels_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            labels=["Verde"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(labels_grp, [("Verde",), ("Verde",), ("Verde",)])

    def test_single_tables_column_labels_2(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            labels=["Azul", "Verde"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg, "number of labels (2) should either match number of tables (3) or be 1"
        )

    def test_single_tables_column_labels_3(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            labels=["Azul", "Verde", "Rojo"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(labels_grp, [("Azul",), ("Verde",), ("Rojo",)])

    def test_single_tables_column_markers_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            markers=["+"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("+",), ("+",), ("+",)])

    def test_single_tables_column_markers_2(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            markers=["*", "-"],
        )
        director = Director()
        director.builder = builder
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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("*",), ("+",), ("-",)])


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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()

        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Chooses the first title in the sequence of tables.
        self.assertEqual(titles, ["Blue filter Measurements"])
        # Table label +  Tablle collumn abbreviatted
        self.assertEqual(
            labels_grp,
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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()

        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Eysdon RGB Filter set"])
        # Table label +  Tablle collumn abbreviatted
        self.assertEqual(
            labels_grp,
            [
                ("Blue-Electr.", "Blue-Photod."),
                ("Green-Electr.", "Green-Photod."),
                ("Red-Electr.", "Red-Photod."),
            ],
        )

    def test_single_tables_columns_label_trimm(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            label_length=3,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        # Table label +  Tablle collumn abbreviatted
        self.assertEqual(
            labels_grp,
            [
                ("Blue-Ele.", "Blue-Pho."),
                ("Green-Ele.", "Green-Pho."),
                ("Red-Ele.", "Red-Pho."),
            ],
        )

    def test_single_tables_columns_labels_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            labels=["label_1", "label_2"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [tables[0].meta["title"]])
        self.assertEqual(
            labels_grp, [("label_1", "label_2"), ("label_1", "label_2"), ("label_1", "label_2")]
        )

    def test_single_tables_columns_labels_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            labels=["label_1", "label_2", "label_3"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(
            msg,
            "number of legends (3) should match number of tables x Y-columns (6) or the number of Y-columns (2)",
        )

    def test_single_tables_columns_labels_3(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            labels=["label_1", "label_2", "label_3", "label_4", "label_5", "label_6"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [tables[0].meta["title"]])
        self.assertEqual(
            labels_grp, [("label_1", "label_2"), ("label_3", "label_4"), ("label_5", "label_6")]
        )

    def test_single_tables_columns_markers_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "-"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "-")])

    def test_single_tables_columns_markers_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "+", "."],
        )
        director = Director()
        director.builder = builder
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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("+", "."), ("v", "^")])


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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(labels_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [(None,), (None,), (None,)])

    def test_multi_tables_column_title_1(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])
        self.assertEqual(labels_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [(None,), (None,), (None,)])

    def test_multi_tables_column_title_2(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of titles (2) should match number of tables (3)")

    def test_multi_tables_column_label(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            label="Intens.",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(labels_grp, [("Intens.",), ("Intens.",), ("Intens.",)])

    def test_multi_tables_column_marker(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            marker="o",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(labels_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [("o",), ("o",), ("o",)])


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
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(
            labels_grp, [("Electr.", "Photod."), ("Electr.", "Photod."), ("Electr.", "Photod.")]
        )
        self.assertEqual(markers_grp, [(None, None), (None, None), (None, None)])

    def test_multi_tables_columns_titles_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])

    def test_multi_tables_columns_titles_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of titles (2) should match number of tables (3)")

    def test_multi_tables_columns_labels_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            labels=["Intens.", "Tran."],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(
            labels_grp, [("Intens.", "Tran."), ("Intens.", "Tran."), ("Intens.", "Tran.")]
        )

    def test_multi_tables_columns_labels_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            labels=["label_1"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of legends (1) should match number of y-columns (2)")

    def test_multi_tables_columns_markers_1(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o", "-"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "-")])

    def test_multi_tables_columns_markers_2(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            markers=["o"],
        )
        director = Director()
        director.builder = builder
        with self.assertRaises(ValueError) as cm:
            _ = director.build_elements()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of markers (1) should match number of y-columns (2)")


if __name__ == "__main__":
    unittest.main()
