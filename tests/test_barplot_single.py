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

import unittest

from psy_simple.plotters import BarPlotter
import psyplot.project as psy
import test_barplot as tb
from psyplot import InteractiveList, open_dataset


class SingleBarPlotterTest(tb.BarPlotterTest):
    """Test of :class:`psy_simple.plotters.ViolinPlotter` with a single array
    instead of an InteractiveList"""

    plot_type = "singlebar"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True
        )
        cls.data[0].psy.arr_name = "arr0"
        cls.data.psy.arr_name = "arr0"
        cls.plotter = BarPlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop("name", self.var)
        return psy.plot.barplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs
        )

    @unittest.skip("""Not possible for single array""")
    def test_plot(self, *args):
        pass

    @unittest.skip("Appending not possible for single line")
    def test_append_data(self):
        pass
