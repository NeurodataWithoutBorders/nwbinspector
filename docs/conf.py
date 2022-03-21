import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from conf_extlinks import extlinks
from conf_extlinks import intersphinx_mapping

sys.path.insert(0, Path(__file__).resolve().parents[1])

project = "NWBInspector"
copyright = "2022, CatalystNeuro"
author = "Cody Baker, Ryan Ly, and Ben Dichter"

extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx.ext.extlinks",
]
templates_path = ["_templates"]
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
]

html_theme_options = {
    "collapse_navigation": False,
}

# --------------------------------------------------
# Extension configuration
# --------------------------------------------------

# Napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

# Autodoc
autoclass_content = "both"
autodoc_member_order = "bysource"
autodata_content = "both"
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "private-members": True,
    "show-inheritance": False,
    "toctree": True,
}
add_module_names = False


def add_refs_to_docstrings(app, what, name, obj, options, lines):
    if what == "function" and obj.__name__.startswith("check_"):
        lines.append(f"Best Practice: :ref:`best_practice_{obj.__name__.split('check_')[1]}`")


def setup(app):
    app.connect("autodoc-process-docstring", add_refs_to_docstrings)
