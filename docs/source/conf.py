# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join("..", "..")))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "gweatherrouting"
copyright = "2017-2025, Davide Gessa (dakk)"
author = "Davide Gessa (dakk)"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "pydata_sphinx_theme",
    "sphinx_design",
    "myst_nb",
]

# "sphinx_rtd_dark_mode",
# "sphinx_rtd_theme",
jupyter_execute_notebooks = "off"
myst_enable_extensions = ["colon_fence"]

templates_path = ["_templates"]
exclude_patterns = []
autodoc_source_dir = [
    "../gweatherrouting",
]
pygments_style = "github-dark"
default_dark_mode = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "GWeatherRouting"
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "logo": {
        "image_light": "_static/logo.png",
        "image_dark": "_static/logo-dark.png",
    },
    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/header-links.html#fontawesome-icons
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/dakk/gweatherrouting",
            "icon": "fa-brands fa-github",
        },
        # {
        #     "name": "Twitter",
        #     "url": "https://twitter.com/dagide",
        #     "icon": "fa-brands fa-twitter",
        # },
    ],
    "navbar_start": ["navbar-logo", "navbar-version"],
    "navbar_align": "content",
    "header_links_before_dropdown": 6,
    "secondary_sidebar_items": [
        "page-toc",
        "searchbox",
        "edit-this-page",
        "sourcelink",
    ],
    "use_edit_page_button": True,
    "analytics": {"google_analytics_id": "G-JJNSHE8EFK"},
    "external_links": [
        # {"name": "", "url": ""},
    ],
}
html_context = {
    "github_user": "dakk",
    "github_repo": "gweatherrouting",
    "github_version": "master",
    "doc_path": "docs/source/",
    "default_mode": "dark",
}
html_sidebars: Dict[str, Any] = {
    "index": [],
    "community": ["search-field.html", "sidebar-nav-bs.html", "twitter.html"],
}

# autosummary_imported_members = True
autosummary_generate = True
