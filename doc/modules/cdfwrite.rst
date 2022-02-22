CDF Writer Class
=================


CDF (path, cdf_spec=None, delete=False)
----------------------------------------
Creates an empty CDF file. path is the path name of the CDF (with or without .cdf extension).

``cdf_spec`` is the optional specification of the CDF file, in the form of a dictionary. The dictionary can have the following values:

- ``Majority`` 'row_major' or 'column_major', or its corresponding value. Default is 'column_major'.
- ``Encoding`` Data encoding scheme. See the CDF documentation about the valid values. Can be in string or its numeric corresponding value. Default is 'host'.
- ``Checksum`` Whether to set the data validation upon file creation. The default is False.
- ``rDim_sizes`` The dimensional sizes, applicable only to rVariables.
- ``Compressed`` Whether to compress the CDF at the file level. A value of 0-9 or True/False, the default is 0/False.


write_globalattrs (globalAttrs)
--------------------------------------

Writes the global attributes. ``globalAttrs`` is a dictionary that has global attribute name(s) and their value(s) pair(s). The value(s) is a dictionary of entry number and value pair(s). For example:

>>> globalAttrs={}
>>> globalAttrs['Global1']={0: 'Global Value 1'}
>>> globalAttrs['Global2']={0: 'Global Value 2'}

For a non-string value, use a list with the value and its CDF data type. For example:

>>> globalAttrs['Global3']={0: [12, 'cdf_int4']}
>>> globalAttrs['Global4']={0: [12.34, 'cdf_double']}

If the data type is not provided, a corresponding CDF data type is assumed:

>>> globalAttrs['Global3']={0: 12}     as 'cdf_int4'
>>> globalAttrs['Global4']={0: 12.34}  as 'cdf_double'

CDF allows multi-values for non-string data for an attribute:

>>> globalAttrs['Global5']={0: [[12.34,21.43], 'cdf_double']}

For multi-entries from a global variable, they should be presented in this form:

>>> GA6={}
>>> GA6[0]='abcd'
>>> GA6[1]=[12, 'cdf_int2']
>>> GA6[2]=[12.5, 'cdf_float']
>>> GA6[3]=[[0,1,2], 'cdf_int8']
>>> globalAttrs['Global6']=GA6
>>> ....
>>> f.write_globalattrs(globalAttrs)

write_variableattrs (variableAttrs)
--------------------------------------

Writes a variable's attributes, provided the variable already exists. ``variableAttrs`` is a dictionary that has variable attribute name and its entry value pair(s). The entry value is also a dictionary of variable id and value pair(s). Variable id can be the variable name or its id number in the file. Use write_var function if the variable does not exist. For example:

>>> variableAttrs={}
>>> entries_1={}
>>> entries_1['var_name_1'] = 'abcd'
>>> entries_1['var_name_2'] = [12, 'cdf_int4']
>>> ....
>>> variableAttrs['attr_name_1'] = entries_1
>>> entries_2={}
>>> entries_2['var_name_1'] = 'xyz'
>>> entries_2['var_name_2'] = [[12, 34], 'cdf_int4']
>>> ....
>>> variableAttrs['attr_name_2']=entries_2
>>> ....
>>> f.write_variableattrs(variableAttrs)


write_var (var_spec, var_attrs=None, var_data=None)
-----------------------------------------------------

Writes a variable, along with variable attributes and data. ``var_spec`` is a dictionary that contains the specifications of the variable. The required/optional keys for creating a variable:

Required keys:

- ``Variable`` The name of the variable
- ``Data_Type`` the CDF data type
- ``Num_Elements`` The number of elements. Always 1 the for numeric type. The char length for string type.
- ``Rec_Vary`` The dimensional sizes, applicable only to rVariables.

For zVariables:

- ``Dim_Sizes`` The dimensional sizes for zVariables only. Use [] for 0-dimension. Each and every dimension is varying for zVariables.

For rVariables:

- ``Dims_Vary`` The dimensional variances for rVariables only.

Optional Keys:

- ``Var_Type`` Whether the variable is a zVariable or rVariable. Valid values: "zVariable" and "rVariable". The default is "zVariable".
- ``Sparse`` Whether the variable has sparse records. Valid values are "no_sparse", "pad_sparse", and "prev_sparse". The default is 'no_sparse'.
- ``Compress`` Set the gzip compression level (0 to 9), 0 for no compression. The default is to compress with level 6 (done only if the compressed data is less than the uncompressed data).
- ``Block_Factor`` The blocking factor, the number of records in a chunk when the variable is compressed.
- ``Pad`` The padded value (in bytes, numpy.ndarray or string)

``var_attrs`` is a dictionary, with {attribute:value} pairs. The attribute is the name of a variable attribute. The value can have its data type specified for the numeric data. If not, based on Python's type, a corresponding CDF type is assumed: CDF_INT4 for int, CDF_DOUBLE for float, CDF_EPOCH16 for complex and and CDF_INT8 for long. For example:

>>> var_attrs= { 'attr1': 'value1', 'attr2': 12.45, 'attr3': [3,4,5], .....} -or- var_attrs= { 'attr1': 'value1', 'attr2': [12.45, 'CDF_DOUBLE'], 'attr3': [[3,4,5], 'CDF_INT4'], ..... }

``var_data`` is the data for the variable. If the variable is a regular variable without sparse records, it must be in a single structure of bytes, or numpy.ndarray for numeric variable, or str or list of strs for string variable. If the variable has sparse records, var_data should be presented in a list/tuple with two elements, the first being a list/tuple that contains the physical record number(s), the second being the variable data in bytes, numpy.ndarray, or a list of strings. Variable data can have just physical records' data (with the same number of records as the first element) or have data from both physical records and virtual records (which with filled data). The var_data has the form:

.. note::
    The attribute entry value for the CDF epoch data type, CDF_EPOCH, CDF_EPOCH16 or CDF_TIME_TT2000, can be presented in either a numeric form, or an encoded string form. For numeric, the CDF_EPOCH data is 8-byte float, CDF_EPOCH16 16-byte complex and CDF_TIME_TT2000 8-byte long. The default encoded string for the epoch data should have this form:

    >>> CDF_EPOCH: 'dd-mon-year hh:mm:ss.mmm'
    >>> CDF_EPOCH16: 'dd-mon-year hh:mm:ss.mmm.uuu.nnn.ppp'
    >>> CDF_TIME_TT2000: 'year-mm-ddThh:mm:ss.mmmuuunnn'

getVersion()
------------
Shows the code version and modified date.


Sample Usage
------------

>>> import cdfwrite
>>> import cdfread
>>> import numpy as np
>>>
>>> cdf_master = cdfread.CDF('/path/to/master_file.cdf')
>>> if (cdf_master.file != None):
>>> # Get the cdf's specification
>>> info=cdf_master.cdf_info()
>>> cdf_file=cdfwrite.CDF('/path/to/swea_file.cdf',cdf_spec=info,delete=True)
>>> if (cdf_file.file == None):
>>>     cdf_master.close()
>>>     raise OSError('Problem writing file.... Stop')
>>>
>>> # Get the global attributes
>>> globalaAttrs=cdf_master.globalattsget(expand=True)
>>> # Write the global attributes
>>> cdf_file.write_globalattrs(globalaAttrs)
>>> zvars=info['zVariables']
>>> print('no of zvars=',len(zvars))
>>> # Loop thru all the zVariables
>>> for x in range (0, len(zvars)):
>>>     # Get the variable's specification
>>>     varinfo=cdf_master.varinq(zvars[x])
>>>     #print('Z =============>',x,': ', varinfo['Variable'])
>>>     # Get the variable's attributes
>>>     varattrs=cdf_master.varattsget(zvars[x], expand=True)
>>>     if (varinfo['Sparse'].lower() == 'no_sparse'):
>>>         # A variable with no sparse records... get the variable data
>>>         vardata=.......
>>>         # Create the zVariable, write out the attributes and data
>>>         cdf_file.write_var(varinfo, var_attrs=varattrs, var_data=vardata)
>>>     else:
>>>         # A variable with sparse records...
>>>         # data is in this form [physical_record_numbers, data_values]
>>>         # physical_record_numbers (0-based) contains the real record
>>>         # numbers. For example, a variable has only 3 physical records
>>>         # at [0, 5, 10]:
>>>         varrecs=[0,5,10]
>>>         # data_values could contain only the physical records' data or
>>>         # both the physical and virtual records' data.
>>>         # For example, a float variable of 1-D with 3 elements with only
>>>         # 3 physical records at [0,5,10]:
>>>         # vardata = [[  5.55000000e+01, -1.00000002e+30,  6.65999985e+01],
>>>         #            [  6.66659973e+02,  7.77770020e+02,  8.88880005e+02],
>>>         #            [  2.00500000e+02,  2.10600006e+02,  2.20699997e+02]]
>>>         # Or, with virtual record data embedded in the data:
>>>         # vardata = [[  5.55000000e+01, -1.00000002e+30,  6.65999985e+01],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [  6.66659973e+02,  7.77770020e+02,  8.88880005e+02],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
>>>         #            [  2.00500000e+02,  2.10600006e+02,  2.20699997e+02]]
>>>         # Records 1, 2, 3, 4, 6, 7, 8, 9 are all virtual records with pad
>>>         # data (variable defined with 'pad_sparse').
>>>         vardata=np.asarray([.,.,.,..])
>>>         # Create the zVariable, and optionally write out the attributes
>>>         # and data
>>>         cdf_file.write_var(varinfo, var_attrs=varattrs,
>>>                    var_data=[varrecs,vardata])
>>>    rvars=info['rVariables']
>>>    print('no of rvars=',len(rvars))
>>>    # Loop thru all the rVariables
>>>    for x in range (0, len(rvars)):
>>>        varinfo=cdf_master.varinq(rvars[x])
>>>        print('R =============>',x,': ', varinfo['Variable'])
>>>        varattrs=cdf_master.varattsget(rvars[x], expand=True)
>>>        if (varinfo['Sparse'].lower() == 'no_sparse'):
>>>            vardata=.......
>>>            # Create the rVariable, write out the attributes and data
>>>            cdf_file.write_var(varinfo, var_attrs=varattrs, var_data=vardata)
>>>        else:
>>>            varrecs=[.,.,.,..]
>>>            vardata=np.asarray([.,.,.,..])
>>>            cdf_file.write_var(varinfo, var_attrs=varattrs,
>>>                       var_data=[varrecs,vardata])
>>> cdf_master.close()
>>> cdf_file.close()


