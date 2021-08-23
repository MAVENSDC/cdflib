import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch

ISTP_TO_XARRAY_ATTRS = {'FIELDNAM': 'standard_name',
                        'LABLAXIS': 'long_name',
                        'UNITS': 'units'}


def _find_xarray_plotting_values(var_att_dict):
    '''
    This is a simple function that looks through a variable attribute dictionary for ISTP attributes that are similar
    to ones used natively by Xarray, specifically their plotting routines.  If some are found, this returns a dictionary
    object of this new xarray attributes
    :param var_att_dict: A dictionary of attributes that a variable has
    :return:a dictionary of attributes that should be added to the created XArray DataArray
    '''
    xarray_att_dict = {}
    if not var_att_dict:
        return xarray_att_dict
    for key,value in var_att_dict.items():
        if key in ISTP_TO_XARRAY_ATTRS:
            xarray_att_dict[ISTP_TO_XARRAY_ATTRS[key]] = value
    return xarray_att_dict


def _convert_cdf_time_types(data, atts, properties, to_datetime=False, to_unixtime=False):
    '''
    # Converts CDF time types into either datetime objects, unixtime, or nothing
    # If nothing, ALL CDF_EPOCH16 types are converted to CDF_EPOCH, because xarray can't handle int64s
    '''

    if not hasattr(data, '__len__'):
        data = [data]

    if to_datetime and to_unixtime:
        print("Cannot convert to both unixtime and datetime.  Continuing with conversion to unixtime.")
        to_datetime = False

    # Convert all data in the "data" variable to unixtime or datetime if needed
    data_type = properties['Data_Type_Description']
    if len(data) == 0 or data_type not in ('CDF_EPOCH', 'CDF_EPOCH16', 'CDF_TIME_TT2000'):
        new_data = data
    else:
        if to_datetime:
            new_data = cdfepoch.to_datetime(data)
            if 'UNITS' in atts:
                atts['UNITS']['Data'] = 'Datetime (UTC)'
        elif to_unixtime:
            new_data = cdfepoch.unixtime(data)
            if 'UNITS' in atts:
                atts['UNITS']['Data'] = 'seconds'
        else:
            if data_type == 'CDF_EPOCH16':
                new_data = cdfepoch.compute(cdfepoch.breakdown(data)[0:7])
            else:
                new_data = data



    # Convert all the attributes in the "atts" dictionary to unixtime or datetime if needed
    new_atts = {}
    for att in atts:
        data_type = atts[att]['Data_Type']
        data = atts[att]['Data']
        if not hasattr(data, '__len__'):
            data = [data]
        if len(data) == 0 or data_type not in ('CDF_EPOCH', 'CDF_EPOCH16', 'CDF_TIME_TT2000'):
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


def _convert_cdf_to_dicts(filename, to_datetime=False, to_unixtime=False):
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
            var_data_temp[var_name] = np.array([])
        else:
            var_data_temp[var_name] = cdf_file.varget(var_name)

        variable_data[var_name], variable_attributes[var_name] = _convert_cdf_time_types(var_data_temp[var_name], var_atts_temp,
                                                                                         variable_properties[var_name],
                                                                                         to_datetime=to_datetime,
                                                                                         to_unixtime=to_unixtime)

    return gatt, variable_attributes, variable_data, variable_properties


def _discover_depend_variables(varatts):
    # This loops through the variable attributes to discover which variables are the coordinates of other variables,
    # Unfortunately, there is no easy way to tell this by looking at the variable ITSELF,
    # you need to look at all variables and see if one points to it.

    list_of_depend_vars = []

    for v in varatts:
        depend_keys = [x for x in list(varatts[v].keys()) if x.startswith("DEPEND_")]
        for d in depend_keys:
            list_of_depend_vars.append(varatts[v][d])

    return list(set(list_of_depend_vars))

def _discover_uncertainty_variables(varatts):
    # This loops through the variable attributes to discover which variables are the labels of other variables
    # Unfortunately, there is no easy way to tell this by looking at the label variable itself
    # This returns a KEY:VALUE pair, with the LABEL VARIABLE corresponding to which dimension it covers.

    list_of_label_vars = {}

    for v in varatts:
        if 'DELTA_PLUS_VAR' in varatts[v].keys():
            list_of_label_vars[varatts[v]['DELTA_PLUS_VAR']] = v
        if 'DELTA_MINUS_VAR' in varatts[v].keys():
            list_of_label_vars[varatts[v]['DELTA_MINUS_VAR']] = v
    return list_of_label_vars

def _discover_label_variables(varatts):
    # This loops through the variable attributes to discover which variables are the labels of other variables
    # Unfortunately, there is no easy way to tell this by looking at the label variable itself
    # This returns a KEY:VALUE pair, with the LABEL VARIABLE corresponding to which dimension it covers.

    list_of_label_vars = {}

    for v in varatts:
        label_keys = [x for x in list(varatts[v].keys()) if x.startswith("LABL_PTR_")]
        for lab in label_keys:
            depend_var_name = 'DEPEND_' + lab[-1]
            if depend_var_name not in varatts[v]:
                continue
            if varatts[v][lab] not in varatts:
                print(f"Warning, variable {v} points to {varatts[v][lab]} as label {lab}, but {varatts[v][lab]} does not exist.")
                print(f"Setting {varatts[v][lab]} as long_name instead.")
                varatts[v]['LABLAXIS'] = varatts[v][lab]
                varatts[v]['long_name'] = varatts[v][lab]
                continue
            list_of_label_vars[varatts[v][lab]] = varatts[v][depend_var_name]
    return list_of_label_vars

def _convert_fillvals_to_nan(var_data, var_atts, var_properties):
    if var_atts is None:
        return var_data
    if var_data is None:
        return var_data

    new_data = var_data
    if 'FILLVAL' in var_atts:
        if (var_properties['Data_Type_Description'] ==
                'CDF_FLOAT' or
                var_properties['Data_Type_Description'] ==
                'CDF_REAL4' or
                var_properties['Data_Type_Description'] ==
                'CDF_DOUBLE' or
                var_properties['Data_Type_Description'] ==
                'CDF_REAL8' or
                var_properties['Data_Type_Description'] ==
                'CDF_TIME_TT2000' or
                var_properties['Data_Type_Description'] ==
                'CDF_EPOCH' or
                var_properties['Data_Type_Description'] ==
                'CDF_EPOCH16'):

            if new_data.size > 1:
                if new_data[new_data == var_atts["FILLVAL"]].size != 0:
                    new_data[new_data == var_atts["FILLVAL"]] = np.nan
            else:
                if new_data == var_atts['FILLVAL']:
                    new_data = np.array(np.nan)
    return new_data

def cdf_to_xarray(filename, to_datetime=False, to_unixtime=False, fillval_to_nan=False):

    # Initialize the dimensions
    # Each variable in the CDF file will have an "unlimited" dimension (i.e. the number of records),
    # as well as well defined dimensions.

    num_unlimited_dims = 0
    created_unlimited_dims = {} # These hold the records of the names/lengths of the created "unlimited" dimensions
    num_regular_dims = 0
    created_regular_dims = {} # These hold the records of the names/lengths of the standard dimensions of the variable
    depend_dimensions = {} # This will be used after the creation of DataArrays, to determine which are "data" and which are "coordinates"

    # Convert the CDF file into a series of dicts, so we don't need to keep reading the file
    global_attributes, all_variable_attributes, all_variable_data, all_variable_properties = _convert_cdf_to_dicts(filename,
                                                                                                       to_datetime=to_datetime,
                                                                                                       to_unixtime=to_unixtime)

    # Make a list of all of the special variables in the file.  These are variables that are pointed to by
    # other variables.
    depend_variables = _discover_depend_variables(all_variable_attributes)
    label_variables = _discover_label_variables(all_variable_attributes)
    uncertainty_variables = _discover_uncertainty_variables(all_variable_attributes)

    created_vars = {}
    for var_name in all_variable_data:
        var_dims = []
        var_atts = all_variable_attributes[var_name]
        var_data = np.array(all_variable_data[var_name])
        var_props = all_variable_properties[var_name]

        # The following "if" statement exists to determine the name of dimension corresponding to the records.
        # If a name cannot be determined based on attributes, then give it the name "unlimited{i}"
        if var_props["Rec_Vary"] and var_props["Last_Rec"] != 0:
            udim_found = False

            # Check if this variable is itself the dimension
            if var_name in depend_variables and (len(var_props["Dim_Sizes"]) == 0 or var_props['Last_Rec'] >= 0):
                var_dims.append(var_name)
                depend_dimensions[var_name] = len(var_data)
                udim_found = True

            # Check if the dimension is already defined within the attribute section
            if 'DEPEND_0' in var_atts and not udim_found:
                depend_0_variable_name = var_atts['DEPEND_0']
                if depend_0_variable_name not in all_variable_properties:
                    print(f"Warning: Variable {var_name} listed DEPEND_0 as {depend_0_variable_name}, but no"
                          f" variable by that name was found.")
                else:
                    if len(all_variable_data[depend_0_variable_name]) == len(var_data):
                        var_dims.append(depend_0_variable_name)
                        depend_dimensions[depend_0_variable_name] = len(var_data)
                        udim_found = True
            if 'DEPEND_TIME' in var_atts and not udim_found:
                depend_time_variable_name = var_atts['DEPEND_TIME']
                if depend_time_variable_name not in all_variable_properties:
                    print(f"Warning: Variable {var_name} listed DEPEND_TIME as {depend_time_variable_name}, but no"
                          f" variable by that name was found.")
                else:
                    if len(all_variable_data[depend_time_variable_name]) == len(var_data):
                        var_dims.append(depend_time_variable_name)
                        depend_dimensions[depend_time_variable_name] = len(var_data)
                        udim_found = True
            '''
            # If the variable still isn't found, it should be fine to name the dimension after the variable
            if var_name in depend_variables and not udim_found:
                var_dims.append(var_name)
                depend_dimensions[var_name] = len(var_data)
                udim_found = True
            '''

            # If none of the above, check if the length of this variable dimension matches a non-specific one that has already been created
            for udim in created_unlimited_dims:
                if udim_found:
                    break
                if len(var_data) == created_unlimited_dims[udim]:
                    udim_found = True
                    var_dims.append(udim)
                    break

            # If none of the above, create a new dimension variable
            if not udim_found:
                new_udim_name = 'unlimited'+str(num_unlimited_dims)
                created_unlimited_dims[new_udim_name] = len(var_data)
                num_unlimited_dims += 1
                var_dims.append(new_udim_name)

        # The following "if" statement exists to determine the names and sizes of any other dimensions in the variable
        if len(var_props["Dim_Sizes"]) != 0 and var_props['Last_Rec'] >= 0:
            i = 0
            for dim_size in var_props["Dim_Sizes"]:
                if var_props["Dim_Vary"][i] == False:
                    continue
                i += 1
                dim_found = False

                # Check if the dimension is already defined within the attribute section
                if 'DEPEND_' + str(i) in var_atts:
                    depend_i_variable_name = var_atts['DEPEND_' + str(i)]
                    if depend_i_variable_name not in all_variable_properties:
                        print(f"Warning: Variable {var_name} listed DEPEND_{str(i)} as {depend_i_variable_name}, but no"
                              f" variable by that name was found.")
                    else:
                        if all_variable_properties[depend_i_variable_name]["Dim_Sizes"] and \
                                (all_variable_properties[depend_i_variable_name]["Dim_Sizes"][0] == var_props["Dim_Sizes"][i - 1]):
                            if all_variable_data[depend_i_variable_name].size == 0:
                                print(f"Warning: Variable {var_name} listed DEPEND_{str(i)} as {depend_i_variable_name}"
                                      f", but that variable is empty.")
                            else:
                                if all_variable_properties[depend_i_variable_name]["Rec_Vary"] and all_variable_properties[depend_i_variable_name]["Last_Rec"] != 0:
                                    var_dims.append(depend_i_variable_name+"_dim")
                                    depend_dimensions[depend_i_variable_name+"_dim"] = var_props["Dim_Sizes"][i - 1]
                                    dim_found = True
                                else:
                                    var_dims.append(depend_i_variable_name)
                                    depend_dimensions[depend_i_variable_name] = var_props["Dim_Sizes"][i - 1]
                                    dim_found=True
                        else:
                            print(f"Warning: Variable {var_name} listed DEPEND_{str(i)} as {depend_i_variable_name}"
                                  f", but that variable's dimensions do not match {var_name}'s dimensions.")

                # Check if the variable is itself a dimension
                if var_name in depend_variables and not dim_found:
                    if var_props["Rec_Vary"] and var_props["Last_Rec"] != 0:
                        var_dims.append(var_name + "_dim")
                        depend_dimensions[var_name + "_dim"] = var_props["Dim_Sizes"][i - 1]
                        dim_found = True
                    else:
                        var_dims.append(var_name)
                        depend_dimensions[var_name] = var_props["Dim_Sizes"][i - 1]
                        dim_found = True

                # If none of the above, check if a non-specific dimension name was already created with this dimension length
                for dim in created_regular_dims:
                    if dim_found:
                        break
                    if dim_size == created_regular_dims[dim]:
                        dim_found = True
                        var_dims.append(dim)
                        break

                # If none of the above, create a new non-specific dimension name
                if not dim_found:
                    new_dim_name = 'dim'+str(num_regular_dims)
                    created_regular_dims[new_dim_name] = dim_size
                    num_regular_dims += 1
                    var_dims.append(new_dim_name)

        if len(var_dims) > 0 and var_data is None:
            var_data = np.array([])

        # For some reason, there are times when the actual shape of the data doesn't match the dimensions listed.
        if var_data is not None:
            if len(np.array(var_data).shape) > len(var_dims):
                var_data = np.squeeze(var_data)
            if len(np.array(var_data).shape) < len(var_dims):
                var_data = np.expand_dims(var_data, axis=0)

        # Looks for attributes to convert over to the things XArray uses to plot
        additional_variable_attrs = _find_xarray_plotting_values(var_atts)
        var_atts.update(additional_variable_attrs)

        # Check if both dimensions and data are empty, if so, set the dimension to the empty dimension
        if var_data.size==0 and not len(var_dims):
            var_dims = 'dim_empty'

        # If the user wants to convert all the FILLVAL values to NaNs, we got them covered
        if fillval_to_nan:
            var_data = _convert_fillvals_to_nan(var_data, var_atts, var_props)

        # Finally, create the new variable
        created_vars[var_name] = xr.Variable(var_dims, var_data, attrs=var_atts)

    # Determine which dimensions are coordinates vs actual data
    # Variables are considered coordinates if one of the other dimensions depends on them.
    # Otherwise, they are considered data coordinates.
    created_coord_vars = {}
    created_data_vars = {}
    for var_name in created_vars:
        if var_name in label_variables:
            # If these are label variables, we'll deal with these later when the DEPEND variables come up
            continue
        elif (var_name in depend_dimensions) or (var_name+'_dim' in depend_dimensions):
            # If these are DEPEND variables, add them to the DataSet coordinates
            created_coord_vars[var_name] = created_vars[var_name]
            # Check if these coordinate variable have associated labels
            for lab in label_variables:
                if label_variables[lab] == var_name: # Found one!
                    if len(created_vars[lab].dims) == len(created_vars[var_name].dims):
                        if created_vars[lab].size != created_vars[var_name].size:
                            print(f"Warning, label variable {lab} does not match the expected dimension sizes of {var_name}")
                        else:
                            created_vars[lab].dims = created_vars[var_name].dims
                    else:
                        created_vars[lab].dims = created_vars[var_name].dims[-1]
                    # Add the labels to the coordinates as well
                    created_coord_vars[lab] = created_vars[lab]
        elif var_name in uncertainty_variables:
            # If there is an uncertainty variable, link it to the uncertainty along a dimension
            if created_vars[var_name].size == created_vars[uncertainty_variables[var_name]].size:
                created_vars[var_name].dims = created_vars[uncertainty_variables[var_name]].dims
                created_coord_vars[var_name] = created_vars[var_name]
            else:
                created_data_vars[var_name] = created_vars[var_name]
        else:
            created_data_vars[var_name] = created_vars[var_name]

    # Create the XArray DataSet Object!    created_coord_vars['time_nssdc']
    return xr.Dataset(data_vars=created_data_vars, coords=created_coord_vars, attrs=global_attributes)

ds = cdf_to_xarray("C:/Work/cdf_test_files/thc_l2_sst_20210709_v01.cdf", to_unixtime=True, fillval_to_nan=True)
print(ds)