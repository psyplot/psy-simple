"""Test module for the simple contour plot."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import unittest

import test_plot2d as t2d
from psyplot import rcParams

from psy_simple.plotters import Simple2DPlotter


class Simple2DPlotterContourTest(t2d.Simple2DPlotterTest):
    plot_type = "simple2D_contour"

    @classmethod
    def setUpClass(cls):
        plotter = Simple2DPlotter()
        rcParams[plotter.plot.default_key] = "contourf"
        super(Simple2DPlotterContourTest, cls).setUpClass()

    @unittest.skip("Extend keyword not implemented")
    def test_extend(self):
        pass

    @unittest.skip("miss_color keyword not implemented")
    def test_miss_color(self):
        pass

    @unittest.skip("miss_color keyword not implemented")
    def ref_miss_color(self):
        pass
