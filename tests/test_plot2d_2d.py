import unittest

import test_base as tb
import test_plot2d as t2d


class Simple2DPlotterTest2D(tb.TestBase2D, t2d.Simple2DPlotterTest):
    """Test :class:`psy_simple.plotters.Simple2DPlotter` class without
    time and vertical dimension"""

    var = "t2m_2d"


# skip the reference creation functions of the 2D Plotter tests
skip_msg = "Reference figures for this class are created by the %s" % (
    t2d.Simple2DPlotterTest.__name__
)
for funcname in filter(
    lambda s: s.startswith("ref"), dir(Simple2DPlotterTest2D)
):
    setattr(
        Simple2DPlotterTest2D,
        funcname,
        unittest.skip(skip_msg)(lambda self: None),
    )
