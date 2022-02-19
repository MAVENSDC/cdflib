Working with XArray
===================

There are two functions for working with XArray DataSets, one for converting
a CDF to a DataSet, and one for going the other way.

These will attempt to determine any
`ISTP Compliance <https://spdf.gsfc.nasa.gov/istp_guide/istp_guide.html>`_ within
the file, and incorporate that into the Dataset object.

.. autofunction:: cdflib.cdf_to_xarray

.. autofunction:: cdflib.xarray_to_cdf
