v1.2.1
======
Changed
-------
* psy-simple has been moved from https://github.com/Chilipp/psy-simple to https://github.com/psyplot/psy-simple,
  see `#7 <https://github.com/psyplot/psy-simple/pull/7>`__

Fixed
-----
* Fixed a bug to calculate color bounds for uniform data,
  see `#9 <https://github.com/psyplot/psy-simple/pull/9>`__


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
