import unittest

import test_base as tb
import test_lineplot as tl


class LinePlotterTest2D(tb.TestBase2D, tl.LinePlotterTest):
    """Test :class:`psy_simple.plotters.LinePlotter` class without
    time and vertical dimension"""

    var = "t2m_2d"

    def test_xticks(self, *args):
        """Test xticks, xticklabels, xtickprops formatoptions"""
        self._test_DataTicksCalculator()

    def test_coord(self):
        """Test whether we can use an alternative coordinate"""
        self.update(coord="v_2d", xlabel="%(name)s")
        self.assertEqual(
            self.plotter.ax.get_xlabel(),
            "v_2d",
            msg="Did not update to the right coordinate!",
        )


# skip the reference creation functions of the 2D Plotter tests
skip_msg = "Reference figures for this class are created by the %s" % (
    tl.LinePlotterTest.__name__
)
for funcname in filter(lambda s: s.startswith("ref"), dir(LinePlotterTest2D)):
    setattr(
        LinePlotterTest2D, funcname, unittest.skip(skip_msg)(lambda self: None)
    )
