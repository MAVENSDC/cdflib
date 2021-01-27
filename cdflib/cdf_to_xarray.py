# Handle the VAR_TYPE of 'metadata'
# Try plotting, they look at attributes.  Perhaps some of the ISTP required attributes can be mapped to the plotting?
# Try converting to netCDF and see what happens

import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch


def _convert_cdf_time_types(data, atts, properties, to_datetime=False, to_unixtime=False):
    '''
    # Converts CDF time types into
    # By default, all CDF_EPOCH16 types are converted to CDF_EPOCH
    '''

    if not hasattr(data, '__len__'):
        data = [data]

    if to_datetime and to_unixtime:
        print("Cannot convert to both unixtime and datetime.  Continuing with conversion to unixtime.")
        to_datetime = False

    data_type = properties['Data_Type_Description']
    if len(data) == 0 or data_type not in ('CDF_EPOCH', 'CDF_EPOCH16', 'CDF_TT2000'):
        new_data = data
    else:
        if to_datetime:
            new_data = cdfepoch.to_datetime(data)
        elif to_unixtime:
            new_data = cdfepoch.unixtime(data)
        else:
            if data_type == 'CDF_EPOCH16':
                new_data = cdfepoch.compute(cdfepoch.breakdown(data)[0:7])
            else:
                new_data = data

    new_atts = {}
    for att in atts:
        data_type = atts[att]['Data_Type']
        data = atts[att]['Data']
        if not hasattr(data, '__len__'):
            data = [data]
        if len(data) == 0 or data_type not in ('CDF_EPOCH', 'CDF_EPOCH16', 'CDF_TT2000'):
            new_atts[att] = data
        else:
            if to_datetime:
                new_atts[att] = cdfepoch.to_datetime(data)
            elif to_unixtime:
                new_atts[att] = cdfepoch.unixtime(data)
            else:
                if data_type == 'CDF_EPOCH16':
                    new_atts[att] = cdfepoch.compute(cdfepoch.breakdown(data)[0:7])
                else:
                    new_atts[att] = data

    return new_data, new_atts


def _cdf_to_dicts(filename, to_datetime=False, to_unixtime=False):
    # Open the CDF file
    # Converts the entire CDF file into python dictionary objects

    cdf_file = cdflib.CDF(filename, string_encoding='latin-1')
    cdf_info = cdf_file.cdf_info()
    all_cdf_variables = cdf_info['rVariables'] + cdf_info['zVariables']

    # Gather all Global Attributes
    try:
        gatt = cdf_file.globalattsget()
    except:
        gatt = {}

    # Gather all information about the CDF file, and store in the below dictionaries
    variable_data = {}
    variable_attributes = {}
    variable_properties = {}
    for var_name in all_cdf_variables:

        attribute_list = cdf_file.varattsget(var_name)
        var_data_temp = {}
        var_atts_temp = {}
        for att in attribute_list:
            var_atts_temp[att] = (cdf_file.attget(att, var_name))

        variable_properties[var_name] = cdf_file.varinq(var_name)

        # Gather the actual variable data
        if variable_properties[var_name]['Last_Rec'] < 0:
            var_data_temp[var_name] = []
        else:
            var_data_temp[var_name] = cdf_file.varget(var_name)

        variable_data[var_name], variable_attributes[var_name] = _convert_cdf_time_types(var_data_temp[var_name], var_atts_temp,
                                                                                         variable_properties[var_name],
                                                                                         to_datetime=to_datetime,
                                                                                         to_unixtime=to_unixtime)

    return gatt, variable_attributes, variable_data, variable_properties


def _discover_depend_variables(varatts):
    # This loops through the variable attributes to discover which variables are the coordinates of other variables
    # Unfortunately, there is no easy way to tell this by looking at the coordinate variable itself

    list_of_depend_vars = []

    for v in varatts:
        depend_keys = [x for x in list(varatts[v].keys()) if x.startswith("DEPEND_")]
        for d in depend_keys:
            list_of_depend_vars.append(varatts[v][d])

    return list(set(list_of_depend_vars))


def cdf_to_xarray(filename, to_datetime=False, to_unixtime=False):

    # Initialize the dimensions
    # Each variable in the CDF file will have an "unlimited" dimension (i.e. the number of records),
    # as well as well defined dimensions.

    num_unlimited_dims = 0
    created_unlimited_dims = {} # These hold the records of the names/lengths of the created "unlimited" dimensions
    num_regular_dims = 0
    created_regular_dims = {} # These hold the records of the names/lengths of the standard dimensions of the variable
    depend_dimensions = {} # This will be used after the creation of DataArrays, to determine which are data and which are coordinates

    # Convert the CDF file into a series of dicts, so we don't need to keep reading the file
    global_attributes, variable_attributes, variable_data, variable_properties = _cdf_to_dicts(filename,
                                                                                               to_datetime=to_datetime,
                                                                                               to_unixtime=to_unixtime)

    # Make a list of all of the coordinate variabes
    depend_variables = _discover_depend_variables(variable_attributes)

    created_vars = {}
    for var_name in variable_data:
        variable_dims = []

        # Determine the name of dimension corresponding to the records.
        # If a name cannot be determined based on attributes, then give it the name "unlimited{i}"
        if variable_properties[var_name]["Rec_Vary"]:
            udim_found = False

            # Check if the dimension is already defined within the attribute section
            if 'DEPEND_0' in variable_attributes[var_name]:
                depend_0_variable_name = variable_attributes[var_name]['DEPEND_0']
                if len(variable_data[depend_0_variable_name]) == len(variable_data[var_name]):
                    variable_dims.append(depend_0_variable_name)
                    depend_dimensions[depend_0_variable_name] = len(variable_data[var_name])
                    udim_found = True
            if 'DEPEND_TIME' in variable_attributes[var_name] and not udim_found:
                depend_time_variable_name = variable_attributes[var_name]['DEPEND_TIME']
                if len(variable_data[depend_time_variable_name]) == len(variable_data[var_name]):
                    variable_dims.append(depend_time_variable_name)
                    depend_dimensions[depend_time_variable_name] = len(variable_data[var_name])
                    udim_found = True


            # Check if this variable is itself the dimension
            if var_name in depend_variables and not udim_found:
                variable_dims.append(var_name)
                depend_dimensions[var_name] = len(variable_data[var_name])
                udim_found = True

            # If none of the above, check if the length of this variable dimension matches a non-specific one that has already been created
            for udim in created_unlimited_dims:
                if udim_found:
                    break
                if len(variable_data[var_name]) == created_unlimited_dims[udim]:
                    udim_found = True
                    variable_dims.append(udim)
                    break

            # If none of the above, create a new dimension variable
            if not udim_found:
                new_udim_name = 'unlimited'+str(num_unlimited_dims)
                created_unlimited_dims[new_udim_name] = len(variable_data[var_name])
                num_unlimited_dims += 1
                variable_dims.append(new_udim_name)

        # Determine the sizes of any other dimensions
        # Verify that there are dimensions in the variable, and that there are records written to the variable
        if len(variable_properties[var_name]["Dim_Sizes"]) != 0 and variable_properties[var_name]['Last_Rec'] >= 0:
            i = 0
            for dim_size in variable_properties[var_name]["Dim_Sizes"]:
                i += 1
                dim_found = False

                # Check if the dimension is already defined within the attribute section
                if 'DEPEND_' + str(i) in variable_attributes[var_name]:
                    depend_i_variable_name = variable_attributes[var_name]['DEPEND_' + str(i)]
                    if variable_properties[depend_i_variable_name]["Dim_Sizes"][0] == variable_properties[var_name]["Dim_Sizes"][i - 1]:
                        if variable_properties[depend_i_variable_name]["Rec_Vary"]:
                            variable_dims.append(depend_i_variable_name+"_dim")
                            depend_dimensions[depend_i_variable_name+"_dim"] = variable_properties[var_name]["Dim_Sizes"][i - 1]
                            dim_found = True
                        else:
                            variable_dims.append(depend_i_variable_name)
                            depend_dimensions[depend_i_variable_name] = variable_properties[var_name]["Dim_Sizes"][i - 1]
                            dim_found=True

                # Check if the variable is itself a dimension
                if var_name in depend_variables and not dim_found:
                    if variable_properties[var_name]["Rec_Vary"]:
                        variable_dims.append(var_name + "_dim")
                        depend_dimensions[var_name + "_dim"] = variable_properties[var_name]["Dim_Sizes"][i - 1]
                        dim_found = True
                    else:
                        variable_dims.append(var_name)
                        depend_dimensions[var_name] = variable_properties[var_name]["Dim_Sizes"][i - 1]
                        dim_found = True

                # If none of the above, check if a non-specific dimension name was already created with this dimension length
                for dim in created_regular_dims:
                    if dim_found:
                        break
                    if dim_size == created_regular_dims[dim]:
                        dim_found = True
                        variable_dims.append(dim)
                        break

                # If none of the above, create a new non-specific dimension name
                if not dim_found:
                    new_dim_name = 'dim'+str(num_regular_dims)
                    created_regular_dims[new_dim_name] = dim_size
                    num_regular_dims += 1
                    variable_dims.append(new_dim_name)

        # Handles the case of exactly 1 record with no dimensions, aka the variable is a single scalar value
        if not variable_properties[var_name]["Rec_Vary"] and len(variable_properties[var_name]["Dim_Sizes"]) == 0 and variable_properties[var_name]['Last_Rec'] == 0:
            udim_found = False
            for udim in created_unlimited_dims:
                if len(variable_data[var_name]) == created_unlimited_dims[udim]:
                    udim_found = True
                    variable_dims.append(udim)
                    break
            if not udim_found:
                new_udim_name = 'unlimited' + str(num_unlimited_dims)
                created_unlimited_dims[new_udim_name] = len(variable_data[var_name])
                num_unlimited_dims += 1
                variable_dims.append(new_udim_name)

        if len(variable_dims) > 0 and variable_data[var_name] is None:
            variable_data[var_name] = []

        if variable_data[var_name] is not None:
            if len(np.array(variable_data[var_name]).shape) > len(variable_dims):
                variable_data[var_name] = np.squeeze(variable_data[var_name])
            if len(np.array(variable_data[var_name]).shape) < len(variable_dims):
                variable_data[var_name] = np.expand_dims(variable_data[var_name], axis=0)

        created_vars[var_name] = xr.Variable(variable_dims, variable_data[var_name], attrs=variable_attributes[var_name])

    # Determine which dimensions are coordinates vs actual data
    # Variables are considered coordinates if one of these 2 are true:
    # 1) Another variable depends on them
    # 2) They contain VAR_TYPE='support_data' in their attributes
    created_coord_vars = {}
    created_data_vars = {}
    for var_name in created_vars:
        if (var_name in depend_dimensions) or (var_name+'_dim' in depend_dimensions):
            created_coord_vars[var_name] = created_vars[var_name]
        elif 'VAR_TYPE' in variable_attributes[var_name]:
            if variable_attributes[var_name]['VAR_TYPE'].lower() == 'data':
                created_data_vars[var_name] = created_vars[var_name]
            else:
                created_coord_vars[var_name] = created_vars[var_name]
        else:
            created_data_vars[var_name] = created_vars[var_name]

    # Create the XArray DataSet Object!
    return xr.Dataset(data_vars=created_data_vars, coords=created_coord_vars, attrs=global_attributes)
