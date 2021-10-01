"""Module for PyQt4/PyQt5 widgets for modifying the formatoptions

This module contains widgets that are inserted in the psyplot GUI. Submodules
are

* :mod:`psy_simple.widgets.texts`: A module for the modification of labels
"""

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

import os.path as osp
from functools import partial
from PyQt5 import QtWidgets


def get_icon(fname, ending='.png'):
    return osp.join(osp.dirname(__file__), 'icons', fname + ending)


class Switch2FmtButton(QtWidgets.QToolButton):
    """A button that contains a menu to switch to other formatoptions"""

    def __init__(self, parent, *fmtos):
        """
        Parameters
        ----------
        parent: psyplot_gui.fmt_widget.FormatoptionWidget
            The formatoption widget that contains the button
        ``*fmtos``
            Instances of the :class:`psyplot.plotter.Formatoption` for which
            the links should be created
        """
        super().__init__(parent=parent)
        self.setText('fmt')
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu()
        for fmto in fmtos:
            name = parent.get_name(fmto)
            menu.addAction(name, partial(parent.set_fmto, name))
        self.setMenu(menu)
