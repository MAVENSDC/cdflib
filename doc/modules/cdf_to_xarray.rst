cdf_to_xarray
=============

cdf_to_xarray function
-----------------------

This module is comprised of a single function which takes a CDF file and converts it to an XArray Dataset object.    

This will attempt to determine any `ISTP Compliance <https://spdf.gsfc.nasa.gov/istp_guide/istp_guide.html>`_ within the file, and incorporate that into the Dataset object.

.. autofunction:: cdflib.cdf_to_xarray