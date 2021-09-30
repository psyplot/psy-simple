import unittest

from psyplot import rcParams
from psy_simple.plotters import Simple2DPlotter

import test_plot2d as t2d


class Simple2DPlotterContourTest(t2d.Simple2DPlotterTest):

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
