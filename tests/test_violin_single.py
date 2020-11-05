"""Test module of the :mod:`psy_simple.plotters` module"""
from psy_simple.plotters import ViolinPlotter
import psyplot.project as psy
import test_base as tb
import test_violin as tv
from psyplot import InteractiveList, open_dataset


class SingleViolinPlotterTest(tv.ViolinPlotterTest):
    """Test of :class:`psy_simple.plotters.ViolinPlotter` with a single array
    instead of an InteractiveList"""

    plot_type = 'singleviolin'

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        cls.data = InteractiveList.from_dataset(
            cls.ds, y=0, z=0, t=0, name=cls.var, auto_update=True)
        cls.data[0].psy.arr_name = 'arr0'
        cls.data.psy.arr_name = 'arr0'
        cls.plotter = ViolinPlotter(cls.data[0])
        cls.create_dirs()

    @classmethod
    def tearDown(cls):
        cls.data[0].psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        name = kwargs.pop('name', self.var)
        return psy.plot.violinplot(
            self.ncfile, name=name, t=0, z=0, y=0, **kwargs)
