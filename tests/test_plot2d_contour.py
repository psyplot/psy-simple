"""Test module for the simple contour plot."""

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
