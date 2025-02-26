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
    SingleTableColumnBuilder,
    SingleTableColumnsBuilder,
    SingleTablesColumnBuilder,
    SingleTablesColumnsBuilder,
)

from licaplot.utils.mpl.plotter.table import (
    TableFromFile, TablesFromFiles,
)



class TestSingleTableColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        path = os.path.join("data", "filters", "Omega_NPB", "QEdata_filter_2nm.ecsv")
        cls.tb_builder = TableFromFile(
            path=path,
            delimiter=None,
            columns=None,
            xcol=1,
            xunit=u.nm,
            ycol=None,
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
            title="Omega Nebula Band Pass Filter",
            label=None,
            marker=None,
        )
        titles = builder.build_titles()
        self.assertEqual(titles, ["Omega Nebula Band Pass Filter"])

    def test_single_table_column_title_2(self):
        builder = SingleTableColumnBuilder(
            builder=self.tb_builder,
            title=["Omega", "Nebula", "Band", "Pass", "Filter"],
            label=None,
            marker=None,
        )
        titles = builder.build_titles()
        self.assertEqual(titles, ["Omega Nebula Band Pass Filter"])

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

    def test_single_tables_column_marker_1(self):
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

    def test_single_tables_column_marker_2(self):
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
            xunit=u.nm,
            ycol=None,
            yunit=u.dimensionless_unscaled,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )

    def test_single_table_column_labels_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
            ycols=[2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        titles = builder.build_titles()
        self.assertEqual(titles, ["Omega Nebula Band Pass Filter"])
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Electr.",)])

    def test_single_table_column_labels_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Wavele.", "Electr.")])

    def test_single_table_column_labels_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=("Foo", "Bar"),
            markers=None,
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        labels_grp = builder.build_legends_grp()
        self.assertEqual(labels_grp, [("Foo", "Bar")])

    def test_single_table_column_labels_4(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=("Foo", "Bar", "Baz"),
            markers=None,
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        with self.assertRaises(ValueError) as cm:
            _ = builder.build_legends_grp()
        msg = cm.exception.args[0]
        self.assertEqual(msg, 'number of labels (3) should match number of y-columns (2)')

    def test_single_table_column_markers_1(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=None,
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [[None, None]])

    def test_single_table_column_markers_2(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=("o", "."),
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        markers_grp = builder.build_markers_grp()
        self.assertEqual(markers_grp, [("o", ".")])

    def test_single_table_column_markers_3(self):
        builder = SingleTableColumnsBuilder(
            builder=self.tb_builder,           
            title="Omega Nebula Band Pass Filter",
            labels=None,
            markers=["o", "+", "."],
            ycols=[1, 2]
        )
        tables = builder.build_tables()
        self.assertEqual(len(tables), 1)
        with self.assertRaises(ValueError) as cm:
            _ = builder.build_markers_grp()
        msg = cm.exception.args[0]
        self.assertEqual(msg, 'number of markers (3) should match number of y-columns (2)')

if __name__ == "__main__":
    unittest.main()
