CDF Reader Class
================

To begin accessing the data within a CDF file, first create a new CDF class.
This can be done with the following commands

>>> import cdflib
>>> cdf_file = cdflib.CDF('/path/to/cdf_file.cdf')

Then, you can call various functions on the variable.

For example:

>>> x = cdf_file.varget("NameOfVariable", startrec = 0, endrec = 150)

This command will return all data inside of the variable `Variable1`, from records 0 to 150.

Below is a list of the 8 different functions you can call.


cdf_info()
----------

Returns a dictionary that shows the basic CDF information. This information includes

* ``CDF`` the name of the CDF
* ``Version`` the version of the CDF
* ``Encoding`` the endianness of the CDF
* ``Majority`` the row/column majority
* ``zVariables`` a list of the names of the zVariables
* ``rVariables`` a list of the names of the rVariables
* ``Attributes`` a list of dictionary objects that contain attribute names and their scope, ex - {attribute_name : scope}
* ``Checksum`` the checksum indicator
* ``Num_rdim`` the number of dimensions, applicable only to rVariables
* ``rDim_sizes`` the dimensional sizes, applicable only to rVariables
* ``Compressed`` CDF is compressed at the file-level
* ``LeapSecondUpdated`` The last updated for the leap second table, if applicable


varinq(variable)
-----------------

Returns a dictionary that shows the basic variable information. This information includes

* ``Variable`` the name of the variable
* ``Num`` the variable number
* ``Var_Type`` the variable type: zVariable or rVariable
* ``Data_Type`` the variable's CDF data type
* ``Num_Elements`` the number of elements of the variable
* ``Num_Dims`` the dimensionality of the variable record
* ``Dim_Sizes`` the shape of the variable record
* ``Sparse`` the variable's record sparseness
* ``Last_Rec`` the maximum written record number (0-based)
* ``Dim_Vary`` the dimensional variance(s)
* ``Rec_Vary`` the record variance
* ``Pad`` the padded value if set
* ``Compress`` the GZIP compression level, 0 to 9. 0 if not compressed
* ``Block_Factor`` the blocking factor if the variable is compressed

attinq(attribute = None)
----------------------------

Returns a python dictionary of attribute information. If no attribute is provided, a list of all attributes is printed.

attget(attribute=None, entry=None)
--------------------------------------

Returns the value of the attribute at the entry number provided. A variable name can be used instead of its corresponding entry number. A dictionary is returned with the following defined keys.

- ``Item_Size`` the number of bytes for each entry value
- ``Num_items`` total number of values extracted
- ``Data_Type`` the CDF data type
- ``Data`` retrieved attribute data as a scalar value, a numpy array or a string


varattsget(variable = None, expand = None)
--------------------------------------------

Gets all variable attributes. Unlike attget, which returns a single attribute entry value, this function returns all of the variable attribute entries, in a ``dict()``.

If there is no entry found, ``None`` is returned. If no variable name is provided, a list of variables are printed.

If expand is entered with non-False, then each entry's data type is also returned in a list form as ``[entry, 'CDF_xxxx']``.

For attributes without any entries, they will also return with None value.


globalattsget(expand = False)
-----------------------------

Gets all global attributes. This function returns all of the global attribute entries, in a dictionary (in the form of 'attribute': {entry: value} pair) from a CDF.

If there is no entry found, None is returned. If expand is entered with non-False, then each entry's data type is also returned in a list form as ``[entry, 'CDF_xxxx']``.

For attributes without any entries, they will also return with None value.


varget()
-------------

>>> varget( variable = None, [epoch=None], [[starttime=None, endtime=None] | [startrec=0, endrec = None]], [,expand=True])

Returns the variable data.  Variable can be entered either a name or a variable number.

By default, it returns a ``numpy.ndarray`` or ``list()`` class object, depending on the data type, with the variable data and its specification.

If ``expand=True``, a dictionary is returned with the following defined keys for the output

- ``Rec_Ndim`` the dimension number of each variable record
- ``Rec_Shape`` the shape of the variable record dimensions
- ``Num_Records`` the total number of records
- ``Records_Returned`` the number of records retrieved
- ``Data_Type`` the CDF data type
- ``Data retrieved`` variable data
- ``Real_Records`` Record numbers for real data for sparse record variable in list

By default, the full variable data is returned.

To acquire only a portion of the data for a record-varying variable, either the time or record (0-based) range can be specified. ``epoch`` can be used to specify which time variable this variable depends on and is to be searched for the time range.
For the ISTP-compliant CDFs, the time variable will come from the attribute 'DEPEND_0' from this variable.  The function will automatically search for it thus no need to specify ``epoch``.

If either the start or end time is not specified, the possible minimum or maximum value for the specific epoch data type is assumed.  If either the start or end record is not specified, the range starts at 0 or/and ends at the last of the written data.

The start (and end) time should be presented in a list as:

- ``[year month day hour minute second millisec]`` for CDF_EPOCH
- ``[year month day hour minute second millisec microsec nanosec picosec]`` for CDF_EPOCH16
- ``[year month day hour minute second millisec microsec nanosec]`` for CDF_TIME_TT2000

If not enough time components are presented, only the last item can have the floating portion for the sub-time components.

.. note::
    CDF's CDF_EPOCH16 data type uses 2 8-byte doubles for each data value. In Python, each value is presented as a complex or numpy.complex128.

epochrange()
-------------

>>> epochrange( epoch, [starttime=None, endtime=None])

Get epoch range. Returns ``list()`` of the record numbers, representing the corresponding starting and ending records within the time range from the epoch data.
``None`` is returned if there is no data either written or found in the time range.

getVersion()
-------------

Shows the code version
