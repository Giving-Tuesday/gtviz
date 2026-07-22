"""Sphinx configuration for gtviz (Read the Docs)."""

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "gtviz"
author = "GivingPulse Analytics"
copyright = "2026, GivingPulse Analytics"

from gtviz import __version__ as release  # noqa: E402

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_copybutton",
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_numpy_docstring = True
napoleon_google_docstring = True

myst_enable_extensions = ["colon_fence", "deflist"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

html_theme = "furo"
html_title = f"gtviz {release}"
html_static_path = ["_static"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
