"""Test the :mod:`psy_simple.colors` module."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import unittest

import _base_testing as bt
import matplotlib.pyplot as plt
import six

import psy_simple.colors as psyc


class TestShowColormaps(unittest.TestCase):
    """Test the :func:`psy_simple.colors.show_colormaps` function"""

    def setUp(self):
        plt.close("all")

    def tearDown(self):
        plt.close("all")

    def test_all(self):
        """Test the display of all colormaps"""
        fig = psyc.show_colormaps(use_qt=False)
        self.assertEqual(fig.number, 1)
        self.assertGreater(len(fig.axes), 15)

    def test_some(self):
        """Test the display of a selection of colormaps"""
        cmap = plt.get_cmap("Reds")
        fig = psyc.show_colormaps(
            ["jet", cmap, "red_white_blue"], use_qt=False
        )
        self.assertEqual(fig.number, 1)
        self.assertEqual(len(fig.axes), 3)

    @unittest.skipIf(
        six.PY2 or (bt.sns_version is not None and bt.sns_version < "0.8"),
        "Not implemented TestCase method" if six.PY2 else "Crashed by seaborn",
    )
    def test_warning_similar(self):
        """Test the display of a warning of a slightly misspelled cmap"""
        with self.assertWarnsRegex(UserWarning, "Similar colormaps"):
            fig = psyc.show_colormaps("jett", use_qt=False)
        self.assertEqual(fig.number, 1)
        self.assertEqual(len(fig.axes), 0)

    @unittest.skipIf(
        six.PY2 or (bt.sns_version is not None and bt.sns_version < "0.8"),
        "Not implemented TestCase method" if six.PY2 else "Crashed by seaborn",
    )
    def test_warning_unknown(self):
        """Test the display of a warning of a completely unknown cmap"""
        with self.assertWarnsRegex(
            UserWarning, "Run function without arguments"
        ):
            fig = psyc.show_colormaps("asdfkj", use_qt=False)
        self.assertEqual(fig.number, 1)
        self.assertEqual(len(fig.axes), 0)


if __name__ == "__main__":
    unittest.main()
