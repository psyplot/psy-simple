"""pytest configuration module for psy-simple."""

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum Hereon
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht
# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
#
# SPDX-License-Identifier: LGPL-3.0-only


def pytest_addoption(parser):
    group = parser.getgroup("psyplot", "psyplot specific options")
    group.addoption(
        "--ref",
        help="Create reference figures instead of running the tests",
        action="store_true",
    )


def pytest_configure(config):
    from PIL import ImageFile

    if config.getoption("ref"):
        import unittest

        unittest.TestLoader.testMethodPrefix = "ref"

    # make PIL load truncated images to avoid OSErrors in a parallelized
    # setup
    ImageFile.LOAD_TRUNCATED_IMAGES = True
