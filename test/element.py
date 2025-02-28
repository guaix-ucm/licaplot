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

from licaplot.utils.mpl.plotter.element import (
    Director,
    SingleTableColumnBuilder,
    SingleTableColumnsBuilder,
    SingleTablesColumnBuilder,
    SingleTablesColumnsBuilder,
    MultiTablesColumnBuilder,
    MultiTablesColumnsBuilder,
)

from licaplot.utils.mpl.plotter.table import (
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
            title=None,
            label=None,
            marker=None,
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
        self.assertEqual(labels_grp, [[None]])
        self.assertEqual(markers_grp, [[None]])

    def test_single_table_column_title_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            label=None,
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_title_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=["Eysdon", "RGB", "Filter", "set"],
            label=None,
            marker=None,
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
            title=None,
            label="label 1",
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(labels_grp, [["label 1"]])
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)

    def test_single_table_column_marker(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label=None,
            marker="o",
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(markers_grp, [["o"]])
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
            title=None,
            label=None,
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
            title=None,
            labels=None,
            markers=None,
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
        self.assertEqual(markers_grp, [[None, None]])

    def test_single_table_columns_title(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Title 1",
            labels=None,
            markers=None,
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
            title=None,
            labels=["label 1", "label 2"],
            markers=None,
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
            markers=None,
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
            title=None,
            labels=None,
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [[None, None]])

    def test_single_table_columns_markers_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
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
            labels=None,
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
            title=None,
            labels=None,
            markers=None,
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
            labels=None,
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_tables_column_labels(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            title=None,
            labels=["Azul", "Verde", "Rojo"],
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(labels_grp, [("Azul",), ("Verde",), ("Rojo",)])

    def test_single_tables_column_markers(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            title=None,
            labels=None,
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
            title=None,
            labels=None,
            markers=None,
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
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])

    def test_single_tables_columns_title(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            labels=None,
            markers=None,
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
            title=None,
            labels=None,
            markers=None,
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

    def test_single_tables_columns_labels(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title=None,
            labels=["Intens.", "Tran."],
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [tables[0].meta["title"]])
        self.assertEqual(
            labels_grp, [("Intens.", "Tran."), ("Intens.", "Tran."), ("Intens.", "Tran.")]
        )

    def test_single_tables_columns_markers(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title=None,
            labels=None,
            markers=["o", "-", "+"],
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "+")])


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
            titles=None,
            label=None,
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(labels_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [[None], [None], [None]])

    def test_multi_tables_column_title(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
            label=None,
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])
        self.assertEqual(labels_grp, [("Photod.",), ("Photod.",), ("Photod.",)])
        self.assertEqual(markers_grp, [[None], [None], [None]])

    def test_multi_tables_column_label(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=None,
            label="Intens.",
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [self.ycol - 1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(labels_grp, [("Intens.",), ("Intens.",), ("Intens.",)])
        self.assertEqual(markers_grp, [[None], [None], [None]])

    def test_multi_tables_column_marker(self):
        builder = MultiTablesColumnBuilder(
            builder=self.tb_builder,
            titles=None,
            label=None,
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
            titles=None,
            labels=None,
            markers=None,
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
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])

    def test_multi_tables_columns_titles(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=["Table 1", "Table 2", "Table 3"],
            labels=None,
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Table 1", "Table 2", "Table 3"])
        self.assertEqual(
            labels_grp, [("Electr.", "Photod."), ("Electr.", "Photod."), ("Electr.", "Photod.")]
        )
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])

    def test_multi_tables_columns_labels(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=None,
            labels=["Intens.", "Tran."],
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol - 1)
        self.assertEqual(yc, [y - 1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, [t.meta["title"] for t in tables])
        self.assertEqual(
            labels_grp, [("Intens.", "Tran."), ("Intens.", "Tran."), ("Intens.", "Tran.")]
        )
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])

    def test_multi_tables_columns_markers(self):
        builder = MultiTablesColumnsBuilder(
            builder=self.tb_builder,
            titles=None,
            labels=None,
            markers=["o", "-"],
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
        self.assertEqual(markers_grp, [("o", "-"), ("o", "-"), ("o", "-")])


if __name__ == "__main__":
    unittest.main()
