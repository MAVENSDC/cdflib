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

- ``CDF`` the name of the CDF
- ``Version`` the version of the CDF
- ``Encoding`` the endianness of the CDF
- ``Majority`` the row/column majority
- ``zVariables`` a list of the names of the zVariables
- ``rVariables`` a list of the names of the rVariables
- ``Attributes`` a list of dictionary objects that contain attribute names and their scope, ex - {attribute_name : scope}
- ``Checksum`` the checksum indicator
- ``Num_rdim`` the number of dimensions, applicable only to rVariables
- ``rDim_sizes`` the dimensional sizes, applicable only to rVariables
- ``Compressed`` CDF is compressed at the file-level
- ``LeapSecondUpdated`` The last updated for the leap second table, if applicable


varinq(variable)
--------

Returns a dictionary that shows the basic variable information. This information includes

- ``Variable`` the name of the variable
- ``Num`` the variable number
- ``Var_Type`` the variable type: zVariable or rVariable
- ``Data_Type`` the variable's CDF data type
- ``Num_Elements`` the number of elements of the variable
- ``Num_Dims`` the dimensionality of the variable record
- ``Dim_Sizes`` the shape of the variable record
- ``Sparse`` the variable's record sparseness
- ``Last_Rec`` the maximum written record number (0-based)
- ``Dim_Vary`` the dimensional variance(s)
- ``Rec_Vary`` the record variance
- ``Pad`` the padded value if set
- ``Compress`` the GZIP compression level, 0 to 9. 0 if not compressed
- ``Block_Factor`` the blocking factor if the variable is compressed

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




epochrange()
-------------

>>> epochrange( epoch, [starttime=None, endtime=None])


getVersion()
-------------

Shows the code version