"""Test module for streamplots."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import os

import _base_testing as bt
import test_vector as tv
from psyplot import rcParams

from psy_simple.plotters import SimpleVectorPlotter


class SimpleStreamVectorPlotterTest(tv.SimpleVectorPlotterTest):
    """Test case for stream plot of
    :class:`psy_simple.plotters.SimpleVectorPlotter`
    """

    @classmethod
    def setUpClass(cls):
        plotter = SimpleVectorPlotter()
        rcParams[plotter.plot.default_key] = "stream"
        return super(SimpleStreamVectorPlotterTest, cls).setUpClass()

    def get_ref_file(self, identifier):
        return super(SimpleStreamVectorPlotterTest, self).get_ref_file(
            identifier + "_stream"
        )

    def ref_arrowsize(self, *args):
        """Create reference file for arrowsize formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.arrowsize` (and others)
        formatoption"""
        sp = self.plot(arrowsize=2.0)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("arrowsize")))

    def ref_arrowstyle(self, *args):
        """Create reference file for arrowstyle formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.arrowstyle` (and
        others) formatoption"""
        sp = self.plot(arrowsize=2.0, arrowstyle="fancy")
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("arrowstyle")))

    def test_arrowsize(self, *args):
        """Test arrowsize formatoption"""
        self.update(arrowsize=2.0)
        self.compare_figures(next(iter(args), self.get_ref_file("arrowsize")))

    def test_arrowstyle(self, *args):
        """Test arrowstyle formatoption"""
        self.update(arrowsize=2.0, arrowstyle="fancy")
        self.compare_figures(next(iter(args), self.get_ref_file("arrowstyle")))

    def ref_density(self, *args):
        """Create reference file for density formatoption.

        Create reference file for
        :attr:`~psy_simple.plotters.SimpleVectorPlotter.density` (and others)
        formatoption"""
        sp = self.plot(density=0.5)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("density")))

    def test_density(self, *args):
        """Test density formatoption"""
        self.update(density=0.5)
        self.compare_figures(next(iter(args), self.get_ref_file("density")))
