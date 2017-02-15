"""Test the :mod:`psy_simple.colors` module"""
import six
import unittest
import matplotlib.pyplot as plt
import psy_simple.colors as psyc


class TestShowColormaps(unittest.TestCase):
    """Test the :func:`psy_simple.colors.show_colormaps` function"""

    def setUp(self):
        plt.close('all')

    def tearDown(self):
        plt.close('all')

    def test_all(self):
        """Test the display of all colormaps"""
        psyc.show_colormaps()
        self.assertEqual(plt.get_fignums(), [1])
        self.assertGreater(len(plt.gcf().axes), 15)

    def test_some(self):
        """Test the display of a selection of colormaps"""
        cmap = plt.get_cmap('Reds')
        psyc.show_colormaps('jet', cmap, 'red_white_blue')
        self.assertEqual(plt.get_fignums(), [1])
        self.assertEqual(len(plt.gcf().axes), 3)

    @unittest.skipIf(six.PY2, 'Not implemented TestCase method')
    def test_warning_similar(self):
        """Test the display of a warning of a slightly misspelled cmap"""
        with self.assertWarnsRegex(UserWarning, 'Similar colormaps'):
            psyc.show_colormaps('jett')
        self.assertEqual(plt.get_fignums(), [1])
        self.assertEqual(len(plt.gcf().axes), 0)

    @unittest.skipIf(six.PY2, 'Not implemented TestCase method')
    def test_warning_unknown(self):
        """Test the display of a warning of a completely unknown cmap"""
        with self.assertWarnsRegex(UserWarning,
                                   'Run function without arguments'):
            psyc.show_colormaps('asdfkj')
        self.assertEqual(plt.get_fignums(), [1])
        self.assertEqual(len(plt.gcf().axes), 0)


if __name__ == '__main__':
    unittest.main()
