**********************
CDF Time Conversions
**********************

There are three (3) unique epoch data types in CDF: CDF_EPOCH, CDF_EPOCH16 and CDF_TIME_TT2000.

- CDF_EPOCH is milliseconds since Year 0.
- CDF_EPOCH16 is picoseconds since Year 0.
- CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with leap seconds.

The following two classes contain functions to convert those times into formats that are in more standard use.


Epochs Class
============

There are 5 main functions in this module to help with time conversions

encode (epochs, iso_8601=False)
------------------------------------------------------------------------------

Encodes the epoch(s) as read from a CDF file into UTC string(s).  Returns a list of strings.

- CDF_EPOCH: The input should be either a float or list of floats (in numpy, a np.float64 or a np.ndarray of np.float64) Each epoch is encoded, by default to a ISO 8601 form: 2004-05-13T15:08:11.022 Or, if iso_8601 is set to False, 13-May-2004 15:08:11.022
- CDF_EPOCH16: The input should be either a complex or list of complex(in numpy, a np.complex128 or a np.ndarray of np.complex128) Each epoch is encoded, by default to a ISO 8601 form: 2004-05-13T15:08:11.022033044055 Or, if iso_8601 is set to False, 13-May-2004 15:08:11.022.033.044.055
- TT2000: The input should be either a int or list of ints (in numpy, a np.int64 or a np.ndarray of np.int64) Each epoch is encoded, by default to a ISO 8601 form: 2008-02-02T06:08:10.10.012014016 Or, if iso_8601 is set to False, 02-Feb-2008 06:08:10.012.014.016


unixtime (epochs, to_np=False)
------------------------------------------------------------------------------

Encodes the epoch(s) as read from a CDF file into a list of seconds after 1970-01-01. Precision is only kept to the nearest microsecond.

If ``to_np=True``, then the values will be returned in a numpy array.


breakdown (epochs, to_np=False)
------------------------------------------------------------------------------

Breaks down the epoch(s) as read from a CDF file into UTC components.  This takes the form of a list, or a list of lists.

- CDF_EPOCH: they are 7 date/time components: year, month, day, hour, minute, second, and millisecond
- CDF_EPOCH16: they are 10 date/time components: year, month, day, hour, minute, second, and millisecond, microsecond, nanosecond, and picosecond.
- TT2000: they are 9 date/time components: year, month, day, hour, minute, second, millisecond, microsecond, nanosecond.

Specify ``to_np=True``, if the result should be in numpy array.

compute[_epoch/_epoch16/_tt200] (datetimes, to_np=False)
------------------------------------------------------------------------------

Computes the provided date/time components into CDF epoch value(s).

For CDF_EPOCH: For computing into CDF_EPOCH value, each date/time elements should have exactly seven (7) components, as year, month, day, hour, minute, second and millisecond, in a list. For example:

>>> [[2017,1,1,1,1,1,111],[2017,2,2,2,2,2,222]]

Or, call function compute_epoch directly, instead, with at least three (3) first (up to seven) components. The last component, if not the 7th, can be a float that can have a fraction of the unit.

For CDF_EPOCH16: They should have exactly ten (10) components, as year, month, day, hour, minute, second, millisecond, microsecond, nanosecond and picosecond, in a list. For example:

>>> [[2017,1,1,1,1,1,123,456,789,999],[2017,2,2,2,2,2,987,654,321,999]]

Or, call function compute_epoch directly, instead, with at least three (3) first (up to ten) components. The last component, if not the 10th, can be a float that can have a fraction of the unit.

For TT2000: Each TT2000 typed date/time should have exactly nine (9) components, as year, month, day, hour, minute, second, millisecond, microsecond, and nanosecond, in a list. For example:

>>> [[2017,1,1,1,1,1,123,456,789],[2017,2,2,2,2,2,987,654,321]]

Or, call function compute_tt2000 directly, instead, with at least three (3) first (up to nine) components. The last component, if not the 9th, can be a float that can have a fraction of the unit.

Specify ``to_np=True``, if the result should be in numpy class.


parse (datetimes, to_np=False)
-------------------------------

Parses the provided date/time string(s) into CDF epoch value(s).

- CDF_EPOCH: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.xxx' or 'yyyy-mm-ddThh:mm:ss.xxx' (in iso_8601). The string is the output from encode function.
- CDF_EPOCH16: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn.ppp' or 'yyyy-mm-ddThh:mm:ss.mmmuuunnnppp' (in iso_8601). The string is the output from encode function.
- TT2000: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn' or 'yyyy-mm-ddThh:mm:ss.mmmuuunnn' (in iso_8601). The string is the output from encode function.


Specify to_``np=True``, if the result should be in numpy class.


findepochrange (epochs, starttime=None, endtime=None)
-------------------------------------------------------

Finds the record range within the start and end time from values of a CDF epoch data type. It returns a list of record numbers. If the start time is not provided, then it is assumed to be the minimum possible value. If the end time is not provided, then the maximum possible value is assumed. The epoch is assumed to be in the chronological order. The start and end times should have the proper number of date/time components, corresponding to the epoch's data type.

The start/end times should be in either be in epoch units, or in the list format described in "compute_epoch/epoch16/tt2000" section.


getVersion ()
-------------

Shows the code version.


getLeapSecondLastUpdated ()
----------------------------

Shows the latest date a leap second was added to the leap second table.


Epochs Astropy
==============

If you have astropy installed, importing cdflib also imports the module cdflib.cdfastropy, which contains all of the functionality of the above module, but uses the Astropy Time class for all conversions. It can be used in the same way as the above module:

>>> import cdflib
>>> epoch_time = cdflib.cdfastropy.compute_epoch([2017,1,1,1,1,1,111])

Additionally, and perhaps most importantly, there is an additonal function that converts CDF_EPOCH/EPOCH16/TT2000 times to the Astropy Time class:


convert_to_astropy (epochs, format=None)
--------------------------------------------
Converts the epoch(s) into Astropy Time(s).

- CDF_EPOCH: The input should be either a float or list of floats (in numpy, a np.float64 or a np.ndarray of np.float64). If you'd like to ignore the input type and convert to CDF_EPOCH directly, specify format='cdf_epoch' when you call the function.
- CDF_EPOCH16: The input should be either a complex or list of complex(in numpy, a np.complex128 or a np.ndarray of np.complex128). If you'd like to ignore the input type and convert to CDF_EPOCH directly, specify format='cdf_epoch16' when you call the function.
- TT2000: The input should be either a int or list of ints (in numpy, a np.int64 or a np.ndarray of np.int64). If you'd like to ignore the input type and convert to CDF_EPOCH directly, specify format='cdf_tt2000' when you call the function.

For more information about Astropy Times and all the functionality it contains, take a look at the astropy documentation

https://docs.astropy.org/en/stable/time/
