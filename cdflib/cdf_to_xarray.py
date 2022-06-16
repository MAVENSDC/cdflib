import re

import numpy as np

from cdflib import CDF
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
    for key, value in var_att_dict.items():
        if key in ISTP_TO_XARRAY_ATTRS:
            xarray_att_dict[ISTP_TO_XARRAY_ATTRS[key]] = value
    return xarray_att_dict


def _convert_cdf_time_types(data, atts, properties, to_datetime=False, to_unixtime=False):
    '''
    # Converts CDF time types into either datetime objects, unixtime, or nothing
    # If nothing, ALL CDF_EPOCH16 types are converted to CDF_EPOCH, because xarray can't handle int64s
    '''

    data = np.squeeze(data)

    if not hasattr(data, '__len__'):
        data = [data]

    try:
        len(data)
    except Exception:
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

    cdf_file = CDF(filename, string_encoding='latin-1')
    cdf_info = cdf_file.cdf_info()
    all_cdf_variables = cdf_info['rVariables'] + cdf_info['zVariables']

    # Gather all Global Attributes
    try:
        gatt = cdf_file.globalattsget()
    except BaseException:
        gatt = {}

    # Gather all information about the CDF file, and store in the below dictionaries
    variable_data = {}
    variable_attributes = {}
    variable_properties = {}

    for var_name in all_cdf_variables:
        var_attribute_list = cdf_file.varattsget(var_name)
        var_data_temp = {}
        var_atts_temp = {}
        for att in var_attribute_list:
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


def _verify_depend_dimensions(dataset, dimension_number, primary_variable_name,
                              coordinate_variable_name, primary_variable_properties):

    primary_data = np.array(dataset[primary_variable_name])
    coordinate_data = np.array(dataset[coordinate_variable_name])

    if len(primary_data.shape) != 0 and len(coordinate_data.shape) == 0:
        print(
            f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.')
        return False

    if len(coordinate_data.shape) != 0 and len(primary_data.shape) == 0:
        print(
            f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.')
        return False

    if len(coordinate_data.shape) > 2:
        print(
            f'ISTP Compliance Warning: {coordinate_variable_name} has too many dimensions to be the DEPEND_{dimension_number} for variable {primary_variable_name}')
        return False
    if len(coordinate_data.shape) == 2:

        if primary_data.shape[0] != coordinate_data.shape[0]:
            print(
                f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the Epoch dimensions do not match.')
            return False

    if primary_variable_properties["Rec_Vary"] and primary_variable_properties["Last_Rec"] > 0:
        if len(primary_data.shape) <= dimension_number:
            print(
                f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but {primary_variable_name} does not have that many dimensions')
            return False

        if primary_data.shape[dimension_number] != coordinate_data.shape[-1]:
            print(
                f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.')
            return False
    else:
        if len(primary_data.shape) <= dimension_number - 1:
            print(
                f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but {primary_variable_name} does not have that many dimensions')
            return False

        if primary_data.shape[dimension_number - 1] != coordinate_data.shape[-1]:
            # This is kind of a hack for now.
            # DEPEND_1 can sometimes refer to the first dimension in a variable, and sometimes the second.
            # So we require both the first and second dimensions don't match the coordinate size before we definitely
            # reject it.
            if len(primary_data.shape) > dimension_number and primary_data.shape[dimension_number] != coordinate_data.shape[-1]:
                print(
                    f'ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.')
                return False

    return True


def _discover_depend_variables(vardata, varatts, varprops):
    # This loops through the variable attributes to discover which variables are the coordinates of other variables,
    # Unfortunately, there is no easy way to tell this by looking at the variable ITSELF,
    # you need to look at all variables and see if one points to it.

    depend_regex = re.compile('depend_[0-9]+$')

    list_of_depend_vars = []

    for v in varatts:
        depend_keys = [x for x in list(varatts[v].keys()) if depend_regex.match(x.lower())]
        for d in depend_keys:
            if varatts[v][d] in vardata:
                if _verify_depend_dimensions(vardata, int(d[-1]), v, varatts[v][d], varprops[v]):
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


def _discover_label_variables(varatts, all_variable_properties, all_variable_data):
    # This loops through the variable attributes to discover which variables are the labels of other variables
    # Unfortunately, there is no easy way to tell this by looking at the label variable itself
    # This returns a KEY:VALUE pair, with the LABEL VARIABLE corresponding to which dimension it covers.

    list_of_label_vars = {}

    for v in varatts:
        label_keys = [x for x in list(varatts[v].keys()) if x.startswith("LABL_PTR_")]
        for lab in label_keys:
            label_dependency = 'DEPEND_' + lab[-1]
            if label_dependency not in varatts[v]:
                continue
            depend_var_name = varatts[v][label_dependency]

            if all_variable_properties[depend_var_name]["Dim_Sizes"] and len(all_variable_properties[v]["Dim_Sizes"]) > 0 and (
                    all_variable_properties[depend_var_name]["Dim_Sizes"][0] == all_variable_properties[v]["Dim_Sizes"][int(lab[-1]) - 1]):
                if all_variable_data[depend_var_name].size == 0:
                    continue
            else:
                continue

            if varatts[v][lab] not in varatts:
                print(f"Warning, variable {v} points to {varatts[v][lab]} as label {lab}, but {varatts[v][lab]} does not exist.")
                print(f"Setting {varatts[v][lab]} as long_name instead.")
                varatts[v]['LABLAXIS'] = varatts[v][lab]
                varatts[v]['long_name'] = varatts[v][lab]
                continue

            list_of_label_vars[varatts[v][lab]] = depend_var_name

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


def _determine_record_dimensions(var_name, var_atts, var_data, var_props, depend_variables,
                                 all_variable_data, all_variable_properties, created_unlimited_dims):
    '''
    Determines the name of the
    :param var_name:
    :param var_atts:
    :param var_data:
    :param var_props:
    :param depend_variables:
    :param all_variable_data:
    :param all_variable_properties:
    :param created_unlimited_dims:
    :return:
    '''

    if var_props["Rec_Vary"] and var_props["Last_Rec"] > 0:

        # Check if this variable is itself the dimension
        if var_name in depend_variables and (len(var_props["Dim_Sizes"]) == 0 or var_props['Last_Rec'] >= 0):
            if not (len(var_props["Dim_Sizes"]) > 0 and var_props['Last_Rec'] > 0):
                return var_name, True, False
            # There might be dimensions listed, but they might not vary
            if len(var_props["Dim_Sizes"]) > 0:
                for i in range(0, len(var_props["Dim_Sizes"])):
                    if var_props["Dim_Vary"][i]:
                        break
                else:
                    return var_name, True, False

        # Check if the dimension is already defined within the attribute section
        if 'DEPEND_0' in var_atts:
            depend_0_variable_name = var_atts['DEPEND_0']
            if depend_0_variable_name not in all_variable_properties:
                print(f"Warning: Variable {var_name} listed DEPEND_0 as {depend_0_variable_name}, but no"
                      f" variable by that name was found.")
            else:
                if len(all_variable_data[depend_0_variable_name]) == len(var_data):
                    return depend_0_variable_name, True, False
                else:
                    print(
                        f"Warning: Variable {var_name} listed DEPEND_0 as {depend_0_variable_name}, but they have different dimension lengths.")

        '''
        # If the variable still isn't found, it should be fine to name the dimension after the variable
        if var_name in depend_variables and not udim_found:
            var_dims.append(var_name)
            depend_dimensions[var_name] = len(var_data)
            udim_found = True
        '''

        # If none of the above, check if the length of this variable dimension
        # matches a non-specific one that has already been created
        for udim in created_unlimited_dims:
            if len(var_data) == created_unlimited_dims[udim]:
                return udim, False, False

        # If none of the above, create a new dimension variable
        new_udim_name = 'record' + str(len(created_unlimited_dims))
        return new_udim_name, False, True

    elif 'DEPEND_0' in var_atts:

        # Check if the dimension is already defined within the attribute section
        depend_0_variable_name = var_atts['DEPEND_0']
        if depend_0_variable_name not in all_variable_properties:
            print(f"Warning: Variable {var_name} listed DEPEND_0 as {depend_0_variable_name}, but no"
                  f" variable by that name was found.")
        else:
            if len(all_variable_data[depend_0_variable_name]) == len(var_data) and len(var_data) != 0:
                return depend_0_variable_name, True, False
            else:
                print(
                    f"Warning: Variable {var_name} listed DEPEND_0 as {depend_0_variable_name}, but they have different dimension lengths.")

        return None, False, False

        # If none of the above, check if the length of this variable dimension matches a non-specific one that has already been created
        # for udim in created_unlimited_dims:
        #    if len(var_data) == created_unlimited_dims[udim]:
        #        return udim, False, False

        # If none of the above, create a new dimension variable
        #new_udim_name = 'record' + str(len(created_unlimited_dims))
        # return new_udim_name, False, True

    else:

        return None, False, False


def _determine_dimension_names(var_name, var_atts, var_data, var_props, depend_variables,
                               all_variable_data, all_variable_properties, created_regular_dims, record_name_found):
    '''
    :param var_name:
    :param var_atts:
    :param var_props:
    :param depend_variables:
    :param all_variable_data:
    :param all_variable_properties:
    :param created_regular_dims:
    :return:
    '''

    return_list = []

    if len(var_props["Dim_Sizes"]) != 0 and var_props['Last_Rec'] >= 0:
        i = 0
        skip_first_dim = record_name_found
        for dim_size in var_data.shape:
            if skip_first_dim:
                skip_first_dim = False
                continue

            i += 1

            # Check if the dimension is already defined within the attribute section
            if 'DEPEND_' + str(i) in var_atts:
                depend_i_variable_name = var_atts['DEPEND_' + str(i)]
                if depend_i_variable_name not in all_variable_properties:
                    print(f"Warning: Variable {var_name} listed DEPEND_{str(i)} as {depend_i_variable_name}, but no"
                          f" variable by that name was found.")
                else:
                    depend_i_variable_data = np.array(all_variable_data[depend_i_variable_name])

                    if not record_name_found:
                        dimension_number = i - 1
                    else:
                        dimension_number = i

                    if depend_i_variable_data.size != 0 and len(depend_i_variable_data.shape) == 1 and \
                            len(var_data.shape) > dimension_number and \
                            (depend_i_variable_data.shape[0] == var_data.shape[dimension_number]):
                        return_list.append((depend_i_variable_name, dim_size, True, False))
                        continue
                    elif len(depend_i_variable_data.shape) > 1 and \
                            depend_i_variable_data.size != 0 and \
                            len(var_data.shape) > dimension_number and \
                            (depend_i_variable_data.shape[1] == var_data.shape[dimension_number]):
                        return_list.append((depend_i_variable_name + "_dim", dim_size, True, False))
                        continue
                    else:
                        print(f"Warning: Variable {var_name} listed DEPEND_{str(i)} as {depend_i_variable_name}"
                              f", but that variable's dimensions do not match {var_name}'s dimensions.")

            # There may be occasions where there was no time-varying reccord identified, but the users intended for it
            # to exist.  Thus, all the DEPEND_X's are off by 1.  We should still try to incorporate those.
            if 'DEPEND_' + str(i - 1) in var_atts and not record_name_found:
                depend_i_variable_name = var_atts['DEPEND_' + str(i - 1)]
                if depend_i_variable_name in all_variable_properties:
                    depend_i_variable_data = np.array(all_variable_data[depend_i_variable_name])
                    if depend_i_variable_data.size != 0 and len(depend_i_variable_data.shape) == 1 and \
                            len(var_data.shape) > i - 1 and \
                            (depend_i_variable_data.shape[0] == var_data.shape[i - 1]):
                        print(f"Warning: Variable {var_name} has no determined time-varying component, but  "
                              f"{depend_i_variable_name} was determined to match closely with one of the dimensions."
                              f"  It will be set automatically for convenience.")
                        return_list.append((depend_i_variable_name, dim_size, True, False))
                        continue
                    elif len(depend_i_variable_data.shape) > 1 and \
                            depend_i_variable_data.size != 0 and \
                            len(var_data.shape) > i - 1 and \
                            (depend_i_variable_data.shape[1] == var_data.shape[i - 1]):
                        print(f"Warning: Variable {var_name} has no determined time-varying component, but  "
                              f"{depend_i_variable_name} was determined to match closely with one of the dimensions."
                              f"  It will be set automatically for convenience.")
                        return_list.append((depend_i_variable_name + "_dim", dim_size, True, False))
                        continue

            # Check if the variable is itself a dimension
            if var_name in depend_variables:
                if len(var_data.shape) == 2 and var_props["Last_Rec"] == 0:
                    if i == 1 and not record_name_found:
                        pass
                    else:
                        basic_dimension_name = var_name + "_dim"
                        return_list.append((basic_dimension_name, dim_size, True, False))
                        continue
                elif var_props["Rec_Vary"] and var_props["Last_Rec"] != 0:
                    basic_dimension_name = var_name + "_dim"
                    for x in return_list:
                        vn = x[0]
                        ds = x[1]
                        if vn == basic_dimension_name and dim_size != ds:
                            basic_dimension_name = var_name + "_dim" + str(i)
                    return_list.append((basic_dimension_name, dim_size, True, False))
                    continue
                else:
                    return_list.append((var_name, dim_size, True, False))
                    continue

            # If none of the above, check if a non-specific dimension name was already created with this dimension length
            for dim in created_regular_dims:
                if dim_size == created_regular_dims[dim]:
                    return_list.append((dim, dim_size, True, False))
                    break
            else:
                # If none of the above, create a new non-specific dimension name
                return_list.append(('dim' + str(len(created_regular_dims)), dim_size, False, True))
                created_regular_dims['dim' + str(len(created_regular_dims))] = dim_size

    return return_list


def _reformat_variable_dims_and_data(var_dims, var_data):
    if len(var_dims) > 0 and var_data is None:
        var_data = np.array([])

    # For some reason, there are times when the actual shape of the data doesn't match the dimensions listed.
    if var_data is not None:
        if len(np.array(var_data).shape) > len(var_dims):
            var_data = np.squeeze(var_data)
        if len(np.array(var_data).shape) < len(var_dims):
            var_data = np.expand_dims(var_data, axis=0)

    # Check if both dimensions and data are empty, if so, set the dimension to the empty dimension
    if var_data.size == 0 and not len(var_dims):
        var_dims = 'dim_empty'

    return var_dims, var_data


def _generate_xarray_data_variables(all_variable_data, all_variable_attributes,
                                    all_variable_properties, fillval_to_nan):

    # Import here to avoid xarray as a dependency of all of cdflib
    import xarray as xr

    # Make a list of all of the special variables in the file.  These are variables that are pointed to by
    # other variables.
    depend_variables = _discover_depend_variables(all_variable_data, all_variable_attributes, all_variable_properties)
    created_unlimited_dims = {}  # These hold the records of the names/lengths of the created "unlimited" dimensions
    created_regular_dims = {}  # These hold the records of the names/lengths of the standard dimensions of the variable
    depend_dimensions = {}  # This will be used after the creation of DataArrays, to determine which are "data" and which are "coordinates"
    created_vars = {}

    for var_name in all_variable_data:
        var_dims = []
        var_atts = all_variable_attributes[var_name]
        var_data = np.array(all_variable_data[var_name])
        var_props = all_variable_properties[var_name]

        # Determine the dimension name of the CDF Records, based on all info in the file
        record_dim_name, dependency, newly_created = _determine_record_dimensions(var_name, var_atts, var_data,
                                                                                  var_props, depend_variables,
                                                                                  all_variable_data,
                                                                                  all_variable_properties,
                                                                                  created_unlimited_dims)
        # Append the dimension name to the list of dimensions
        if record_dim_name:
            var_dims.append(record_dim_name)
            if dependency:
                depend_dimensions[record_dim_name] = len(var_data)
            if newly_created:
                created_unlimited_dims[record_dim_name] = len(var_data)

        # Determine the dimension names of the labeled Dimensions in the CDF file
        returned_dimension_info = _determine_dimension_names(var_name, var_atts, var_data, var_props, depend_variables,
                                                             all_variable_data, all_variable_properties,
                                                             created_regular_dims, record_dim_name)

        # Append the dimensions to the list of defined dimension names
        for dimension_dim_names, dimension_size, dependency, newly_created in returned_dimension_info:
            if dimension_dim_names:
                var_dims.append(dimension_dim_names)
                if dependency:
                    depend_dimensions[dimension_dim_names] = dimension_size
                if newly_created:
                    created_regular_dims[dimension_dim_names] = dimension_size

        # There might be a few tweaks needed to the data or the dimension labels
        var_dims, var_data = _reformat_variable_dims_and_data(var_dims, var_data)

        # Looks for attributes to convert over to the things XArray uses to plot
        additional_variable_attrs = _find_xarray_plotting_values(var_atts)
        var_atts.update(additional_variable_attrs)

        # If the user wants to convert all the FILLVAL values to NaNs, we got them covered
        if fillval_to_nan:
            var_data = _convert_fillvals_to_nan(var_data, var_atts, var_props)

        # Finally, create the new variable
        try:
            created_vars[var_name] = xr.Variable(var_dims, var_data, attrs=var_atts)
        except Exception as e:
            print(f'ERROR: Creating Variable {var_name} ran into exception: {e}')

    return created_vars, depend_dimensions


def _verify_dimension_sizes(created_data_vars, created_coord_vars):

    for var in created_data_vars:
        for d in created_data_vars[var].dims:
            if d in created_data_vars:
                if created_data_vars[d].dims != (d,):
                    raise Exception(f'ERROR: Variable \"{var}\" contains the dimensions {created_data_vars[var].dims}. '
                                    f'Dimension \"{d}\" is a data variable, but '
                                    f'its dimensions must be equal to itself. '
                                    f'Instead, its dimensions are {created_data_vars[d].dims}. '
                                    f'This is likely due to issues with \"DEPEND_X\" attributes in either {var} or {d}')
            if d in created_coord_vars:
                if created_coord_vars[d].dims != (d,):
                    raise Exception(f'ERROR: Variable \"{var}\" contains the dimensions {created_data_vars[var].dims}. '
                                    f'Dimension \"{d}\" is a data variable, but '
                                    f'its dimensions must be equal to itself.  '
                                    f'Instead, its dimensions are {created_coord_vars[d].dims}.  '
                                    f'This is likely due to issues with \"DEPEND_X\" attributes in either {var} or {d}')
    for var in created_coord_vars:
        for d in created_coord_vars[var].dims:
            if d in created_data_vars:
                if created_data_vars[d].dims != (d,):
                    raise Exception(f'ERROR: Variable \"{var}\" contains the dimensions {created_coord_vars[var].dims}. '
                                    f'Dimension \"{d}\" is a data variable, but '
                                    f'its dimensions must be equal to itself.  '
                                    f'Instead, its dimensions are {created_data_vars[d].dims}.  '
                                    f'This is likely due to issues with \"DEPEND_X\" attributes in either {var} or {d}')
            if d in created_coord_vars:
                if created_coord_vars[d].dims != (d,):
                    raise Exception(f'ERROR: Variable \"{var}\" contains the dimensions {created_coord_vars[var].dims}. '
                                    f'Dimension \"{d}\" is a data variable, but '
                                    f'its dimensions must be equal to itself.  '
                                    f'Instead, its dimensions are {created_coord_vars[d].dims}.  '
                                    f'This is likely due to issues with \"DEPEND_X\" attributes in either {var} or {d}')


def cdf_to_xarray(filename, to_datetime=False, to_unixtime=False, fillval_to_nan=False):
    """
    This function converts CDF files into XArray Dataset Objects.

    Parameters:
        filename (str):  The path to the CDF file to read
        to_datetime (bool, optional): Whether or not to convert CDF_EPOCH/EPOCH_16/TT2000 to datetime, or leave them as is
        to_unixtime (bool, optional): Whether or not to convert CDF_EPOCH/EPOCH_16/TT2000 to unixtime, or leave them as is
        fillval_to_nan (bool, optional): If True, any data values that match the FILLVAL attribute for a variable will be set to NaN

    Returns:
        An XArray Dataset Object

    Example MMS:
        >>> #Import necessary libraries
        >>> import cdflib
        >>> import xarray as xr
        >>> import os
        >>> import urllib.request

        >>> #Download a CDF file
        >>> fname = 'mms2_fgm_srvy_l2_20160809_v4.47.0.cdf'
        >>> url = ("https://lasp.colorado.edu/maven/sdc/public/data/sdc/web/cdflib_testing/mms2_fgm_srvy_l2_20160809_v4.47.0.cdf")
        >>> if not os.path.exists(fname):
        >>>     urllib.request.urlretrieve(url, fname)

        >>> #Load in and display the CDF file
        >>> mms_data = cdflib.cdf_to_xarray("mms2_fgm_srvy_l2_20160809_v4.47.0.cdf", to_unixtime=True, fillval_to_nan=True)
        >>> print(mms_data)

        >>> # Show off XArray functionality
        >>>
        >>> # Slice the data using built in XArray functions
        >>> mms_data2 = mms_data.isel(dim0=0)
        >>> # Plot the sliced data using built in XArray functions
        >>> mms_data2['mms2_fgm_b_gse_srvy_l2'].plot()
        >>> # Zoom in on the slices data in time using built in XArray functions
        >>> mms_data3 = mms_data2.isel(Epoch=slice(716000,717000))
        >>> # Plot the zoomed in sliced data using built in XArray functionality
        >>> mms_data3['mms2_fgm_b_gse_srvy_l2'].plot()

    Example THEMIS:
        >>> #Import necessary libraries
        >>> import cdflib
        >>> import xarray as xr
        >>> import os
        >>> import urllib.request

        >>> #Download a CDF file
        >>> fname = 'thg_l2_mag_amd_20070323_v01.cdf'
        >>> url = ("https://lasp.colorado.edu/maven/sdc/public/data/sdc/web/cdflib_testing/thg_l2_mag_amd_20070323_v01.cdf")
        >>> if not os.path.exists(fname):
        >>>     urllib.request.urlretrieve(url, fname)

        >>> #Load in and display the CDF file
        >>> thg_data = cdflib.cdf_to_xarray(fname, to_unixtime=True, fillval_to_nan=True)
        >>> print(thg_data)

    Processing Steps:
        1. For each variable in the CDF file
            1. Determine the name of the dimension that spans the data "records"
                - Check if the variable itself might be a dimension
                - The DEPEND_0 likely points to the approrpiate dimensions
                - If neither of the above, we create a new dimensions named "recordX"
            2. Determine the name of the other dimensions of the variable, if they exist
                - Check if the variable name itself might be a dimension
                - The DEPEND_X probably points to the appropriate dimensions for that variable, so we check those
                - If either of the above are time varying, the code appends "_dim" to the end of the name
                - If no dimensions are found through the above checks, create a dumension named "dimX"
            3. Gather all attributes that belong to the variable
            4. Add a few attributes that enable better plotting with built-in xarray functions (name, units, etc)
            5. Optionally, convert FILLVALs to NaNs in the data
            6. Optionally, convert CDF_EPOCH/EPOCH16/TT2000 variables to unixtime or datetime
            7. Create an XArray Variable object using the dimensions determined in steps 1 and 2, the attributes from steps 3 and 4, and then the variable data
        2. Gather all the Variable objects created in the first step, and separate them into data variables or coordinate variables
        3. Gather all global scope attributes in the CDF file
        4. Create an XArray Dataset objects with the data variables, coordinate variables, and global attributes.
    """
    # Import here to avoid xarray as a dependency of all of cdflib
    import xarray as xr

    # Convert the CDF file into a series of dicts, so we don't need to keep reading the file
    global_attributes, all_variable_attributes, all_variable_data, all_variable_properties = _convert_cdf_to_dicts(
        filename, to_datetime=to_datetime, to_unixtime=to_unixtime)

    created_vars, depend_dimensions = _generate_xarray_data_variables(all_variable_data, all_variable_attributes,
                                                                      all_variable_properties, fillval_to_nan)

    label_variables = _discover_label_variables(all_variable_attributes, all_variable_properties, all_variable_data)
    uncertainty_variables = _discover_uncertainty_variables(all_variable_attributes)

    # Determine which dimensions are coordinates vs actual data
    # Variables are considered coordinates if one of the other dimensions depends on them.
    # Otherwise, they are considered data coordinates.
    created_coord_vars = {}
    created_data_vars = {}
    for var_name in created_vars:

        if var_name in label_variables:
            # If these are label variables, we'll deal with these later when the DEPEND variables come up
            continue
        elif (var_name in depend_dimensions) or (var_name + '_dim' in depend_dimensions):
            # If these are DEPEND variables, add them to the DataSet coordinates
            created_coord_vars[var_name] = created_vars[var_name]
            # Check if these coordinate variable have associated labels
            for lab in label_variables:
                if label_variables[lab] == var_name:  # Found one!
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

    # Check that the datasets are valid
    _verify_dimension_sizes(created_data_vars, created_coord_vars)

    # Create the XArray DataSet Object!
    return xr.Dataset(data_vars=created_data_vars, coords=created_coord_vars, attrs=global_attributes)
