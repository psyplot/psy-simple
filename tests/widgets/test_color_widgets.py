"""Test module for the :mod:`psy_simple.widgets.colors` module"""
import six
import os.path as osp
import numpy as np
from psyplot.data import isstring
import psy_simple.widgets.colors as pswc
from psy_simple.colors import get_cmap
import matplotlib.colors as mcol
from psyplot_gui.compat.qtcompat import QTest, Qt, QtGui
import _widgets_base_testing as bt
import unittest


class CMapWidgetTest(bt.PsyPlotGuiTestCase):
    """Test case for the :class:`psy_simple.widgets.colors.CMapFmtWidget`"""

    @property
    def fmt_widget(self):
        return self.window.fmt_widget

    @property
    def plotter(self):
        return self.project.plotters[0]

    def setUp(self):
        import psyplot.project as psy
        super(CMapWidgetTest, self).setUp()
        self.project = psy.plot.plot2d(
            self.get_file(osp.join('..', 'test-t2m-u-v.nc')),
            name='t2m')
        self.fmt_widget.fmto = self.plotter.cmap

    def assertColormapEqual(self, cmap, reference, force_string=False):
        """Test whether two colormaps are the same

        Parameters
        ----------
        cmap: str or :class:`matplotlib.colors.Colormap`
            The colormap to test
        reference: str or :class:`matplotlib.colors.Colormap`
            The reference colormap"""
        if force_string or (isstring(cmap) and isstring(reference)):
            self.assertEqual(cmap, reference)
        if isstring(cmap):
            cmap = get_cmap(cmap)
        if isstring(reference):
            reference = get_cmap(reference)
        colors = np.linspace(0, 1, 4)
        self.assertAlmostArrayEqual(cmap(colors), reference(colors))

    def test_instance(self):
        """Test changes"""
        self.assertIsInstance(self.fmt_widget.fmt_widget, pswc.CMapFmtWidget)

    def test_choose_cmap(self):
        fmt_w = self.fmt_widget
        fmt_w.fmt_widget.choose_cmap('Blues')
        self.assertColormapEqual(fmt_w.get_obj(), 'Blues', True)
        cmap = get_cmap('Blues')
        fmt_w.fmt_widget.choose_cmap(cmap)
        chosen = fmt_w.get_obj()
        self.assertIsInstance(chosen, mcol.Colormap)
        self.assertColormapEqual(chosen, cmap)

    def test_show_colormap_01_standard(self):
        fmt_w = self.fmt_widget
        fmt_w.fmt_widget.choose_cmap('Blues')
        dialog = fmt_w.fmt_widget.show_cmap()
        self.assertIsInstance(dialog, pswc.ColormapDialog)
        self.assertEqual(dialog.table.rowCount(), 1)
        dialog.table.selectRow(0)
        self.assertColormapEqual(dialog.table.chosen_colormap, 'Blues', True)
        dialog.close()

    def test_show_colormap_02_custom(self):
        fmt_w = self.fmt_widget
        cmap = get_cmap('Blues')
        fmt_w.fmt_widget.choose_cmap(cmap)
        dialog = fmt_w.fmt_widget.show_cmap()
        self.assertIsInstance(dialog, pswc.ColormapDialog)
        self.assertEqual(dialog.table.rowCount(), 1)
        dialog.table.selectRow(0)
        self.assertIsInstance(dialog.table.chosen_colormap, mcol.Colormap)
        self.assertColormapEqual(dialog.table.chosen_colormap, 'Blues')
        dialog.close()


class BoundsWidgetTest(bt.PsyPlotGuiTestCase):
    """Test case for the :class:`psy_simple.widgets.colors.BoundsFmtWidget`"""

    @property
    def fmt_widget(self):
        return self.window.fmt_widget

    @property
    def plotter(self):
        return self.project.plotters[0]

    def setUp(self):
        import psyplot.project as psy
        super(BoundsWidgetTest, self).setUp()
        self.project = psy.plot.plot2d(
            self.get_file(osp.join('..', 'test-t2m-u-v.nc')),
            name='t2m')
        self.fmt_widget.fmto = self.plotter.bounds

    def assertColormapEqual(self, cmap, reference, force_string=False):
        """Test whether two colormaps are the same

        Parameters
        ----------
        cmap: str or :class:`matplotlib.colors.Colormap`
            The colormap to test
        reference: str or :class:`matplotlib.colors.Colormap`
            The reference colormap"""
        if force_string or (isstring(cmap) and isstring(reference)):
            self.assertEqual(cmap, reference)
        if isstring(cmap):
            cmap = get_cmap(cmap)
        if isstring(reference):
            reference = get_cmap(reference)
        colors = np.linspace(0, 1, 4)
        self.assertAlmostArrayEqual(cmap(colors), reference(colors))

    def test_instance(self):
        """Test changes"""
        self.assertIsInstance(self.fmt_widget.fmt_widget, pswc.BoundsFmtWidget)

    def test_minmax(self):
        self.project.update(bounds=['minmax', 14, 5, 95])
        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertIs(w, fmt_w.fmt_widget._auto_array_widget)
        self.assertEqual(fmt_w.fmt_widget.method_combo.currentText(), 'minmax')
        self.assertEqual(w.sb_N.value(), 14)
        self.assertEqual(float(w.txt_min_pctl.text()), 5)
        self.assertEqual(float(w.txt_max_pctl.text()), 95)

        w.txt_min_pctl.setText('10')
        self.assertEqual(fmt_w.get_obj(), ['minmax', 14, 10, 95])

    def test_powernorm(self):
        """Test a :class:`matplotlib.colors.PowerNorm`"""
        self.project.update(bounds=mcol.PowerNorm(1.0, 280, 290))
        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertIs(w, fmt_w.fmt_widget._norm_widget)
        w.txt_gamma.setText('2.0')
        self.assertIsInstance(fmt_w.get_obj(), mcol.PowerNorm)

    def test_symlognorm(self):
        """Test a :class:`matplotlib.colors.SymLogNorm`"""
        self.project.update(bounds=mcol.SymLogNorm(1.0))
        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertIs(w, fmt_w.fmt_widget._norm_widget)
        w.txt_linthresh.setText('2.0')
        self.assertIsInstance(fmt_w.get_obj(), mcol.SymLogNorm)

    def test_array(self):
        bounds = np.arange(280., 290.1, 1)
        self.project.update(bounds=bounds)
        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertEqual(float(w.txt_min.text()), 280)
        self.assertEqual(float(w.txt_max.text()), 290)
        self.assertEqual(float(w.txt_step.text()), 1)
        self.assertEqual(w.sb_nsteps.value(), 11)
        self.assertIs(w, fmt_w.fmt_widget._array_widget)
        self.assertEqual(fmt_w.get_obj(), bounds.tolist())
        self.assertTrue(w.txt_step.isEnabled())
        self.assertFalse(w.sb_nsteps.isEnabled())
        w.txt_step.setText('0.5')
        self.assertAlmostArrayEqual(
            fmt_w.get_obj(), np.arange(280, 290.1, 0.5))

        w.step_inc_combo.setCurrentText('# Steps')
        self.assertFalse(w.txt_step.isEnabled())
        self.assertTrue(w.sb_nsteps.isEnabled())
        w.sb_nsteps.setValue(12)
        w.set_array()
        self.assertAlmostArrayEqual(
            fmt_w.get_obj(), np.round(np.linspace(280, 290, 12), 3))


if __name__ == '__main__':
    unittest.main()
