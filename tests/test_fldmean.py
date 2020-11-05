import unittest
from itertools import chain

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from psyplot import InteractiveList, open_dataset
from psy_simple.plotters import FldmeanPlotter

import psyplot.project as psy

import test_base as tb
import test_lineplot as tl


bold = tb.bold


class FldmeanPlotterTest(tl.LinePlotterTest):
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
