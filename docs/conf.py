# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from pathlib import Path

from sphinx.ext import apidoc

sys.path.insert(0, os.path.abspath(".."))

if not os.path.exists("_static"):
    os.makedirs("_static")

# isort: off

import psy_simple

# isort: on


def generate_apidoc(app):
    appdir = Path(app.__file__).parent
    apidoc.main(
        ["-fMEeTo", str(api), str(appdir), str(appdir / "migrations" / "*")]
    )


api = Path("api")

if not api.exists():
    generate_apidoc(psy_simple)

# -- Project information -----------------------------------------------------

project = "psy-simple"
copyright = "2021-2024 Helmholtz-Zentrum hereon GmbH"
author = "Philipp S. Sommer"


linkcheck_ignore = [
    # we do not check link of the psy-simple as the
    # badges might not yet work everywhere. Once psy-simple
    # is settled, the following link should be removed
    r"https://.*psy-simple"
]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "hereon_nc_sphinxext",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "autodocsumm",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


autodoc_default_options = {
    "show_inheritance": True,
    "members": True,
    "autosummary": True,
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "collapse_navigation": False,
    "includehidden": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "django": ("https://django.readthedocs.io/en/stable/", None),
}
