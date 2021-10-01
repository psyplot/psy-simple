"""Test module for the :mod:`psy_simple.widgets.colors` module"""

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

import matplotlib as mpl

mpl_version = tuple(map(int, mpl.__version__.split('.')[:2]))


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

    def test_edit_colormap_01_standard(self):
        dialog = pswc.ColormapDialog('Blues')
        self.assertIsInstance(dialog, pswc.ColormapDialog)
        self.assertEqual(dialog.table.rowCount(), 1)
        dialog.table.selectRow(0)
        self.assertColormapEqual(dialog.table.chosen_colormap, 'Blues', True)
        dialog.close()

    def test_edit_colormap_02_custom(self):
        cmap = get_cmap('Blues')
        dialog = pswc.ColormapDialog(cmap)
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
        self.assertEqual(fmt_w.get_obj(), ['minmax', 14, 10, 95, None, None])

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
        if mpl_version <= (3, 1):
            kws = {}
        else:
            kws = {'base': 10}
        self.project.update(bounds=mcol.SymLogNorm(1.0, **kws))
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


class BackgroundColorWidgetTest(bt.PsyPlotGuiTestCase):
    """Test case for the :class:`BackGroundColorWidget`
    """

    @property
    def fmt_widget(self):
        return self.window.fmt_widget

    @property
    def plotter(self):
        return self.project.plotters[0]

    def setUp(self):
        import psyplot.project as psy
        super().setUp()
        self.project = psy.plot.plot2d(
            self.get_file(osp.join('..', 'test-t2m-u-v.nc')),
            name='t2m')
        self.fmt_widget.fmto = self.plotter.background

    def test_transparent(self):
        w = self.fmt_widget.fmt_widget
        w.cb_enable.setChecked(True)
        self.assertIsNone(self.fmt_widget.get_obj())
        self.assertFalse(w.color_label.isEnabled())

    def test_color_change(self):
        w = self.fmt_widget.fmt_widget
        w.color_label.set_color(QtGui.QColor(51, 51, 51, 255))
        obj = self.fmt_widget.get_obj()
        self.assertEqual(list(obj), [0.2, 0.2, 0.2, 1.0])


class CTicksWidgetTest(bt.PsyPlotGuiTestCase):
    """Test case for the :class:`psy_simple.widgets.colors.BoundsFmtWidget`"""

    @property
    def fmt_widget(self):
        return self.window.fmt_widget

    @property
    def plotter(self):
        return self.project.plotters[0]

    def setUp(self):
        import psyplot.project as psy
        super(CTicksWidgetTest, self).setUp()
        self.project = psy.plot.plot2d(
            self.get_file(osp.join('..', 'test-t2m-u-v.nc')),
            name='t2m')
        self.fmt_widget.fmto = self.plotter.cticks

    def test_instance(self):
        """Test changes"""
        self.assertIsInstance(self.fmt_widget.fmt_widget,
                              pswc.CTicksFmtWidget)

    def test_minmax(self):
        self.project.update(cticks=['minmax', 14, 5, 95])
        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertIs(w, fmt_w.fmt_widget._auto_array_widget)
        self.assertEqual(fmt_w.fmt_widget.method_combo.currentText(), 'minmax')
        self.assertEqual(w.sb_N.value(), 14)
        self.assertEqual(float(w.txt_min_pctl.text()), 5)
        self.assertEqual(float(w.txt_max_pctl.text()), 95)

        w.txt_min_pctl.setText('10')
        self.assertEqual(fmt_w.get_obj(), ['minmax', 14, 10, 95, None, None])

    def test_bounds(self):
        self.project.update(cticks=['bounds', 3])

        fmt_w = self.fmt_widget
        fmt_w.reset_fmt_widget()
        w = fmt_w.fmt_widget.current_widget
        self.assertIs(w, fmt_w.fmt_widget._auto_array_widget)
        self.assertEqual(fmt_w.fmt_widget.method_combo.currentText(), 'bounds')
        self.assertEqual(w.sb_N.value(), 3)


if __name__ == '__main__':
    unittest.main()
