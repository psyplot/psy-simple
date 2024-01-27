"""Test module for the fldmean plotter for icon grids."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import os
import unittest

import _base_testing as bt
import matplotlib.pyplot as plt
import psyplot.project as psy
from psyplot import InteractiveList, open_dataset

from psy_simple.plotters import FldmeanPlotter

try:
    from cdo import Cdo

    Cdo()
except Exception:
    with_cdo = False
else:
    with_cdo = True


@unittest.skipIf(not with_cdo, "CDOs are required for unstructured grids.")
class IconFldmeanPlotterTest(bt.PsyPlotTestCase):
    plot_type = "fldmean"

    grid_type = "icon"

    ncfile = os.path.join(bt.test_dir, "icon_test.nc")

    var = "t2m"

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, z=[0, 1], name=cls.var, auto_update=True
        )
        cls.plotter = FldmeanPlotter(cls.data)
        cls.create_dirs()

    def ref_plot(self, close=True):
        """Basic reference plot"""
        sp = psy.plot.fldmean(self.ncfile, name=self.var, z=[0, 1])
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("basic")))
        if close:
            sp.close(True, True)

    @classmethod
    def tearDown(cls):
        cls.data.psy.update(todefault=True, replot=True)

    @classmethod
    def tearDownClass(cls):
        super(IconFldmeanPlotterTest, cls).tearDownClass()
        cls.ds.close()
        plt.close(cls.plotter.ax.get_figure().number)

    def test_plot(self):
        """Test whether it can be plotted"""
        self.compare_figures(self.get_ref_file("basic"))
