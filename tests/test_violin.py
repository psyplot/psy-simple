"""Test module of the :mod:`psy_simple.plotters` module."""

# Disclaimer
# ----------
#
# Copyright (C) 2021 Helmholtz-Zentrum Hereon
# Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
# Copyright (C) 2016-2021 University of Lausanne
#
# This file is part of psy-simple and is released under the GNU LGPL-3.O license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LGPL-3.0 license for more details.
#
# You should have received a copy of the GNU LGPL-3.0 license
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
