A Collection of Packages
++++++++++++++++++++++++

This is a collection of Python packages containing utilities I frequently use
in various projects.

Minimum Python Version
======================

- `cached-property` - 3.7 and up
- `make-release` - 3.7 and up

Package Installation
====================

Include package(s) in your project's ``pyproject.toml``, ``requirements.txt``,
or ``setup.py``. For example, if your project uses Poetry::

    # pyproject.toml
    [tool.poetry.dependencies]
    python = "^3.7"
    "com.wyattbaldwin.xyz" = "^1.0"

.. note: TOML requires double quotes around keys that contain dots.

Or use ``pip install``::

    pip install com.wyattbaldwin.xyz

Development
===========

- Clone the ``com.wyattbaldwin`` repository
- Install Poetry_
- ``cd`` into a package directory
- Run ``poetry install``
- Activate the virtualenv created by Poetry
- Run ``run-tests``

.. _Poetry: https://python-poetry.org/docs/#installation
