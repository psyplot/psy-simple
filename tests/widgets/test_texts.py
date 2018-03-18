"""Test module for the :mod:`psy_simple.widgets.texts` module"""
import os.path as osp
import psy_simple.widgets.texts as pswt
from psyplot_gui.compat.qtcompat import QTest, Qt, QtGui
import _widgets_base_testing as bt
import unittest


class TitleFmtWidgetTest(bt.PsyPlotGuiTestCase):
    """Test case for the LabelWidget"""

    @property
    def fmt_widget(self):
        return self.window.fmt_widget

    @property
    def plotter(self):
        return self.project.plotters[0]

    def setUp(self):
        import psyplot.project as psy
        super(TitleFmtWidgetTest, self).setUp()
        self.project = psy.plot.lineplot(
            self.get_file(osp.join('..', 'test-t2m-u-v.nc')),
            name='t2m', x=0, y=0, z=0)

    def test_instance(self):
        """Test changes"""
        self.fmt_widget.fmto = self.plotter.title
        self.assertIsInstance(self.fmt_widget.fmt_widget, pswt.LabelWidget)
        self.fmt_widget.fmto = self.plotter.titleprops
        self.assertIsInstance(self.fmt_widget.fmt_widget,
                              pswt.FontPropertiesWidget)
        self.fmt_widget.fmto = self.plotter.titleweight
        self.assertIsInstance(self.fmt_widget.fmt_widget,
                              pswt.FontWeightWidget)
        self.fmt_widget.fmto = self.plotter.titlesize
        self.assertIsInstance(self.fmt_widget.fmt_widget,
                              pswt.FontSizeWidget)

    def test_choose_font(self):
        self.fmt_widget.fmto = self.plotter.titleprops
        fmto_widget = self.fmt_widget.fmt_widget
        font = QtGui.QFont('Arial', 24, QtGui.QFont.Bold, True)
        fmto_widget.choose_font(font)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties,
                         dict(family='Arial', size=24, weight='bold',
                              style='italic'))
        self.assertTrue(fmto_widget.btn_bold.isChecked())
        self.assertTrue(fmto_widget.btn_italic.isChecked())
        self.assertEqual(fmto_widget.spin_box.value(), 24)

    def test_btn_bold(self):
        self.test_choose_font()
        fmto_widget = self.fmt_widget.fmt_widget
        QTest.mouseClick(fmto_widget.btn_bold, Qt.LeftButton)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['weight'], 'normal')
        QTest.mouseClick(fmto_widget.btn_bold, Qt.LeftButton)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['weight'], 'bold')

    def test_btn_italic(self):
        self.test_choose_font()
        fmto_widget = self.fmt_widget.fmt_widget
        QTest.mouseClick(fmto_widget.btn_italic, Qt.LeftButton)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['style'], 'normal')
        QTest.mouseClick(fmto_widget.btn_italic, Qt.LeftButton)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['style'], 'italic')

    def test_modify_size(self):
        self.test_choose_font()
        fmto_widget = self.fmt_widget.fmt_widget
        fmto_widget.spin_box.setValue(28)
        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['size'], 28)

    def test_choose_color(self):
        """Test choosing the color"""
        self.fmt_widget.fmto = self.plotter.titleprops
        fmto_widget = self.fmt_widget.fmt_widget
        fmto_widget.choose_color(QtGui.QColor(Qt.red))

        properties = self.fmt_widget.get_obj()
        self.assertEqual(properties['color'], (1.0, 0.0, 0.0, 1.0))


if __name__ == '__main__':
    unittest.main()
