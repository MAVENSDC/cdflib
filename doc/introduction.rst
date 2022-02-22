Introduction
===================

What is cdflib?
------------------

cdflib is an effort to replicate the CDF libraries using a pure python implementation.  This means users do not need to install the `CDF NASA libraries <https://cdf.gsfc.nasa.gov/>`_.  

The only module you need to install is numpy, but there are a few things you can do with astropy and xarray.  

While this origally started as a way to read PDS-archive compliant CDF files, thanks to many contributors, it has grown to be able to handle every type of CDF file.  


What can cdflib do?
-------------------

* Ability to read variables and attributes from CDF files (see `modules\cdfread`_)
* Writes CDF version 3 files
* Can convert between CDF time types (EPOCH/EPOCH16/TT2000) to other common time formats
* Can convert CDF files into XArray Dataset objects
* Can convert XArray Dataset objects into CDF files, attempting to maintain ISTP compliance



