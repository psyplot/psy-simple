"""Test module for vector (quiver) plots."""

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

from psyplot import rcParams, open_dataset, ArrayList
from psy_simple.plotters import SimpleVectorPlotter
import psyplot.project as psy

import _base_testing as bt
import test_plot2d as t2d


class SimpleVectorPlotterTest(t2d.Simple2DPlotterTest):
    """Test :class:`psyplot.plotter.maps.SimpleVectorPlotter` class"""

    plot_type = "simplevector"

    var = ["u", "v"]

    def plot(self, **kwargs):
        kwargs.setdefault("color", "absolute")
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault("t", ds.time.values[0])
        kwargs.setdefault("z", ds.lev.values[0])
        kwargs.setdefault("x", slice(0, 69.0))
        kwargs.setdefault("y", slice(81.0, 34.0))
        kwargs.setdefault("method", "sel")
        sp = psy.plot.vector(ds, name=[self.var], **kwargs)
        return sp

    @unittest.skip("miss_color formatoption not implemented")
    def ref_miss_color(self, close=True):
        pass

    def ref_arrowsize(self, close=True):
        """Create reference file for arrowsize formatoption.

        Create reference file for
        :attr:`~psyplot.plotter.maps.VectorPlotter.arrowsize` (and others)
        formatoption"""
        sp = self.plot(arrowsize=100.0)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("arrowsize")))
        if close:
            sp.close(True, True)

    def ref_datagrid(self, close=True):
        """Create reference file for datagrid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.datagrid`
        formatoption"""
        sp = self.plot()
        sp.update(datagrid="k-")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("datagrid")))
        if close:
            sp.close(True, True)

    def test_datagrid(self, *args):
        """Test datagrid formatoption"""
        self.update(datagrid="k-")
        self.compare_figures(next(iter(args), self.get_ref_file("datagrid")))

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True
        )[0]
        cls.data = cls.data.psy.sel(lon=slice(0, 69.0), lat=slice(81.0, 34.0))
        cls.data.attrs["long_name"] = "absolute wind speed"
        cls.data.name = "wind"
        plotter = SimpleVectorPlotter()
        rcParams[plotter.color.default_key] = "absolute"
        cls.plotter = SimpleVectorPlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups["colors"]

    def update(self, *args, **kwargs):
        kwargs.setdefault("color", "absolute")
        super(SimpleVectorPlotterTest, self).update(*args, **kwargs)

    @unittest.skip("Not supported")
    def test_maskless(self):
        pass

    @unittest.skip("Not supported")
    def test_maskgreater(self):
        pass

    @unittest.skip("Not supported")
    def test_maskleq(self):
        pass

    @unittest.skip("Not supported")
    def test_maskgeq(self):
        pass

    @unittest.skip("Not supported")
    def test_maskbetween(self):
        pass

    @unittest.skip("Not supported")
    def test_miss_color(self):
        pass

    def test_cbarspacing(self, *args):
        """Test cbarspacing formatoption"""
        self.update(
            cbarspacing="proportional",
            cticks="rounded",
            color="absolute",
            bounds=np.arange(0, 1.45, 0.1).tolist()
            + np.linspace(1.5, 13.5, 7, endpoint=True).tolist()
            + np.arange(13.6, 15.05, 0.1).tolist(),
        )
        self.compare_figures(
            next(iter(args), self.get_ref_file("cbarspacing"))
        )

    def test_arrowsize(self, *args):
        """Test arrowsize formatoption"""
        self.update(arrowsize=100.0)
        self.compare_figures(next(iter(args), self.get_ref_file("arrowsize")))

    _max_rounded_ref = 70

    @property
    def _minmax_cticks(self):
        speed = (
            self.plotter.plot_data.values[0] ** 2
            + self.plotter.plot_data.values[1] ** 2
        ) ** 0.5
        speed = speed[~np.isnan(speed)]
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True),
            decimals=2,
        ).tolist()

    def test_bounds(self):
        """Test bounds formatoption"""
        self.update(color="absolute")
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist(),
        )
        self.update(bounds="minmax")
        bounds = [
            0.36,
            1.4,
            2.45,
            3.49,
            4.54,
            5.59,
            6.63,
            7.68,
            8.72,
            9.77,
            10.81,
        ]

        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 3).tolist(),
            np.linspace(1.0, 8.5, 5, endpoint=True).tolist(),
        )
