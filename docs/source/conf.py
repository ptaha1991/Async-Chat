# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
# sys.path.insert(0, os.path.abspath('.'))
#
# path = os.path.dirname(os.path.abspath('../../server.py'))
# sys.path.insert(0, path)

sys.path.insert(0, "/Users/nataliapisarova/Desktop/REPO/async/Async-chat/Async-Chat")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Async-chat'
copyright = '2023, Natalia'
author = 'Natalia'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
