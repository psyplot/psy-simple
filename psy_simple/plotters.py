import six
import re
from warnings import warn
from psyplot.warning import PsyPlotRuntimeWarning
from abc import abstractproperty, abstractmethod
from functools import partial
from itertools import chain, starmap, cycle, islice, repeat
from pandas import (
    date_range, to_datetime, DatetimeIndex, to_timedelta, MultiIndex)
import weakref
from pandas.tseries import offsets
import xarray as xr
import matplotlib as mpl
import matplotlib.axes
from matplotlib.ticker import FormatStrFormatter, FixedLocator, FixedFormatter
from matplotlib.dates import DateFormatter, AutoDateFormatter
import matplotlib.colors as mcol
import numpy as np
from psyplot.docstring import docstrings, dedent
from psyplot.plotter import (
    Plotter, Formatoption, BEFOREPLOTTING, DictFormatoption, END, rcParams,
    START)
from psy_simple.base import (
    BasePlotter, TextBase, label_size, label_weight, label_props, MaskLess,
    MaskGreater, MaskBetween, MaskLeq, MaskGeq, Mask)
from psy_simple.colors import get_cmap
from psyplot.data import (
    InteractiveList, isstring, CFDecoder, _infer_interval_breaks)
from psyplot.compat.pycompat import map, zip, range
from psy_simple.plugin import (
    validate_color, validate_float, safe_list as slist)
from psyplot.utils import is_iterable


def _get_index_vals(index):
    if (isinstance(index, MultiIndex) and
            len(index.names) == 1):
        return index.get_level_values(0).values
    else:
        return index.values


def round_to_05(n, exp=None, mode='s'):
    """
    Round to the next 0.5-value.

    This function applies the round function `func` to round `n` to the
    next 0.5-value with respect to its exponent with base 10 (i.e.
    1.3e-4 will be rounded to 1.5e-4) if `exp` is None or with respect
    to the given exponent in `exp`.

    Parameters
    ----------
    n: numpy.ndarray
        number to round
    exp: int or numpy.ndarray
        Exponent for rounding. If None, it will be computed from `n` to be the
        exponents for base 10.
    mode: {'s', 'l'}
        rounding mode. If 's', it will be rounded to value whose absolute
        value is below `n`, if 'l' it will rounded to the value whose absolute
        value is above `n`.

    Returns
    -------
    numpy.ndarray
        rounded `n`

    Examples
    --------
    The effects of the different parameters are show in the example below::

        >>> from psyplot.plotter.simple import round_to_05
        >>> a = [-100.3, 40.6, 8.7, -0.00023]
        >>>round_to_05(a, mode='s')
        array([ -1.00000000e+02,   4.00000000e+01,   8.50000000e+00,
                -2.00000000e-04])

        >>> round_to_05(a, mode='l')
        array([ -1.50000000e+02,   4.50000000e+01,   9.00000000e+00,
                -2.50000000e-04])"""
    n = np.asarray(n)
    if exp is None:
        exp = np.floor(np.log10(np.abs(n)))  # exponent for base 10
    ntmp = np.abs(n)/10.**exp  # mantissa for base 10
    if mode == 's':
        n1 = ntmp
        s = 1.
        n2 = nret = np.floor(ntmp)
    else:
        n1 = nret = np.ceil(ntmp)
        s = -1.
        n2 = ntmp
    return np.where(n1 - n2 > 0.5, np.sign(n)*(nret + s*0.5)*10.**exp,
                    np.sign(n)*nret*10.**exp)


def convert_radian(coord, *variables):
    """Convert the given coordinate from radian to degree

    Parameters
    ----------
    coord: xr.Variable
        The variable to transform
    ``*variables``
        The variables that are on the same unit.

    Returns
    -------
    xr.Variable
        The transformed variable if one of the given `variables` has units in
        radian"""
    if any(v.attrs.get('units', '').startswith('radian') for v in variables):
        return coord * 180. / np.pi
    return coord


class AlternativeXCoord(Formatoption):
    """
    Use an alternative variable as x-coordinate

    This formatoption let's you specify another variable in the base dataset
    of the data array in case you want to use this as the x-coordinate instead
    of the raw data

    Possible types
    --------------
    None
        Use the default
    str
        The name of the variable to use in the base dataset
    xarray.DataArray
        An alternative variable with the same shape as the displayed array

    Examples
    --------
    To see the difference, we create a simple test dataset::

        >>> import xarray as xr

        >>> import numpy as np

        >>> import psyplot.project as psy

        >>> ds = xr.Dataset({
        ...     'temp': xr.Variable(('time', ), np.arange(5)),
        ...     'std': xr.Variable(('time', ), np.arange(5, 10))})
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 5)
        Coordinates:
          * time     (time) int64 0 1 2 3 4
        Data variables:
            temp     (time) int64 0 1 2 3 4
            std      (time) int64 5 6 7 8 9

    If we create a plot with it, we get the ``'time'`` dimension on the
    x-axis::

        >>> plotter = psy.plot.lineplot(ds, name=['temp']).plotters[0]

        >>> plotter.plot_data[0].dims
        ('time',)

    If we however set the ``'coord'`` keyword, we get::

        >>> plotter = psy.plot.lineplot(
        ...     ds, name=['temp'], coord='std').plotters[0]

        >>> plotter.plot_data[0].dims
        ('std',)

    and ``'std'`` is plotted on the x-axis."""

    name = 'Alternative X-Variable'

    group = 'data'

    priority = START

    data_dependent = True

    #: Bool. If True, this Formatoption directly uses the raw_data, otherwise
    #: use the normal data
    use_raw_data = True

    @property
    def data_iterator(self):
        return self.iter_raw_data if self.use_raw_data else self.iter_data

    def update(self, value):
        if value is not None:
            for i, da in enumerate(self.data_iterator):
                self.set_data(self.replace_coord(i), i)

    def diff(self, value):
        try:
            return ~((np.shape(value) == np.shape(self.value)) &
                     np.all(value == self.value))
        except TypeError:
            return True

    def replace_coord(self, i):
        """Replace the coordinate for the data array at the given position

        Parameters
        ----------
        i: int
            The number of the data array in the raw data (if the raw data is
            not an interactive list, use 0)

        Returns
        xarray.DataArray
            The data array with the replaced coordinate"""
        da = next(islice(self.data_iterator, i, i+1))
        name, coord = self.get_alternative_coord(da, i)
        other_coords = {key: da.coords[key]
                        for key in set(da.coords).difference(da.dims)}
        ret = da.rename({da.dims[-1]: name}).assign_coords(
            **{name: coord}).assign_coords(**other_coords)
        return ret

    def get_alternative_coord(self, da, i):
        if isinstance(self.value, xr.DataArray):
            return self.value.name, self.value.variable
        alternative_name = next(islice(cycle(slist(self.value)), i, i+1))
        coord_da = InteractiveList.from_dataset(
            da.psy.base, name=alternative_name, dims=da.psy.idims)[0]
        coord = xr.Variable((coord_da.name, ), coord_da, coord_da.attrs)
        return coord_da.name, coord


class AlternativeXCoordPost(AlternativeXCoord):
    # The same as the :class:`AlternativeXCoord, but it uses the
    # :attr:`psyplot.plotter.Formatoption.data` attribute as a src, not the
    # :attr:`psyplot.plotter.Formatoption.raw_data`

    __doc__ = AlternativeXCoord.__doc__

    use_raw_data = False


class Grid(Formatoption):
    """
    Display the grid

    Show the grid on the plot with the specified color.


    Possible types
    --------------
    None
        If the grid is currently shown, it will not be displayed any longer. If
        the grid is not shown, it will be drawn
    bool
        If True, the grid is displayed with the automatic settings (usually
        black)
    string, tuple.
        Defines the color of the grid.

    Notes
    -----
    %(colors)s"""

    group = 'axes'

    name = 'Grid lines'

    def update(self, value):
        try:
            value = validate_color(value)
            self.ax.grid(color=value)
        except (ValueError, TypeError, AttributeError):
            self.ax.grid(value)


class AxisColor(DictFormatoption):
    """
    Color the x- and y-axes

    This formatoption colors the left, right, bottom and top axis bar.

    Possible types
    --------------
    dict
        Keys may be one of {'right', 'left', 'bottom', 'top'},  the values can
        be any valid color or None.

    Notes
    -----
    %(colors)s"""

    group = 'axes'

    name = 'Color of x- and y-axes'

    @property
    def value2pickle(self):
        """Return the current axis colors"""
        return {key: s.get_edgecolor() for key, s in self.ax.spines.items()}

    def initialize_plot(self, value):
        positions = ['right', 'left', 'bottom', 'top']
        #: :class:`dict` storing the default linewidths
        self.default_lw = dict(zip(positions, map(
            lambda pos: self.ax.spines[pos].get_linewidth(), positions)))
        self.update(value)

    def update(self, value):
        for pos, color in six.iteritems(value):
            spine = self.ax.spines[pos]
            spine.set_color(color)
            if color is not None and spine.get_linewidth() == 0.0:
                spine.set_linewidth(1.0)
            elif color is None:
                spine.set_color(mpl.rcParams['axes.edgecolor'])
                spine.set_linewidth(self.default_lw[pos])


class TicksManagerBase(Formatoption):
    """
    Abstract base class for formatoptions handling ticks"""

    @abstractmethod
    def update_axis(self, val):
        pass


@docstrings.get_sections(base='TicksManager')
class TicksManager(TicksManagerBase, DictFormatoption):
    """
    Abstract base class for ticks formatoptions controlling major and minor
    ticks

    This formatoption simply serves as a base that allows the simultaneous
    managment of major and minor ticks

    Possible types
    --------------
    dict
        A dictionary with the keys ``'minor'`` and (or) ``'major'`` to specify
        which ticks are managed. If the given value is not a dictionary with
        those keys, it is put into a dictionary with the key determined by the
        rcParams ``'ticks.which'`` key (usually ``'major'``).
        The values in the dictionary can be one types below."""

    group = 'ticks'

    def update(self, value):
        for which, val in six.iteritems(value):
            self.which = which
            self.update_axis(val)


@docstrings.get_sections(base='DataTicksCalculator')
class DataTicksCalculator(Formatoption):
    """
    Abstract base formatoption to calculate ticks and bounds from the data

    Possible types
    --------------
    numeric array
        specifies the ticks manually
    str or list [str, ...]
        A list of the below mentioned values of the mapping like
        ``[method, N, percmin, percmax, vmin, vmax]``, where only the first
        one is absolutely necessary
    dict
        Automatically determine the ticks corresponding to the data. The
        mapping can have the following keys, but only `method` is not optional.

        N
            An integer describing the number of boundaries (or ticks per
            power of ten, see `log` and `symlog` above)
        percmin
            The percentile to use for the minimum (by default, 0, i.e. the
            minimum of the array)
        percmax
            The percentile to use for the maximum (by default, 100, i.e. the
            maximum of the array)
        vmin
            The minimum to use (in which case it is not calculated from the
            specified `method`)
        vmax
            The maximum to use (in which case it is not calculated from the
            specified `method`)
        method
            A string that defines how minimum and maximum shall be set. This
            argument is **not optional** and can be one of the following:

            data
                plot the ticks exactly where the data is.
            mid
                plot the ticks in the middle of the data.
            rounded
                Sets the minimum and maximum of the ticks to the rounded data
                minimum or maximum. Ticks are rounded to the next 0.5 value
                with to the difference between data max- and minimum. The
                minimal tick will always be lower or equal than the data
                minimum, the maximal tick will always be higher or equal than
                the data maximum.
            roundedsym
                Same as `rounded` above but the ticks are chose such that they
                are symmetric around zero
            minmax
                Uses the minimum as minimal tick and maximum as maximal tick
            sym
                Same as minmax but symmetric around zero
            log
                Use logarithmic bounds. In this case, the given number `N`
                determines the number of bounds per power of tenth (i.e.
                ``N == 2`` results in something like ``1.0, 5.0, 10.0, 50.0``,
                etc., If this second number is None, then it will be chosen
                such that we have around 11 boundaries but at least one per
                power of ten.
            symlog
                The same as ``log`` but symmetric around 0. If the number `N`
                is None, then we have around 12 boundaries but at least one
                per power of ten"""

    data_dependent = True

    @property
    def full_array(self):
        """The full array of this and the shared data"""
        return np.concatenate(
            [self.array] + [fmto.array for fmto in self.shared])

    @property
    def array(self):
        """The numpy array of the data"""
        data = self.data
        if not hasattr(data, 'notnull'):
            data = data.to_series()
        mask = np.asarray(data.notnull())
        return data.values[mask]

    def _data_ticks(self, step=None, *args, **kwargs):
        step = step or 1
        """Array of ticks that match exactly the data"""
        return np.unique(self.array)[::step]

    def _mid_data_ticks(self, step=None, *args, **kwargs):
        step = step or 1
        """Array of ticks in the middle between the data points"""
        arr = np.unique(self.array)
        return ((arr[:-1] + arr[1:])/2.)[::step]

    def _collect_array(self, percmin=None, percmax=None):
        """Collect the data from the shared formatoptions (if necessary)."""

        def nanmin(arr):
            try:
                return np.nanmin(arr)
            except TypeError:
                return arr.min()

        def nanmax(arr):
            try:
                return np.nanmax(arr)
            except TypeError:
                return arr.max()

        def minmax(arr):
            return [nanmin(arr), nanmax(arr)]

        def shared_arrays():
            for fmto in self.shared:
                fmto._lock_children()
                # do not lock the fmto itself, because this breaks the plotter
                # update procedure. But make sure, that the dependencies are
                # locked
                arr = fmto.array
                yield arr
                # release the locks
                fmto._release_children()

        if not self.shared:
            arr = self.array
        else:
            # np.concatenate all arrays if any of the percentiles are required
            if percmin is not None or percmax is not None:
                arr = np.concatenate(tuple(chain(
                    [self.array], shared_arrays())))
            # np.concatenate only min and max-values instead of the full arrays
            else:
                arr = np.concatenate(tuple(map(minmax, chain(
                    [self.array], shared_arrays()))))
        return arr

    def _calc_vmin_vmax(self, percmin=None, percmax=None,
                        vmin=None, vmax=None):

        def nanmin(arr):
            try:
                return np.nanmin(arr)
            except TypeError:
                return arr.min()

        def nanmax(arr):
            try:
                return np.nanmax(arr)
            except TypeError:
                return arr.max()

        if vmin is not None and vmax is not None:
            return vmin, vmax

        percentiles = []
        arr = self._collect_array(percmin, percmax)
        try:
            if vmin is not None:
                pass
            elif not percmin:
                vmin = nanmin(arr)
            else:
                percentiles.append(percmin)
            if vmax is not None:
                pass
            elif percmax is None or percmax == 100:
                vmax = nanmax(arr)
            else:
                percentiles.append(percmax)
        except ValueError:
            self.logger.warn(
                'Cannot calculate minimum and maximum of the data!',
                exc_info=True)
            return 0, 1
        if percentiles:
            percentiles = iter(np.percentile(arr, percentiles))
            if percmin:
                vmin = next(percentiles)
            if percmax and percmax < 100:
                vmax = next(percentiles)
        return vmin, vmax

    @staticmethod
    def _round_min_max(vmin, vmax):
        if vmin == vmax:
            return vmin, vmax
        exp = np.floor(np.log10(abs(vmax - vmin)))
        larger = round_to_05([vmin, vmax], exp, mode='l')
        smaller = round_to_05([vmin, vmax], exp, mode='s')
        return min([larger[0], smaller[0]]), max([larger[1], smaller[1]])

    def _rounded_ticks(self, N=None, *args, **kwargs):
        N = N or 11
        vmin, vmax = self._round_min_max(
            *self._calc_vmin_vmax(*args, **kwargs))
        return np.linspace(vmin, vmax, N, endpoint=True)

    def _log_bounds(self, expmin, expmax, N):
        bounds = []
        for i in range(int(expmax - expmin)):
            new_vals = np.linspace(1 * 10 ** (expmin + i),
                                   9 * 10 ** (expmin + i), N + 1)[:-1]
            bounds.extend(new_vals)
        return bounds

    def _log_ticks(self, symmetric=False, N=None, *args, **kwargs):
        vmin, vmax = self._calc_vmin_vmax(*args, **kwargs)
        larger = round_to_05([vmin, vmax], mode='l')
        smaller = round_to_05([vmin, vmax], mode='s')
        vmin, vmax = min([larger[0], smaller[0]]), max([larger[1], smaller[1]])

        if symmetric and np.sign(vmin) == np.sign(vmax):
            if vmin < 0:  # make vmax positive
                vmax = -vmax
            else:  # make vmin negative
                vmin = -vmin
        elif symmetric:
            vmax = np.max([-vmin, vmax])
            vmin = -vmax

        if vmin == vmax:
            return vmin, vmax

        signs = np.sign([vmin, vmax])
        crossing0 = vmin != 0 and vmax != 0 and signs[0] != signs[1]
        if not crossing0:
            vmin, vmax = np.sort(np.abs([vmin, vmax]))
            vmin0 = vmax
            vmax0 = vmin

            expmin, expmax = np.floor(np.log10(np.abs([vmin, vmax])))

            dexp = int(expmax - expmin)
            expmax0 = np.inf
        else:  # vmin < 0, vmax > 0
            arr = self._collect_array()
            less0 = arr < 0
            greater0 = arr > 0
            if not less0.size:
                vmin0 = round_to_05(arr[arr > 0].min(), mode='s')
                vmax0 = -vmin0
            elif not greater0.size:
                vmax0 = round_to_05(arr[arr < 0].max(), mode='l')
                vmin0 = -vmax0
            else:
                vmin0 = round_to_05(arr[arr > 0].min(), mode='s')
                vmax0 = round_to_05(arr[arr < 0].max(), mode='l')
                if symmetric:
                    vmin0 = min(-vmax0, vmin0)
                    vmax0 = -vmin0

            expmin, expmax0 = np.floor(np.log10(np.abs([vmax0, vmin])))
            expmin0, expmax = np.floor(np.log10(np.abs([vmin0, vmax])))

            dexp_neg = int(expmax0 - expmin)
            dexp_pos = int(expmax - expmin0)

            dexp = int(dexp_neg + dexp_pos)

        if dexp == 0 or (dexp == 1 and vmax == 1 * 10**expmax):
            # effectively only one factor of 10 (e.g. vmin = 1, vmax = 10)
            N = N or (11 if not symmetric else 12)
            return np.linspace(vmin, vmax, N, endpoint=True)
        else:
            if N is None:
                # we go close to 11 bounds in total
                N = int(max(np.floor((11 if not symmetric else 12) / dexp), 1))
            if not crossing0:
                bounds = self._log_bounds(expmin, expmax, N)
                bounds += [1*10**expmax]
                if signs[0] == -1 and signs[1] == -1:
                    bounds = -np.array(bounds)
            else:
                bounds_neg = -np.array(self._log_bounds(expmin, expmax0, N))
                bounds_pos = self._log_bounds(expmin0, expmax, N)
                bounds = np.unique(
                    np.r_[bounds_neg, bounds_pos,
                          -1 * 10 ** expmin, -1 * 10 ** expmax0,
                          1 * 10 ** expmin0, 1 * 10 ** expmax])
                bounds = bounds[(bounds <= vmax0) | (bounds >= vmin0)]

            return np.unique(bounds)

    def _roundedsym_ticks(self, N=None, *args, **kwargs):
        N = N or 10
        vmax = max(map(abs, self._round_min_max(
            *self._calc_vmin_vmax(*args, **kwargs))))
        vmin = -vmax
        return np.linspace(vmin, vmax, N, endpoint=True)

    def _data_minmax_ticks(self, N=None, *args, **kwargs):
        N = N or 11
        vmin, vmax = self._calc_vmin_vmax(*args, **kwargs)
        return np.linspace(vmin, vmax, N, endpoint=True)

    def _data_symminmax_ticks(self, N=None, *args, **kwargs):
        N = N or 10
        vmax = max(map(abs, self._calc_vmin_vmax(*args, **kwargs)))
        vmin = -vmax
        return np.linspace(vmin, vmax, N, endpoint=True)

    def __init__(self, *args, **kwargs):
        super(DataTicksCalculator, self).__init__(*args, **kwargs)
        self.calc_funcs = {
            'data': self._data_ticks,
            'mid': self._mid_data_ticks,
            'rounded': self._rounded_ticks,
            'roundedsym': self._roundedsym_ticks,
            'minmax': self._data_minmax_ticks,
            'sym': self._data_symminmax_ticks,
            'log': partial(self._log_ticks, False),
            'symlog': partial(self._log_ticks, True),
            }


@docstrings.get_sections(base='TicksBase')
class TicksBase(TicksManagerBase, DataTicksCalculator):
    """
    Abstract base class for calculating ticks

    Possible types
    --------------
    None
        use the default ticks
    int
        for an integer *i*, only every *i-th* tick of the default ticks are
        used"""

    dependencies = ['transpose', 'plot']

    group = 'ticks'

    @abstractproperty
    def axis(self):
        pass

    def __init__(self, *args, **kwargs):
        super(TicksBase, self).__init__(*args, **kwargs)
        self.default_locators = {}

    def initialize_plot(self, value):
        self.set_default_locators()
        self.update(value)

    def update_axis(self, value):
        which = self.which
        if value is None:
            self.set_locator(self.default_locators[which])
        elif isinstance(value, int):
            return self._reduce_ticks(value)
        elif len(value) and isinstance(value[0], six.string_types):
            return self.set_ticks(self.calc_funcs[value[0]](*value[1:]))
        elif isinstance(value, tuple):
            steps = 11 if len(value) == 2 else value[3]
            self.set_ticks(np.linspace(value[0], value[1], steps,
                                       endpoint=True))
        else:
            self.set_ticks(value)

    def set_ticks(self, value):
        self.axis.set_ticks(value, minor=self.which == 'minor')

    def get_locator(self):
        return getattr(self.axis, 'get_%s_locator' % self.which)()

    def set_locator(self, locator):
        """Sets the locator corresponding of the axis

        Parameters
        ----------
        locator: matplotlib.ticker.Locator
            The locator to set
        which: {None, 'minor', 'major'}
            Specify which locator shall be set. If None, it will be taken from
            the :attr:`which` attribute"""
        getattr(self.axis, "set_%s_locator" % self.which)(locator)

    def set_default_locators(self, which=None):
        """Sets the default locator that is used for updating to None or int

        Parameters
        ----------
        which: {None, 'minor', 'major'}
            Specify which locator shall be set"""
        if which is None or which == 'minor':
            self.default_locators['minor'] = self.axis.get_minor_locator()
        if which is None or which == 'major':
            self.default_locators['major'] = self.axis.get_major_locator()

    def _reduce_ticks(self, i):
        loc = self.default_locators[self.which]
        self.set_locator(FixedLocator(loc()[::i]))


@docstrings.get_sections(base='DtTicksBase')
class DtTicksBase(TicksBase, TicksManager):
    """
    Abstract base class for x- and y-tick formatoptions

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(TicksBase.possible_types)s
    %(DataTicksCalculator.possible_types)s
            hour
                draw ticks every hour
            day
                draw ticks every day
            week
                draw ticks every week
            month, monthend, monthbegin
                draw ticks in the middle, at the end or at the beginning of each
                month
            year, yearend, yearbegin
                draw ticks in the middle, at the end or at the beginning of each
                year

        For data, mid, hour, day, week, month, etc., the optional second value
        can be an integer i determining that every i-th data point shall be
        used (by default, it is set to 1). For rounded, roundedsym, minmax and
        sym, the second value determines the total number of ticks (defaults to
        11)."""

    def __init__(self, *args, **kwargs):
        super(DtTicksBase, self).__init__(*args, **kwargs)
        self.calc_funcs.update({
            'hour': self._frequent_ticks('H'),
            'day': self._frequent_ticks('D'),
            'week': self._frequent_ticks(offsets.Week()),
            'month': self._mid_dt_ticks('M'),
            'monthend': self._frequent_ticks(
                offsets.MonthEnd(), onset=offsets.MonthBegin()),
            'monthbegin': self._frequent_ticks(
                offsets.MonthBegin(), onset=offsets.MonthBegin(),
                offset=offsets.MonthBegin()),
            'year': self._mid_dt_ticks(offsets.YearBegin()),
            'yearend': self._frequent_ticks(
                offsets.YearEnd(), onset=offsets.YearBegin()),
            'yearbegin': self._frequent_ticks(
                offsets.YearBegin(), onset=offsets.YearBegin(),
                offset=offsets.YearBegin())})

    def update(self, value):
        value = value or {'minor': None, 'major': None}
        super(DtTicksBase, self).update(value)

    @property
    def dtdata(self):
        """The np.unique :attr:`data` as datetime objects"""
        data = self.data
        # do nothing if the data is a pandas.Index without time informations
        # or not a pandas.Index
        if not getattr(data, 'is_all_dates', None):
            warn("[%s] - Could not convert time informations for %s ticks "
                 "with object %r." % (self.logger.name, self.key, type(data)))
            return None
        else:
            return data

    def _frequent_ticks(self, freq, onset=None, offset=None):
        def func(N=None, *args, **kwargs):
            step = N or 1
            data = self.dtdata
            if data is None:
                return
            mindata = data.min() if onset is None else data.min() - onset
            maxdata = data.max() if offset is None else data.max() + offset
            return date_range(
                mindata, maxdata, freq=freq)[::step].to_pydatetime()
        return func

    def _mid_dt_ticks(self, freq):
        def func(N=None, *args, **kwargs):
            step = N or 1
            data = self.dtdata
            if data is None:
                return
            data = date_range(
                data.min(), data.max(), freq=freq).to_pydatetime()
            data[:-1] += (data[1:] - data[:-1])/2
            return data[:-1:step]
        return func


class XTicks(DtTicksBase):
    """
    Modify the x-axis ticks

    Possible types
    --------------
    %(DtTicksBase.possible_types)s

    Examples
    --------
    Plot 11 ticks over the whole data range::

        >>> plotter.update(xticks='rounded')

    Plot 7 ticks over the whole data range where the maximal and minimal
    tick matches the data maximum and minimum::

        >>> plotter.update(xticks=['minmax', 7])

    Plot ticks every year and minor ticks every month::

        >>> plotter.update(xticks={'major': 'year', 'minor': 'month'})

    See Also
    --------
    xticklabels, ticksize, tickweight, xtickprops, yticks"""

    children = TicksBase.children + ['yticks']

    dependencies = DtTicksBase.dependencies + ['plot']

    name = 'Location of the x-Axis ticks'

    @property
    def axis(self):
        return self.ax.xaxis

    @property
    def data(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        data = getattr(self.plot, 'plotted_data', super(XTicks, self).data)
        if not len(data):
            data = super(XTicks, self).data
        if isinstance(data, InteractiveList):
            df = InteractiveList(map(select_array, data)).to_dataframe()
        else:
            df = data.to_series()
        if self.transpose.value:
            return df
        else:
            if isinstance(df.index, MultiIndex) and len(df.index.names) == 1:
                return df.index.get_level_values(0)
            else:
                return df.index

    def initialize_plot(self, *args, **kwargs):
        super(XTicks, self).initialize_plot(*args, **kwargs)
        self.transpose.swap_funcs['ticks'] = self._swap_ticks

    def _swap_ticks(self):
        xticks = self
        yticks = self.yticks
        old_xlocators = xticks.default_locators
        xticks.default_locators = yticks.default_locators
        yticks.default_locators = old_xlocators
        old_xval = self.value
        with self.plotter.no_validation:
            self.plotter[self.key] = self.yticks.value
            self.plotter[self.yticks.key] = old_xval


class YTicks(DtTicksBase):
    """
    Modify the y-axis ticks

    Possible types
    --------------
    %(DtTicksBase.possible_types)s

    See Also
    --------
    yticklabels, ticksize, tickweight, ytickprops
    xticks: for possible examples"""

    dependencies = DtTicksBase.dependencies + ['plot']

    name = 'Location of the y-Axis ticks'

    @property
    def axis(self):
        return self.ax.yaxis

    @property
    def data(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        data = getattr(self.plot, 'plotted_data', super(XTicks, self).data)
        if not len(data):
            data = super(XTicks, self).data
        if isinstance(data, InteractiveList):
            df = InteractiveList(map(select_array, data)).to_dataframe()
        else:
            df = data.to_series()
        if self.transpose.value:
            if isinstance(df.index, MultiIndex) and len(df.index.names) == 1:
                return df.index.get_level_values(0)
            else:
                return df.index
        else:
            return df


@docstrings.get_sections(base='TickLabelsBase')
class TickLabelsBase(TicksManagerBase):
    """
    Abstract base class for ticklabels

    Possible types
    --------------
    str
        A formatstring like ``'%%Y'`` for plotting the year (in the case that
        time is shown on the axis) or '%%i' for integers
    array
        An array of strings to use for the ticklabels"""

    dependencies = ['transpose']

    group = 'ticks'

    @abstractproperty
    def axis(self):
        """The axis on the axes to modify the ticks of"""
        pass

    def __init__(self, *args, **kwargs):
        super(TickLabelsBase, self).__init__(*args, **kwargs)
        self.default_formatters = {}

    def initialize_plot(self, value):
        self.set_default_formatters()
        self.update(value)

    def update_axis(self, value):
        if value is None:
            self.set_formatter(self.default_formatters['major'])
        elif isinstance(value, six.string_types):
            self.set_stringformatter(value)
        else:
            ticks = self.axis.get_ticklocs(minor=self.which == 'minor')
            if len(ticks) != len(value):
                warn("[%s] - Length of ticks (%i) and ticklabels (%i)"
                     "do not match!" % (self.key, len(ticks), len(value)))
            self.set_ticklabels(value)

    def set_stringformatter(self, s):
        default_formatter = self.default_formatters['major']
        if isinstance(default_formatter, AutoDateFormatter):
            self.set_formatter(DateFormatter(s))
        else:
            self.set_formatter(FormatStrFormatter(s))

    def set_ticklabels(self, labels):
        """Sets the given tick labels"""
        self.set_formatter(FixedFormatter(labels))

    @abstractmethod
    def set_formatter(self, formatter):
        """Sets a given formatter"""
        pass

    @abstractmethod
    def set_default_formatters(self):
        """Sets the default formatters that is used for updating to None"""
        pass


class TickLabels(TickLabelsBase, TicksManager):

    def update(self, value):
        if (getattr(self, self.key.replace('label', '')).value.get(
                 'minor') is not None and
                'minor' not in self.value):
            items = chain(six.iteritems(value), [('minor', None)])
        else:
            items = six.iteritems(value)
        super(TickLabels, self).update(dict(items))

    def set_default_formatters(self, which=None):
        """Sets the default formatters that is used for updating to None

        Parameters
        ----------
        which: {None, 'minor', 'major'}
            Specify which locator shall be set"""
        if which is None or which == 'minor':
            self.default_formatters['minor'] = self.axis.get_minor_formatter()
        if which is None or which == 'major':
            self.default_formatters['major'] = self.axis.get_major_formatter()

    def set_formatter(self, formatter, which=None):
        which = which or self.which
        getattr(self.axis, 'set_%s_formatter' % which)(formatter)


class XTickLabels(TickLabels):
    """
    Modify the x-axis ticklabels

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(TickLabelsBase.possible_types)s

    See Also
    --------
    xticks, ticksize, tickweight, xtickprops, yticklabels"""

    dependencies = TickLabelsBase.dependencies + ['xticks', 'yticklabels']

    name = 'x-xxis Ticklabels'

    @property
    def axis(self):
        return self.ax.xaxis

    def initialize_plot(self, *args, **kwargs):
        super(XTickLabels, self).initialize_plot(*args, **kwargs)
        self.transpose.swap_funcs['ticklabels'] = self._swap_ticklabels

    def _swap_ticklabels(self):
        xticklabels = self
        yticklabels = self.yticklabels
        old_xformatters = xticklabels.default_formatters
        xticklabels.default_formatters = yticklabels.default_formatters
        yticklabels.default_formatters = old_xformatters
        old_xval = self.value
        with self.plotter.no_validation:
            self.plotter[self.key] = self.yticklabels.value
            self.plotter[self.yticklabels.key] = old_xval


class YTickLabels(TickLabels):
    """
    Modify the y-axis ticklabels

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(TickLabelsBase.possible_types)s

    See Also
    --------
    yticks, ticksize, tickweight, ytickprops, xticklabels"""

    dependencies = TickLabelsBase.dependencies + ['yticks']

    name = 'y-xxis ticklabels'

    @property
    def axis(self):
        return self.ax.yaxis


class BarXTicks(XTicks):

    __doc__ = XTicks.__doc__

    connections = XTicks.connections + ['xlim']

    dependencies = XTicks.dependencies + ['categorical']

    def update(self, value):
        import matplotlib.ticker as mtick
        if self.categorical.is_categorical and not self.transpose.value:
            self.default_locators['major'] = mtick.FixedLocator(
                np.unique(self.array))
            self.default_locators['minor'] = mtick.NullLocator()
        else:
            self.default_locators = self._orig_default_locators.copy()
        return super(BarXTicks, self).update(value)

    def set_default_locators(self):
        super(BarXTicks, self).set_default_locators()
        self._orig_default_locators = self.default_locators.copy()

    @property
    def array(self):
        if self.transpose.value and 'stacked' in slist(self.plot.value):
            df = self.data.to_dataframe()
            return np.concatenate(
                [[min([0, df.values.min()])], df.sum(axis=1).values])
        elif self.transpose.value:
            return np.concatenate(
                [self.plot.get_xys(arr)[1] for arr in self.plot.iter_data])
        else:
            return np.concatenate(
                [self.plot.get_xys(arr)[0] for arr in self.plot.iter_data])


class BarYTicks(YTicks):

    __doc__ = YTicks.__doc__

    connections = YTicks.connections + ['ylim']

    dependencies = YTicks.dependencies + ['categorical']

    def update(self, value):
        import matplotlib.ticker as mtick
        if self.categorical.is_categorical and self.transpose.value:
            self.default_locators['major'] = mtick.FixedLocator(
                np.unique(self.array))
            self.default_locators['minor'] = mtick.NullLocator()
        else:
            self.default_locators = self._orig_default_locators.copy()
        return super(BarYTicks, self).update(value)

    def set_default_locators(self):
        super(BarYTicks, self).set_default_locators()
        self._orig_default_locators = self.default_locators.copy()

    @property
    def array(self):
        if not self.transpose.value and 'stacked' in slist(self.plot.value):
            df = self.data.to_dataframe()
            return np.concatenate(
                [[min([0, df.values.min()])], df.sum(axis=1).values])
        elif self.transpose.value:
            return np.concatenate(
                [self.plot.get_xys(arr)[0] for arr in self.plot.iter_data])
        else:
            return np.concatenate(
                [self.plot.get_xys(arr)[1] for arr in self.plot.iter_data])


class BarXTickLabels(XTickLabels):

    __doc__ = XTickLabels.__doc__

    dependencies = XTickLabels.dependencies + ['plot', 'categorical']

    def set_stringformatter(self, s):
        if not self.transpose.value and self.plot.value is not None:
            index = self.data.to_dataframe().index
            if index.is_all_dates:
                if self.categorical.is_categorical:
                    xticks = self.ax.get_xticks(minor=self.which == 'minor')
                    arr = list(map(lambda t: t.toordinal(),
                                   to_datetime(index[xticks.astype(int)])))
                    self.ax.set_xticklabels(list(map(DateFormatter(s), arr)))
                else:
                    self.set_formatter(DateFormatter(s))
                return
        super(BarXTickLabels, self).set_stringformatter(s)


class BarYTickLabels(YTickLabels):

    __doc__ = YTickLabels.__doc__

    dependencies = YTickLabels.dependencies + ['plot', 'categorical']

    def set_stringformatter(self, s):
        if self.transpose.value and self.plot.value is not None:
            index = self.data.to_dataframe().index
            if index.is_all_dates:
                if self.categorical.is_categorical:
                    yticks = self.ax.get_yticks(self.which == 'minor')
                    arr = list(map(lambda t: t.toordinal(),
                                   to_datetime(index[yticks.astype(int)])))
                    self.ax.set_yticklabels(list(map(DateFormatter(s), arr)))
                else:
                    self.set_formatter(DateFormatter(s))
                return
        super(BarYTickLabels, self).set_stringformatter(s)


class TicksOptions(TicksManagerBase):
    """Base class for ticklabels options that apply for x- and y-axis"""

    def update(self, value):
        for which, val in six.iteritems(value):
            for axis, axisname in zip([self.ax.xaxis, self.ax.yaxis], 'xy'):
                self.which = which
                self.axis = axis
                self.axisname = axisname
                self.update_axis(val)


class TickSizeBase(TicksOptions):
    """Abstract base class for modifying tick sizes"""

    def update_axis(self, value):
        for t in self.axis.get_ticklabels(which=self.which):
            t.set_size(value)


class TickSize(TickSizeBase, TicksOptions, DictFormatoption):
    """
    Change the ticksize of the ticklabels

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(fontsizes)s

    See Also
    --------
    tickweight, xtickprops, ytickprops"""

    dependencies = TicksOptions.dependencies + ['xtickprops', 'ytickprops']

    name = 'Font size of the ticklabels'


class TickWeightBase(TicksOptions):
    """Abstract base class for modifying font weight of ticks"""

    def update_axis(self, value):
        for t in self.axis.get_ticklabels(which=self.which):
            t.set_weight(value)


class TickWeight(TickWeightBase, TicksOptions, DictFormatoption):
    """
    Change the fontweight of the ticks

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(fontweights)s

    See Also
    --------
    ticksize, xtickprops, ytickprops"""

    dependencies = TicksOptions.dependencies + ['xtickprops', 'ytickprops']

    name = 'Font weight of the ticklabels'


@docstrings.get_sections(base='TickPropsBase')
class TickPropsBase(TicksManagerBase):
    """
    Abstract base class for tick parameters

    Possible types
    --------------
    dict
        Items may be anything of the :func:`matplotlib.pyplot.tick_params`
        function"""

    @abstractproperty
    def axisname(self):
        """The name of the axis (either 'x' or 'y')"""
        pass

    def update_axis(self, value):
        value = value.copy()
        if float('.'.join(mpl.__version__.split('.')[:2])) >= 1.5:
            value.pop('visible', None)
        self.ax.tick_params(
            self.axisname, which=self.which, reset=True, **value)


@docstrings.get_sections(base='XTickProps')
class XTickProps(TickPropsBase, TicksManager, DictFormatoption):
    """
    Specify the x-axis tick parameters

    This formatoption can be used to make a detailed change of the ticks
    parameters on the x-axis.

    Possible types
    --------------
    %(TicksManager.possible_types)s
    %(TickPropsBase.possible_types)s

    See Also
    --------
    xticks, yticks, ticksize, tickweight, ytickprops"""

    axisname = 'x'

    name = 'Font properties of the x-ticklabels'

    @property
    def axis(self):
        return self.ax.xaxis


class YTickProps(XTickProps):
    """
    Specify the y-axis tick parameters

    This formatoption can be used to make a detailed change of the ticks
    parameters of the y-axis.

    Possible types
    --------------
    %(XTickProps.possible_types)s

    See Also
    --------
    xticks, yticks, ticksize, tickweight, xtickprops"""

    axisname = 'y'

    name = 'Font properties of the y-ticklabels'

    @property
    def axis(self):
        return self.ax.xaxis


@docstrings.get_sections(base='Xlabel')
class Xlabel(TextBase, Formatoption):
    """
    Set the x-axis label

    Set the label for the x-axis.
    %(replace_note)s

    Possible types
    --------------
    str
        The text for the :func:`~matplotlib.pyplot.xlabel` function.

    See Also
    --------
    xlabelsize, xlabelweight, xlabelprops"""

    children = ['transpose', 'ylabel']

    name = 'x-axis label'

    @property
    def enhanced_attrs(self):
        arr = self.transpose.get_x(self.data)
        replot = self.plotter.replot or not hasattr(self, '_enhanced_attrs')
        attrs = self.get_enhanced_attrs(arr, replot=replot)
        arr_attrs = self.get_enhanced_attrs(self.data, replot=replot)
        for attr, val in arr_attrs.items():
            attrs.setdefault(attr, val)
        self._enhanced_attrs = attrs
        return attrs

    def initialize_plot(self, value):
        self.transpose.swap_funcs['labels'] = self._swap_labels
        self._texts = [self.ax.set_xlabel(self.replace(
            value, self.data, self.enhanced_attrs))]

    def update(self, value):
        self._texts[0].set_text(self.replace(value, self.data,
                                             self.enhanced_attrs))

    def _swap_labels(self):
        plotter = self.plotter
        self.transpose._swap_labels()
        old_xlabel = self.value
        with plotter.no_validation:
            plotter[self.key] = self.ylabel.value
            plotter[self.ylabel.key] = old_xlabel


class BarXlabel(Xlabel):
    """
    Set the x-axis label

    Set the label for the x-axis.
    %(replace_note)s

    Possible types
    --------------
    %(Xlabel.possible_types)s

    See Also
    --------
    xlabelsize, xlabelweight, xlabelprops"""

    #: Xlabel is modified by the pandas plot routine, therefore we update it
    #: after each plot
    update_after_plot = True


@docstrings.get_sections(base='Ylabel')
class Ylabel(TextBase, Formatoption):
    """
    Set the y-axis label

    Set the label for the y-axis.
    %(replace_note)s

    Possible types
    --------------
    str
        The text for the :func:`~matplotlib.pyplot.ylabel` function.

    See Also
    --------
    ylabelsize, ylabelweight, ylabelprops"""

    children = ['transpose']

    name = 'y-axis label'

    @property
    def enhanced_attrs(self):
        arr = self.transpose.get_y(self.data)
        replot = self.plotter.replot or not hasattr(self, '_enhanced_attrs')
        attrs = self.get_enhanced_attrs(arr, replot=replot)
        arr_attrs = self.get_enhanced_attrs(self.data, replot=replot)
        for attr, val in arr_attrs.items():
            attrs.setdefault(attr, val)
        self._enhanced_attrs = attrs
        return attrs

    def initialize_plot(self, value):
        self._texts = [self.ax.set_ylabel(self.replace(
            value, self.data, self.enhanced_attrs))]

    def update(self, value):
        self._texts[0].set_text(self.replace(
            value, self.data, self.enhanced_attrs))


class BarYlabel(Ylabel):
    """
    Set the y-axis label

    Set the label for the y-axis.
    %(replace_note)s

    Possible types
    --------------
    %(Ylabel.possible_types)s

    See Also
    --------
    ylabelsize, ylabelweight, ylabelprops"""

    #: Ylabel is modified by the pandas plot routine, therefore we update it
    #: after each plot
    update_after_plot = True


@docstrings.get_sections(base='LabelOptions')
class LabelOptions(DictFormatoption):
    """
    Base formatoption class for label sizes

    Possible types
    --------------
    dict
        A dictionary with the keys ``'x'`` and (or) ``'y'`` to specify
        which ticks are managed. If the given value is not a dictionary with
        those keys, it is used for the x- and y-axis.
        The values in the dictionary can be one types below.
    """

    children = ['xlabel', 'ylabel']

    def update(self, value):
        for axis, val in value.items():
            self._text = getattr(self, axis + 'label')._texts[0]
            self.axis_str = axis
            self.update_axis(val)

    @abstractmethod
    def update_axis(self, value):
        pass


class LabelSize(LabelOptions):
    """
    Set the size of both, x- and y-label

    Possible types
    --------------
    %(LabelOptions.possible_types)s
    %(fontsizes)s

    See Also
    --------
    xlabel, ylabel, labelweight, labelprops"""

    group = 'labels'

    parents = ['labelprops']

    name = 'font size of x- and y-axis label'

    def update_axis(self, value):
        self._text.set_size(value)


class LabelWeight(LabelOptions):
    """
    Set the font size of both, x- and y-label

    Possible types
    --------------
    %(LabelOptions.possible_types)s
    %(fontweights)s

    See Also
    --------
    xlabel, ylabel, labelsize, labelprops"""

    group = 'labels'

    parents = ['labelprops']

    name = 'font weight of x- and y-axis label'

    def update_axis(self, value):
        self._text.set_weight(value)


class LabelProps(LabelOptions):
    """
    Set the font properties of both, x- and y-label

    Possible types
    --------------
    %(LabelOptions.possible_types)s
    dict
        Items may be any valid text property

    See Also
    --------
    xlabel, ylabel, labelsize, labelweight"""

    group = 'labels'

    children = ['xlabel', 'ylabel', 'labelsize', 'labelweight']

    name = 'font properties of x- and y-axis label'

    def update_axis(self, fontprops):
        fontprops = fontprops.copy()
        if 'size' not in fontprops and 'fontsize' not in fontprops:
            fontprops['size'] = self.labelsize.value[self.axis_str]
        if 'weight' not in fontprops and 'fontweight' not in fontprops:
            fontprops['weight'] = self.labelweight.value[self.axis_str]
        self._text.update(fontprops)


class Transpose(Formatoption):
    """
    Switch x- and y-axes

    By default, one-dimensional arrays have the dimension on the x-axis and two
    dimensional arrays have the first dimension on the y and the second on the
    x-axis. You can set this formatoption to True to change this behaviour

    Possible types
    --------------
    bool
        If True, axes are switched"""

    group = 'axes'

    name = 'Switch x- and y-axes'

    priority = START

    def __init__(self, *args, **kwargs):
        super(Transpose, self).__init__(*args, **kwargs)
        self.swap_funcs = {
            'ticks': self._swap_ticks,
            'ticklabels': self._swap_ticklabels,
            'limits': self._swap_limits,
            'labels': self._swap_labels,
            }

    def initialize_plot(self, value):
        pass

    def update(self, value):
        for func in six.itervalues(self.swap_funcs):
            func()

    def _swap_ticks(self):
        xaxis = self.ax.xaxis
        yaxis = self.ax.yaxis
        # swap major ticks
        old_xlocator = xaxis.get_major_locator()
        xaxis.set_major_locator(yaxis.get_major_locator())
        yaxis.set_major_locator(old_xlocator)
        # swap minor ticks
        old_xlocator = xaxis.get_minor_locator()
        xaxis.set_minor_locator(yaxis.get_minor_locator())
        yaxis.set_minor_locator(old_xlocator)

    def _swap_ticklabels(self):
        xaxis = self.ax.xaxis
        yaxis = self.ax.yaxis
        # swap major ticklabels
        old_xformatter = xaxis.get_major_formatter()
        xaxis.set_major_formatter(yaxis.get_major_formatter())
        yaxis.set_major_formatter(old_xformatter)
        # swap minor ticklabels
        old_xformatter = xaxis.get_minor_formatter()
        xaxis.set_minor_formatter(yaxis.get_minor_formatter())
        yaxis.set_minor_formatter(old_xformatter)

    def _swap_limits(self):
        old_xlim = list(self.ax.get_xlim())
        self.ax.set_xlim(*self.ax.get_ylim())
        self.ax.set_ylim(*old_xlim)

    def _swap_labels(self):
        old_xlabel = self.ax.get_xlabel()
        self.ax.set_xlabel(self.ax.get_ylabel())
        self.ax.set_ylabel(old_xlabel)

    def get_x(self, arr):
        if not hasattr(arr, 'ndim'):  # if the data object is an array list
            arr = arr[0]
        if arr.dims[0] == 'variable' and arr.ndim > 1:
                arr = arr.psy[0]
        is_unstructured = arr.psy.decoder.is_unstructured(arr)
        if not is_unstructured and arr.ndim == 1:
            if self.value:
                return arr
            else:
                #: The x-coordinate name of the variable as stored in the
                #: dataset (might differ from the one in this array because
                #: this could also be time, z, y, etc.)
                ds_coord = arr.psy.get_dim('x', True)
                xname = arr.dims[0]
        else:
            if self.value:
                ds_coord = arr.psy.get_dim('y', True)
                xname = arr.dims[-2 if not is_unstructured else -1]
            else:
                ds_coord = arr.psy.get_dim('x', True)
                xname = arr.dims[-1]
        if xname == ds_coord:
            if self.value:
                return arr.psy.get_coord('y', True)
            return arr.psy.get_coord('x', True)
        else:
            return arr.coords[xname]

    def get_y(self, arr):
        if not hasattr(arr, 'ndim'):  # if the data object is an array list
            arr = arr[0]
        elif arr.dims[0] == 'variable' and arr.ndim > 1:
                arr = arr.psy[0]
        is_unstructured = arr.psy.decoder.is_unstructured(arr)
        if not is_unstructured and arr.ndim == 1:
            if not self.value:
                return arr
            else:
                #: The x-coordinate name of the variable as stored in the
                #: dataset (might differ from the one in this array because
                #: this could also be time, z, y, etc.)
                ds_coord = arr.psy.get_dim('x', True)
                yname = arr.dims[0]
        else:
            if not self.value:
                ds_coord = arr.psy.get_dim('y', True)
                yname = arr.dims[-2 if not is_unstructured else -1]
            else:
                ds_coord = arr.psy.get_dim('x', True)
                yname = arr.dims[-1]
        if yname == ds_coord:
            if self.value:
                return arr.psy.get_coord('x', True)
            return arr.psy.get_coord('y', True)
        else:
            return arr.coords[yname]


@docstrings.get_sections(base='LineColors')
class LineColors(Formatoption):
    """
    Set the color coding

    This formatoptions sets the color of the lines, bars, etc.

    Possible types
    --------------
    None
        to use the axes color_cycle
    iterable
        (e.g. list) to specify the colors manually
    str
        %(cmap_note)s
    matplotlib.colors.ColorMap
        to automatically choose the colors according to the number of lines,
        etc. from the given colormap"""

    group = 'colors'

    priority = BEFOREPLOTTING

    name = 'Color cycle'

    @property
    def value2pickle(self):
        return self.colors

    @property
    def value2share(self):
        return self.extended_colors

    def __init__(self, *args, **kwargs):
        super(LineColors, self).__init__(*args, **kwargs)
        self.colors = []

    @property
    def extended_colors(self):
        for c in self.colors:
            yield c
        while True:
            c = next(self.color_cycle)
            self.colors.append(c)
            yield c

    def update(self, value):
        changed = self.plotter.has_changed(self.key)
        if value is None:
            prop_cycler = mpl.rcParams['axes.prop_cycle']
            self.color_cycle = cycle((props['color'] for props in prop_cycler))
            prop_cycler._keys  # this should make a copy
        else:
            try:
                self.color_cycle = cycle(get_cmap(value)(
                    np.linspace(0., 1., len(list(self.iter_data)),
                                endpoint=True)))
            except (ValueError, TypeError, KeyError):
                try:
                    # do not use safe_list, because it might be a generator
                    validate_color(value)
                except (ValueError, TypeError, AttributeError):
                    pass
                else:
                    value = [value]
                self.color_cycle = cycle(iter(value))
        if changed:
            self.colors.clear()


class Marker(Formatoption):
    """
    Choose the marker for points

    Possible types
    --------------
    None
        Use the default from matplotlibs rcParams
    str
        A valid symbol for the matplotlib markers (see
        :mod:`matplotlib.markers`)
    """

    priority = BEFOREPLOTTING

    def update(self, value):
        if value is None:
            self.markers = repeat(mpl.rcParams['lines.marker'])
        else:
            self.markers = cycle(value)


class MarkerSize(Formatoption):
    """
    Choose the size of the markers for points

    Possible types
    --------------
    None
        Use the default from matplotlibs rcParams
    float
        The size of the marker
    """

    connections = ['plot']

    priority = BEFOREPLOTTING

    def update(self, value):
        if value is None:
            self.plot._kwargs.pop('markersize', None)
        else:
            self.plot._kwargs['markersize'] = value


class LineWidth(Formatoption):
    """
    Choose the width of the lines

    Possible types
    --------------
    None
        Use the default from matplotlibs rcParams
    float
        The width of the lines
    """

    connections = ['plot']

    priority = BEFOREPLOTTING

    def update(self, value):
        if value is None:
            self.plot._kwargs.pop('linewidth', None)
        else:
            self.plot._kwargs['linewidth'] = value


class LinePlot(Formatoption):
    """
    Choose the line style of the plot

    Possible types
    --------------
    None
        Don't make any plotting
    ``'area'``
        To make an area plot (filled between y=0 and y), see
        :func:`matplotlib.pyplot.fill_between`
    ``'areax'``
        To make a transposed area plot (filled between x=0 and x), see
        :func:`matplotlib.pyplot.fill_betweenx`
    ``'stacked'``
        Make a stacked plot
    str or list of str
        The line style string to use (['solid' | 'dashed', 'dashdot', 'dotted'
        | (offset, on-off-dash-seq) | '-' | '--' | '-.' | ':' | 'None' | ' ' |
        '']).
    """

    plot_fmt = True

    group = 'plotting'

    priority = BEFOREPLOTTING + 0.1

    children = ['color', 'transpose', 'marker']

    name = 'Line plot type'

    @property
    def plotted_data(self):
        """The data that is shown to the user"""
        return InteractiveList(
            [arr for arr, val in zip(self.iter_data,
                                     cycle(slist(self.value)))
             if val is not None])

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._kwargs = {}

    def update(self, value):
        # the real plot making is done by make_plot
        pass

    def make_plot(self):
        if hasattr(self, '_plot'):
            self.remove()
        value = self.value
        if value is not None:
            if 'stacked' in value:
                self._stacked_plot()
            else:
                try:
                    markers = self.marker.markers
                except AttributeError:
                    markers = repeat(None)
                self._plot = list(filter(None, chain.from_iterable(starmap(
                    self.plot_arr, zip(
                        self.iter_data, self.color.extended_colors,
                        cycle(slist(self.value)), markers)))))

    def _stacked_plot(self):
        transpose = self.transpose.value
        data = self.data
        if isinstance(data, InteractiveList):
            data = InteractiveList([arr[0] if arr.ndim == 2 else arr
                                    for arr in data])
            df = data.to_dataframe()
        else:
            df = data.to_series().to_frame()
        index = self._get_index(df)
        if not isinstance(index, DatetimeIndex):
            try:
                x = np.asarray(index.values).astype(float)
            except ValueError:
                x = np.arange(index.values.size)
        else:
            x = index.to_pydatetime()
        base = np.zeros_like(df.iloc[:, 0])
        self._plot = []
        for (col, s), c, val in zip(df.items(), self.color.extended_colors,
                                    cycle(slist(self.value))):
            if val is None:
                continue
            pm = self.ax.fill_betweenx if transpose else \
                self.ax.fill_between
            y = np.where(s.isnull(), 0, s.values)
            self._plot.append(pm(x, base, base + y, facecolor=c))
            base += y

    def _get_index(self, df):
        if isinstance(df.index, MultiIndex) and len(df.index.names) == 1:
            index = df.index.get_level_values(0)
        else:
            index = df.index
        return index

    def plot_arr(self, arr, c, ls, m):
        if ls is None:
            return [None]
        # since date time objects are covered better by pandas,
        # we convert to a series
        if arr.ndim == 2:  # contains also error information
            arr = arr[0]
        df = arr.to_series()
        try:
            y = np.asarray(df.values).astype(float)
        except ValueError:
            y = np.arange(df.values.size)
        index = self._get_index(df)
        if not isinstance(index, DatetimeIndex):
            try:
                x = np.asarray(index.values).astype(float)
            except ValueError:
                x = np.arange(index.values.size)
        else:
            x = index.to_pydatetime()

        if self.transpose.value:
            x, y = y, x
        if ls in ['area', 'areay']:
            ymin = np.vstack([y, np.zeros_like(y)]).min(axis=0)
            ymax = np.vstack([y, np.zeros_like(y)]).max(axis=0)
            return [self.ax.fill_between(x, ymin, ymax, color=c)]
        elif ls == 'areax':
            xmin = np.vstack([x, np.zeros_like(x)]).min(axis=0)
            xmax = np.vstack([x, np.zeros_like(x)]).max(axis=0)
            return [self.ax.fill_betweenx(y, xmin, xmax, color=c)]
        else:
            return self.ax.plot(x, y,
                                color=c, linestyle=ls, marker=m,
                                **self._kwargs)

    def remove(self):
        for artist in self._plot:
            artist.remove()
        del self._plot


class ErrorPlot(Formatoption):
    """
    Visualize the error range

    This formatoption visualizes the error range. For this, you must provide a
    two-dimensional data array as input. The first dimension might be either of
    length

    - 2 to provide the deviation from minimum and maximum error range from
      the data
    - 3 to provide the minimum and maximum error range explicitly

    Possible types
    --------------
    None
        No errors are visualized
    'fill'
        The area between min- and max-error is filled with the same color as
        the line and the alpha is determined by the :attr:`fillalpha` attribute

    Examples
    --------
    Assume you have the standard deviation stored in the ``'std'``-variable and
    the data in the ``'data'`` variable. Then you can visualize the standard
    deviation simply via::

        >>> psy.plot.lineplot(input_ds, name=[['data', 'std']])

    On the other hand, assume you want to visualize the area between the 25th
    and 75th percentile (stored in the variables ``'p25'`` and ``'p75'``)::

        >>> psy.plot.lineplot(input_ds, name=[['data', 'p25', 'p75']])

    See Also
    --------
    erroralpha
    """

    plot_fmt = True

    group = 'plotting'

    priority = BEFOREPLOTTING

    children = ['color', 'transpose', 'plot']

    name = 'Error plot type'

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._kwargs = {}

    def update(self, value):
        pass  # the work is done in make_plot

    def make_plot(self):
        if hasattr(self, '_plot'):
            self.remove()
        if self.value is not None:
            self._plot = []
            colors = self.color.extended_colors
            for da, line in zip(self.iter_data, self.plot._plot):
                if da.ndim == 2 and da.shape[0] > 1:
                    data = da[0].to_series()
                    error = da[1:, :]
                    if error.shape[0] == 1:
                        min_range = data.values - error[0]
                        max_range = data.values + error[0]
                    else:
                        min_range = error[0]
                        max_range = error[1]
                    if self.value == 'fill':
                        vals = self._get_x_values(data)
                        self.plot_fill(vals, min_range, max_range,
                                       next(colors), zorder=line.zorder)
                else:
                    next(colors)

    def _get_x_values(self, df):
        if isinstance(df.index, MultiIndex) and len(df.index.names) == 1:
            index = df.index.get_level_values(0)
        else:
            index = df.index
        if not isinstance(index, DatetimeIndex):
            try:
                x = np.asarray(index.values).astype(float)
            except ValueError:
                x = np.arange(index.values.size)
        else:
            x = index.to_pydatetime()
        return x

    def plot_fill(self, index, min_range, max_range, c, **kwargs):
        if self.transpose.value:
            plot_method = self.ax.fill_betweenx
        else:
            plot_method = self.ax.fill_between
        self._plot.append(
            plot_method(index, min_range, max_range, facecolor=c,
                        **dict(chain(*map(
                            six.iteritems, [self._kwargs, kwargs])))))

    def remove(self):
        for artist in self._plot:
            artist.remove()
        del self._plot


class ErrorAlpha(Formatoption):
    """
    Set the alpha value for the error range

    This formatoption can be used to set the alpha value (opacity) for the
    :attr:`error` formatoption

    Possible types
    --------------
    float
        A float between 0 and 1

    See Also
    --------
    error"""

    priority = BEFOREPLOTTING

    name = 'Alpha value of the error range'

    group = 'colors'

    connections = ['error']

    def update(self, value):
        self.error._kwargs['alpha'] = value


class BarWidths(Formatoption):
    """
    Specify the widths of the bars

    Possible types
    --------------
    'equal'
        Each bar will have the same width (the default)
    'data'
        Each bar will have the width as specified by the boundaries
    float
        The width for each bar

    See Also
    --------
    categorical
    """

    priority = BEFOREPLOTTING

    name = 'Width of the bars'

    def update(self, value):
        # Does nothing, the work is done in the :class:`BarPlot` formatoption
        pass


class CategoricalBars(Formatoption):
    """
    The location of each bar

    Possible types
    --------------
    None
        If None, use a categorical plotting if the widths are ``'equal'``,
        otherwise, not
    bool
        If True, use a categorical plotting

    See Also
    --------
    widths
    """

    priority = BEFOREPLOTTING

    name = 'Categorical or non-categorical plotting'

    dependencies = ['widths']

    def update(self, value):
        widths = self.widths.value
        self.is_categorical = (value is None and widths == 'equal') or value


class BarAlpha(Formatoption):
    """
    Specify the transparency (alpha)

    Possible types
    --------------
    float
        A value between 0 (opaque) and 1 invisible"""

    priority = BEFOREPLOTTING

    name = 'Transparency of the bars'

    def update(self, value):
        pass


class BarPlot(Formatoption):
    """
    Choose how to make the bar plot

    Possible types
    --------------
    None
        Don't make any plotting
    'bar'
        Create a usual bar plot with the bars side-by-side
    'stacked'
        Create stacked plot
    """

    plot_fmt = True

    group = 'plotting'

    priority = BEFOREPLOTTING

    children = ['color', 'transpose', 'alpha']

    dependencies = ['widths', 'categorical']

    name = 'Bar plot type'

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._kwargs = {}

    def update(self, value):
        # the real plot making is done by make_plot
        pass

    def remove(self):
        for artist in self._plot:
            artist.remove()
        del self._plot

    @property
    def plotted_data(self):
        """The data that is shown to the user"""
        return InteractiveList(
            [arr for arr, val in zip(self.iter_data,
                                     cycle(slist(self.value)))
             if val is not None])

    def make_plot(self):
        if hasattr(self, '_plot'):
            self.remove()
        if self.value is not None:
            ax = self.ax
            # for a transposed plot, we use the barh plot method of the axes
            pm = ax.barh if self.transpose.value else ax.bar
            alpha = self.alpha.value
            if 'stacked' not in slist(self.value):
                self._plot = [
                    pm(*self.get_xys(arr), facecolor=c, alpha=alpha,
                       align='edge')
                    for arr, c in zip(self.iter_data,
                                      self.color.extended_colors)]
                if self._set_date:
                    if self.transpose.value:
                        ax.yaxis_date()
                    else:
                        ax.xaxis_date()
            else:  # make a stacked plot
                if isinstance(self.data, InteractiveList):
                    df = self.data.to_dataframe()
                else:
                    df = self.data.to_series().to_frame()
                try:
                    df.index = df.index.get_level_values(0)
                except AttributeError:
                    pass
                x, y, s = self.get_xys(df.iloc[:, 0].to_xarray())
                self._plot = containers = []
                base = np.zeros_like(y)
                for i, (col, c, plot) in enumerate(
                        zip(df.columns, self.color.extended_colors,
                            cycle(slist(self.value)))):
                    if not plot:
                        continue
                    y = df.iloc[:, i].values
                    y = np.where(np.isnan(y), 0, y)
                    if not i:
                        containers.append(
                            pm(x, y, s, facecolor=c, alpha=alpha))
                    elif self.transpose.value:
                        containers.append(
                            pm(x, y, s, facecolor=c, alpha=alpha, left=base))
                    else:
                        containers.append(
                            pm(x, y, s, facecolor=c, alpha=alpha, bottom=base))
                    base += y

    def get_xys(self, arr):
        width = self.widths.value
        y = arr.values
        self._set_date = False
        if self.categorical.is_categorical:
            x = np.arange(len(y))
            if width == 'data':
                self.logger.warn(
                    "Cannot use 'data'-based bar width for categorical plots!")
                width = 0.5
            elif width == 'equal':
                width = 0.5  # pandas default value
        elif width == 'data':
            x = _infer_interval_breaks(arr.coords[arr.dims[0]].values)
            is_datelike = arr.indexes[arr.dims[0]].is_all_dates
            s = x[1:] - x[:-1]
            if is_datelike:
                # convert to datetime
                x = to_datetime(x)
                # calculate widths in days
                s = to_timedelta(s).total_seconds() / 86400.
                self._set_date = True
            x = x[:-1]
            width = s
        else:
            if width == 'equal':
                # Use half of the smalles step
                x = _infer_interval_breaks(arr.coords[arr.dims[0]].values)
                width = np.abs(np.diff(x)).min() / 2
            x = arr.coords[arr.dims[0]].values
        return x, y, width


class ViolinXTicks(XTicks):

    __doc__ = XTicks.__doc__

    @property
    def array(self):
        if not self.transpose.value:
            return np.array(list(range(len(self.data))))
        return super(ViolinXTicks, self).array


class ViolinYTicks(YTicks):

    __doc__ = YTicks.__doc__

    @property
    def array(self):
        if self.transpose.value:
            return np.array(list(range(len(self.data))))
        return super(ViolinYTicks, self).array


class ViolinXTickLabels(XTickLabels, TextBase):
    __doc__ = XTickLabels.__doc__

    data_dependent = True

    def update_axis(self, value):
        if self.transpose.value or value is None:
            return super(ViolinXTickLabels, self).update_axis(value)
        if isinstance(value, six.string_types):
            self.set_ticklabels([
                self.replace(value, arr, self.get_enhanced_attrs(
                    arr, replot=True)) for arr in self.data])
        else:
            self.set_ticklabels([
                self.replace(val, arr, self.get_enhanced_attrs(
                    arr, replot=True)) for val, arr in zip(value, self.data)])


class ViolinYTickLabels(YTickLabels, TextBase):
    __doc__ = XTickLabels.__doc__

    data_dependent = True

    def update_axis(self, value):
        if self.transpose.value or value is None:
            return super(ViolinYTickLabels, self).update_axis(value)
        if isinstance(value, six.string_types):
            self.set_ticklabels([
                self.replace(value, arr, self.get_enhanced_attrs(
                    arr, replot=True)) for arr in self.data])
        else:
            self.set_ticklabels([
                self.replace(val, arr, self.get_enhanced_attrs(
                    arr, replot=True)) for val, arr in zip(value, self.data)])


class ViolinPlot(Formatoption):
    """
    Choose how to make the violin plot

    Possible types
    --------------
    None or False
        Don't make any plotting
    bool
        If True, visualize the violins
    """

    plot_fmt = True

    group = 'plotting'

    priority = BEFOREPLOTTING

    children = ['color', 'transpose']

    name = 'Violin plot type'

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._kwargs = {}

    def update(self, value):
        # the real plot making is done by make_plot
        pass

    def remove(self):
        for artist in self._plot:
            artist.remove()
        del self._plot

    def make_plot(self):
        if hasattr(self, '_plot'):
            self.remove()
        if self.value:
            from seaborn import violinplot
            if isinstance(self.data, InteractiveList):
                df = self.data.to_dataframe()
            else:
                df = self.data.to_series().to_frame()
            old_artists = self.ax.containers[:] + self.ax.lines[:] \
                + self.ax.collections[:]
            palette = list(islice(self.color.extended_colors, df.shape[1]))
            violinplot(data=df, palette=palette, ax=self.ax,
                       orient='h' if self.transpose.value else 'v',
                       **self._kwargs)
            artists = self.ax.containers + self.ax.lines + self.ax.collections
            self._plot = [
                artist for artist in artists
                if artist not in old_artists]


@docstrings.get_sections(base='LimitBase')
@dedent
class LimitBase(DataTicksCalculator):
    """
    Base class for x- and y-limits

    Possible types
    --------------
    None
        To not change the current limits
    str or list [str, str] or [[str, float], [str, float]]
        Automatically determine the ticks corresponding to the data. The given
        string determines how the limits are calculated. The float determines
        the percentile to use
        A string can be one of the following:

        rounded
            Sets the minimum and maximum of the limits to the rounded data
            minimum or maximum. Limits are rounded to the next 0.5 value with
            to the difference between data max- and minimum. The minimum
            will always be lower or equal than the data minimum, the maximum
            will always be higher or equal than the data maximum.
        roundedsym
            Same as `rounded` above but the limits are chosen such that they
            are symmetric around zero
        minmax
            Uses the minimum and maximum
        sym
            Same as minmax but symmetric around zero
    tuple (xmin, xmax)
        `xmin` is the smaller value, `xmax` the larger. Any of those values can
        be None or one of the strings (or lists) above to use the corresponding
        value here
    """

    group = 'axes'

    children = ['transpose']

    connections = ['plot']

    @property
    def value2share(self):
        return self.range

    @abstractmethod
    def set_limit(self, min_val, max_val):
        """The method to set the minimum and maximum limit

        Parameters
        ----------
        min_val: float
            The value for the lower limit
        max_val: float
            The value for the upper limit"""
        pass

    def __init__(self, *args, **kwargs):
        super(LimitBase, self).__init__(*args, **kwargs)
        self._calc_funcs = {
            'rounded': self._round_min_max,
            'roundedsym': self._roundedsym_min_max,
            'minmax': self._min_max,
            'sym': self._sym_min_max}

    def _round_min_max(self, vmin, vmax):
        try:
            exp = np.floor(np.log10(abs(vmax - vmin)))
            larger = round_to_05([vmin, vmax], exp, mode='l')
            smaller = round_to_05([vmin, vmax], exp, mode='s')
        except TypeError:
            self.logger.debug("Failed to calculate rounded limits!",
                              exc_info=True)
            return vmin, vmax
        return min([larger[0], smaller[0]]), max([larger[1], smaller[1]])

    def _min_max(self, vmin, vmax):
        return vmin, vmax

    def _roundedsym_min_max(self, vmin, vmax):
        vmax = max(map(abs, self._round_min_max(vmin, vmax)))
        return -vmax, vmax

    def _sym_min_max(self, vmin, vmax):
        vmax = max(abs(vmin), abs(vmax))
        return -vmax, vmax

    def update(self, value):
        value = list(value)
        value_lists = list(map(slist, value))
        kwargs = {}
        for kw, l in zip(['percmin', 'percmax'], value_lists):
            if len(l) == 2:
                kwargs[kw] = l[1]
        vmin, vmax = self._calc_vmin_vmax(**kwargs)
        if vmin == vmax:
            vmax = vmax + 1
            vmin = vmin - 1
        for key, func in self._calc_funcs.items():
            if key in value_lists[0] or key in value_lists[1]:
                minmax = func(vmin, vmax)
                for i, val in enumerate(value_lists):
                    if key in val:
                        value[i] = minmax[i]
        self.range = value
        self.logger.debug('Setting %s with %s', self.key, value)
        self.set_limit(*value)


class Xlim(LimitBase):
    """
    Set the x-axis limits

    Possible types
    --------------
    %(LimitBase.possible_types)s

    See Also
    --------
    ylim
    """

    children = LimitBase.children + ['ylim']

    dependencies = ['xticks']

    connections = LimitBase.connections + ['sym_lims']

    axisname = 'x'

    name = 'x-axis limits'

    @property
    def array(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        data = list(getattr(self.plot, 'plotted_data', self.iter_data)) or \
            self.iter_data
        df = InteractiveList(map(select_array, data)).to_dataframe()
        if (self.transpose.value and 'stacked' in slist(self.plot.value)):
            summed = df.sum(axis=1).values
            arr = np.concatenate(
                [[min(summed.min(), 0)], df.sum(axis=1).values])
        elif self.transpose.value:
            arr = df.values[df.notnull().values]
        else:
            arr = _get_index_vals(df.index)
        try:
            arr.astype(float)
        except (ValueError,  TypeError):
            arr = np.arange(len(arr))
        return arr

    def set_limit(self, *args):
        if self.ax.xaxis_inverted():
            args = reversed(args)
        try:
            self.ax.set_xlim(*args)
        except (AttributeError, TypeError):  # np.datetime64
            self.ax.set_xlim(*to_datetime(args))

    def initialize_plot(self, value):
        super(Xlim, self).initialize_plot(value)
        self.transpose.swap_funcs['limits'] = self._swap_limits

    def _swap_limits(self):
        self.transpose._swap_limits()
        old_xlim = self.value
        with self.plotter.no_validation:
            self.plotter[self.key] = self.ylim.value
            self.plotter[self.ylim.key] = old_xlim


class Ylim(LimitBase):
    """
    Set the y-axis limits

    Possible types
    --------------
    %(LimitBase.possible_types)s

    See Also
    --------
    xlim
    """
    children = LimitBase.children + ['xlim']

    dependencies = ['yticks']

    connections = LimitBase.connections + ['sym_lims']

    axisname = 'y'

    name = 'y-axis limits'

    @property
    def array(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        data = list(getattr(self.plot, 'plotted_data', self.iter_data)) or \
            self.iter_data
        df = InteractiveList(map(select_array, data)).to_dataframe()
        if (not self.transpose.value and 'stacked' in slist(self.plot.value)):
            summed = df.sum(axis=1).values
            arr = np.concatenate(
                [[min(summed.min(), 0)], df.sum(axis=1).values])
        elif self.transpose.value:
            arr = _get_index_vals(df.index)
        else:
            arr = df.values[df.notnull().values]
        try:
            arr.astype(float)
        except ValueError:
            return np.arange(len(arr))
        return arr

    def set_limit(self, *args):
        if self.ax.yaxis_inverted():
            args = reversed(args)
        try:
            self.ax.set_ylim(*args)
        except (AttributeError, TypeError):  # np.datetime64
            self.ax.set_ylim(*to_datetime(args))


class SymmetricLimits(Formatoption):
    """
    Make x- and y-axis symmetric

    Possible types
    --------------
    None
        No symmetric type
    'min'
        Use the minimum of x- and y-limits
    'max'
        Use the maximum of x- and y-limits
    [str, str]
        A combination, ``None``, ``'min'`` and ``'max'`` specific for minimum
        and maximum limit
    """

    dependencies = ['xlim', 'ylim']

    name = 'Symmetric x- and y-axis limits'

    def update(self, value):
        if all(v is None for v in value):
            return
        xlim = self.xlim.range[:]
        ylim = self.ylim.range[:]
        for i, v in enumerate(value):
            if v == 'min':
                xlim[i] = ylim[i] = min(xlim[i], ylim[i])
            elif v == 'max':
                xlim[i] = ylim[i] = max(xlim[i], ylim[i])
        self.xlim.set_limit(*xlim)
        self.ylim.set_limit(*ylim)


class ViolinXlim(Xlim):
    # xlim class for ViolinPlotter
    __doc__ = Xlim.__doc__

    @property
    def array(self):
        if not self.transpose.value:
            return np.array(
                [-0.5, len(list(self.iter_data)) - 0.5])
        return super(ViolinXlim, self).array

    def _round_min_max(self, *args, **kwargs):
        if not self.transpose.value:
            return self.array
        return super(ViolinXlim, self)._round_min_max(*args, **kwargs)


class BarXlim(ViolinXlim):
    # xlim class for bar plotter
    __doc__ = Xlim.__doc__

    dependencies = ViolinXlim.dependencies + ['categorical']

    @property
    def array(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        categorical = self.categorical.is_categorical
        if self.transpose.value and 'stacked' in slist(self.plot.value):
            data = list(getattr(self.plot, 'plotted_data',
                                self.iter_data)) or self.iter_data
            df = InteractiveList(map(select_array, data)).to_dataframe()
            summed = df.sum(axis=1).values
            return np.concatenate(
                [[min(summed.min(), 0)], df.sum(axis=1).values])
        elif categorical and not self.transpose.value:
            return np.array(
                [-0.5, len(self.data.to_dataframe().index) - 0.5])
        elif not categorical:
            return _infer_interval_breaks(Xlim.array.fget(self))
        return super(BarXlim, self).array

    def _round_min_max(self, *args, **kwargs):
        if not self.categorical.is_categorical:
            return Xlim._round_min_max(self, *args, **kwargs)
        else:
            return super(BarXlim, self)._round_min_max(*args, **kwargs)


class Xlim2D(Xlim):
    __doc__ = Xlim.__doc__

    @property
    def array(self):
        xcoord = self.transpose.get_x(self.data)
        func = 'get_x' if not self.transpose.value else 'get_y'
        data = next(self.iter_data)
        if (self.decoder.is_unstructured(data) and
                xcoord.name == getattr(self.decoder, func)(data).name):
            bounds = self.decoder.get_cell_node_coord(
                data, axis='x', coords=data.coords)
            if bounds is None:
                bounds = xcoord
            if self.plotter.convert_radian:
                bounds = convert_radian(bounds, xcoord, bounds)
            return bounds.values.ravel()
        return self.decoder.get_plotbounds(xcoord)


class Ylim2D(Ylim):
    __doc__ = Ylim.__doc__

    @property
    def array(self):
        ycoord = self.transpose.get_y(self.data)
        func = 'get_x' if self.transpose.value else 'get_y'
        data = next(self.iter_data)
        if (self.decoder.is_unstructured(data) and
                ycoord.name == getattr(self.decoder, func)(data).name):
            bounds = self.decoder.get_cell_node_coord(
                data, axis='y', coords=data.coords)
            if bounds is None:
                bounds = ycoord
            if self.plotter.convert_radian:
                bounds = convert_radian(bounds, ycoord, bounds)
            return bounds.values.ravel()
        return self.decoder.get_plotbounds(self.transpose.get_y(self.data))


class ViolinYlim(Ylim):
    # Ylim class for ViolinPlotter
    __doc__ = Ylim.__doc__

    @property
    def array(self):
        if self.transpose.value:
            return np.array(
                [-0.5, len(list(self.iter_data)) - 0.5])
        return super(ViolinYlim, self).array

    def _round_min_max(self, *args, **kwargs):
        if self.transpose.value:
            return self.array
        return super(ViolinYlim, self)._round_min_max(*args, **kwargs)


class BarYlim(ViolinYlim):
    # ylim class for bar plotter
    __doc__ = Ylim.__doc__

    dependencies = ViolinYlim.dependencies + ['categorical']

    @property
    def array(self):
        def select_array(arr):
            if arr.ndim > 1:
                return arr.psy[0]
            return arr
        categorical = self.categorical.is_categorical
        if not self.transpose.value and 'stacked' in slist(self.plot.value):
            data = list(getattr(self.plot, 'plotted_data',
                                self.iter_data)) or self.iter_data
            df = InteractiveList(map(select_array, data)).to_dataframe()
            summed = df.sum(axis=1).values
            return np.concatenate(
                [[min(summed.min(), 0)], df.sum(axis=1).values])
        elif categorical and self.transpose.value:
            return np.array(
                [-0.5, len(self.data.to_dataframe().index) - 0.5])
        elif not categorical and self.transpose.value:
            return _infer_interval_breaks(Ylim.array.fget(self))
        elif not categorical:
            return Ylim.array.fget(self)
        return super(BarYlim, self).array

    def _round_min_max(self, *args, **kwargs):
        if not self.categorical.is_categorical:
            return Ylim._round_min_max(self, *args, **kwargs)
        else:
            return super(BarYlim, self)._round_min_max(*args, **kwargs)


class XRotation(Formatoption):
    """
    Rotate the x-axis ticks

    Possible types
    --------------
    float
        The rotation angle in degrees

    See Also
    --------
    yrotation"""

    group = 'ticks'

    children = ['yticklabels']

    name = 'Rotate x-ticklabels'

    def update(self, value):
        for text in self.ax.get_xticklabels(which='both'):
            text.set_rotation(value)


class YRotation(Formatoption):
    """
    Rotate the y-axis ticks

    Possible types
    --------------
    float
        The rotation angle in degrees

    See Also
    --------
    xrotation"""

    group = 'ticks'

    children = ['yticklabels']

    name = 'Rotate y-ticklabels'

    def update(self, value):
        for text in self.ax.get_yticklabels(which='both'):
            text.set_rotation(value)


class CMap(Formatoption):
    """
    Specify the color map

    This formatoption specifies the color coding of the data via a
    :class:`matplotlib.colors.Colormap`

    Possible types
    --------------
    str
        %(cmap_note)s
    matplotlib.colors.Colormap
        The colormap instance to use

    See Also
    --------
    bounds: specifies the boundaries of the colormap"""

    group = 'colors'

    priority = BEFOREPLOTTING

    name = 'Colormap'

    connections = ['bounds', 'cbar']  # necessary for get_fmt_widget

    def get_cmap(self, arr=None, cmap=None, N=None):
        """Get the :class:`matplotlib.colors.Colormap` for plotting

        Parameters
        ----------
        arr: np.ndarray
            The array to plot
        cmap: str or matplotlib.colors.Colormap
            The colormap to use. If None, the :attr:`value` of this
            formatoption is used
        N: int
            The number of colors in the colormap. If None, the norm of the
            :attr:`bounds` formatoption is used and, if necessary, the
            given array `arr`

        Returns
        -------
        matplotlib.colors.Colormap
            The colormap returned by :func:`psy_simple.colors.get_cmap`"""
        N = N or None
        if cmap is None:
            cmap = self.value
        if N is None:
            try:
                N = self.bounds.norm.Ncmap
            except AttributeError:
                if arr is not None and self.bounds.norm is not None:
                    N = len(np.unique(self.bounds.norm(arr.ravel())))
        if N is not None:
            return get_cmap(cmap, N)
        return get_cmap(cmap)

    def update(self, value):
        pass  # the colormap is set when plotting

    def get_fmt_widget(self, parent, project):
        """Open a :class:`psy_simple.widget.CMapFmtWidget`"""
        from psy_simple.widgets.colors import CMapFmtWidget
        return CMapFmtWidget(parent, self, project)


class MissColor(Formatoption):
    """
    Set the color for missing values

    Possible types
    --------------
    None
        Use the default from the colormap
    string, tuple.
        Defines the color of the grid."""

    group = 'colors'

    priority = END

    dependencies = ['plot']

    connections = ['transform']

    name = 'Color of missing values'

    update_after_plot = True

    def update(self, value):
        if self.plotter.replot:
            self.remove()
        if self.plot.value is None:
            return
        elif value is not None and self.plot.value == 'contourf':
            warn('[%s] - The miss_color formatoption is not supported for '
                 'filled contour plots!' % self.logger.name)
        mappable = self.plot.mappable
        if value is not None:
            mappable.get_cmap().set_bad(value)
        else:
            mappable.get_cmap().set_bad(alpha=0)
        mappable.changed()

    def remove(self):
        if hasattr(self, '_miss_color_plot'):
            try:
                self._miss_color_plot.remove()
                del self._miss_color_plot
            except ValueError:
                pass


@docstrings.get_sections(base='Bounds', sections=['Possible types', 'Examples',
                                              'See Also'])
class Bounds(DataTicksCalculator):
    """
    Specify the boundaries of the colorbar

    Possible types
    --------------
    None
        make no normalization
    %(DataTicksCalculator.possible_types)s
    int
        Specifies how many ticks to use with the ``'rounded'`` option. I.e. if
        integer ``i``, then this is the same as ``['rounded', i]``.
    matplotlib.colors.Normalize
        A matplotlib normalization instance

    Examples
    --------
    - Plot 11 bounds over the whole data range::

          >>> plotter.update(bounds='rounded')

      which is equivalent to::

          >>> plotter.update(bounds={'method': 'rounded'})

    - Plot 7 ticks over the whole data range where the maximal and minimal
      tick matches the data maximum and minimum::

          >>> plotter.update(bounds=['minmax', 7])

      which is equivaluent to::

          >>> plotter.update(bounds={'method': 'minmax', 'N': 7})

    - chop the first and last five percentiles::

          >>> plotter.update(bounds=['rounded', None, 5, 95])

      which is equivalent to::

          >>> plotter.update(bounds={'method': 'rounded', 'percmin': 5,
          ...                        'percmax': 95})

    - Plot 3 bounds per power of ten::

          >>> plotter.update(bounds=['log', 3])

    - Plot continuous logarithmic bounds::

          >>> from matplotlib.colors import LogNorm
          >>> plotter.update(bounds=LogNorm())


    See Also
    --------
    cmap: Specifies the colormap"""

    group = 'colors'

    priority = BEFOREPLOTTING

    name = 'Boundaries of the color map'

    connections = ['cmap', 'cbar']  # necessary for get_fmt_widget

    @property
    def value2share(self):
        """The normalization instance"""
        if len(self.bounds) > 1:
            return list(self.bounds)
        return self.norm

    def update(self, value):
        if value is None or isinstance(value, mpl.colors.Normalize):
            self.norm = value
            self.bounds = [0]
        else:
            if isinstance(value[0], six.string_types):
                value = self.calc_funcs[value[0]](*value[1:])
            self.bounds = value
            self.norm = mpl.colors.BoundaryNorm(
                value, len(value) - 1)

    def get_fmt_widget(self, parent, project):
        """Open a :class:`psy_simple.widget.CMapFmtWidget`"""
        from psy_simple.widgets.colors import BoundsFmtWidget
        return BoundsFmtWidget(parent, self, project)


def format_coord_func(ax, ref):
    """Create a function that can replace the
    :func:`matplotlib.axes.Axes.format_coord`

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        The axes instance
    ref: weakref.weakref
        The reference to the :class:`~psyplot.plotter.Formatoption` instance

    Returns
    -------
    function
        The function that can be used to replace `ax.format_coord`
    """
    orig_format_coord = ax.format_coord

    def func(x, y):
        orig_s = orig_format_coord(x, y)
        fmto = ref()
        if fmto is None:
            return orig_s
        try:
            orig_s += fmto.add2format_coord(x, y)
        except Exception:
            fmto.logger.debug(
                'Failed to get plot informations for status bar!', exc_info=1)
        return orig_s

    return func


class InterpolateBounds(Formatoption):
    """
    Interpolate grid cell boundaries for 2D plots

    This formatoption can be used to tell enable and disable the interpolation
    of grid cell boundaries. Usually, netCDF files only contain the centered
    coordinates. In this case, we interpolate the boundaries between the
    grid cell centers.

    Possible types
    --------------
    None
        Interpolate the boundaries, except for circumpolar grids
    bool
        If True (the default), the grid cell boundaries are inter- and
        extrapolated. Otherwise, if False, the coordinate centers are used and
        the default behaviour of matplotlib cuts of the most outer row and
        column of the 2D-data. Note that this results in a slight shift of the
        data
    """

    priority = BEFOREPLOTTING

    def update(self, value):
        pass


@docstrings.get_sections(base='Plot2D')
class Plot2D(Formatoption):
    """
    Choose how to visualize a 2-dimensional scalar data field

    Possible types
    --------------
    None
        Don't make any plotting
    'mesh'
        Use the :func:`matplotlib.pyplot.pcolormesh` function to make the plot
        or the :func:`matplotlib.pyplot.tripcolor` for an unstructered grid
    'tri'
        Use the :func:`matplotlib.pyplot.tripcolor` function to plot data on a
        unstructured grid
    'contourf'
        Make a filled contour plot using the :func:`matplotlib.pyplot.contourf`
        function or the :func:`matplotlib.pyplot.tricontourf` for unstructured
        data. The levels for the contour plot are controlled by the
        :attr:`levels` formatoption
    'tricontourf'
        Make a filled contour plot using the
        :func:`matplotlib.pyplot.tricontourf` function
    """

    plot_fmt = True

    group = 'plotting'

    priority = BEFOREPLOTTING

    name = '2D plot type'

    children = ['cmap', 'bounds']

    dependencies = ['levels', 'interp_bounds']

    @property
    def array(self):
        """The (masked) data array that is plotted"""
        arr = self.data.values
        return np.ma.masked_array(arr, mask=np.isnan(arr))

    @property
    def notnull_array(self):
        """The data array that is plotted"""
        arr = self.data.values
        return arr[~np.isnan(arr)]

    @property
    def xbounds(self):
        """Boundaries of the x-coordinate"""
        data = self.data
        coord = self.decoder.get_x(data, coords=data.coords)
        return self.decoder.get_plotbounds(coord)

    @property
    def ybounds(self):
        """Boundaries of the y-coordinate"""
        data = self.data
        coord = self.decoder.get_y(data, coords=data.coords)
        return self.decoder.get_plotbounds(coord)

    @property
    def xcoord(self):
        """The x coordinate :class:`xarray.Variable`"""
        return self.decoder.get_x(self.data, coords=self.data.coords)

    @property
    def ycoord(self):
        """The y coordinate :class:`xarray.Variable`"""
        return self.decoder.get_y(self.data, coords=self.data.coords)

    @property
    def mappable(self):
        """Returns the mappable that can be used for colorbars"""
        return self._plot

    @property
    def format_coord(self):
        """The function that can replace the axes.format_coord method"""
        return format_coord_func(self.ax, weakref.ref(self))

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._plot_funcs = {
            'mesh': self._pcolormesh,
            'contourf': self._contourf,
            'tricontourf': self._contourf,
            'contour': self._contourf,
            'tricontour': self._contourf,
            'tri': self._polycolor,
            'poly': self._polycolor}
        self._orig_format_coord = None
        self._kwargs = {}

    def update(self, value):
        # the real plot making is done by make_plot
        pass

    def make_plot(self):
        # remove the plot if it shall be replotted or any of the dependencies
        # changed
        if self.plotter.replot or any(
                self.plotter.has_changed(key) for key in chain(
                    self.connections, self.dependencies, [self.key])):
            self.remove()
        if self.value is not None:
            if self.value == 'tri':
                warn("The 'tri' value is depreceated and will be removed "
                     "in the future. Use 'poly' instead!",
                     DeprecationWarning)
            self._plot_funcs[self.value]()
            if self._orig_format_coord is None:
                self._orig_format_coord = self.ax.format_coord
                self.ax.format_coord = self.format_coord

    def _pcolormesh(self):
        if self.decoder.is_unstructured(self.raw_data):
            return self._polycolor()
        arr = self.array
        cmap = self.cmap.get_cmap(arr)
        if hasattr(self, '_plot'):
            self._plot.update(dict(cmap=cmap, norm=self.bounds.norm))
            # for cartopy, we have to consider the wrapped collection if the
            # data has to be transformed
            try:
                coll = self._plot._wrapped_collection_fix
            except AttributeError:
                pass
            else:
                coll.update(dict(cmap=cmap, norm=self.bounds.norm))
        else:
            x, y = self._get_xy_pcolormesh()
            self._plot = self.ax.pcolormesh(
                x, y, arr, norm=self.bounds.norm,
                cmap=cmap, rasterized=True, **self._kwargs)

    def _get_xy_pcolormesh(self):
        interp_bounds = self.interp_bounds.value
        if interp_bounds is None and not self.decoder.is_circumpolar(
                self.raw_data):
            interp_bounds = True
        if interp_bounds:
            return self.xbounds, self.ybounds
        else:
            return self.xcoord.values, self.ycoord.values

    def _contourf(self):
        if hasattr(self, '_plot') and self.plotter.has_changed(
                self.levels.key):
            self.remove()
        arr = self.array
        cmap = self.cmap.get_cmap(arr)
        filled = self.value not in ['contour', 'tricontour']
        if hasattr(self, '_plot'):
            self._plot.set_cmap(cmap)
            self._plot.set_norm(self.bounds.norm)
        else:
            levels = self.levels.norm.boundaries
            xcoord = self.xcoord
            ycoord = self.ycoord
            if self.plotter.convert_radian:
                xcoord = convert_radian(xcoord, xcoord)
                ycoord = convert_radian(ycoord, ycoord)
            if (self.value in ['tricontourf', 'tricontour'] or
                    self.decoder.is_unstructured(self.raw_data)):
                pm = self.ax.tricontourf if filled else self.ax.tricontour
                mask = ~np.isnan(arr)
                x = xcoord.values[mask]
                y = ycoord.values[mask]
                arr = arr[mask]
            else:
                pm = self.ax.contourf if filled else self.ax.contour
                x = xcoord.values
                y = ycoord.values
            self._plot = pm(
                x, y, arr, levels, norm=self.bounds.norm,
                cmap=cmap, **self._kwargs)

    @property
    def cell_nodes_x(self):
        """The unstructured x-boundaries with shape (N, m) where m > 2"""
        decoder = self.decoder
        xcoord = self.xcoord
        data = self.data
        xbounds = decoder.get_cell_node_coord(
            data, coords=data.coords, axis='x')
        if self.plotter.convert_radian:
            xbounds = convert_radian(xbounds, xcoord, xbounds)
        return xbounds.values

    @property
    def cell_nodes_y(self):
        """The unstructured y-boundaries with shape (N, m) where m > 2"""
        decoder = self.decoder
        ycoord = self.ycoord
        data = self.data
        ybounds = decoder.get_cell_node_coord(
            data, coords=data.coords, axis='y')
        if self.plotter.convert_radian:
            ybounds = convert_radian(ybounds, ycoord, ybounds)
        return ybounds.values

    def _polycolor(self):
        from matplotlib.collections import PolyCollection
        self.logger.debug('Retrieving bounds')
        xbounds = self.cell_nodes_x
        ybounds = self.cell_nodes_y
        self.logger.debug('Retrieving data')
        arr = self.array
        cmap = self.cmap.get_cmap(arr)
        if hasattr(self, '_plot'):
            self.logger.debug('Updating plot')
            self._plot.update(dict(cmap=cmap, norm=self.bounds.norm))
        else:
            self.logger.debug('Making plot with %i cells', arr.size)
            self._plot = PolyCollection(
                np.dstack([xbounds, ybounds]), array=arr.ravel(),
                norm=self.bounds.norm, rasterized=True, cmap=cmap,
                edgecolors='none', antialiaseds=False, **self._kwargs)
            self.logger.debug('Adding collection to axes')
            self.ax.add_collection(self._plot, autolim=False)
        self.logger.debug('Done.')

    def remove(self):
        if hasattr(self, '_plot'):
            try:
                self._plot.remove()
            except AttributeError:  # contour plot
                for artist in self._plot.collections[:]:
                    try:
                        artist.remove()
                    except ValueError:
                        pass
            del self._plot

    def add2format_coord(self, x, y):
        """Additional information for the :meth:`format_coord`"""
        if self.value is None:
            return ''
        data = self.data
        xcoord = self.xcoord
        ycoord = self.ycoord
        if self.decoder.is_unstructured(self.raw_data):
            x, y, z = self.get_xyz_tri(xcoord, x, ycoord, y, data)
        elif xcoord.ndim == 1:
            x, y, z = self.get_xyz_1d(xcoord, x, ycoord, y, data)
        elif xcoord.ndim == 2:
            x, y, z = self.get_xyz_2d(xcoord, x, ycoord, y, data)
        if z is None:
            return ''
        xunit = xcoord.attrs.get('units', '')
        if xunit:
            xunit = ' ' + xunit
        yunit = ycoord.attrs.get('units', '')
        if yunit:
            yunit = ' ' + yunit
        zunit = data.attrs.get('units', '')
        if zunit:
            zunit = ' ' + zunit
        return ', data: %s: %.4g%s, %s: %.4g%s, %s: %.4g%s' % (
            xcoord.name, x, xunit, ycoord.name, y, yunit,
            data.name, z, zunit)

    def get_xyz_tri(self, xcoord, x, ycoord, y, data):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        1d coords"""
        return self.get_xyz_2d(xcoord, x, ycoord, y, data)

    def get_xyz_1d(self, xcoord, x, ycoord, y, data):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        1d coords"""
        x_idx = xcoord.indexes[xcoord.name]
        y_idx = ycoord.indexes[ycoord.name]
        xclose = x_idx.get_loc(x, method='nearest')
        yclose = y_idx.get_loc(y, method='nearest')
        dx_max = np.diff(x_idx.sort_values()).max()
        dy_max = np.diff(y_idx.sort_values()).max()

        x_data = xcoord[xclose].values
        y_data = ycoord[yclose].values
        if abs(x_data - x) > dx_max or abs(y_data - y) > dy_max:
            val = None
        else:
            val = data[yclose, xclose].values
        return x_data, y_data, val

    def get_xyz_2d(self, xcoord, x, ycoord, y, data):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        2d coords"""
        xy = xcoord.values.ravel() + 1j * ycoord.values.ravel()
        dist = np.abs(xy - (x + 1j * y))
        imin = np.nanargmin(dist)
        xy_min = xy[imin]

        xb = self.decoder.get_cell_node_coord(
            data, {xcoord.name: xcoord, ycoord.name: ycoord},
            axis='x')
        yb = self.decoder.get_cell_node_coord(
            data, {xcoord.name: xcoord, ycoord.name: ycoord},
            axis='y')

        dx_max = np.diff(xb).max()
        dy_max = np.diff(yb).max()

        x_data = xy_min.real
        y_data = xy_min.imag

        if abs(x_data - x) > dx_max or abs(y_data - y) > dy_max:
            val = None
        else:
            val = data.values.ravel()[imin]

        return x_data, y_data, val


docstrings.delete_types('Bounds.possible_types', 'no_norm|None',
                        'None', 'matplotlib.colors.Normalize')


class ContourLevels(Bounds):
    """
    The levels for the contour plot

    This formatoption sets the levels for the filled contour plot and only has
    an effect if the :attr:`plot` Formatoption is set to ``'contourf'``

    Possible types
    --------------
    None
        Use the settings from the :attr:`bounds` formatoption and if this
        does not specify boundaries, use 11
    %(Bounds.possible_types.no_norm|None)s
    """

    dependencies = ['cbounds']

    priority = BEFOREPLOTTING

    name = 'Levels for the filled contour plot'

    def update(self, value):
        if value is None:
            try:
                value = self.cbounds.norm.boundaries
            except AttributeError:
                value = ['rounded', 11]
        super(ContourLevels, self).update(value)


class MaskDataGrid(Formatoption):
    """Mask the datagrid where the array is NaN

    This boolean formatoption enables to mask the grid of the :attr:`datagrid`
    formatoption where the data is NaN

    Possible types
    --------------
    bool
        Either True, to not display the data grid for cells with NaN, or False

    See Also
    --------
    datagrid"""

    def update(self, value):
        """dummy, since this fmt is considered in the :class:`DataGrid ` fmt"""
        pass



class DataGrid(Formatoption):
    """
    Show the grid of the data

    This formatoption shows the grid of the data (without labels)

    Possible types
    --------------
    None
        Don't show the data grid
    str
        A linestyle in the form ``'k-'``, where ``'k'`` is the color and
        ``'-'`` the linestyle.
    dict
        any keyword arguments that are passed to the plotting function (
        :func:`matplotlib.pyplot.triplot` for unstructured grids and
        :func:`matplotlib.pyplot.hlines` for rectilinear grids)

    See Also
    --------
    mask_datagrid: To display cells with NaN"""

    children = ['transform']

    dependencies = ['mask_datagrid']

    connections = ['plot']

    name = 'Grid of the data'

    @property
    def xcoord(self):
        """The x coordinate :class:`xarray.Variable`"""
        return self.decoder.get_x(self.data, coords=self.data.coords)

    @property
    def ycoord(self):
        """The y coordinate :class:`xarray.Variable`"""
        return self.decoder.get_y(self.data, coords=self.data.coords)

    @property
    def xbounds(self):
        """Boundaries of the x-coordinate"""
        return self.decoder.get_plotbounds(self.xcoord)

    @property
    def ybounds(self):
        """Boundaries of the y-coordinate"""
        return self.decoder.get_plotbounds(self.ycoord)

    @property
    def cell_nodes_x(self):
        """The unstructured x-boundaries with shape (N, m) where m > 2"""
        decoder = self.decoder
        xcoord = self.xcoord
        data = self.data
        xbounds = decoder.get_cell_node_coord(
            data, coords=data.coords, axis='x',
            nans='skip' if self.mask_datagrid.value else None)
        if self.plotter.convert_radian:
            xbounds = convert_radian(xbounds, xcoord, xbounds)
        return xbounds.values

    @property
    def cell_nodes_y(self):
        """The unstructured y-boundaries with shape (N, m) where m > 2"""
        decoder = self.decoder
        ycoord = self.ycoord
        data = self.data
        ybounds = decoder.get_cell_node_coord(
            data, coords=data.coords, axis='y',
            nans='skip' if self.mask_datagrid.value else None)
        if self.plotter.convert_radian:
            ybounds = convert_radian(ybounds, ycoord, ybounds)
        return ybounds.values

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(Formatoption.parameters)s"""
        super(DataGrid, self).__init__(*args, **kwargs)
        self._kwargs = {}

    def update(self, value):
        self.remove()
        if value is not None:
            xb = self.cell_nodes_x
            yb = self.cell_nodes_y
            n = len(xb)
            xb = np.c_[xb, xb[:, :1], [[np.nan]] * n].ravel()
            yb = np.c_[yb, yb[:, :1], [[np.nan]] * n].ravel()
            if isinstance(value, dict):
                self._artists = self.ax.plot(xb, yb, **value)
            else:
                self._artists = self.ax.plot(xb, yb, value)

    def remove(self):
        if not hasattr(self, '_artists'):
            return
        for artist in self._artists:
            artist.remove()
        del self._artists


class VectorDataGrid(DataGrid):

    @property
    def data(self):
        return super().data[0]


class SimplePlot2D(Plot2D):
    """
    Specify the plotting method

    Possible types
    --------------
    None
        Don't make any plotting
    'mesh'
        Use the :func:`matplotlib.pyplot.pcolormesh` function to make the plot
    """

    dependencies = Plot2D.dependencies + ['transpose']

    @property
    def array(self):
        if self.transpose.value:
            return super(SimplePlot2D, self).array.T
        else:
            return super(SimplePlot2D, self).array

    @property
    def xbounds(self):
        return self.decoder.get_plotbounds(self.transpose.get_x(
            self.data))

    @property
    def ybounds(self):
        return self.decoder.get_plotbounds(self.transpose.get_y(
            self.data))

    @property
    def xcoord(self):
        if self.transpose.value:
            return super(SimplePlot2D, self).ycoord
        return super(SimplePlot2D, self).xcoord

    @property
    def ycoord(self):
        if self.transpose.value:
            return super(SimplePlot2D, self).xcoord
        return super(SimplePlot2D, self).ycoord

    @property
    def cell_nodes_x(self):
        if self.transpose.value:
            return super(SimplePlot2D, self).cell_nodes_y
        return super(SimplePlot2D, self).cell_nodes_x

    @property
    def cell_nodes_y(self):
        if self.transpose.value:
            return super(SimplePlot2D, self).cell_nodes_x
        return super(SimplePlot2D, self).cell_nodes_y


class XTicks2D(XTicks):

    __doc__ = XTicks.__doc__

    @property
    def data(self):
        data = []
        plot_data = super(XTicks, self).data
        if not isinstance(plot_data, InteractiveList):
            plot_data = [plot_data]
        for da in plot_data:
            data.append(self.transpose.get_x(da))
        if len(data) == 1:
            return data[0]
        try:
            return xr.concat(data)
        except Exception:
            self.logger.debug(
                'Failed to concatenate the data, returning first object!',
                exc_info=True)
            return data[0]


class YTicks2D(YTicks):

    __doc__ = YTicks.__doc__

    @property
    def data(self):
        data = []
        plot_data = super(YTicks, self).data
        if not isinstance(plot_data, InteractiveList):
            plot_data = [plot_data]
        for da in plot_data:
            for da in plot_data:
                data.append(self.transpose.get_y(da))
        if len(data) == 1:
            return data[0]
        try:
            return xr.concat(data)
        except Exception:
            self.logger.debug(
                'Failed to concatenate the data, returning first object!',
                exc_info=True)
            return data[0]


class Extend(Formatoption):
    """
    Draw arrows at the side of the colorbar

    Possible types
    --------------
    str {'neither', 'both', 'min' or 'max'}
        If not 'neither', make pointed end(s) for out-of-range values
    """

    group = 'colors'

    name = 'Ends of the colorbar'

    connections = ['plot']

    def update(self, value):
        # nothing to do here because the extend is set by the Cbar formatoption
        if self.plot.value == 'contourf' and value != 'neither':
            warn('[%s] - Extend keyword is not implemented for contour '
                 'plots' % self.logger.name)
        else:
            self.plot.mappable.norm.extend = value


class CbarSpacing(Formatoption):
    """
    Specify the spacing of the bounds in the colorbar

    Possible types
    --------------
    str {'uniform', 'proportional'}
        if ``'uniform'``, every color has exactly the same width in the
        colorbar, if ``'proportional'``, the size is chosen according to the
        data"""

    group = 'colors'

    connections = ['cbar']

    name = 'Spacing of the colorbar'

    def update(self, value):
        self.cbar._kwargs['spacing'] = value


@docstrings.get_sections(base='Cbar')
class Cbar(Formatoption):
    """
    Specify the position of the colorbars

    Possible types
    --------------
    bool
        True: defaults to 'b'
        False: Don't draw any colorbar
    str
        The string can be a combination of one of the following strings:
        {'fr', 'fb', 'fl', 'ft', 'b', 'r', 'sv', 'sh'}

        - 'b', 'r' stand for bottom and right of the axes
        - 'fr', 'fb', 'fl', 'ft' stand for bottom, right, left and top of the
          figure
        - 'sv' and 'sh' stand for a vertical or horizontal colorbar in a
          separate figure
    list
        A containing one of the above positions

    Examples
    --------
    Draw a colorbar at the bottom and left of the axes::

    >>> plotter.update(cbar='bl')"""

    dependencies = ['plot', 'cmap', 'bounds', 'extend', 'cbarspacing',
                    'levels']

    group = 'colors'

    name = 'Position of the colorbar'

    priority = END + 0.1

    figure_positions = {'fr', 'fb', 'fl', 'ft', 'b', 'r', 'l', 't'}

    original_position = None

    @property
    def init_kwargs(self):
        return dict(chain(six.iteritems(super(Cbar, self).init_kwargs),
                          [('other_cbars', self.other_cbars)]))

    @docstrings.dedent
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(Formatoption.parameters)s
        other_cbars: list of str
            List of other colorbar formatoption keys (necessary for a
            sufficient resizing of the axes)"""
        self.other_cbars = kwargs.pop('other_cbars', [])
        super(Cbar, self).__init__(*args, **kwargs)
        self._kwargs = {}
        self._just_drawn = set()

    def initialize_plot(self, value):
        self._set_original_position()
        self.cbars = {}
        super(Cbar, self).initialize_plot(value)

    def _set_original_position(self):
        """Gets and sets the original position of the axes without colorbar"""
        # this is somewhat a hack to make sure that we get the right position
        # although the figure has not been drawn so far
        for key in self.other_cbars:
            fmto = getattr(self.plotter, key, None)
            if fmto is not None and fmto.original_position:
                self.original_position = fmto.original_position
                return
        ax = self.ax
        if ax._adjustable in ['box', 'box-forced']:
            figW, figH = ax.get_figure().get_size_inches()
            fig_aspect = figH / figW
            position = ax.get_position(True)
            pb = position.frozen()
            box_aspect = ax.get_data_ratio()
            pb1 = pb.shrunk_to_aspect(box_aspect, pb, fig_aspect)
            self.original_position = pb1.anchored(ax.get_anchor(), pb)
        else:
            self.original_position = ax.get_position(True)

    @property
    def value2share(self):
        """Those colorbar positions that are directly at the axes"""
        return self.value.intersection(['r', 'b', 'l', 't'])

    def update(self, value):
        """
        Updates the colorbar

        Parameters
        ----------
        value
            The value to update (see possible types)
        no_fig_cbars
            Does not update the colorbars that are not in the axes of this
            plot"""
        plotter = self.plotter
        if plotter.replot or any(
                plotter.has_changed(key, False) for key in self.dependencies
                if getattr(self, key, None) is not None and key not in [
                        self._child_mapping['cmap'], self._child_mapping[
                            'bounds']]):
            cbars2delete = set(self.cbars)
        else:
            changed_bounds = plotter.has_changed(self.bounds.key)
            if changed_bounds and (type(changed_bounds[0]) is not
                                   type(changed_bounds[1])):
                cbars2delete = set(self.cbars)
            else:
                cbars2delete = set(self.cbars).difference(value)
        if cbars2delete:
            # if the colorbars are in the figure of the axes, we have to first
            # remove all the colorbars and then redraw it in order to make
            # sure that the axes gets the right position
            if cbars2delete & self.figure_positions:
                cbars2delete.update(self.figure_positions)
                self.remove(positions=cbars2delete)
                # remove other cbars
                for key in self.other_cbars:
                    fmto = getattr(plotter, key)
                    fmto.remove(self.figure_positions)
                # redraw other cbars
                for key in self.other_cbars:
                    fmto = getattr(plotter, key)
                    fmto.update(fmto.value)
            else:
                self.remove(positions=cbars2delete)
        for pos in value.intersection(self.cbars):
            if self.plot.value is not None:
                self.update_colorbar(pos)
        for pos in sorted(value.difference(self.cbars)):
            if self.plot.value is not None:
                self.draw_colorbar(pos)
        plotter._figs2draw.update(map(lambda cbar: cbar.ax.get_figure(),
                                      six.itervalues(self.cbars)))

    def update_colorbar(self, pos):
        cbar = self.cbars[pos]
        mappable = self.plot.mappable
        if mpl.__version__ < '3.1':
            cbar.set_norm(self.plot.mappable.norm)
            cbar.set_cmap(self.plot.mappable.cmap)
        else:  # change the colorbar and reconnect signals
            old = cbar.mappable
            cbar.update_normal(mappable)
            if not getattr(mappable, 'colorbar_cid', False):
                if getattr(old, 'colorbar_cid', False):
                    old.callbacksSM.disconnect(old.colorbar_cid)
                    old.colorbar = None
                    old.colorbar_cid = None
                cid = mappable.callbacksSM.connect(
                    'changed', cbar.on_mappable_changed)
                mappable.colorbar = cbar
                mappable.colorbar_cid = cid
            cbar.update_normal(cbar.mappable)
        cbar.draw_all()

    def remove(self, positions='all'):
        import matplotlib.pyplot as plt

        def try2remove(cbar):
            try:
                cbar.remove()
            except KeyError:
                # the colorbar has been removed already from some other
                # Cbar instance
                pass
        if positions == 'all':
            positions = self.cbars.keys()
        positions = set(positions).intersection(self.cbars.keys())
        if not positions:
            return
        adjustment = {}
        to_adjust = {'fr': 'right', 'fl': 'left', 'ft': 'top', 'fb': 'bottom'}
        for pos in positions:
            cbar = self.cbars.pop(pos)
            if pos in ['sh', 'sv']:
                plt.close(cbar.ax.get_figure())
            else:
                # set the axes for the mappable if this has been removed
                mappable = cbar.mappable
                delaxes = not hasattr(mappable, 'axes')
                if getattr(mappable, 'axes', None) is None:
                    mappable.axes = self.plotter.ax
                    try2remove(cbar)
                    if delaxes:
                        del mappable.axes
                    else:
                        mappable.axes = None
                else:
                    try2remove(cbar)
                if pos in to_adjust:
                    adjustment[to_adjust[pos]] = mpl.rcParams[
                        'figure.subplot.' + to_adjust[pos]]
        if adjustment:
            self.ax.get_figure().subplots_adjust(**adjustment)
        if self.figure_positions.intersection(positions):
            self.ax.set_position(self.original_position)
        return

    def draw_colorbar(self, pos):
        import matplotlib.pyplot as plt
        # TODO: Manage to draw colorbars left and top (gridspec does not work)
        orientations = {
            # 'b': 'bottom', 'r': 'right', 'l': 'left', 't': 'top',
            'b': 'horizontal', 'r': 'vertical',
            'fr': 'vertical', 'fl': 'vertical', 'sv': 'vertical',
            'ft': 'horizontal', 'fb': 'horizontal', 'sh': 'horizontal'}

        orientation = orientations[pos]
        kwargs = self._kwargs.copy()
        if pos in ['b', 'r', 'l', 't']:
            fig = self.ax.get_figure()
            # kwargs = {'ax': self.ax, 'location': orientation}
            kwargs.update({'ax': self.ax, 'orientation': orientation})
        elif pos == 'sh':
            fig = plt.figure(figsize=(8, 1))
            kwargs.update({'cax': fig.add_axes([0.05, 0.5, 0.9, 0.3])})
            self.plotter._figs2draw.add(fig)  # add figure for drawing
        elif pos == 'sv':
            fig = plt.figure(figsize=(1, 8))
            kwargs.update({'cax': fig.add_axes([0.3, 0.05, 0.3, 0.9])})
            self.plotter._figs2draw.add(fig)  # add figure for drawing
        else:
            fig = self.ax.get_figure()
            if pos == 'fb':
                fig.subplots_adjust(bottom=0.2)
                kwargs['cax'] = fig.add_axes(
                    [0.125, 0.135, 0.775, 0.05],
                    label=self.raw_data.psy.arr_name + '_fb')
            elif pos == 'fr':
                fig.subplots_adjust(right=0.8)
                kwargs['cax'] = fig.add_axes(
                    [0.825, 0.25, 0.035, 0.6],
                    label=self.raw_data.psy.arr_name + '_fr')
            elif pos == 'fl':
                fig.subplots_adjust(left=0.225)
                kwargs['cax'] = fig.add_axes(
                    [0.075, 0.25, 0.035, 0.6],
                    label=self.raw_data.psy.arr_name + '_fl')
            elif pos == 'ft':
                fig.subplots_adjust(top=0.75)
                kwargs['cax'] = fig.add_axes(
                    [0.125, 0.825, 0.775, 0.05],
                    label=self.raw_data.psy.arr_name + '_ft')
        if float('.'.join(mpl.__version__.split('.')[:2])) <= 3.2:
            kwargs['extend'] = self.extend.value
        if 'location' not in kwargs:
            kwargs['orientation'] = orientation
        self.cbars[pos] = cbar = fig.colorbar(self.plot.mappable, **kwargs)
        self._just_drawn.add(cbar)
        self.set_label_pos(pos)

    def set_label_pos(self, pos):
        ax = self.cbars[pos].ax
        if pos == 'fl':
            # draw tick labels left
            ax.tick_params('y', labelleft=True, labelright=False)
            ax.yaxis.set_label_position('left')
            ax.yaxis.tick_left()
        elif pos == 'ft':
            # draw ticklabels at the top
            ax.tick_params('x', labeltop=True, labelbottom=False)
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()
        elif pos == 'r':
            # draw ticklabels on the right
            ax.tick_params('y', labelleft=False, labelright=True)
            ax.yaxis.set_label_position('right')
            ax.yaxis.tick_right()

    def finish_update(self):
        # Set the label position again in case this has been changed
        for pos, cbar in self.cbars.items():
            self.set_label_pos(pos)
        self._just_drawn.clear()


class CLabel(TextBase, Formatoption):
    """
    Show the colorbar label

    Set the label of the colorbar.
    %(replace_note)s

    Possible types
    --------------
    str
        The title for the :meth:`~matplotlib.colorbar.Colorbar.set_label`
        method.

    See Also
    --------
    clabelsize, clabelweight, clabelprops"""

    children = ['plot']

    dependencies = ['cbar']

    name = 'Colorbar label'

    data_dependent = True

    group = 'labels'

    axis_locations = {
            'b': 'x', 'r': 'y', 'l': 'y', 't': 'x',  # axes locations
            'fr': 'y', 'fl': 'y', 'sv': 'y',         # vertical figure cbars
            'ft': 'x', 'fb': 'x', 'sh': 'x'}         # horizontal figure cbars

    def update(self, value):
        arr = self.plot.data
        self.texts = []
        for pos, cbar in six.iteritems(self.cbar.cbars):
            cbar.set_label(self.replace(
                    value, arr, attrs=self.get_enhanced_attrs(arr)))
            self.texts.append(getattr(
                cbar.ax, self.axis_locations[pos] + 'axis').get_label())


class VCLabel(CLabel):
    """
    Show the colorbar label of the vector plot

    Set the label of the colorbar.
    %(replace_note)s

    Possible types
    --------------
    str
        The title for the :meth:`~matplotlib.colorbar.Colorbar.set_label`
        method.

    See Also
    --------
    vclabelsize, vclabelweight, vclabelprops"""
    pass


class CbarOptions(Formatoption):
    """Base class for colorbar formatoptions"""

    which = 'major'

    children = ['plot']

    dependencies = ['cbar']

    @property
    def colorbar(self):
        try:
            return self._colorbar
        except AttributeError:
            try:
                pos, cbar = next(six.iteritems(self.cbar.cbars))
            except StopIteration:
                raise AttributeError("No colorbar set")
            self.position = pos
            self.colorbar = cbar
            return self.colorbar

    @colorbar.setter
    def colorbar(self, cbar):
        self._colorbar = cbar

    @property
    def axis(self):
        """axis of the colorbar with the ticks. Will be overwritten during
        update process."""
        return getattr(
            self.colorbar.ax, self.axis_locations[self.position] + 'axis')

    @property
    def axisname(self):
        return self.axis_locations[self.position]

    @property
    def data(self):
        try:
            return self.plot.data
        except AttributeError:
            return super().data

    axis_locations = CLabel.axis_locations

    def update(self, value):
        for pos, cbar in six.iteritems(self.cbar.cbars):
            self.colorbar = cbar
            self.position = pos
            self.update_axis(value)


@docstrings.get_sections(base='CTicks')
class CTicks(CbarOptions, TicksBase):
    """
    Specify the tick locations of the colorbar

    Possible types
    --------------
    None
        use the default ticks
    %(DataTicksCalculator.possible_types)s
            bounds
                let the :attr:`bounds` keyword determine the ticks. An
                additional integer `i` may be specified to only use every i-th
                bound as a tick (see also `int` below)
            midbounds
                Same as `bounds` but in the middle between two bounds
    int
        Specifies how many ticks to use with the ``'bounds'`` option. I.e. if
        integer ``i``, then this is the same as ``['bounds', i]``.

    See Also
    --------
    cticklabels
    """

    dependencies = CbarOptions.dependencies + ['bounds']

    connections = CbarOptions.connections + ['cmap']

    name = 'Colorbar ticks'

    _default_locator = None

    @property
    def default_locator(self):
        """Default locator of the axis of the colorbars"""
        if self._default_locator is None:
            self.set_default_locators()
        return self._default_locator

    @default_locator.setter
    def default_locator(self, locator):
        self._default_locator = locator

    def __init__(self, *args, **kwargs):
        super(CTicks, self).__init__(*args, **kwargs)
        self.calc_funcs['bounds'] = self._bounds_ticks
        self.calc_funcs['midbounds'] = self._mid_bounds_ticks

    def set_ticks(self, value):
        self.ticks = value
        self.colorbar.set_ticks(value)

    def _bounds_ticks(self, step=None, *args, **kwargs):
        step = step or 1
        return self.bounds.bounds[::step]

    def _mid_bounds_ticks(self, step=None, *args, **kwargs):
        step = step or 1
        ret = 0.5 * (self.bounds.bounds[1:] + self.bounds.bounds[:-1])
        return ret[::step]

    def update(self, value):
        # reset the locators if the colorbar has been drawn from scratch
        if self.cbar._just_drawn or (
                not self.plotter.has_changed(self.key) and self.value is None):
            if self.cbar.cbars:
                try:
                    del self._colorbar
                except AttributeError:
                    pass
                self.set_default_locators()
        super(CTicks, self).update(value)

    def update_axis(self, value):
        cbar = self.colorbar
        if value is None:
            cbar.locator = self.default_locator
            cbar.formatter = self.default_formatter
            cbar.update_ticks()
        else:
            TicksBase.update_axis(self, value)

    def set_default_locators(self, *args, **kwargs):
        try:
            cbar = self.colorbar
        except AttributeError:
            pass
        else:
            self.default_locator = cbar.locator
            self.default_formatter = cbar.formatter

    def get_fmt_widget(self, parent, project):
        """Open a :class:`psy_simple.widget.CMapFmtWidget`"""
        from psy_simple.widgets.colors import CTicksFmtWidget
        return CTicksFmtWidget(parent, self, project)


class VectorCTicks(CTicks):
    """
    Specify the tick locations of the vector colorbar

    Possible types
    --------------
    %(CTicks.possible_types)s

    See Also
    --------
    cticklabels, vcticklabels
    """

    dependencies = CTicks.dependencies + ['color']

    @property
    def array(self):
        arr = self.color._color_array
        return arr[~np.isnan(arr)]


class CTickLabels(CbarOptions, TickLabelsBase):
    """
    Specify the colorbar ticklabels

    Possible types
    --------------
    %(TickLabelsBase.possible_types)s

    See Also
    --------
    cticks, cticksize, ctickweight, ctickprops
    vcticks, vcticksize, vctickweight, vctickprops
    """

    name = 'Colorbar ticklabels'

    @property
    def default_formatters(self):
        """Default locator of the axis of the colorbars"""
        if self._default_formatters:
            return self._default_formatters
        else:
            self.set_default_formatters()
        return self._default_formatters

    @default_formatters.setter
    def default_formatters(self, d):  # d is expected to be a dictionary
        self._default_formatters = d

    def set_default_formatters(self):
        if self.cbar.cbars:
            self.default_formatters = {self.which: self.colorbar.formatter}

    def set_formatter(self, formatter):
        cbar = self.colorbar
        cbar.formatter = formatter
        cbar.update_ticks()


class CTickSize(CbarOptions, TickSizeBase):
    """
    Specify the font size of the colorbar ticklabels

    Possible types
    --------------
    %(fontsizes)s

    See Also
    --------
    ctickweight, ctickprops, cticklabels, cticks
    vctickweight, vctickprops, vcticklabels, vcticks"""

    group = 'colors'

    name = 'Font size of the colorbar ticklabels'

    dependencies = CbarOptions.dependencies + ['ctickprops']


class CTickWeight(CbarOptions, TickWeightBase):
    """
    Specify the fontweight of the colorbar ticklabels

    Possible types
    --------------
    %(fontweights)s

    See Also
    --------
    cticksize, ctickprops, cticklabels, cticks
    vcticksize, vctickprops, vcticklabels, vcticks"""

    group = 'colors'

    name = 'Font weight of the colorbar ticklabels'

    dependencies = CbarOptions.dependencies + ['ctickprops']


class CTickProps(CbarOptions, TickPropsBase):
    """
    Specify the font properties of the colorbar ticklabels

    Possible types
    --------------
    %(TickPropsBase.possible_types)s

    See Also
    --------
    cticksize, ctickweight, cticklabels, cticks
    vcticksize, vctickweight, vcticklabels, vcticks"""

    children = CbarOptions.children + TickPropsBase.children

    group = 'colors'

    name = 'Font properties of the colorbar ticklabels'

    def update_axis(self, value):
        value = value.copy()
        default = self.default
        if 'major' in default or 'minor' in default:
            default = default.get(self.which, {})
        for key, val in chain(
                default.items(), mpl.rcParams.find_all(
                    self.axisname + 'tick\.%s\.\w' % self.which).items()):
            value.setdefault(key.split('.')[-1], val)

        if float('.'.join(mpl.__version__.split('.')[:2])) >= 1.5:
            value.pop('visible', None)
        posnames = ['top', 'bottom'] if self.axisname == 'x' else [
            'left', 'right']
        label_positions = dict(zip(
            map('label{}'.format, posnames),
            [True, False] if self.position in ['t', 'ft', 'l', 'fl'] else
            [False, True]))
        label_positions.update(**value)
        self.colorbar.ax.tick_params(
            self.axisname, which=self.which, reset=True, **label_positions)


class ArrowSize(Formatoption):
    """
    Change the size of the arrows

    Possible types
    --------------
    None
        make no scaling
    float
        Factor scaling the size of the arrows

    See Also
    --------
    arrowstyle, linewidth, density, color"""

    group = 'vector'

    priority = BEFOREPLOTTING

    dependencies = ['plot']

    name = 'Size of the arrows'

    def update(self, value):
        kwargs = self.plot._kwargs
        if self.plot.value == 'stream':
            kwargs.pop('scale', None)
            kwargs['arrowsize'] = value or 1.0
        else:
            kwargs.pop('arrowsize', None)
            kwargs['scale'] = value


class ArrowStyle(Formatoption):
    """Change the style of the arrows

    Possible types
    --------------
    str
        Any arrow style string (see
        :class:`~matplotlib.patches.FancyArrowPatch`)

    Notes
    -----
    This formatoption only has an effect for stream plots

    See Also
    --------
    arrowsize, linewidth, density, color"""

    group = 'vector'

    priority = BEFOREPLOTTING

    dependencies = ['plot']

    name = 'Style of the arrows'

    def update(self, value):
        if self.plot.value == 'stream':
            self.plot._kwargs['arrowstyle'] = value
        else:
            self.plot._kwargs.pop('arrowstyle', None)


@docstrings.get_sections(base='WindCalculator')
class VectorCalculator(Formatoption):
    """
    Abstract formatoption that provides calculation functions for speed, etc.

    Possible types
    --------------
    string {'absolute', 'u', 'v'}
        Strings may define how the formatoption is calculated. Possible strings
        are

        - **absolute**: for the absolute wind speed
        - **u**: for the u component
        - **v**: for the v component
    """

    dependencies = ['plot', 'transpose']

    priority = BEFOREPLOTTING

    data_dependent = True

    def __init__(self, *args, **kwargs):
        super(VectorCalculator, self).__init__(*args, **kwargs)
        self._calc_funcs = {
            'absolute': self._calc_speed,
            'u': self._get_u,
            'v': self._get_v}

    def _maybe_ravel(self, arr):
        if (getattr(self, 'transpose', None) is not None and
                self.transpose.value):
            arr = arr.T
        if self.plot.value == 'quiver':
            return np.ravel(arr)
        return np.asarray(arr)

    def _calc_speed(self, scale=1.0):
        data = self.plot.data
        return self._maybe_ravel(
            np.sqrt(data[0].values**2 + data[1].values**2)) * scale

    def _get_u(self, scale=1.0):
        return self._maybe_ravel(self.plot.data[0].values) * scale

    def _get_v(self, scale=1.0):
        return self._maybe_ravel(self.plot.data[1].values) * scale


class VectorLineWidth(VectorCalculator):
    """
    Change the linewidth of the arrows

    Possible types
    --------------
    float
        give the linewidth explicitly
    %(WindCalculator.possible_types)s
    tuple (string, float)
        `string` may be one of the above strings, `float` may be a scaling
        factor
    2D-array
        The values determine the linewidth for each plotted arrow. Note that
        the shape has to match the one of u and v.

    See Also
    --------
    arrowsize, arrowstyle, density, color"""

    name = 'Linewidth of the arrows'

    def update(self, value):
        if value is None:
            self.plot._kwargs['linewidth'] = 0 if self.plot.value == 'quiver' \
                else None
        elif np.asarray(value).ndim and isinstance(value[0], six.string_types):
            self.plot._kwargs['linewidth'] = self._calc_funcs[value[0]](
                *value[1:])
        else:
            self.plot._kwargs['linewidth'] = self._maybe_ravel(value)


class VectorColor(VectorCalculator):
    """
    Set the color for the arrows

    This formatoption can be used to set a single color for the vectors or
    define the color coding

    Possible types
    --------------
    float
        Determines the greyness
    color
        Defines the same color for all arrows. The string can be either a html
        hex string (e.g. '#eeefff'), a single letter (e.g. 'b': blue,
        'g': green, 'r': red, 'c': cyan, 'm': magenta, 'y': yellow, 'k': black,
        'w': white) or any other color
    %(WindCalculator.possible_types)s
    2D-array
        The values determine the color for each plotted arrow. Note that
        the shape has to match the one of u and v.

    See Also
    --------
    arrowsize, arrowstyle, density, linewidth"""

    dependencies = VectorCalculator.dependencies + ['cmap', 'bounds']

    group = 'colors'

    name = 'Color of the arrows'

    def update(self, value):
        try:
            value = validate_color(value)
            self.colored = False
        except ValueError:
            if (isinstance(value, six.string_types) and
                    value in self._calc_funcs):
                value = self._calc_funcs[value]()
                self.colored = True
                self._color_array = value
            else:
                try:
                    value = validate_float(value)
                    self.colored = False
                except ValueError:
                    value = self._maybe_ravel(value)
                    self.colored = True
                    self._color_array = value
        if self.plot.value == 'quiver' and self.colored:
            self.plot._args = [value]
            self.plot._kwargs.pop('color', None)
        else:
            self.plot._args = []
            self.plot._kwargs['color'] = value
        if self.colored:
            self._set_cmap()
        else:
            self._delete_cmap()

    def _set_cmap(self):
        if self.plotter.has_changed(self.key) or self.plotter._initializing:
            self.bounds.update(self.bounds.value)
        self.plot._kwargs['cmap'] = get_cmap(
            self.cmap.value, len(self.bounds.bounds) - 1 or None)
        self.plot._kwargs['norm'] = self.bounds.norm

    def _delete_cmap(self):
        self.plot._kwargs.pop('cmap', None)
        self.plot._kwargs.pop('norm', None)


@docstrings.get_sections(base='Density')
class Density(Formatoption):
    """
    Change the density of the arrows

    Possible types
    --------------
    float
        Scales the density of the arrows in x- and y-direction (1.0 means
        no scaling)
    tuple (x, y)
        Defines the scaling in x- and y-direction manually

    Notes
    -----
    quiver plots do not support density scaling
    """

    dependencies = ['plot']

    group = 'vector'

    name = 'Density of the arrows'

    priority = BEFOREPLOTTING

    data_dependent = True

    def __init__(self, *args, **kwargs):
        super(Density, self).__init__(*args, **kwargs)
        self._density_funcs = {
            'stream': self._set_stream_density,
            'quiver': self._set_quiver_density}
        self._remove_funcs = {
            'stream': self._unset_stream_density,
            'quiver': self._unset_quiver_density}

    def update(self, value):
        has_changed = self.plotter.has_changed(self.plot.key)
        if has_changed:
            self.remove(has_changed[0])
        try:
            value = tuple(value)
        except TypeError:
            value = [value, value]
        if self.plot.value:
            self._density_funcs[self.plot.value](value)

    def _set_stream_density(self, value):
        return
        self.plot._kwargs['density'] = value

    def _set_quiver_density(self, value):
        if any(val != 1.0 for val in value):
            warn("[%s] - Quiver plot does not support the density "
                 "keyword!" % self.logger.name,
                 RuntimeWarning)

    def _unset_stream_density(self):
        self.plot._kwargs.pop('density', None)

    def _unset_quiver_density(self):
        pass

    def remove(self, plot_type=None):
        plot_type = plot_type or self.plot.value
        self._remove_funcs[plot_type]()


class VectorPlot(Formatoption):
    """
    Choose the vector plot type

    Possible types
    --------------
    str
        Plot types can be either

        quiver
            to make a quiver plot
        stream
            to make a stream plot"""

    plot_fmt = True

    group = 'plotting'

    name = 'Plot type of the arrows'

    priority = BEFOREPLOTTING

    children = ['cmap', 'bounds']

    connections = ['transpose', 'transform', 'arrowsize', 'arrowstyle',
                   'density', 'linewidth', 'color']

    @property
    def format_coord(self):
        """The function that can replace the axes.format_coord method"""
        return format_coord_func(self.ax, weakref.ref(self))

    @property
    def mappable(self):
        """The mappable, i.e. the container of the plot"""
        if self.value == 'stream':
            return self._plot.lines
        else:
            return self._plot

    @property
    def xcoord(self):
        """The x coordinate :class:`xarray.Variable`"""
        v = next(self.raw_data.psy.iter_base_variables)
        return self.decoder.get_x(v, coords=self.data.coords)

    @property
    def ycoord(self):
        """The y coordinate :class:`xarray.Variable`"""
        v = next(self.raw_data.psy.iter_base_variables)
        return self.decoder.get_y(v, coords=self.data.coords)

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        self._plot_funcs = {
            'quiver': self._quiver_plot,
            'stream': self._stream_plot}
        self._orig_format_coord = None
        self._args = []
        self._kwargs = {}

    @property
    def array(self):
        return self.data.values

    def update(self, value):
        pass
        # the real plot making is done by make_plot but we store the value here
        # in case it is shared

    def make_plot(self):
        # remove the plot if it shall be replotted or any of the dependencies
        # changed. Otherwise there is nothing to change
        if hasattr(self, '_plot') and (self.plotter.replot or any(
                self.plotter.has_changed(key) for key in chain(
                    self.connections, self.dependencies, [self.key]))):
            self.remove()
        if not hasattr(self, "_plot") and self.value is not None:
            self._plot_funcs[self.value]()
            if self._orig_format_coord is None:
                self._orig_format_coord = self.ax.format_coord
                self.ax.format_coord = self.format_coord

    def _quiver_plot(self):
        x, y, u, v = self._get_data()
        self._plot = self.ax.quiver(x, y, u, v, *self._args, rasterized=True,
                                    **self._kwargs)

    def _stream_plot(self):
        x, y, u, v = self._get_data()
        dx = (x[-1] - x[0]) / (len(x) - 1)
        dy = (y[-1] - y[0]) / (len(y) - 1)
        if not np.allclose(np.diff(x), dx):
            warn("Rescaling x to be equally spaced!", PsyPlotRuntimeWarning)
            x = x[0] + np.zeros_like(x) + (np.arange(len(x)) * dx)
        if not np.allclose(np.diff(y), dy):
            warn("Rescaling y to be equally spaced!", PsyPlotRuntimeWarning)
            y = y[0] + np.zeros_like(y) + (np.arange(len(y)) * dy)
        self._plot = self.ax.streamplot(x, y, u, v, **self._kwargs)

    def _get_data(self):
        data = self.data
        if self.transpose.value:
            u = data[0].T.values
            v = data[1].T.values
        else:
            u, v = data.values
        x = self.transpose.get_x(data)
        y = self.transpose.get_y(data)
        return np.asarray(x), np.asarray(y), u, v

    def remove(self):

        def keep(x):
            return not isinstance(x, mpl.patches.FancyArrowPatch)

        if not hasattr(self, '_plot'):
            return
        if isinstance(self._plot, mpl.streamplot.StreamplotSet):
            try:
                self._plot.lines.remove()
            except ValueError:
                pass
            # remove arrows
            self.ax.patches = [patch for patch in self.ax.patches
                               if keep(patch)]
        else:
            try:
                self._plot.remove()
            except ValueError:  # the artist has already been removed
                pass
        del self._plot

    def add2format_coord(self, x, y):
        """Additional information for the :meth:`format_coord`"""
        u, v = self.data
        uname, vname = self.data.coords['variable'].values
        xcoord = self.xcoord
        ycoord = self.ycoord
        if self.decoder.is_unstructured(self.raw_data[0]):
            x, y, z1, z2 = self.get_xyz_tri(xcoord, x, ycoord, y, u, v)
        elif xcoord.ndim == 1:
            x, y, z1, z2 = self.get_xyz_1d(xcoord, x, ycoord, y, u, v)
        elif xcoord.ndim == 2:
            x, y, z1, z2 = self.get_xyz_2d(xcoord, x, ycoord, y, u, v)
        speed = (z1**2 + z2**2)**0.5
        xunit = xcoord.attrs.get('units', '')
        if xunit:
            xunit = ' ' + xunit
        yunit = ycoord.attrs.get('units', '')
        if yunit:
            yunit = ' ' + yunit
        zunit = u.attrs.get('units', '')
        if zunit:
            zunit = ' ' + zunit
        return (', vector data: %s: %.4g%s, %s: %.4g%s, %s: %.4g%s, '
                '%s: %.4g%s, absolute: %.4g%s') % (
                    xcoord.name, x, xunit, ycoord.name, y, yunit,
                    uname, z1, zunit, vname, z2, zunit,
                    speed, zunit)

    def get_xyz_tri(self, xcoord, x, ycoord, y, u, v):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        1d coords"""
        return self.get_xyz_2d(xcoord, x, ycoord, y, u, v)

    def get_xyz_1d(self, xcoord, x, ycoord, y, u, v):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        1d coords"""
        xclose = xcoord.indexes[xcoord.name].get_loc(x, method='nearest')
        yclose = ycoord.indexes[ycoord.name].get_loc(y, method='nearest')
        uval = u[yclose, xclose].values
        vval = v[yclose, xclose].values
        return xcoord[xclose].values, ycoord[yclose].values, uval, vval

    def get_xyz_2d(self, xcoord, x, ycoord, y, u, v):
        """Get closest x, y and z for the given `x` and `y` in `data` for
        2d coords"""
        xy = xcoord.values.ravel() + 1j * ycoord.values.ravel()
        dist = np.abs(xy - (x + 1j * y))
        imin = np.nanargmin(dist)
        xy_min = xy[imin]
        return (xy_min.real, xy_min.imag, u.values.ravel()[imin],
                v.values.ravel()[imin])


class SimpleVectorPlot(VectorPlot):
    # disable the stream plot for unstructured grids because it is not supported
    # for 1d arrays and for circumpolar grids because 2d coordinates are not
    # supported

    __doc__ = VectorPlot.__doc__

    def set_value(self, value, *args, **kwargs):
        if value == 'stream' and self.raw_data is not None:
            u = self.raw_data[0]
            if u.psy.decoder.is_unstructured(u):
                warn('[%s] - Streamplot is not supported for unstructured '
                     'grids!' % self.logger.name)
                value = 'quiver'
            elif u.psy.decoder.is_circumpolar(u):
                warn('[%s] - Streamplot is not supported for circumpolar '
                     'grids!' % self.logger.name)
                value = 'quiver'
        super(SimpleVectorPlot, self).set_value(value, *args, **kwargs)


class CombinedVectorPlot(VectorPlot):

    __doc__ = VectorPlot.__doc__

    def update(self, *args, **kwargs):
        self._kwargs['zorder'] = 2
        super(CombinedVectorPlot, self).update(*args, **kwargs)


class VectorCbar(Cbar):
    """
    Specify the position of the vector plot colorbars

    Possible types
    --------------
    %(Cbar.possible_types)s
    """

    dependencies = Cbar.dependencies + ['color']

    priority = END

    def update(self, *args, **kwargs):
        if self.color.colored:
            super(VectorCbar, self).update(*args, **kwargs)
        else:
            self.remove()


class VectorBounds(Bounds):
    """
    Specify the boundaries of the vector colorbar

    Possible types
    --------------
    %(Bounds.possible_types)s

    Examples
    --------
    %(Bounds.examples)s

    See Also
    --------
    %(Bounds.see_also)s"""

    parents = ['color']

    @property
    def array(self):
        arr = self.color._color_array
        return arr[~np.isnan(arr)]

    def update(self, *args, **kwargs):
        if not self.color.colored:
            return
        return super(VectorBounds, self).update(*args, **kwargs)


class LegendLabels(Formatoption, TextBase):
    """
    Set the labels of the arrays in the legend

    This formatoption specifies the labels for each array in the legend.
    %(replace_note)s

    Possible types
    --------------
    str:
        A single string that shall be used for all arrays.
    list of str:
        Same as a single string but specified for each array

    See Also
    --------
    legend"""

    data_dependent = True

    name = 'Labels in the legend'

    def update(self, value):
        def get1d(arr):
            if arr.ndim > 1:
                return arr[0]
            return arr
        if isinstance(value, six.string_types):
            self.labels = [
                self.replace(value, arr, self.get_enhanced_attrs(
                    get1d(arr), replot=True))
                for arr in self.iter_data]
        else:
            self.labels = [
                self.replace(val, arr, self.get_enhanced_attrs(
                    get1d(arr), replot=True)) for val, arr in zip(
                        value, self.iter_data)]


class Legend(DictFormatoption):
    """
    Draw a legend

    This formatoption determines where and if to draw the legend. It uses the
    :attr:`labels` formatoption to determine the labels.

    Possible types
    --------------
    bool
        Draw a legend or not
    str or int
        Specifies where to plot the legend (i.e. the location)
    dict
        Give the keywords for the :func:`matplotlib.pyplot.legend` function

    See Also
    --------
    labels"""

    dependencies = ['legendlabels', 'plot', 'color', 'marker']

    name = 'Properties of the legend'

    def update(self, value):
        self.remove()
        shared_by = self.shared_by
        if shared_by is not None:
            # update the legend of the other formatoption instead of this one
            if not shared_by.plotter._updating:
                shared_by.update(shared_by.value)
            return
        if not value.get('loc'):
            return
        artists = []
        labels = []
        for fmto in self.shared.union([self]):
            if hasattr(fmto.plot, '_plot'):
                this_artists, this_labels = fmto.get_artists_and_labels()
                artists.extend(this_artists)
                labels.extend(this_labels)
        self.legend = self.ax.legend(artists, labels, **value)

    def get_artists_and_labels(self):
        return self.plot._plot, [
            l for l, ls in zip(self.legendlabels.labels,
                               cycle(slist(self.plot.value)))
            if ls is not None]

    def remove(self):
        if hasattr(self, 'legend'):
            self.legend.remove()


class MeanCalculator(Formatoption):
    """
    Determine how the error is visualized

    Possible types
    --------------
    'mean'
        Calculate the weighted mean
    'median'
        Calculate the weighted median (i.e. the 50th percentile)
    float between 0 and 100
        Calculate the given quantile

    See Also
    --------
    err_calc: Determines how to calculate the error
    """

    priority = START

    name = 'Mean calculation'

    group = 'data'

    data_dependent = True

    requires_replot = True

    def update(self, value):
        for i, arr in enumerate(self.iter_data):
            if value == 'mean':
                data = arr.psy.fldmean()
            elif value == 'median':
                data = arr.psy.fldpctl(50)
            else:
                data = arr.psy.fldpctl(value)
            data.psy.arr_name = arr.psy.arr_name
            self.set_data(data, i)


class ErrorCalculator(Formatoption):
    """
    Calculation of the error

    This formatoption is used to calculate the error range.

    Possible types
    --------------
    None
        Do not calculate any error range
    float
        A float between 0 and 50. This will represent the distance from the
        median (i.e. the 50th percentile). A value of 45 will hence correspond
        to the 5th and 95th percentile
    list of 2 floats between 0 and 100
        Two floats where the first corresponds to the minimum and the second
        to the maximum percentile
    str
        A string with 'std' in it. Then we will use the standard deviation. Any
        number in this string, e.g. '3.5std' will serve as a multiplier
        (in this case 3.5 times the standard deviation).

    See Also
    --------
    mean: Determines how the line is calculated
    """

    priority = START

    name = 'Mean calculation'

    group = 'data'

    children = ['mean']

    data_dependent = True

    requires_replot = True

    def update(self, value):
        if value is None:
            return
        if isstring(value):
            use_std = True
            m = re.search(r'\d+\.?\d*', value)
            if m:
                multiplier = float(m.group())
            else:
                multiplier = 1
        else:
            use_std = False
        for i, (arr, mean) in enumerate(zip(self.iter_raw_data,
                                            self.iter_data)):
            mean = mean.to_dataset()
            if use_std:
                err = multiplier * arr.psy.fldstd()
                mean[value] = err.variable
                data = mean[[arr.name, value]].psy.to_array()
            else:
                err = arr.psy.fldpctl(value)
                names = list(map('pctl{:1.3g}'.format, value))
                mean[names[0]] = err.variable[0]
                mean[names[1]] = err.variable[1]
                data = mean[[arr.name] + names].psy.to_array()
            data.psy.arr_name = arr.psy.arr_name
            data.attrs.update(arr.attrs)
            data.name = arr.name
            self.set_data(data, i)


docstrings.delete_types('LimitBase.possible_types', 'no_None', 'None')


class Hist2DXRange(LimitBase):
    """
    Specify the range of the histogram for the x-dimension

    This formatoption specifies the minimum and maximum of the histogram
    in the x-dimension

    Possible types
    --------------
    %(LimitBase.possible_types.no_None)s

    Notes
    -----
    This formatoption always acts on the coordinate, no matter what the
    value of the :attr:`transpose` formatoption is

    See also
    --------
    yrange"""

    priority = START

    group = 'data'

    name = 'Range of the histogram in x-direction'

    data_dependent = True

    dependencies = ['coord']

    @property
    def array(self):
        # We don't use the :attr:`data` attribute because this fails if the
        # formatoption is shared and the ``coord`` formatoption is not None
        if self.coord.value is not None:
            coord = self.coord.get_alternative_coord(
                self.raw_data, self.index_in_list or 0)[1].values
        else:
            da = self.raw_data
            coord = da.coords[da.dims[0]].values
        ret = coord[~np.isnan(coord)]
        return ret

    def set_limit(self, *args):
        self.range = args


class Hist2DYRange(Hist2DXRange):
    """
    Specify the range of the histogram for the x-dimension

    This formatoption specifies the minimum and maximum of the histogram
    in the x-dimension

    Possible types
    --------------
    %(LimitBase.possible_types.no_None)s

    Notes
    -----
    This formatoption always acts on the DataArray, no matter what the
    value of the :attr:`transpose` formatoption is

    See Also
    --------
    xrange"""

    name = 'Range of the histogram in y-direction'

    data_dependent = True

    @property
    def array(self):
        return np.asarray(self.raw_data)[np.asarray(self.raw_data.notnull())]


class DataPrecision(Formatoption):
    """
    Set the precision of the data

    This formatoption can be used to specify the precision of the data which
    then will be the minimal bin width of the 2D histogram or the bandwith of
    the kernel size (if the :attr:`density` formatoption is set to ``'kde'``)

    Possible types
    --------------
    float
        If 0, this formatoption has no effect at all. Otherwise it is assumed
        to be the precision of the data
    str
        One of ``{'scott' | 'silverman'}``. This uses the statsmodels package
        to estimate the bandwidth of the data that is then used in the
        histogram or KDE plot"""

    priority = START

    dependencies = ['xrange', 'yrange']

    connections = ['density']

    group = 'data'

    name = 'Precision of the visualized data'

    data_dependent = True

    def estimate_bw(self, method, values, data_range=None):
        import statsmodels.nonparametric.api as smnp
        bw_func = getattr(smnp.bandwidths, "bw_" + method)
        if data_range is not None:
            vmin, vmax = sorted(data_range)
            values = values[(values >= vmin) & (values <= vmax)]
        if not len(values):
            raise ValueError("No values found within the given range of "
                             f"{data_range}!")
        return bw_func(values)

    def update(self, value):
        self.bins = [0, 0]
        value = slist(value)
        if len(value) == 1:
            value = [value[0], value[0]]
        self.prec = value
        for i, prec in enumerate(value):
            if prec == 0:
                continue
            da = self.data
            if i == 0:
                data = da.coords[da.dims[0]].values
                data = data[~np.isnan(data)]
                r = self.xrange.range
            else:
                data = da[da.notnull()].values
                r = self.yrange.range
            if isstring(prec):
                prec = self.prec[i] = self.estimate_bw(prec, data, r)
            if r is not None:
                dmin, dmax = r
            else:
                dmax = np.ceil(data.max().values / prec) * prec
                dmin = data.min().values
            self.bins[i] = max(int((dmax - dmin) / prec), 1)


class HistBins(Formatoption):
    """
    Specify the bins of the 2D-Histogramm

    This formatoption can be used to specify, how many bins to use. In other
    words, it determines the grid size of the resulting histogram or kde plot.
    If however you also set the :attr:`precision` formatoption keyword then the
    minimum of precision and the bins specified here will be used.

    Possible types
    --------------
    int
        If 0, only use the bins specified by the :attr:`precision` keyword
        (raises an error if the :attr:`precision` is also set to 0),
        otherwise the number of bins to use
    tuple (x, y) of int
        The bins for x and y explicitly
    """

    priority = START

    dependencies = ['precision']

    group = 'data'

    name = 'Number of bins of the histogram'

    data_dependent = True

    def update(self, value):
        self.bins = [0, 0]
        try:
            value = tuple(value)
        except TypeError:
            value = [value, value]
        for i, (bins, bins_prec) in enumerate(zip(value, self.precision.bins)):
            if bins == 0 and bins_prec == 0:
                raise ValueError('precision and bins must not both be 0!')
            elif bins == 0:
                self.bins[i] = bins_prec
            elif bins_prec == 0:
                self.bins[i] = bins
            else:
                self.bins[i] = min(bins, bins_prec)


class NormedHist2D(Formatoption):
    """
    Specify the normalization of the histogram

    This formatoption can be used to normalize the histogram. It has no effect
    if the :attr:`density` formatoption is set to ``'kde'``

    Possible types
    --------------
    None
        Do not make any normalization
    str
        One of

        counts
            To make the normalization based on the total number counts
        area
            To make the normalization basen on the total number of counts and
            area (the default behaviour of :func:`numpy.histogram2d`)
        x, col, column or columns
            To normalize every column
        y, row or rows
            To normalize every row

    See Also
    --------
    density
    """

    priority = START

    name = 'Specify how to normalize the histogram'

    group = 'data'

    name = 'Normalize the histogram'

    data_dependent = True

    def update(self, value):
        pass  # nothing to do here

    def hist2d(self, da, **kwargs):
        """Make the two dimensional histogram

        Parameters
        ----------
        da: xarray.DataArray
            The data source"""
        if self.value is None or self.value == 'counts':
            normed = False
        else:
            normed = True
        y = da.values
        x = da.coords[da.dims[0]].values
        counts, xedges, yedges = np.histogram2d(
            x, y, normed=normed, **kwargs)
        if self.value == 'counts':  # normalize such that all values sum to one
            counts = counts / counts.sum().astype(float)
        elif self.value in ['x', 'col', 'column', 'columns']:
            # normalize such that every column sums to one
            counts = counts / counts.sum(axis=1, keepdims=True).astype(float)
        elif self.value in ['y', 'row', 'rows']:
            # normalize such that every row sums to one
            counts = counts / counts.sum(axis=1, keepdims=True).astype(float)
        return counts, xedges, yedges


class PointDensity(Formatoption):
    """
    Specify the method to calculate the density

    Possible types
    --------------
    str
        One of the following strings are possible

        hist
            Make a 2D-histogram. The normalization is controlled by the
            :attr:`normed` formatoption
        kde
            Fit a bivariate kernel density estimate to the data. Note that
            this choice requires pythons [statsmodels]_ module to be
            installed

    References
    ----------
    .. [statsmodels] http://statsmodels.sourceforge.net/
    """

    priority = START

    name = 'Type of the density plot'

    dependencies = ['normed', 'bins', 'xrange', 'yrange', 'precision', 'coord']

    group = 'data'

    name = 'Calculation of the point density'

    data_dependent = True

    def update(self, value):
        if value == 'hist':
            self._hist()
        else:
            self._kde()

    def _kde(self):
        if self.coord.value is None:
            raw_da = self.raw_data
        else:
            raw_da = self.coord.replace_coord(0)
        xyranges = [self.xrange.range, self.yrange.range]
        bws = self.precision.prec
        grid = self.bins.bins
        for i, bw in enumerate(bws):
            if bw == 0:
                bws[i] = 'scott'
        coord = raw_da.coords[raw_da.dims[0]]
        xname = coord.name
        yname = raw_da.name
        x, y, z = self._statsmodels_bivariate_kde(
            raw_da.coords[raw_da.dims[0]].values, raw_da.values, bws,
            grid[0], grid[1], xyranges)
        xcent = xr.Variable((xname, ), x, attrs=coord.attrs.copy())
        ycent = xr.Variable((yname, ), y, attrs=raw_da.attrs.copy())
        var = xr.Variable((yname, xname), z,
                          attrs=raw_da.psy.base.attrs.copy())
        ds = xr.Dataset({'counts': var}, {xname: xcent, yname: ycent})
        ds = ds.assign_coords(**self._get_other_coords(raw_da))
        self.decoder = CFDecoder(ds)
        arr = ds.counts
        arr.psy.init_accessor(base=ds, decoder=self.decoder)
        self.data = arr

    def _statsmodels_bivariate_kde(self, x, y, bws, xsize, ysize, xyranges):
        """Compute a bivariate kde using statsmodels.
        This function is mainly motivated through
        seaborn.distributions._statsmodels_bivariate_kde"""
        import statsmodels.nonparametric.api as smnp
        for i, (coord, bw) in enumerate(zip([x, y], bws)):
            if isinstance(bw, six.string_types):
                bw_func = getattr(smnp.bandwidths, "bw_" + bw)
                bws[i] = bw_func(coord)
        kde = smnp.KDEMultivariate([x, y], "cc", bws)
        x_support = np.linspace(xyranges[0][0], xyranges[0][1], xsize)
        y_support = np.linspace(xyranges[1][0], xyranges[1][1], ysize)
        xx, yy = np.meshgrid(x_support, y_support)
        z = kde.pdf([xx.ravel(), yy.ravel()]).reshape(xx.shape)
        return x_support, y_support, z

    def _hist(self):
        if self.coord.value is None:
            raw_da = self.raw_data
        else:
            raw_da = self.coord.replace_coord(0)
        bins = self.bins.bins
        range_ = [self.xrange.range, self.yrange.range]
        z, x, y = self.normed.hist2d(raw_da, bins=bins, range=range_)
        coord = raw_da.coords[raw_da.dims[0]]
        xname = coord.name
        yname = raw_da.name
        # calculate the centers
        xcent = xr.Variable((xname, ), np.c_[[x[:-1], x[1:]]].mean(axis=0),
                            attrs=coord.attrs.copy())
        ycent = xr.Variable((yname, ), np.c_[[y[:-1], y[1:]]].mean(axis=0),
                            attrs=raw_da.attrs.copy())
        xbounds = xr.Variable((xname, 'bnds'), np.c_[[x[:-1], x[1:]]].T)
        ybounds = xr.Variable((yname, 'bnds'), np.c_[[y[:-1], y[1:]]].T)
        xcent.attrs['bounds'] = xname + '_bnds'
        ycent.attrs['bounds'] = yname + '_bnds'
        var = xr.Variable((yname, xname), z.T,
                          attrs=raw_da.psy.base.attrs.copy())
        variables = {'counts': var}
        coords = {xname: xcent, yname: ycent,
                  xname + '_bnds': xbounds, yname + '_bnds': ybounds}
        ds = xr.Dataset(variables, coords)
        ds = ds.assign_coords(**self._get_other_coords(raw_da))
        self.decoder = CFDecoder(ds)
        arr = ds.counts
        arr.psy.init_accessor(base=ds, decoder=self.decoder)
        self.data = arr

    def _get_other_coords(self, raw_da):
        return {key: raw_da.coords[key]
                for key in set(raw_da.coords).difference(raw_da.dims)}


class XYTickPlotter(Plotter):
    """Plotter class for x- and y-ticks and x- and y- ticklabels
    """
    _rcparams_string = ['plotter.simple.']

    transpose = Transpose('transpose')
    xticks = XTicks('xticks')
    xticklabels = XTickLabels('xticklabels')
    yticks = YTicks('yticks')
    yticklabels = YTickLabels('yticklabels')
    ticksize = TickSize('ticksize')
    tickweight = TickWeight('tickweight')
    xtickprops = XTickProps('xtickprops')
    ytickprops = YTickProps('ytickprops')
    xlabel = Xlabel('xlabel')
    ylabel = Ylabel('ylabel')
    labelsize = LabelSize('labelsize')
    labelweight = LabelWeight('labelweight')
    labelprops = LabelProps('labelprops')
    xrotation = XRotation('xrotation')
    yrotation = YRotation('yrotation')


class Base2D(Plotter):
    """Base plotter for 2-dimensional plots
    """

    #: Boolean that is True if coordinates with units in radian should be
    #: converted to degrees
    convert_radian = False

    _rcparams_string = ['plotter.plot2d.']

    cmap = CMap('cmap')
    bounds = Bounds('bounds')
    extend = Extend('extend')
    cbar = Cbar('cbar')
    plot = None
    clabel = CLabel('clabel')
    clabelsize = label_size(clabel, 'Colorbar label', dependencies=['clabel'])
    clabelweight = label_weight(clabel, 'Colorbar label',
                                dependencies=['clabel'])
    cbarspacing = CbarSpacing('cbarspacing')
    clabelprops = label_props(clabel, 'Colorbar label',
                              dependencies=['clabel'])
    cticks = CTicks('cticks')
    cticklabels = CTickLabels('cticklabels')
    cticksize = CTickSize('cticksize')
    ctickweight = CTickWeight('ctickweight')
    ctickprops = CTickProps('ctickprops')
    mask_datagrid = MaskDataGrid('mask_datagrid')
    datagrid = DataGrid('datagrid', index_in_list=0)


class SimplePlotterBase(BasePlotter, XYTickPlotter):
    """Base class for all simple plotters"""

    #: The number variables that one data array visualized by this plotter
    #: might have.
    allowed_vars = 1

    #: The number of allowed dimensions in the for the visualization. If
    #: the array is unstructured, one dimension will be subtracted
    allowed_dims = 1

    transpose = Transpose('transpose')
    axiscolor = AxisColor('axiscolor')
    grid = Grid('grid')
    color = LineColors('color')
    xlim = Xlim('xlim')
    ylim = Ylim('ylim')
    sym_lims = SymmetricLimits('sym_lims')
    legendlabels = LegendLabels('legendlabels')
    legend = Legend('legend')

    @classmethod
    @docstrings.dedent
    def check_data(cls, name, dims, is_unstructured=None):
        """
        A validation method for the data shape

        Parameters
        ----------
        name: str or list of str
            The variable names (at maximum :attr:`allowed_vars` variables per
            array)
        dims: list with length 1 or list of lists with length 1
            The dimension of the arrays. Only 1D-Arrays are allowed
        is_unstructured: bool or list of bool, optional
            True if the corresponding array is unstructured. This keyword is
            ignored

        Returns
        -------
        %(Plotter.check_data.returns)s
        """
        if isinstance(name, six.string_types) or not is_iterable(name):
            name = [name]
            dims = [dims]
        N = len(name)
        if len(dims) != N:
            return [False] * N, [
                'Number of provided names (%i) and dimensions '
                '%(i) are not the same' % (N, len(dims))] * N
        checks = [True] * N
        messages = [''] * N
        for i, (n, d) in enumerate(zip(name, dims)):
            if n != 0 and not n:
                checks[i] = False
                messages[i] = 'At least one variable name is required!'
            elif ((not isstring(n) and is_iterable(n) and
                   len(n) > cls.allowed_vars) and
                  len(d) != (cls.allowed_dims - len(slist(n)))):
                checks[i] = False
                messages[i] = 'Only %i names are allowed per array!' % (
                    cls.allowed_vars)
            elif len(d) != cls.allowed_dims:
                checks[i] = False
                messages[i] = 'Only %i-dimensional arrays are allowed!' % (
                    cls.allowed_dims)
        return checks, messages


class LinePlotter(SimplePlotterBase):
    """Plotter for simple one-dimensional line plots
    """

    _rcparams_string = ['plotter.line.']

    #: The number variables that one data array visualized by this plotter
    #: might have. We allow up to 3 variableswhere the second and third
    #: variable might be the errors (see the :attr:`error` formatoption)
    allowed_vars = 3

    coord = AlternativeXCoord('coord')
    marker = Marker('marker')
    markersize = MarkerSize('markersize')
    linewidth = LineWidth('linewidth')
    plot = LinePlot('plot')
    error = ErrorPlot('error')
    erroralpha = ErrorAlpha('erroralpha')


class ViolinPlotter(SimplePlotterBase):
    """Plotter for making violin plots"""

    _rcparams_string = ['plotter.violin.']

    plot = ViolinPlot('plot')
    xlim = ViolinXlim('xlim')
    ylim = ViolinYlim('ylim')
    xticks = ViolinXTicks('xticks')
    xticklabels = ViolinXTickLabels('xticklabels')
    yticks = ViolinYTicks('yticks')
    yticklabels = ViolinYTickLabels('yticklabels')


class BarPlotter(SimplePlotterBase):
    """Plotter for making bar plots"""

    _rcparams_string = ['plotter.bar.']

    coord = AlternativeXCoord('coord')
    widths = BarWidths('widths')
    alpha = BarAlpha('alpha')
    categorical = CategoricalBars('categorical')
    plot = BarPlot('plot')
    xlim = BarXlim('xlim')
    ylim = BarYlim('ylim')
    xticks = BarXTicks('xticks')
    yticks = BarYTicks('yticks')
    xticklabels = BarXTickLabels('xticklabels')
    yticklabels = BarYTickLabels('yticklabels')
    xlabel = BarXlabel('xlabel')
    ylabel = BarYlabel('ylabel')


class Simple2DBase(Base2D):
    """Base class for :class:`Simple2DPlotter` and
    :class:`psyplot.plotter.maps.FieldPlotter` that defines the data
    management"""

    #: The number of allowed dimensions in the for the visualization. If
    #: the array is unstructured, one dimension will be subtracted
    allowed_dims = 2

    miss_color = MissColor('miss_color', index_in_list=0)

    @classmethod
    @docstrings.dedent
    def check_data(cls, name, dims, is_unstructured):
        """
        A validation method for the data shape

        Parameters
        ----------
        name: str or list of str
            The variable names (one variable per array)
        dims: list with length 1 or list of lists with length 1
            The dimension of the arrays. Only 1D-Arrays are allowed
        is_unstructured: bool or list of bool
            True if the corresponding array is unstructured.

        Returns
        -------
        %(Plotter.check_data.returns)s
        """
        if isinstance(name, six.string_types) or not is_iterable(name):
            name = [name]
            dims = [dims]
            is_unstructured = [is_unstructured]
        N = len(name)
        if N != 1:
            return [False] * N, [
                'Number of provided names (%i) must equal 1!' % (N)] * N
        elif len(dims) != 1:
            return [False], [
                'Number of provided dimension lists (%i) must equal 1!' % (
                    len(dims))]
        elif len(is_unstructured) != 1:
            return [False], [
                ('Number of provided unstructured information (%i) must '
                 'equal 1!') % (len(is_unstructured))]
        if name[0] != 0 and not name[0]:
            return [False], ['At least one variable name must be provided!']
        # unstructured arrays have only 1 dimension
        dimlen = cls.allowed_dims
        if is_unstructured[0]:
            dimlen -= 1
        # Check that the array is two-dimensional
        #
        # if more than one array name is provided, the dimensions should be
        # one les than dimlen to have a 2D array
        if (not isstring(name[0]) and not is_iterable(name[0])
                and len(name[0]) != 1 and len(dims[0]) != dimlen - 1):
            return [False], ['Only one name is allowed per array!']
        # otherwise the number of dimensions must equal dimlen
        if len(dims[0]) != dimlen:
            return [False], [
                'An array with dimension %i is required, not %i' % (
                    dimlen, len(dims[0]))]
        return [True], ['']

    def _set_data(self, *args, **kwargs):
        Plotter._set_data(self, *args, **kwargs)
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data
        ndims = self.allowed_dims
        if data.psy.decoder.is_unstructured(data):
            ndims -= 1
        if data.ndim != ndims:
            raise ValueError(f"Can only plot {self.allowed_dims}-dimensional "
                             "data!")


class Simple2DPlotter(Simple2DBase, SimplePlotterBase):
    """Plotter for visualizing 2-dimensional data.

    See Also
    --------
    psyplot.plotter.maps.FieldPlotter"""

    transpose = Transpose('transpose')
    interp_bounds = InterpolateBounds('interp_bounds')
    plot = SimplePlot2D('plot')
    xticks = XTicks2D('xticks')
    yticks = YTicks2D('yticks')
    xlim = Xlim2D('xlim')
    ylim = Ylim2D('ylim')
    levels = ContourLevels('levels', cbounds='bounds')
    legend = None
    legendlabels = None
    color = None  # no need for this formatoption


class DensityPlotter(Simple2DPlotter):
    """A plotter to visualize the density of points in a 2-dimensional grid"""

    allowed_vars = 1

    allowed_dims = 1

    _rcparams_string = ['plotter.density.']

    coord = AlternativeXCoord('coord')
    xrange = Hist2DXRange('xrange')
    yrange = Hist2DYRange('yrange')
    precision = DataPrecision('precision')
    bins = HistBins('bins')
    normed = NormedHist2D('normed')
    density = PointDensity('density')


class BaseVectorPlotter(Base2D):
    """Base plotter for vector plots
    """

    _rcparams_string = ["plotter.vector."]

    allowed_dims = 3

    arrowsize = ArrowSize('arrowsize')
    arrowstyle = ArrowStyle('arrowstyle')
    density = Density('density')
    color = VectorColor('color')
    linewidth = VectorLineWidth('linewidth')
    cbar = VectorCbar('cbar')
    bounds = VectorBounds('bounds')
    cticks = VectorCTicks('cticks')
    datagrid = VectorDataGrid('datagrid')

    @classmethod
    @docstrings.dedent
    def check_data(cls, name, dims, is_unstructured):
        """
        A validation method for the data shape

        Parameters
        ----------
        name: str or list of str
            The variable names (two variables for the array or one if the dims
            are one greater)
        dims: list with length 1 or list of lists with length 1
            The dimension of the arrays. Only 2D-Arrays are allowed (or 1-D if
            the array is unstructured)
        is_unstructured: bool or list of bool
            True if the corresponding array is unstructured.

        Returns
        -------
        %(Plotter.check_data.returns)s
        """
        if isinstance(name, six.string_types) or not is_iterable(name):
            name = [name]
            dims = [dims]
            is_unstructured = [is_unstructured]
        N = len(name)
        if N != 1:
            return [False] * N, [
                'Number of provided names (%i) must equal 1!' % (N)] * N
        elif len(dims) != 1:
            return [False], [
                'Number of provided dimension lists (%i) must equal 1!' % (
                    len(dims))]
        elif len(is_unstructured) != 1:
            return [False], [
                ('Number of provided unstructured information (%i) must '
                 'equal 1!') % (len(is_unstructured))]
        if name[0] != 0 and not name[0]:
            return [False], ['Two variable names must be provided!']
        # unstructured arrays have only 1 dimension
        dimlen = 1 if is_unstructured[0] else 2
        # Check that the array is two-dimensional
        #
        # if more than one array name is provided, the dimensions should be
        # one les than dimlen to have a 2D array
        if (((isstring(name[0] or not is_iterable(name[0])) or
              len(name[0]) == 1) and len(dims[0]) != dimlen + 1) or
                len(name[0]) > 2):
            return [False], [
                ('Two variables (one for x- and one for y-direction) are '
                 'required!')]
        elif ((isstring(name[0]) or len(name[0]) == 1) and
              len(dims[0]) == dimlen + 1):
            dimlen += 1
        # otherwise the number of dimensions must equal dimlen
        if len(dims[0]) != dimlen:
            return [False], [
                'An array with dimension %i is required, not %i' % (
                    dimlen, len(dims[0]))]
        return [True], ['']

    def _set_data(self, *args, **kwargs):
        Plotter._set_data(self, *args, **kwargs)
        if isinstance(self.data, InteractiveList):
            data = self.data[0]
        else:
            data = self.data
        ndims = self.allowed_dims
        if data.psy.decoder.is_unstructured(data):
            ndims -= 1
        if data.ndim != ndims:
            raise ValueError(f"Can only plot {self.allowed_dims}-dimensional "
                             "data!")


class SimpleVectorPlotter(BaseVectorPlotter, SimplePlotterBase):
    """Plotter for visualizing 2-dimensional vector data

    See Also
    --------
    psyplot.plotter.maps.VectorPlotter"""

    plot = SimpleVectorPlot('plot')
    xticks = XTicks2D('xticks')
    yticks = YTicks2D('yticks')
    xlim = Xlim2D('xlim')
    ylim = Ylim2D('ylim')
    legend = None
    legendlabels = None


class ScalarCombinedBase(Plotter):
    """Base plotter for combined 2-dimensional scalar field with any other
    plotter"""

    _rcparams_string = ["plotter.combinedsimple."]

    # scalar plot formatoptions
    cbar = Cbar('cbar', other_cbars=['vcbar'])
    cticks = CTicks('cticks')
    bounds = Bounds('bounds', index_in_list=0)

    # make sure that masking options only affect the scalar field
    maskless = MaskLess('maskless', index_in_list=0)
    maskleq = MaskLeq('maskleq', index_in_list=0)
    maskgreater = MaskGreater('maskgreater', index_in_list=0)
    maskgeq = MaskGeq('maskgeq', index_in_list=0)
    maskbetween = MaskBetween('maskbetween', index_in_list=0)


class CombinedBase(ScalarCombinedBase):
    """Base plotter for combined 2-dimensional scalar and vector plot"""

    # vector plot formatoptions
    color = VectorColor('color', plot='vplot', cmap='vcmap', bounds='vbounds',
                        index_in_list=1)
    linewidth = VectorLineWidth('linewidth', plot='vplot', index_in_list=1)
    arrowsize = ArrowSize('arrowsize', plot='vplot', index_in_list=1)
    arrowstyle = ArrowStyle('arrowstyle', plot='vplot', index_in_list=1)
    vcbar = VectorCbar('vcbar', plot='vplot', cmap='vcmap', bounds='vbounds',
                       cbarspacing='vcbarspacing', other_cbars=['cbar'],
                       index_in_list=1)
    vcbarspacing = CbarSpacing('vcbarspacing', cbar='vcbar', index_in_list=1)
    vclabel = VCLabel('vclabel', plot='vplot', cbar='vcbar', index_in_list=1)
    vclabelsize = label_size(vclabel, 'Vector colorbar label',
                             dependencies=['vclabel'])
    vclabelweight = label_weight(vclabel, 'Vector colorbar label',
                                 dependencies=['vclabel'])
    vclabelprops = label_props(vclabel, 'Vector colorbar label',
                               dependencies=['vclabel'])
    vcmap = CMap('vcmap', index_in_list=1, bounds='vbounds', cbar='vcbar')
    vbounds = VectorBounds('vbounds', index_in_list=1, cmap='vcmap',
                           cbar='vcbar')
    vcticks = VectorCTicks('vcticks', cbar='vcbar', plot='vplot',
                           bounds='vbounds', index_in_list=1)
    vcticklabels = CTickLabels('vcticklabels', cbar='vcbar', index_in_list=1)
    vcticksize = CTickSize('vcticksize', cbar='vcbar', index_in_list=1,
                           ctickprops='vctickprops')
    vctickweight = CTickWeight('vctickweight', cbar='vcbar', index_in_list=1)
    vctickprops = CTickProps('vctickprops', cbar='vcbar',
                             index_in_list=1)

    @classmethod
    @docstrings.dedent
    def check_data(cls, name, dims, is_unstructured):
        """
        A validation method for the data shape

        Parameters
        ----------
        name: list of str with length 2
            The variable names (one for the first, two for the second array)
        dims: list with length 2 of lists with length 1
            The dimension of the arrays. Only 2D-Arrays are allowed (or 1-D if
            an array is unstructured)
        is_unstructured: bool or list of bool
            True if the corresponding array is unstructured.

        Returns
        -------
        %(Plotter.check_data.returns)s
        """
        if isinstance(name, six.string_types) or not is_iterable(name):
            name = [name]
            dims = [dims]
            is_unstructured = [is_unstructured]
        msg = ('Two arrays are required (one for the scalar and '
               'one for the vector field)')
        if len(name) < 2:
            return [None], [msg]
        elif len(name) > 2:
            return [False], [msg]
        valid1, msg1 = Simple2DBase.check_data(name[:1], dims[0:1],
                                               is_unstructured[:1])
        valid2, msg2 = BaseVectorPlotter.check_data(name[1:], dims[1:],
                                                    is_unstructured[1:])
        return valid1 + valid2, msg1 + msg2

    def _set_data(self, *args, **kwargs):
        super(CombinedBase, self)._set_data(*args, **kwargs)
        # implement 2 simple checks to make sure that we get the right data
        if not isinstance(self.plot_data, InteractiveList):
            raise ValueError(
                "Combined plots must be lists of one scalar field and a"
                "vector field. Got one %s instead" % str(type(
                    self.plot_data)))
        elif len(self.plot_data) < 2:
            raise ValueError(
                "Combined plots must be lists of one scalar field and a"
                "vector field. Got a list of length %i instead!" % len(
                    self.plot_data))


class CombinedSimplePlotter(CombinedBase, Simple2DPlotter,
                            SimpleVectorPlotter):
    """Combined 2D plotter and vector plotter

    See Also
    --------
    psyplot.plotter.maps.CombinedPlotter: for visualizing the data on a map"""
    plot = Plot2D('plot', index_in_list=0)
    vplot = CombinedVectorPlot('vplot', index_in_list=1, cmap='vcmap',
                               bounds='vbounds')
    density = Density('density', plot='vplot', index_in_list=1)


class FldmeanPlotter(LinePlotter):

    _rcparams_string = ["plotter.fldmean."]

    allowed_dims = 3

    err_calc = ErrorCalculator('err_calc')
    mean = MeanCalculator('mean')

    # We reimplement the masking formatoption to make sure, that they are
    # called after the mean calculation
    maskgeq = MaskGeq('maskgeq', additional_children=['err_calc'])
    maskleq = MaskLeq('maskleq', additional_children=['err_calc'])
    maskgreater = MaskGreater('maskgreater', additional_children=['err_calc'])
    maskless = MaskLess('maskless', additional_children=['err_calc'])
    maskbetween = MaskBetween('maskbetween', additional_children=['err_calc'])
    mask = Mask('mask', additional_children=['err_calc'])
    coord = AlternativeXCoordPost('coord', additional_children=['err_calc'])
