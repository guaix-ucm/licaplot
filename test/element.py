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
        cls.path = os.path.join("data", "filters", "Omega_NPB", "QEdata_filter_2nm.ecsv")
        cls.tb_builder = TableFromFile(
            path=cls.path,
            delimiter=None,
            columns=None,
            xcol=1,
            ycol=2,
            xunit=u.nm,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_table_column_title_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            label=None,
            marker=None,
        )
        titles = builder.build_titles()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_title_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=["Eysdon", "RGB", "Filter", "set"],
            label=None,
            marker=None,
        )
        titles = builder.build_titles()
        self.assertEqual(titles, ["Eysdon RGB Filter set"])

    def test_single_table_column_title_3(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label=None,
            marker=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        titles = builder.build_titles()
        self.assertEqual(titles, [tables[0].meta["title"]])

    def test_single_table_column_label_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label=None,
            marker=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [[None]])

    def test_single_table_columns_label_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label="label 1",
            marker=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [["label 1"]])

    def test_single_table_column_marker_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label=None,
            marker=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [[None]])

    def test_single_table_column_marker_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=None,
            label=None,
            marker="o",
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [["o"]])

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
        with self.assertRaises(ValueError) as cm:
            _ = builder.build_tables()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "Y column number (8) should be 1 <= Y <= (4)")

    def test_single_table_column_all_1(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            label=None,
            marker=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        print(labels_grp)
        self.assertEqual(xc, 0)
        self.assertEqual(yc, [1])
        self.assertEqual(len(tables), 1)
        self.assertEqual(titles, ["Eysdon RGB Filter set"])
        self.assertEqual(labels_grp, [[None]])
        self.assertEqual(markers_grp, [[None]])


# =============================================================================
#                                TEST CASE 2
# =============================================================================


class TestSingleTableColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        path = os.path.join("data", "filters", "Omega_NPB", "QEdata_filter_2nm.ecsv")
        cls.tb_builder = TableFromFile(
            path=path,
            delimiter=None,
            columns=None,
            xcol=1,
            ycol=[1, 2],
            xunit=u.nm,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_table_columns_labels_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        titles = builder.build_titles()
        self.assertEqual(titles, ["Omega Nebula Band Pass Filter"])
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Wavele.", "Electr.")])

    def test_single_table_columns_labels_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Wavele.", "Electr.")])

    def test_single_table_columns_labels_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=("Foo", "Bar"),
            markers=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Foo", "Bar")])

    def test_single_table_columns_labels_4(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=("Foo", "Bar", "Baz"),
            markers=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        with self.assertRaises(ValueError) as cm:
            _ = builder.build_legends_grp()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of labels (3) should match number of y-columns (2)")

    def test_single_table_columns_markers_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [[None, None]])

    def test_single_table_columns_markers_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=("o", "."),
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [("o", ".")])

    def test_single_table_columns_markers_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=["o", "+", "."],
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        with self.assertRaises(ValueError) as cm:
            _ = builder.build_markers_grp()
        msg = cm.exception.args[0]
        self.assertEqual(msg, "number of markers (3) should match number of y-columns (2)")

    def test_single_table_columns_director_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=("o", "."),
        )
        director = Director()
        director.builder = builder
        xc, yycc, tables, titles, legends_grp, markers_grp = director.build_elements()
        self.assertEqual(markers_grp, [("o", ".")])

    def test_single_table_columns_director_2(self):
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

    def test_single_tables_column_all_1(self):
        builder = SingleTablesColumnBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            labels=None,
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol-1)
        self.assertEqual(yc, [self.ycol-1])
        self.assertEqual(len(tables), self.ntab)
        self.assertEqual(titles, ["Eysdon RGB Filter set"])
        self.assertEqual(labels_grp, [("Blue",), ("Green",), ("Red",)])
        self.assertEqual(markers_grp, [[None], [None], [None]])


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
        cls.xcol=1
        cls.ycol=[2,3]
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

    def test_single_tables_columns_all_1(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            labels=None,
            markers=None,
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()

        self.assertEqual(xc, self.xcol-1)
        self.assertEqual(yc, [y-1 for y in self.ycol])
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
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])

    def test_single_tables_columns_all_2(self):
        builder = SingleTablesColumnsBuilder(
            builder=self.tb_builder,
            title="Eysdon RGB Filter set",
            labels=None,
            markers=None,
            label_length=3
        )
        director = Director()
        director.builder = builder
        xc, yc, tables, titles, labels_grp, markers_grp = director.build_elements()
        self.assertEqual(xc, self.xcol-1)
        self.assertEqual(yc, [y-1 for y in self.ycol])
        self.assertEqual(len(tables), self.ntab)

        self.assertEqual(titles, ["Eysdon RGB Filter set"])
        # Table label +  Tablle collumn abbreviatted
        self.assertEqual(
            labels_grp,
            [
                ("Blue-Ele.", "Blue-Pho."),
                ("Green-Ele.", "Green-Pho."),
                ("Red-Ele.", "Red-Pho."),
            ],
        )
        self.assertEqual(markers_grp, [[None, None], [None, None], [None, None]])


if __name__ == "__main__":
    unittest.main()
