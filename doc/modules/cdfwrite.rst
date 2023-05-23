CDF Writer Class
=================

.. autoclass:: cdflib.cdfwrite.CDF
   :members:


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
