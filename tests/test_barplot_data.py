"""Test module of the :mod:`psy_simple.plotters` module"""
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
