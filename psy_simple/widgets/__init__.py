"""Module for PyQt4/PyQt5 widgets for modifying the formatoptions

This module contains widgets that are inserted in the psyplot GUI. Submodules
are

* :mod:`psy_simple.widgets.texts`: A module for the modification of labels
"""
import os.path as osp


def get_icon(fname):
    return osp.join(osp.dirname(__file__), 'icons', fname)
