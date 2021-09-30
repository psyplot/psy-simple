import os

import numpy as np
import matplotlib.pyplot as plt

from psyplot import InteractiveList

import _base_testing as bt
import test_base as tb
import test_plot2d as t2d

bold = tb.bold


class IconTestMixin(object):
    """A mixin class for changed test methods for icon"""

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

    def test_xlabel(self):
        """Test xlabel formatoption"""
        self.update(xlabel="{desc}")
        label = self.plotter.ax.xaxis.get_label()
        self.assertIn("longitude [radian]", label.get_text())
        self.update(
            labelsize=22, labelweight="bold", labelprops={"ha": "left"}
        )
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), "left")

    def test_ylabel(self):
        """Test ylabel formatoption"""
        self.update(ylabel="{desc}")
        label = self.plotter.ax.yaxis.get_label()
        self.assertIn("latitude [radian]", label.get_text())
        self.update(
            labelsize=22, labelweight="bold", labelprops={"ha": "left"}
        )
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), "left")

    def _test_DataTicksCalculator(self):
        # testing of psy_simple.plotters.DataTicksCalculator

        ax = plt.gca()
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data

        try:
            lon = data.clon.values
        except AttributeError:
            lon = data.elon.values

        self.update(xticks="rounded")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-3, 3.5, 11, endpoint=True).tolist(),
        )
        self.update(xticks="roundedsym")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-3.5, 3.5, 10, endpoint=True).tolist(),
        )
        self.update(xticks="minmax")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(lon.min(), lon.max(), 11, endpoint=True).tolist(),
        )
        self.update(xticks="sym")
        vmax = np.abs(lon).max()
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-vmax, vmax, 10, endpoint=True).tolist(),
        )


class IconSimplePlotterTest(IconTestMixin, t2d.Simple2DPlotterTest):
    """Test :class:`psy_simple.plotters.Simple2DPlotter` class for icon grid"""

    grid_type = "icon"

    masking_val = 280

    ncfile = os.path.join(bt.test_dir, "icon_test.nc")

    def test_bounds(self):
        """Test bounds formatoption"""
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

