# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ObjectBox Python Bindings'
copyright = '2024, ObjectBox Ltd.'
author = 'ObjectBox Ltd.'
release = '4.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'autoapi.extension',
]
#    'sphinx.ext.inheritance_diagram',
#    'sphinx.ext.autodoc',

# -- autoapi configuration ---------------------------------------------------
# https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html

autoapi_dirs = ['../objectbox']
# autoapi_template_dir = ''
# autoapi_file_patterns = ['*.py', '*.pyi']
# autoapi_generate_api_docs = True
autoapi_options = [ 
    'members', 
    'inherited-members',
    'undoc-members', 
    # 'private-members', 
    # 'special-members', 
    # 'show-inheritance', 
    # 'show-inheritance-diagram',
    'show-module-summary', 
    'imported-members', 
]
# autoapi_ignore = ['*migrations']
# autoapi_root = 'autoapi'
autoapi_add_toctree_entry = False # default: True
autoapi_python_class_content = "both" # default: "class"
# autoapi_member_order = 'bysource' 
# autoapi_python_use_implicit_namespaces = False
# autoapi_own_page_level = 'module'

# Advanced:
# autoapi_keep_files = False

# Experimental:
autodoc_typehints = 'description'

only_top_level : bool = True

if only_top_level:
    def skip_submodules(app, what, name, obj, skip, options):
        if what == "module":
            skip = True
        elif what == "package" and name != "objectbox":
            skip = True
        return skip


    def setup(sphinx):
        sphinx.connect("autoapi-skip-member", skip_submodules)

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

# html_static_path = ['_static']
