"""
This test module only test the Command Line Interface, with its various options.
The command output is written to a separate log file so that stdout is clean for unittest.

From the project base dir dir, run as:

    python -m unittest -v test.builder.TestSingle
    python -m unittest -v test.builder.TestMulti
    <etc>

or the complete suite:

    python -m unittest -v test.builder

"""

import os
import unittest
from shlex import split
from subprocess import run

import decouple
import astropy.units as u

from licaplot.utils.mpl.plotter.builder import SingleTableColumnBuilder


class TestSingle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        cls.dir = "data/filters/Omega_NPB"
        cls.path = os.path.join(cls.dir, "QEdata_filter_2nm.ecsv")
        # run(split(f"touch {cls.log}"))
        # run(split(f"truncate --size 0 {cls.log}"))

    def test_single_table_column(self):
        builder = SingleTableColumnBuilder(
            path=self.__class__.path,
            xcol=1 - 1,
            xunit=u.nm,
            ycol=4 - 1,
            yunit=u.dimensionless_unscaled,
            title="Omega Nebula Band Pass Filter",
            label=None,
            marker=None,
            columns=None,
            delimiter=None,
            xlow=None,
            xhigh=None,
            lunit=u.nm,
            resolution=None,
            lica_trim=None,
        )
        titles = builder.build_titles()
        self.assertEquals(titles, [[None]])

    def test_single_table_columns(self):
        self.assertTrue(False, "test case not written")

    def test_single_tables_column(self):
        self.assertTrue(False, "test case not written")

    def test_single_tables_columns(self):
        self.assertTrue(False, "test case not written")


class TestMultie(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        # run(split(f"touch {cls.log}"))
        # run(split(f"truncate --size 0 {cls.log}"))

    def test_multi_table_column(self):
        self.assertTrue(False, "test case not written")

    def test_multi_table_columns(self):
        self.assertTrue(False, "test case not written")

    def test_multi_tables_column(self):
        self.assertTrue(False, "test case not written")

    def test_multi_tables_columns(self):
        self.assertTrue(False, "test case not written")


if __name__ == "__main__":
    unittest.main()
