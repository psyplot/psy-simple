v1.4.0
======
Compatibility fixes and LGPL license

As with psyplot 1.4.0, psy-simple is now continuously tested and deployed with
CircleCI.

Fixed
-----
- Compatibility fixes for matplotlib>=3.3

Changed
-------
- psy-simple is now officially licensed under LGPL-3.0-only,
  see `#28 <https://github.com/psyplot/psy-simple/pull/28>`__
- We use CicleCI now for a standardized CI/CD pipeline to build and test
  the code and docs all at one place, see `#27 <https://github.com/psyplot/psy-simple/pull/27>`__


v1.3.1
======
Patch for plotting the polygons with 3D bounds

Changed
-------
* the values ``'tri'``, ``'tricontour'`` and ``'tricontourf'`` for the ``plot``
  formatoptions have been depreceated and should be replaced by ``'poly'``,
  ``'contour'`` and ``'contourf'`` respectively, see
  `#23 <https://github.com/psyplot/psy-simple/pull/23>`__

Fixed
-----
* A bug was fixed with the ``extend`` formatoption if ``plot=None``, see
  `#20 <https://github.com/psyplot/psy-simple/pull/20>`__
* variables with 3D bounds are now interpreted correctly, see
  `#24 <https://github.com/psyplot/psy-simple/pull/24>`__

v1.3.0
======
New background and mask formatoptions and more options for colorbar bounds

Added
-----
* a new ``background`` formatoption has been implemented that allows to set the
  facecolor of the axes (i.e. the background color for the plot)
* a new ``mask`` formatoption has been implemented that allows to mask the
  data based on a mask that can either be in the dataset or in a separate
  file (see `#15 <https://github.com/psyplot/psy-simple/pull/15>`__)
* the ``bounds`` and other ``ticks`` (e.g. ``xticks, yticks, cticks``)
  formatoptions have gained multiple new  values (all backwards-compatible, see
  `#13 <https://github.com/psyplot/psy-simple/pull/13>`__):

  * they now support discrete logarithmic and symmetric bounds/ticks via
    ``bounds='log'`` and ``bounds='symlog'``.
  * The bounds and other tick formatoptions (`xticks, cticks, yticks, etc.`) now
    support a dictionary as a value, e.g.::

        plotter.update(bounds={'method': 'rounded', 'percmin': 5})
  * You can specify ``vmin`` and ``vmax`` for color bounds and ticks which
    prevents their automatic estimation, e.g. via::

        plotter.update(bounds={'method': 'rounded', 'vmin': 50, 'vmax': 75})
        # or
        plotter.update(bounds=['rounded', None, None, None, 50, 75])

Changed
-------
* values in the statusbar are only shown, if the drawn artist contains the
  cursor position, see `#18 <https://github.com/psyplot/psy-simple/pull/18>`__
* psy-simple now requires matplotlib greater or equal than 2.0
* psy-simple has been moved from https://github.com/Chilipp/psy-simple to https://github.com/psyplot/psy-simple,
  see `#7 <https://github.com/psyplot/psy-simple/pull/7>`__
* The color handling of the `color` formatoption has been changed to allow
  appending of new data. The `colors` attribute can be extended by the
  `color_cycle` using the `extended_colors` attribute (see
  `#10 <https://github.com/psyplot/psy-simple/pull/10>`__)

Fixed
-----
* Fixed a bug to calculate color bounds for uniform data,
  see `#9 <https://github.com/psyplot/psy-simple/pull/9>`__
* An issue has been fixed with the setting of colorbar ticks after updating
  the colorbar bounds (see `#13 <https://github.com/psyplot/psy-simple/pull/13>`__)


v1.2.0
======
Added
-----
* The ``plot2d`` plotmethod now also supports unstructured data of any shape
  (see `issue#6 <https://github.com/psyplot/psyplot/issues/6>`__)
* Added a ``categorical`` formatoption to the ``barplot`` plot method to allow
  a switch between categorical and non-categorical plots
* The lineplot method now also support ``'stacked'`` plots

v1.1.0
======
Added
-----
* Changelog
* ``interp_bounds`` formatoption for the ``plot2d`` plot method (see the
  `docs <https://psyplot.readthedocs.io/projects/psy-simple/en/latest/api/psy_simple.plotters.html#psy_simple.plotters.Simple2DPlotter.interp_bounds>`__)
* Added the ``fldmean`` plot method that can be used to directly calculate and
  plot the mean over the x- and y-dimensions

Changed
-------
* The xlim and ylim formatoptions now consider inverted x- and y-axes
