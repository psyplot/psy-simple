"""Test module for the density plotter."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import unittest

import test_density as td
from psyplot import rcParams

from psy_simple.plotters import DensityPlotter


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
