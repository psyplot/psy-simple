"""Test module of the :mod:`psy_simple.plotters` module"""
import unittest

from psy_simple.plotters import ViolinPlotter

import psyplot.project as psy
from psyplot import InteractiveList, open_dataset

import test_lineplot as tl


class ViolinPlotterTest(tl.LinePlotterTest):
    """Test class for :class:`psy_simple.plotters.BarPlotter`"""

    plot_type = "violin"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True
        )
        cls.plotter = ViolinPlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.violinplot(
            self.ncfile, name=name, t=0, z=0, y=[0, 1], **kwargs
        )

    @unittest.skip("No need for figure creation")
    def ref_xticks(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_area(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_areax(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_stacked(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_stacked_transposed(self, close=True):
        pass

    @unittest.skip("seaborn changes colors")
    def test_append_data(self):
        pass

    @unittest.skip("Test needs to be implemented")
    def test_xticks(self, *args):
        """
        .. todo::

            Implement this test"""
        # TODO: implement this test
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_area(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_areax(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked_transposed(self, close=True):
        pass

    def test_color(self):
        pass

    @unittest.skip("Not implemented for ViolinPlotter")
    def test_coord(self):
        pass
