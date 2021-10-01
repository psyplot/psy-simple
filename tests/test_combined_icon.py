"""Test module for the combined simple plotter for the icon grid."""

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

from psyplot import ArrayList, open_dataset, rcParams
from psy_simple.plotters import CombinedSimplePlotter
import psyplot.project as psy

import _base_testing as bt
from test_plot2d_icon import IconTestMixin
import test_combined as tc


class IconCombinedSimplePlotterTest(
    IconTestMixin, tc.CombinedSimplePlotterTest
):
    """Test :class:`psy_simple.plotters.CombinedSimplePlotter` class for icon
    grid
    """

    grid_type = "icon"

    ncfile = os.path.join(bt.test_dir, "icon_test.nc")

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        plotter = CombinedSimplePlotter()
        rcParams[plotter.vcmap.default_key] = "winter"
        cls._data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True, prefer_list=True
        )[0]
        cls._data.attrs["long_name"] = "Temperature"
        cls._data.attrs["name"] = "t2m"
        cls.plotter = CombinedSimplePlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups["colors"]

        # there is an issue with the colorbar that the size of the axes changes
        # slightly after replotting. Therefore we force a replot here
        cls.plotter.update(color="absolute")
        cls.plotter.update(todefault=True, replot=True)

    def plot(self, **kwargs):
        color_fmts = psy.plot.vector.plotter_cls().fmt_groups["colors"]
        fix_colorbar = not color_fmts.intersection(kwargs)
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault("color", "absolute")
        if self.vector_mode:
            kwargs = self._rename_fmts(kwargs)
        sp = psy.plot.combined(ds, name=[self.var], **kwargs)
        if not self.vector_mode or fix_colorbar:
            # if we have no color formatoptions, we have to consider that
            # the position of the plot may have slighty changed
            sp.update(
                todefault=True,
                replot=True,
                **dict(item for item in kwargs.items() if item[0] != "color")
            )
        return sp

    @unittest.skip(
        "Density for quiver plots of unstructered data is not " "supported!"
    )
    def ref_density(self):
        pass

    @unittest.skip(
        "Density for quiver plots of unstructered data is not " "supported!"
    )
    def test_density(self):
        pass

    def test_bounds(self):
        """Test bounds formatoption"""
        # test bounds of scalar field
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(240, 310, 11, endpoint=True).tolist(),
        )
        self.update(bounds="minmax")
        bounds = [
            243.76,
            250.04,
            256.31,
            262.58,
            268.85,
            275.12,
            281.39,
            287.66,
            293.94,
            300.21,
            306.48,
        ]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(255, 305, 5, endpoint=True).tolist(),
        )

        # test vector bounds
        self.update(color="absolute")
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist(),
        )
        self.update(vbounds="minmax")
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
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(vbounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.round(np.linspace(0.5, 9.0, 5, endpoint=True), 2).tolist(),
        )

    @property
    def _minmax_cticks(self):
        if not self.vector_mode:
            arr = self.plotter.plot_data[0].values
            arr = arr[~np.isnan(arr)]
            return np.round(
                np.linspace(arr.min(), arr.max(), 11, endpoint=True), decimals=2
            ).tolist()
        arr = self.plotter.plot_data[1].values
        speed = (arr[0] ** 2 + arr[1] ** 2) ** 0.5
        speed = speed[~np.isnan(speed)]
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True), decimals=2
        ).tolist()

