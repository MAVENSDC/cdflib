This is a python script to read CDF V3 files without needing to install the CDF NASA library.  

##########
CDF Class
##########


	import pds_cdf
	swea_cdf_file = pds_cdf.CDF('/path/to/swea_file.cdf')
	
Then, you can call the following commands on the variable below.  For example::

	x = swea_cdf_file.varget("NameOfVariable", startrec = 0, endrec = 150)

cdf_info()
=============
	
Returns a dictionary that shows the basic CDF information. 
This information includes
		+---------------+--------------------------------------------------------------------------------+
		| ['CDF']       | the name of the CDF                                                            |
		+---------------+--------------------------------------------------------------------------------+
		| ['Version']   | the version of the CDF                                                         |
		+---------------+--------------------------------------------------------------------------------+
		| ['Encoding']  | the endianness of the CDF                                                      |
		+---------------+--------------------------------------------------------------------------------+
		| ['Majority']  | the row/column majority                                                        |
		+---------------+--------------------------------------------------------------------------------+
		| ['zVariables']| the dictionary for zVariable numbers and their corresponding names             |
		+---------------+--------------------------------------------------------------------------------+
		| ['rVariables']| the dictionary for rVariable numbers and their corresponding names             |
		+---------------+--------------------------------------------------------------------------------+
		| ['Attributes']| the dictionary for attribute numbers and their corresponding names and scopes  |
		+---------------+--------------------------------------------------------------------------------+
		  

varinq(variable)
=============
	
Returns a dictionary that shows the basic variable information.  
This information includes
		+-----------------+--------------------------------------------------------------------------------+
		| ['Variable']    | the name of the variable                                                       |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Num']         | the variable number                                                            |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Var_Type']    | the variable type: zVariable or rVariable                                      |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Data_Type']   | the variable's CDF data type                                                   |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Num_Elements']| the number of elements of the variable                                         |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Num_Dims']    | the dimensionality of the variable record                                      |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Dim_Sizes']   | the shape of the variable record                                               |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Sparse']      | the variable's record sparseness                                               |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Last_Rec']    | the maximum written record number (0-based)                                    |
		+-----------------+--------------------------------------------------------------------------------+


attinq( attribute = None)
=============
	
Returns a python dictionary of attribute information.  If no attribute is provided, a list of all attributes is printed.  
                   
attget( attribute = None, entry_num = None )
=============
	
Returns the value of the attribute at the entry number provided. A variable name can be used instead of its corresponding 
entry number. A dictionary is returned with the following defined keys

		+-----------------+--------------------------------------------------------------------------------+
		| ['Item_Size']   | the number of bytes for each entry value                                       |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Num_Items']   | total number of values extracted                                               |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Data_Type']   | the CDF data type                                                              |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Data']        | retrieved attribute data as a scalar value, a numpy array or a string          |
		+-----------------+--------------------------------------------------------------------------------+

varattsget(variable = None)
=============
	
Gets all variable attributes. 
Unlike attget, which returns a single attribute entry value,
this function returns all of the variable attribute entries,
in a dictionary (in the form of 'attribute': value pair) for
a variable. If there is no entry found, None is returned.
If no variable name is provided, a list of variables are printed.  
			   
globalattsget()
=============
	
Gets all global attributes.  
This function returns all of the global attribute entries,
in a dictionary (in the form of 'attribute': {entry: value}
pair) from a CDF. If there is no entry found, None is
returned.
                   
varget( variable = None, [epoch=None], [[starttime=None, endtime=None] | [startrec=0, endrec = None]], [,expand=True])
=============
Returns the variable data. Variable can be entered either
a name or a variable number. By default, it returns a
'numpy.ndarray' or 'list' class object, depending on the
data type, with the variable data and its specification.

If "expand" is set as True, a dictionary is returned
with the following defined keys for the output
		+-----------------+--------------------------------------------------------------------------------+
		| ['Rec_Ndim']    | the dimension number of each variable record                                   |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Rec_Shape']   | the shape of the variable record dimensions                                    |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Num_Records'] | the number of the retrieved records                                            |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Data_Type']   | the CDF data type                                                              |
		+-----------------+--------------------------------------------------------------------------------+
		| ['Data']        | retrieved variable data                                                        |
		+-----------------+--------------------------------------------------------------------------------+
		
By default, the full variable data is returned. To acquire
only a portion of the data for a record-varying variable,
either the time or record (0-based) range can be specified.
'epoch' can be used to specify which time variable this 
variable depends on and is to be searched for the time range.
For the ISTP-compliant CDFs, the time variable will come from
the attribute 'DEPEND_0' from this variable. The function will
automatically search for it thus no need to specify 'epoch'.
If either the start or end time is not specified,
the possible minimum or maximum value for the specific epoch
data type is assumed. If either the start or end record is not
specified, the range starts at 0 or/and ends at the last of the
written data.  

Note: CDF's CDF_EPOCH16 data type uses 2 8-byte doubles for each data value.  In Python, each value is presented as a complex or numpy.complex128.

epochrange( epoch, [starttime=None, endtime=None])
=============
Get epoch range. 
Returns a list of the record numbers, representing the
corresponding starting and ending records within the time
range from the epoch data. A None is returned if there is no
data either written or found in the time range.

					
##########
CDF Epoch 
##########

Importing cdflib also imports the module CDFepoch, which handles CDF-based epochs.

There are three (3) epoch data types in CDD: CDF_EPOCH, CDF_EPOCH16 and 
CDF_TIME_TT2000. 

- CDF_EPOCH is milliseconds since Year 0. 

- CDF_EPOCH16 is picoseconds since Year 0. 

- CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with leap seconds. 

CDF_EPOCH is a single double(as float in Python), CDF_EPOCH16 is 2-doubles (as complex in Python),
and TT2000 is 8-byte integer (as int in Python). In Numpy, they are np.float64, np.complex128 and np.int64, respectively. 
All these epoch values can come from from CDF.varget function.

Four main functions are provided 

encode (epochs, iso_8601=False)
=============

Encodes the epoch(s) into UTC string(s).
	
	For CDF_EPOCH: 
				The input should be either a float or list of floats
				(in numpy, a np.float64 or a np.ndarray of np.float64)
				Each epoch is encoded, by default to a ISO 8601 form:
				2004-05-13T15:08:11.022 
				Or, if iso_8601 is set to False,
				13-May-2004 15:08:11.022
	For CDF_EPOCH16: 
				  The input should be either a complex or list of 
				  complex(in numpy, a np.complex128 or a np.ndarray of np.complex128)
				  Each epoch is encoded, by default to a ISO 8601 form:
				  2004-05-13T15:08:11.022033044055 
				  Or, if iso_8601 is set to False,
				  13-May-2004 15:08:11.022.033.044.055
	For TT2000: 
			 The input should be either a int or list of ints
			 (in numpy, a np.int64 or a np.ndarray of np.int64)
			 Each epoch is encoded, by default to a ISO 8601 form:
			 2008-02-02T06:08:10.10.012014016
			 Or, if iso_8601 is set to False,
			 02-Feb-2008 06:08:10.012.014.016

breakdown (epochs, to_np=False)
=============

Breaks down the epoch(s) into UTC components. 

	For CDF_EPOCH: 
				they are 7 date/time components: year, month, day,
				hour, minute, second, and millisecond
	For CDF_EPOCH16: 
				  they are 10 date/time components: year, month, day,
				  hour, minute, second, and millisecond, microsecond,
				  nanosecond, and picosecond.
	For TT2000: 
			 they are 9 date/time components: year, month, day,
			 hour, minute, second, millisecond, microsecond, 
			 nanosecond.
			 
Specify to_np to True, if the result should be in numpy array.

compute[_epoch/_epoch16/_tt200] (datetimes, to_np=False)
=============

Computes the provided date/time components into CDF epoch value(s).

	For CDF_EPOCH: 
		For computing into CDF_EPOCH value, each date/time elements should 
		have exactly seven (7) components, as year, month, day, hour, minute,
		second and millisecond, in a list. For example:
		[[2017,1,1,1,1,1,111],[2017,2,2,2,2,2,222]]
		Or, call function compute_epoch directly, instead, with at least three
		(3) first (up to seven) components. The last component, if
		not the 7th, can be a float that can have a fraction of the unit.

	For CDF_EPOCH16:
		They should have exactly ten (10) components, as year, 
		month, day, hour, minute, second, millisecond, microsecond, nanosecond 
		and picosecond, in a list. For example:
		[[2017,1,1,1,1,1,123,456,789,999],[2017,2,2,2,2,2,987,654,321,999]]
		Or, call function compute_epoch directly, instead, with at least three
		(3) first (up to ten) components. The last component, if
		not the 10th, can be a float that can have a fraction of the unit.

	For TT2000:
		Each TT2000 typed date/time should have exactly nine (9) components, as 
		year, month, day, hour, minute, second, millisecond, microsecond, 
		and nanosecond, in a list.  For example:
		[[2017,1,1,1,1,1,123,456,789],[2017,2,2,2,2,2,987,654,321]]
		Or, call function compute_tt2000 directly, instead, with at least three
		(3) first (up to nine) components. The last component, if
		not the 9th, can be a float that can have a fraction of the unit.

Specify to_np to True, if the result should be in numpy class.

findepochrange (epochs, starttime=None, endtime=None)
=============

Finds the record range within the start and end time from values 
of a CDF epoch data type. It returns a list of record numbers. 
If the start time is not provided, then it is 
assumed to be the minimum possible value. If the end time is not 
provided, then the maximum possible value is assumed. The epoch is
assumed to be in the chronological order. The start and end times
should have the proper number of date/time components, corresponding
to the epoch's data type.


Authors: Bryan Harter, Michael Liu
