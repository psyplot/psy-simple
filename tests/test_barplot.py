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

import os
import unittest
import numpy as np
import matplotlib.colors as mcol

from psyplot import InteractiveList, open_dataset
from psy_simple.plotters import BarPlotter
import psyplot.project as psy

import _base_testing as bt
import test_lineplot as tl


class BarPlotterTest(tl.LinePlotterTest):
    """Test class for :class:`psy_simple.plotters.BarPlotter`"""

    plot_type = "bar"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True
        )
        cls.plotter = BarPlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.barplot(
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

    def ref_plot(self, close=True):
        """Create the reference figure for the stacked plot"""
        sp = self.plot(plot="stacked")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("stacked")))
        sp2 = self.plot(plot="stacked", transpose=True)
        sp2.export(
            os.path.join(bt.ref_dir, self.get_ref_file("stacked_transposed"))
        )
        if close:
            sp.close(True, True, True)
            sp2.close(True, True, True)

    def test_plot(self, *args):
        """Test the stacked plot"""
        self.update(plot="stacked")
        self.compare_figures(next(iter(args), self.get_ref_file("stacked")))
        self.update(plot="stacked", transpose=True)
        self.compare_figures(
            next(iter(args), self.get_ref_file("stacked_transposed"))
        )

    def test_xticks(self, *args):
        self._test_DtTicksBase()

    def _test_DtTicksBase(self, *args):
        data = InteractiveList.from_dataset(
            self.data[0].psy.base,
            y=[0, 1],
            z=0,
            x=0,
            name=self.var,
            auto_update=True,
        )
        plotter = self.plotter.__class__(data)
        ax = plotter.ax
        plotter.update(xticklabels="%m")
        self.assertListEqual(
            ax.get_xticks().astype(int).tolist(), list(range(5))
        )

    def test_color(self):
        colors = ["y", "g"][: len(self.data)]
        current_colors = [
            c[0].get_facecolor() for c in self.plotter.ax.containers
        ]
        self.update(color=colors)

        self.assertEqual(
            [c[0].get_facecolor() for c in self.plotter.ax.containers],
            list(map(mcol.colorConverter.to_rgba, colors)),
        )
        self.update(color=None)
        self.assertEqual(
            [c[0].get_facecolor() for c in self.plotter.ax.containers],
            current_colors,
        )

    def test_ylim(self):
        """Test ylim formatoption"""
        curr_lim = self.plotter.ax.get_ylim()
        self.update(ylim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, 300))
        self.update(ylim=(-1, "rounded"))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, curr_lim[1]))
        self.update(ylim=(0, ["minmax", 75]))
        data = self.data.to_dataframe()
        arr = data[data.notnull()].values
        self.assertAlmostArrayEqual(
            self.plotter.ax.get_ylim(), [0, np.percentile(arr, 75)]
        )
