"""Test module for vector (quiver) plots with icon data."""

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

import numpy as np

from psyplot import rcParams, ArrayList, open_dataset
from psy_simple.plotters import SimpleVectorPlotter
import psyplot.project as psy

import _base_testing as bt
from test_plot2d_icon import IconTestMixin
import test_vector as tv


class IconSimpleVectorPlotterTest(IconTestMixin, tv.SimpleVectorPlotterTest):
    """
    Test :class:`psy_simple.plotters.SimpleVectorPlotter` class for icon grid
    """

    grid_type = "icon"

    ncfile = os.path.join(bt.test_dir, "icon_test.nc")

    @classmethod
    def setUpClass(cls):
        plotter = SimpleVectorPlotter()
        rcParams[plotter.color.default_key] = "absolute"
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True
        )[0]
        cls.data.attrs["long_name"] = "absolute wind speed"
        cls.data.name = "wind"
        cls.plotter = SimpleVectorPlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups["colors"]

    def plot(self, **kwargs):
        kwargs.setdefault("color", "absolute")
        ds = psy.open_dataset(self.ncfile)
        sp = psy.plot.vector(ds, name=[self.var], **kwargs)
        return sp

    def test_bounds(self):
        """Test bounds formatoption"""
        self.update(color="absolute")
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist(),
        )
        self.update(bounds="minmax")
        bounds = [
            0.08,
            1.18,
            2.28,
            3.38,
            4.48,
            5.59,
            6.69,
            7.79,
            8.89,
            9.99,
            11.09,
        ]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.round(np.linspace(0.5, 9.0, 5, endpoint=True), 2).tolist(),
        )

