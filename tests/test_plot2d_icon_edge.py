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
