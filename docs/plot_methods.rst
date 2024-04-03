.. SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0

.. _plot_methods:

psyplot plot methods
====================

This plugin defines the following new plot methods for the
:class:`psyplot.project.ProjectPlotter` class. They can, for example, be
accessed through

.. ipython::

    In [1]: import psyplot.project as psy

    In [2]: psy.plot.lineplot

.. autosummary::
    :toctree: generated

    ~psyplot.project.plot.lineplot
    ~psyplot.project.plot.vector
    ~psyplot.project.plot.violinplot
    ~psyplot.project.plot.plot2d
    ~psyplot.project.plot.combined
    ~psyplot.project.plot.density
    ~psyplot.project.plot.barplot
    ~psyplot.project.plot.fldmean
