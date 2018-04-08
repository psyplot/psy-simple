"""Module for color specific widgets

This module corresponds to the :mod:`psy_simple.colors` module as a version for
the usage in the psyplot GUI."""
import six
from functools import partial
from psyplot.data import safe_list
from psy_simple.widgets import Switch2FmtButton
from psy_simple.colors import _get_cmaps, get_cmap
from psyplot.docstring import docstrings
import numpy as np
import xarray as xr
import matplotlib.colors as mcol
from psyplot_gui.compat.qtcompat import (
    QDialog, QTableView, Qt, QtCore, QtGui, with_qt5, QVBoxLayout,
    QDialogButtonBox, QDesktopWidget, QWidget, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QLabel, QDoubleValidator)


if with_qt5:
    from PyQt5.QtWidgets import QColorDialog, QSpinBox
else:
    from PyQt4.QtGui import QColorDialog, QSpinBox


docstrings.delete_params('show_colormaps.parameters', 'show', 'use_qt')


class ColormapModel(QtCore.QAbstractTableModel):
    """A model for displaying colormaps"""

    @docstrings.get_sectionsf('ColormapModel')
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
        names = _get_cmaps(names)
        self.names = names

        colors = np.zeros((len(names), N, 4))
        a = np.linspace(0, 1, N)
        for i, cmap in enumerate(map(lambda name: get_cmap(name, N),
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


class ColormapTable(QTableView):
    """A table for displaying colormaps"""

    @docstrings.with_indent(8)
    def __init__(self, names=[], N=10, *args, **kwargs):
        """
        Parameters
        ----------
        %(ColormapModel.parameters)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the QTableView
        """
        super(ColormapTable, self).__init__(*args, **kwargs)
        self.setModel(ColormapModel(names, N))
        self.doubleClicked.connect(self.change_color)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)

    def setModel(self, model):
        super(ColormapTable, self).setModel(model)
        self.orig_color_da = model.color_da.copy(True)

    def change_color(self, index):
        model = self.model()
        current = model.data(index, Qt.BackgroundColorRole)
        if current is None:
            return
        color = QColorDialog.getColor(current, parent=self)
        if not color.isValid():
            return
        model.color_da[index.row(), index.column()] = color.getRgbF()
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


class ColormapDialog(QDialog):
    """A widget for selecting a colormap"""

    @docstrings.with_indent(8)
    def __init__(self, names=[], N=10, *args, **kwargs):
        """
        Parameters
        ----------
        %(ColormapModel.parameters)s

        Other Parameters
        ----------------
        ``*args, **kwargs``
            Anything else that is passed to the ColormapDialog
        """
        super(QDialog, self).__init__(*args, **kwargs)
        vbox = QVBoxLayout()
        self.table = ColormapTable(names=names, N=N)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        col_width = self.table.columnWidth(0)
        header_width = self.table.verticalHeader().width()
        row_height = self.table.rowHeight(0)
        available = QDesktopWidget().availableGeometry()
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
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=obj)
        buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(buttons)
        buttons.accepted.connect(obj.accept)
        buttons.rejected.connect(obj.reject)

        obj.table.selectionModel().selectionChanged.connect(
            lambda indices: buttons.button(QDialogButtonBox.Ok).setEnabled(
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
        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=obj)
        buttons.rejected.connect(obj.close)
        vbox.addWidget(buttons)
        if show:
            obj.show()
        return obj


class CMapFmtWidget(QWidget):
    """The widget for modifying the :class:`psy_simple.plotters.CMap` fmt"""

    def __init__(self, parent, fmto, project):
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()

        # add a select colormap button
        self.btn_choose = button = QPushButton('Choose...')
        button.clicked.connect(partial(self.choose_cmap, None))
        hbox.addWidget(button)

        # add a show colormap button
        self.btn_show = button = QPushButton('Show...')
        button.clicked.connect(self.show_cmap)
        hbox.addWidget(button)

        hbox.addWidget(Switch2FmtButton(parent, fmto.bounds, fmto.cbar))

        self.setLayout(hbox)

    def choose_cmap(self, cmap=None):
        parent = self.parent()
        if cmap is None:
            cmap = ColormapDialog.get_colormap(
                N=getattr(parent.fmto.bounds.norm, 'Ncmap', 10))
        if cmap is not None:
            parent.set_obj(cmap)

    def show_cmap(self):
        parent = self.parent()
        cmap = parent.get_obj()
        if cmap is not None:
            return ColormapDialog.show_colormap(
                cmap, N=getattr(parent.fmto.bounds.norm, 'Ncmap', 10),
                parent=self)


class DataTicksCalculatorFmtWidget(QWidget):
    """Fmt widget for :class:`psy_simple.plotters.DataTicksCalculator`

    This widget contains a combo box with the different options from the
    :attr:`psy_simple.plotters.DataTicksCalculator.calc_funcs`, a spin box
    for the number of increments and two text widgets for minimum and maximum
    percentile"""

    def __init__(self, parent, fmto, what=None, N=None, pctl_min=None,
                 pctl_max=None):
        QWidget.__init__(self, parent)

        hbox = QHBoxLayout()

        self.combo = QComboBox()
        self.combo.addItems(sorted(fmto.calc_funcs))
        hbox.addWidget(self.combo)

        self.sb_N = QSpinBox()
        hbox.addWidget(self.sb_N)

        self.txt_min_pctl = QLineEdit()
        self.txt_min_pctl.setValidator(QDoubleValidator(0., 100., 10))
        hbox.addWidget(QLabel('Percentiles:'))
        hbox.addWidget(QLabel('Min.:'))
        hbox.addWidget(self.txt_min_pctl)

        self.txt_max_pctl = QLineEdit()
        self.txt_max_pctl.setValidator(QDoubleValidator(0., 100., 10))
        hbox.addWidget(QLabel('Max.:'))
        hbox.addWidget(self.txt_max_pctl)

        if what is not None:
            self.combo.setCurrentText(what)
        if N is not None:
            self.sb_N.setValue(N)
        if pctl_min is not None:
            self.txt_min_pctl.setText('%1.6g' % pctl_min)
        if pctl_max is not None:
            self.txt_max_pctl.setText('%1.6g' % pctl_max)

        self.combo.currentTextChanged.connect(self.set_obj)
        self.sb_N.valueChanged.connect(self.set_obj)
        self.txt_min_pctl.textChanged.connect(self.set_obj)
        self.txt_max_pctl.textChanged.connect(self.set_obj)

        self.setLayout(hbox)

    def set_obj(self):
        obj = [self.combo.currentText(),
               self.sb_N.value()]
        if (self.txt_min_pctl.text().strip() or
                self.txt_max_pctl.text().strip()):
            obj.append(float(self.txt_min_pctl.text().strip() or 0))
            if self.txt_max_pctl.text().strip():
                obj.append(float(self.txt_max_pctl.text().strip()))
        self.parent().set_obj(obj)


class ArrayFmtWidget(QWidget):
    """Fmt widget for :class:`psy_simple.plotters.DataTicksCalculator`

    This formatoption widgets contains 3 line edits, one for the minimum, one
    for the maximum and one for the step size. And a spin box for the number
    of increments"""

    def __init__(self, parent, array=None):
        QWidget.__init__(self, parent)

        self.txt_min = QLineEdit()
        self.txt_min.setValidator(QDoubleValidator())
        self.txt_max = QLineEdit()
        self.txt_max.setValidator(QDoubleValidator())
        self.txt_step = QLineEdit()
        self.txt_step.setValidator(QDoubleValidator(1e-10, 1e10, 10))
        self.sb_nsteps = QSpinBox()
        self.step_inc_combo = combo = QComboBox()
        combo.addItems(['Step', '# Steps'])

        if array is not None:
            self.txt_min.setText('%1.4g' % array.min())
            self.txt_max.setText('%1.4g' % array.max())
            steps = np.diff(array)
            if len(steps) == 1 or np.diff(steps).max() < 1e-5:
                self.txt_step.setText('%1.4g' % steps[0])
                combo.setCurrentIndex(0)
            else:
                combo.setCurrentIndex(1)
            self.sb_nsteps.setValue(len(array))

        self.toggle_txt_step(combo.currentText())

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Min.'))
        hbox.addWidget(self.txt_min)
        hbox.addWidget(QLabel('Max.'))
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
        self.parent().set_obj(np.round(arr, 4).tolist())


class NormalizationWidget(QWidget):
    """A simple widget representing a boundary norm"""

    def __init__(self, parent, norm):
        QWidget.__init__(self, parent)
        self.norm = norm

        validator = QDoubleValidator()
        self.txt_min = QLineEdit()
        self.txt_min.setValidator(validator)
        self.txt_max = QLineEdit()
        self.txt_max.setValidator(validator)

        self.lbl_linthresh = QLabel('linthresh:')
        self.txt_linthresh = QLineEdit()  # linthresh for SymLogNorm
        self.txt_linthresh.setValidator(validator)
        self.txt_linthresh.setToolTip(
            'The threshold for linear scaling. Within this distance from 0, '
            'the scaling will be linear, not logarithmic.')

        self.lbl_gamma = QLabel('gamma:')
        self.txt_gamma = QLineEdit()  # gamma for PowerNorm
        self.txt_gamma.setValidator(validator)
        self.txt_gamma.setToolTip('The power value for the PowerNorm')

        self.fill_from_norm()

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Min.:'))
        hbox.addWidget(self.txt_min)
        hbox.addWidget(QLabel('Max.:'))
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
        if issubclass(cls, mcol.PowerNorm):
            args = [float(self.txt_gamma.text().strip() or 1.0)]
        elif issubclass(cls, mcol.SymLogNorm):
            args = [float(self.txt_linthresh.text().strip() or 1e-3)]
        else:
            args = []
        vmin = vmax = None
        if self.txt_min.text().strip():
            vmin = float(self.txt_min.text().strip())
        if self.txt_max.text().strip():
            vmax = float(self.txt_max.text().strip())
        try:
            norm = cls(*args, vmin=vmin, vmax=vmax)
        except Exception:
            pass
        else:
            self.parent().set_obj(norm)


class BoundsFmtWidget(QWidget):
    """The widget for modifying the :class:`psy_simple.plotters.Bounds` fmt"""

    _array_widget = None

    _auto_array_widget = None

    _norm_widget = None

    current_widget = None

    norm_map = {
        'No normalization': mcol.NoNorm,
        'Logarithmic': mcol.LogNorm,
        'Symmetric logarithmic': mcol.SymLogNorm,
        'Power-law': mcol.PowerNorm,
        }

    default_args = {
        'Symmetric logarithmic': [1e-3],  # linthresh
        'Power-law': [1.0]  # gamma
        }

    def __init__(self, parent, fmto, project):
        QWidget.__init__(self, parent)
        hbox = QHBoxLayout()

        self.combo = combo = QComboBox(self)
        combo.addItems(['Auto discrete', 'No normalization',
                        'Discrete', 'Logarithmic', 'Symmetric logarithmic',
                        'Power-law', 'Custom'])
        hbox.addWidget(combo)
        value = fmto.value
        if value is None:
            combo.setCurrentText('No normalization')
            value = mcol.Normalize()
        elif isinstance(value, mcol.Normalize):
            if isinstance(value, mcol.LogNorm):
                combo.setCurrentText('Logarithmic')
            elif isinstance(value, mcol.SymLogNorm):
                combo.setCurrentText('Symmetric logarithmic')
            elif isinstance(value, mcol.PowerNorm):
                combo.setCurrentText('Power-law')
            else:
                combo.setCurrentText('Custom')
        elif isinstance(value[0], six.string_types):
            combo.setCurrentText('Auto discrete')
        else:
            combo.setCurrentText('Discrete')

        combo.currentTextChanged.connect(self.toggle_combo)

        # add a button to select other formatoptions
        hbox.addWidget(Switch2FmtButton(parent, fmto.cmap, fmto.cbar))
        self.setLayout(hbox)
        self.toggle_combo(combo.currentText())

        # refresh the norm widget if necessary
        if isinstance(value, mcol.Normalize):
            self.current_widget.norm = value
            self.current_widget.fill_from_norm()

    def toggle_combo(self, s):
        if self.current_widget is not None:
            self.current_widget.setVisible(False)
        if s == 'Auto discrete':
            self.current_widget = self.get_auto_discrete_array_widget()
        elif s == 'Discrete':
            self.current_widget = self.get_discrete_array_widget()
        elif s in self.norm_map:
            norm = self.norm_map[s](*self.default_args.get(s, []))
            self.current_widget = self.get_norm_widget(norm)
        else:
            self.current_widget = None
        if self.current_widget is not None:
            self.current_widget.setVisible(True)

    def get_auto_discrete_array_widget(self):
        if self._auto_array_widget is not None:
            return self._auto_array_widget
        fmto = self.parent().fmto
        args = []
        try:
            what = fmto.value[0]
        except TypeError:
            pass
        else:
            if isinstance(what, six.string_types):
                args = list(fmto.value)
                if fmto.value[1] is None:  # N is None
                    args[1] = len(fmto.norm.boundaries)
        self._auto_array_widget = DataTicksCalculatorFmtWidget(
            self.parent(), fmto, *args)
        self.layout().insertWidget(1, self._auto_array_widget)
        return self._auto_array_widget

    def get_discrete_array_widget(self):
        if self._array_widget is not None:
            return self._array_widget
        fmto = self.parent().fmto
        try:
            arr = fmto.norm.boundaries
        except AttributeError:
            arr = fmto.calc_funcs['rounded']()
        self._array_widget = ArrayFmtWidget(self.parent(), arr)
        self.layout().insertWidget(1, self._array_widget)
        return self._array_widget

    def get_norm_widget(self, norm):
        if self._norm_widget is not None:
            if not isinstance(self._norm_widget.norm, norm.__class__):
                self._norm_widget.norm = norm
                self._norm_widget.fill_from_norm()
            return self._norm_widget
        self._norm_widget = NormalizationWidget(self.parent(), norm)
        self.layout().insertWidget(1, self._norm_widget)
        return self._norm_widget

    def set_obj(self, obj):
        self.parent().set_obj(obj)
