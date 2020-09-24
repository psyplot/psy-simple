"""Module for color specific widgets

This module corresponds to the :mod:`psy_simple.colors` module as a version for
the usage in the psyplot GUI."""
import six
import os.path as osp
from itertools import chain
from functools import partial
import contextlib
from psyplot.data import safe_list, rcParams
from psy_simple.widgets import Switch2FmtButton, get_icon
import psy_simple.colors as psc
from psy_simple.plugin import BoundsType, CTicksType
from psyplot.docstring import docstrings
import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.colors as mcol
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt


mpl_version = tuple(map(int, mpl.__version__.split('.')[:2]))


docstrings.delete_params('show_colormaps.parameters', 'show', 'use_qt')


class ColormapModel(QtCore.QAbstractTableModel):
    """A model for displaying colormaps"""

    @docstrings.get_sections(base='ColormapModel')
    @docstrings.with_indent(8)
    def __init__(self, names=[], N=10, *args, **kwargs):
        """
        Parameters
        ----------
        %(show_colormaps.parameters.no_show|use_qt)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the QAbstractTableModel
        """
        super(ColormapModel, self).__init__(*args, **kwargs)
        names = psc._get_cmaps(names)
        self.set_colors(N, names)

    def set_colors(self, N=None, names=None):
        self.names = names = names or self.names
        self.N = N = N or self.N

        colors = np.zeros((len(names), N, 4))
        a = np.linspace(0, 1, N)
        for i, cmap in enumerate(map(lambda name: psc.get_cmap(name, N),
                                     names)):
            colors[i, :, :] = cmap(a)

        self.color_da = xr.DataArray(
            colors, coords={'cmap': list(map(str, names))},
            dims=('cmap', 'color', 'rgba'))

    def rowCount(self, index=QtCore.QModelIndex()):
        return self.color_da.shape[0]

    def columnCount(self, index=QtCore.QModelIndex()):
        return self.color_da.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        """Cell content"""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return ' '
        if role == Qt.BackgroundColorRole:
            color = self.color_da[index.row(), index.column()].values
            return QtGui.QColor.fromRgbF(*color)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set header data"""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return six.text_type(self.color_da.cmap[section].values)
        return super(ColormapModel, self).headerData(section, orientation,
                                                     role)

    def reset(self):
        self.beginResetModel()
        self.endResetModel()


class ColormapTable(QtWidgets.QTableView):
    """A table for displaying colormaps"""

    @docstrings.with_indent(8)
    def __init__(self, names=[], N=10, editable=True, *args, **kwargs):
        """
        Parameters
        ----------
        %(ColormapModel.parameters)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the QtWidgets.QTableView
        """
        super(ColormapTable, self).__init__(*args, **kwargs)
        self.setModel(ColormapModel(names, N))
        if editable:
            self.doubleClicked.connect(self.change_color)
        self.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

    def setModel(self, model):
        super(ColormapTable, self).setModel(model)
        self.orig_color_da = model.color_da.copy(True)

    def change_color(self, index):
        model = self.model()
        current = model.data(index, Qt.BackgroundColorRole)
        if current is None:
            return
        color = QtWidgets.QColorDialog.getColor(current, parent=self)
        if not color.isValid():
            return
        model.color_da[index.row(), index.column(), :] = list(color.getRgbF())
        indices = self.selectedIndexes()
        model.reset()
        self.selectRow(indices[0].row())

    def rowCount(self):
        return self.model().rowCount()

    def columnCount(self):
        return self.model().columnCount()

    @property
    def chosen_colormap(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        model = self.model()
        name = six.text_type(self.orig_color_da.cmap[row].values)
        colors = model.color_da[row].values
        orig_colors = self.orig_color_da[row].values
        if np.allclose(colors, orig_colors):
            return model.names[row]
        return mcol.LinearSegmentedColormap.from_list(
            name, colors, N=self.columnCount())


class ColormapDialog(QtWidgets.QDialog):
    """A widget for selecting a colormap"""

    @docstrings.with_indent(8)
    def __init__(self, names=[], N=10, editable=True, *args, **kwargs):
        """
        Parameters
        ----------
        %(ColormapModel.parameters)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the ColormapDialog
        """
        super(QtWidgets.QDialog, self).__init__(*args, **kwargs)
        vbox = QtWidgets.QVBoxLayout()
        self.table = ColormapTable(names=names, N=N, editable=editable)
        if editable:
            vbox.addWidget(QtWidgets.QLabel("Double-click a color to edit"))
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        col_width = self.table.columnWidth(0)
        header_width = self.table.verticalHeader().width()
        row_height = self.table.rowHeight(0)
        available = QtWidgets.QDesktopWidget().availableGeometry()
        height = int(min(row_height * (self.table.rowCount() + 1),
                         2. * available.height() / 3.))
        width = int(min(header_width + col_width * N + 0.5 * col_width,
                        2. * available.width() / 3.))
        self.resize(QtCore.QSize(width, height))

    @classmethod
    @docstrings.with_indent(8)
    def get_colormap(cls, names=[], N=10, *args, **kwargs):
        """Open a :class:`ColormapDialog` and get a colormap

        Parameters
        ----------
        %(ColormapModel.parameters)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the ColormapDialog

        Returns
        -------
        str or matplotlib.colors.Colormap
            Either the name of a standard colormap available via
            :func:`psy_simple.colors.get_cmap` or a colormap
        """
        names = safe_list(names)
        obj = cls(names, N, *args, **kwargs)
        vbox = obj.layout()
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=obj)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(buttons)
        buttons.accepted.connect(obj.accept)
        buttons.rejected.connect(obj.reject)

        obj.table.selectionModel().selectionChanged.connect(
            lambda indices: buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
                bool(indices)))
        accepted = obj.exec_()
        if accepted:
            return obj.table.chosen_colormap

    docstrings.delete_params('show_colormaps.parameters', 'use_qt')

    @classmethod
    @docstrings.with_indent(8)
    def show_colormap(cls, names=[], N=10, show=True, *args, **kwargs):
        """Show a colormap dialog

        Parameters
        ----------
        %(show_colormaps.parameters.no_use_qt)s"""
        names = safe_list(names)
        obj = cls(names, N, *args, **kwargs)
        vbox = obj.layout()
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, parent=obj)
        buttons.rejected.connect(obj.close)
        vbox.addWidget(buttons)
        if show:
            obj.show()
        return obj


def create_cmap_thumb(cmap, output=None):
    from matplotlib.figure import Figure
    from matplotlib.cm import ScalarMappable

    fig = Figure(figsize=(4., 0.2))
    cax = fig.add_axes([0, 0, 1, 1])
    _cmap = psc.get_cmap(cmap)
    mappable = ScalarMappable(cmap=_cmap)
    mappable.set_array([])
    fig.colorbar(mappable, cmap=_cmap, cax=cax, orientation='horizontal')
    if output:
        fig.savefig(output, dpi=72)
    return fig


class HighlightWidget(QtWidgets.QWidget):

    def set_highlighted(self, b):
        self.setBackgroundRole(QtGui.QPalette.Highlight if b else
                               QtGui.QPalette.Window)
        self.setAutoFillBackground(b)

    def enterEvent(self, event):
        self.set_highlighted(True)

    def leaveEvent(self, event):
        self.set_highlighted(False)


class CmapButton(QtWidgets.QToolButton):
    """A button with a dropdown menu to select colormaps"""

    # a signal that is triggered if the colormap has been changed
    colormap_changed = QtCore.pyqtSignal([str], [mcol.Colormap])

    def __init__(self, cmaps=None, current=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if cmaps is None:
            cmaps = list(rcParams['widgets.colors.cmaps'])

        self.cmaps = cmaps

        self.setText(current or cmaps[0])
        self.cmap_menu = self.setup_cmap_menu()
        self.setMenu(self.cmap_menu)

        max_width = max(map(self.fontMetrics().width, cmaps)) * 2
        self.setMinimumWidth(max_width)
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)

    def setup_cmap_menu(self):
        menu = QtWidgets.QMenu()
        for cmap in self.cmaps:
            icon = get_icon(osp.join('cmaps', cmap))
            if osp.exists(icon):
                action = QtWidgets.QWidgetAction(menu)
                w = HighlightWidget()
                hbox = QtWidgets.QVBoxLayout()
                label = QtWidgets.QLabel()
                label.setPixmap(QtGui.QPixmap(icon))
                hbox.addWidget(label)
                cmap_label = QtWidgets.QLabel(cmap)
                hbox.addWidget(cmap_label)
                w.setLayout(hbox)
                action.setDefaultWidget(w)
                action.triggered.connect(partial(self.set_cmap, cmap))
                menu.addAction(action)
            else:
                menu.addAction(cmap, partial(self.set_cmap, cmap))
        return menu

    def set_cmap(self, cmap):
        if isinstance(cmap, str):
            self.setText(str(cmap))
            self.colormap_changed[str].emit(cmap)
        else:
            self.setText('Custom')
            self.colormap_changed[mcol.Colormap].emit(cmap)

    def open_cmap_dialog(self, N=10):
        cmap = ColormapDialog.get_colormap(N=N)
        if cmap is not None:
            self.set_cmap(cmap)


class ColorLabel(QtWidgets.QTableWidget):
    """A QTableWidget with one cell and no headers to just display a color"""

    #: a signal that is emitted with an rgba color if the chosen color changes
    color_changed = QtCore.pyqtSignal(QtGui.QColor)

    #: QtCore.QColor. The current color that is displayed
    color = None

    def __init__(self, color='w', *args, **kwargs):
        """The color to display

        Parameters
        ----------
        color: object
            Either a QtGui.QColor object or a color that can be converted
            to RGBA using the :func:`matplotlib.colors.to_rgba` function"""
        super(ColorLabel, self).__init__(*args, **kwargs)
        self.setColumnCount(1)
        self.setRowCount(1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setHidden(True)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        self.verticalHeader().setHidden(True)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QTableWidget.NoSelection)
        self.itemClicked.connect(self.select_color)
        self.color_item = QtWidgets.QTableWidgetItem()
        self.setItem(0, 0, self.color_item)
        self.adjust_height()
        self.set_color(color)
        self.orig_color = self.color

        self.setMaximumWidth(80)

    def select_color(self, *args):
        """Select a color using :meth:`PyQt5.QtWidgets.QColorDialog.getColor`
        """
        color = QtWidgets.QColorDialog.getColor(
            self.color_item.background().color())
        if color.isValid():
            self.set_color(color)

    def set_color(self, color):
        """Set the color of the label

        This method sets the given `color` as background color for the cell
        and emits the :attr:`color_changed` signal

        Parameters
        ----------
        color: object
            Either a QtGui.QColor object or a color that can be converted
            to RGBA using the :func:`matplotlib.colors.to_rgba` function"""
        color = self._set_color(color)
        self.color_changed.emit(color)

    def setEnabled(self, b):
        if not b:
            orig_color = self.color
            self._set_color('0.75')
            self.color = orig_color
        else:
            self._set_color(self.color)
        super().setEnabled(b)

    def _set_color(self, color):
        if not isinstance(color, QtGui.QColor):
            color = QtGui.QColor(
                *map(int, np.round(np.array(mcol.to_rgba(color)) * 255)))
        self.color_item.setBackground(color)
        self.color = color
        return color

    def adjust_height(self):
        """Adjust the height to match the row height"""
        h = self.rowHeight(0) * self.rowCount()
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

    def sizeHint(self):
        """Reimplemented to use the rowHeight as height"""
        s = super(ColorLabel, self).sizeHint()
        return QtCore.QSize(s.width(), self.rowHeight(0) * self.rowCount())


class BackGroundColorWidget(QtWidgets.QWidget):
    """The widget to select the axes background color"""

    def __init__(self, parent, fmto, project):
        super().__init__()
        ax = fmto.ax
        self.cb_enable = QtWidgets.QCheckBox('transparent')
        self.color_label = ColorLabel(ax.patch.get_facecolor())
        self.editor = parent

        self.cb_enable.setChecked(fmto.value is None)

        self.toggle_color_button()

        self.color_label.color_changed.connect(self.set_color)

        self.cb_enable.stateChanged.connect(self.toggle_color_button)
        self.cb_enable.stateChanged.connect(self.set_transparent)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Select color:'))
        layout.addWidget(self.color_label)
        layout.addWidget(self.cb_enable)
        layout.addStretch(0)
        self.setLayout(layout)

    def set_transparent(self):
        if self.cb_enable.isChecked():
            self.editor.set_obj(None)
        else:
            self.set_color(self.color_label.color)

    def toggle_color_button(self):
        self.color_label.setEnabled(not self.cb_enable.isChecked())

    def set_color(self, color):
        if isinstance(color, QtGui.QColor):
            color = list(color.getRgbF())
        self.editor.set_obj(color)


class CMapFmtWidget(QtWidgets.QWidget):
    """The widget for modifying the :class:`psy_simple.plotters.CMap` fmt"""

    def __init__(self, parent, fmto, project, properties=True):
        QtWidgets.QWidget.__init__(self, parent)
        hbox = QtWidgets.QHBoxLayout()

        self.editor = parent

        # add a select colormap button
        self.btn_choose = button = CmapButton()
        button.colormap_changed.connect(self.set_obj)
        button.colormap_changed[mcol.Colormap].connect(self.set_obj)
        self.btn_choose.cmap_menu.addSeparator()
        self.btn_choose.cmap_menu.addAction(
            'More...', partial(self.choose_cmap, None))

        if isinstance(fmto.value, str):
            self.btn_choose.setText(fmto.value)
        else:
            self.btn_choose.setText("Custom")

        hbox.addWidget(button)

        # add a show colormap button
        self.btn_show = button = QtWidgets.QPushButton('Edit...')
        button.clicked.connect(self.edit_cmap)
        hbox.addWidget(button)

        # add a checkbox to invert the colormap
        self.cb_invert = QtWidgets.QCheckBox("Inverted")
        self.cb_invert.setEnabled(isinstance(fmto.value, str))
        if isinstance(fmto.value, str):
            self.cb_invert.setChecked(fmto.value.endswith('_r'))
        self.cb_invert.stateChanged.connect(self.invert_cmap)
        hbox.addWidget(self.cb_invert)

        hbox.addStretch(0)

        if properties:
            hbox.addWidget(Switch2FmtButton(parent, fmto.bounds, fmto.cbar))

        self.setLayout(hbox)

    def set_obj(self, obj):
        self.editor.set_obj(obj)
        self.invert_cmap()

    def invert_cmap(self):
        try:
            value = self.editor.get_obj()
        except Exception:
            return
        if isinstance(value, str):
            self.cb_invert.setEnabled(True)
            if self.cb_invert.isChecked() and not value.endswith('_r'):
                self.editor.set_obj(value + '_r')
            elif value.endswith('_r'):
                self.editor.set_obj(value[:-2])
        else:
            self.refresh_cb_invert(value)

    def refresh_cb_invert(self, obj):
        try:
            self.cb_invert.blockSignals(True)
            if isinstance(obj, str):
                self.cb_invert.setEnabled(True)
                self.cb_invert.setChecked(obj.endswith('_r'))
            else:
                self.cb_invert.setEnabled(False)
                self.cb_invert.setChecked(False)
        finally:
            self.cb_invert.blockSignals(False)

    def choose_cmap(self, cmap=None):
        if cmap is None:
            editor = self.editor
            N = getattr(editor.fmto.bounds.norm, 'Ncmap', 10)
            self.btn_choose.open_cmap_dialog(N)
        else:
            self.set_obj(cmap)

    def edit_cmap(self):
        editor = self.editor
        cmap = editor.get_obj()
        if cmap is not None:
            cmap = ColormapDialog.get_colormap(
                cmap, N=getattr(editor.fmto.bounds.norm, 'Ncmap', 10),
                parent=self)
            if cmap is not None:
                editor.set_obj(cmap)


class DataTicksCalculatorFmtWidget(QtWidgets.QWidget):
    """Fmt widget for :class:`psy_simple.plotters.DataTicksCalculator`

    This widget contains a combo box with the different options from the
    :attr:`psy_simple.plotters.DataTicksCalculator.calc_funcs`, a spin box
    for the number of increments and two text widgets for minimum and maximum
    percentile"""

    def __init__(self, parent, method=None, methods_type=BoundsType):
        self.methods_type = methods_type
        QtWidgets.QWidget.__init__(self, parent)

        self.method = method

        hbox = QtWidgets.QHBoxLayout()

        self.sb_N = QtWidgets.QSpinBox()
        self.sb_N.setSpecialValueText('auto')
        self.sb_N.setMinimum(0)
        hbox.addWidget(self.sb_N)

        self.txt_min_pctl = QtWidgets.QLineEdit()
        self.txt_min_pctl.setValidator(QtGui.QDoubleValidator(0., 100., 10))


        hbox.addWidget(QtWidgets.QLabel('Min.:'))

        self.combo_min = QtWidgets.QComboBox()
        self.combo_min.addItems(['absolute', 'percentile'])
        hbox.addWidget(self.combo_min)

        hbox.addWidget(self.txt_min_pctl)

        self.txt_max_pctl = QtWidgets.QLineEdit()
        self.txt_max_pctl.setValidator(QtGui.QDoubleValidator(0., 100., 10))
        hbox.addWidget(QtWidgets.QLabel('Max.:'))

        self.combo_max = QtWidgets.QComboBox()
        self.combo_max.addItems(['absolute', 'percentile'])
        hbox.addWidget(self.combo_max)

        hbox.addWidget(self.txt_max_pctl)

        self.sb_N.valueChanged.connect(self.set_obj)
        self.combo_min.currentIndexChanged.connect(self.set_obj)
        self.combo_max.currentIndexChanged.connect(self.set_obj)
        self.txt_min_pctl.textChanged.connect(self.set_obj)
        self.txt_max_pctl.textChanged.connect(self.set_obj)

        self.setLayout(hbox)

    def set_obj(self):
        obj = {
            'method': self.method,
            'N': self.sb_N.value() or None,
            }
        if self.txt_min_pctl.text().strip():
            key = 'vmin' if self.combo_min.currentText() == 'absolute' else \
                'percmin'
            obj[key] = float(self.txt_min_pctl.text().strip())
        if self.txt_max_pctl.text().strip():
            key = 'vmax' if self.combo_max.currentText() == 'absolute' else \
                'percmax'
            obj[key] = float(self.txt_max_pctl.text().strip())
        val = list(self.methods_type(**obj))
        try:
            val[0] = val[0].name
        except AttributeError:
            pass
        self.parent().set_obj(val)

    def refresh(self, method, fmto):
        value = fmto.value
        if value is None:
            value = self.methods_type(method)
        try:
            value = self.methods_type(*value)
        except (ValueError, TypeError):
            pass
        else:
            self.sb_N.setValue(value.N or 0)

            bounds_val = value.method.name in ['bounds', 'midbounds']
            self.txt_min_pctl.setEnabled(not bounds_val)
            self.txt_max_pctl.setEnabled(not bounds_val)
            self.combo_min.setEnabled(not bounds_val)
            self.combo_max.setEnabled(not bounds_val)

            decimals = None
            if value.vmin is not None and value.vmax is not None:
                decimals = self.get_decimals(value.vmin, value.vmax)
            if value.vmin is not None:
                if decimals is None:
                    decimals = -np.floor(np.log10(value.vmin)) + 4
                self.txt_min_pctl.setText(str(np.round(value.vmin, decimals)))
                self.combo_min.setCurrentText('absolute')
            elif value.percmin != 0:
                self.txt_min_pctl.setText('%1.6g' % value.percmin)
                self.combo_min.setCurrentText('percentile')

            if value.vmax is not None:
                if decimals is None:
                    decimals = -np.floor(np.log10(value.vmax)) + 4
                self.txt_max_pctl.setText(str(np.round(value.vmax, decimals)))
                self.combo_max.setCurrentText('absolute')
            elif value.percmax != 100:
                self.txt_max_pctl.setText('%1.6g' % value.percmax)
                self.combo_max.setCurrentText('percentile')

    @staticmethod
    def get_decimals(vmin, vmax):
        if vmin == vmax:
            decimals = 4
        else:
            decimals = -np.floor(np.log10(abs(vmax - vmin))) + 4
        return int(decimals)


class ArrayFmtWidget(QtWidgets.QWidget):
    """Fmt widget for :class:`psy_simple.plotters.DataTicksCalculator`

    This formatoption widgets contains 3 line edits, one for the minimum, one
    for the maximum and one for the step size. And a spin box for the number
    of increments"""

    def __init__(self, parent, array=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.txt_min = QtWidgets.QLineEdit()
        self.txt_min.setValidator(QtGui.QDoubleValidator())
        self.txt_max = QtWidgets.QLineEdit()
        self.txt_max.setValidator(QtGui.QDoubleValidator())
        self.txt_step = QtWidgets.QLineEdit()
        self.txt_step.setValidator(QtGui.QDoubleValidator(1e-10, 1e10, 10))
        self.sb_nsteps = QtWidgets.QSpinBox()
        self.step_inc_combo = combo = QtWidgets.QComboBox()
        combo.addItems(['Step', '# Steps'])

        if array is not None:
            vmin, vmax = array.min(), array.max()
            decimals = self.get_decimals(vmin, vmax)

            self.txt_min.setText(f'%1.{decimals}g' % vmin)
            self.txt_max.setText(f'%1.{decimals}g' % vmax)
            steps = np.diff(array)
            if len(steps) == 1 or np.diff(steps).max() < 1e-5:
                self.txt_step.setText(f'%1.{decimals}g' % steps[0])
                combo.setCurrentIndex(0)
            else:
                combo.setCurrentIndex(1)
            self.sb_nsteps.setValue(len(array))

        self.toggle_txt_step(combo.currentText())

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel('Min.'))
        hbox.addWidget(self.txt_min)
        hbox.addWidget(QtWidgets.QLabel('Max.'))
        hbox.addWidget(self.txt_max)
        hbox.addWidget(combo)
        hbox.addWidget(self.txt_step)
        hbox.addWidget(self.sb_nsteps)
        self.setLayout(hbox)

        for w in [self.txt_min, self.txt_max, self.txt_step]:
            w.textChanged.connect(self.set_array)
        self.sb_nsteps.valueChanged.connect(self.set_array)

        combo.currentTextChanged.connect(self.toggle_txt_step)

    def toggle_txt_step(self, s):
        show_step = s == 'Step'
        self.txt_step.setVisible(show_step)
        self.sb_nsteps.setVisible(not show_step)
        self.txt_step.setEnabled(show_step)
        self.sb_nsteps.setEnabled(not show_step)
        self.set_array()

    @staticmethod
    def get_decimals(vmin, vmax):
        if vmin == vmax:
            decimals = 4
        else:
            decimals = -np.floor(np.log10(abs(vmax - vmin))) + 4
        return int(decimals)

    def set_array(self, *args, **kwargs):
        try:
            vmin = float(self.txt_min.text())
        except (ValueError, TypeError):
            return
        try:
            vmax = float(self.txt_max.text())
        except (ValueError, TypeError):
            return
        if self.txt_step.isEnabled():
            try:
                step = float(self.txt_step.text().strip())
            except (ValueError, TypeError):
                return
            arr = np.arange(vmin, vmax + 0.05 * step, step)
        else:
            arr = np.linspace(vmin, vmax, self.sb_nsteps.value())
        self.parent().set_obj(
            np.round(arr, self.get_decimals(vmin, vmax)).tolist())

    def set_obj(self):
        self.set_array()


class NormalizationWidget(QtWidgets.QWidget):
    """A simple widget representing a boundary norm"""

    def __init__(self, parent, norm):
        QtWidgets.QWidget.__init__(self, parent)
        self.norm = norm

        validator = QtGui.QDoubleValidator()
        self.txt_min = QtWidgets.QLineEdit()
        self.txt_min.setValidator(validator)
        self.txt_max = QtWidgets.QLineEdit()
        self.txt_max.setValidator(validator)

        self.lbl_linthresh = QtWidgets.QLabel('linthresh:')
        self.txt_linthresh = QtWidgets.QLineEdit()  # linthresh for SymLogNorm
        self.txt_linthresh.setValidator(validator)
        self.txt_linthresh.setToolTip(
            'The threshold for linear scaling. Within this distance from 0, '
            'the scaling will be linear, not logarithmic.')

        self.lbl_gamma = QtWidgets.QLabel('gamma:')
        self.txt_gamma = QtWidgets.QLineEdit()  # gamma for PowerNorm
        self.txt_gamma.setValidator(validator)
        self.txt_gamma.setToolTip('The power value for the PowerNorm')

        self.fill_from_norm()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel('Min.:'))
        hbox.addWidget(self.txt_min)
        hbox.addWidget(QtWidgets.QLabel('Max.:'))
        hbox.addWidget(self.txt_max)
        hbox.addWidget(self.lbl_linthresh)
        hbox.addWidget(self.txt_linthresh)
        hbox.addWidget(self.lbl_gamma)
        hbox.addWidget(self.txt_gamma)
        self.setLayout(hbox)

        self.txt_min.textChanged.connect(self.set_obj)
        self.txt_max.textChanged.connect(self.set_obj)
        self.txt_linthresh.textChanged.connect(self.set_obj)
        self.txt_gamma.textChanged.connect(self.set_obj)

    def fill_from_norm(self):
        norm = self.norm
        if norm.vmin is not None:
            self.txt_min.setText('%1.6g' % norm.vmin)
        if norm.vmax is not None:
            self.txt_max.setText('%1.6g' % norm.vmax)
        if isinstance(self.norm, mcol.SymLogNorm):
            self.txt_linthresh.setVisible(True)
            self.txt_linthresh.setEnabled(True)
            self.lbl_linthresh.setVisible(True)
            self.txt_linthresh.setText('%1.6g' % norm.linthresh)
        else:
            self.txt_linthresh.setVisible(False)
            self.txt_linthresh.setEnabled(False)
            self.lbl_linthresh.setVisible(False)
        if isinstance(norm, mcol.PowerNorm):
            self.txt_gamma.setVisible(True)
            self.txt_gamma.setEnabled(True)
            self.lbl_gamma.setVisible(True)
            self.txt_gamma.setText('%1.6g' % norm.gamma)
        else:
            self.txt_gamma.setVisible(False)
            self.txt_gamma.setEnabled(False)
            self.lbl_gamma.setVisible(False)

    def set_obj(self):
        cls = self.norm.__class__
        kws = {}
        if issubclass(cls, mcol.PowerNorm):
            args = [float(self.txt_gamma.text().strip() or 1.0)]
        elif issubclass(cls, mcol.SymLogNorm):
            args = [float(self.txt_linthresh.text().strip() or 1e-3)]
            if mpl_version >= (3, 2):
                kws["base"] = 10
        else:
            args = []
        vmin = vmax = None
        if self.txt_min.text().strip():
            vmin = float(self.txt_min.text().strip())
        if self.txt_max.text().strip():
            vmax = float(self.txt_max.text().strip())
        try:
            norm = cls(*args, vmin=vmin, vmax=vmax, **kws)
        except Exception:
            pass
        else:
            self.parent().set_obj(norm)


class BoundsFmtWidget(QtWidgets.QWidget):
    """The widget for modifying the :class:`psy_simple.plotters.Bounds` fmt"""

    _array_widget = None

    _auto_array_widget = None

    _norm_widget = None

    current_widget = None

    methods_type = BoundsType

    norm_map = {
        'No normalization': mcol.Normalize,
        'log': mcol.LogNorm,
        'symlog': mcol.SymLogNorm,
        'power-law': mcol.PowerNorm,
        }

    default_args = {
        'symlog': [1e-3],  # linthresh
        'power-law': [1.0]  # gamma
        }

    default_kws = {
        "symlog": {"base": 10} if mpl_version >= (3, 2) else {}
    }

    methods = ['Discrete', 'Continuous']

    def __init__(self, parent, fmto, project, properties=True):
        QtWidgets.QWidget.__init__(self, parent)
        self._editor = parent
        hbox = QtWidgets.QHBoxLayout()

        self.type_combo = QtWidgets.QComboBox(self)
        self.type_combo.addItems(self.methods)

        self.method_combo = QtWidgets.QComboBox(self)

        self.discrete_items = sorted(fmto.calc_funcs) + ['Custom']

        hbox.addWidget(self.type_combo)
        hbox.addWidget(self.method_combo)
        hbox.addStretch(0)

        self.type_combo.currentTextChanged.connect(self.refresh_methods)
        self.method_combo.currentTextChanged.connect(
            self.refresh_current_widget)

        # add a button to select other formatoptions
        if properties:
            hbox.addWidget(Switch2FmtButton(parent, fmto.cmap, fmto.cbar))
        self.setLayout(hbox)

        self.set_value(fmto.value)

    def set_value(self, value):
        with self.block_widgets(self.method_combo, self.type_combo):
            if value is None:
                self.type_combo.setCurrentText('Continuous')
                self.refresh_methods('Continuous')
                self.method_combo.setCurrentText('No normalization')
            elif isinstance(value, mcol.Normalize) and not hasattr(
                    value, 'boundaries'):
                self.type_combo.setCurrentText('Continuous')
                self.refresh_methods('Continuous')

                if isinstance(value, mcol.LogNorm):
                    self.method_combo.setCurrentText('log')
                elif isinstance(value, mcol.SymLogNorm):
                    self.method_combo.setCurrentText('symlog')
                elif isinstance(value, mcol.PowerNorm):
                    self.method_combo.setCurrentText('power-law')
                else:
                    self.method_combo.setCurrentText('Custom')
            else:
                self.type_combo.setCurrentText('Discrete')
                self.refresh_methods('Discrete')
                if not isinstance(value, mcol.Normalize) and isinstance(
                        value[0], six.string_types):
                    self.method_combo.setCurrentText(value[0])
                else:
                    self.method_combo.setCurrentText('Custom')

        self.refresh_methods(self.type_combo.currentText())

    @contextlib.contextmanager
    def block_widgets(self, *widgets):
        for w in widgets:
            w.blockSignals(True)
        yield
        for w in widgets:
            w.blockSignals(False)

    def refresh_methods(self, text):
        current = self.method_combo.currentText()
        with self.block_widgets(self.method_combo):
            self.method_combo.clear()
            if text == 'Discrete':
                items = self.discrete_items
                self.method_combo.addItems(items)
                if current in items:
                    self.method_combo.setCurrentText(current)
                elif current == 'No normalization' and 'rounded' in items:
                    self.method_combo.setCurrentText('rounded')
            else:
                self.method_combo.addItems(list(self.norm_map))
                if current in self.norm_map:
                    self.method_combo.setCurrentText(current)
                else:
                    self.method_combo.setCurrentText('No normalization')

        self.refresh_current_widget()

    def refresh_current_widget(self):
        if self.current_widget is not None:
            self.current_widget.setVisible(False)
        if self.type_combo.currentText() == 'Continuous':
            s = self.method_combo.currentText()
            norm = self.norm_map[s](*self.default_args.get(s, []),
                                    **self.default_kws.get(s, {}))
            self.current_widget = self.get_norm_widget(norm)
        else:
            if self.method_combo.currentText() != 'Custom':
                self.current_widget = self.get_auto_discrete_array_widget()
            else:
                self.current_widget = self.get_discrete_array_widget()
        if self.current_widget is not None:
            self.current_widget.setVisible(True)
            self.current_widget.set_obj()

    def get_auto_discrete_array_widget(self):
        method = self.method_combo.currentText()
        if self._auto_array_widget is not None:
            self._auto_array_widget.method = method
        else:
            self._auto_array_widget = DataTicksCalculatorFmtWidget(
                self._editor, method, self.methods_type)
            self.layout().insertWidget(3, self._auto_array_widget)

        fmto = self._editor.fmto
        self._auto_array_widget.refresh(
            self.method_combo.currentText(), fmto)
        return self._auto_array_widget

    def get_discrete_array_widget(self):
        if self._array_widget is not None:
            return self._array_widget
        fmto = self._editor.fmto
        try:
            arr = fmto.norm.boundaries
        except AttributeError:
            arr = fmto.calc_funcs['rounded']()
        self._array_widget = ArrayFmtWidget(self._editor, arr)
        self.layout().insertWidget(3, self._array_widget)
        return self._array_widget

    def get_norm_widget(self, norm):
        if self._norm_widget is not None:
            if norm.__class__ is not self._norm_widget.norm.__class__:
                # don't use isinstance here because of mcol.Normalize
                self._norm_widget.norm = norm
                self._norm_widget.fill_from_norm()
            return self._norm_widget
        self._norm_widget = NormalizationWidget(self._editor, norm)
        self.layout().insertWidget(3, self._norm_widget)
        return self._norm_widget

    def set_obj(self, obj):
        self._editor.set_obj(obj)


class CTicksFmtWidget(BoundsFmtWidget):
    """The formatoptions widget for the colorbar ticks."""

    methods = ['Discrete', 'Auto']

    norm_map = {}

    methods_type = CTicksType

    auto_val = None

    def set_value(self, value):
        if value is self.auto_val:
            with self.block_widgets(self.method_combo, self.type_combo):
                self.type_combo.setCurrentText('Auto')
            self.refresh_methods('Auto')
        else:
            super().set_value(value)

    def refresh_methods(self, text):
        if text == 'Auto':
            with self.block_widgets(self.method_combo):
                self.method_combo.clear()
            self.set_obj(self.auto_val)
            self.refresh_current_widget()
        else:
            super().refresh_methods(text)

    def refresh_current_widget(self):
        w = self.current_widget
        auto_ticks = self.type_combo.currentText() == 'Auto'
        if auto_ticks and w is not None:
            w.setVisible(False)
            self.current_widget = None
        if not auto_ticks:
            super().refresh_current_widget()


if __name__ == '__main__':
    # build colormap thumbnails
    import matplotlib.pyplot as plt
    available_cmaps = set(
        chain(plt.cm.cmap_d, psc._cmapnames, rcParams['colors.cmaps']))
    N = len(available_cmaps)
    for i, cmap in enumerate(available_cmaps, 1):
        print("%i of %i: Generating thumb %s" % (i, N, cmap))
        create_cmap_thumb(cmap, get_icon(osp.join('cmaps', cmap)))