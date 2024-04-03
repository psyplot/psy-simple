"""Test module for the CombinedSimplePlotter."""


# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


import os
import re
import unittest
from functools import wraps
from itertools import chain

import _base_testing as bt
import numpy as np
import psyplot.project as psy
import six
import test_base as tb
import test_plot2d as t2d
import test_vector as tv
from psyplot import ArrayList, open_dataset, rcParams
from psyplot.utils import _TempBool

from psy_simple.plotters import CombinedSimplePlotter

bold = tb.bold


def _do_from_both(func):
    """Call the given `func` only from :class:`t2d.Simple2DPlotterTest` and
    :class:`tv.SimpleVectorPlotterTest`"""
    func.__doc__ = getattr(tv.SimpleVectorPlotterTest, func.__name__).__doc__

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        getattr(t2d.Simple2DPlotterTest, func.__name__)(self, *args, **kwargs)
        if hasattr(self, "plotter"):
            self.plotter.update(todefault=True)
        with self.vector_mode:
            getattr(tv.SimpleVectorPlotterTest, func.__name__)(
                self, *args, **kwargs
            )

    return wrapper


def _in_vector_mode(func):
    """Call the given `func` only from :class:`tv.SimpleVectorPlotterTest`"""
    func.__doc__ = getattr(tv.SimpleVectorPlotterTest, func.__name__).__doc__

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.vector_mode:
            getattr(tv.SimpleVectorPlotterTest, func.__name__)(
                self, *args, **kwargs
            )

    return wrapper


class _CombinedPlotterData(object):
    """Descriptor that returns the data"""

    # Note: We choose to use a descriptor rather than a usual property because
    # it shall also work for class objects and not only instances

    def __get__(self, instance, owner):
        if instance is None:
            return owner._data
        if instance.vector_mode:
            return instance._data[1]
        return instance._data[0]

    def __set__(self, instance, value):
        instance._data = value


class CombinedSimplePlotterTest(tv.SimpleVectorPlotterTest):
    """Test case for vector plot of
    :class:`psy_simple.plotters.CombinedSimplePlotter`"""

    plot_type = "simplecombined"

    data = _CombinedPlotterData()

    var = ["t2m", ["u", "v"]]

    @property
    def vector_mode(self):
        """:class:`bool` indicating whether a vector specific formatoption is
        tested or not"""
        try:
            return self._vector_mode
        except AttributeError:
            self._vector_mode = _TempBool(False)
            return self._vector_mode

    @vector_mode.setter
    def vector_mode(self, value):
        self.vector_mode.value = bool(value)

    def compare_figures(self, fname, **kwargs):
        kwargs.setdefault("tol", 10)
        return super(CombinedSimplePlotterTest, self).compare_figures(
            fname, **kwargs
        )

    @classmethod
    def setUpClass(cls):
        cls.ds = open_dataset(cls.ncfile)
        plotter = CombinedSimplePlotter()
        rcParams[plotter.vcmap.default_key] = "winter"
        cls._data = ArrayList.from_dataset(
            cls.ds,
            t=0,
            z=0,
            name=[cls.var],
            auto_update=True,
            prefer_list=True,
        )[0]
        for i in range(len(cls.data)):
            cls._data[i] = cls._data[i].psy.sel(
                lon=slice(0, 69.0), lat=slice(81.0, 34.0)
            )
        cls._data.attrs["long_name"] = "Temperature"
        cls._data.attrs["name"] = "t2m"
        cls.plotter = CombinedSimplePlotter(cls.data)
        cls.create_dirs()
        cls._color_fmts = cls.plotter.fmt_groups["colors"]

        # there is an issue with the colorbar that the size of the axes changes
        # slightly after replotting. Therefore we force a replot here
        cls.plotter.update(color="absolute")
        cls.plotter.update(todefault=True, replot=True)

    def tearDown(self):
        self._data.psy.update(t=0, todefault=True, replot=True)

    def plot(self, **kwargs):
        color_fmts = psy.plot.vector.plotter_cls().fmt_groups["colors"]
        fix_colorbar = not color_fmts.intersection(kwargs)
        ds = psy.open_dataset(self.ncfile)
        kwargs.setdefault("t", ds.time.values[0])
        kwargs.setdefault("z", ds.lev.values[0])
        kwargs.setdefault("x", slice(0, 69.0))
        kwargs.setdefault("y", slice(81.0, 34.0))
        kwargs.setdefault("method", "sel")
        kwargs.setdefault("color", "absolute")
        if self.vector_mode:
            kwargs = self._rename_fmts(kwargs)
        sp = psy.plot.combined(ds, name=[self.var], **kwargs)
        if not self.vector_mode or fix_colorbar:
            # if we have no color formatoptions, we have to consider that
            # the position of the plot may have slighty changed
            sp.update(
                todefault=True,
                replot=True,
                **dict(item for item in kwargs.items() if item[0] != "color"),
            )
        return sp

    def _rename_fmts(self, kwargs):
        def check_key(key):
            if not any(re.match("v" + key, fmt) for fmt in vcolor_fmts):
                return key
            else:
                return "v" + key

        vcolor_fmts = {
            fmt
            for fmt in chain(
                psy.plot.combined.plotter_cls().fmt_groups["colors"],
                ["ctick|clabel"],
            )
            if fmt.startswith("v")
        }
        return {check_key(key): val for key, val in kwargs.items()}

    def update(self, *args, **kwargs):
        if self.vector_mode and (
            self._color_fmts.intersection(kwargs)
            or any(re.match("ctick|clabel", fmt) for fmt in kwargs)
        ):
            kwargs.setdefault("color", "absolute")
            kwargs = self._rename_fmts(kwargs)
        super(tv.SimpleVectorPlotterTest, self).update(*args, **kwargs)

    def get_ref_file(self, identifier):
        if self.vector_mode:
            identifier += "_vector"
        return super(CombinedSimplePlotterTest, self).get_ref_file(identifier)

    @property
    def _minmax_cticks(self):
        if not self.vector_mode:
            return np.round(
                np.linspace(
                    self.plotter.plot_data[0].values.min(),
                    self.plotter.plot_data[0].values.max(),
                    11,
                    endpoint=True,
                ),
                decimals=2,
            ).tolist()
        speed = (
            self.plotter.plot_data[1].values[0] ** 2
            + self.plotter.plot_data[1].values[1] ** 2
        ) ** 0.5
        return np.round(
            np.linspace(speed.min(), speed.max(), 11, endpoint=True),
            decimals=2,
        ).tolist()

    @_do_from_both
    def ref_cbar(self, close=True):
        pass

    def ref_cbarspacing(self, close=True):
        """Create reference file for cbarspacing formatoption"""
        kwargs = dict(
            bounds=list(range(245, 255))
            + np.linspace(255, 280, 6, endpoint=True).tolist()
            + list(range(281, 290))
        )
        sp = self.plot(cbarspacing="proportional", cticks="rounded", **kwargs)
        sp.export(os.path.join(bt.ref_dir, self.get_ref_file("cbarspacing")))
        with self.vector_mode:
            tv.SimpleVectorPlotterTest.ref_cbarspacing(self, close=close)
        if close:
            sp.close(True, True)

    @_do_from_both
    def ref_cmap(self, close=True):
        pass

    def ref_miss_color(self, close=True):
        t2d.Simple2DPlotterTest.ref_miss_color(self, close)

    @_in_vector_mode
    def ref_arrowsize(self, *args, **kwargs):
        pass

    def _label_test(self, key, label_func, has_time=True):
        kwargs = {
            key: "Test plot at %Y-%m-%d, {tinfo} o'clock of %(long_name)s"
        }
        self.update(**kwargs)
        t_str = "1979-01-31, 18:00" if has_time else "%Y-%m-%d, %H:%M"
        self.assertEqual(
            "Test plot at %s o'clock of %s"
            % (t_str, self.data.attrs.get("long_name", "Temperature")),
            label_func().get_text(),
        )
        self._data.psy.update(t=1)
        t_str = "1979-02-28, 18:00" if has_time else "%Y-%m-%d, %H:%M"
        self.assertEqual(
            "Test plot at %s o'clock of %s"
            % (t_str, self.data.attrs.get("long_name", "Temperature")),
            label_func().get_text(),
        )
        self._data.psy.update(t=0)

    def test_miss_color(self, *args, **kwargs):
        t2d.Simple2DPlotterTest.test_miss_color(self, *args, **kwargs)

    @_do_from_both
    def test_cbar(self, *args, **kwargs):
        pass

    def test_cbarspacing(self, *args, **kwargs):
        """Test cbarspacing formatoption"""
        self.update(
            cbarspacing="proportional",
            cticks="rounded",
            bounds=list(range(245, 255))
            + np.linspace(255, 280, 6, endpoint=True).tolist()
            + list(range(281, 290)),
        )
        self.compare_figures(
            next(iter(args), self.get_ref_file("cbarspacing"))
        )
        self.plotter.update(todefault=True)
        with self.vector_mode:
            tv.SimpleVectorPlotterTest.test_cbarspacing(self, *args, **kwargs)

    @_do_from_both
    def test_cmap(self, *args, **kwargs):
        pass

    @unittest.skipIf(
        six.PY34, "The axes size changes using the arrowsize formatoption"
    )
    @_in_vector_mode
    def test_arrowsize(self):
        pass

    def test_bounds(self):
        """Test bounds formatoption"""
        # test bounds of scalar field
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(250, 290, 11, endpoint=True).tolist(),
        )
        self.update(bounds="minmax")
        bounds = [
            251.73,
            255.54,
            259.35,
            263.16,
            266.97,
            270.78,
            274.59,
            278.4,
            282.22,
            286.03,
            289.84,
        ]
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(bounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.bounds.norm.boundaries, 2).tolist(),
            np.linspace(250, 290, 5, endpoint=True).tolist(),
        )

        # test vector bounds
        self.update(color="absolute")
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(),
            np.linspace(0, 15, 11, endpoint=True).tolist(),
        )
        self.update(vbounds="minmax")
        bounds = [
            0.36,
            1.4,
            2.45,
            3.49,
            4.54,
            5.59,
            6.63,
            7.68,
            8.72,
            9.77,
            10.81,
        ]
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 2).tolist(), bounds
        )
        self.update(vbounds=["rounded", 5, 5, 95])
        self.assertEqual(
            np.round(self.plotter.vbounds.norm.boundaries, 3).tolist(),
            np.linspace(1.0, 8.5, 5, endpoint=True).tolist(),
        )

    def test_clabel(self):
        def get_clabel():
            return self.plotter.vcbar.cbars["b"].ax.xaxis.get_label()

        t2d.Simple2DPlotterTest.test_clabel(self)
        with self.vector_mode:
            self.update(color="absolute")
            self._label_test("vclabel", get_clabel)
            label = get_clabel()
            self.update(
                vclabelsize=22,
                vclabelweight="bold",
                vclabelprops={"ha": "left"},
            )
            self.assertEqual(label.get_size(), 22)
            self.assertEqual(label.get_weight(), bold)
            self.assertEqual(label.get_ha(), "left")


class CombinedSimplePlotterTest2D(tb.TestBase2D, CombinedSimplePlotterTest):
    """Test :class:`psy_simple.plotters.CombinedSimplePlotter` class without
    time and vertical dimension"""

    var = ["t2m", ["u_2d", "v_2d"]]

    def _label_test(self, key, label_func, has_time=None):
        if has_time is None:
            has_time = not bool(self.vector_mode)
        CombinedSimplePlotterTest._label_test(
            self, key, label_func, has_time=has_time
        )


# skip the reference creation functions of the 2D Plotter tests
skip_msg = (
    "Reference figures for this class are created by the "
    "CombinedSimplePlotterTest"
)

for funcname in filter(
    lambda s: s.startswith("ref"), dir(CombinedSimplePlotterTest2D)
):
    setattr(
        CombinedSimplePlotterTest2D,
        funcname,
        unittest.skip(skip_msg)(lambda self: None),
    )
