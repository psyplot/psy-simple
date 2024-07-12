"""Test module for 2D plots."""

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import os
import unittest

import _base_testing as bt
import matplotlib.pyplot as plt
import numpy as np
import psyplot.project as psy
import pytest
import test_base as tb
import test_lineplot as tl
import xarray as xr
from psyplot import ArrayList, open_dataset

from psy_simple.plotters import Simple2DPlotter

bold = tb.bold


class References2D(object):
    """abstract base class that defines reference methods for 2D plotter"""

    def ref_datagrid(self, close=True):
        """Create reference file for datagrid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.datagrid`
        formatoption"""
        kwargs = dict(xlim=(0, 40), ylim=(0, 40))
        sp = self.plot(**kwargs)
        sp.update(datagrid="k-")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("datagrid")))
        if close:
            sp.close(True, True)

    def ref_cmap(self, close=True):
        """Create reference file for cmap formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cmap`
        formatoption"""
        sp = self.plot(cmap="RdBu")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("cmap")))
        if close:
            sp.close(True, True)

    def ref_cbar(self, close=True):
        """Create reference file for cbar formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cbar`
        formatoption"""
        sp = self.plot(cbar=["fb", "fr", "fl", "ft", "b", "r"])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("cbar")))
        if close:
            sp.close(True, True)

    def ref_miss_color(self, close=True):
        """Create reference file for miss_color formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.miss_color`
        formatoption"""
        if self.plot_type[:3] == "map":
            kwargs = {"projection": "ortho", "grid_labels": False}
        else:
            kwargs = {}
        sp = self.plot(maskless=280, miss_color="0.9", **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("miss_color")))
        if close:
            sp.close(True, True)

    def ref_cbarspacing(self, close=True):
        """Create reference file for cbarspacing formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cbarspacing`
        formatoption"""
        if self.plot_type.endswith("vector") or getattr(
            self, "vector_mode", False
        ):
            kwargs = dict(
                bounds=np.arange(0, 1.45, 0.1).tolist()
                + np.linspace(1.5, 13.5, 7, endpoint=True).tolist()
                + np.arange(13.6, 15.05, 0.1).tolist(),
                color="absolute",
            )
        else:
            kwargs = dict(
                bounds=list(range(235, 250))
                + np.linspace(250, 295, 7, endpoint=True).tolist()
                + list(range(296, 310))
            )
        sp = self.plot(cbarspacing="proportional", cticks="rounded", **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("cbarspacing")))
        if close:
            sp.close(True, True)


class Simple2DPlotterTest(tl.LinePlotterTest, References2D):
    """Test :class:`psyplot.plotter.maps.Simple2DPlotter` class"""

    plot_type = "simple2D"

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.plot2d(self.ncfile, name=name, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=cls.var, auto_update=True
        )[0]
        cls.plotter = Simple2DPlotter(cls.data)
        cls.create_dirs()

    @unittest.skip("legend formatoption not implemented for 2D-Plotter")
    def ref_legend(self, *args, **kwargs):
        pass

    @unittest.skip("no need for xticks formatoption reference for 2D-Plotter")
    def ref_xticks(self, *args, **kwargs):
        pass

    @unittest.skip("color formatoption not implemented for 2D-Plotter")
    def test_color(self):
        pass

    @unittest.skip("Not implemented for 2D-Plotter")
    def test_coord(self):
        pass

    @unittest.skip("Not implemented for 2D-Plotter")
    def ref_plot_area(self, close=True):
        pass

    @unittest.skip("Not implemented for 2D-Plotter")
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

    @unittest.skip("Not implemented for 2D-Plotter")
    def test_plot_area(self, *args):
        pass

    @unittest.skip("Not implemented for 2D-Plotter")
    def test_plot_areax(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("Appending not possible for plot2d")
    def test_append_data(self):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked_transposed(self, close=True):
        pass

    def test_ylabel(self):
        """Test ylabel formatoption"""
        self.update(ylabel="{desc}")
        label = self.plotter.ax.yaxis.get_label()
        self.assertEqual(label.get_text(), "latitude [degrees_north]")
        self.update(
            labelsize=22, labelweight="bold", labelprops={"ha": "left"}
        )
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), "left")

    def test_xticks(self):
        """Test xticks formatoption"""
        self._test_DataTicksCalculator()

    def test_extend(self):
        """Test extend formatoption"""
        self.update(extend="both")
        self.assertEqual(self.plotter.cbar.cbars["b"].extend, "both")
        self.update(extend="min")
        self.assertEqual(self.plotter.cbar.cbars["b"].extend, "min")
        self.update(extend="neither")
        self.assertEqual(self.plotter.cbar.cbars["b"].extend, "neither")

    def test_legend(self):
        pass

    def test_cticks(self):
        """Test cticks, cticksize, ctickweight, ctickprops formatoptions"""
        cticks = self._minmax_cticks
        self.update(cticks="minmax")
        cbar = self.plotter.cbar.cbars["b"]
        self.assertAlmostArrayEqual(
            list(
                map(lambda t: float(t.get_text()), cbar.ax.get_xticklabels())
            ),
            cticks,
            atol=1e-2,
        )
        self.update(cticklabels="%3.1f")
        cticks = np.round(cticks, decimals=1).tolist()
        self.assertAlmostArrayEqual(
            list(
                map(lambda t: float(t.get_text()), cbar.ax.get_xticklabels())
            ),
            cticks,
            atol=0.1,
        )
        self.update(
            cticksize=20, ctickweight=bold, ctickprops={"labelcolor": "r"}
        )
        texts = cbar.ax.get_xticklabels()
        n = len(texts)
        self.assertEqual([t.get_weight() for t in texts], [bold] * n)
        self.assertEqual([t.get_size() for t in texts], [20] * n)
        self.assertEqual([t.get_color() for t in texts], ["r"] * n)

    @property
    def _minmax_cticks(self):
        return np.round(
            np.linspace(
                self.data.values.min(),
                self.data.values.max(),
                11,
                endpoint=True,
            ),
            decimals=2,
        ).tolist()

    def test_clabel(self):
        """Test clabel, clabelsize, clabelweight, clabelprops formatoptions"""

        def get_clabel():
            return self.plotter.cbar.cbars["b"].ax.xaxis.get_label()

        self._label_test("clabel", get_clabel)
        label = get_clabel()
        self.update(
            clabelsize=22, clabelweight="bold", clabelprops={"ha": "left"}
        )
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), "left")

    def test_datagrid(self, *args):
        """Test datagrid formatoption"""
        self.update(xlim=(0, 40), ylim=(0, 40), datagrid="k-")
        self.compare_figures(next(iter(args), self.get_ref_file("datagrid")))

    def test_cmap(self, *args):
        """Test colormap (cmap) formatoption"""
        self.update(cmap="RdBu")
        fname = next(iter(args), self.get_ref_file("cmap"))
        self.compare_figures(fname)
        self.update(cmap=plt.get_cmap("RdBu"))
        self.compare_figures(fname)

    def test_cbar(self, *args):
        """Test colorbar (cbar) formatoption"""
        self.update(cbar=["fb", "fr", "fl", "ft", "b", "r"])
        self.compare_figures(next(iter(args), self.get_ref_file("cbar")))

    def test_bounds(self):
        """Test bounds formatoption"""
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries,
            np.linspace(235, 310, 11, endpoint=True),
            atol=1e-2,
        )
        self.update(bounds="minmax")
        bounds = [
            239.91,
            246.89,
            253.88,
            260.87,
            267.86,
            274.84,
            281.83,
            288.82,
            295.81,
            302.79,
            309.78,
        ]
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries, bounds, atol=1e-2
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertAlmostArrayEqual(
            self.plotter.bounds.norm.boundaries,
            np.linspace(245, 300, 5, endpoint=True),
            atol=1e-2,
        )

    def test_miss_color(self, *args):
        """Test miss_color formatoption"""
        self.update(maskless=280, miss_color="0.9")
        self.compare_figures(next(iter(args), self.get_ref_file("miss_color")))

    def test_cbarspacing(self, *args):
        """Test cbarspacing formatoption"""
        self.update(
            cbarspacing="proportional",
            cticks="rounded",
            bounds=list(range(235, 250))
            + np.linspace(250, 295, 7, endpoint=True).tolist()
            + list(range(296, 310)),
        )
        self.compare_figures(
            next(iter(args), self.get_ref_file("cbarspacing"))
        )

    def test_ylim(self):
        """Test ylim formatoption"""
        super(Simple2DPlotterTest, self).test_ylim(test_pctls=False)


@pytest.mark.parametrize("vmin,vmax", [(1, int(1e2)), (int(-10), int(1e2))])
def test_log_bounds(vmin, vmax):
    ds = xr.Dataset()
    ds["test"] = (("y", "x"), np.random.randint(vmin, vmax, (40, 50)) * 1e-3)
    vmin *= 10e-3
    vmax *= 10e-3
    ds["x"] = ("x", np.arange(50))
    ds["y"] = ("y", np.arange(40))

    sp = ds.psy.plot.plot2d(bounds="log")
    plotter = sp.plotters[0]

    assert len(plotter.bounds.norm.boundaries) in [10, 11, 12]
    assert np.isclose(
        plotter.bounds.norm.boundaries[0], [vmin, vmin * 0.1, vmin * 10]
    ).any()
    assert np.isclose(
        plotter.bounds.norm.boundaries[-1], [vmax, vmax * 0.1, vmax * 10]
    ).any()


def test_symlog_bounds():
    vmin = -1
    vmax = 100
    ds = xr.Dataset()
    ds["test"] = (("y", "x"), np.random.randint(vmin, vmax, (40, 50)) * 1e-3)
    vmin *= 10e-3
    vmax *= 10e-3
    ds["x"] = ("x", np.arange(50))
    ds["y"] = ("y", np.arange(40))

    sp = ds.psy.plot.plot2d(bounds="symlog")
    plotter = sp.plotters[0]

    assert len(plotter.bounds.norm.boundaries) in [12, 13, 14]
    assert plotter.bounds.norm.boundaries[0] == pytest.approx(-0.1)
    assert plotter.bounds.norm.boundaries[-1] == pytest.approx(0.1)


class Simple2DPlotterTestArtificial(unittest.TestCase):
    """A test case for artifial data"""

    def test_single_level(self):
        """Test the case when all the data contains exactly one value"""
        ds = xr.Dataset()
        ds["test"] = (("y", "x"), np.ones((4, 5)))
        sp = ds.psy.plot.plot2d(cmap="Reds", bounds=["rounded", 3])
        self.assertEqual(list(sp.plotters[0].bounds.bounds), [1.0, 1.0, 1.5])


def test_plot_poly_3D_bounds():
    """Test plotting the polygons with 3D bounds."""
    fname = os.path.join(bt.test_dir, "rotated-pole-test.nc")
    with psy.plot.plot2d(fname, plot="poly") as sp:
        assert sp[0].ndim == 2
        plotter = sp.plotters[0]
        xmin, xmax = plotter.ax.get_xlim()
        ymin, ymax = plotter.ax.get_ylim()
        assert xmax - xmin > 100
        assert ymax - ymin > 50


def test_datagrid_3D_bounds():
    """Test plotting the datagrid with 3D bounds."""
    fname = os.path.join(bt.test_dir, "rotated-pole-test.nc")
    with psy.plot.plot2d(fname, datagrid="k-") as sp:
        assert sp[0].ndim == 2
        plotter = sp.plotters[0]
        xmin, xmax = plotter.ax.get_xlim()
        ymin, ymax = plotter.ax.get_ylim()
        assert xmax - xmin > 100
        assert ymax - ymin > 50


class Simple2DPlotterTest2D(tb.TestBase2D, Simple2DPlotterTest):
    """Test :class:`psy_simple.plotters.Simple2DPlotter` class without
    time and vertical dimension"""

    var = "t2m_2d"


# skip the reference creation functions of the 2D Plotter tests
skip_msg = (
    "Reference figures for this class are created by the "
    "Simple2DPlotterTest"
)
for funcname in filter(
    lambda s: s.startswith("ref"), dir(Simple2DPlotterTest2D)
):
    setattr(
        Simple2DPlotterTest2D,
        funcname,
        unittest.skip(skip_msg)(lambda self: None),
    )
