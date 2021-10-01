"""Test module for the density plotter."""

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
from psy_simple.plotters import DensityPlotter

import test_density as td


class DensityPlotterTestKDE(td.DensityPlotterTest):
    """Test of the :class:`psy_simple.plotters.DensityPlotter` class
    with kde plot"""

    @classmethod
    def setUpClass(cls):
        plotter = DensityPlotter()
        rcParams[plotter.density.default_key] = "kde"
        super().setUpClass()

    @unittest.skip("Not implemented for KDE plots!")
    def test_normed(self):
        pass
