"""
This test module only test the Command Line Interface, with its various options.
The command output is written to a separate log file so that stdout is clean for unittest.

From the project base dir dir, run as:

    python -m unittest -v test.builder.TestTableFromFile
    python -m unittest -v test.builder.TestTablesFromFile
    <etc>

or the complete suite:

    python -m unittest -v test.builder

"""

import os
import unittest
import astropy.units as u

from licatools.utils.mpl.plotter import TableFromFile, TablesFromFiles


class TestTableFromFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join("data", "filters", "Omega_NPB", "QEdata_filter_2nm.ecsv")


    def test_table_1(self):
        builder = TableFromFile(
            path=self.path,
            xcn=1,
            ycn=2,
            delimiter=None,
            columns=None,
            xlow=None,
            xhigh=None,
            xlunit=u.nm,
            resolution=5,
            lica_trim=None,
        )
        table, xc, yc = builder.build_tables()
        self.assertIsNotNone(table)


class TestTablesFromFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = (
            ("data", "filters", "Omega_NPB", "QEdata_diode_2nm.ecsv"),
            ("data", "filters", "Omega_NPB", "QEdata_filter_2nm.ecsv"),
        )
        cls.paths = [os.path.join(*path) for path in paths]

    def test_table_1(self):
        builder = TablesFromFiles(
            paths=self.paths,
            delimiter=None,
            columns=None,
            xcn=1,
            ycn=[1, 2],
            xlow=None,
            xhigh=None,
            xlunit=u.nm,
            resolution=None,
            lica_trim=None,
        )
        xc, yc, tables = builder.build_tables()
        self.assertEqual(len(tables), len(self.paths))
        for i in range(len(self.paths)):
            self.assertIsNotNone(tables[i])


if __name__ == "__main__":
    unittest.main()
