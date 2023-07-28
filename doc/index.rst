cdflib
======

A python package to read CDF files without needing to install the CDF NASA library.

**Last Built**: |today| | **Version**: |version| | **Source**: `github`_ | **Archive**: `zenodo`_.

.. _github: https://github.com/MAVENSDC/cdflib
.. _zenodo: https://zenodo.org/record/4746617#.Y5NfWXbMKF4

Installing
----------
cdflib requires python 3 and numpy. To install run

.. code::
   bash

   python3 -m pip install cdflib


What is cdflib?
------------------

cdflib is an effort to replicate the CDF libraries using a pure python implementation.
This means users do not need to install the `CDF NASA libraries <https://cdf.gsfc.nasa.gov/>`_.

The only module you need to install is ``numpy``, but there are a few things you can do with ``astropy`` and ``xarray``.

While this originally started as a way to read PDS-archive compliant CDF files, thanks to many contributors, it has grown to be able to handle every type of CDF file.

What can cdflib do?
-------------------

- Ability to read variables and attributes from CDF files (see ``CDF Reader Class``)
- Writes CDF version 3 files (see ``CDF Writer Class``)
- Can convert between CDF time types (EPOCH/EPOCH16/TT2000) to other common time formats (see ``CDF Time Conversions``)
- Can convert CDF files into XArray Dataset objects and vice versa, attempting to maintain ISTP compliance (see ``Working with XArray``)

.. note::
    While we try to simplify things in this documentation, the full API description of each module can be found in the ``API Reference`` section


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   modules/index
   changelog
   development
