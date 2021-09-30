"""Test module of the :mod:`psy_simple.plotters` module"""
import unittest

from psy_simple.plotters import LinePlotter

import psyplot.project as psy

import test_lineplot as tl
from psyplot import InteractiveList, open_dataset


class SingleLinePlotterTest(tl.LinePlotterTest):
    """Test of :class:`psy_simple.plotters.LinePlotter` with a single array
    instead of an InteractiveList"""

    plot_type = "singleline"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True
        )
        cls.data[0].psy.arr_name = "arr0"
        cls.data.psy.arr_name = "arr0"
        cls.plotter = LinePlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.lineplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs
        )

    @unittest.skip("No need for figure creation")
    def ref_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("Appending not possible for single line")
    def test_append_data(self):
        pass
