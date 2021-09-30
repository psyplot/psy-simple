"""Test module of the :mod:`psy_simple.plotters` module"""
import os
import sys
import unittest
import tempfile
from itertools import chain

import numpy as np
import matplotlib as mpl
import matplotlib.colors as mcol
import matplotlib.pyplot as plt

from psyplot import open_dataset, InteractiveList
from psy_simple.plotters import LinePlotter, mpl_version
import psyplot.project as psy

import test_base as tb
import _base_testing as bt


bold = tb.bold


class LinePlotterTest(tb.BasePlotterTest):
    """Test class for :class:`psy_simple.plotters.LinePlotter`"""

    plot_type = "line"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True
        )
        cls.plotter = LinePlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.lineplot(
            self.ncfile, name=name, t=0, z=0, y=[0, 1], **kwargs
        )

    @unittest.skipIf(
        mpl_version == 3.3,
        "Updating grids is known to malfunction for matplotlib 3.3!",
    )
    def ref_grid(self, close=True):
        """Create reference file for grid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.grid`
        formatoption"""
        sp = self.plot()
        sp.update(grid=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("grid1")))
        sp.update(grid="b")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("grid2")))
        if close:
            sp.close(True, True)

    def ref_transpose(self, close=True):
        """Create reference file for transpose formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.transpose`
        formatoption"""
        sp = self.plot()
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("transpose1")))
        sp.update(transpose=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("transpose2")))
        if close:
            sp.close(True, True)

    def ref_legend(self, close=True):
        """Create reference file for legend formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.legend`
        formatoption"""
        sp = self.plot(
            legend={
                "loc": "upper center",
                "bbox_to_anchor": (0.5, -0.05),
                "ncol": 2,
            }
        )
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("legend")))
        if close:
            sp.close(True, True)

    def ref_xticks(self, close=True):
        """Create reference file for xticks formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.xticks`
        formatoption"""
        sp = psy.plot.lineplot(
            self.ncfile,
            name=self.var,
            lon=0,
            lev=0,
            lat=[0, 1],
            xticklabels={"major": "%m", "minor": "%d"},
            xtickprops={"pad": 7.0},
            xticks={"minor": "week", "major": "month"},
        )
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("xticks")))
        if close:
            sp.close(True, True)

    def ref_plot_area(self, close=True):
        """Create reference file for plot formatoption with ``'area'``"""
        sp = self.plot(plot="area")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("plot_area")))
        if close:
            sp.close(True, True)

    def ref_plot_areax(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot="areax", transpose=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("plot_areax")))
        if close:
            sp.close(True, True)

    def ref_plot_None(self, close=True):
        sp = self.plot(plot=["--", None])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("plot_None")))
        if close:
            sp.close(True, True)

    def ref_plot_stacked(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot="stacked")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("plot_stacked")))
        if close:
            sp.close(True, True)

    def ref_plot_stacked_transposed(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot="stacked", transpose=True)
        sp.export(
            os.path.join(
                bt.ref_dir, self.get_ref_file("plot_stacked_transposed")
            )
        )
        if close:
            sp.close(True, True)

    def test_plot_area(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot="area")
        self.compare_figures(next(iter(args), self.get_ref_file("plot_area")))

    def test_plot_areax(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot="areax", transpose=True)
        self.compare_figures(next(iter(args), self.get_ref_file("plot_areax")))

    def test_plot_None(self, *args):
        """Test excluding one specific line"""
        self.update(plot=["--", None])
        self.compare_figures(next(iter(args), self.get_ref_file("plot_None")))

    def test_plot_stacked(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot="stacked")
        self.compare_figures(
            next(iter(args), self.get_ref_file("plot_stacked"))
        )

    def test_mask_01_var(self):
        def get_data(data):
            if isinstance(data, InteractiveList):
                return data[0]
            else:
                return data

        data = get_data(self.data)
        mask = data.copy(data=np.ones_like(data, dtype=bool))
        mask[..., 3] = False
        data.psy.base["mask"] = mask
        try:
            self.update(mask="mask")
            self.assertTrue(
                np.all(get_data(self.plotter.plot_data).isnull()[..., 3])
            )
        finally:
            del data.psy.base["mask"]

    def test_mask_02_da(self):
        def get_data(data):
            if isinstance(data, InteractiveList):
                return data[0]
            else:
                return data

        data = get_data(self.data)
        mask = data.copy(data=np.ones_like(data, dtype=bool))
        mask[..., 3] = False
        self.update(mask=mask)
        self.assertTrue(
            np.all(get_data(self.plotter.plot_data).isnull()[..., 3])
        )

    @unittest.skipIf(sys.platform == "win32", "Skipped due to tempfile issue.")
    def test_mask_03_fname(self):
        def get_data(data):
            if isinstance(data, InteractiveList):
                return data[0]
            else:
                return data

        data = get_data(self.data)
        mask = data.copy(data=np.ones_like(data, dtype=bool))
        mask[..., 3] = False
        with tempfile.TemporaryDirectory(prefix="psyplot_") as tmpdir:
            maskfile = os.path.join(tmpdir, "mask.nc")
            mask.drop_vars(set(mask.coords) - set(mask.dims)).to_netcdf(
                maskfile
            )
            self.update(mask=maskfile)
            self.assertTrue(
                np.all(get_data(self.plotter.plot_data).isnull()[..., 3])
            )

    def test_append_data(self):
        """Test appending new data to the list"""

        def get_color(artist):
            try:
                ret = artist.get_color()
            except AttributeError:
                try:
                    ret = artist.get_facecolor()
                except AttributeError:
                    ret = artist[0].get_facecolor()
            return mcol.to_rgba(ret)

        data = self.data
        n = len(data)
        self.assertEqual(len(self.plotter.plot_data), n)
        old_c = mcol.to_rgba(self.plotter.color.colors[-1])
        self.assertEqual(get_color(self.plotter.plot._plot[-1]), old_c)

        try:
            # append data
            new = data[-1].psy.copy()
            data.append(new, new_name=True)
            self.assertEqual(len(data), n + 1)
            self.plotter.update(replot=True)
            self.assertEqual(len(self.plotter.plot_data), n + 1)
            c = mcol.to_rgba(self.plotter.color.colors[-1])
            self.assertNotEqual(c, old_c)
            self.assertEqual(get_color(self.plotter.plot._plot[-1]), c)

            # remove data again
            data.pop(-1)
            self.plotter.update(replot=True)
            self.assertEqual(len(self.plotter.plot_data), n)
            self.assertEqual(get_color(self.plotter.plot._plot[-1]), old_c)

            # append data again
            data.append(new, new_name=True)
            self.plotter.update(replot=True)
            self.assertEqual(len(self.plotter.plot_data), n + 1)
            self.assertEqual(get_color(self.plotter.plot._plot[-1]), c)
        finally:
            if len(data) > n:
                data.pop(-1)

    def test_plot_stacked_transposed(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot="stacked", transpose=True)
        self.compare_figures(
            next(iter(args), self.get_ref_file("plot_stacked_transposed"))
        )

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord="v", xlabel="%(name)s")
        self.assertEqual(
            self.plotter.ax.get_xlabel(),
            "v",
            msg="Did not update to the right coordinate!",
        )

    @unittest.skipIf(
        mpl_version == 3.3,
        "Updating grids is known to malfunction for matplotlib 3.3!",
    )
    def test_grid(self, *args):
        """Test grid formatoption"""
        args = iter(args)
        self.update(grid=True)
        self.compare_figures(next(args, self.get_ref_file("grid1")))
        self.update(grid="b")
        self.compare_figures(next(args, self.get_ref_file("grid2")))

    def test_xlabel(self):
        """Test xlabel formatoption"""
        self.update(xlabel="{desc}")
        label = self.plotter.ax.xaxis.get_label()
        self.assertEqual(label.get_text(), "longitude [degrees_east]")
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
        self.assertEqual(label.get_text(), "Temperature [K]")
        self.update(
            labelsize=22, labelweight="bold", labelprops={"ha": "left"}
        )
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), "left")

    def test_xlim(self):
        """Test xlim formatoption"""
        curr_lim = self.plotter.ax.get_xlim()
        self.update(xlim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_xlim(), (-1, 300))
        self.update(xlim=(-1, "rounded"))
        self.assertEqual(self.plotter.ax.get_xlim(), (-1, curr_lim[1]))

    def test_ylim(self, test_pctls=True):
        """Test ylim formatoption"""
        curr_lim = self.plotter.ax.get_ylim()
        self.update(ylim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, 300))
        self.update(ylim=(-1, "rounded"))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, curr_lim[1]))
        if test_pctls:
            self.update(ylim=(["minmax", 25], ["minmax", 75]))
            data = self.data.to_dataframe()
            arr = data[data.notnull()].values
            self.assertAlmostArrayEqual(
                self.plotter.ax.get_ylim(),
                np.percentile(arr, [25, 75]).tolist(),
            )

    def test_sym_lims(self):
        ax = self.plotter.ax
        xrange = ax.get_xlim()
        yrange = ax.get_ylim()
        mins = [min(xrange[0], yrange[0]), min(xrange[1], yrange[1])]
        maxs = [max(xrange[0], yrange[0]), max(xrange[1], yrange[1])]

        self.update(sym_lims="min")
        self.assertEqual(ax.get_xlim()[0], mins[0])
        self.assertEqual(ax.get_xlim()[1], mins[1])
        self.assertEqual(ax.get_ylim()[0], mins[0])
        self.assertEqual(ax.get_ylim()[1], mins[1])

        self.update(sym_lims="max")
        self.assertEqual(ax.get_xlim()[0], maxs[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], maxs[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

        self.update(sym_lims=["min", "max"])
        self.assertEqual(ax.get_xlim()[0], mins[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], mins[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

        self.update(sym_lims=[None, "max"])
        self.assertEqual(ax.get_xlim()[0], xrange[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], yrange[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

    def test_color(self):
        colors = ["y", "g"][: len(self.data)]
        current_colors = [l.get_color() for l in self.plotter.ax.lines]
        self.update(color=colors)
        self.assertEqual(
            [l.get_color() for l in self.plotter.ax.lines], colors
        )
        self.update(color=None)
        self.assertEqual(
            [l.get_color() for l in self.plotter.ax.lines], current_colors
        )

    def test_transpose(self, *args):
        """Test transpose formatoption"""
        args = iter(args)
        self.compare_figures(next(args, self.get_ref_file("transpose1")))
        self.update(transpose=True)
        self.compare_figures(next(args, self.get_ref_file("transpose2")))

    def test_legend(self, *args):
        """Test legend and legendlabels formatoption"""
        args = iter(args)
        self.update(legend=False)
        self.assertIsNone(self.plotter.ax.legend_)
        self.update(
            legend={
                "loc": "upper center",
                "bbox_to_anchor": (0.5, -0.05),
                "ncol": 2,
            }
        )
        self.compare_figures(next(args, self.get_ref_file("legend")))
        self.update(legendlabels="%(lat)s")
        self.assertAlmostArrayEqual(
            [float(t.get_text()) for t in plt.gca().legend_.get_texts()],
            [da.lat.values for da in self.data],
        )

    def test_xticks(self, *args):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self._test_DataTicksCalculator()
        self._test_DtTicksBase(*args)

    _max_rounded_ref = 400

    def _test_DataTicksCalculator(self):
        # testing of psy_simple.plotters.DataTicksCalculator
        self.update(xticks=["data", 2])
        ax = plt.gca()
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data

        lon = data.lon.values

        self.assertEqual(list(ax.get_xticks()), list(lon[::2]))
        self.update(xticks=["mid", 2])

        self.assertEqual(
            list(ax.get_xticks()), list((lon[:-1] + lon[1:]) / 2.0)[::2]
        )
        self.update(xticks="rounded")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(0, self._max_rounded_ref, 11, endpoint=True).tolist(),
        )
        self.update(xticks="roundedsym")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(
                -self._max_rounded_ref,
                self._max_rounded_ref,
                10,
                endpoint=True,
            ).tolist(),
        )
        self.update(xticks="minmax")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(lon.min(), lon.max(), 11, endpoint=True).tolist(),
        )
        self.update(xticks="sym")
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-lon.max(), lon.max(), 10, endpoint=True).tolist(),
        )

    # apparently matplotlib changed how they numerically represent the
    # date ticks. Therefore we enable multiple options.
    ref_dt_vals = {
        "month": [
            {3361.25, 3331.75, 3422.25, 3391.75},
            {722494.75, 722524.25, 722554.75, 722585.25},
        ],
        "monthbegin": [
            {722450.75, 722481.75, 722509.75, 722540.75, 722570.75, 722601.75},
            {3438.75, 3407.75, 3377.75, 3346.75, 3318.75, 3287.75},
        ],
        "monthend": [
            {722480.75, 722508.75, 722539.75, 722569.75, 722600.75},
            {3437.75, 3406.75, 3376.75, 3345.75, 3317.75},
        ],
        "week": {
            722487.75,
            722494.75,
            722501.75,
            722508.75,
            722515.75,
            722522.75,
            722529.75,
            722536.75,
            722543.75,
            722550.75,
            722557.75,
            722564.75,
            722571.75,
            722578.75,
            722585.75,
            722592.75,
            722599.75,
        },
    }

    def _test_DtTicksBase(self, *args):
        # testing of psy_simple.plotters.DtTicksBase
        args = iter(args)
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
        xticks = {"major": ax.get_xticks(), "minor": ax.get_xticks(minor=True)}
        plotter.update(xticks="month")
        self.assertIn(set(ax.get_xticks()), self.ref_dt_vals["month"])
        plotter.update(xticks="monthbegin")
        self.assertIn(set(ax.get_xticks()), self.ref_dt_vals["monthbegin"])
        plotter.update(xticks="monthend")
        self.assertIn(set(ax.get_xticks()), self.ref_dt_vals["monthend"])
        plotter.update(xticks="month", xticklabels="%m")
        # sometimes the labels are only set after drawing
        if ax.get_xticklabels()[0].get_text():
            self.assertEqual(
                [int(t.get_text()) for t in ax.get_xticklabels()[:]],
                list(range(2, 6)),
            )
        plotter.update(
            xticks={"minor": "week"},
            xticklabels={"minor": "%d"},
            xtickprops={"pad": 7.0},
        )
        ticks = np.asarray(ax.get_xticks(minor=True))
        self.assertLessEqual(
            set(ticks[(ticks >= 722487.75) & (ticks <= 722599.75)].tolist()),
            self.ref_dt_vals["week"],
        )
        self.compare_figures(next(args, self.get_ref_file("xticks")))
        plotter.update(xticks={"major": None, "minor": None})
        self.assertEqual(list(ax.get_xticks()), list(xticks["major"]))
        self.assertEqual(
            list(ax.get_xticks(minor=True)), list(xticks["minor"])
        )

    def test_tick_rotation(self):
        """Test xrotation and yrotation formatoption"""
        self.update(xrotation=90, yrotation=90)
        self.assertTrue(
            all(
                t.get_rotation() == 90
                for t in self.plotter.ax.get_xticklabels()
            )
        )
        self.assertTrue(
            all(
                t.get_rotation() == 90
                for t in self.plotter.ax.get_yticklabels()
            )
        )

    def test_ticksize(self):
        """Tests ticksize formatoption"""
        self.update(ticksize=24)
        ax = self.plotter.ax
        self.assertTrue(
            all(
                t.get_size() == 24
                for t in chain(ax.get_xticklabels(), ax.get_yticklabels())
            )
        )
        self.update(
            xticks={"major": ["data", 40], "minor": ["data", 10]},
            ticksize={"major": 12, "minor": 10},
            xtickprops={"pad": 7.0},
        )
        self.assertTrue(
            all(
                t.get_size() == 12
                for t in chain(ax.get_xticklabels(), ax.get_yticklabels())
            )
        )
        self.assertTrue(
            all(t.get_size() == 10 for t in ax.get_xticklabels(minor=True))
        )

    def test_axiscolor(self):
        """Test axiscolor formatoption"""
        ax = self.plotter.ax
        positions = ["top", "right", "left", "bottom"]
        # test updating all to red
        self.update(axiscolor="red")
        self.assertEqual(
            ["red"] * 4,
            list(self.plotter["axiscolor"].values()),
            "Edgecolors are not red but "
            + ", ".join(self.plotter["axiscolor"].values()),
        )
        # test updating all to the default setup
        self.update(axiscolor=None)
        for pos in positions:
            error = "Edgecolor ({0}) is not the default color ({1})!".format(
                ax.spines[pos].get_edgecolor(), mpl.rcParams["axes.edgecolor"]
            )
            self.assertEqual(
                mpl.colors.colorConverter.to_rgba(
                    mpl.rcParams["axes.edgecolor"]
                ),
                ax.spines[pos].get_edgecolor(),
                msg=error,
            )
            error = "Linewidth ({0}) is not the default width ({1})!".format(
                ax.spines[pos].get_linewidth(), mpl.rcParams["axes.linewidth"]
            )
            self.assertEqual(
                mpl.rcParams["axes.linewidth"],
                ax.spines[pos].get_linewidth(),
                msg=error,
            )
        # test updating only one spine
        self.update(axiscolor={"top": "red"})
        self.assertEqual(
            (1.0, 0.0, 0.0, 1.0),
            ax.spines["top"].get_edgecolor(),
            msg="Axiscolor ({0}) has not been updated".format(
                ax.spines["top"].get_edgecolor()
            ),
        )
        self.assertGreater(
            ax.spines["top"].get_linewidth(), 0.0, "Line width of axis is 0!"
        )
        for pos in positions[1:]:
            error = "Edgecolor ({0}) is not the default color ({1})!".format(
                ax.spines[pos].get_edgecolor(), mpl.rcParams["axes.edgecolor"]
            )
            self.assertEqual(
                mpl.colors.colorConverter.to_rgba(
                    mpl.rcParams["axes.edgecolor"]
                ),
                ax.spines[pos].get_edgecolor(),
                msg=error,
            )


class LinePlotterTest2D(tb.TestBase2D, LinePlotterTest):
    """Test :class:`psy_simple.plotters.LinePlotter` class without
    time and vertical dimension"""

    var = "t2m_2d"

    def test_xticks(self, *args):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self._test_DataTicksCalculator()

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord="v_2d", xlabel="%(name)s")
        self.assertEqual(
            self.plotter.ax.get_xlabel(),
            "v_2d",
            msg="Did not update to the right coordinate!",
        )


# skip the reference creation functions of the 2D Plotter tests
skip_msg = (
    "Reference figures for this class are created by the " "LinePlotterTest"
)
for funcname in filter(lambda s: s.startswith("ref"), dir(LinePlotterTest2D)):
    setattr(
        LinePlotterTest2D, funcname, unittest.skip(skip_msg)(lambda self: None)
    )
