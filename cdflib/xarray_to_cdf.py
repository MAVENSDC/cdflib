import cdflib
import xarray as xr
import numpy as np
from datetime import datetime
from cdflib.epochs import CDFepoch as cdfepoch


def _dtype_to_cdf_type(var, dtype):

    if var.lower().startswith('epoch'):
        return 33, 1 # CDF_EPOCH_TT2000

    if dtype == np.int8 or dtype == np.int16 or dtype == np.int32 or dtype == np.int64:
        return 8, 1 #'CDF_INT8'
    elif dtype == np.float64 or dtype == np.float32 or dtype == np.float16:
        return 45, 1 #'CDF_DOUBLE'
    elif dtype == np.uint8 or dtype == np.uint16 or dtype == np.uint32 or dtype == np.uint64:
        return 14, 1 #'CDF_UNIT4'
    elif dtype == np.str_:
        return 51, int(dtype.str[2:]) # CDF_CHAR, and the length of the longest string in the numpy array
    else:
        print(f'Data type of {dtype} not supported')

    return

def _dtype_to_fillval(dtype):

    if dtype == np.int8 or dtype == np.int16 or dtype == np.int32 or dtype == np.int64:
        return -9223372036854775808 # Default FILLVAL of 'CDF_INT8'
    elif dtype == np.float64 or dtype == np.float32 or dtype == np.float16:
        return -1e30 #Default FILLVAL of 'CDF_DOUBLE'
    elif dtype == np.uint8 or dtype == np.uint16 or dtype == np.uint32 or dtype == np.uint64:
        return 4294967294 #Default FILLVAL of 'CDF_UNIT4'
    else:
        print(f'Data type of {dtype} not supported')

    return

def _dimension_checker(dataset):

    # NOTE: This may add attributes to the dataset object!

    # This variable will capture all ISTP compliant variables
    istp_depend_dimension_list = []

    # This variable will capture all other non-epoch dimension variables
    depend_dimension_list = []

    # Loop through the data
    for var in dataset:

        # Determine the variable type (data, support_data, metadata, ignore_data)
        if 'VAR_TYPE' not in dataset[var].attrs:
            print(f'ISTP Compliance Warning: Variable {var} does not have an attribute VAR_TYPE to describe the variable.  Attributes must be either data, support_data, metadata, or ignore_data.')
            var_type = None
        else:
            var_type = dataset[var].attrs['VAR_TYPE']
            if var_type.lower() not in ('data', 'support_data', 'metadata', 'ignore_data'):
                print(f'ISTP Compliance Warning: Variable {var} attribute VAR_TYPE is not set to either data, support_data, metadata, or ignore_data.')
                var_type = None

        # Determine ISTP compliant variables
        for att in dataset[var].attrs:
            if att.startswith('DEPEND') and att != 'DEPEND_0':
                if (dataset[var].attrs[att] in dataset) or (dataset[var].attrs[att] in dataset.coords):
                    istp_depend_dimension_list.append(dataset[var].attrs[att])
                else:
                    print(f'ISTP Compliance Warning: variable {var} listed {dataset[var].attrs[att]} as its {att}.  However, it was not found in the dataset.')

        # Determine potential dimension (non-epoch) variables
        potential_depend_dims = dataset[var].dims[1:]
        i = 1
        for d in potential_depend_dims:
            if d in dataset.coords:
                depend_dimension_list.append(d)
                if not f'DEPEND_{i}' in dataset[var].attrs:
                    dataset[var].attrs[f'DEPEND_{i}'] = d
            else:
                if var_type.lower() == 'data':
                    print(f'ISTP Compliance Warning: variable {var} contains a dimension {d} that is not defined in xarray.')
            i += 1

    depend_dimension_list = list(set(depend_dimension_list))
    istp_depend_dimension_list = list(set(istp_depend_dimension_list))

    combined_depend_dimension_list = set(depend_dimension_list + istp_depend_dimension_list)

    return combined_depend_dimension_list

def _epoch_checker(dataset, dim_vars):

    # This holds the list of epoch variables
    depend_0_list = []

    # Loop through the non-coordinate data
    for var in dataset:

        # Look at the first dimension of each data
        potential_depend_0 = dataset[var].dims[0]

        # We want to ignore any dimensions that were already gathered in the _dimension_checker function
        if potential_depend_0 in dim_vars:
            continue

        # Ensure that the dimension is listed somewhere else in the dataset
        if potential_depend_0 in dataset or potential_depend_0 in dataset.coords:
            depend_0_list.append(potential_depend_0)
        else:
            print(f'ISTP Compliance Warning: variable {var} contained an EPOCH dimension {potential_depend_0}, but it was not found in the data set.')

        # Add the depend_0 as an attribute if it doesn't exist yet
        if 'DEPEND_0' not in dataset[var].attrs:
            dataset[var].attrs['DEPEND_0'] = potential_depend_0
            print(f'ISTP Compliance Action: Adding attribute DEPEND_0={potential_depend_0} to {var}')

    depend_0_list = list(set(depend_0_list))

    if not depend_0_list:
        print(f'ISTP Compliance Warning: No variable for the time dimension could be found.')

    epoch_found = True
    for d in depend_0_list:
        if d.lower().startswith('epoch'):
            epoch_found=True

    if not epoch_found:
        print(f'ISTP Compliance Warning: There is no variable named Epoch.  Epoch is the required name of a DEPEND_0 attribute.')

    return depend_0_list

def _global_attribute_checker(dataset):
    required_global_attributes = ["Project",
                                  "Source_name",
                                  "Discipline",
                                  "Data_type",
                                  "Descriptor",
                                  "Data_version",
                                  "Logical_file_id",
                                  "PI_name",
                                  "PI_affiliation",
                                  "TEXT",
                                  "Instrument_type",
                                  "Mission_group",
                                  "Logical_source",
                                  "Logical_source_description"]
    for ga in required_global_attributes:
        if ga not in dataset.attrs:
            print(f'ISTP Compliance_Warning: Missing dataset attribute {ga}.')

def _variable_attribute_checker(dataset, epoch_list):

    data = (dataset, dataset.coords)

    for d in data:

        for var in d:

            # Check for VAR_TYPE
            if 'VAR_TYPE' not in d[var].attrs:
                print(f'ISTP Compliance Warning: VAR_TYPE is not defined for variable {var}.')
                var_type = None
            else:
                var_type = d[var].attrs['VAR_TYPE']
                if var_type not in ('data', 'support_data', 'metadata', 'ignore_data'):
                    print(f'ISTP Complaince Warning: VAR_TYPE for variable {var} is given a non-compliant value of {var_type}')
                    var_type = None

            # Check for CATDESC
            if 'CATDESC' not in d[var].attrs:
                print(f'ISTP Compliance Warning: CATDESC attribute is required for variable {var}')

            if 'DISPLAY_TYPE' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: DISPLAY_TYPE not set for variable {var}')

            if 'FIELDNAM' not in d[var].attrs:
                print(f'ISTP Compliance Warning: FIELDNAM attribute is required for variable {var}')

            if 'FORMAT' not in d[var].attrs:
                if 'FORM_PTR' in d[var].attrs:
                    if d[var].attrs['FORM_PTR'] in dataset or d[var].attrs['FORM_PTR'] in dataset.coords:
                        pass
                    else:
                        print(f'ISTP Compliance Warning: FORM_PTR for variable {var} does not point to an existing variable.')
                else:
                    print(f'ISTP Compliance Warning: FORMAT or FORM_PTR attribute is required for variable {var}')
            else:
                print(f'ISTP Compliance Warning: FORMAT or FORM_PTR attribute is required for variable {var}')

            if 'LABLAXIS' not in d[var].attrs:
                if var_type == 'data':
                    if 'LABL_PTR_1' in d[var].attrs:
                        if d[var].attrs['LABL_PTR_1'] in dataset or d[var].attrs['LABL_PTR_1'] in dataset.coords:
                            pass
                        else:
                            print(f'ISTP Compliance Warning: LABL_PTR_1 attribute for variable {var} does not point to an existing variable.')
                    else:
                        print(f'ISTP Compliance Warning: LABLAXIS or LABL_PTR_1 attribute is required for variable {var}')

            if 'UNITS' not in d[var].attrs:
                if var_type == 'data' or var_type == 'support_data':
                    if 'UNIT_PTR' not in d[var].attrs:
                        print(f'ISTP Compliance Warning: UNITS or UNIT_PTR attribute is required for variable {var}')
                    else:
                        if d[var].attrs['UNIT_PTR'] not in dataset:
                            print(f'ISTP Compliance Warning: UNIT_PTR attribute for variable {var} does not point to an existing variable.')

            if 'VALIDMIN' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: VALIDMIN required for variable {var}')
                elif var_type == 'support_data':
                    if dataset[var].dims[0] in epoch_list:
                        print(f'ISTP Compliance Warning: VALIDMIN required for variable {var}')

            if 'VALIDMAX' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: VALIDMAX required for variable {var}')
                elif var_type == 'support_data':
                    if d[var].dims[0] in epoch_list:
                        print(f'ISTP Compliance Warning: VALIDMAX required for variable {var}')

            if 'FILLVAL' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: FILLVAL required for variable {var}')
                    fillval = _dtype_to_fillval(d[var].dtype)
                    d[var].attrs['FILLVAL'] = fillval
                    print(f'ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}')
                elif var_type == 'support_data':
                    if d[var].dims[0] in epoch_list:
                        print(f'ISTP Compliance Warning: FILLVAL required for variable {var}')
                        fillval = _dtype_to_fillval(d[var].dtype)
                        d[var].attrs['FILLVAL'] = fillval
                        print(f'ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}')

def _unixtime_to_tt2000(unixtime_data):
    tt2000_data = np.array([])
    for ud in unixtime_data:
        dt = datetime.utcfromtimestamp(ud)
        dt_to_convert = [dt.year,
                         dt.month,
                         dt.day,
                         dt.hour,
                         dt.minute,
                         dt.second,
                         int(dt.microsecond/1000),
                         int(dt.microsecond % 1000),
                         0]
        tt2000_data = np.append(tt2000_data, cdfepoch.compute(dt_to_convert))
    return tt2000_data

def _datetime_to_tt2000(datetime_data):
    tt2000_data = np.array([])
    for dd in datetime_data:
        dd_to_convert = [dd.year,
                         dd.month,
                         dd.day,
                         dd.hour,
                         dd.minute,
                         dd.second,
                         int(dd.microsecond/1000),
                         int(dd.microsecond % 1000),
                         0]
        np.append(tt2000_data, cdfepoch.compute(dd_to_convert))
    return tt2000_data

def xarray_to_cdf(dataset, file_name, from_unixtime=False, from_datetime=False):

    x = cdflib.CDF(file_name)

    dim_vars = _dimension_checker(dataset)

    depend_0_vars = _epoch_checker(dataset, dim_vars)

    _global_attribute_checker(dataset)

    _variable_attribute_checker(dataset, depend_0_vars)


    # Gather the global attributes, write them into the file
    glob_att_dict = {}
    for ga in dataset.attrs:
        glob_att_dict[ga] = {0: dataset.attrs[ga]}
    x.write_globalattrs(glob_att_dict)

    # Gather the variables, write them into the file
    var_att_dict = {}
    datasets = (dataset, dataset.coords)
    for d in datasets:
        for var in d:
            for att in d[var].attrs:
                var_att_dict[att] = d[var].attrs[att]


            cdf_data_type, cdf_num_elements = _dtype_to_cdf_type(var, d[var].dtype)

            var_spec = {'Variable': var,
                        'Data_Type': cdf_data_type,
                        'Num_Elements': cdf_num_elements,
                        'Rec_Vary': True,
                        'Dim_Sizes': list(d[var].shape[1:]),
                        'Compress': 0}

            var_data = d[var].data
            if var.lower().startswith('epoch'):
                if from_unixtime:
                    var_data = _unixtime_to_tt2000(d[var].data)
                elif from_datetime:
                    var_data = _datetime_to_tt2000(d[var].data)
            print(f'writing variable {var}')
            x.write_var(var_spec, var_attrs=var_att_dict, var_data=var_data)

    return
