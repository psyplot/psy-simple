"""Test module for vector (quiver) plots with icon data."""

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import os

import _base_testing as bt
import numpy as np
import psyplot.project as psy
import test_vector as tv
from psyplot import ArrayList, open_dataset, rcParams
from test_plot2d_icon import IconTestMixin

from psy_simple.plotters import SimpleVectorPlotter


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
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries,
            np.linspace(0, 15, 11, endpoint=True),
            atol=1e-2,
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
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries, bounds, atol=1e-2
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries,
            np.linspace(0.5, 9.0, 5, endpoint=True),
            atol=1e-2,
        )
