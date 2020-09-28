"""psy-simple psyplot plugin

This module defines the rcParams for the psy-simple plugin"""
import six
import re
import matplotlib as mpl
import dataclasses
import numpy as np
import enum
from matplotlib.patches import ArrowStyle
from warnings import warn
from itertools import repeat
from psyplot.config.rcsetup import (
    RcParams, safe_list, SubDict, validate_dict, validate_stringlist,
    validate_stringset)
from matplotlib.rcsetup import (
    validate_bool, validate_color, validate_fontsize,
    ValidateInStrings, validate_int, validate_legend_loc,
    validate_colorlist)
from psy_simple import __version__ as plugin_version
import xarray as xr


def get_versions(requirements=True):
    return {'version': plugin_version}


def patch_prior_1_0(plotter_d, versions):
    """Patch psy_simple plotters for versions smaller than 1.0

    Before psyplot 1.0.0, the plotters in the psy_simple package where part of
    the psyplot.plotter.simple module. This has to be corrected"""
    plotter_d['cls'] = ('psy_simple.plotters', plotter_d['cls'][1])


#: patches to apply when loading a project
patches = {
    ('psyplot.plotter.simple', 'LinRegPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'DensityRegPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'ViolinPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'Simple2DPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'SimpleVectorPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'BarPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'CombinedSimplePlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'DensityPlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'LinePlotter'): patch_prior_1_0,
    ('psyplot.plotter.simple', 'SimplePlotterBase'): patch_prior_1_0,
    }


bound_strings = ['data', 'mid', 'rounded', 'roundedsym', 'minmax', 'sym',
                 'log', 'symlog']

tick_strings = bound_strings + ['hour', 'day', 'week', 'month', 'monthend',
                                'monthbegin', 'year', 'yearend', 'yearbegin']


class strEnum(str, enum.Enum):
    pass


BoundsMethod = strEnum(
    'BoundsMethod', zip(bound_strings, bound_strings), module=__name__)


cticks_strings = bound_strings + ['bounds', 'midbounds']


CTicksMethod = strEnum(
    'CTicksMethod', zip(cticks_strings, cticks_strings), module=__name__)

TicksMethod = strEnum(
    'TicksMethod', zip(tick_strings, tick_strings), module=__name__)


@dataclasses.dataclass
class BoundsType:
    method: BoundsMethod
    N: int = None
    percmin: float = 0
    percmax: float = 100
    vmin: float = None
    vmax: float = None

    def __post_init__(self):
        for field, val in zip(dataclasses.fields(self), self):
            if val is not None or field.name == 'method':
                val = field.type(val)
                setattr(self, field.name, val)

    def __iter__(self):
        return iter(dataclasses.astuple(self))


@dataclasses.dataclass
class CTicksType(BoundsType):
    method: CTicksMethod


@dataclasses.dataclass
class TicksType(BoundsType):
    method: TicksMethod


def try_and_error(*funcs):
    """Apply multiple validation functions

    Parameters
    ----------
    ``*funcs``
        Validation functions to test

    Returns
    -------
    function"""
    def validate(value):
        exc = None
        for func in funcs:
            try:
                return func(value)
            except (ValueError, TypeError) as e:
                exc = e
        raise exc
    return validate


# -----------------------------------------------------------------------------
# ------------------------- validation functions ------------------------------
# -----------------------------------------------------------------------------


def validate_str(s):
    """Validate a string

    Parameters
    ----------
    s: str

    Returns
    -------
    str

    Raises
    ------
    ValueError"""
    if not isinstance(s, six.string_types):
        raise ValueError("Did not found string!")
    return six.text_type(s)


def validate_float(s):
    """convert `s` to float or raise

    Returns
    -------
    s converted to a float: float

    Raises
    ------
    ValueError"""
    try:
        return float(s)
    except (ValueError, TypeError):
        raise ValueError('Could not convert "%s" to float' % str(s))


def validate_text(value):
    """Validate a text formatoption

    Parameters
    ----------
    value: see :attr:`psyplot.plotter.labelplotter.text`

    Raises
    ------
    ValueError"""
    possible_transform = ['axes', 'fig', 'data']
    validate_transform = ValidateInStrings('transform', possible_transform,
                                           True)
    tests = [validate_float, validate_float, validate_str,
             validate_transform, dict]
    if isinstance(value, six.string_types):
        xpos, ypos = rcParams['texts.default_position']
        return [(xpos, ypos, value, 'axes', {'ha': 'right'})]
    elif isinstance(value, tuple):
        value = [value]
    try:
        value = list(value)[:]
    except TypeError:
        raise ValueError("Value must be string or list of tuples!")
    for i, val in enumerate(value):
        try:
            val = tuple(val)
        except TypeError:
            raise ValueError(
                "Text must be an iterable of the form "
                "(x, y, s[, trans, params])!")
        if len(val) < 3:
            raise ValueError(
                "Text tuple must at least be like [x, y, s], with floats x, "
                "y and string s!")
        elif len(val) == 3 or isinstance(val[3], dict):
            val = list(val)
            val.insert(3, 'data')
            if len(val) == 4:
                val += [{}]
            val = tuple(val)
        if len(val) > 5:
            raise ValueError(
                "Text tuple must not be longer then length 5. It can be "
                "like (x, y, s[, trans, params])!")
        value[i] = (validate(x) for validate, x in zip(tests, val))
    return value


def validate_fontweight(value):
    if value is None:
        return None
    elif isinstance(value, six.string_types):
        return six.text_type(value)
    elif mpl.__version__ >= '1.5':
        return validate_float(value)
    raise ValueError("Font weights must be None or a string!")


def validate_limits(value):
    if value is None or isinstance(value, six.string_types):
        return (value, value)
    if not len(value) == 2:
        raise ValueError("Limits must have length 2!")
    return tuple(value)


def validate_none(b):
    """Validate that None is given

    Parameters
    ----------
    b: {None, 'none'}
        None or string (the case is ignored)

    Returns
    -------
    None

    Raises
    ------
    ValueError"""
    if isinstance(b, six.string_types):
        b = b.lower()
    if b is None or b == 'none':
        return None
    else:
        raise ValueError('Could not convert "%s" to None' % b)


validate_bool_maybe_none = try_and_error(validate_none, validate_bool)


def validate_axiscolor(value):
    """Validate a dictionary containing axiscolor definitions

    Parameters
    ----------
    value: dict
        see :attr:`psyplot.plotter.baseplotter.axiscolor`

    Returns
    -------
    dict

    Raises
    ------
    ValueError"""
    validate = try_and_error(validate_none, validate_color)
    possible_keys = {'right', 'left', 'top', 'bottom'}
    try:
        value = dict(value)
        false_keys = set(value) - possible_keys
        if false_keys:
            raise ValueError("Wrong keys (%s)!" % (', '.join(false_keys)))
        for key, val in value.items():
            value[key] = validate(val)
    except:
        value = dict(zip(possible_keys, repeat(validate(value))))
    return value


def validate_dataarray(val):
    if not isinstance(val, xr.DataArray):
        raise ValueError("Require xarray.DataArray, not %r" % type(val))
    return val


def validate_marker(val):
    """Does not really make a validation because markers can be quite of
    different types"""
    if val is None:
        return None
    else:
        return safe_list(val)


def validate_alpha(val):
    '''Validate an alpha value between 0 and 1'''
    val = validate_float(val)
    if val < 0 or val > 1:
        raise ValueError('Alpha values must lay between 0 and 1!')
    return val


def validate_iter(value):
    """Validate that the given value is an iterable"""
    try:
        iter(value)
    except TypeError:
        raise ValueError("%s is not an iterable!" % repr(value))
    else:
        return value


def validate_cbarpos(value):
    """Validate a colorbar position

    Parameters
    ----------
    value: bool or str
        A string can be a combination of 'sh|sv|fl|fr|ft|fb|b|r'

    Returns
    -------
    list
        list of strings with possible colorbar positions

    Raises
    ------
    ValueError"""
    patt = 'sh|sv|fl|fr|ft|fb|b|r'
    if value is True:
        value = {'b'}
    elif not value:
        value = set()
    elif isinstance(value, six.string_types):
        for s in re.finditer('[^%s]+' % patt, value):
            warn("Unknown colorbar position %s!" % s.group(), RuntimeWarning)
        value = set(re.findall(patt, value))
    else:
        value = validate_stringset(value)
        for s in (s for s in value
                  if not re.match(patt, s)):
            warn("Unknown colorbar position %s!" % s)
            value.remove(s)
    return value


def validate_cmap(val):
    """Validate a colormap

    Parameters
    ----------
    val: str or :class:`mpl.colors.Colormap`

    Returns
    -------
    str or :class:`mpl.colors.Colormap`

    Raises
    ------
    ValueError"""
    from matplotlib.colors import Colormap
    try:
        return validate_str(val)
    except ValueError:
        if not isinstance(val, Colormap):
            raise ValueError(
                "Could not find a valid colormap!")
        return val


def validate_cmaps(cmaps):
    """Validate a dictionary of color lists

    Parameters
    ----------
    cmaps: dict
        a mapping from a colormap name to a list of colors

    Raises
    ------
    ValueError
        If one of the values in `cmaps` is not a color list

    Notes
    -----
    For all items (listname, list) in `cmaps`, the reversed list is
    automatically inserted with the ``listname + '_r'`` key."""
    cmaps = {validate_str(key): validate_colorlist(val) for key, val in cmaps}
    for key, val in six.iteritems(cmaps):
        cmaps.setdefault(key + '_r', val[::-1])
    return cmaps


def validate_sym_lims(val):
    validator = try_and_error(validate_none, ValidateInStrings(
        'sym_links', ['min', 'max'], True))
    val = safe_list(val)
    if len(val) != 2:
        val = val + val
    if not len(val) == 2:
        raise ValueError("Need two values for the symmetric limits, not %i" % (
            len(val)))
    return list(map(validator, val))


def validate_legend(value):
    if isinstance(value, dict):
        return value
    try:
        return {'loc': validate_int(value)}
    except (ValueError, TypeError) as e:
        pass
    try:
        return {'loc': validate_legend_loc(value)}
    except (ValueError, TypeError) as e:
        pass
    value = validate_bool(value)
    return {'loc': 'best' if value else False}


def validate_lineplot(value):
    """Validate the value for the LinePlotter.plot formatoption

    Parameters
    ----------
    value: None, str or list with mixture of both
        The value to validate"""
    if value is None:
        return value
    elif isinstance(value, six.string_types):
        return six.text_type(value)
    else:
        value = list(value)
        for i, v in enumerate(value):
            if v is None:
                pass
            elif isinstance(v, six.string_types):
                value[i] = six.text_type(v)
            else:
                raise ValueError('Expected None or string, found %s' % (v, ))
    return value


validate_ticklabels = try_and_error(validate_none, validate_str,
                                    validate_stringlist)

validate_extend = ValidateInStrings('extend',
                                    ['neither', 'both', 'min', 'max'])


class ValidateList(object):
    """Validate a list of the specified `dtype`
    """

    def __init__(self, dtype=None, length=None, listtype=list):
        """
        Parameters
        ----------
        dtype: object
            A datatype (e.g. :class:`float`) that shall be used for the
            conversion
        length: int
            The expected length of the list
        listtype: type
            The type to use for creating the list. Should accept any iterable
        """
        #: data type (e.g. :class:`float`) used for the conversion
        self.dtype = dtype
        self.length = length
        self.listtype = list

    def __call__(self, l):
        """Validate whether `l` is a list with contents of :attr:`dtype`

        Parameters
        ----------
        l: list-like

        Returns
        -------
        list
            list with values of dtype :attr:`dtype`

        Raises
        ------
        ValueError"""
        try:
            if self.dtype is None:
                validated = self.listtype(l)
            else:
                try:
                    len(self.dtype)
                except TypeError:
                    validated = self.listtype(map(self.dtype, l))
                else:
                    validated = self.listtype()
                    for val in l:
                        valid = False
                        for dtype in self.dtype:
                            try:
                                validated.append(dtype(val))
                            except (TypeError, ValueError):
                                pass
                            else:
                                valid = True
                                break
                        if not valid:
                            raise ValueError(
                                f"{val} cannot be converted to any of the "
                                f"given data types: {self.dtype}!")

        except TypeError:
            if self.dtype is None:
                raise ValueError("Could not convert to list!")
            else:
                raise ValueError(
                    "Could not convert to list of type %s!" % str(self.dtype))
        if self.length is not None and len(validated) != self.length:
            raise ValueError('List with length %i is required! Not %i!' % (
                self.length, len(validated)))
        return validated


def validate_err_calc(val):
    """Validation function for the
    :attr:`psy_simple.plotter.FldmeanPlotter.err_calc` formatoption"""
    try:
        val = validate_float(val)
    except (ValueError, TypeError):
        pass
    else:
        if val <= 100 and val >= 0:
            return val
        raise ValueError("Percentiles for the error calculation must lie "
                         "between 0 and 100, not %s" % val)
    try:
        val = ValidateList(float, 2)(val)
    except (ValueError, TypeError):
        pass
    else:
        if all((v <= 100 and v >= 0) for v in val):
            return val
        raise ValueError("Percentiles for the error calculation must lie "
                         "between 0 and 100, not %s" % val)
    try:
        val = validate_str(val)
    except ValueError:
        pass
    else:
        if 'std' not in val:
            raise ValueError(
                'A string for the error calculation must contain std!')
    return val


class DictValValidator(object):
    """A validation class for formatoptions that expect dictionaries as values
    """

    def __init__(self, key, valid, validators, default, ignorecase=False):
        """
        Parameters
        ----------
        key: str
            The name of the formatoption (will be used for error handling)
        valid: list of str
            The valid keys for the dictionary
        validators: func
            The validation function for the values of the dictionary
        default: object
            The default value to use if a key from `valid` is given in the
            provided value
        ignorecase: bool
            Whether the case of the keys should be ignored
        """
        self.key = key
        self.valid = valid
        self.key_validator = ValidateInStrings(key, valid, ignorecase)
        self.default = default
        self.validate = validators

    def __call__(self, value):
        if isinstance(value, dict) and value and all(
                isinstance(key, six.string_types) for key in value):
            failed_key = False
            for key, val in list(six.iteritems(value)):
                try:
                    new_key = self.key_validator(key)
                except ValueError:
                    failed_key = True
                    break
                else:
                    value[new_key] = self.validate(value.pop(key))
            if failed_key:
                if self.default is None:
                    value = self.validate(value)
                    value = dict(zip(self.valid, repeat(value)))
                else:
                    value = {self.default: self.validate(value)}
        elif self.default is None:
            value = self.validate(value)
            value = dict(zip(self.valid, repeat(value)))
        else:
            value = {self.default: self.validate(value)}
        return value


class TicksValidator(ValidateInStrings):

    def __call__(self, val):
        # validate the ticks
        # if None, int or tuple (defining min- and max-range), pass
        if val is None or isinstance(val, int) or (
                isinstance(val, tuple) and len(val) <= 3):
            return val
        # strings must be in the given list
        elif isinstance(val, six.string_types):
            return list(TicksType(val))
        elif isinstance(val, dict):
            return list(TicksType(**val))
        elif len(val) and isinstance(val[0], six.string_types):
            return list(TicksType(*val))
        # otherwise we assume an array
        else:
            return ValidateList()(val)


class BoundsValidator:

    def __init__(self, type, default='rounded', possible_instances=None):
        """
        For parameter description see
        :class:`matplotlib.rcsetup.ValidateInStrings`.

        Other Parameters
        ----------------
        inis: tuple
            Tuple of object types that may pass the check
        default: str
            The default string to use for an integer (Default: 'rounded')"""
        self.type = type
        self.possible_instances = possible_instances
        self.default = default

    def instance_check(self, val):
        if self.possible_instances:
            return isinstance(val, self.possible_instances)
        return False

    def __call__(self, val):
        if val is None or self.instance_check(val):
            return val
        elif isinstance(val, dict):
            return list(self.type(**val))
        elif isinstance(val, int):
            return list(self.type(self.default, val))
        elif isinstance(val, six.string_types):
            return list(self.type(val))
        elif isinstance(val[0], six.string_types):
            return list(self.type(*val))
        # otherwise we assume an array
        else:
            return ValidateList(float)(val)


class LineWidthValidator(ValidateInStrings):

    def __call__(self, val):
        if val is None:
            return val
        elif isinstance(val, six.string_types):
            return [ValidateInStrings.__call__(self, val), 1.0]
        elif np.asarray(val).ndim and isinstance(val[0], six.string_types):
            return [ValidateInStrings.__call__(self, val[0])] + list(val[1:])
        # otherwise we assume an array
        else:
            return np.asarray(val, float)


# -----------------------------------------------------------------------------
# ------------------------------ rcParams -------------------------------------
# -----------------------------------------------------------------------------


#: the :class:`~psyplot.config.rcsetup.RcParams` for the psy-simple plugin
rcParams = RcParams(defaultParams={

    # -------------------------------------------------------------------------
    # ----------------------- Registered plotters -----------------------------
    # -------------------------------------------------------------------------

    'project.plotters': [
        {'simple': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'SimplePlotterBase',
             'plot_func': False,
             'summary': ('All plotters that are visualized by the psy-simple '
                         'package')},
         'lineplot': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'LinePlotter',
             'prefer_list': True,
             'default_slice': None,
             'summary': 'Make a line plot of one-dimensional data'},
         'fldmean': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'FldmeanPlotter',
             'prefer_list': True,
             'default_slice': None,
             'summary': 'Calculate and plot the mean over x- and y-dimensions'
             },
         'density': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'DensityPlotter',
             'prefer_list': False,
             'default_slice': None,
             'summary': 'Make a density plot of point data'},
         'barplot': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'BarPlotter',
             'prefer_list': True,
             'default_slice': None,
             'summary': 'Make a bar plot of one-dimensional data'},
         'violinplot': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'ViolinPlotter',
             'prefer_list': True,
             'default_slice': None,
             'summary': 'Make a violin plot of your data'},
         'plot2d': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'Simple2DPlotter',
             'prefer_list': False,
             'default_slice': 0,
             'default_dims': {'x': slice(None), 'y': slice(None)},
             'summary': 'Make a simple plot of a 2D scalar field'},
         'vector': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'SimpleVectorPlotter',
             'prefer_list': False,
             'default_slice': 0,
             'default_dims': {'x': slice(None), 'y': slice(None)},
             'summary': 'Make a simple plot of a 2D vector field',
             'example_call': "filename, name=[['u_var', 'v_var']], ..."},
         'combined': {
             'module': 'psy_simple.plotters',
             'plotter_name': 'CombinedSimplePlotter',
             'prefer_list': True,
             'default_slice': 0,
             'default_dims': {'x': slice(None), 'y': slice(None)},
             'summary': ('Plot a 2D scalar field with an overlying vector '
                         'field'),
             'example_call': (
                 "filename, name=[['my_variable', ['u_var', 'v_var']]], ...")},
         },
        validate_dict],

    # -------------------------------------------------------------------------
    # --------------------- Default formatoptions -----------------------------
    # -------------------------------------------------------------------------

    'plotter.baseplotter.tight': [False, validate_bool,
                                  'fmt key for tight layout of the plots'],
    'plotter.simple.grid': [
        False, try_and_error(validate_bool_maybe_none, validate_color),
        'fmt key to visualize the grid on simple plots (i.e. without '
        'projection)'],

    # labels
    'plotter.baseplotter.title': [
        '', six.text_type, 'fmt key to control the title of the axes'],
    'plotter.baseplotter.figtitle': [
        '', six.text_type, 'fmt key to control the title of the axes'],
    'plotter.baseplotter.text': [
        [], validate_text, 'fmt key to show text anywhere on the plot'],
    'plotter.simple.ylabel': [
        '', six.text_type, 'fmt key to modify the y-axis label for simple'
        'plot (i.e. plots withouth projection)'],
    'plotter.simple.xlabel': [
        '', six.text_type, 'fmt key to modify the y-axis label for simple'
        'plot (i.e. plots withouth projection)'],
    'plotter.plot2d.clabel': [
        '', six.text_type, 'fmt key to modify the colorbar label for 2D'
        'plots'],

    # text sizes
    'plotter.baseplotter.titlesize': [
        'large', validate_fontsize,
        'fmt key for the fontsize of the axes title'],
    'plotter.baseplotter.figtitlesize': [
        12, validate_fontsize, 'fmt key for the fontsize of the figure title'],
    'plotter.simple.labelsize': [
        'medium', DictValValidator(
            'labelsize', ['x', 'y'], validate_fontsize, None, True),
        'fmt key for the fontsize of the x- and y-l abel of simple plots '
        '(i.e. without projection)'],
    'plotter.simple.ticksize': [
        'medium', DictValValidator(
            'ticksize', ['major', 'minor'], validate_fontsize, 'major', True),
        'fmt key for the fontsize of the ticklabels of x- and y-axis of '
        'simple plots (i.e. without projection)'],
    'plotter.plot2d.cticksize': [
        'medium', validate_fontsize,
        'fmt key for the fontsize of the ticklabels of the colorbar of 2D '
        'plots'],
    'plotter.plot2d.clabelsize': [
        'medium', validate_fontsize,
        'fmt key for the fontsize of the colorbar label'],

    # text weights
    'plotter.baseplotter.titleweight': [
        None, validate_fontweight,
        'fmt key for the fontweight of the axes title'],
    'plotter.baseplotter.figtitleweight': [
        None, validate_fontweight,
        'fmt key for the fontweight of the figure title'],
    'plotter.simple.labelweight': [
        None, DictValValidator(
            'labelweight', ['x', 'y'], validate_fontweight, None, True),
        'fmt key for the fontweight of the x- and y-l abel of simple plots '
        '(i.e. without projection)'],
    'plotter.simple.tickweight': [None, DictValValidator(
        'tickweight', ['major', 'minor'], validate_fontweight, 'major', True),
        'fmt key for the fontweight of the ticklabels of x- and y-axis of '
        'simple plots (i.e. without projection)'],
    'plotter.plot2d.ctickweight': [
        None, validate_fontweight,
        'fmt key for the fontweight of the ticklabels of the colorbar of 2D '
        'plots'],
    'plotter.plot2d.clabelweight': [
        None, validate_fontweight,
        'fmt key for the fontweight of the colorbar label'],

    # text properties
    'plotter.baseplotter.titleprops': [
        {}, validate_dict, 'fmt key for the additional properties of the title'
        ],
    'plotter.baseplotter.figtitleprops': [
        {}, validate_dict,
        'fmt key for the additional properties of the figure title'],
    'plotter.simple.labelprops': [{}, DictValValidator(
        'labelprops', ['x', 'y'], validate_dict, None, True),
        'fmt key for the additional properties of the x- and y-label'],
    'plotter.simple.xtickprops': [
        {'major': {}, 'minor': {}}, DictValValidator(
            'xtickprops', ['major', 'minor'], validate_dict, 'major', True),
        'fmt key for the additional properties of the ticklabels of x-axis'],
    'plotter.simple.ytickprops': [
        {'major': {}, 'minor': {}}, DictValValidator(
            'ytickprops', ['major', 'minor'], validate_dict, 'major', True),
        'fmt key for the additional properties of the ticklabels of y-axis'],
    'plotter.plot2d.clabelprops': [
        {}, validate_dict,
        'fmt key for the additional properties of the colorbar label'],
    'plotter.plot2d.ctickprops': [
        {}, validate_dict,
        'fmt key for the additional properties of the colorbar ticklabels'],

    # mask formatoptions
    'plotter.baseplotter.background': [
        'rc', try_and_error(ValidateInStrings('background', ['rc']),
                            validate_none, validate_color),
        "The background color for the plot"],
    'plotter.baseplotter.mask': [
        None, try_and_error(validate_none, validate_str, validate_dataarray)],
    'plotter.baseplotter.maskleq': [
        None, try_and_error(validate_none, validate_float),
        'fmt key to mask values less or equal than a certain threshold'],
    'plotter.baseplotter.maskless': [
        None, try_and_error(validate_none, validate_float),
        'fmt key to mask values less than a certain threshold'],
    'plotter.baseplotter.maskgreater': [
        None, try_and_error(validate_none, validate_float),
        'fmt key to mask values greater than a certain threshold'],
    'plotter.baseplotter.maskgeq': [
        None, try_and_error(validate_none, validate_float),
        'fmt key to mask values greater than or equal to a certain threshold'],
    'plotter.baseplotter.maskbetween': [
        None, try_and_error(validate_none, ValidateList(float, 2)),
        'fmt key to mask values between a certain range'],

    # density plotter
    'plotter.density.coord': [
        None, try_and_error(validate_none, validate_dataarray,
                            validate_str, validate_stringlist),
        'Alternative x-coordinate to use for DensityPlotter'],
    'plotter.density.xrange': [
        'minmax', validate_limits, 'The histogram limits of the density plot'],
    'plotter.density.yrange': [
        'minmax', validate_limits, 'The histogram limits of the density plot'],
    'plotter.density.precision': [
        0, try_and_error(validate_float, ValidateList((float, str), 2),
                         validate_str),
        'The precision of the data to make sure that the bin width is not '
        'below this value'],
    'plotter.density.bins': [
        10, try_and_error(validate_int, ValidateList(int, 2)),
        'The bins in x- and y-direction of the density plot'],
    'plotter.density.normed': [
        None, try_and_error(validate_none, ValidateInStrings(
            'normed', ['area', 'counts', 'x', 'y', 'col', 'column', 'columns',
                       'row', 'rows'], True)),
        'The normalization of the density histogram'],
    'plotter.density.density': [
        'hist', ValidateInStrings('density', ['hist', 'kde'], True)],

    # axis color
    'plotter.simple.axiscolor': [
        None, validate_axiscolor, 'fmt key to modify the color of the spines'],

    # SimplePlot
    'plotter.line.coord': [
        None, try_and_error(validate_none, validate_dataarray,
                            validate_str, validate_stringlist),
        'Alternative x-coordinate to use for LinePlotter'],
    'plotter.line.plot': [
        '-', validate_lineplot,
        'fmt key to modify the line style'],
    'plotter.line.error': [
        'fill', try_and_error(ValidateInStrings('error', ['fill'], True),
                              validate_none),
        'The visualization type of the errors for line plots'],
    'plotter.line.marker': [
        None, validate_marker, 'The symbol of the marker'],
    'plotter.line.markersize': [
        None, try_and_error(validate_none, validate_float),
        'The size of the marker'],
    'plotter.line.linewidth': [
        None, try_and_error(validate_none, validate_float),
        'The widths of the lines'],
    'plotter.line.erroralpha': [
        0.15, validate_alpha, 'The alpha value of the error range'],
    'plotter.bar.coord': [
        None, try_and_error(validate_none, validate_dataarray,
                            validate_str, validate_stringlist),
        'Alternative x-coordinate to use for BarPlotter'],
    'plotter.bar.widths': [
        'equal', try_and_error(
            validate_float, ValidateInStrings(
                'widths', ['equal', 'data'], True)),
        'fmt key to change between equal and data given width of the bars'],
    'plotter.bar.categorical': [
        None, validate_bool_maybe_none,
        'fmt key to change between categorical and non-categorical plotting'],
    'plotter.bar.alpha': [
        1.0, validate_float,
        'fmt key to control the transparency for the bar plots'],
    'plotter.bar.plot': [
        'bar', validate_lineplot,
        'fmt key to modify whether bar plots shall be stacked or not'],
    'plotter.violin.plot': [
        True, validate_bool_maybe_none,
        'fmt key to modify whether violin plots shall be drawn'],
    'plotter.simple.transpose': [
        False, validate_bool, 'fmt key to switch x- and y-axis'],
    'plotter.simple.color': [
        None, try_and_error(validate_none, validate_cmap, validate_iter),
        'fmt key to modify the color cycle simple plots'],
    'plotter.simple.ylim': [
        'rounded', validate_limits, 'fmt key to specify the y-axis limits'],
    'plotter.simple.xlim': [
        'rounded', validate_limits, 'fmt key to specify the x-axis limits'],
    'plotter.simple.sym_lims': [
        None, validate_sym_lims,
        'fmt key to make symmetric x- and y-axis limits'],
    'plotter.simple.xticks': [
        {'major': None, 'minor': None}, DictValValidator(
            'xticks', ['major', 'minor'], TicksValidator(
                'xticks', tick_strings, True), 'major', True),
        'fmt key to modify the x-axis ticks'],
    'plotter.simple.yticks': [
        {'major': None, 'minor': None}, DictValValidator(
            'yticks', ['major', 'minor'], TicksValidator(
                'yticks', tick_strings, True), 'major', True),
        'fmt key to modify the y-axis ticks'],
    'plotter.simple.xticklabels': [
        None, DictValValidator('xticklabels', ['major', 'minor'],
                               validate_ticklabels, 'major', True),
        'fmt key to modify the x-axis ticklabels'],
    'plotter.simple.yticklabels': [
        None, DictValValidator('yticklabels', ['major', 'minor'],
                               validate_ticklabels, 'major', True),
        'fmt key to modify the y-axis ticklabels'],
    'plotter.simple.xrotation': [
        0, validate_float,
        'fmt key to modify the rotation of the x-axis ticklabels'],
    'plotter.simple.yrotation': [
        0, validate_float,
        'fmt key to modify the rotation of the x-axis ticklabels'],
    'plotter.simple.legendlabels': [
        '%(arr_name)s', try_and_error(
            validate_str, ValidateList(six.text_type)),
        'fmt key to modify the legend labels'],
    'plotter.simple.legend': [
        True, validate_legend, 'fmt key to draw a legend'],

    # FldmeanPlotter
    'plotter.fldmean.mean': [
        'mean', try_and_error(
            ValidateInStrings('mean', ['mean', 'median'], True),
            validate_float),
        "The calculation result, either the 'mean', 'median' or a percentile"],
    'plotter.fldmean.err_calc': [
        'std', validate_err_calc,
        "The error calculation method, either the 'std' or a minimum "
        "and maximum percentile"],

    # Plot2D
    'plotter.plot2d.interp_bounds': [
        None, validate_bool_maybe_none,
        'Switch to interpolate the bounds for 2D plots'],
    'plotter.plot2d.plot': [
        'mesh', try_and_error(validate_none, ValidateInStrings(
            '2d plot', ['mesh', 'contourf', 'contour', 'poly',
                        'tri', 'tricontourf', 'tricontour'], True)),
        'fmt key to specify the plot type of 2D scalar plots'],
    'plotter.plot2d.plot.min_circle_ratio': [
        0.05, validate_float,
        'fmt key to specify the min_circle_ratio that is used to mask very '
        ' flat triangles in a triangular plot'],
    'plotter.plot2d.cbar': [
        ['b'], validate_cbarpos,
        'fmt key to specify the position of the colorbar'],
    'plotter.plot2d.cbarspacing': [
        'uniform', validate_str,
        'fmt key to specify the spacing of the colorbar'],
    'plotter.plot2d.miss_color': [
        None, try_and_error(validate_none, validate_color),
        'fmt key to specify the color of missing values'],
    'plotter.plot2d.cmap': [
        'white_blue_red', validate_cmap, 'fmt key to specify the colormap'],
    'plotter.plot2d.cticks': [
        None, try_and_error(validate_none, BoundsValidator(
            CTicksType, default='bounds')),
        'fmt key to specify the ticks of the colorbar'],
    'plotter.plot2d.cticklabels': [
        None, validate_ticklabels,
        'fmt key to specify the ticklabels of the colorbar'],
    'plotter.plot2d.extend': [
        'neither', validate_extend,
        'fmt key to specify the style of the colorbar on minimum and maximum'],
    'plotter.plot2d.bounds': [
        'rounded', BoundsValidator(BoundsType, 'bounds', mpl.colors.Normalize),
        'fmt key to specify bounds and norm of the colorbar'],
    'plotter.plot2d.levels': [
        None, BoundsValidator(BoundsType),
        'fmt key to specify the levels for a contour plot'],
    # TODO: Implement opacity
    # 'plotter.plot2d.opacity': [None, try_and_error(validate_none,
    #                                                validate_opacity)],
    'plotter.plot2d.datagrid': [
        None, try_and_error(validate_none, validate_dict, validate_str),
        'fmt key to plot the lines of the data grid'],
    'plotter.plot2d.mask_datagrid': [
        True, validate_bool,
        'fmt key to mask cells with NaN when plotting the data grid'],

    # VectorPlot
    'plotter.vector.plot': [
        'quiver', try_and_error(validate_none, ValidateInStrings(
            '2d plot', ['quiver', 'stream'], True)),
        'fmt key for the plot type of vector plots'],
    'plotter.vector.arrowsize': [
        None, try_and_error(validate_none, validate_float),
        'fmt key for the size of the arrows on vector plots'],
    'plotter.vector.arrowstyle': [
        '-|>', ValidateInStrings('arrowstyle', ArrowStyle._style_list),
        'fmt key for the style of the arrows on stream plots'],
    'plotter.vector.density': [
        1.0, try_and_error(validate_float, ValidateList(float, 2)),
        'fmt key for the density of arrows on a vector plot'],
    'plotter.vector.linewidth': [
        None, LineWidthValidator('linewidth', ['absolute', 'u', 'v'], True),
        'fmt key for the linewidths of the arrows'],
    'plotter.vector.color': [
        'k', try_and_error(validate_float, validate_color, ValidateInStrings(
            'color', ['absolute', 'u', 'v'], True)),
        'fmt key for the colors of the arrows'],

    # default texts
    'texts.labels': [{'tinfo': '%H:%M',
                      'dtinfo': '%B %d, %Y. %H:%M',
                      'dinfo': '%B %d, %Y',
                      'desc': '%(long_name)s [%(units)s]',
                      'sdesc': '%(name)s [%(units)s]'}, validate_dict,
                     'labels that shall be replaced in TextBase formatoptions',
                     ' (e.g. the title formatoption) when inserted within '
                     'curly braces ({}))'],
    'texts.default_position': [(1., 1.), ValidateList(float, 2),
                               'default position for the text fmt key'],
    'texts.delimiter': [', ', validate_str,
                        'default delimiter to separate netCDF meta attributes '
                        'when displayed on the plot'],

    # -------------------------------------------------------------------------
    # ---------------------------- Miscallaneous ------------------------------
    # -------------------------------------------------------------------------

    # color lists for user-defined colormaps (see for example
    # psy_simple.colors._cmapnames)
    'colors.cmaps': [
        {}, validate_cmaps,
        'User defined color lists that shall be accessible through the '
        ':meth:`psyplot.plotter.colors.get_cmap` function'],

    'widgets.colors.cmaps': [
        ["viridis", "Reds", "Blues", "Greens", "binary", "RdBu", "coolwarm",
         "red_white_blue", "winter", "jet", "white_blue_red", "gist_ncar",
         "gist_earth", "Paired", "gnuplot", "gnuplot2"],
        validate_stringlist,
        'Colormaps that should be listed in the context menu of the cmap '
        'button'],

    'ticks.which': ['major', ValidateInStrings(
        'ticks.which', ['major', 'minor'], True),
        'default tick that is used when using a x- or y-tick formatoption'],
    })


# add combinedplotter strings for vectorplot
_subd = SubDict(rcParams.defaultParams, ['plotter.vector.', 'plotter.plot2d.'])
for _key in ['plot', 'cbar', 'cmap', 'bounds', 'cticksize', 'cbarspacing',
             'ctickweight', 'ctickprops', 'clabel', 'cticks', 'cticklabels',
             'clabelsize', 'clabelprops', 'clabelweight']:
    rcParams.defaultParams['plotter.combinedsimple.v%s' % _key] = _subd[_key]
rcParams.defaultParams['plotter.combinedsimple.plot'] = rcParams.defaultParams[
    'plotter.plot2d.plot']
del _key, _subd


rcParams.update_from_defaultParams()
