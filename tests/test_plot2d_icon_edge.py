"""Test module for the contour plot for the icon edge grid."""

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

import _base_testing as bt
from test_plot2d_icon import IconTestMixin
import test_plot2d as t2d


class IconEdgeSimplePlotterTest(IconTestMixin, t2d.Simple2DPlotterTest):
    """Icon edge grid test :class:`psy_simple.plotters.Simple2DPlotter` class
    """

    grid_type = "icon_edge"

    masking_val = 280

    ncfile = os.path.join(bt.test_dir, "icon_edge_test.nc")

    def test_bounds(self):
        """Test bounds formatoption"""
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(240, 310, 11, endpoint=True).tolist(),
        )
        self.update(bounds="minmax")
        bounds = [
            242.48,
            249.06,
            255.64,
            262.21,
            268.79,
            275.37,
            281.94,
            288.52,
            295.1,
            301.67,
            308.25,
        ]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(255, 305, 5, endpoint=True).tolist(),
        )
