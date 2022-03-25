[![Actions Status](https://github.com/MAVENSDC/cdflib/workflows/ci/badge.svg)](https://github.com/MAVENSDC/cdflib/actions)
[![codecov](https://codecov.io/gh/MAVENSDC/cdflib/branch/master/graph/badge.svg?token=IJ6moGc40e)](https://codecov.io/gh/MAVENSDC/cdflib)
[![DOI](https://zenodo.org/badge/102912691.svg)](https://zenodo.org/badge/latestdoi/102912691)
[![Documentation Status](https://readthedocs.org/projects/cdflib/badge/?version=latest)](https://cdflib.readthedocs.io/en/latest/?badge=latest)

# CDFlib

`cdflib` is a python module to read/write CDF (Common Data Format `.cdf`) files without needing to install the
[CDF NASA library](https://cdf.gsfc.nasa.gov/).

Python &ge; 3.6 is required.
This module uses only Numpy, no complicated prereqs.

## Install

To install, open up your terminal/command prompt, and type:
```sh
pip install cdflib
```
There are two different CDF classes: a cdf reader, and a cdf writer.

Currently, you cannot simultaneously read and write to the same file.
Future implementations, however, will unify these two classes.

## CDF Reader Class

To begin accessing the data within a CDF file, first create a new CDF class.
This can be done with the following commands

```python
import cdflib

cdf_file = cdflib.CDF('/path/to/cdf_file.cdf')
```

Then, you can call various functions on the variable.
For example:

```python
x = cdf_file.varget("NameOfVariable", startrec = 0, endrec = 150)
```

This command will return all data inside of the variable `Variable1`, from records 0 to 150.
Below is a list of the 8 different functions you can call.

### cdf_info()

Returns a dictionary that shows the basic CDF information.
This information includes

* `CDF` the name of the CDF
* `Version` the version of the CDF
* `Encoding` the endianness of the CDF
* `Majority` the row/column majority
* `zVariables` a list of the names of the zVariables
* `rVariables` a list of the names of the rVariables
* `Attributes` a list of dictionary objects that contain attribute names and their scope, ex - {attribute_name : scope}
* `Checksum` the checksum indicator
* `Num_rdim` the number of dimensions, applicable only to rVariables
* `rDim_sizes` the dimensional sizes, applicable only to rVariables
* `Compressed` CDF is compressed at the file-level
* `LeapSecondUpdated` The last updated for the leap second table, if applicable

### varinq(variable)

Returns a dictionary that shows the basic variable information.
This information includes

* `Variable` the name of the variable
* `Num` the variable number
* `Var_Type` the variable type: zVariable or rVariable
* `Data_Type` the variable's CDF data type
* `Num_Elements']| the number of elements of the variable
* `Num_Dims` the dimensionality of the variable record
* `Dim_Sizes` the shape of the variable record
* `Sparse` the variable's record sparseness
* `Last_Rec` the maximum written record number (0-based)
* `Dim_Vary` the dimensional variance(s)
* `Rec_Vary` the record variance
* `Pad` the padded value if set
* `Compress` the GZIP compression level, 0 to 9.  0 if not compressed
* `Block_Factor']| the blocking factor if the variable is compressed

### attinq( attribute = None)

Returns a python dictionary of attribute information.
If no attribute is
provided, a list of all attributes is printed.

### attget( attribute = None, entry = None )

Returns the value of the attribute at the entry number provided. A
variable name can be used instead of its corresponding entry number. A
dictionary is returned with the following defined keys

* `Item_Size` the number of bytes for each entry value
* `Num_Items` total number of values extracted
* `Data_Type` the CDF data type
* `Data` retrieved attribute data as a scalar value, a numpy array or a string

### varattsget(variable = None, expand = False)

Gets all variable attributes.
Unlike attget, which returns a single attribute entry value, this function returns all of the variable attribute entries, in a `dict()`.
If there is no entry found, `None` is returned. If
no variable name is provided, a list of variables are printed. If expand
is entered with non-False, then each entry's data type is also returned
in a list form as `[entry, 'CDF_xxxx']`. For attributes without any
entries, they will also return with None value.

### globalattsget(expand = False)

Gets all global attributes. This function returns all of the global
attribute entries, in a dictionary (in the form of 'attribute':
{entry: value} pair) from a CDF. If there is no entry found, None is
returned. If expand is entered with non-False, then each entry's data
type is also returned in a list form as `[entry, 'CDF_xxxx']`.
For attributes without any entries, they will also return with None value.

### varget()

```python
varget( variable = None, [epoch=None], [[starttime=None, endtime=None] | [startrec=0, endrec = None]], [,expand=True])
```

Returns the variable data. Variable can be entered either
a name or a variable number. By default, it returns a `numpy.ndarray`
or `list()` class object, depending on the data type, with the variable
data and its specification.

If `expand=True`, a dictionary is returned with the
following defined keys for the output

* `Rec_Ndim` the dimension number of each variable record
* `Rec_Shape` the shape of the variable record dimensions
* `Num_Records` the total number of records
* `Records_Returned` the number of records retrieved
* `Data_Type` the CDF data type
* `Data` retrieved variable data
* `Real_Records` Record numbers for real data for sparse record variable in list

By default, the full variable data is returned. To acquire only a
portion of the data for a record-varying variable, either the time or
record (0-based) range can be specified. 'epoch' can be used to
specify which time variable this variable depends on and is to be
searched for the time range. For the ISTP-compliant CDFs, the time
variable will come from the attribute 'DEPEND_0' from this variable.
The function will automatically search for it thus no need to specify
'epoch'. If either the start or end time is not specified, the
possible minimum or maximum value for the specific epoch data type is
assumed. If either the start or end record is not specified, the range
starts at 0 or/and ends at the last of the written data.

The start (and end) time should be presented in a list as:

* [year month day hour minute second millisec] for CDF_EPOCH
* [year month day hour minute second millisec microsec nanosec picosec] for CDF_EPOCH16
* [year month day hour minute second millisec microsec nanosec] for CDF_TIME_TT2000

If not enough time components are presented, only the last item can have the floating portion for the sub-time components.

Note: CDF's CDF_EPOCH16 data type uses 2 8-byte doubles for each data value.
In Python, each value is presented as a complex or
numpy.complex128.

### epochrange

```python
epochrange( epoch, [starttime=None, endtime=None])
```

Get epoch range.
Returns `list()` of the record numbers, representing the corresponding starting and ending records within the time range from the epoch data.
`None` is returned if there is no data either written or found in the time range.

### getVersion ()

Shows the code version.

```python
import cdflib

swea_cdf_file = cdflib.CDF('/path/to/swea_file.cdf') swea_cdf_file.cdf_info()

x = swea_cdf_file.varget('NameOfVariable') swea_cdf_file.close()
```

## CDF Writer Class

### CDF (path, cdf_spec=None, delete=False)

Creates an empty CDF file. path is the path name of the CDF (with or
without .cdf extension).
`cdf_spec` is the optional specification of the
CDF file, in the form of a dictionary. The dictionary can have the
following values:

* `Majority` 'row_major' or 'column_major', or its corresponding value. Default is 'column_major'.
* `Encoding` Data encoding scheme. See the CDF documentation about the valid values. Can be in string or its numeric corresponding value. Default is 'host'.
* `Checksum` Whether to set the data validation upon file creation. The default is False.
* `rDim_sizes` The dimensional sizes, applicable only to rVariables.
* `Compressed` Whether to compress the CDF at the file level. A value of 0-9 or True/False, the default is 0/False.

### write_globalattrs (globalAttrs)

Writes the global attributes. **globalAttrs** is a dictionary that has
global attribute name(s) and their value(s) pair(s). The value(s) is a
dictionary of entry number and value pair(s). For example:

```python
globalAttrs={}
globalAttrs['Global1']={0: 'Global Value 1'}
globalAttrs['Global2']={0: 'Global Value 2'}
```

For a non-string value, use a list with the value and its CDF data type.
For example:

```python
globalAttrs['Global3']={0: [12, 'cdf_int4']}
globalAttrs['Global4']={0: [12.34, 'cdf_double']}
```

If the data type is not provided, a corresponding CDF data type is
assumed:

```python
globalAttrs['Global3']={0: 12}     as 'cdf_int4'
globalAttrs['Global4']={0: 12.34}  as 'cdf_double'
```

CDF allows multi-values for non-string data for an attribute:

```python
globalAttrs['Global5']={0: [[12.34,21.43], 'cdf_double']}
```

For multi-entries from a global variable, they should be presented in
this form:

```python
GA6={}
GA6[0]='abcd'
GA6[1]=[12, 'cdf_int2']
GA6[2]=[12.5, 'cdf_float']
GA6[3]=[[0,1,2], 'cdf_int8']
globalAttrs['Global6']=GA6
....
f.write_globalattrs(globalAttrs)
```

### write_variableattrs (variableAttrs)

Writes a variable's attributes, provided the variable already exists.
**variableAttrs** is a dictionary that has variable attribute name and
its entry value pair(s). The entry value is also a dictionary of
variable id and value pair(s). Variable id can be the variable name or
its id number in the file. Use write_var function if the variable does
not exist.
For example:

```python
variableAttrs={}
entries_1={}

entries_1['var_name_1'] = 'abcd'
entries_1['var_name_2'] = [12, 'cdf_int4']
....
variableAttrs['attr_name_1'] = entries_1

entries_2={}
entries_2['var_name_1'] = 'xyz'
entries_2['var_name_2'] = [[12, 34], 'cdf_int4']
....
variableAttrs['attr_name_2']=entries_2
....
f.write_variableattrs(variableAttrs)
```

### write_var (var_spec, var_attrs=None, var_data=None)

Writes a variable, along with variable attributes and data.
**var_spec** is a dictionary that contains the specifications of the
variable. The required/optional keys for creating a variable:

Required keys:

* `Variable` The name of the variable
* `Data_Type` the CDF data type
* `Num_Elements` The number of elements. Always 1 the for numeric type. The char length for string type.
* `Rec_Vary` The dimensional sizes, applicable only to rVariables.

For zVariables:

* `Dim_Sizes` The dimensional sizes for zVariables only. Use [] for 0-dimension. Each and every dimension is varying for zVariables.

For rVariables:

* `Dims_Vary` The dimensional variances for rVariables only.

Optional keys:

* `Var_Type` Whether the variable is a zVariable or rVariable. Valid values: "zVariable" and "rVariable". The default is "zVariable".
* `Sparse` Whether the variable has sparse records. Valid values are "no_sparse", "pad_sparse", and "prev_sparse". The default is 'no_sparse'.
* `Compress` Set the gzip compression level (0 to 9), 0 for no compression. The default is to compress with level 6 (done only if the compressed data is less than the uncompressed data).
* `Block_Factor` The blocking factor, the number of records in a chunk when the variable is compressed.
* `Pad` The padded value (in bytes, numpy.ndarray or string)

**var_attrs** is a dictionary, with {attribute:value} pairs. The
attribute is the name of a variable attribute. The value can have its
data type specified for the numeric data. If not, based on Python's
type, a corresponding CDF type is assumed: CDF_INT4 for int,
CDF_DOUBLE for float, CDF_EPOCH16 for complex and and CDF_INT8 for
long. For example:

```python
var_attrs= { 'attr1': 'value1', 'attr2': 12.45, 'attr3': [3,4,5], .....} -or- var_attrs= { 'attr1': 'value1', 'attr2': [12.45, 'CDF_DOUBLE'], 'attr3': [[3,4,5], 'CDF_INT4'], ..... }
```

**var_data** is the data for the variable. If the variable is a regular
variable without sparse records, it must be in a single structure of
bytes, or numpy.ndarray for numeric variable, or str or list of strs for
string variable. If the variable has sparse records, var_data should be
presented in a list/tuple with two elements, the first being a
list/tuple that contains the physical record number(s), the second being
the variable data in bytes, numpy.ndarray, or a list of strings.
Variable data can have just physical records' data (with the same
number of records as the first element) or have data from both physical
records and virtual records (which with filled data). The var_data has
the form:

```python
[[[rec]()#1,rec_#2,rec_#3,...], [[data]()#1,data_#2,data_#3,...]]
```
See the sample for its setup.

### getVersion()

Shows the code version and modified date.

Note: The attribute entry value for the CDF epoch data type, CDF_EPOCH,
CDF_EPOCH16 or CDF_TIME_TT2000, can be presented in either a numeric
form, or an encoded string form.
For numeric, the CDF_EPOCH data is 8-byte float, CDF_EPOCH16 16-byte complex and CDF_TIME_TT2000 8-byte
long. The default encoded string for the epoch `data should have this
form:

```python
CDF_EPOCH: 'dd-mon-year hh:mm:ss.mmm'
CDF_EPOCH16: 'dd-mon-year hh:mm:ss.mmm.uuu.nnn.ppp'
CDF_TIME_TT2000: 'year-mm-ddThh:mm:ss.mmmuuunnn'
```

where mon is a 3-character month.

Sample use -

Use a master CDF file as the template for creating a CDF. Both global
and variable meta-data comes from the master CDF.
Each variable's specification also is copied from the master CDF.
Just fill the variable data to write a new CDF file:

```python
import cdfwrite
import cdfread
import numpy as np

cdf_master = cdfread.CDF('/path/to/master_file.cdf')
if (cdf_master.file != None):
# Get the cdf's specification
info=cdf_master.cdf_info()
cdf_file=cdfwrite.CDF('/path/to/swea_file.cdf',cdf_spec=info,delete=True)
if (cdf_file.file == None):
    cdf_master.close()
    raise OSError('Problem writing file.... Stop')

# Get the global attributes
globalaAttrs=cdf_master.globalattsget(expand=True)
# Write the global attributes
cdf_file.write_globalattrs(globalaAttrs)
zvars=info['zVariables']
print('no of zvars=',len(zvars))
# Loop thru all the zVariables
for x in range (0, len(zvars)):
    # Get the variable's specification
    varinfo=cdf_master.varinq(zvars[x])
    #print('Z =============>',x,': ', varinfo['Variable'])
    # Get the variable's attributes
    varattrs=cdf_master.varattsget(zvars[x], expand=True)
    if (varinfo['Sparse'].lower() == 'no_sparse'):
        # A variable with no sparse records... get the variable data
        vardata=.......
        # Create the zVariable, write out the attributes and data
        cdf_file.write_var(varinfo, var_attrs=varattrs, var_data=vardata)
    else:
        # A variable with sparse records...
        # data is in this form [physical_record_numbers, data_values]
        # physical_record_numbers (0-based) contains the real record
        # numbers. For example, a variable has only 3 physical records
        # at [0, 5, 10]:
        varrecs=[0,5,10]
        # data_values could contain only the physical records' data or
        # both the physical and virtual records' data.
        # For example, a float variable of 1-D with 3 elements with only
        # 3 physical records at [0,5,10]:
        # vardata = [[  5.55000000e+01, -1.00000002e+30,  6.65999985e+01],
        #            [  6.66659973e+02,  7.77770020e+02,  8.88880005e+02],
        #            [  2.00500000e+02,  2.10600006e+02,  2.20699997e+02]]
        # Or, with virtual record data embedded in the data:
        # vardata = [[  5.55000000e+01, -1.00000002e+30,  6.65999985e+01],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [  6.66659973e+02,  7.77770020e+02,  8.88880005e+02],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [ -1.00000002e+30, -1.00000002e+30, -1.00000002e+30],
        #            [  2.00500000e+02,  2.10600006e+02,  2.20699997e+02]]
        # Records 1, 2, 3, 4, 6, 7, 8, 9 are all virtual records with pad
        # data (variable defined with 'pad_sparse').
        vardata=np.asarray([.,.,.,..])
        # Create the zVariable, and optionally write out the attributes
        # and data
        cdf_file.write_var(varinfo, var_attrs=varattrs,
                   var_data=[varrecs,vardata])
   rvars=info['rVariables']
   print('no of rvars=',len(rvars))
   # Loop thru all the rVariables
   for x in range (0, len(rvars)):
       varinfo=cdf_master.varinq(rvars[x])
       print('R =============>',x,': ', varinfo['Variable'])
       varattrs=cdf_master.varattsget(rvars[x], expand=True)
       if (varinfo['Sparse'].lower() == 'no_sparse'):
           vardata=.......
           # Create the rVariable, write out the attributes and data
           cdf_file.write_var(varinfo, var_attrs=varattrs, var_data=vardata)
       else:
           varrecs=[.,.,.,..]
           vardata=np.asarray([.,.,.,..])
           cdf_file.write_var(varinfo, var_attrs=varattrs,
                      var_data=[varrecs,vardata])
cdf_master.close()
cdf_file.close()
```

## CDF Epochs

Importing cdflib also imports the module CDFepoch, which handles
CDF-based epochs. The following functions can be used to convert back
and forth between different ways to display the date. You can call these
functions like so:

```python
import cdflib

cdf_file = cdflib.cdfepoch.compute_epoch([2017,1,1,1,1,1,111])
```

There are three (3) epoch data types in CDF: CDF_EPOCH, CDF_EPOCH16
and CDF_TIME_TT2000.

- CDF_EPOCH is milliseconds since Year 0.
- CDF_EPOCH16 is picoseconds since Year 0.
- CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with
    leap seconds.

CDF_EPOCH is a single double(as float in Python), CDF_EPOCH16 is
2-doubles (as complex in Python), and TT2000 is 8-byte integer (as int
in Python). In Numpy, they are np.float64, np.complex128 and np.int64,
respectively. All these epoch values can come from from CDF.varget
function.

Five main functions are provided

### encode (epochs, iso_8601=False)

Encodes the epoch(s) into UTC string(s).

* CDF_EPOCH: The input should be either a float or list of floats (in numpy, a
  np.float64 or a np.ndarray of np.float64) Each epoch is encoded, by
  default to a ISO 8601 form: 2004-05-13T15:08:11.022 Or, if iso_8601
  is set to False, 13-May-2004 15:08:11.022
* CDF_EPOCH16: The input should be either a complex or list of complex(in numpy, a
  np.complex128 or a np.ndarray of np.complex128) Each epoch is
  encoded, by default to a ISO 8601 form:
  2004-05-13T15:08:11.022033044055 Or, if iso_8601 is set to False,
  13-May-2004 15:08:11.022.033.044.055
* TT2000: The input should be either a int or list of ints (in numpy, a
  np.int64 or a np.ndarray of np.int64) Each epoch is encoded, by
  default to a ISO 8601 form: 2008-02-02T06:08:10.10.012014016 Or, if
  iso_8601 is set to False, 02-Feb-2008 06:08:10.012.014.016

### unixtime (epochs, to_np=False)

Encodes the epoch(s) into seconds after 1970-01-01.
Precision is only kept to the nearest microsecond.

If `to_np=True`, then the values will be returned in a numpy array.

### breakdown (epochs, to_np=False)

Breaks down the epoch(s) into UTC components.

* CDF_EPOCH: they are 7 date/time components: year, month, day, hour, minute, second, and millisecond
* CDF_EPOCH16:  they are 10 date/time components: year, month, day, hour, minute, second, and millisecond, microsecond, nanosecond, and picosecond.
* TT2000: they are 9 date/time components: year, month, day, hour, minute, second, millisecond, microsecond, nanosecond.

Specify `to_np=True`, if the result should be in numpy array.

### compute[_epoch/_epoch16/_tt200] (datetimes, to_np=False)

Computes the provided date/time components into CDF epoch value(s).

For CDF_EPOCH: For computing into CDF_EPOCH value, each date/time elements should
have exactly seven (7) components, as year, month, day, hour,
minute, second and millisecond, in a list. For example:

```python
[[2017,1,1,1,1,1,111],[2017,2,2,2,2,2,222]]
```

Or, call function
compute_epoch directly, instead, with at least three (3) first (up
to seven) components. The last component, if not the 7th, can be a
float that can have a fraction of the unit.

For CDF_EPOCH16: They should have exactly ten (10) components, as year, month, day,
hour, minute, second, millisecond, microsecond, nanosecond and
picosecond, in a list. For example:

```python
[[2017,1,1,1,1,1,123,456,789,999],[2017,2,2,2,2,2,987,654,321,999]]
```

Or, call function compute_epoch directly, instead, with at least
three (3) first (up to ten) components. The last component, if not
the 10th, can be a float that can have a fraction of the unit.

For TT2000: Each TT2000 typed date/time should have exactly nine (9) components,
as year, month, day, hour, minute, second, millisecond, microsecond,
and nanosecond, in a list. For example:

```python
[[2017,1,1,1,1,1,123,456,789],[2017,2,2,2,2,2,987,654,321]]
```

Or, call function compute_tt2000 directly, instead, with at least
three (3) first (up to nine) components. The last component, if not
the 9th, can be a float that can have a fraction of the unit.

Specify `to_np=True`, if the result should be in numpy class.

### parse (datetimes, to_np=False)

Parses the provided date/time string(s) into CDF epoch value(s).

* CDF_EPOCH: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.xxx' or 'yyyy-mm-ddThh:mm:ss.xxx' (in iso_8601). The string is the output from encode function.
* CDF_EPOCH16: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn.ppp' or 'yyyy-mm-ddThh:mm:ss.mmmuuunnnppp' (in iso_8601). The string is the output from encode function.
* TT2000: The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn' or 'yyyy-mm-ddThh:mm:ss.mmmuuunnn' (in iso_8601). The string is the output from encode function.

Specify `to_np=True`, if the result should be in numpy class.

### findepochrange (epochs, starttime=None, endtime=None)

Finds the record range within the start and end time from values of a
CDF epoch data type. It returns a list of record numbers. If the start
time is not provided, then it is assumed to be the minimum possible
value. If the end time is not provided, then the maximum possible value
is assumed. The epoch is assumed to be in the chronological order. The
start and end times should have the proper number of date/time
components, corresponding to the epoch's data type.

The start/end times should be in either be in epoch units, or in the
list format described in "compute_epoch/epoch16/tt2000" section.

### getVersion ()

Shows the code version.

### getLeapSecondLastUpdated ()

Shows the latest date a leap second was added to the leap second table.

## CDF Astropy Epochs

If the user has astropy installed, importing cdflib also imports the module
cdflib.cdfastropy, which contains all of the functionality of the above module,
but uses the Astropy Time class for all conversions.  It can be used in the same
way as the above module:

```python
import cdflib

cdf_file = cdflib.cdfastropy.compute_epoch([2017,1,1,1,1,1,111])
```

Additionally, and perhaps most importantly, there is an additonal function that converts
CDF_EPOCH/EPOCH16/TT2000 times to the Astropy Time class:

### convert_to_astropy (epochs, format=None)

Converts the epoch(s) into Astropy Time(s).

* CDF_EPOCH: The input should be either a float or list of floats (in numpy, a
  np.float64 or a np.ndarray of np.float64).  If you'd like to ignore the input type and convert
  to CDF_EPOCH directly, specify format='cdf_epoch' when you call the function.
* CDF_EPOCH16: The input should be either a complex or list of complex(in numpy, a
  np.complex128 or a np.ndarray of np.complex128).  If you'd like to ignore the input type and convert
  to CDF_EPOCH directly, specify format='cdf_epoch16' when you call the function.
* TT2000: The input should be either a int or list of ints (in numpy, a
  np.int64 or a np.ndarray of np.int64).  If you'd like to ignore the input type and convert
  to CDF_EPOCH directly, specify format='cdf_tt2000' when you call the function.

For more information about Astropy Times and all the functionality it contains, take a look at the astropy documentation

https://docs.astropy.org/en/stable/time/
