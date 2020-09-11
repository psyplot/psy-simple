# -*- coding: utf-8 -*-
"""colors module of the psyplot package.

This module contains some additional color maps and the show_colormaps
function to visualize available colormaps."""
import six
import matplotlib as mpl
from matplotlib.colors import Colormap, LinearSegmentedColormap, BoundaryNorm
from matplotlib.cm import get_cmap as mpl_get_cmap
import numpy as np
from difflib import get_close_matches
from itertools import chain
from warnings import warn
from psyplot.docstring import docstrings
from psyplot import rcParams
from psyplot.data import safe_list
import psyplot


_cmapnames = {  # names of self defined colormaps (see get_cmap function below)
    'red_white_blue': [  # symmetric water fluxes
        (1, 0, 0), (1, 0.5, 0), (1, 1, 0), (1, 1., 1),
        (0, 1, 1), (0, 0.5, 1), (0, 0, 1)],
    'blue_white_red': [  # symmetric temperature
        (0, 0, 1), (0, 0.5, 1), (0, 1, 1), (1, 1., 1),
        (1, 1, 0), (1, 0.5, 0), (1, 0, 0)],
    'white_blue_red': [  # temperature
        (1, 1., 1), (0, 0, 1), (0, 1, 1), (1, 1, 0), (1, 0, 0)],
    'white_red_blue': [  # water fluxes
        (1, 1., 1), (1, 0, 0), (1, 1, 0), (0, 1, 1), (0, 0, 1)],
    'rwb': [
        (1, 0, 0), (1, 1., 1), (0, 0, 1)],
    'wrb': [
        (1, 1., 1), (1, 0, 0), (0, 0, 1)],
    'wbr': [
        (1, 1., 1), (0, 0, 1), (1, 0, 0)]
    }
for key, val in list(_cmapnames.items()):
    _cmapnames[key + '_r'] = val[::-1]

_color_array = np.linspace(0, 1, 256, endpoint=True)

_cmapnames['w_RdBu'] = np.append(
    [[1., 1., 1., 1.]], mpl_get_cmap('RdBu')(_color_array), axis=0)
_cmapnames['w_RdBu_r'] = np.append(
    [[1., 1., 1., 1.]], mpl_get_cmap('RdBu_r')(_color_array), axis=0)

_cmapnames['w_Reds'] = np.append(
    [[1., 1., 1., 1.]], mpl_get_cmap('Reds')(_color_array), axis=0)

_cmapnames['w_Blues'] = np.append(
    [[1., 1., 1., 1.]], mpl_get_cmap('Blues')(_color_array), axis=0)

_cmapnames['w_Greens'] = np.append(
    [[1., 1., 1., 1.]], mpl_get_cmap('Greens')(_color_array), axis=0)


docstrings.params['cmap_note'] = """
        Strings may be any valid colormap name suitable for the
        :func:`matplotlib.cm.get_cmap` function or one of the color lists
        defined in the 'colors.cmaps' key of the :attr:`psyplot.rcParams`
        dictionary (including their reversed color maps given via the '_r'
        extension)."""


class FixedColorMap(LinearSegmentedColormap):
    """Bug fixing colormap with same functionality as matplotlibs colormap

    This class fixes a bug in the
    :meth:`cartopy.mpl.geoaxes.GeoAxes.streamplot` method in python 3.4

    Notes
    -----
    To reproduce the error type in python 3.4::

        >>> import cartopy.crs as ccrs
        >>> import matplotlib.pyplot as plt
        >>> import psyplot.project as psy
        >>> maps = psy.plot.mapvector(
        ...     'test-t2m-u-v.nc', name=[['u', 'v']], plot='stream',
        ...     lonlatbox='Europe', color='absolute')
        >>> plotter = maps[0].plotter
        >>> x, y, u, v = plotter.plot._get_data()
        >>> maps.close(True, True)
        >>> ax = plt.axes(projection=ccrs.PlateCarree())
        >>> ax.set_extent(plotter.lonlatbox.lonlatbox, crs=ccrs.PlateCarree())
        >>> m = ax.streamplot(x, y, u, v, density=[1.0, 1.0],
        ...                   color=plotter.plot._kwargs['color'],
        ...                   norm=plotter.plot._kwargs['norm'])

    This raises in matplotlib.colors, line 557, in
    :meth:`matplotlib.colors.Colormap.__call__`::

        ``xa = np.array([X])``
        ValueError: setting an array element with a sequence.
    """

    if six.PY3:
        def __call__(self, X, *args, **kwargs):
            if isinstance(X, np.ma.core.MaskedArray) and X.ndim == 0:
                X = np.array(np.nan)
            return super(FixedColorMap, self).__call__(X, *args, **kwargs)

        @staticmethod
        def from_list(*args, **kwargs):
            cmap = LinearSegmentedColormap.from_list(*args, **kwargs)
            return FixedColorMap(cmap.name, cmap._segmentdata, cmap.N,
                                 cmap._gamma)


class FixedBoundaryNorm(BoundaryNorm):
    """Bug fixing Norm with same functionality as matplotlibs BoundaryNorm

    This class fixes a bug in the
    :meth:`cartopy.mpl.geoaxes.GeoAxes.streamplot` for matplotlib version 1.5

    Notes
    -----
    To reproduce the error type::

        >>> import cartopy.crs as ccrs
        >>> import matplotlib.pyplot as plt
        >>> import psyplot.project as psy
        >>> import matplotlib.colors as mcol
        >>> maps = psy.plot.mapvector(
        ...     'test-t2m-u-v.nc', name=[['u', 'v']], plot='stream',
        ...     lonlatbox='Europe', color='absolute')
        >>> plotter = maps[0].plotter
        >>> x, y, u, v = plotter.plot._get_data()
        >>> maps.close(True, True)
        >>> ax = plt.axes(projection=ccrs.PlateCarree())
        >>> ax.set_extent(plotter.lonlatbox.lonlatbox, crs=ccrs.PlateCarree())
        >>> m = ax.streamplot(
        ...     x, y, u, v, color=plotter.plot._kwargs['color'],
        ...     norm=mcol.BoundaryNorm(plotter.bounds.norm.boundaries,
        ...                            plotter.bounds.norm.Ncmap,
        ...                            plotter.bounds.norm.clip),
        ...                            density=[1.0, 1.0])

    This raises in matplotlib.colors, line 1316, in
    :meth:`matplotlib.colors.BoundaryNorm.__call__`::

        ``ret = int(ret[0])  # assume python scalar``
        MaskError: Cannot convert masked element to a Python int.
    """

    if mpl.__version__ > '1.4':
        def __call__(self, value, clip=None):
            if isinstance(value, np.ma.core.MaskedConstant):
                return value
            return super(FixedBoundaryNorm, self).__call__(value, clip=clip)


@docstrings.dedent
def get_cmap(name, lut=None):
    """
    Returns the specified colormap.

    Parameters
    ----------
    name: str or :class:`matplotlib.colors.Colormap`
        If a colormap, it returned unchanged.
        %(cmap_note)s
    lut: int
        An integer giving the number of entries desired in the lookup table

    Returns
    -------
    matplotlib.colors.Colormap
        The colormap specified by `name`

    See Also
    --------
    show_colormaps: A function to display all available colormaps

    Notes
    -----
    Different from the :func::`matpltolib.pyplot.get_cmap` function, this
    function changes the number of colors if `name` is a
    :class:`matplotlib.colors.Colormap` instance to match the given `lut`."""
    if name in rcParams['colors.cmaps']:
        colors = rcParams['colors.cmaps'][name]
        lut = lut or len(colors)
        return FixedColorMap.from_list(name=name, colors=colors, N=lut)
    elif name in _cmapnames:
        colors = _cmapnames[name]
        lut = lut or len(colors)
        return FixedColorMap.from_list(name=name, colors=colors, N=lut)
    else:
        cmap = mpl_get_cmap(name)
        # Note: we could include the `lut` in the call of mpl_get_cmap, but
        # this raises a ValueError for colormaps like 'viridis' in mpl version
        # 1.5. Besides the mpl_get_cmap function does not modify the lut if
        # it does not match
        if lut is not None and cmap.N != lut:
            cmap = FixedColorMap.from_list(
                name=cmap.name, colors=cmap(np.linspace(0, 1, lut)), N=lut)
        return cmap


def _get_cmaps(names):
    """Filter the given `names` for colormaps"""
    import matplotlib.pyplot as plt
    available_cmaps = list(
        chain(plt.cm.cmap_d, _cmapnames, rcParams['colors.cmaps']))
    names = safe_list(names)
    wrongs = []
    for arg in (arg for arg in names if (not isinstance(arg, Colormap) and
                                         arg not in available_cmaps)):
        if isinstance(arg, str):
            similarkeys = get_close_matches(arg, available_cmaps)
        if similarkeys != []:
            warn("Colormap %s not found in standard colormaps.\n"
                 "Similar colormaps are %s." % (arg, ', '.join(similarkeys)))
        else:
            warn("Colormap %s not found in standard colormaps.\n"
                 "Run function without arguments to see all colormaps" % arg)
        names.remove(arg)
        wrongs.append(arg)
    if not names and not wrongs:
        names = sorted(m for m in available_cmaps if not m.endswith("_r"))
    return names


@docstrings.get_sections(base='show_colormaps')
@docstrings.dedent
def show_colormaps(names=[], N=10, show=True, use_qt=None):
    """Function to show standard colormaps from pyplot

    Parameters
    ----------
    ``*args``: str or :class:`matplotlib.colors.Colormap`
        If a colormap, it returned unchanged.
        %(cmap_note)s
    N: int, optional
        Default: 11. The number of increments in the colormap.
    show: bool, optional
        Default: True. If True, show the created figure at the end with
        pyplot.show(block=False)
    use_qt: bool
        If True, use the
        :class:`psy_simple.widgets.color.ColormapDialog.show_colormaps`, if
        False use a matplotlib implementation based on [1]_. If None, use
        the Qt implementation if it is running in the psyplot GUI.

    Returns
    -------
    psy_simple.widgets.color.ColormapDialog or matplitlib.figure.Figure
        Depending on `use_qt`, either an instance of the
        :class:`psy_simple.widgets.color.ColormapDialog` or the
        :class:`matplotlib.figure.Figure`

    References
    ----------
    .. [1] http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html
    """
    names = safe_list(names)
    if use_qt or (use_qt is None and psyplot.with_gui):
        from psy_simple.widgets.colors import ColormapDialog
        from psyplot_gui.main import mainwindow
        return ColormapDialog.show_colormap(names, N, show, parent=mainwindow)
    import matplotlib.pyplot as plt
    # This example comes from the Cookbook on www.scipy.org.  According to the
    # history, Andrew Straw did the conversion from an old page, but it is
    # unclear who the original author is.
    a = np.vstack((np.linspace(0, 1, 256).reshape(1, -1)))
    # Get a list of the colormaps in matplotlib.  Ignore the ones that end with
    # '_r' because these are simply reversed versions of ones that don't end
    # with '_r'
    cmaps = _get_cmaps(names)
    nargs = len(cmaps) + 1
    fig = plt.figure(figsize=(5, 10))
    fig.subplots_adjust(top=0.99, bottom=0.01, left=0.2, right=0.99)
    for i, m in enumerate(cmaps):
        ax = plt.subplot(nargs, 1, i+1)
        plt.axis("off")
        plt.pcolormesh(a, cmap=get_cmap(m, N + 1))
        pos = list(ax.get_position().bounds)
        fig.text(pos[0] - 0.01, pos[1], m, fontsize=10,
                 horizontalalignment='right')
    fig.canvas.set_window_title("Figure %i: Predefined colormaps" % fig.number)
    if show:
        plt.show(block=False)
    return fig
