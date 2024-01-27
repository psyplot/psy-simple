"""Test module of the :mod:`psyplot.plotter.baseplotter` module."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import unittest
from itertools import chain

import _base_testing as bt
import matplotlib as mpl
import matplotlib.colors as mcol
import matplotlib.pyplot as plt
import numpy as np
import psyplot
from psyplot import InteractiveList, open_dataset

from psy_simple.base import BasePlotter

if mpl.__version__ >= "1.5" and mpl.__version__ < "2.1":
    from matplotlib.font_manager import weight_dict

    bold = weight_dict["bold"]
else:
    bold = "bold"


class BasePlotterTest(bt.PsyPlotTestCase):
    """Test :class:`psyplot.plotter.baseplotter.BasePlotter` class"""

    var = "t2m"

    masking_val = 250

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=[0, 1], z=0, t=0, name=cls.var, auto_update=True
        )
        cls.plotter = BasePlotter(cls.data)

    @classmethod
    def tearDownClass(cls):
        super(BasePlotterTest, cls).tearDownClass()
        cls.ds.close()
        plt.close(cls.plotter.ax.get_figure().number)

    def tearDown(self):
        self.data.psy.update(t=0, todefault=True, replot=True)

    def update(self, *args, **kwargs):
        """Update the plotter of this instance"""
        self.plotter.update(*args, **kwargs)

    def _label_test(self, key, label_func, has_time=True):
        kwargs = {
            key: "Test plot at %Y-%m-%d, {tinfo} o'clock of %(long_name)s"
        }
        self.update(**kwargs)
        t_str = "1979-01-31, 18:00" if has_time else "%Y-%m-%d, %H:%M"
        self.assertEqual(
            "Test plot at %s o'clock of %s"
            % (t_str, self.data.attrs.get("long_name", "Temperature")),
            label_func().get_text(),
        )
        self.data.psy.update(t=1)
        t_str = "1979-02-28, 18:00" if has_time else "%Y-%m-%d, %H:%M"
        self.assertEqual(
            "Test plot at %s o'clock of %s"
            % (t_str, self.data.attrs.get("long_name", "Temperature")),
            label_func().get_text(),
        )
        self.data.psy.update(t=0)

    def test_title(self):
        """Test title, titlesize, titleweight, titleprops formatoptions"""

        def get_title():
            return self.plotter.ax.title

        self._label_test("title", get_title)
        self.update(
            titlesize=22, titleweight="bold", titleprops={"ha": "left"}
        )
        self.assertEqual(get_title().get_size(), 22)
        self.assertEqual(get_title().get_weight(), bold)
        self.assertEqual(get_title().get_ha(), "left")

    def test_background(self):
        self.update(background="0.5")
        bc = mcol.to_rgba(self.plotter.ax.patch.get_facecolor())
        self.assertEqual(bc, (0.5, 0.5, 0.5, 1.0))

    def test_figtitle(self):
        """Test figtitle, figtitlesize, figtitleweight, figtitleprops
        formatoptions"""

        def get_figtitle():
            fig = plt.gcf()
            for text in fig.texts:
                if text.get_position() == (0.5, 0.98):
                    return text

        self._label_test("figtitle", get_figtitle)
        self.update(
            figtitlesize=22,
            figtitleweight="bold",
            figtitleprops={"ha": "left"},
        )
        self.assertEqual(get_figtitle().get_size(), 22)
        self.assertEqual(get_figtitle().get_weight(), bold)
        self.assertEqual(get_figtitle().get_ha(), "left")

    def test_text(self):
        """Test text formatoption"""

        def get_default_text():
            for text in chain(*self.plotter.text._texts.values()):
                if text.get_position() == tuple(
                    psyplot.rcParams["texts.default_position"]
                ):
                    return text

        self._label_test("text", get_default_text)
        self.update(text=(0.5, 0.5, "%(name)s", "fig", {"fontsize": 16}))
        for t in self.plotter.text._texts["fig"]:
            if t.get_position() == (0.5, 0.5):
                text = t
                break
            else:
                text = False
        self.assertTrue(text is not False)
        if not text:
            return
        self.assertEqual(text.get_text(), getattr(self.data, "name", self.var))
        self.assertEqual(text.get_fontsize(), 16)

    def test_maskgreater(self):
        """Test maskgreater formatoption"""
        self.update(maskgreater=self.masking_val)
        for arr in self.plotter.maskgreater.iter_data:
            self.assertLessEqual(arr.max().values, self.masking_val)

    def test_maskgeq(self):
        """Test maskgeq formatoption"""
        self.update(maskgeq=self.masking_val)
        for arr in self.plotter.maskgeq.iter_data:
            self.assertLessEqual(arr.max().values, self.masking_val)

    def test_maskless(self):
        """Test maskless formatoption"""
        self.update(maskless=self.masking_val)
        for arr in self.plotter.maskless.iter_data:
            self.assertGreaterEqual(arr.min().values, self.masking_val)

    def test_maskleq(self):
        """Test maskleq formatoption"""
        self.update(maskleq=self.masking_val)
        for arr in self.plotter.maskleq.iter_data:
            self.assertGreaterEqual(arr.min().values, self.masking_val)

    def test_maskbetween(self):
        """Test maskbetween formatoption"""
        self.update(maskbetween=[self.masking_val, self.masking_val + 1])
        for arr in self.plotter.maskbetween.iter_data:
            data = arr.values[~np.isnan(arr.values)]
            self.assertLessEqual(
                data[data < self.masking_val + 1].max(), self.masking_val
            )
            self.assertGreaterEqual(
                data[data > self.masking_val].max(), self.masking_val + 1
            )


class TestBase2D(object):
    """Test :class:`psyplot.plotter.baseplotter.BasePlotter` class without time
    and vertical dimension"""

    def _label_test(self, key, label_func, has_time=False):
        return super(TestBase2D, self)._label_test(
            key, label_func, has_time=has_time
        )


class BasePlotterTest2D(TestBase2D, BasePlotterTest):
    """Test :class:`psyplot.plotter.baseplotter.BasePlotter` class without time
    and vertical dimension"""

    var = "t2m_2d"


if __name__ == "__main__":
    unittest.main()
