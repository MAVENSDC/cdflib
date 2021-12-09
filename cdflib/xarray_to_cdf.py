import cdflib
import xarray as xr
import numpy as np
from datetime import datetime
from cdflib.epochs import CDFepoch as cdfepoch
import re

def _dtype_to_cdf_type(var):

    epoch_regex_1 = re.compile('epoch$')
    epoch_regex_2 = re.compile('epoch_[0-9]+$')
    if epoch_regex_1.match(var.name.lower()) or epoch_regex_2.match(var.name.lower()):
        return 33, 1 # CDF_EPOCH_TT2000

    if var.dtype == np.int8 or var.dtype == np.int16 or var.dtype == np.int32 or var.dtype == np.int64:
        return 8, 1 #'CDF_INT8'
    elif var.dtype == np.float64 or var.dtype == np.float32 or var.dtype == np.float16:
        return 45, 1 #'CDF_DOUBLE'
    elif var.dtype == np.uint8 or var.dtype == np.uint16 or var.dtype == np.uint32 or var.dtype == np.uint64:
        return 14, 1 #'CDF_UNIT4'
    elif var.dtype.type == np.str_:
        return 51, int(var.dtype.str[2:]) # CDF_CHAR, and the length of the longest string in the numpy array
    elif var.dtype.type == np.bytes_: # Bytes are usually strings
        return 51, int(var.dtype.str[2:]) # CDF_CHAR, and the length of the longest string in the numpy array
    elif var.dtype == np.object: # This commonly means we have multidimensional arrays of strings
        try:
            longest_string = 0
            for x in np.nditer(var.data, flags=['refs_ok']):
                if len(str(x)) > longest_string:
                    longest_string = len(str(x))
            return 51, longest_string
        except Exception as e:
            print(f'NOT SUPPORTED: Data in variable {var.name} has data type {var.dtype}.  Attempting to convert it to strings ran into the error: {str(e)}')
            return 51, 1
    else:
        print(f'NOT SUPPORTED: Data in variable {var.name} has data type of {var.dtype}.')
        return 51, 1

def _dtype_to_fillval(dtype):

    if dtype == np.int8 or dtype == np.int16 or dtype == np.int32 or dtype == np.int64:
        return -9223372036854775808 # Default FILLVAL of 'CDF_INT8'
    elif dtype == np.float64 or dtype == np.float32 or dtype == np.float16:
        return -1e30 #Default FILLVAL of 'CDF_DOUBLE'
    elif dtype == np.uint8 or dtype == np.uint16 or dtype == np.uint32 or dtype == np.uint64:
        return 4294967294 #Default FILLVAL of 'CDF_UNIT4'
    elif dtype.type == np.str_:
        return " " # Default FILLVAL of 'CDF_CHAR'
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
            depend_dimension_list.append(d)
            if d in dataset.coords: # Check if the dimension is in the coordinates themselves
                if not f'DEPEND_{i}' in dataset[var].attrs:
                    dataset[var].attrs[f'DEPEND_{i}'] = d
            else:
                # If the dimension is not labeled in the coordinate, look for a time-varying coordinate with those dimensions.
                # That one is likely to be the 'DEPEND_i' we are looking for
                if var_type is None or var_type != 'metadata':
                    for c in dataset.coords:
                        if len(dataset.coords[c].dims) == 2:
                            if d == dataset.coords[c].dims[1]:
                                # We have found a coordinate variable that depends on this dimension
                                if not f'DEPEND_{i}' in dataset[var].attrs:
                                    dataset[var].attrs[f'DEPEND_{i}'] = c
                                    #pass
                                break
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

        # Continue if there are no dimensions
        if len(dataset[var].dims) == 0:
            continue

        epoch_regex_1 = re.compile('epoch$')
        epoch_regex_2 = re.compile('epoch_[0-9]+$')
        first_dim_name = dataset[var].dims[0]

        # Look at the first dimension of each data
        if 'VAR_TYPE' in dataset[var].attrs and dataset[var].attrs['VAR_TYPE'] == 'data':
            potential_depend_0 = first_dim_name
        elif 'DEPEND_0' in dataset[var].attrs:
            potential_depend_0 = dataset[var].attrs['DEPEND_0']
        elif epoch_regex_1.match(first_dim_name.lower()) or epoch_regex_2.match(first_dim_name.lower()):
            potential_depend_0 = first_dim_name
        elif epoch_regex_1.match(var.lower()) or epoch_regex_2.match(var.lower()):
            potential_depend_0 = first_dim_name
        else:
            potential_depend_0 = ''

        # We want to ignore any dimensions that were already gathered in the _dimension_checker function
        if potential_depend_0 in dim_vars or potential_depend_0 == '':
            continue

        # Ensure that the dimension is listed somewhere else in the dataset
        if potential_depend_0 in dataset or potential_depend_0 in dataset.coords:
            depend_0_list.append(potential_depend_0)
        elif epoch_regex_1.match(var.lower()) or epoch_regex_2.match(var.lower()):
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
                    if len(dataset[var].dims) > 0:
                        if dataset[var].dims[0] in epoch_list:
                            print(f'ISTP Compliance Warning: VALIDMIN required for variable {var}')

            if 'VALIDMAX' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: VALIDMAX required for variable {var}')
                elif var_type == 'support_data':
                    if len(dataset[var].dims) > 0:
                        if d[var].dims[0] in epoch_list:
                            print(f'ISTP Compliance Warning: VALIDMAX required for variable {var}')

            if 'FILLVAL' not in d[var].attrs:
                if var_type == 'data':
                    print(f'ISTP Compliance Warning: FILLVAL required for variable {var}')
                    fillval = _dtype_to_fillval(d[var].dtype)
                    d[var].attrs['FILLVAL'] = fillval
                    print(f'ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}')
                elif var_type == 'support_data':
                    if len(dataset[var].dims) > 0:
                        if d[var].dims[0] in epoch_list:
                            print(f'ISTP Compliance Warning: FILLVAL required for variable {var}')
                            fillval = _dtype_to_fillval(d[var].dtype)
                            d[var].attrs['FILLVAL'] = fillval
                            print(f'ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}')

def _label_checker(dataset):
    # NOTE: This may add attributes to the dataset object!

    # This variable will capture all ISTP compliant variables
    istp_label_list = []

    # Loop through the data
    for var in dataset:
        # Determine ISTP compliant variables
        for att in dataset[var].attrs:
            if att.startswith('LABL_PTR'):
                if (dataset[var].attrs[att] in dataset) or (dataset[var].attrs[att] in dataset.coords):
                    istp_label_list.append(dataset[var].attrs[att])
                else:
                    print(
                        f'ISTP Compliance Warning: variable {var} listed {dataset[var].attrs[att]} as its {att}.  However, it was not found in the dataset.')

    istp_label_list = list(set(istp_label_list))

    for l in istp_label_list:
        if 'VAR_TYPE' not in dataset[l].attrs:
            dataset[l].attrs['VAR_TYPE'] = 'metadata'

    return istp_label_list

def _unixtime_to_tt2000(unixtime_data):
    tt2000_data = np.array([])

    # Make sure the object is iterable.  Sometimes numpy arrays claim to be iterable when they aren't.
    if not hasattr(unixtime_data, '__len__'):
        unixtime_data = [unixtime_data]
    elif isinstance(unixtime_data, np.ndarray):
        if unixtime_data.size <= 1:
            unixtime_data = [unixtime_data]

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

    label_vars = _label_checker(dataset)

    dim_vars = _dimension_checker(dataset)

    depend_0_vars = _epoch_checker(dataset, dim_vars)

    _global_attribute_checker(dataset)

    _variable_attribute_checker(dataset, depend_0_vars)

    # Gather the global attributes, write them into the file
    glob_att_dict = {}
    for ga in dataset.attrs:
        if hasattr(dataset.attrs[ga], '__len__') and not isinstance(dataset.attrs[ga], str):
            i = 0
            glob_att_dict[ga] = {}
            for _ in dataset.attrs[ga]:
                glob_att_dict[ga][i] = dataset.attrs[ga][i]
                i += 1
        else:
            glob_att_dict[ga] = {0: dataset.attrs[ga]}
    x.write_globalattrs(glob_att_dict)

    # Gather the variables, write them into the file
    datasets = (dataset, dataset.coords)
    for d in datasets:
        for var in d:
            var_att_dict = {}
            for att in d[var].attrs:
                var_att_dict[att] = d[var].attrs[att]

            cdf_data_type, cdf_num_elements = _dtype_to_cdf_type(d[var])
            if cdf_data_type is None or cdf_num_elements is None:
                continue

            if len(d[var].dims) > 0:
                if d[var].dims[0] in depend_0_vars:
                    dim_sizes = d[var].shape[1:]
                    record_vary = True
                else:
                    dim_sizes = d[var].shape
                    record_vary = False
            else:
                dim_sizes = []
                record_vary = True

            var_spec = {'Variable': var,
                        'Data_Type': cdf_data_type,
                        'Num_Elements': cdf_num_elements,
                        'Rec_Vary': record_vary,
                        'Dim_Sizes': list(dim_sizes),
                        'Compress': 0}

            var_data = d[var].data

            epoch_regex_1 = re.compile('epoch$')
            epoch_regex_2 = re.compile('epoch_[0-9]+$')
            if epoch_regex_1.match(var.lower()) or epoch_regex_2.match(var.lower()):
                if from_unixtime:
                    var_data = _unixtime_to_tt2000(d[var].data)
                elif from_datetime:
                    var_data = _datetime_to_tt2000(d[var].data)
            print(f'writing variable {var}')

            x.write_var(var_spec, var_attrs=var_att_dict, var_data=var_data)

    return
