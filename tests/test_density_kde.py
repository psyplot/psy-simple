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
