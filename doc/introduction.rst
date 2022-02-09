Introduction
===================

What is cdflib?
------------------

cdflib is an effort to replicate the CDF libraries using a pure python implementation.  This means users do not need to install the CDF libraries.  

While this origally started as a way to read PDS-archive compliant CDF files, thanks to many contributors, it has grown to be able to handle every type of CDF file.  


What does it do?
-------------------

* Ability to read variables and attributes from CDF files
* Can write CDF files
* Can convert between CDF time types and other common time formats
* Can convert CDF files into XArray Dataset objects
* Can convert XArray Dataset objects into CDF files, attempting to maintain ISTP compliance 
