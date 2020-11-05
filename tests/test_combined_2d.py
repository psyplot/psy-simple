import test_base as tb
import test_combined as tc


class CombinedSimplePlotterTest2D(tb.TestBase2D, tc.CombinedSimplePlotterTest):
    """Test :class:`psy_simple.plotters.CombinedSimplePlotter` class without
    time and vertical dimension"""

    var = ['t2m', ['u_2d', 'v_2d']]

    def _label_test(self, key, label_func, has_time=None):
        if has_time is None:
            has_time = not bool(self.vector_mode)
        tc.CombinedSimplePlotterTest._label_test(
            self, key, label_func, has_time=has_time)
