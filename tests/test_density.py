"""Test module for the density plotter."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import _base_testing as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from psy_simple.plotters import DensityPlotter


class DensityPlotterTest(bt.PsyPlotTestCase):
    """Test of the :class:`psy_simple.plotters.DensityPlotter` class"""

    @classmethod
    def setUpClass(cls):
        cls.data = cls.define_data()
        cls.plotter = DensityPlotter(cls.data)

    @classmethod
    def tearDownClass(cls):
        super(DensityPlotterTest, cls).tearDownClass()
        del cls.data
        plt.close(cls.plotter.ax.get_figure().number)

    def tearDown(self):
        self.plotter.update(todefault=True)

    @classmethod
    def update(cls, **kwargs):
        """Update the plotter of this test case"""
        cls.plotter.update(**kwargs)

    @property
    def plot_data(self):
        return self.plotter.plot_data

    @classmethod
    def define_data(cls, mean=[0, 0], cov=[[10, 0], [0, 10]]):
        x, y = np.random.multivariate_normal(mean, cov, 5000).T
        df = pd.DataFrame(y, columns=["y"], index=pd.Index(x, name="x"))
        ds = xr.Dataset.from_dataframe(df)
        ds["v"] = xr.Variable(("x",), x)
        ret = xr.DataArray(ds.y)
        ret.psy.init_accessor(base=ds)
        return ret

    def test_bins(self):
        """Test the bins formatoption"""
        bins = [100, 10]
        self.update(bins=bins)
        self.assertEqual(len(self.plot_data.x), 100)
        self.assertEqual(len(self.plot_data.y), 10)

    def test_xrange(self):
        """Test the xrange formatoption"""
        data = self.data
        xrange = np.percentile(data.x.values, [25, 75])
        self.update(xrange=xrange)
        self.assertGreaterEqual(self.plot_data.x.min(), xrange[0])
        self.assertLessEqual(self.plot_data.x.max(), xrange[1])

        # now update to use the quantiles explicitely
        self.update(xrange=(["minmax", 25], ["minmax", 75]))
        self.assertGreaterEqual(self.plot_data.x.min(), xrange[0])
        self.assertLessEqual(self.plot_data.x.max(), xrange[1])

    def test_yrange(self):
        """Test the yrange formatoption"""
        data = self.data
        yrange = np.percentile(data.values, [25, 75])
        self.update(yrange=yrange)
        self.assertGreaterEqual(self.plot_data.y.min(), yrange[0])
        self.assertLessEqual(self.plot_data.y.max(), yrange[1])

        # now update to use the quantiles explicitely
        self.update(yrange=(["minmax", 25], ["minmax", 75]))
        self.assertGreaterEqual(self.plot_data.y.min(), yrange[0])
        self.assertLessEqual(self.plot_data.y.max(), yrange[1])

    def test_normed(self):
        """Test the normed formatoption"""
        self.update(normed="counts")
        data = self.plot_data
        self.assertAlmostEqual(data.values.sum(), 1.0)

        self.update(normed="area")
        data = self.plot_data
        a0, a1 = data.x.values[:2]
        b0, b1 = data.y.values[:2]
        area = (a1 - a0) * (b1 - b0)
        self.assertAlmostEqual((self.plot_data.values * area).sum(), 1.0)

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord="v", xlabel="%(name)s")
        self.assertEqual(
            self.plotter.ax.get_xlabel(),
            "v",
            msg="Did not update to the right coordinate!",
        )
