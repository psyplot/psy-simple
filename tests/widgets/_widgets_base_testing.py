# -*- coding: utf-8 -*-
"""Module defining the base class for the gui test"""

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

import six
import os
import os.path as osp
import numpy as np
import unittest

os.environ['PSYPLOT_PLUGINS'] = 'yes:psy_simple.plugin'


from psyplot_gui.compat.qtcompat import QApplication
from psyplot_gui import rcParams
from psyplot import rcParams as psy_rcParams


def is_running_in_gui():
    from psyplot_gui.main import mainwindow
    return mainwindow is not None


running_in_gui = is_running_in_gui()


on_travis = os.environ.get('TRAVIS')


def setup_rcparams():
    rcParams.defaultParams['console.start_channels'][0] = False
    rcParams.defaultParams['main.listen_to_port'][0] = False
    rcParams.defaultParams['help_explorer.render_docs_parallel'][0] = False
    rcParams.defaultParams['help_explorer.use_intersphinx'][0] = False
    rcParams.defaultParams['plugins.include'][0] = []
    rcParams.defaultParams['plugins.exclude'][0] = 'all'
    rcParams.update_from_defaultParams()


class PsyPlotGuiTestCase(unittest.TestCase):
    """A base class for testing the psyplot_gui module

    At the initializzation of the TestCase, a new
    :class:`psyplot_gui.main.MainWindow` widget is created which is closed at
    the end of all the tests"""

    @classmethod
    def setUpClass(cls):
        from psyplot_gui.main import mainwindow
        cls._close_app = mainwindow is None
        cls._app = QApplication.instance()
        if not running_in_gui:
            if cls._app is None:
                cls._app = QApplication([])
            cls._app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        if not running_in_gui:
            cls._app.quit()
            del cls._app

    def setUp(self):
        import psyplot_gui.main as main
        if not running_in_gui:
            setup_rcparams()
            self.window = main.MainWindow.run(show=False)
        else:
            self.window = main.mainwindow

    def tearDown(self):
        import psyplot.project as psy
        import matplotlib.pyplot as plt
        if not running_in_gui:
            import psyplot_gui.main as main
            self.window.close()
            rcParams.update_from_defaultParams()
            psy_rcParams.update_from_defaultParams()
            rcParams.disconnect()
            psy_rcParams.disconnect()
            main._set_mainwindow(None)
        del self.window
        psy.close('all')
        plt.close('all')

    def get_file(self, fname):
        """Get the path to the file `fname`

        Parameters
        ----------
        fname: str
            The path of the file name (relative to the test directory)

        Returns
        -------
        str
            The complete path to the given file"""
        return osp.join(osp.dirname(__file__), fname)

    def assertAlmostArrayEqual(self, actual, desired, rtol=1e-07, atol=0,
                               msg=None, **kwargs):
        """Asserts that the two given arrays are almost the same

        This method uses the :func:`numpy.testing.assert_allclose` function
        to compare the two given arrays.

        Parameters
        ----------
        actual : array_like
            Array obtained.
        desired : array_like
            Array desired.
        rtol : float, optional
            Relative tolerance.
        atol : float, optional
            Absolute tolerance.
        equal_nan : bool, optional.
            If True, NaNs will compare equal.
        msg : str, optional
            The error message to be printed in case of failure.
        verbose : bool, optional
            If True, the conflicting values are appended to the error message.
        """
        try:
            np.testing.assert_allclose(actual, desired, rtol=rtol, atol=atol,
                                       err_msg=msg or '', **kwargs)
        except AssertionError as e:
            if six.PY2:
                self.fail(e.message)
            else:
                self.fail(str(e))
