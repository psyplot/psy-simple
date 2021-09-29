"""Test module of the :mod:`psy_simple.plotters` module."""

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

import os
from psy_simple.plotters import BarPlotter
import psyplot.project as psy
import test_lineplot as tl
import test_barplot as tb
import _base_testing as bt
from psyplot import rcParams


class BarPlotterDataTest(tb.BarPlotterTest):
    """TestCase of :class:`psy_simple.plotters.BarPlotter` with widhts=='data'
    """

    plot_type = "bar_data"

    @classmethod
    def setUpClass(cls):
        plotter = BarPlotter()
        rcParams[plotter.widths.default_key] = "data"
        super().setUpClass()

    def test_ylim(self):
        """Test ylim formatoption"""
        tl.LinePlotterTest.test_ylim(self)

    def _test_DtTicksBase(self, *args):
        tl.LinePlotterTest._test_DtTicksBase(self, *args)

    def ref_xticks(self, close=True):
        """Create reference file for xticks formatoption

        Create reference file for
        :attr:`~psy_simple.plotters.BarPlotter.xticks`
        formatoption"""
        sp = psy.plot.barplot(
            self.ncfile,
            name=self.var,
            lon=0,
            lev=0,
            lat=[0, 1],
            xticklabels={"major": "%m", "minor": "%d"},
            xtickprops={"pad": 7.0},
            xticks={"minor": "week", "major": "month"},
        )
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("xticks")))
        if close:
            sp.close(True, True)
