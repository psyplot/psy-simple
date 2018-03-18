"""Module for PyQt4/PyQt5 widgets for modifying the formatoptions

This module contains widgets that are inserted in the psyplot GUI. Submodules
are

* :mod:`psy_simple.widgets.texts`: A module for the modification of labels
"""
import os.path as osp
from functools import partial
from psyplot_gui.compat.qtcompat import QToolButton, QMenu


def get_icon(fname):
    return osp.join(osp.dirname(__file__), 'icons', fname)


class Switch2FmtButton(QToolButton):
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
        QToolButton.__init__(self, parent=parent)
        self.setText('fmt')
        self.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu()
        for fmto in fmtos:
            name = parent.get_name(fmto)
            menu.addAction(name, partial(parent.set_fmto, name))
        self.setMenu(menu)
