"""Test module of the :mod:`psy_simple.plotters` module"""
import os
import re
import six
import pytest
from functools import wraps
from itertools import chain
import tempfile
import unittest
import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.colors as mcol
import matplotlib.pyplot as plt
from psyplot.utils import _TempBool
from psy_simple.plotters import (
    LinePlotter, Simple2DPlotter, BarPlotter, ViolinPlotter,
    SimpleVectorPlotter, CombinedSimplePlotter, DensityPlotter,
    FldmeanPlotter)
import psyplot.project as psy
import test_base as tb
import _base_testing as bt
from psyplot import InteractiveList, ArrayList, open_dataset, rcParams


try:
    from cdo import Cdo
    Cdo()
except Exception:
    with_cdo = False
else:
    with_cdo = True


bold = tb.bold


class LinePlotterTest(tb.BasePlotterTest):
    """Test class for :class:`psy_simple.plotters.LinePlotter`"""

    plot_type = 'line'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True)
        cls.plotter = LinePlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.lineplot(
            self.ncfile, name=name, t=0, z=0, y=[0, 1], **kwargs)

    def ref_grid(self, close=True):
        """Create reference file for grid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.grid`
        formatoption"""
        sp = self.plot()
        sp.update(grid=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('grid1')))
        sp.update(grid='b')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('grid2')))
        if close:
            sp.close(True, True)

    def ref_transpose(self, close=True):
        """Create reference file for transpose formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.transpose`
        formatoption"""
        sp = self.plot()
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('transpose1')))
        sp.update(transpose=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('transpose2')))
        if close:
            sp.close(True, True)

    def ref_legend(self, close=True):
        """Create reference file for legend formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.legend`
        formatoption"""
        sp = self.plot(
            legend={'loc': 'upper center', 'bbox_to_anchor': (0.5, -0.05),
                    'ncol': 2})
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('legend')))
        if close:
            sp.close(True, True)

    def ref_xticks(self, close=True):
        """Create reference file for xticks formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.LinePlotter.xticks`
        formatoption"""
        sp = psy.plot.lineplot(
            self.ncfile, name=self.var, lon=0, lev=0, lat=[0, 1],
            xticklabels={'major': '%m', 'minor': '%d'},
            xtickprops={'pad': 7.0},
            xticks={'minor': 'week', 'major': 'month'})
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('xticks')))
        if close:
            sp.close(True, True)

    def ref_plot_area(self, close=True):
        """Create reference file for plot formatoption with ``'area'``"""
        sp = self.plot(plot='area')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('plot_area')))
        if close:
            sp.close(True, True)

    def ref_plot_areax(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot='areax', transpose=True)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('plot_areax')))
        if close:
            sp.close(True, True)

    def ref_plot_None(self, close=True):
        sp = self.plot(plot=['--', None])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('plot_None')))
        if close:
            sp.close(True, True)

    def ref_plot_stacked(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot='stacked')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('plot_stacked')))
        if close:
            sp.close(True, True)

    def ref_plot_stacked_transposed(self, close=True):
        """Create reference file for plot formatoption with ``'areax'``"""
        sp = self.plot(plot='stacked', transpose=True)
        sp.export(os.path.join(bt.ref_dir,
                               self.get_ref_file('plot_stacked_transposed')))
        if close:
            sp.close(True, True)

    def test_plot_area(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot='area')
        self.compare_figures(next(iter(args), self.get_ref_file('plot_area')))

    def test_plot_areax(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot='areax', transpose=True)
        self.compare_figures(next(iter(args), self.get_ref_file('plot_areax')))

    def test_plot_None(self, *args):
        """Test excluding one specific line"""
        self.update(plot=['--', None])
        self.compare_figures(next(iter(args), self.get_ref_file('plot_None')))

    def test_plot_stacked(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot='stacked')
        self.compare_figures(next(iter(args),
                                  self.get_ref_file('plot_stacked')))

    def test_mask_01_var(self):
        def get_data(data):
            if isinstance(data, InteractiveList):
                return data[0]
            else:
                return data
        data = get_data(self.data)
        mask = data.copy(data=np.ones_like(data, dtype=bool))
        mask[..., 3] = False
        data.psy.base['mask'] = mask
        try:
            self.update(mask='mask')
            self.assertTrue(
                np.all(get_data(self.plotter.plot_data).isnull()[..., 3]))
        finally:
            del data.psy.base['mask']

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
            np.all(get_data(self.plotter.plot_data).isnull()[..., 3]))

    def test_mask_03_fname(self):
        def get_data(data):
            if isinstance(data, InteractiveList):
                return data[0]
            else:
                return data
        data = get_data(self.data)
        mask = data.copy(data=np.ones_like(data, dtype=bool))
        mask[..., 3] = False
        with tempfile.TemporaryDirectory(prefix='psyplot_') as tmpdir:
            maskfile = os.path.join(tmpdir, 'mask.nc')
            mask.drop_vars(set(mask.coords) - set(mask.dims)).to_netcdf(
                maskfile)
            self.update(mask=maskfile)
            self.assertTrue(
                np.all(get_data(self.plotter.plot_data).isnull()[..., 3]))

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
            self.assertEqual(len(data), n+1)
            self.plotter.update(replot=True)
            self.assertEqual(len(self.plotter.plot_data), n+1)
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
            self.assertEqual(len(self.plotter.plot_data), n+1)
            self.assertEqual(get_color(self.plotter.plot._plot[-1]), c)
        finally:
            if len(data) > n:
                data.pop(-1)

    def test_plot_stacked_transposed(self, *args):
        """Test plot formatoption with ``'areax'``"""
        self.update(plot='stacked', transpose=True)
        self.compare_figures(
            next(iter(args), self.get_ref_file('plot_stacked_transposed')))

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord='v', xlabel='%(name)s')
        self.assertEqual(self.plotter.ax.get_xlabel(), 'v',
                         msg='Did not update to the right coordinate!')

    def test_grid(self, *args):
        """Test grid formatoption"""
        args = iter(args)
        self.update(grid=True)
        self.compare_figures(next(args, self.get_ref_file('grid1')))
        self.update(grid='b')
        self.compare_figures(next(args, self.get_ref_file('grid2')))

    def test_xlabel(self):
        """Test xlabel formatoption"""
        self.update(xlabel='{desc}')
        label = self.plotter.ax.xaxis.get_label()
        self.assertEqual(label.get_text(), 'longitude [degrees_east]')
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_ylabel(self):
        """Test ylabel formatoption"""
        self.update(ylabel='{desc}')
        label = self.plotter.ax.yaxis.get_label()
        self.assertEqual(label.get_text(), 'Temperature [K]')
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_xlim(self):
        """Test xlim formatoption"""
        curr_lim = self.plotter.ax.get_xlim()
        self.update(xlim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_xlim(), (-1, 300))
        self.update(xlim=(-1, 'rounded'))
        self.assertEqual(self.plotter.ax.get_xlim(), (-1, curr_lim[1]))

    def test_ylim(self, test_pctls=True):
        """Test ylim formatoption"""
        curr_lim = self.plotter.ax.get_ylim()
        self.update(ylim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, 300))
        self.update(ylim=(-1, 'rounded'))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, curr_lim[1]))
        if test_pctls:
            self.update(ylim=(["minmax", 25], ["minmax", 75]))
            data = self.data.to_dataframe()
            arr = data[data.notnull()].values
            self.assertAlmostArrayEqual(self.plotter.ax.get_ylim(),
                                        np.percentile(arr, [25, 75]).tolist())

    def test_sym_lims(self):
        ax = self.plotter.ax
        xrange = ax.get_xlim()
        yrange = ax.get_ylim()
        mins = [min(xrange[0], yrange[0]), min(xrange[1], yrange[1])]
        maxs = [max(xrange[0], yrange[0]), max(xrange[1], yrange[1])]

        self.update(sym_lims='min')
        self.assertEqual(ax.get_xlim()[0], mins[0])
        self.assertEqual(ax.get_xlim()[1], mins[1])
        self.assertEqual(ax.get_ylim()[0], mins[0])
        self.assertEqual(ax.get_ylim()[1], mins[1])

        self.update(sym_lims='max')
        self.assertEqual(ax.get_xlim()[0], maxs[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], maxs[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

        self.update(sym_lims=['min', 'max'])
        self.assertEqual(ax.get_xlim()[0], mins[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], mins[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

        self.update(sym_lims=[None, 'max'])
        self.assertEqual(ax.get_xlim()[0], xrange[0])
        self.assertEqual(ax.get_xlim()[1], maxs[1])
        self.assertEqual(ax.get_ylim()[0], yrange[0])
        self.assertEqual(ax.get_ylim()[1], maxs[1])

    def test_color(self):
        colors = ['y', 'g'][:len(self.data)]
        current_colors = [l.get_color() for l in self.plotter.ax.lines]
        self.update(color=colors)
        self.assertEqual([l.get_color() for l in self.plotter.ax.lines],
                         colors)
        self.update(color=None)
        self.assertEqual([l.get_color() for l in self.plotter.ax.lines],
                         current_colors)

    def test_transpose(self, *args):
        """Test transpose formatoption"""
        args = iter(args)
        self.compare_figures(next(args, self.get_ref_file('transpose1')))
        self.update(transpose=True)
        self.compare_figures(next(args, self.get_ref_file('transpose2')))

    def test_legend(self, *args):
        """Test legend and legendlabels formatoption"""
        args = iter(args)
        self.update(legend=False)
        self.assertIsNone(self.plotter.ax.legend_)
        self.update(legend={
            'loc': 'upper center', 'bbox_to_anchor': (0.5, -0.05), 'ncol': 2})
        self.compare_figures(next(args, self.get_ref_file('legend')))
        self.update(legendlabels='%(lat)s')
        self.assertAlmostArrayEqual(
            [float(t.get_text()) for t in plt.gca().legend_.get_texts()],
            [da.lat.values for da in self.data])

    def test_xticks(self, *args):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self._test_DataTicksCalculator()
        self._test_DtTicksBase(*args)

    _max_rounded_ref = 400

    def _test_DataTicksCalculator(self):
        # testing of psy_simple.plotters.DataTicksCalculator
        self.update(xticks=['data', 2])
        ax = plt.gca()
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data

        lon = data.lon.values

        self.assertEqual(list(ax.get_xticks()),
                         list(lon[::2]))
        self.update(xticks=['mid', 2])

        self.assertEqual(
            list(ax.get_xticks()), list(
                (lon[:-1] + lon[1:]) / 2.)[::2])
        self.update(xticks='rounded')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(0, self._max_rounded_ref, 11, endpoint=True).tolist())
        self.update(xticks='roundedsym')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-self._max_rounded_ref, self._max_rounded_ref, 10,
                        endpoint=True).tolist())
        self.update(xticks='minmax')
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                lon.min(), lon.max(),
                11, endpoint=True).tolist())
        self.update(xticks='sym')
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                -lon.max(), lon.max(),
                10, endpoint=True).tolist())

    # apparently matplotlib changed how they numerically represent the
    # date ticks. Therefore we enable multiple options.
    ref_dt_vals = {
        "month": [{3361.25, 3331.75, 3422.25, 3391.75},
                  {722494.75, 722524.25, 722554.75, 722585.25}],
        "monthbegin": [
            {722450.75, 722481.75, 722509.75, 722540.75, 722570.75, 722601.75},
            {3438.75, 3407.75, 3377.75, 3346.75, 3318.75, 3287.75},
        ],
        "monthend": [
            {722480.75, 722508.75, 722539.75, 722569.75, 722600.75},
            {3437.75, 3406.75, 3376.75, 3345.75, 3317.75},
        ],
        "week": {722487.75, 722494.75, 722501.75, 722508.75, 722515.75,
                 722522.75, 722529.75, 722536.75, 722543.75, 722550.75,
                 722557.75, 722564.75, 722571.75, 722578.75, 722585.75,
                 722592.75, 722599.75}
    }

    def _test_DtTicksBase(self, *args):
        # testing of psy_simple.plotters.DtTicksBase
        args = iter(args)
        data = InteractiveList.from_dataset(
            self.data[0].psy.base, y=[0, 1], z=0, x=0, name=self.var,
            auto_update=True)
        plotter = self.plotter.__class__(data)
        ax = plotter.ax
        xticks = {'major': ax.get_xticks(), 'minor': ax.get_xticks(minor=True)}
        plotter.update(xticks='month')
        self.assertIn(set(ax.get_xticks()), self.ref_dt_vals["month"])
        plotter.update(xticks='monthbegin')
        self.assertIn(
            set(ax.get_xticks()), self.ref_dt_vals["monthbegin"])
        plotter.update(xticks='monthend')
        self.assertIn(
            set(ax.get_xticks()), self.ref_dt_vals["monthend"])
        plotter.update(xticks='month', xticklabels='%m')
        # sometimes the labels are only set after drawing
        if ax.get_xticklabels()[0].get_text():
            self.assertEqual(
                [int(t.get_text()) for t in ax.get_xticklabels()[:]],
                list(range(2, 6)))
        plotter.update(xticks={'minor': 'week'}, xticklabels={'minor': '%d'},
                       xtickprops={'pad': 7.0})
        ticks = np.asarray(ax.get_xticks(minor=True))
        self.assertLessEqual(
            set(ticks[(ticks >= 722487.75) & (ticks <= 722599.75)].tolist()),
            self.ref_dt_vals["week"])
        self.compare_figures(next(args, self.get_ref_file('xticks')))
        plotter.update(xticks={'major': None, 'minor': None})
        self.assertEqual(list(ax.get_xticks()),
                         list(xticks['major']))
        self.assertEqual(list(ax.get_xticks(minor=True)),
                         list(xticks['minor']))

    def test_tick_rotation(self):
        """Test xrotation and yrotation formatoption"""
        self.update(xrotation=90, yrotation=90)
        self.assertTrue(all(
            t.get_rotation() == 90 for t in self.plotter.ax.get_xticklabels()))
        self.assertTrue(all(
            t.get_rotation() == 90 for t in self.plotter.ax.get_yticklabels()))

    def test_ticksize(self):
        """Tests ticksize formatoption"""
        self.update(ticksize=24)
        ax = self.plotter.ax
        self.assertTrue(all(t.get_size() == 24 for t in chain(
            ax.get_xticklabels(), ax.get_yticklabels())))
        self.update(
            xticks={'major': ['data', 40], 'minor': ['data', 10]},
            ticksize={'major': 12, 'minor': 10}, xtickprops={'pad': 7.0})
        self.assertTrue(all(t.get_size() == 12 for t in chain(
            ax.get_xticklabels(), ax.get_yticklabels())))
        self.assertTrue(all(
            t.get_size() == 10 for t in ax.get_xticklabels(minor=True)))

    def test_axiscolor(self):
        """Test axiscolor formatoption"""
        ax = self.plotter.ax
        positions = ['top', 'right', 'left', 'bottom']
        # test updating all to red
        self.update(axiscolor='red')
        self.assertEqual(['red']*4, list(self.plotter['axiscolor'].values()),
                         "Edgecolors are not red but " + ', '.join(
                         self.plotter['axiscolor'].values()))
        # test updating all to the default setup
        self.update(axiscolor=None)
        for pos in positions:
            error = "Edgecolor ({0}) is not the default color ({1})!".format(
                ax.spines[pos].get_edgecolor(), mpl.rcParams['axes.edgecolor'])
            self.assertEqual(mpl.colors.colorConverter.to_rgba(
                                 mpl.rcParams['axes.edgecolor']),
                             ax.spines[pos].get_edgecolor(), msg=error)
            error = "Linewidth ({0}) is not the default width ({1})!".format(
                ax.spines[pos].get_linewidth(), mpl.rcParams['axes.linewidth'])
            self.assertEqual(mpl.rcParams['axes.linewidth'],
                             ax.spines[pos].get_linewidth(), msg=error)
        # test updating only one spine
        self.update(axiscolor={'top': 'red'})
        self.assertEqual((1., 0., 0., 1.0), ax.spines['top'].get_edgecolor(),
                         msg="Axiscolor ({0}) has not been updated".format(
                             ax.spines['top'].get_edgecolor()))
        self.assertGreater(ax.spines['top'].get_linewidth(), 0.0,
                           "Line width of axis is 0!")
        for pos in positions[1:]:
            error = "Edgecolor ({0}) is not the default color ({1})!".format(
                ax.spines[pos].get_edgecolor(), mpl.rcParams['axes.edgecolor'])
            self.assertEqual(mpl.colors.colorConverter.to_rgba(
                                 mpl.rcParams['axes.edgecolor']),
                             ax.spines[pos].get_edgecolor(), msg=error)


class CoordinateTest(unittest.TestCase):
    """A test case for the :class:`psy_simple.plotters.AlternativeXCoord` class
    """

    def tearDown(self):
        psy.close('all')

    @property
    def _test_dataset(self):
        v = xr.Variable(('exp', ), [1, 1, 2, 2, 3, 3])
        return xr.Dataset({'v1': v, 'v2': v.copy(True), 'v3': v.copy(True)})

    def test_duplicates_line(self):
        """"Test the coordinate containing duplicates"""
        ds = self._test_dataset
        sp = psy.plot.lineplot(ds, name=['v1', 'v2'], coord='v3',
                               xlabel='%(name)s')
        ax = sp.plotters[0].ax
        self.assertEqual(ax.get_xlabel(), 'v3')
        self.assertEqual(sp.plotters[0].plot_data[0].dims, ('v3', ))

        sp.update(coord=None)
        self.assertEqual(ax.get_xlabel(), 'exp')
        self.assertEqual(sp.plotters[0].plot_data[0].dims, ('exp', ))

        sp.update(coord='v3')
        self.assertEqual(ax.get_xlabel(), 'v3')
        self.assertEqual(sp.plotters[0].plot_data[0].dims, ('v3', ))

    def test_duplicates_density(self):
        ds = self._test_dataset
        sp = psy.plot.density(ds, name='v1', coord='v3', xlabel='%(name)s')
        ax = sp.plotters[0].ax
        self.assertEqual(ax.get_xlabel(), 'v3')
        self.assertEqual(sp.plotters[0].plot_data.dims, ('v1', 'v3'))

        sp.update(coord=None)
        self.assertEqual(ax.get_xlabel(), 'exp')
        self.assertEqual(sp.plotters[0].plot_data.dims, ('v1', 'exp'))

        sp.update(coord='v3')
        self.assertEqual(ax.get_xlabel(), 'v3')
        self.assertEqual(sp.plotters[0].plot_data.dims, ('v1', 'v3'))


class SingleLinePlotterTest(LinePlotterTest):
    """Test of :class:`psy_simple.plotters.LinePlotter` with a single array
    instead of an InteractiveList"""

    plot_type = 'singleline'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True)
        cls.data[0].psy.arr_name = 'arr0'
        cls.data.psy.arr_name = 'arr0'
        cls.plotter = LinePlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.lineplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs)

    @unittest.skip("No need for figure creation")
    def ref_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("Appending not possible for single line")
    def test_append_data(self):
        pass


class ViolinPlotterTest(LinePlotterTest):
    """Test class for :class:`psy_simple.plotters.BarPlotter`"""

    plot_type = 'violin'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True)
        cls.plotter = ViolinPlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.violinplot(
            self.ncfile, name=name, t=0, z=0, y=[0, 1], **kwargs)

    @unittest.skip("No need for figure creation")
    def ref_xticks(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_area(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
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

    @unittest.skip("seaborn changes colors")
    def test_append_data(self):
        pass

    @unittest.skip('Test needs to be implemented')
    def test_xticks(self, *args):
        """
        .. todo::

            Implement this test"""
        # TODO: implement this test
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_area(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_areax(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked_transposed(self, close=True):
        pass

    def test_color(self):
        pass

    @unittest.skip('Not implemented for ViolinPlotter')
    def test_coord(self):
        pass


class SingleViolinPlotterTest(ViolinPlotterTest):
    """Test of :class:`psy_simple.plotters.ViolinPlotter` with a single array
    instead of an InteractiveList"""

    plot_type = 'singleviolin'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True)
        cls.data[0].psy.arr_name = 'arr0'
        cls.data.psy.arr_name = 'arr0'
        cls.plotter = ViolinPlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.violinplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs)


class BarPlotterTest(LinePlotterTest):
    """Test class for :class:`psy_simple.plotters.BarPlotter`"""

    plot_type = 'bar'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True)
        cls.plotter = BarPlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.barplot(
            self.ncfile, name=name, t=0, z=0, y=[0, 1], **kwargs)

    @unittest.skip("No need for figure creation")
    def ref_xticks(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def ref_plot_area(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
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

    @unittest.skip("No need for figure creation")
    def test_plot_area(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_areax(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_None(self, *args):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked(self, close=True):
        pass

    @unittest.skip("No need for figure creation")
    def test_plot_stacked_transposed(self, close=True):
        pass

    def ref_plot(self, close=True):
        """Create the reference figure for the stacked plot"""
        sp = self.plot(plot='stacked')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('stacked')))
        sp2 = self.plot(plot='stacked', transpose=True)
        sp2.export(os.path.join(bt.ref_dir,
                                self.get_ref_file('stacked_transposed')))
        if close:
            sp.close(True, True, True)
            sp2.close(True, True, True)

    def test_plot(self, *args):
        """Test the stacked plot"""
        self.update(plot='stacked')
        self.compare_figures(next(iter(args), self.get_ref_file('stacked')))
        self.update(plot='stacked', transpose=True)
        self.compare_figures(next(iter(args),
                                  self.get_ref_file('stacked_transposed')))

    def test_xticks(self, *args):
        self._test_DtTicksBase()

    def _test_DtTicksBase(self, *args):
        data = InteractiveList.from_dataset(
            self.data[0].psy.base, y=[0, 1], z=0, x=0, name=self.var,
            auto_update=True)
        plotter = self.plotter.__class__(data)
        ax = plotter.ax
        plotter.update(xticklabels='%m')
        self.assertListEqual(ax.get_xticks().astype(int).tolist(),
                             list(range(5)))

    def test_color(self):
        colors = ['y', 'g'][:len(self.data)]
        current_colors = [
            c[0].get_facecolor() for c in self.plotter.ax.containers]
        self.update(color=colors)

        self.assertEqual(
            [c[0].get_facecolor() for c in self.plotter.ax.containers],
            list(map(mcol.colorConverter.to_rgba, colors)))
        self.update(color=None)
        self.assertEqual(
            [c[0].get_facecolor() for c in self.plotter.ax.containers],
            current_colors)

    def test_ylim(self):
        """Test ylim formatoption"""
        curr_lim = self.plotter.ax.get_ylim()
        self.update(ylim=(-1, 300))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, 300))
        self.update(ylim=(-1, 'rounded'))
        self.assertEqual(self.plotter.ax.get_ylim(), (-1, curr_lim[1]))
        self.update(ylim=(0, ["minmax", 75]))
        data = self.data.to_dataframe()
        arr = data[data.notnull()].values
        self.assertAlmostArrayEqual(self.plotter.ax.get_ylim(),
                                    [0, np.percentile(arr, 75)])


class BarPlotterDataTest(BarPlotterTest):
    """TestCase of :class:`psy_simple.plotters.BarPlotter` with widhts=='data'
    """

    plot_type = 'bar_data'

    @classmethod
    def setUpClass(cls):
        plotter = BarPlotter()
        rcParams[plotter.widths.default_key] = 'data'
        super(BarPlotterDataTest, cls).setUpClass()

    def test_ylim(self):
        """Test ylim formatoption"""
        LinePlotterTest.test_ylim(self)

    def _test_DtTicksBase(self, *args):
        LinePlotterTest._test_DtTicksBase(self, *args)

    def ref_xticks(self, close=True):
        """Create reference file for xticks formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.BarPlotter.xticks`
        formatoption"""
        sp = psy.plot.barplot(
            self.ncfile, name=self.var, lon=0, lev=0, lat=[0, 1],
            xticklabels={'major': '%m', 'minor': '%d'},
            xtickprops={'pad': 7.0},
            xticks={'minor': 'week', 'major': 'month'})
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('xticks')))
        if close:
            sp.close(True, True)


class SingleBarPlotterTest(BarPlotterTest):
    """Test of :class:`psy_simple.plotters.ViolinPlotter` with a single array
    instead of an InteractiveList"""

    plot_type = 'singlebar'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True)
        cls.data[0].psy.arr_name = 'arr0'
        cls.data.psy.arr_name = 'arr0'
        cls.plotter = BarPlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.barplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs)

    @unittest.skip("""Not possible for single array""")
    def test_plot(self, *args):
        pass

    @unittest.skip("Appending not possible for single line")
    def test_append_data(self):
        pass


class References2D(object):
    """abstract base class that defines reference methods for 2D plotter"""

    def ref_datagrid(self, close=True):
        """Create reference file for datagrid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.datagrid`
        formatoption"""
        kwargs = dict(xlim=(0, 40), ylim=(0, 40))
        sp = self.plot(**kwargs)
        sp.update(datagrid='k-')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('datagrid')))
        if close:
            sp.close(True, True)

    def ref_cmap(self, close=True):
        """Create reference file for cmap formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cmap`
        formatoption"""
        sp = self.plot(cmap='RdBu')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('cmap')))
        if close:
            sp.close(True, True)

    def ref_cbar(self, close=True):
        """Create reference file for cbar formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cbar`
        formatoption"""
        sp = self.plot(cbar=['fb', 'fr', 'fl', 'ft', 'b', 'r'])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('cbar')))
        if close:
            sp.close(True, True)

    def ref_miss_color(self, close=True):
        """Create reference file for miss_color formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.miss_color`
        formatoption"""
        if self.plot_type[:3] == 'map':
            kwargs = {'projection': 'ortho', 'grid_labels': False}
        else:
            kwargs = {}
        sp = self.plot(maskless=280, miss_color='0.9', **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('miss_color')))
        if close:
            sp.close(True, True)

    def ref_cbarspacing(self, close=True):
        """Create reference file for cbarspacing formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.cbarspacing`
        formatoption"""
        if self.plot_type.endswith('vector') or getattr(self, 'vector_mode',
                                                        False):
            kwargs = dict(
                bounds=np.arange(0, 1.45, 0.1).tolist() + np.linspace(
                    1.5, 13.5, 7, endpoint=True).tolist() + np.arange(
                        13.6, 15.05, 0.1).tolist(), color='absolute')
        else:
            kwargs = dict(bounds=list(range(235, 250)) + np.linspace(
                250, 295, 7, endpoint=True).tolist() + list(range(296, 310)))
        sp = self.plot(
            cbarspacing='proportional', cticks='rounded',
            **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('cbarspacing')))
        if close:
            sp.close(True, True)


class Simple2DPlotterTest(LinePlotterTest, References2D):
    """Test :class:`psyplot.plotter.maps.Simple2DPlotter` class"""

    plot_type = 'simple2D'

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.plot2d(self.ncfile, name=name, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=cls.var, auto_update=True)[0]
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

    @unittest.skip('Not implemented for 2D-Plotter')
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
        self.update(ylabel='{desc}')
        label = self.plotter.ax.yaxis.get_label()
        self.assertEqual(label.get_text(), 'latitude [degrees_north]')
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_xticks(self):
        """Test xticks formatoption"""
        self._test_DataTicksCalculator()

    def test_extend(self):
        """Test extend formatoption"""
        self.update(extend='both')
        self.assertEqual(self.plotter.cbar.cbars['b'].extend, 'both')
        self.update(extend='min')
        self.assertEqual(self.plotter.cbar.cbars['b'].extend, 'min')
        self.update(extend='neither')
        self.assertEqual(self.plotter.cbar.cbars['b'].extend, 'neither')

    def test_legend(self):
        pass

    def test_cticks(self):
        """Test cticks, cticksize, ctickweight, ctickprops formatoptions"""
        cticks = self._minmax_cticks
        self.update(cticks='minmax')
        cbar = self.plotter.cbar.cbars['b']
        self.assertEqual(list(map(
            lambda t: float(t.get_text()), cbar.ax.get_xticklabels())), cticks)
        self.update(cticklabels='%3.1f')
        cticks = np.round(cticks, decimals=1).tolist()
        self.assertAlmostArrayEqual(list(map(
            lambda t: float(t.get_text()), cbar.ax.get_xticklabels())), cticks,
            atol=0.1)
        self.update(cticksize=20, ctickweight=bold, ctickprops={
            'labelcolor': 'r'})
        texts = cbar.ax.get_xticklabels()
        n = len(texts)
        self.assertEqual([t.get_weight() for t in texts], [bold] * n)
        self.assertEqual([t.get_size() for t in texts], [20] * n)
        self.assertEqual([t.get_color() for t in texts], ['r'] * n)

    @property
    def _minmax_cticks(self):
        return np.round(
            np.linspace(self.data.values.min(), self.data.values.max(), 11,
                        endpoint=True), decimals=2).tolist()

    def test_clabel(self):
        """Test clabel, clabelsize, clabelweight, clabelprops formatoptions"""
        def get_clabel():
            return self.plotter.cbar.cbars['b'].ax.xaxis.get_label()
        self._label_test('clabel', get_clabel)
        label = get_clabel()
        self.update(clabelsize=22, clabelweight='bold',
                    clabelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_datagrid(self, *args):
        """Test datagrid formatoption"""
        self.update(xlim=(0, 40), ylim=(0, 40), datagrid='k-')
        self.compare_figures(next(iter(args), self.get_ref_file('datagrid')))

    def test_cmap(self, *args):
        """Test colormap (cmap) formatoption"""
        self.update(cmap='RdBu')
        fname = next(iter(args), self.get_ref_file('cmap'))
        self.compare_figures(fname)
        self.update(cmap=plt.get_cmap('RdBu'))
        self.compare_figures(fname)

    def test_cbar(self, *args):
        """Test colorbar (cbar) formatoption"""
        self.update(cbar=['fb', 'fr', 'fl', 'ft', 'b', 'r'])
        self.compare_figures(next(iter(args), self.get_ref_file('cbar')))

    def test_bounds(self):
        """Test bounds formatoption"""
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(235, 310, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [239.91, 246.89, 253.88, 260.87, 267.86, 274.84, 281.83,
                  288.82, 295.81, 302.79, 309.78]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(245, 300, 5, endpoint=True).tolist())

    def test_miss_color(self, *args):
        """Test miss_color formatoption"""
        self.update(maskless=280, miss_color='0.9')
        self.compare_figures(next(iter(args), self.get_ref_file('miss_color')))

    def test_cbarspacing(self, *args):
        """Test cbarspacing formatoption"""
        self.update(
            cbarspacing='proportional', cticks='rounded',
            bounds=list(range(235, 250)) + np.linspace(
                250, 295, 7, endpoint=True).tolist() + list(range(296, 310)))
        self.compare_figures(next(iter(args),
                                  self.get_ref_file('cbarspacing')))

    def test_ylim(self):
        """Test ylim formatoption"""
        super(Simple2DPlotterTest, self).test_ylim(test_pctls=False)


@pytest.mark.parametrize('vmin,vmax', [(1, int(1e2)), (int(-10), int(1e2))])
def test_log_bounds(vmin, vmax):
    ds = xr.Dataset()
    ds['test'] = (('y', 'x'), np.random.randint(vmin, vmax, (40, 50)) * 1e-3)
    vmin *= 10e-3
    vmax *= 10e-3
    ds['x'] = ('x', np.arange(50))
    ds['y'] = ('y', np.arange(40))

    sp = ds.psy.plot.plot2d(bounds='log')
    plotter = sp.plotters[0]

    assert len(plotter.bounds.norm.boundaries) in [10, 11, 12]
    assert np.isclose(plotter.bounds.norm.boundaries[0],
                      [vmin, vmin * 0.1, vmin*10]).any()
    assert np.isclose(plotter.bounds.norm.boundaries[-1],
                      [vmax, vmax * 0.1, vmax * 10]).any()


def test_symlog_bounds():
    vmin = -1
    vmax = 100
    ds = xr.Dataset()
    ds['test'] = (('y', 'x'), np.random.randint(vmin, vmax, (40, 50)) * 1e-3)
    vmin *= 10e-3
    vmax *= 10e-3
    ds['x'] = ('x', np.arange(50))
    ds['y'] = ('y', np.arange(40))

    sp = ds.psy.plot.plot2d(bounds='symlog')
    plotter = sp.plotters[0]

    assert len(plotter.bounds.norm.boundaries) in [12, 13, 14]
    assert plotter.bounds.norm.boundaries[0] == pytest.approx(-0.1)
    assert plotter.bounds.norm.boundaries[-1] == pytest.approx(0.1)


class Simple2DPlotterContourTest(Simple2DPlotterTest):

    plot_type = 'simple2D_contour'

    @classmethod
    def setUpClass(cls):
        plotter = Simple2DPlotter()
        rcParams[plotter.plot.default_key] = 'contourf'
        super(Simple2DPlotterContourTest, cls).setUpClass()

    @unittest.skip('Extend keyword not implemented')
    def test_extend(self):
        pass

    @unittest.skip('miss_color keyword not implemented')
    def test_miss_color(self):
        pass

    @unittest.skip('miss_color keyword not implemented')
    def ref_miss_color(self):
        pass


class Simple2DPlotterTestArtificial(unittest.TestCase):
    """A test case for artifial data"""

    def test_single_level(self):
        """Test the case when all the data contains exactly one value"""
        ds = xr.Dataset()
        ds['test'] = (('y', 'x'), np.ones((4, 5)))
        sp = ds.psy.plot.plot2d(cmap='Reds', bounds=['rounded', 3])
        self.assertEqual(list(sp.plotters[0].bounds.bounds), [1., 1., 1.])


class IconTestMixin(object):
    """A mixin class for changed test methods for icon"""

    def ref_datagrid(self, close=True):
        """Create reference file for datagrid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.datagrid`
        formatoption"""
        sp = self.plot()
        sp.update(datagrid='k-')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('datagrid')))
        if close:
            sp.close(True, True)

    def test_datagrid(self, *args):
        """Test datagrid formatoption"""
        self.update(datagrid='k-')
        self.compare_figures(next(iter(args), self.get_ref_file('datagrid')))

    def test_xlabel(self):
        """Test xlabel formatoption"""
        self.update(xlabel='{desc}')
        label = self.plotter.ax.xaxis.get_label()
        self.assertIn('longitude [radian]', label.get_text())
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_ylabel(self):
        """Test ylabel formatoption"""
        self.update(ylabel='{desc}')
        label = self.plotter.ax.yaxis.get_label()
        self.assertIn('latitude [radian]', label.get_text())
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

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

        self.update(xticks='rounded')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-3, 3.5, 11, endpoint=True).tolist())
        self.update(xticks='roundedsym')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-3.5, 3.5, 10, endpoint=True).tolist())
        self.update(xticks='minmax')
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                lon.min(), lon.max(),
                11, endpoint=True).tolist())
        self.update(xticks='sym')
        vmax = np.abs(lon).max()
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                -vmax, vmax,
                10, endpoint=True).tolist())


class IconSimplePlotterTest(IconTestMixin, Simple2DPlotterTest):
    """Test :class:`psy_simple.plotters.Simple2DPlotter` class for icon grid"""

    grid_type = 'icon'

    masking_val = 280

    ncfile = os.path.join(bt.test_dir, 'icon_test.nc')

    def test_bounds(self):
        """Test bounds formatoption"""
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(240, 310, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [243.76, 250.04, 256.31, 262.58, 268.85, 275.12, 281.39,
                  287.66, 293.94, 300.21, 306.48]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(255, 305, 5, endpoint=True).tolist())


class IconEdgeSimplePlotterTest(IconTestMixin, Simple2DPlotterTest):
    """Icon edge grid test :class:`psy_simple.plotters.Simple2DPlotter` class
    """

    grid_type = 'icon_edge'

    masking_val = 280

    ncfile = os.path.join(bt.test_dir, 'icon_edge_test.nc')

    def test_bounds(self):
        """Test bounds formatoption"""
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(240, 310, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [242.48, 249.06, 255.64, 262.21, 268.79, 275.37, 281.94,
                  288.52, 295.1, 301.67, 308.25]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(255, 305, 5, endpoint=True).tolist())


class IconSimplePlotterContourTest(IconSimplePlotterTest):

    plot_type = 'icon_contour'

    @classmethod
    def setUpClass(cls):
        plotter = Simple2DPlotter()
        rcParams[plotter.plot.default_key] = 'contourf'
        super(IconSimplePlotterContourTest, cls).setUpClass()

    @unittest.skip('Extend keyword not implemented')
    def test_extend(self):
        pass

    @unittest.skip('miss_color keyword not implemented')
    def test_miss_color(self):
        pass

    @unittest.skip('miss_color keyword not implemented')
    def ref_miss_color(self):
        pass

    @unittest.skip('nan not supported for icon contour')
    def test_mask_01_var(self):
        pass

    @unittest.skip('nan not supported for icon contour')
    def test_mask_02_da(self):
        pass

    @unittest.skip('nan not supported for icon contour')
    def test_mask_03_fname(self):
        pass


class LinePlotterTest2D(tb.TestBase2D, LinePlotterTest):
    """Test :class:`psy_simple.plotters.LinePlotter` class without
    time and vertical dimension"""

    var = 't2m_2d'

    def test_xticks(self, *args):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self._test_DataTicksCalculator()

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord='v_2d', xlabel='%(name)s')
        self.assertEqual(self.plotter.ax.get_xlabel(), 'v_2d',
                         msg='Did not update to the right coordinate!')


class Simple2DPlotterTest2D(tb.TestBase2D, Simple2DPlotterTest):
    """Test :class:`psy_simple.plotters.Simple2DPlotter` class without
    time and vertical dimension"""

    var = 't2m_2d'


class SimpleVectorPlotterTest(Simple2DPlotterTest):
    """Test :class:`psyplot.plotter.maps.SimpleVectorPlotter` class"""

    plot_type = 'simplevector'

    var = ['u', 'v']

    def plot(self, **kwargs):
        kwargs.setdefault('color', 'absolute')
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault('t', ds.time.values[0])
        kwargs.setdefault('z', ds.lev.values[0])
        kwargs.setdefault('x', slice(0, 69.0))
        kwargs.setdefault('y', slice(81.0, 34.0))
        kwargs.setdefault('method', 'sel')
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
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('arrowsize')))
        if close:
            sp.close(True, True)

    def ref_datagrid(self, close=True):
        """Create reference file for datagrid formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.Simple2DPlotter.datagrid`
        formatoption"""
        sp = self.plot()
        sp.update(datagrid='k-')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('datagrid')))
        if close:
            sp.close(True, True)

    def test_datagrid(self, *args):
        """Test datagrid formatoption"""
        self.update(datagrid='k-')
        self.compare_figures(next(iter(args), self.get_ref_file('datagrid')))

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True)[0]
        cls.data = cls.data.psy.sel(lon=slice(0, 69.0), lat=slice(81.0, 34.0))
        cls.data.attrs['long_name'] = 'absolute wind speed'
        cls.data.name = 'wind'
        plotter = SimpleVectorPlotter()
        rcParams[plotter.color.default_key] = 'absolute'
        cls.plotter = SimpleVectorPlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups['colors']

    def update(self, *args, **kwargs):
        kwargs.setdefault('color', 'absolute')
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
            cbarspacing='proportional', cticks='rounded', color='absolute',
            bounds=np.arange(0, 1.45, 0.1).tolist() + np.linspace(
                    1.5, 13.5, 7, endpoint=True).tolist() + np.arange(
                        13.6, 15.05, 0.1).tolist())
        self.compare_figures(next(iter(args),
                                  self.get_ref_file('cbarspacing')))

    @unittest.skipIf(
        six.PY34, "The axes size changes using the arrowsize formatoption")
    def test_arrowsize(self, *args):
        """Test arrowsize formatoption"""
        self.update(arrowsize=100.0)
        self.compare_figures(next(iter(args), self.get_ref_file('arrowsize')))

    _max_rounded_ref = 70

    @property
    def _minmax_cticks(self):
        speed = (self.plotter.plot_data.values[0]**2 +
                 self.plotter.plot_data.values[1]**2) ** 0.5
        speed = speed[~np.isnan(speed)]
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True),
            decimals=2).tolist()

    def test_bounds(self):
        """Test bounds formatoption"""
        self.update(color='absolute')
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [0.36, 1.4, 2.45, 3.49, 4.54, 5.59, 6.63, 7.68, 8.72, 9.77,
                  10.81]

        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 3).tolist(),
            np.linspace(1.0, 8.5, 5, endpoint=True).tolist())


class SimpleStreamVectorPlotterTest(SimpleVectorPlotterTest):
    """Test case for stream plot of
    :class:`psy_simple.plotters.SimpleVectorPlotter`
    """

    @classmethod
    def setUpClass(cls):
        plotter = SimpleVectorPlotter()
        rcParams[plotter.plot.default_key] = 'stream'
        return super(SimpleStreamVectorPlotterTest, cls).setUpClass()

    def get_ref_file(self, identifier):
        return super(SimpleStreamVectorPlotterTest, self).get_ref_file(
            identifier + '_stream')

    def ref_arrowsize(self, *args):
        """Create reference file for arrowsize formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.arrowsize` (and others)
        formatoption"""
        sp = self.plot(arrowsize=2.0)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('arrowsize')))

    def ref_arrowstyle(self, *args):
        """Create reference file for arrowstyle formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.arrowstyle` (and
        others) formatoption"""
        sp = self.plot(arrowsize=2.0, arrowstyle='fancy')
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('arrowstyle')))

    def test_arrowsize(self, *args):
        """Test arrowsize formatoption"""
        self.update(arrowsize=2.0)
        self.compare_figures(next(iter(args), self.get_ref_file('arrowsize')))

    def test_arrowstyle(self, *args):
        """Test arrowstyle formatoption"""
        self.update(arrowsize=2.0, arrowstyle='fancy')
        self.compare_figures(next(iter(args), self.get_ref_file('arrowstyle')))

    def ref_density(self, *args):
        """Create reference file for density formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.density` (and others)
        formatoption"""
        sp = self.plot(density=0.5)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('density')))

    def test_density(self, *args):
        """Test density formatoption"""
        self.update(density=0.5)
        self.compare_figures(next(iter(args), self.get_ref_file('density')))


class IconSimpleVectorPlotterTest(IconTestMixin, SimpleVectorPlotterTest):
    """
    Test :class:`psy_simple.plotters.SimpleVectorPlotter` class for icon grid
    """

    grid_type = 'icon'

    ncfile = os.path.join(bt.test_dir, 'icon_test.nc')

    @classmethod
    def setUpClass(cls):
        plotter = SimpleVectorPlotter()
        rcParams[plotter.color.default_key] = 'absolute'
        cls.ds = open_dataset(cls.ncfile)
        cls.data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True)[0]
        cls.data.attrs['long_name'] = 'absolute wind speed'
        cls.data.name = 'wind'
        cls.plotter = SimpleVectorPlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups['colors']

    def plot(self, **kwargs):
        kwargs.setdefault('color', 'absolute')
        ds = psy.open_dataset(self.ncfile)
        sp = psy.plot.vector(ds, name=[self.var], **kwargs)
        return sp

    def test_bounds(self):
        """Test bounds formatoption"""
        self.update(color='absolute')
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [0.08, 1.18, 2.28, 3.38, 4.48, 5.59, 6.69, 7.79, 8.89, 9.99,
                  11.09]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.round(np.linspace(0.5, 9.0, 5, endpoint=True), 2).tolist())


def _do_from_both(func):
    """Call the given `func` only from :class:`Simple2DPlotterTest` and
    :class:`SimpleVectorPlotterTest`"""
    func.__doc__ = getattr(SimpleVectorPlotterTest, func.__name__).__doc__

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        getattr(Simple2DPlotterTest, func.__name__)(self, *args, **kwargs)
        if hasattr(self, 'plotter'):
            self.plotter.update(todefault=True)
        with self.vector_mode:
            getattr(SimpleVectorPlotterTest, func.__name__)(
                self, *args, **kwargs)

    return wrapper


def _in_vector_mode(func):
    """Call the given `func` only from :class:`SimpleVectorPlotterTest`"""
    func.__doc__ = getattr(SimpleVectorPlotterTest, func.__name__).__doc__

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.vector_mode:
            getattr(SimpleVectorPlotterTest, func.__name__)(
                self, *args, **kwargs)

    return wrapper


class _CombinedPlotterData(object):
    """Descriptor that returns the data"""
    # Note: We choose to use a descriptor rather than a usual property because
    # it shall also work for class objects and not only instances

    def __get__(self, instance, owner):
        if instance is None:
            return owner._data
        if instance.vector_mode:
            return instance._data[1]
        return instance._data[0]

    def __set__(self, instance, value):
        instance._data = value


class CombinedSimplePlotterTest(SimpleVectorPlotterTest):
    """Test case for vector plot of
    :class:`psy_simple.plotters.CombinedSimplePlotter`"""

    plot_type = 'simplecombined'

    data = _CombinedPlotterData()

    var = ['t2m', ['u', 'v']]

    @property
    def vector_mode(self):
        """:class:`bool` indicating whether a vector specific formatoption is
        tested or not"""
        try:
            return self._vector_mode
        except AttributeError:
            self._vector_mode = _TempBool(False)
            return self._vector_mode

    @vector_mode.setter
    def vector_mode(self, value):
        self.vector_mode.value = bool(value)

    def compare_figures(self, fname, **kwargs):
        kwargs.setdefault('tol', 10)
        return super(CombinedSimplePlotterTest, self).compare_figures(
            fname, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        plotter = CombinedSimplePlotter()
        rcParams[plotter.vcmap.default_key] = 'winter'
        cls._data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True,
            prefer_list=True)[0]
        for i in range(len(cls.data)):
            cls._data[i] = cls._data[i].psy.sel(lon=slice(0, 69.0),
                                                lat=slice(81.0, 34.0))
        cls._data.attrs['long_name'] = 'Temperature'
        cls._data.attrs['name'] = 't2m'
        cls.plotter = CombinedSimplePlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups['colors']

        # there is an issue with the colorbar that the size of the axes changes
        # slightly after replotting. Therefore we force a replot here
        cls.plotter.update(color='absolute')
        cls.plotter.update(todefault=True, replot=True)

    def tearDown(self):
        self._data.psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        color_fmts = psy.plot.vector.plotter_cls().fmt_groups['colors']
        fix_colorbar = not color_fmts.intersection(kwargs)
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault('t', ds.time.values[0])
        kwargs.setdefault('z', ds.lev.values[0])
        kwargs.setdefault('x', slice(0, 69.0))
        kwargs.setdefault('y', slice(81.0, 34.0))
        kwargs.setdefault('method', 'sel')
        kwargs.setdefault('color', 'absolute')
        if self.vector_mode:
            kwargs = self._rename_fmts(kwargs)
        sp = psy.plot.combined(ds, name=[self.var], **kwargs)
        if not self.vector_mode or fix_colorbar:
            # if we have no color formatoptions, we have to consider that
            # the position of the plot may have slighty changed
            sp.update(todefault=True, replot=True, **dict(
                item for item in kwargs.items() if item[0] != 'color'))
        return sp

    def _rename_fmts(self, kwargs):
        def check_key(key):
            if not any(re.match('v' + key, fmt) for fmt in vcolor_fmts):
                return key
            else:
                return 'v' + key
        vcolor_fmts = {
            fmt for fmt in chain(
                psy.plot.combined.plotter_cls().fmt_groups['colors'],
                ['ctick|clabel']) if fmt.startswith('v')}
        return {check_key(key): val for key, val in kwargs.items()}

    def update(self, *args, **kwargs):
        if self.vector_mode and (
                self._color_fmts.intersection(kwargs) or any(
                    re.match('ctick|clabel', fmt) for fmt in kwargs)):
            kwargs.setdefault('color', 'absolute')
            kwargs = self._rename_fmts(kwargs)
        super(SimpleVectorPlotterTest, self).update(*args, **kwargs)

    def get_ref_file(self, identifier):
        if self.vector_mode:
            identifier += '_vector'
        return super(CombinedSimplePlotterTest, self).get_ref_file(identifier)

    @property
    def _minmax_cticks(self):
        if not self.vector_mode:
            return np.round(
                np.linspace(self.plotter.plot_data[0].values.min(),
                            self.plotter.plot_data[0].values.max(), 11,
                            endpoint=True), decimals=2).tolist()
        speed = (self.plotter.plot_data[1].values[0]**2 +
                 self.plotter.plot_data[1].values[1]**2) ** 0.5
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True),
            decimals=2).tolist()

    @_do_from_both
    def ref_cbar(self, close=True):
        pass

    def ref_cbarspacing(self, close=True):
        """Create reference file for cbarspacing formatoption"""
        kwargs = dict(bounds=list(range(245, 255)) + np.linspace(
                255, 280, 6, endpoint=True).tolist() + list(range(281, 290)))
        sp = self.plot(
            cbarspacing='proportional', cticks='rounded',
            **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('cbarspacing')))
        with self.vector_mode:
            SimpleVectorPlotterTest.ref_cbarspacing(self, close=close)
        if close:
            sp.close(True, True)

    @_do_from_both
    def ref_cmap(self, close=True):
        pass

    def ref_miss_color(self, close=True):
        Simple2DPlotterTest.ref_miss_color(self, close)

    @_in_vector_mode
    def ref_arrowsize(self, *args, **kwargs):
        pass

    def _label_test(self, key, label_func, has_time=True):
        kwargs = {
            key: "Test plot at %Y-%m-%d, {tinfo} o'clock of %(long_name)s"}
        self.update(**kwargs)
        t_str = '1979-01-31, 18:00' if has_time else '%Y-%m-%d, %H:%M'
        self.assertEqual(
            u"Test plot at %s o'clock of %s" % (
                t_str, self.data.attrs.get('long_name', 'Temperature')),
            label_func().get_text())
        self._data.psy.update(t=1)
        t_str = '1979-02-28, 18:00' if has_time else '%Y-%m-%d, %H:%M'
        self.assertEqual(
            u"Test plot at %s o'clock of %s" % (
                t_str, self.data.attrs.get('long_name', 'Temperature')),
            label_func().get_text())
        self._data.psy.update(t=0)

    def test_miss_color(self, *args, **kwargs):
        Simple2DPlotterTest.test_miss_color(self, *args, **kwargs)

    @_do_from_both
    def test_cbar(self, *args, **kwargs):
        pass

    def test_cbarspacing(self, *args, **kwargs):
        """Test cbarspacing formatoption"""
        self.update(
            cbarspacing='proportional', cticks='rounded',
            bounds=list(range(245, 255)) + np.linspace(
                255, 280, 6, endpoint=True).tolist() + list(range(281, 290)))
        self.compare_figures(next(iter(args),
                                  self.get_ref_file('cbarspacing')))
        self.plotter.update(todefault=True)
        with self.vector_mode:
            SimpleVectorPlotterTest.test_cbarspacing(self, *args, **kwargs)

    @_do_from_both
    def test_cmap(self, *args, **kwargs):
        pass

    @unittest.skipIf(
        six.PY34, "The axes size changes using the arrowsize formatoption")
    @_in_vector_mode
    def test_arrowsize(self):
        pass

    def test_bounds(self):
        """Test bounds formatoption"""
        # test bounds of scalar field
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(250, 290, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [251.73, 255.54, 259.35, 263.16, 266.97, 270.78, 274.59,
                  278.4, 282.22, 286.03, 289.84]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(250, 290, 5, endpoint=True).tolist())

        # test vector bounds
        self.update(color='absolute')
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist())
        self.update(vbounds='minmax')
        bounds = [0.36, 1.4, 2.45, 3.49, 4.54, 5.59, 6.63, 7.68, 8.72, 9.77,
                  10.81]
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(), bounds)
        self.update(vbounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 3).tolist(),
            np.linspace(1.0, 8.5, 5, endpoint=True).tolist())

    def test_clabel(self):
        def get_clabel():
            return self.plotter.vcbar.cbars['b'].ax.xaxis.get_label()
        Simple2DPlotterTest.test_clabel(self)
        with self.vector_mode:
            self.update(color='absolute')
            self._label_test('vclabel', get_clabel)
            label = get_clabel()
            self.update(vclabelsize=22, vclabelweight='bold',
                        vclabelprops={'ha': 'left'})
            self.assertEqual(label.get_size(), 22)
            self.assertEqual(label.get_weight(), bold)
            self.assertEqual(label.get_ha(), 'left')


class CombinedSimplePlotterTest2D(tb.TestBase2D, CombinedSimplePlotterTest):
    """Test :class:`psy_simple.plotters.CombinedSimplePlotter` class without
    time and vertical dimension"""

    var = ['t2m', ['u_2d', 'v_2d']]

    def _label_test(self, key, label_func, has_time=None):
        if has_time is None:
            has_time = not bool(self.vector_mode)
        CombinedSimplePlotterTest._label_test(
            self, key, label_func, has_time=has_time)


class IconCombinedSimplePlotterTest(IconTestMixin, CombinedSimplePlotterTest):
    """Test :class:`psy_simple.plotters.CombinedSimplePlotter` class for icon
    grid
    """

    grid_type = 'icon'

    ncfile = os.path.join(bt.test_dir, 'icon_test.nc')

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        plotter = CombinedSimplePlotter()
        rcParams[plotter.vcmap.default_key] = 'winter'
        cls._data = ArrayList.from_dataset(
            cls.ds, t=0, z=0, name=[cls.var], auto_update=True,
            prefer_list=True)[0]
        cls._data.attrs['long_name'] = 'Temperature'
        cls._data.attrs['name'] = 't2m'
        cls.plotter = CombinedSimplePlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups['colors']

        # there is an issue with the colorbar that the size of the axes changes
        # slightly after replotting. Therefore we force a replot here
        cls.plotter.update(color='absolute')
        cls.plotter.update(todefault=True, replot=True)

    def plot(self, **kwargs):
        color_fmts = psy.plot.vector.plotter_cls().fmt_groups['colors']
        fix_colorbar = not color_fmts.intersection(kwargs)
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault('color', 'absolute')
        if self.vector_mode:
            kwargs = self._rename_fmts(kwargs)
        sp = psy.plot.combined(ds, name=[self.var], **kwargs)
        if not self.vector_mode or fix_colorbar:
            # if we have no color formatoptions, we have to consider that
            # the position of the plot may have slighty changed
            sp.update(todefault=True, replot=True, **dict(
                item for item in kwargs.items() if item[0] != 'color'))
        return sp

    @unittest.skip("Density for quiver plots of unstructered data is not "
                   "supported!")
    def ref_density(self):
        pass

    @unittest.skip("Density for quiver plots of unstructered data is not "
                   "supported!")
    def test_density(self):
        pass

    def test_bounds(self):
        """Test bounds formatoption"""
        # test bounds of scalar field
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(240, 310, 11, endpoint=True).tolist())
        self.update(bounds='minmax')
        bounds = [243.76, 250.04, 256.31, 262.58, 268.85, 275.12, 281.39,
                  287.66, 293.94, 300.21, 306.48]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds)
        self.update(bounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(255, 305, 5, endpoint=True).tolist())

        # test vector bounds
        self.update(color='absolute')
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist())
        self.update(vbounds='minmax')
        bounds = [0.08, 1.18, 2.28, 3.38, 4.48, 5.59, 6.69, 7.79, 8.89, 9.99,
                  11.09]
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(), bounds)
        self.update(vbounds=['rounded', 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.round(np.linspace(0.5, 9.0, 5, endpoint=True), 2).tolist())


    @property
    def _minmax_cticks(self):
        if not self.vector_mode:
            arr = self.plotter.plot_data[0].values
            arr = arr[~np.isnan(arr)]
            return np.round(
                np.linspace(arr.min(), arr.max(), 11, endpoint=True),
                decimals=2).tolist()
        arr = self.plotter.plot_data[1].values
        speed = (arr[0]**2 + arr[1]**2) ** 0.5
        speed = speed[~np.isnan(speed)]
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True),
            decimals=2).tolist()


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
        '''Update the plotter of this test case'''
        cls.plotter.update(**kwargs)

    @property
    def plot_data(self):
        return self.plotter.plot_data

    @classmethod
    def define_data(cls, mean=[0, 0], cov=[[10, 0], [0, 10]]):
        import numpy as np
        import pandas as pd
        import xarray as xr
        x, y = np.random.multivariate_normal(mean, cov, 5000).T
        df = pd.DataFrame(y, columns=['y'], index=pd.Index(x, name='x'))
        ds = xr.Dataset.from_dataframe(df)
        ds['v'] = xr.Variable(('x', ), x)
        ret = xr.DataArray(ds.y)
        ret.psy.init_accessor(base=ds)
        return ret

    def test_bins(self):
        '''Test the bins formatoption'''
        bins = [100, 10]
        self.update(bins=bins)
        self.assertEqual(len(self.plot_data.x), 100)
        self.assertEqual(len(self.plot_data.y), 10)

    def test_xrange(self):
        '''Test the xrange formatoption'''
        data = self.data
        xrange = np.percentile(data.x.values, [25, 75])
        self.update(xrange=xrange)
        self.assertGreaterEqual(self.plot_data.x.min(), xrange[0])
        self.assertLessEqual(self.plot_data.x.max(), xrange[1])

        # now update to use the quantiles explicitely
        self.update(xrange=(['minmax', 25], ['minmax', 75]))
        self.assertGreaterEqual(self.plot_data.x.min(), xrange[0])
        self.assertLessEqual(self.plot_data.x.max(), xrange[1])

    def test_yrange(self):
        '''Test the yrange formatoption'''
        data = self.data
        yrange = np.percentile(data.values, [25, 75])
        self.update(yrange=yrange)
        self.assertGreaterEqual(self.plot_data.y.min(), yrange[0])
        self.assertLessEqual(self.plot_data.y.max(), yrange[1])

        # now update to use the quantiles explicitely
        self.update(yrange=(['minmax', 25], ['minmax', 75]))
        self.assertGreaterEqual(self.plot_data.y.min(), yrange[0])
        self.assertLessEqual(self.plot_data.y.max(), yrange[1])

    def test_normed(self):
        '''Test the normed formatoption'''
        self.update(normed='counts')
        data = self.plot_data
        self.assertAlmostEqual(data.values.sum(), 1.0)

        self.update(normed='area')
        data = self.plot_data
        a0, a1 = data.x.values[:2]
        b0, b1 = data.y.values[:2]
        area = ((a1 - a0) * (b1 - b0))
        self.assertAlmostEqual((self.plot_data.values * area).sum(),
                               1.0)

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord='v', xlabel='%(name)s')
        self.assertEqual(self.plotter.ax.get_xlabel(), 'v',
                         msg='Did not update to the right coordinate!')


class DensityPlotterTestKDE(DensityPlotterTest):
    """Test of the :class:`psy_simple.plotters.DensityPlotter` class
    with kde plot"""

    @classmethod
    def setUpClass(cls):
        plotter = DensityPlotter()
        rcParams[plotter.density.default_key] = 'kde'
        super(DensityPlotterTestKDE, cls).setUpClass()

    @unittest.skip('Not implemented for KDE plots!')
    def test_normed(self):
        pass


class FldmeanPlotterTest(LinePlotterTest):
    """Test of the :class:`psy_simple.plotters.FldmeanPlotter` class"""

    plot_type = 'fldmean'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, t=[0, 1], name=cls.var, auto_update=True)
        cls.plotter = FldmeanPlotter(cls.data)
        cls.create_dirs()

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.fldmean(
            self.ncfile, name=name, t=[0, 1], **kwargs)

    @classmethod
    def tearDown(cls):
        cls.data.psy.update(todefault=True, replot=True)

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        coord = xr.DataArray(np.arange(len(self.data[0])), name='test',
                             dims=('test', ))
        self.update(coord=coord, xlabel='%(name)s')
        self.assertEqual(self.plotter.ax.get_xlabel(), 'test',
                         msg='Did not update to the right coordinate!')

    def _label_test(self, key, label_func, has_time=False):
        kwargs = {key: "Test plot for %(name)s"}
        self.update(**kwargs)
        self.assertEqual(
            label_func().get_text(),
            u"Test plot for " + self.var)

    def test_legend(self, *args):
        """Test legend and legendlabels formatoption"""
        args = iter(args)
        self.update(legend=False)
        self.assertIsNone(self.plotter.ax.legend_)
        self.update(legend={
            'loc': 'upper center', 'bbox_to_anchor': (0.5, -0.05), 'ncol': 2})
        self.compare_figures(next(args, self.get_ref_file('legend')))
        self.update(legendlabels='%m')
        self.assertAlmostArrayEqual(
            [float(t.get_text()) for t in plt.gca().legend_.get_texts()],
            [da.expand_dims('time').time.to_index().month[0]
             for da in self.data])

    def test_xticks(self):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self.update(xticks=['data', 2])
        ax = plt.gca()
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data

        lev = data.lev.values[::-1]

        self.assertEqual(list(ax.get_xticks()),
                         list(lev[::2]))
        self.update(xticks=['mid', 2])

        self.assertEqual(
            list(ax.get_xticks()), list(
                (lev[:-1] + lev[1:]) / 2.)[::2])
        self.update(xticks='rounded')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(20000.0, 100000.0, 11, endpoint=True).tolist())
        self.update(xticks='roundedsym')
        self.assertEqual(
            list(ax.get_xticks()),
            np.linspace(-100000, 100000, 10, endpoint=True).tolist())
        self.update(xticks='minmax')
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                lev.min(), lev.max(),
                11, endpoint=True).tolist())
        self.update(xticks='sym')
        self.assertEqual(
            list(ax.get_xticks()), np.linspace(
                -lev.max(), lev.max(),
                10, endpoint=True).tolist())

    def test_ticksize(self):
        """Tests ticksize formatoption"""
        self.update(ticksize=24)
        ax = self.plotter.ax
        self.assertTrue(all(t.get_size() == 24 for t in chain(
            ax.get_xticklabels(), ax.get_yticklabels())))
        self.update(
            ticksize={'major': 12, 'minor': 10}, xtickprops={'pad': 7.0})
        self.assertTrue(all(t.get_size() == 12 for t in chain(
            ax.get_xticklabels(), ax.get_yticklabels())))
        self.assertTrue(all(
            t.get_size() == 10 for t in ax.get_xticklabels(minor=True)))

    def test_xlabel(self):
        """Test xlabel formatoption"""
        self.update(xlabel='{desc}')
        label = self.plotter.ax.xaxis.get_label()
        self.assertEqual(label.get_text(), 'pressure [Pa]')
        self.update(labelsize=22, labelweight='bold',
                    labelprops={'ha': 'left'})
        self.assertEqual(label.get_size(), 22)
        self.assertEqual(label.get_weight(), bold)
        self.assertEqual(label.get_ha(), 'left')

    def test_ylim(self, test_pctls=False):
        super(FldmeanPlotterTest, self).test_ylim(test_pctls)

    @unittest.skip('nan not supported for icon contour')
    def test_mask_01_var(self):
        pass

    @unittest.skip('nan not supported for icon contour')
    def test_mask_02_da(self):
        pass

    @unittest.skip('nan not supported for icon contour')
    def test_mask_03_fname(self):
        pass


@unittest.skipIf(not with_cdo, 'CDOs are required for unstructured grids.')
class IconFldmeanPlotterTest(bt.PsyPlotTestCase):

    plot_type = 'fldmean'

    grid_type = 'icon'

    ncfile = os.path.join(bt.test_dir, 'icon_test.nc')

    var = 't2m'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, z=[0, 1], name=cls.var, auto_update=True)
        cls.plotter = FldmeanPlotter(cls.data)
        cls.create_dirs()

    def ref_plot(self, close=True):
        """Basic reference plot"""
        sp = psy.plot.fldmean(self.ncfile, name=self.var, z=[0, 1])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file('basic')))
        if close:
            sp.close(True, True)

    @classmethod
    def tearDown(cls):
        cls.data.psy.update(todefault=True, replot=True)

    @classmethod
    def tearDownClass(cls):
        super(IconFldmeanPlotterTest, cls).tearDownClass()
        cls.ds.close()
        plt.close(cls.plotter.ax.get_figure().number)

    def test_plot(self):
        """Test whether it can be plotted"""
        self.compare_figures(self.get_ref_file('basic'))


tests2d = [LinePlotterTest2D, Simple2DPlotterTest2D]

# skip the reference creation functions of the 2D Plotter tests
for cls in tests2d:
    skip_msg = "Reference figures for this class are created by the %s" % (
        cls.__name__[:-2])
    for funcname in filter(lambda s: s.startswith('ref'), dir(cls)):
        setattr(cls, funcname, unittest.skip(skip_msg)(lambda self: None))
del cls


@pytest.mark.parametrize(
    "old,new",
    (("tri", "poly"), ("tricontour", "contour"), ("tricontourf", "contourf")),
    )
def test_plot_deprecation(old, new):
    """Test if tri is deprecated correctly"""
    with psy.open_dataset(os.path.join(bt.test_dir, "icon_test.nc")) as ds:
        with pytest.warns(DeprecationWarning, match="plot=[\"']%s[\"']" % old):
            sp = ds.psy.plot.plot2d(name="t2m", plot=old)
    plotter = sp.plotters[0]
    assert plotter.plot.value == new


def test_plot_poly_3D_bounds():
    """Test plotting the polygons with 3D bounds."""
    fname = os.path.join(bt.test_dir, "rotated-pole-test.nc")
    with psy.plot.plot2d(fname, plot='poly') as sp:
        assert sp[0].ndim == 2
        plotter = sp.plotters[0]
        xmin, xmax = plotter.ax.get_xlim()
        ymin, ymax = plotter.ax.get_ylim()
        assert xmax - xmin > 100
        assert ymax - ymin > 50


def test_datagrid_3D_bounds():
    """Test plotting the datagrid with 3D bounds."""
    fname = os.path.join(bt.test_dir, "rotated-pole-test.nc")
    with psy.plot.plot2d(fname, datagrid='k-') as sp:
        assert sp[0].ndim == 2
        plotter = sp.plotters[0]
        xmin, xmax = plotter.ax.get_xlim()
        ymin, ymax = plotter.ax.get_ylim()
        assert xmax - xmin > 100
        assert ymax - ymin > 50


if __name__ == '__main__':
    unittest.main()
