Working with XArray
===================

There are two functions for working with XArray Datasets, one for converting
a CDF to a DataSet, and one for going the other way. To use these you need
the ``xarray`` package installed.

These will attempt to determine any
`ISTP Compliance <https://spdf.gsfc.nasa.gov/istp_guide/istp_guide.html>`_, and incorporate that into the output.

.. autofunction:: cdflib.cdf_to_xarray

.. autofunction:: cdflib.xarray_to_cdf
