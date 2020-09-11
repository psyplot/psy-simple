import six
from abc import abstractmethod
from collections import defaultdict
from itertools import chain
import numpy as np
import inspect
import pandas as pd
import matplotlib.pyplot as plt
from psyplot.docstring import docstrings, safe_modulo, dedent
from psyplot.data import InteractiveList, open_dataset
from psyplot.compat.pycompat import filter
from psyplot.plotter import (
    Plotter, Formatoption, rcParams, START)

docstrings.params['replace_note'] = inspect.cleandoc("""
    You can insert any meta key from the :attr:`xarray.DataArray.attrs` via a
    string like ``'%%(key)s'``. Furthermore there are some special cases:

    - Strings like ``'%%Y'``, ``'%%b'``, etc. will be replaced using the
      :meth:`datetime.datetime.strftime` method as long as the data has a time
      coordinate and this can be converted to a :class:`~datetime.datetime`
      object.
    - ``'%%(x)s'``, ``'%%(y)s'``, ``'%%(z)s'``, ``'%%(t)s'`` will be replaced
      by the value of the x-, y-, z- or time coordinate (as long as this
      coordinate is one-dimensional in the data)
    - any attribute of one of the above coordinates is inserted via
      ``axis + key`` (e.g. the name of the x-coordinate can be inserted via
      ``'%%(xname)s'``).
    - Labels defined in the :class:`psyplot.rcParams` ``'texts.labels'`` key
      are also replaced when enclosed by '{}'. The standard labels are

      - %s""" % '\n      - '.join(
    '%s: ``%s``' % tuple(item) for item in six.iteritems(
        rcParams['texts.labels'])))

docstrings.params['colors'] = inspect.cleandoc("""
    The following color abbreviations are supported:

    ==========  ========
    character   color
    ==========  ========
    'b'         blue
    'g'         green
    'r'         red
    'c'         cyan
    'm'         magenta
    'y'         yellow
    'k'         black
    'w'         white
    ==========  ========

    In addition, you can specify colors in many weird and wonderful ways,
    including full names (``'green'``), hex strings (``'#008000'``), RGB or
    RGBA tuples (``(0,1,0,1)``) or grayscale intensities as a string
    (``'0.8'``).""")

docstrings.params['fontsizes'] = inspect.cleandoc("""
    float
        The absolute font size in points (e.g., 12)
    string
        Strings might be 'xx-small', 'x-small', 'small', 'medium', 'large',
        'x-large', 'xx-large'.""")


class TextBase(object):
    """Abstract base class for formatoptions that provides a replace method"""

    delimiter = None

    group = 'labels'

    @property
    def enhanced_attrs(self):
        """The enhanced attributes of the array"""
        arr = self.data
        return self.get_enhanced_attrs(arr)

    @property
    def rc(self):
        """:class:`~psyplot.config.rcsetup.SubDict` of rcParams 'texts' key"""
        try:
            return self._rc
        except AttributeError:
            return rcParams.find_and_replace(base_str=['texts.'])

    data_dependent = True

    @docstrings.dedent
    def replace(self, s, data, attrs=None):
        """
        Replace the attributes of the plotter data in a string

        %(replace_note)s

        Parameters
        ----------
        s: str
            String where the replacements shall be made
        data: InteractiveBase
            Data object from which to use the coordinates and insert the
            coordinate and attribute informations
        attrs: dict
            Meta attributes that shall be used for replacements. If None, it
            will be gained from `data.attrs`

        Returns
        -------
        str
            `s` with inserted informations"""
        # insert labels
        s = s.format(**self.rc['labels'])
        # replace attributes
        attrs = attrs or data.attrs
        if hasattr(getattr(data, 'psy', None), 'arr_name'):
            attrs = attrs.copy()
            attrs['arr_name'] = data.psy.arr_name
        s = safe_modulo(s, attrs)
        # replace datetime.datetime like time informations
        if isinstance(data, InteractiveList):
            data = data[0]
        tname = self.any_decoder.get_tname(
            next(self.plotter.iter_base_variables), data.coords)
        if tname is not None and tname in data.coords:
            time = data.coords[tname]
            if not time.values.ndim:
                try:  # assume a valid datetime.datetime instance
                    s = pd.to_datetime(str(time.values[()])).strftime(s)
                except ValueError:
                    pass
        if six.PY2:
            return s.decode('utf-8')
        return s

    def get_fig_data_attrs(self, delimiter=None):
        """Join the data attributes with other plotters in the project

        This method joins the attributes of the
        :class:`~psyplot.InteractiveBase` instances in the project that
        draw on the same figure as this instance does.

        Parameters
        ----------
        delimiter: str
            Specifies the delimiter with what the attributes are joined. If
            None, the :attr:`delimiter` attribute of this instance or (if the
            latter is also None), the rcParams['texts.delimiter'] item is used.

        Returns
        -------
        dict
            A dictionary with all the meta attributes joined by the specified
            `delimiter`"""
        if self.project is not None:
            delimiter = next(filter(lambda d: d is not None, [
                delimiter, self.delimiter, self.rc['delimiter']]))
            figs = self.project.figs
            fig = self.ax.get_figure()
            if self.plotter._initialized and fig in figs:
                ret = figs[fig].joined_attrs(delimiter=delimiter,
                                             plot_data=True)
            else:
                ret = self.get_enhanced_attrs(self.plotter.plot_data)
                self.logger.debug(
                    'Can not get the figure attributes because plot has not '
                    'yet been initialized!')
            return ret
        else:
            return self.get_enhanced_attrs(self.plotter.plot_data)

    def get_enhanced_attrs(self, *args, **kwargs):
        replot = kwargs.pop('replot', False)
        if hasattr(self, '_enhanced_attrs') and not (
                self.plotter.replot or replot):
            return self._enhanced_attrs
        self._enhanced_attrs = self.plotter.get_enhanced_attrs(*args, **kwargs)
        return self._enhanced_attrs

    def get_fmt_widget(self, parent, project):
        """Create a combobox with the attributes"""
        from psy_simple.widgets.texts import LabelWidget
        return LabelWidget(parent, self, project)


docstrings.params['fontweights'] = inspect.cleandoc("""
    float
        a float between 0 and 1000
    string
        Possible strings are one of 'ultralight', 'light', 'normal',
        'regular', 'book', 'medium', 'roman', 'semibold', 'demibold',
        'demi', 'bold', 'heavy', 'extra bold', 'black'.""")


@docstrings.get_sections(base='label_weight')
@dedent
def label_weight(base, label_name=None, children=[], parents=[],
                 dependencies=[]):
    """
    Function that returns a Formatoption class for modifying the fontweight

    This function returns a :class:`~psyplot.plotter.Formatoption` instance
    that modifies the weight of the given `base` formatoption

    Parameters
    ----------
    base: Formatoption
        The base formatoption instance that is used in the
        :class:`psyplot.Plotter` subclass to create the label. The instance
        must have a ``texts`` attribute which stores all the
        :class:`matplotlib.text.Text` instances.
    label_name: str
        The name of the label to use in the documentation. If None,
        it will be ``key``, where ``key`` is the
        :attr:`psyplot.plotter.Formatoption.key`` attribute of `base`
    children: list of str
        The childrens of the resulting formatoption class (besides the `base`
        formatoption which is included anyway)
    parents: list of str
        The parents of the resulting formatoption class (besides the `base`
        the properties formatoption from `base` (see :func:`label_props`))
    dependencies: list of str
        The dependencies of the formatoption

    Returns
    -------
    Formatoption
        The formatoption instance that modifies the fontweight of `base`

    See Also
    --------
    label_size, label_props, Figtitle, Title"""
    label_name = label_name or base.key
    cl_children = children
    cl_parents = parents
    cl_dependencies = dependencies

    class LabelWeight(Formatoption):
        __doc__ = """
        Set the fontweight of the %s

        Possible types
        --------------
        %%(fontweights)s

        See Also
        --------
        %s, %s, %s""" % (label_name, base.key, base.key + 'size',
                         base.key + 'props')
        children = [base.key] + \
            cl_children
        parent = [base.key + 'props'] + cl_parents
        dependencies = cl_dependencies

        group = 'labels'

        name = 'Font weight of ' + (base.name or base.key)

        def update(self, value):
            for text in getattr(self, base.key).texts:
                text.set_weight(value)

        def get_fmt_widget(self, parent, project):
            """Get a widget with the different font weights"""
            from psy_simple.widgets.texts import FontWeightWidget
            return FontWeightWidget(
                parent, self, next(iter(getattr(self, base.key).texts), None),
                base)

    return LabelWeight(base.key + 'weight')


@docstrings.dedent
def label_size(base, label_name=None, children=[], parents=[],
               dependencies=[]):
    """
    Function that returns a Formatoption class for modifying the fontsite

    This function returns a :class:`~psyplot.plotter.Formatoption` instance
    that modifies the size of the given `base` formatoption

    Parameters
    ----------
    %(label_weight.parameters)s

    Returns
    -------
    Formatoption
        The formatoption instance that modifies the fontsize of `base`

    See Also
    --------
    label_weight, label_props, Figtitle, Title"""
    label_name = label_name or base.key
    cl_children = children
    cl_parents = parents
    cl_dependencies = dependencies

    class LabelSize(Formatoption):
        __doc__ = """
        Set the size of the %s

        Possible types
        --------------
        %%(fontsizes)s

        See Also
        --------
        %s, %s, %s""" % (label_name, base.key, base.key + 'weight',
                         base.key + 'props')
        children = [base.key] + cl_children
        parent = [base.key + 'props'] + cl_parents
        dependencies = cl_dependencies

        group = 'labels'

        name = 'Font size of ' + (base.name or base.key)

        def update(self, value):
            for text in getattr(self, base.key).texts:
                text.set_size(value)

        def get_fmt_widget(self, parent, project):
            """Get a widget with the different font weights"""
            from psy_simple.widgets.texts import FontSizeWidget
            return FontSizeWidget(
                parent, self, next(iter(getattr(self, base.key).texts), None),
                base)

    return LabelSize(base.key + 'size')


docstrings.keep_params('label_weight.parameters', 'base', 'label_name')


@docstrings.dedent
def label_props(base, label_name=None, children=[], parents=[],
                dependencies=[]):
    """
    Function that returns a Formatoption class for modifying the fontsite

    This function returns a :class:`~psyplot.plotter.Formatoption` instance
    that modifies the size of the given `base` formatoption

    Parameters
    ----------
    %(label_weight.parameters)s
    children: list of str
        The childrens of the resulting formatoption class (besides the `base`
        formatoption, the ``base.key + 'size'`` and ``base.key + 'weight'``
        keys, which are included anyway (see :func:`label_size`,
        :func:`label_weight`))
    parents: list of str
        The parents of the resulting formatoption class

    Returns
    -------
    Formatoption
        The formatoption instance that modifies the fontsize of `base`

    See Also
    --------
    label_weight, label_props, Figtitle, Title"""
    label_name = label_name or base.key
    cl_children = children
    cl_parents = parents
    cl_dependencies = dependencies

    class LabelProps(Formatoption):
        __doc__ = """
        Properties of the %s

        Specify the font properties of the figure title manually.

        Possible types
        --------------
        dict
            Items may be any valid text property

        See Also
        --------
        %s, %s, %s""" % (label_name, base.key, base.key + 'size',
                         base.key + 'weight')
        children = cl_children
        parents = cl_parents
        dependencies = [base.key, base.key + 'size', base.key + 'weight'] + \
            cl_dependencies

        group = 'labels'

        name = 'Font properties of ' + (base.name or base.key)

        def __init__(self, *args, **kwargs):
            super(LabelProps, self).__init__(*args, **kwargs)
            self.default_props = {}
            self._todefault = False

        def set_value(self, value, validate=True, todefault=False):
            self._todefault = todefault
            super(LabelProps, self).set_value(value, validate, todefault)

        def update(self, fontprops):
            fontprops = fontprops.copy()
            # store default font properties
            try:
                text = next(iter(getattr(self, base.key).texts))
            except StopIteration:
                return
            # TODO: This handling of the default management is not really
            # satisfying because you run into troubles when using alternate
            # property names (e.g. if you use 'ha' and 'horizontalalignment'
            # at the same time)
            if not self._todefault:
                for key in fontprops:
                    if key == 'bbox':
                        default = dict(facecolor='none', edgecolor='none')
                    else:
                        default = getattr(text, 'get_' + key)()
                    self.default_props.setdefault(key, default)
            else:
                fontprops = self.default_props.copy()
                self.default_props.clear()
            if 'size' not in fontprops and 'fontsize' not in fontprops:
                fontprops['size'] = getattr(self, base.key + 'size').value
            if 'weight' not in fontprops and 'fontweight' not in fontprops:
                fontprops['weight'] = getattr(self, base.key + 'weight').value
            for text in getattr(self, base.key).texts:
                text.update(fontprops)
            self._todefault = False

        def get_fmt_widget(self, parent, project):
            """Get a widget with the different font weights"""
            from psy_simple.widgets.texts import FontPropertiesWidget
            return FontPropertiesWidget(
                parent, self, next(iter(getattr(self, base.key).texts), None),
                base)

    return LabelProps(base.key + 'props')


class Title(TextBase, Formatoption):
    """
    Show the title

    Set the title of the plot.
    %(replace_note)s

    Possible types
    --------------
    str
        The title for the :func:`~matplotlib.pyplot.title` function.

    Notes
    -----
    This is the title of this specific subplot! For the title of the whole
    figure, see the :attr:`figtitle` formatoption.

    See Also
    --------
    figtitle, titlesize, titleweight, titleprops"""

    name = 'Axes title'

    def initialize_plot(self, value):
        arr = self.data
        self.texts = [self.ax.set_title(
            self.replace(value, arr, attrs=self.enhanced_attrs))]

    def update(self, value):
        arr = self.data
        self.texts[0].set_text(self.replace(
            value, arr, attrs=self.enhanced_attrs))


class Figtitle(TextBase, Formatoption):
    """
    Plot a figure title

    Set the title of the figure.
    %(replace_note)s

    Possible types
    --------------
    str
        The title for the :func:`~matplotlib.pyplot.suptitle` function

    Notes
    -----
    - If the plotter is part of a :class:`psyplot.project.Project` and multiple
      plotters of this project are on the same figure, the replacement
      attributes (see above) are joined by a delimiter. If the
      :attr:`delimiter` attribute of this :class:`Figtitle` instance is not
      None, it will be used. Otherwise the rcParams['texts.delimiter'] item is
      used.
    - This is the title of the whole figure! For the title of this specific
      subplot, see the :attr:`title` formatoption.

    See Also
    --------
    title, figtitlesize, figtitleweight, figtitleprops"""

    name = 'Figure title'

    @property
    def enhanced_attrs(self):
        return self.get_fig_data_attrs()

    def initialize_plot(self, s):
        if s:
            self.texts = [self.ax.get_figure().suptitle(
                self.replace(s, self.plotter.data, self.enhanced_attrs))]
            self.clear_other_texts()
        else:
            self.texts = [self.ax.get_figure().suptitle('')]

    def update(self, s):
        if s:
            self.texts[0].set_text(self.replace(s, self.plotter.data,
                                                self.enhanced_attrs))
            self.clear_other_texts()
        else:
            self.texts[0].set_text('')

    def clear_other_texts(self, remove=False):
        """Make sure that no other text is a the same position as this one

        This method clears all text instances in the figure that are at the
        same position as the :attr:`_text` attribute

        Parameters
        ----------
        remove: bool
            If True, the Text instances are permanently deleted from the
            figure, otherwise there text is simply set to ''"""
        fig = self.ax.get_figure()
        # don't do anything if our figtitle is the only Text instance
        if len(fig.texts) == 1:
            return
        for i, text in enumerate(fig.texts):
            if text == self._text:
                continue
            if text.get_position() == self._text.get_position():
                if not remove:
                    text.set_text('')
                else:
                    del fig[i]


class Text(TextBase, Formatoption):
    """
    Add text anywhere on the plot

    This formatoption draws a text on the specified position on the figure.
    %(replace_note)s

    Possible types
    --------------
    str
        If string s: this will be used as (1., 1., s, {'ha': 'right'}) (i.e. a
        string in the upper right corner of the axes).
    tuple or list of tuples (x,y,s[,coord.-system][,options]])
        Each tuple defines a text instance on the plot. 0<=x, y<=1 are the
        coordinates. The coord.-system can be either the data coordinates
        (default, ``'data'``) or the axes coordinates (``'axes'``) or the
        figure coordinates ('fig'). The string s finally is the text. options
        may be a dictionary to specify format the appearence (e.g. ``'color'``,
        ``'fontweight'``, ``'fontsize'``, etc., see
        :class:`matplotlib.text.Text` for possible keys).
        To remove one single text from the plot, set (x,y,''[, coord.-system])
        for the text at position (x,y)
    empty list
        remove all texts from the plot

    See Also
    --------
    title, figtitle"""

    name = 'Arbitrary text on the plot'

    @property
    def transform(self):
        """Dictionary containing the relevant transformations"""
        ax = self.ax
        return {'axes': ax.transAxes,
                'fig': ax.get_figure().transFigure,
                'data': ax.transData}

    def __init__(self, *args, **kwargs):
        Formatoption.__init__(self, *args, **kwargs)
        #: texts that shall be removed when updating
        self._texts_to_remove = set()
        #: :class:`matplotlib.texts.Text` instances on the figure
        self._texts = defaultdict(set)

    def _remove_texttuple(self, pos):
        """Remove a texttuple from the value in the plotter

        Parameters
        ----------
        pos: tuple (x, y, cs)
            x and y are the x- and y-positions and cs the coordinate system"""
        for i, (old_x, old_y, s, old_cs, d) in enumerate(self.value):
            if (old_x, old_y, old_cs) == pos:
                self.value.pop(i)
                return
        raise ValueError("{0} not found!".format(pos))

    def _update_texttuple(self, x, y, s, cs, d):
        """Update the text tuple at `x` and `y` with the given `s` and `d`"""
        pos = (x, y, cs)
        for i, (old_x, old_y, old_s, old_cs, old_d) in enumerate(self.value):
            if (old_x, old_y, old_cs) == pos:
                self.value[i] = (old_x, old_y, s, old_cs, d)
                return
        raise ValueError("No text tuple found at {0}!".format(pos))

    def set_value(self, value, validate=True, todefault=False):
        value = self.validate(value) if validate else value
        # mark all texts for removing if value is empty
        if not value or todefault:
            with self.plotter.no_validation:
                self.plotter[self.key] = []
            for cs, texts in self._texts.items():
                for t in texts:
                    pos = t.get_position()
                    self._texts_to_remove.add((pos[0], pos[1], cs))

        # loop through texttuples to see whether one changed or has to be
        # removed. x: x-coord, y: y-coord, s: string, cs: coord.-system,
        # d: text params dictionary
        for x, y, s, cs, d in value:
            if not s:
                try:
                    self._remove_texttuple((x, y, cs))
                    self._texts_to_remove.add((x, y, cs))
                except ValueError:
                    pass
            else:
                try:
                    self._update_texttuple(x, y, s, cs, d)
                except ValueError:
                    self.value.append((x, y, s, cs, d))

    def update(self, value, texts_to_remove=None):
        # remove texts
        for (x, y, cs) in texts_to_remove or self._texts_to_remove:
            for t in self._texts[cs]:
                if (x, y) == t.get_position():
                    self._texts[cs].remove(t)
                    t.remove()
                    break
        if self.plotter.replot:
            value = self.value + value
        # now update the old texts or create new ones
        for x, y, s, cs, d in value:
            if cs == 'fig':
                s = self.replace(
                    s, self.plotter.data, self.get_fig_data_attrs(
                        d.pop('delimiter', None)))
            else:
                s = self.replace(s, self.plotter.data, self.enhanced_attrs)
            found = False
            for t in self._texts[cs]:
                if (x, y) == t.get_position():
                    t.set_text(s)
                    t.update(d.copy())
                    found = True
                    break
            if not found:
                self._texts[cs].add(self.ax.text(
                    x, y, s, d.copy(), transform=self.transform[cs]))

    def share(self, fmto, **kwargs):
        """Share the settings of this formatoption with other data objects

        Parameters
        ----------
        fmto: Formatoption
            The :class:`Formatoption` instance to share the attributes with
        ``**kwargs``
            Any other keyword argument that shall be passed to the update
            method of `fmto`

        Notes
        -----
        The Text formatoption sets the 'texts_to_remove' keyword to the
        :attr:`_texts_to_remove` attribute of this instance (if not already
        specified in ``**kwargs``"""
        kwargs.setdefault('texts_to_remove', self._texts_to_remove)
        super(Text, self).share(fmto, **kwargs)

    def diff(self, value):
        my_value = self.value
        return (not len(value) and len(my_value)) or any(
            val not in my_value for val in value)

    def finish_update(self):
        """Clears the :attr:`_texts_to_remove` set"""
        self._texts_to_remove.clear()

    def remove(self):
        for t in chain.from_iterable(six.itervalues(self._texts)):
            t.remove()
        self._texts.clear()


class Tight(Formatoption):
    """
    Automatically adjust the plots.

    If set to True, the plots are automatically adjusted to fit to the figure
    limitations via the :func:`matplotlib.pyplot.tight_layout()` function.

    Possible types
    --------------
    bool
        True for automatic adjustment

    Warnings
    --------
    There is no update method to undo what happend after this formatoption is
    set to True!"""

    group = 'axes'

    name = 'Tight layout'

    def update(self, value):
        if value:
            plt.sca(self.ax)
            plt.tight_layout()


class BackgroundColor(Formatoption):
    """The background color for the matplotlib axes.

    Possible types
    --------------
    'rc'
        to use matplotlibs rc params
    None
        to use a transparent color
    color
        Any possible matplotlib color
    """

    group = 'axes'

    name = 'Background color of the plot'

    def update(self, value):
        if value == 'rc':
            self.ax.patch.set_facecolor(plt.rcParams['axes.facecolor'])
            self.ax.set_facecolor(plt.rcParams['axes.facecolor'])
        elif value is None:
            self.ax.patch.set_facecolor('none')
            self.ax.set_facecolor('none')
        else:
            self.ax.patch.set_facecolor(value)
            self.ax.set_facecolor(value)

    def get_fmt_widget(self, parent, project):
        from psy_simple.widgets.colors import BackGroundColorWidget
        return BackGroundColorWidget(parent, self, project)


class ValueMaskBase(Formatoption):
    """Base class for masking formatoptions"""
    priority = START

    group = 'masking'

    data_dependent = True

    @abstractmethod
    def mask_func(self):
        """The masking function that is called"""
        return

    def update(self, value):
        if value is None:
            pass
        else:
            for i, data in enumerate(self.iter_data):
                self.set_data(self._mask_data(data, value), i)

    def _mask_data(self, data, value):
        data = data.copy(data=np.copy(data.values))
        data.values[~np.isnan(data.values)] = self.mask_func(
            data.values[~np.isnan(data.values)], value)
        return data


class MaskLess(ValueMaskBase):
    """
    Mask data points smaller than a number

    Possible types
    --------------
    float
        The floating number to mask below

    See Also
    --------
    maskleq, maskgreater, maskgeq, maskbetween
    """

    name = 'Mask less'

    def mask_func(self, data, value):
        data[data < value] = np.nan
        return data


class MaskLeq(ValueMaskBase):
    """
    Mask data points smaller than or equal to a number

    Possible types
    --------------
    float
        The floating number to mask below

    See Also
    --------
    maskless, maskgreater, maskgeq, maskbetween
    """

    name = 'Mask lesser than or equal'

    def mask_func(self, data, value):
        data[data <= value] = np.nan
        return data


class MaskGreater(ValueMaskBase):
    """
    Mask data points greater than a number

    Possible types
    --------------
    float
        The floating number to mask above

    See Also
    --------
    maskless, maskleq, maskgeq, maskbetween
    """

    name = 'Mask greater'

    def mask_func(self, data, value):
        data[data > value] = np.nan
        return data


class MaskGeq(ValueMaskBase):
    """
    Mask data points greater than or equal to a number

    Possible types
    --------------
    float
        The floating number to mask above

    See Also
    --------
    maskless, maskleq, maskgreater, maskbetween
    """

    name = 'Mask greater than or equal'

    def mask_func(self, data, value):
        data[data >= value] = np.nan
        return data


class MaskBetween(ValueMaskBase):
    """
    Mask data points between two numbers

    Possible types
    --------------
    float
        The floating number to mask above

    See Also
    --------
    maskless, maskleq, maskgreater, maskgeq
    """

    name = 'Mask between two values'

    def mask_func(self, data, value):
        data[np.all([data >= value[0], data <= value[1]], axis=0)] = np.nan
        return data


class Mask(Formatoption):
    """Mask the data where a certain condition is True

    This formatoption can be used to mask the plotting data based on another
    array. This array can be the name of a variable in the base dataset,
    or it can be a numeric array. Note that the data needs to be on exactly
    the same coordinates as the data shown here

    Possible types
    --------------
    None
        Apply no mask
    str
        The name of a variable in the base dataset to use.

        - dimensions that are in the given `mask` but not in the visualized
          base variable will be aggregated using :func:`numpy.any`
        - if the given `mask` misses dimensions that are in the visualized
          data (i.e. the data of this plotter), we broadcast the `mask` to
          match the shape of the data
        - dimensions that are in `mask` and the base variable, but not in the
          visualized data will be matched against each other
    str
        The path to a netCDF file that shall be loaded
    xr.DataArray or np.ndarray
        An array that can be broadcasted to the shape of the data
    """

    priority = START

    group = 'masking'

    name = "Apply a mask"

    def update(self, value):
        if value is None:
            return
        for i, data in enumerate(self.iter_data):
            mask = self.load_mask(data, value)
            new_data = data.where(mask.astype(bool))
            new_data.psy.base = data.psy.base
            new_data.psy.idims = data.psy.idims
            self.set_data(new_data, i)

    def diff(self, value):
        try:
            return bool(self.value != value)
        except ValueError:
            if hasattr(value, 'shape') and hasattr(self.value, 'shape'):
                return ((value.shape != self.value.shape) |
                        (value != self.value).any())
            else:
                return True

    def load_mask(self, data, value):
        if isinstance(value, str) and value in data.psy.base:
            mask = data.psy.base[value]
            if not set(mask.dims).intersection(data.dims):
                raise ValueError("No intersection between dimensions of mask "
                                 f"{value}: {mask.dims}, and the data: "
                                 f"{data.dims}")
        elif isinstance(value, str):
            try:
                mask = open_dataset(value)
            except Exception:
                raise ValueError(
                    f"{value} is not in the base dataset of "
                    f"{data.psy.arr_name} and could not be loaded with "
                    f"psy.open_dataset({repr(value)})")
            else:
                available_vars = [
                    v for v in mask
                    if set(mask[v].dims).intersection(data.dims)]
                if not available_vars:
                    raise ValueError(f"No variable in {value} has an overlap "
                                     f"with the data dimensions {data.dims}")
                else:
                    mask = mask[available_vars[0]]
        else:
            mask = value
        base_var = next(data.psy.iter_base_variables)

        # aggregate mask over dimensions that are not in the base variable
        dims2agg = set(mask.dims).difference(set(base_var.dims))
        if dims2agg:
            mask = mask.any(list(dims2agg))

        # select idims of mask
        idims = {d: sl for d, sl in data.psy.idims.items()
                 if d in mask.dims and d not in data.dims}
        if idims:
            mask = mask.isel(**idims)

        return mask


class TitlesPlotter(Plotter):
    """Plotter class for labels"""
    _rcparams_string = ['plotter.baseplotter.']
    title = Title('title')
    titlesize = label_size(title)
    titleweight = label_weight(title)
    titleprops = label_props(title)
    figtitle = Figtitle('figtitle')
    figtitlesize = label_size(figtitle, 'figure title')
    figtitleweight = label_weight(figtitle, 'figure title')
    figtitleprops = label_props(figtitle, 'figure title')
    text = Text('text')


class BasePlotter(TitlesPlotter):
    """Base class with formatoptions for plotting on an matplotlib axes"""
    _rcparams_string = ['plotter.baseplotter.']

    tight = Tight('tight')
    background = BackgroundColor('background')
    maskless = MaskLess('maskless')
    maskleq = MaskLeq('maskleq')
    maskgreater = MaskGreater('maskgreater')
    maskgeq = MaskGeq('maskgeq')
    maskbetween = MaskBetween('maskbetween')
    mask = Mask('mask')
