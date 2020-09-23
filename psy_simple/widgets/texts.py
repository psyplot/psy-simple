# -*- coding: utf-8 -*-
"""Psyplot GUI widgets for modifying label formatoptions

This module contains PyQt widgets that can be used to modify label
formatoptions (e.g. title, xlabel, titleprops, etc.) in the psyplot GUI."""
from psyplot_gui.compat.qtcompat import (
    QWidget, QComboBox, QHBoxLayout, QPushButton, QLabel, QtGui, with_qt5,
    QToolButton, QIcon, Qt)
from psy_simple.widgets import get_icon, Switch2FmtButton
from warnings import warn
import matplotlib as mpl
import matplotlib.colors as mcol
from psyplot.compat.pycompat import OrderedDict
from psyplot.docstring import docstrings
from psyplot import utils
from functools import partial


if with_qt5:
    from PyQt5.QtWidgets import QSpinBox, QFontDialog, QColorDialog
else:
    from PyQt4.QtGui import QSpinBox, QFontDialog, QColorDialog


if with_qt5:
    weights_mpl2qt = OrderedDict([
        ('ultralight', QtGui.QFont.ExtraLight),
        ('light', QtGui.QFont.Light),
        ('normal', QtGui.QFont.Normal),
        ('regular', QtGui.QFont.Normal),
        ('book', QtGui.QFont.Normal),
        ('medium', QtGui.QFont.Medium),
        ('roman', QtGui.QFont.Medium),
        ('semibold', QtGui.QFont.DemiBold),
        ('demibold', QtGui.QFont.DemiBold),
        ('demi', QtGui.QFont.DemiBold),
        ('bold', QtGui.QFont.Bold),
        ('heavy', QtGui.QFont.Bold),
        ('extra bold', QtGui.QFont.ExtraBold),
        ('black', QtGui.QFont.Black),
        ])
else:
    weights_mpl2qt = OrderedDict([
        ('ultralight', QtGui.QFont.Light),
        ('light', QtGui.QFont.Light),
        ('normal', QtGui.QFont.Normal),
        ('regular', QtGui.QFont.Normal),
        ('book', QtGui.QFont.Normal),
        ('medium', QtGui.QFont.Normal),
        ('roman', QtGui.QFont.Normal),
        ('semibold', QtGui.QFont.DemiBold),
        ('demibold', QtGui.QFont.DemiBold),
        ('demi', QtGui.QFont.DemiBold),
        ('bold', QtGui.QFont.Bold),
        ('heavy', QtGui.QFont.Bold),
        ('extra bold', QtGui.QFont.Black),
        ('black', QtGui.QFont.Black),
        ])


weights_qt2mpl = OrderedDict(
    map(reversed, utils.unique_everseen(weights_mpl2qt.items(),
                                        key=lambda t: t[1])))


def mpl_weight2qt(weight):
    """Convert a weight from matplotlib definition to a Qt weight

    Parameters
    ----------
    weight: int or string
        Either an integer between 1 and 1000 or a string out of
        :attr:`weights_mpl2qt`

    Returns
    -------
    int
        One type of the PyQt5.QtGui.QFont.Weight"""
    try:
        weight = weights_mpl2qt[weight]
    except KeyError:
        try:
            weight = float(weight) / 10
        except (ValueError, TypeError):
            weight = QtGui.QFont.Normal
        else:
            try:
                weight = min(filter(lambda w: w >= weight, weights_qt2mpl),
                             key=lambda w: abs(w - weight))
            except ValueError:
                weight = QtGui.QFont.Normal
    return weight


class DictCombo(QComboBox):
    """A combobox that inserts keys into the formatoption"""

    def __init__(self, attrs, fmt_widget, modulo_style=True):
        QComboBox.__init__(self)
        self.fmt_widget = fmt_widget
        self.addItems(
            [''] +
            [(key + ': ' + str(val))[:40] for key, val in attrs.items()])
        func = self.insert_modulo if modulo_style else self.insert_bracketed
        self.currentTextChanged.connect(func)

    def insert_modulo(self, s):
        self.fmt_widget.insert_obj(
            ('%(' + s.split(':')[0] + ')s') if s else '')

    def insert_bracketed(self, s):
        self.fmt_widget.insert_obj(
                ('{' + s.split(':')[0] + '}') if s else '')


class LabelWidget(QWidget):
    """A widget to modify a text label (title, xlabel, etc.)

    This widget contains one combobox for the ``'labels'`` key in the
    :attr:`psyplot.rcParams` dictionary, and a second combobox for the
    enhanced attributes of the corresponding formatoption object `fmto`.

    Additionally, it provides buttons to switch to the formatoption options
    of the corresponding fontsize, fontweight and fontproperties of this
    label"""

    @docstrings.get_sections(base='LabelWidget')
    def __init__(self, parent, fmto, project, properties=True):
        """
        Parameters
        ----------
        parent: psyplot_gui.fmt_widget.FormatoptionWidget
            The formatoption widget where this widget is inserted
        fmto: psyplot.plotter.Formatoption
            The formatoption that is represented by this widget
        project: psyplot.project.Project
            The current psyplot subproject"""
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()

        # Create a combo box for the rcParams 'labels' key
        label_combo = DictCombo(fmto.rc['labels'], parent, modulo_style=False)
        hbox.addWidget(label_combo)

        # Create a combo for the :attr:`enhanced_attrs`
        attrs = OrderedDict(sorted(utils.join_dicts(
            [getattr(plotter, fmto.key).enhanced_attrs
             for plotter in project.plotters],
            delimiter=', ').items()))
        attr_combo = DictCombo(attrs, parent)
        hbox.addWidget(attr_combo)

        fmtos = [
            # add a button to change to the properties formatoption
            getattr(fmto.plotter, fmto.key + 'props', None),
            getattr(fmto.plotter, fmto.key + 'size', None),
            getattr(fmto.plotter, fmto.key + 'weight', None)
            ]
        fmtos = list(filter(None, fmtos))
        if fmtos and properties:
            hbox.addWidget(Switch2FmtButton(parent, *fmtos))

        self.setLayout(hbox)


docstrings.keep_params('LabelWidget.parameters', 'parent', 'fmto')


class FontWeightWidget(QWidget):
    """A widget for modifying the fontweight of a label"""

    @docstrings.get_sections(base='FontWeightWidget')
    @docstrings.with_indent(8)
    def __init__(self, parent, fmto, artist=None, base=None):
        """
        Parameters
        ----------
        %(LabelWidget.parameters.parent|fmto)s
        artist: matplotlib.text.Text
            The text instance this formatoption is modifying
        base: psyplot.plotter.Formatoption
            The original formatoption of the label the given `fmto` belongs to
        """
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Font weights:'))
        if artist is None:
            weight = 'normal'
        else:
            weight = artist.get_weight()

        self.spin_box = spin_box = QSpinBox(self)
        spin_box.setRange(1, 1000)
        try:
            weight = int(weight)
        except ValueError:
            spin_box.setValue(mpl_weight2qt(weight) * 10)
        else:
            spin_box.setValue(weight)
        spin_box.valueChanged.connect(parent.set_obj)
        hbox.addWidget(spin_box)

        combo = QComboBox()
        combo.addItems(list(weights_mpl2qt))
        if weight in weights_mpl2qt:
            combo.setCurrentText(weight)
        else:
            combo.setCurrentText(weights_qt2mpl[mpl_weight2qt(weight)])
        combo.currentTextChanged.connect(parent.set_obj)
        hbox.addWidget(combo)

        # add a button to change to the properties formatoption
        if base is not None:
            fmtos = [
                base,
                getattr(fmto.plotter, base.key + 'props', None),
                getattr(fmto.plotter, base.key + 'size', None),
                ]
            fmtos = list(filter(None, fmtos))
            hbox.addWidget(Switch2FmtButton(parent, *fmtos))

        self.setLayout(hbox)


class FontSizeWidget(QWidget):
    """A widget for modifying the fontsize of a label"""

    @docstrings.with_indent(8)
    def __init__(self, parent, fmto, artist=None, base=None):
        """
        Parameters
        ----------
        %(FontWeightWidget.parameters)s
        """
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Font sizes:'))

        self.spin_box = spin_box = QSpinBox(self)
        spin_box.setRange(1, int(1e9))
        if artist is not None:
            spin_box.setValue(int(artist.get_size()))

        spin_box.valueChanged.connect(parent.set_obj)
        hbox.addWidget(spin_box)

        combo = QComboBox()
        combo.addItems(['xx-small', 'x-small', 'small', 'medium', 'large',
                        'x-large', 'xx-large'])
        combo.currentTextChanged.connect(parent.set_obj)
        hbox.addWidget(combo)

        # add a button to change to the properties formatoption
        if base is not None:
            fmtos = [
                base,
                getattr(fmto.plotter, base.key + 'props', None),
                getattr(fmto.plotter, base.key + 'weight', None),
                ]
            fmtos = list(filter(None, fmtos))
            hbox.addWidget(Switch2FmtButton(parent, *fmtos))

        self.setLayout(hbox)


class FontPropertiesWidget(QWidget):
    """A widget for modifying the font properties or a label"""

    #: The current QFont of the artist
    current_font = None

    @docstrings.with_indent(8)
    def __init__(self, parent, fmto, artist=None, base=None):
        """
        Parameters
        ----------
        %(FontWeightWidget.parameters)s
        """
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()
        if artist is not None:
            self.current_font = self.artist_to_qfont(artist)
            self.current_color = QtGui.QColor.fromRgbF(
                *mcol.to_rgba(artist.get_color()))
        else:
            self.current_color = QtGui.QColor(Qt.black)
        self.fmto_name = fmto.name or fmto.key

        # choose font button
        button = QPushButton('Choose font')
        button.clicked.connect(partial(self.choose_font, None))
        hbox.addWidget(button)

        # font size spin box
        self.spin_box = spin_box = QSpinBox(self)
        spin_box.setRange(1, int(1e9))
        if artist is not None:
            spin_box.setValue(int(artist.get_size()))
        spin_box.valueChanged.connect(self.modify_size)
        hbox.addWidget(spin_box)

        # font color button
        self.btn_font_color = button = QToolButton(self)
        button.setIcon(QIcon(get_icon('font_color')))
        button.clicked.connect(partial(self.choose_color, None))
        hbox.addWidget(button)

        # bold button
        self.btn_bold = button = QToolButton(self)
        button.setIcon(QIcon(get_icon('bold')))
        button.clicked.connect(self.toggle_bold)
        button.setCheckable(True)
        if artist is not None:
            button.setChecked(self.current_font.weight() > 50)
        hbox.addWidget(button)

        # italic button
        self.btn_italic = button = QToolButton(self)
        button.setIcon(QIcon(get_icon('italic')))
        button.clicked.connect(self.toggle_italic)
        button.setCheckable(True)
        if artist is not None:
            button.setChecked(self.current_font.italic())
        hbox.addWidget(button)

        if base is not None:
            # add a button to change to the base formatoption
            fmtos = [
                base,
                getattr(fmto.plotter, base.key + 'size', None),
                getattr(fmto.plotter, base.key + 'weight', None),
                ]
            fmtos = list(filter(None, fmtos))
            hbox.addWidget(Switch2FmtButton(parent, *fmtos))

        self.setLayout(hbox)

    @staticmethod
    def artist_to_qfont(artist):
        """Convert a :class:`matplotlib.text.Text` artist to a QFont object

        Parameters
        ----------
        artist: matplotlib.text.Text
            The text artist, e.g. an axes title

        Returns
        -------
        PyQt5.QtGui.QFont
            The QFont object"""
        size = int(artist.get_size())
        weight = mpl_weight2qt(artist.get_weight())
        italic = artist.get_style() == 'italic'
        for family in artist.get_family():
            if family in ['sans-serif', 'cursive', 'monospace', 'serif']:
                for name in mpl.rcParams['font.' + family]:
                    font = QtGui.QFont(name, size, weight, italic)
                    if font.exactMatch():
                        break
            else:
                font = QtGui.QFont(family, size, weight, italic)
        return font

    @staticmethod
    def qfont_to_artist_props(font):
        properties = {
            'family': font.family(),
            'size': font.pointSize(),
            'weight': weights_qt2mpl[font.weight()],
            'style': 'italic' if font.italic() else 'normal'}
        if font.underline():
            warn("Underline is ignored! Use LaTeX syntax: $\\underline{text}$!"
                 )
        if font.strikeOut():
            warn("StrikeOut is ignored! Use LaTeX syntax: $\\sout{text}$!")
        return properties

    def modify_size(self, val):
        properties = self.load_properties()
        properties['fontsize' if 'fontsize' in properties else 'size'] = val
        self.current_font.setPointSize(val)
        self.parent().set_obj(properties)

    def toggle_bold(self):
        properties = self.load_properties()
        bold = self.btn_bold.isChecked()
        properties['weight'] = 'bold' if bold else 'normal'
        self.current_font.setBold(bold)
        self.parent().set_obj(properties)

    def toggle_italic(self):
        properties = self.load_properties()
        italic = self.btn_italic.isChecked()
        properties['style'] = 'italic' if italic else 'normal'
        self.current_font.setItalic(italic)
        self.parent().set_obj(properties)

    def load_properties(self):
        return dict(self.parent().get_obj() or {})

    def choose_font(self, font=None):
        """Choose a font for the label through a dialog"""
        fmt_widget = self.parent()
        if font is None:
            if self.current_font:
                font, ok = QFontDialog.getFont(
                    self.current_font, fmt_widget,
                    'Select %s font' % self.fmto_name,
                    QFontDialog.DontUseNativeDialog)
            else:
                font, ok = QFontDialog.getFont(fmt_widget)
            if not ok:
                return
        self.current_font = font
        properties = self.load_properties()
        properties.update(self.qfont_to_artist_props(font))
        fmt_widget.set_obj(properties)
        self.refresh()

    def refresh(self):
        """Refresh the widgets from the current font"""
        font = self.current_font

        # refresh btn_bold
        self.btn_bold.blockSignals(True)
        self.btn_bold.setChecked(font.weight() > 50)
        self.btn_bold.blockSignals(False)

        # refresh btn_italic
        self.btn_italic.blockSignals(True)
        self.btn_italic.setChecked(font.italic())
        self.btn_italic.blockSignals(False)

        # refresh font size
        self.spin_box.blockSignals(True)
        self.spin_box.setValue(font.pointSize())
        self.spin_box.blockSignals(False)

    def choose_color(self, color=None):
        fmt_widget = self.parent()
        if color is None:
            color = QColorDialog.getColor(
                self.current_color, fmt_widget,
                'Select %s color' % self.fmto_name)
        if not color.isValid():
            return
        self.current_color = color
        properties = self.load_properties()
        properties['color'] = color.getRgbF()
        fmt_widget.set_obj(properties)
