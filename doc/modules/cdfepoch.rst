**********************
CDF Time Conversions
**********************

There are three (3) unique epoch data types in CDF: CDF_EPOCH, CDF_EPOCH16 and CDF_TIME_TT2000.

- CDF_EPOCH is milliseconds since Year 0.
- CDF_EPOCH16 is picoseconds since Year 0.
- CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with leap seconds.

The following two classes contain functions to convert those times into formats that are in more standard use.


.. automodapi:: cdflib.epochs
    :no-inheritance-diagram:

.. automodapi:: cdflib.epochs_astropy
    :no-inheritance-diagram:
