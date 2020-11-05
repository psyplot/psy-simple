import unittest

from psyplot import rcParams
from psy_simple.plotters import Simple2DPlotter

import test_plot2d_icon as t2di


class IconSimplePlotterContourTest(t2di.IconSimplePlotterTest):

    plot_type = "icon_contour"

    @classmethod
    def setUpClass(cls):
        plotter = Simple2DPlotter()
        rcParams[plotter.plot.default_key] = "contourf"
        super(IconSimplePlotterContourTest, cls).setUpClass()

    @unittest.skip("Extend keyword not implemented")
    def test_extend(self):
        pass

    @unittest.skip("miss_color keyword not implemented")
    def test_miss_color(self):
        pass

    @unittest.skip("miss_color keyword not implemented")
    def ref_miss_color(self):
        pass

    @unittest.skip("nan not supported for icon contour")
    def test_mask_01_var(self):
        pass

    @unittest.skip("nan not supported for icon contour")
    def test_mask_02_da(self):
        pass

    @unittest.skip("nan not supported for icon contour")
    def test_mask_03_fname(self):
        pass
