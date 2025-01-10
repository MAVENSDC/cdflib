import os
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union, cast
from warnings import warn

import numpy as np
import numpy.typing as npt
import xarray as xr

from cdflib.cdfwrite import CDF
from cdflib.epochs import CDFepoch as cdfepoch
from cdflib.logging import logger

DATATYPES_TO_STRINGS = {
    1: "CDF_INT1",
    2: "CDF_INT2",
    4: "CDF_INT4",
    8: "CDF_INT8",
    11: "CDF_UINT1",
    12: "CDF_UINT2",
    14: "CDF_UINT4",
    21: "CDF_REAL4",
    22: "CDF_REAL8",
    31: "CDF_EPOCH",
    32: "CDF_EPOCH16",
    33: "CDF_TIME_TT2000",
    41: "CDF_BYTE",
    44: "CDF_FLOAT",
    45: "CDF_DOUBLE",
    51: "CDF_CHAR",
    52: "CDF_UCHAR",
}

STRINGS_TO_DATATYPES = {
    "CDF_INT1": 1,
    "CDF_INT2": 2,
    "CDF_INT4": 4,
    "CDF_INT8": 8,
    "CDF_UINT1": 11,
    "CDF_UINT2": 12,
    "CDF_UINT4": 14,
    "CDF_REAL4": 21,
    "CDF_REAL8": 22,
    "CDF_EPOCH": 31,
    "CDF_EPOCH16": 32,
    "CDF_TIME_TT2000": 33,
    "CDF_BYTE": 41,
    "CDF_FLOAT": 44,
    "CDF_DOUBLE": 45,
    "CDF_CHAR": 51,
    "CDF_UCHAR": 52,
}

DATATYPE_FILLVALS = {
    1: np.int8(-128),
    2: np.int16(-32768),
    4: np.int32(-2147483648),
    8: np.int64(-9223372036854775808),
    11: np.uint8(255),
    12: np.uint16(65535),
    14: np.uint32(4294967295),
    21: np.float32(-1e31),
    22: np.float64(-1e31),
    31: np.float64(-1e31),
    32: np.complex128(complex(-1e31, -1e31)),
    33: np.datetime64(-9223372036854775808, "ns"),
    41: np.int8(-128),
    44: np.float32(-1e31),
    45: np.float64(-1e31),
    51: np.str_(" "),
    52: np.str_(" "),
}

# Regular expression to match valid ISTP variable/attribute names
ISTP_COMPLIANT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class ISTPError(Exception):
    """
    Exception raised for ISTP Compliance Errors
    """

    def __init__(self, message: str = ""):
        super().__init__(message)


def _warn_or_except(message: str, exception: bool = False) -> None:
    if exception:
        if "ISTP" in message:
            raise ISTPError(message)
        else:
            raise Exception(message)
    else:
        logger.warning(message)


def _is_datetime_array(data: Union[npt.ArrayLike, datetime]) -> bool:
    try:
        if isinstance(data, datetime):
            return True
        elif isinstance(data, np.ndarray):
            if data.ndim == 0:
                return isinstance(data.item(), datetime)
            else:
                return all(isinstance(x, datetime) for x in data)
        elif hasattr(data, "__iter__"):
            return all(isinstance(x, datetime) for x in data)
        else:
            iterable_data = np.atleast_1d(data)
            return all(isinstance(x, datetime) for x in iterable_data)
    except:
        return False


def _is_datetime64_array(data: Any) -> bool:
    # Returns true if the input has a type of np.datetime64
    try:
        x = np.array(data)
        return x.dtype.type == np.datetime64
    except:
        return False


def _is_istp_epoch_variable(var_name: str) -> Union[re.Match, None]:
    # Checks if the variable is given the name of the ISTP Epoch variable standard
    epoch_regex_1 = re.compile("epoch$")
    epoch_regex_2 = re.compile("epoch_[0-9]+$")
    return epoch_regex_1.match(var_name.lower()) or epoch_regex_2.match(var_name.lower())


def _dtype_to_cdf_type(var: xr.DataArray, terminate_on_warning: bool = False) -> Tuple[int, int]:
    # Determines which CDF types to cast the xarray.Dataset to

    # Set some defaults
    cdf_data_type = "CDF_CHAR"
    element_size = 1

    # Check for overrides of datatype
    if "CDF_DATA_TYPE" in var.attrs:
        if var.attrs["CDF_DATA_TYPE"] in STRINGS_TO_DATATYPES:
            cdf_data_type = var.attrs["CDF_DATA_TYPE"]
            return STRINGS_TO_DATATYPES[cdf_data_type], element_size

    # Everything named "epoch" should be cast to a CDF_TIME_TT2000
    if _is_istp_epoch_variable(var.name.lower()):  # type: ignore
        return STRINGS_TO_DATATYPES["CDF_TIME_TT2000"], element_size

    numpy_data_type = var.dtype
    if numpy_data_type == np.int8:
        cdf_data_type = "CDF_INT1"
    elif numpy_data_type == np.int16:
        cdf_data_type = "CDF_INT2"
    elif numpy_data_type == np.int32:
        cdf_data_type = "CDF_INT4"
    elif numpy_data_type == np.int64:
        cdf_data_type = "CDF_INT8"
    elif numpy_data_type in (np.float32, np.float16):
        cdf_data_type = "CDF_FLOAT"
    elif numpy_data_type == np.float64:
        cdf_data_type = "CDF_DOUBLE"
    elif numpy_data_type == np.uint8:
        cdf_data_type = "CDF_UINT1"
    elif numpy_data_type == np.uint16:
        cdf_data_type = "CDF_UINT2"
    elif numpy_data_type == np.uint32:
        cdf_data_type = "CDF_UINT4"
    elif numpy_data_type == np.uint64:
        _warn_or_except(
            f"CONVERSION ERROR: Data in variable {var.name} is a 64bit unsigned integer. CDF does not currently support this data type. See documentation for supported xarray/numpy data types.",
            terminate_on_warning,
        )
        cdf_data_type = "CDF_UINT4"
    elif numpy_data_type == np.complex128:
        cdf_data_type = "CDF_EPOCH16"
    elif numpy_data_type.type in (np.str_, np.bytes_):
        element_size = int(numpy_data_type.str[2:])  # The length of the longest string in the numpy array
    elif var.dtype == object:  # This commonly means we either have multidimensional arrays of strings or datetime objects
        if _is_datetime_array(var.data):
            cdf_data_type = "CDF_TIME_TT2000"
        else:
            try:
                longest_string = 0
                for x in np.nditer(var.data, flags=["refs_ok"]):
                    if len(str(x)) > longest_string:
                        longest_string = len(str(x))
                element_size = longest_string
            except Exception as e:
                _warn_or_except(
                    f"NOT SUPPORTED: Data in variable {var.name} has data type {var.dtype}.  Attempting to convert it to strings ran into the error: {str(e)}",
                    terminate_on_warning,
                )
    elif var.dtype.type == np.datetime64:
        cdf_data_type = "CDF_TIME_TT2000"
    else:
        _warn_or_except(f"NOT SUPPORTED: Data in variable {var.name} has data type of {var.dtype}.", terminate_on_warning)

    return STRINGS_TO_DATATYPES[cdf_data_type], element_size


def _dtype_to_fillval(
    var: xr.DataArray, terminate_on_warning: bool = False
) -> Union[np.number, np.str_, np.datetime64, np.complex128]:
    datatype, _ = _dtype_to_cdf_type(var, terminate_on_warning=terminate_on_warning)
    if datatype in DATATYPE_FILLVALS:
        return DATATYPE_FILLVALS[datatype]  # type: ignore[return-value]
    else:
        return np.str_(" ")


def _convert_nans_to_fillval(var_data: xr.Dataset, terminate_on_warning: bool = False) -> xr.Dataset:
    new_data = var_data

    for var_name in new_data.data_vars:
        data_array = new_data[var_name]
        fill_value = _dtype_to_fillval(data_array)
        if fill_value.dtype.type != np.datetime64:
            try:
                new_data[var_name] = new_data[var_name].fillna(fill_value)
            except:
                pass
        var_att_dict = {}
        for att in data_array.attrs:
            try:
                var_att_dict[att] = np.nan_to_num(data_array.attrs[att], -1e31)  # type: ignore
            except:
                var_att_dict[att] = data_array.attrs[att]
        new_data[var_name].attrs = var_att_dict

    for var_name in new_data.coords:
        data_array = new_data[var_name]
        fill_value = _dtype_to_fillval(data_array)
        if fill_value.dtype.type != np.datetime64:
            try:
                new_data[var_name] = new_data[var_name].fillna(fill_value)
            except:
                pass
        var_att_dict = {}
        for att in data_array.attrs:
            try:
                var_att_dict[att] = np.nan_to_num(data_array.attrs[att], -1e31)  # type: ignore
            except:
                var_att_dict[att] = data_array.attrs[att]
        new_data[var_name].attrs = var_att_dict

    return new_data


def _verify_depend_dimensions(
    dataset: xr.Dataset,
    dimension_number: int,
    primary_variable_name: str,
    coordinate_variable_name: str,
    terminate_on_warning: bool = False,
) -> bool:
    try:
        primary_data = np.array(dataset[primary_variable_name])
        coordinate_data = np.array(dataset[coordinate_variable_name])

        if len(primary_data.shape) != 0 and len(coordinate_data.shape) == 0:
            _warn_or_except(
                f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.",
                terminate_on_warning,
            )
            return False

        if len(coordinate_data.shape) != 0 and len(primary_data.shape) == 0:
            _warn_or_except(
                f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.",
                terminate_on_warning,
            )
            return False

        if len(coordinate_data.shape) > 2:
            _warn_or_except(
                f"ISTP Compliance Warning: {coordinate_variable_name} has too many dimensions to be the DEPEND_{dimension_number} for variable {primary_variable_name}",
                terminate_on_warning,
            )
            return False

        if len(coordinate_data.shape) == 2:
            if primary_data.shape[0] != coordinate_data.shape[0]:
                _warn_or_except(
                    f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the Epoch dimensions do not match.",
                    terminate_on_warning,
                )
                return False

        # All variables should have at the very least a size of dimension_number
        # (i.e. a variable with a DEPEND_2 should have 2 dimensions)
        if len(primary_data.shape) < dimension_number:
            _warn_or_except(
                f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but {primary_variable_name} does not have that many dimensions",
                terminate_on_warning,
            )
            return False

        # All variables with a DEPEND_0 should always have a shape size of at least dimension_number + 1
        # (i.e. a variable with a DEPEND_2 should have 2 dimensions, 2 for DEPEND_1 and DEPEND_2, and 1 for DEPEND_0)
        if len(primary_data.shape) < dimension_number + 1:
            if "VAR_TYPE" in dataset[primary_variable_name].attrs:
                if dataset[primary_variable_name].attrs["VAR_TYPE"] == "data":
                    # Data variables should always have as many dimensions as their are DEPENDS
                    _warn_or_except(
                        f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but {primary_variable_name} does not have that many dimensions",
                        terminate_on_warning,
                    )
                    return False
                else:
                    for key in dataset[primary_variable_name].attrs:
                        if key.lower() == "depend_0":
                            # support_data variables with a DEPEND_0 should always match the dimension number
                            _warn_or_except(
                                f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but {primary_variable_name} does not have that many dimensions",
                                terminate_on_warning,
                            )
                            return False

        # Check that the size of the dimension that DEPEND_{i} is refering to is
        # also the same size of the DEPEND_{i}'s last dimension
        for key in dataset[primary_variable_name].attrs:
            if key.lower() == "depend_0":
                if primary_data.shape[dimension_number] != coordinate_data.shape[-1]:
                    _warn_or_except(
                        f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.",
                        terminate_on_warning,
                    )
                    return False
            else:
                if primary_data.shape[dimension_number - 1] != coordinate_data.shape[-1]:
                    _warn_or_except(
                        f"ISTP Compliance Warning: {coordinate_variable_name} is listed as the DEPEND_{dimension_number} for variable {primary_variable_name}, but the dimensions do not match.",
                        terminate_on_warning,
                    )
                    return False
    except ISTPError as istp_e:
        raise istp_e
    except Exception as e:
        if terminate_on_warning:
            raise Exception(
                f"Unknown error occured verifying {primary_variable_name}'s DEPEND_{dimension_number}, which is pointed to {coordinate_variable_name}. Error message: {e}"
            )
        else:
            print(
                f"Unknown error occured verifying {primary_variable_name}'s DEPEND_{dimension_number}, which is pointed to {coordinate_variable_name}"
            )
            return False

    return True


def _dimension_checker(dataset: xr.Dataset, terminate_on_warning: bool = False) -> List[str]:
    depend_regex = re.compile("depend_[0-9]+$")

    # NOTE: This may add attributes to the dataset object!

    # This variable will capture all ISTP compliant variables
    istp_depend_dimension_list = []

    # This variable will capture all other non-epoch dimension variables
    depend_dimension_list = []

    data = (dataset, dataset.coords)

    for d in data:
        # Loop through the data
        for var in d:
            var = cast(str, var)
            # Determine the variable type (data, support_data, metadata, ignore_data)
            if "VAR_TYPE" not in dataset[var].attrs:
                _warn_or_except(
                    f"ISTP Compliance Warning: Variable {var} does not have an attribute VAR_TYPE to describe the variable.  Attributes must be either data, support_data, metadata, or ignore_data.",
                    terminate_on_warning,
                )
                var_type = None
            else:
                var_type = dataset[var].attrs["VAR_TYPE"]
                if var_type.lower() not in ("data", "support_data", "metadata", "ignore_data"):
                    _warn_or_except(
                        f"ISTP Compliance Warning: Variable {var} attribute VAR_TYPE is not set to either data, support_data, metadata, or ignore_data.",
                        terminate_on_warning,
                    )
                    var_type = None

            # Determine ISTP compliant variables
            for att in dataset[var].attrs:
                if depend_regex.match(att.lower()) and att != "DEPEND_0":
                    if (dataset[var].attrs[att] in dataset) or (dataset[var].attrs[att] in dataset.coords):
                        depend_i = dataset[var].attrs[att]
                        if _verify_depend_dimensions(
                            dataset, int(att[-1]), var, depend_i, terminate_on_warning=terminate_on_warning
                        ):
                            istp_depend_dimension_list.append(dataset[var].attrs[att])
                    else:
                        _warn_or_except(
                            f"ISTP Compliance Warning: variable {var} listed {dataset[var].attrs[att]} as its {att}.  However, it was not found in the dataset.",
                            terminate_on_warning,
                        )

            # Determine potential dimension (non-epoch) variables
            potential_depend_dims = dataset[var].dims[1:]
            potential_depend_dims = cast(List[str], potential_depend_dims)
            i = 1
            for dim in potential_depend_dims:
                depend_dimension_list.append(dim)
                if dim not in dataset:  # Check if the dimension is in the coordinates themselves
                    if var_type is not None and var_type.lower() == "data":
                        if f"DEPEND_{i}" not in dataset[var].attrs:
                            _warn_or_except(
                                f"ISTP Compliance Warning: variable {var} contains a dimension {dim} that is not defined in xarray.  "
                                f"Specify one of the other xarray DataArrays as the DEPEND_{i} attribute.",
                                terminate_on_warning,
                            )
                i += 1

    depend_dimension_list = list(set(depend_dimension_list))
    istp_depend_dimension_list = list(set(istp_depend_dimension_list))

    combined_depend_dimension_list = list(set(depend_dimension_list + istp_depend_dimension_list))

    return combined_depend_dimension_list


def _recheck_dimensions_after_epoch_checker(
    dataset: xr.Dataset, time_varying_dimensions: List[str], dim_vars: List[str], terminate_on_warning: bool = False
) -> List[str]:
    # We need to go back and take a look at the first dimensions of data that were not identified as time-varying
    depend_dimension_list = []
    data = (dataset, dataset.coords)
    for d in data:
        for var in d:
            if var not in time_varying_dimensions:
                if len(dataset[var].dims) >= 1:
                    depend_dimension_list.append(dataset[var].dims[0])

    depend_dimension_list = list(set(depend_dimension_list + dim_vars))
    depend_dimension_list = cast(List[str], depend_dimension_list)

    return depend_dimension_list


def _epoch_checker(dataset: xr.Dataset, dim_vars: List[str], terminate_on_warning: bool = False) -> Tuple[List[str], List[str]]:
    # This holds the list of epoch variables
    depend_0_list = []
    time_varying_dimensions = []

    data = (dataset, dataset.coords)

    for d in data:
        # Loop through the non-coordinate data
        for var in d:
            var = cast(str, var)
            # Continue if there are no dimensions
            if len(dataset[var].dims) == 0:
                continue

            first_dim_name = cast(str, dataset[var].dims[0])

            # Look at the first dimension of each data
            if "DEPEND_0" in dataset[var].attrs:
                potential_depend_0 = dataset[var].attrs["DEPEND_0"]
            elif _is_istp_epoch_variable(first_dim_name):
                potential_depend_0 = first_dim_name
            elif _is_istp_epoch_variable(var):
                potential_depend_0 = var
            elif "VAR_TYPE" in dataset[var].attrs and dataset[var].attrs["VAR_TYPE"].lower() == "data":
                potential_depend_0 = first_dim_name
            elif (
                "VAR_TYPE" in dataset[var].attrs
                and dataset[var].attrs["VAR_TYPE"].lower() == "support_data"
                and len(dataset[var].dims) > 1
            ):
                potential_depend_0 = first_dim_name
            else:
                potential_depend_0 = ""

            # We want to ignore any dimensions that were already gathered in the _dimension_checker function
            if potential_depend_0 in dim_vars or potential_depend_0 == "":
                continue

            # Ensure that the dimension is listed somewhere else in the dataset
            if potential_depend_0 in dataset or potential_depend_0 in dataset.coords:
                if _verify_depend_dimensions(dataset, 0, var, potential_depend_0, terminate_on_warning=terminate_on_warning):
                    depend_0_list.append(potential_depend_0)
                    time_varying_dimensions.append(var)
                else:
                    _warn_or_except(
                        f'ISTP Compliance Warning: variable {var} contained a "record" dimension {potential_depend_0}, but they have different dimensions.',
                        terminate_on_warning,
                    )
            elif _is_istp_epoch_variable(var):
                depend_0_list.append(potential_depend_0)
                time_varying_dimensions.append(var)
            else:
                _warn_or_except(
                    f'ISTP Compliance Warning: variable {var} contained an "record" dimension {potential_depend_0}, but it was not found in the data set.',
                    terminate_on_warning,
                )

    depend_0_list = list(set(depend_0_list))

    if not depend_0_list:
        _warn_or_except(f"ISTP Compliance Warning: No variable for the time dimension could be found.", terminate_on_warning)

    epoch_found = False
    for d in depend_0_list:
        if d.lower().startswith("epoch"):
            monotonically_increasing = _verify_monotonically_increasing(dataset[d].data)
            if monotonically_increasing:
                epoch_found = True
            else:
                _warn_or_except(
                    f"Variable {d} was determined to be an ISTP 'Epoch' variable, but it is not monotonically increasing.",
                    terminate_on_warning,
                )

    if not epoch_found:
        _warn_or_except(
            f"ISTP Compliance Warning: There is no variable named Epoch.  Epoch is the required name of a DEPEND_0 attribute.",
            terminate_on_warning,
        )

    return depend_0_list, time_varying_dimensions


def _verify_monotonically_increasing(epoch_data: npt.NDArray) -> np.bool_:
    return np.all(epoch_data[1:] > epoch_data[:-1])


def _validate_varatt_names(dataset: xr.Dataset, terminate_on_warning: bool) -> None:
    for var_name in dataset.variables:
        if not ISTP_COMPLIANT_NAME.match(str(var_name)):
            _warn_or_except(
                f"Invalid ISTP variable name: {str(var_name)}",
                terminate_on_warning,
            )

    # Check attributes in the dataset
    for attr_name in dataset.attrs:
        if not ISTP_COMPLIANT_NAME.match(str(attr_name)):
            _warn_or_except(
                f"Invalid ISTP global attribute name: {str(attr_name)}",
                terminate_on_warning,
            )

    # Check attributes of each variable
    for var in dataset.variables:
        for attr_name in dataset[var].attrs:
            if not ISTP_COMPLIANT_NAME.match(str(attr_name)):
                _warn_or_except(
                    f"Invalid ISTP variable attribute name: {str(attr_name)}",
                    terminate_on_warning,
                )


def _add_depend_variables_to_dataset(
    dataset: xr.Dataset,
    dim_vars: List[str],
    depend_0_vars: List[str],
    time_varying_dimensions: List[str],
    terminate_on_warning: bool = False,
    auto_fix_depends: bool = True,
) -> xr.Dataset:
    data = (dataset, dataset.coords)

    for d in data:
        for var in d:
            # Check if we should set DEPEND_0
            if var in time_varying_dimensions:
                if "DEPEND_0" not in dataset[var].attrs:
                    depend_0 = dataset[var].dims[0]

                    if depend_0 is not None and depend_0 in depend_0_vars and var != depend_0:
                        _warn_or_except(f"ISTP Compliance Error, need to add DEPEND_0={depend_0} to {var}")
                        if auto_fix_depends:
                            _warn_or_except("Auto correcting enabled, correcting...")
                            dataset[var].attrs["DEPEND_0"] = depend_0

                potential_depend_dims = dataset[var].dims[1:]

            else:
                potential_depend_dims = dataset[var].dims

            # Check if we should add a DEPEND_{i}
            i = 1
            for dim in potential_depend_dims:
                if dim in dataset and dim in dim_vars:
                    if not f"DEPEND_{i}" in dataset[var].attrs and var != dim:
                        _warn_or_except(f"ISTP Compliance Error, need to add DEPEND_{i}={dim} to {var}")
                        if auto_fix_depends:
                            _warn_or_except("Auto correcting enabled, correcting...")
                            dataset[var].attrs[f"DEPEND_{i}"] = dim
                i += 1

    return dataset


def _global_attribute_checker(dataset: xr.Dataset, terminate_on_warning: bool = False) -> None:
    required_global_attributes = [
        "Project",
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
        "Logical_source_description",
    ]
    for ga in required_global_attributes:
        if ga not in dataset.attrs:
            _warn_or_except(f"ISTP Compliance Warning: Missing dataset attribute {ga}.", terminate_on_warning)


def _variable_attribute_checker(dataset: xr.Dataset, epoch_list: List[str], terminate_on_warning: bool = False) -> None:
    data = (dataset, dataset.coords)

    for d in data:
        for var in d:
            # Ensure None of the attributes are given a type of "None"
            for key, value in d[var].attrs.items():
                if value is None:
                    _warn_or_except(
                        f"CDF Warning: {key} was given a type of None for variable {var}. CDF does not allow None types, so {key} will be skipped.",
                        terminate_on_warning,
                    )

            # Check for VAR_TYPE
            if "VAR_TYPE" not in d[var].attrs:
                _warn_or_except(f"ISTP Compliance Warning: VAR_TYPE is not defined for variable {var}.", terminate_on_warning)
                var_type = ""
            else:
                var_type = d[var].attrs["VAR_TYPE"]
                if var_type.lower() not in ("data", "support_data", "metadata", "ignore_data"):
                    _warn_or_except(
                        f"ISTP Compliance Warning: VAR_TYPE for variable {var} is given a non-compliant value of {var_type}.",
                        terminate_on_warning,
                    )
                    var_type = ""

            # Check for CATDESC
            if "CATDESC" not in d[var].attrs:
                _warn_or_except(f"ISTP Compliance Warning: CATDESC attribute is required for variable {var}.", terminate_on_warning)

            # All "data" needs to have a DISPLAY_TYPE
            # DISPLAY_TYPE determines the LABLAXIS
            if var_type.lower() == "data":
                if "DISPLAY_TYPE" not in d[var].attrs:
                    _warn_or_except(f"ISTP Compliance Warning: DISPLAY_TYPE not set for variable {var}.", terminate_on_warning)
                elif d[var].attrs["DISPLAY_TYPE"].lower() == "image":
                    if "LABLAXIS" not in d[var].attrs:
                        _warn_or_except(
                            f"ISTP Compliance Warning: LABLAXIS attribute is required for variable {var} when DISPLAY_TYPE=image and VAR_TYPE=data.",
                            terminate_on_warning,
                        )
                else:
                    depend_pattern = re.compile(r"^DEPEND_([1-9])$")
                    for key in d[var].attrs:
                        match = depend_pattern.match(key)
                        if match:
                            corresponding_label_key = None
                            depend_number = int(match.group(1))
                            if d[var].attrs["DISPLAY_TYPE"].lower() in ("time_series", "stack_plot"):
                                corresponding_label_key = f"LABL_PTR_{depend_number}"
                            elif d[var].attrs["DISPLAY_TYPE"].lower() == "spectrogram":
                                if depend_number != 1:
                                    corresponding_label_key = f"LABL_PTR_{depend_number}"
                            if corresponding_label_key:
                                if corresponding_label_key not in d[var].attrs:
                                    _warn_or_except(
                                        f"ISTP Compliance Warning: {corresponding_label_key} attribute is required for variable {var} with its current DISPLAY_TYPE and VAR_TYPE, because there are {depend_number} or more dimensions.",
                                        terminate_on_warning,
                                    )
                                else:
                                    if (
                                        d[var].attrs[corresponding_label_key] in dataset
                                        or d[var].attrs[corresponding_label_key] in dataset.coords
                                    ):
                                        pass
                                    else:
                                        _warn_or_except(
                                            f"ISTP Compliance Warning: {corresponding_label_key} attribute for variable {var} does not point to an existing variable.",
                                            terminate_on_warning,
                                        )
                                    if "LABLAXIS" in d[var].attrs:
                                        _warn_or_except(
                                            f"Cannot include both LABLAXIS and {corresponding_label_key} in the attributes to variable {var}.",
                                            terminate_on_warning,
                                        )
                if "LABLAXIS" not in d[var].attrs and "LABL_PTR_1" not in d[var].attrs:
                    _warn_or_except(
                        f"ISTP Compliance Warning: LABLAXIS or LABL_PTR_1 attribute is required for variable {var} because VAR_TYPE=data.",
                        terminate_on_warning,
                    )

            # Every variable must have a FIELDNAM
            if "FIELDNAM" not in d[var].attrs:
                _warn_or_except(
                    f"ISTP Compliance Warning: FIELDNAM attribute is required for variable {var}.", terminate_on_warning
                )

            if "FORMAT" not in d[var].attrs:
                if "FORM_PTR" in d[var].attrs:
                    if d[var].attrs["FORM_PTR"] in dataset or d[var].attrs["FORM_PTR"] in dataset.coords:
                        pass
                    else:
                        _warn_or_except(
                            f"ISTP Compliance Warning: FORM_PTR for variable {var} does not point to an existing variable.",
                            terminate_on_warning,
                        )
                else:
                    _warn_or_except(
                        f"ISTP Compliance Warning: FORMAT or FORM_PTR attribute is required for variable {var}",
                        terminate_on_warning,
                    )

            # Every variable needs a units
            if "UNITS" not in d[var].attrs:
                if var_type.lower() == "data" or var_type.lower() == "support_data":
                    if "UNIT_PTR" not in d[var].attrs:
                        _warn_or_except(
                            f"ISTP Compliance Warning: UNITS or UNIT_PTR attribute is required for variable {var}",
                            terminate_on_warning,
                        )
                    else:
                        if d[var].attrs["UNIT_PTR"] not in dataset:
                            _warn_or_except(
                                f"ISTP Compliance Warning: UNIT_PTR attribute for variable {var} does not point to an existing variable.",
                                terminate_on_warning,
                            )

            if "VALIDMIN" not in d[var].attrs:
                if var_type.lower() == "data":
                    _warn_or_except(f"ISTP Compliance Warning: VALIDMIN required for variable {var}", terminate_on_warning)
                elif var_type.lower() == "support_data":
                    if len(dataset[var].dims) > 0:
                        if dataset[var].dims[0] in epoch_list:
                            _warn_or_except(f"ISTP Compliance Warning: VALIDMIN required for variable {var}", terminate_on_warning)

            if "VALIDMAX" not in d[var].attrs:
                if var_type.lower() == "data":
                    _warn_or_except(f"ISTP Compliance Warning: VALIDMAX required for variable {var}", terminate_on_warning)
                elif var_type.lower() == "support_data":
                    if len(dataset[var].dims) > 0:
                        if d[var].dims[0] in epoch_list:
                            _warn_or_except(f"ISTP Compliance Warning: VALIDMAX required for variable {var}", terminate_on_warning)

            if "FILLVAL" not in d[var].attrs:
                if var_type.lower() == "data":
                    _warn_or_except(f"ISTP Compliance Warning: FILLVAL required for variable {var}", terminate_on_warning)
                    fillval = _dtype_to_fillval(d[var])
                    d[var].attrs["FILLVAL"] = fillval
                    _warn_or_except(
                        f"ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}", terminate_on_warning
                    )
                elif var_type.lower() == "support_data":
                    if len(dataset[var].dims) > 0:
                        if d[var].dims[0] in epoch_list:
                            _warn_or_except(f"ISTP Compliance Warning: FILLVAL required for variable {var}", terminate_on_warning)
                            fillval = _dtype_to_fillval(d[var])
                            d[var].attrs["FILLVAL"] = fillval
                            _warn_or_except(
                                f"ISTP Compliance Action: Automatically set FILLVAL to {fillval} for variable {var}",
                                terminate_on_warning,
                            )


def _label_checker(dataset: xr.Dataset, terminate_on_warning: bool = False) -> List[str]:
    # NOTE: This may add attributes to the dataset object!

    # This variable will capture all ISTP compliant variables
    istp_label_list = []

    # Loop through the data
    for var in dataset:
        # Determine ISTP compliant variables
        for att in dataset[var].attrs:
            if att.startswith("LABL_PTR"):
                if (dataset[var].attrs[att] in dataset) or (dataset[var].attrs[att] in dataset.coords):
                    istp_label_list.append(dataset[var].attrs[att])
                else:
                    _warn_or_except(
                        f"ISTP Compliance Warning: variable {var} listed {dataset[var].attrs[att]} as its {att}.  However, it was not found in the dataset.",
                        terminate_on_warning,
                    )

    istp_label_list = list(set(istp_label_list))

    for l in istp_label_list:
        if "VAR_TYPE" not in dataset[l].attrs:
            dataset[l].attrs["VAR_TYPE"] = "metadata"

    return istp_label_list


def _unixtime_to_cdf_time(unixtime_data: xr.DataArray, cdf_epoch: bool = False, cdf_epoch16: bool = False) -> npt.NDArray:
    if cdf_epoch:
        return cdfepoch.timestamp_to_cdfepoch(unixtime_data)
    if cdf_epoch16:
        return cdfepoch.timestamp_to_cdfepoch16(unixtime_data)
    return cdfepoch.timestamp_to_tt2000(unixtime_data)


def _datetime_to_cdf_time(
    datetime_array: xr.DataArray,
    cdf_epoch: bool = False,
    cdf_epoch16: bool = False,
    attribute_name: str = "",
) -> object:
    if attribute_name:
        datetime_data = datetime_array.attrs[attribute_name]
    else:
        datetime_data = datetime_array.data
    datetime64_data = np.atleast_1d(np.array(datetime_data, dtype="datetime64[ns]"))
    cdf_epoch = False
    cdf_epoch16 = False
    if "CDF_DATA_TYPE" in datetime_array.attrs:
        if datetime_array.attrs["CDF_DATA_TYPE"] == "CDF_EPOCH":
            cdf_epoch = True
        elif datetime_array.attrs["CDF_DATA_TYPE"] == "CDF_EPOCH16":
            cdf_epoch16 = True

    if cdf_epoch16 or cdf_epoch:
        dtype_for_time_data = np.float64
    else:
        dtype_for_time_data = np.int64  # type: ignore

    years = datetime64_data.astype("datetime64[Y]").astype("int64") + 1970
    months = datetime64_data.astype("datetime64[M]").astype("int64") % 12 + 1
    days = np.zeros(len(datetime64_data), dtype=np.int64)
    i = 0
    for i in range(len(datetime64_data)):
        day = ((datetime64_data[i] - np.datetime64(f"{years[i]}-{months[i]:02d}", "M")) / 86400000000000).astype("int64") + 1
        days[i] = day.item()
        i += 1
    hours = datetime64_data.astype("datetime64[h]").astype("int64") % 24
    minutes = datetime64_data.astype("datetime64[m]").astype("int64") % 60
    seconds = datetime64_data.astype("datetime64[s]").astype("int64") % 60
    milliseconds = datetime64_data.astype("datetime64[ms]").astype("int64") % 1000
    microseconds = datetime64_data.astype("datetime64[us]").astype("int64") % 1000
    nanoseconds = datetime64_data.astype("datetime64[ns]").astype("int64") % 1000
    picoseconds = 0

    cdf_time_data = np.zeros(len(datetime64_data), dtype=dtype_for_time_data)
    for i in range(len(datetime64_data)):
        dd_to_convert = [
            years[i],
            months[i],
            days[i],
            hours[i],
            minutes[i],
            seconds[i],
            milliseconds[i],
            microseconds[i],
            nanoseconds[i],
            picoseconds,
        ]
        if np.isnat(datetime64_data[i]):
            if cdf_epoch16:
                cdf_time_data[i] == np.complex128(complex(-1e30, -1e30))
            elif cdf_epoch:
                cdf_time_data[i] == np.float64(-1e30)
            else:
                cdf_time_data[i] == np.int64(-9223372036854775808)
        else:
            if cdf_epoch16:
                converted_data = cdfepoch.compute(dd_to_convert)
            elif cdf_epoch:
                converted_data = cdfepoch.compute(dd_to_convert[0:7])
            else:
                converted_data = cdfepoch.compute(dd_to_convert[0:9])
            cdf_time_data[i] = converted_data

    return cdf_time_data


def xarray_to_cdf(
    xarray_dataset: xr.Dataset,
    file_name: str,
    unix_time_to_cdf_time: bool = False,
    istp: bool = True,
    terminate_on_warning: bool = False,
    auto_fix_depends: bool = True,
    record_dimensions: List[str] = ["record0"],
    compression: int = 0,
    nan_to_fillval: bool = True,
    from_unixtime: bool = False,
    from_datetime: bool = False,
    unixtime_to_cdftt2000: bool = False,
    datetime_to_cdftt2000: bool = True,
    datetime64_to_cdftt2000: bool = True,
) -> None:
    """
    This function converts XArray Dataset objects into CDF files.

    Parameters:
        xarray_dataset (xarray.Dataset): The XArray Dataset object that you'd like to convert into a CDF file
        file_name (str):  The path to the place the newly created CDF file
        unix_time_to_cdf_time (bool, optional): Whether or not to assume variables that will become a CDF_EPOCH/EPOCH16/TT2000 are a unix timestamp
        istp (bool, optional): Whether or not to do checks on the Dataset object to attempt to enforce CDF compliance
        terminate_on_warning (bool, optional): Whether or not to throw an error when given warnings or to continue trying to make the file
        auto_fix_depends (bool, optional): Whether or not to automatically add dependencies
        record_dimensions (list of str, optional): If the code cannot determine which dimensions should be made into CDF records, you may provide a list of them here
        compression (int, optional): The level of compression to gzip the data in the variables.  Default is no compression, standard is 6.
        nan_to_fillval (bool, optional): Convert all np.nan and np.datetime64('NaT') to the standard CDF FILLVALs.
        from_datetime (bool, optional, deprecated): Same as the datetime_to_cdftt2000 option
        from_unixtime (bool, optional, deprecated): Same as the unixtime_to_cdftt2000 option
        datetime_to_cdftt2000 (bool, optional, deprecated): Whether or not to convert variables named "epoch" or "epoch_X" to CDF_TT2000 from datetime objects
        datetime64_to_cdftt2000 (bool, optional, deprecated): Whether or not to convert variables named "epoch" or "epoch_X" to CDF_TT2000 from the numpy datetime64
        unixtime_to_cdftt2000 (bool, optional, deprecated): Whether or not to convert variables named "epoch" or "epoch_X" to CDF_TT2000 from unixtime
    Returns:
        None, but generates a CDF file

    Example CDF file from scratch:
        >>> # Import the needed libraries
        >>> from cdflib.xarray import xarray_to_cdf
        >>> import xarray as xr
        >>> import os
        >>> import urllib.request

        >>> # Create some fake data
        >>> var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
        >>> var_dims = ['epoch', 'direction']
        >>> data = xr.Variable(var_dims, var_data)

        >>> # Create fake epoch data
        >>> epoch_data = [1, 2, 3]
        >>> epoch_dims = ['epoch']
        >>> epoch = xr.Variable(epoch_dims, epoch_data)

        >>> # Combine the two into an xarray Dataset and export as CDF (this will print out many ISTP warnings)
        >>> ds = xr.Dataset(data_vars={'data': data, 'epoch': epoch})
        >>> xarray_to_cdf(ds, 'hello.cdf')

        >>> # Add some global attributes
        >>> global_attributes = {'Project': 'Hail Mary',
        >>>                      'Source_name': 'Thin Air',
        >>>                      'Discipline': 'None',
        >>>                      'Data_type': 'counts',
        >>>                      'Descriptor': 'Midichlorians in unicorn blood',
        >>>                      'Data_version': '3.14',
        >>>                      'Logical_file_id': 'SEVENTEEN',
        >>>                      'PI_name': 'Darth Vader',
        >>>                      'PI_affiliation': 'Dark Side',
        >>>                      'TEXT': 'AHHHHH',
        >>>                      'Instrument_type': 'Banjo',
        >>>                      'Mission_group': 'Impossible',
        >>>                      'Logical_source': ':)',
        >>>                      'Logical_source_description': ':('}

        >>> # Lets add a new coordinate variable for the "direction"
        >>> dir_data = [1, 2, 3]
        >>> dir_dims = ['direction']
        >>> direction = xr.Variable(dir_dims, dir_data)

        >>> # Recreate the Dataset with this new objects, and recreate the CDF
        >>> ds = xr.Dataset(data_vars={'data': data, 'epoch': epoch, 'direction':direction}, attrs=global_attributes)
        >>> os.remove('hello.cdf')
        >>> xarray_to_cdf(ds, 'hello.cdf')

    Example netCDF -> CDF conversion:
        >>> # Download a netCDF file (if needed)
        >>> fname = 'dn_magn-l2-hires_g17_d20211219_v1-0-1.nc'
        >>> url = ("https://lasp.colorado.edu/maven/sdc/public/data/sdc/web/cdflib_testing/dn_magn-l2-hires_g17_d20211219_v1-0-1.nc")
        >>> if not os.path.exists(fname):
        >>>     urllib.request.urlretrieve(url, fname)

        >>> # Load in the dataset, and set VAR_TYPES attributes (the most important attribute as far as this code is concerned)
        >>> goes_r_mag = xr.load_dataset("dn_magn-l2-hires_g17_d20211219_v1-0-1.nc")
        >>> for var in goes_r_mag:
        >>>     goes_r_mag[var].attrs['VAR_TYPE'] = 'data'
        >>> goes_r_mag['coordinate'].attrs['VAR_TYPE'] = 'support_data'
        >>> goes_r_mag['time'].attrs['VAR_TYPE'] = 'support_data'
        >>> goes_r_mag['time_orbit'].attrs['VAR_TYPE'] = 'support_data'

        >>> # Create the CDF file
        >>> xarray_to_cdf(goes_r_mag, 'hello.cdf')

    Processing Steps:
        1. Determines the list of dimensions that represent time-varying dimensions.  These ultimately become the "records" of the CDF file
            - If it is named "epoch" or "epoch_N", it is considered time-varying
            - If a variable points to another variable with a DEPEND_0 attribute, it is considered time-varying
            - If a variable has an attribute of VAR_TYPE equal to "data", it is time-varying
            - If a variable has an attribute of VAR_TYPE equal to "support_data" and it is 2 dimensional, it is time-varying
        2. Determine a list of "dimension" variables within the Dataset object
            - These are all coordinates in the dataset that are not time-varying
            - Additionally, variables that a DEPEND_N attribute points to are also considered dimensions
        3. Optionally, if ISTP=true, automatically add in DEPEND_0/1/2/etc attributes as necessary
        4. Optionally, if ISTP=true, check all variable attributes and global attributes are present
        5. Convert all data into either CDF_INT8, CDF_DOUBLE, CDF_UINT4, or CDF_CHAR
        6. Optionally, convert variables with the name "epoch" or "epoch_N" to CDF_TT2000
        7. Write all variables and global attributes to the CDF file!

    ISTP Warnings:
        If ISTP=true, these are some of the common things it will check:

        - Missing or invalid VAR_TYPE variable attributes
        - DEPEND_N missing from variables
        - DEPEND_N/LABL_PTR/UNIT_PTR/FORM_PTR are pointing to missing variables
        - Missing required global attributes
        - Conflicting global attributes
        - Missing an "epoch" dimension
        - DEPEND_N attribute pointing to a variable with uncompatible dimensions

    CDF Data Types:
        All variable data is automatically converted to one of the following CDF types, based on the type of data in the xarray Dataset:

        =============  ===============
        Numpy type     CDF Data Type
        =============  ===============
        np.datetime64  CDF_TIME_TT2000
        np.int8        CDF_INT1
        np.int16       CDF_INT2
        np.int32       CDF_INT4
        np.int64       CDF_INT8
        np.float16     CDF_FLOAT
        np.float32     CDF_FLOAT
        np.float64     CDF_DOUBLE
        np.uint8       CDF_UINT1
        np.uint16      CDF_UINT2
        np.uint32      CDF_UINT4
        np.complex_    CDF_EPOCH16
        np.str_        CDF_CHAR
        np.bytes_      CDF_CHAR
        object         CDF_CHAR
        datetime       CDF_TIME_TT2000
        =============  ===============

        If you want to attempt to cast your data to a different type, you need to add an attribute to your variable called "CDF_DATA_TYPE".
        xarray_to_cdf will read this attribute and override the default conversions.  Valid choices are:

        - Integers: CDF_INT1, CDF_INT2, CDF_INT4, CDF_INT8
        - Unsigned Integers: CDF_UINT1, CDF_UINT2, CDF_UINT4
        - Floating Point: CDF_REAL4, CDF_FLOAT, CDF_DOUBLE, CDF_REAL8
        - Time: CDF_EPOCH, CDF_EPOCH16, CDF_TIME_TT2000

    """

    if from_unixtime or unixtime_to_cdftt2000:
        warn(
            "from_unixtime and unixtime_to_cdftt2000 will eventually be phased out. Instead, use the more descriptive unix_time_to_cdf_time.",
            DeprecationWarning,
            stacklevel=2,
        )

    if from_datetime or datetime_to_cdftt2000:
        warn(
            "The from_datetime and datetime_to_cdftt2000 are obsolete. Python datetime objects are automatically converted to a CDF time. If you do not wish datetime objects to be converted, cast them to a different type prior to calling xarray_to_cdf()",
            DeprecationWarning,
            stacklevel=2,
        )

    if datetime64_to_cdftt2000:
        warn(
            "datetime64_to_cdftt2000 will eventually be phased out. Instead, datetime64 types will automatically be converted into a CDF time type. If you do not wish datetime64 arrays to be converted, cast them to a different type prior to calling xarray_to_cdf()",
            DeprecationWarning,
            stacklevel=2,
        )

    if unixtime_to_cdftt2000 or from_unixtime:
        unix_time_to_cdf_time = True

    if os.path.isfile(file_name):
        _warn_or_except(f"{file_name} already exists, cannot create CDF file.  Returning...", terminate_on_warning)
        return

    # Make a deep copy of the data before continuing
    dataset = xarray_dataset.copy()

    if nan_to_fillval:
        _convert_nans_to_fillval(dataset)

    if istp:
        # This checks all the variable and attribute names to ensure they are ISTP compliant.
        _validate_varatt_names(dataset, terminate_on_warning)

        # This creates a list of suspected or confirmed label variables
        _label_checker(dataset, terminate_on_warning)

        # This creates a list of suspected or confirmed dimension variables
        dim_vars = _dimension_checker(dataset, terminate_on_warning)

        # This creates a list of suspected or confirmed record variables
        depend_0_vars, time_varying_dimensions = _epoch_checker(dataset, dim_vars, terminate_on_warning)

        depend_0_vars = record_dimensions + depend_0_vars
        time_varying_dimensions = record_dimensions + time_varying_dimensions

        # After we do the first pass of checking for dimensions and record variables, lets do a second pass to make sure
        # we've got everything
        dim_vars = _recheck_dimensions_after_epoch_checker(dataset, time_varying_dimensions, dim_vars, terminate_on_warning)

        # This function will alter the attributes of the data variables if needed
        dataset = _add_depend_variables_to_dataset(
            dataset, dim_vars, depend_0_vars, time_varying_dimensions, terminate_on_warning, auto_fix_depends
        )

        _global_attribute_checker(dataset, terminate_on_warning)

        _variable_attribute_checker(dataset, depend_0_vars, terminate_on_warning)
    else:
        depend_0_vars = record_dimensions
        time_varying_dimensions = record_dimensions

    # Gather the global attributes, write them into the file
    glob_att_dict: Dict[str, Dict[int, Any]] = {}
    for ga in dataset.attrs:
        if hasattr(dataset.attrs[ga], "__iter__") and not isinstance(dataset.attrs[ga], str):
            i = 0
            glob_att_dict[ga] = {}
            for entry in dataset.attrs[ga]:
                glob_att_dict[ga][i] = entry
                i += 1
        else:
            glob_att_dict[ga] = {0: dataset.attrs[ga]}

    x = CDF(file_name)
    x.write_globalattrs(glob_att_dict)

    # Gather the variables, write them into the file
    datasets = (dataset, dataset.coords)
    for d in datasets:
        for var in d:
            var = cast(str, var)

            cdf_data_type, cdf_num_elements = _dtype_to_cdf_type(d[var])
            if cdf_data_type is None or cdf_num_elements is None:
                continue

            if len(d[var].dims) > 0:
                if var in time_varying_dimensions or var in depend_0_vars:
                    dim_sizes = d[var].shape[1:]
                    record_vary = True
                else:
                    dim_sizes = d[var].shape
                    record_vary = False
            else:
                dim_sizes = []
                record_vary = True

            var_data = d[var].data

            cdf_epoch = False
            cdf_epoch16 = False
            if "CDF_DATA_TYPE" in d[var].attrs:
                if d[var].attrs["CDF_DATA_TYPE"] == "CDF_EPOCH":
                    cdf_epoch = True
                elif d[var].attrs["CDF_DATA_TYPE"] == "CDF_EPOCH16":
                    cdf_epoch16 = True

            if (_is_datetime_array(d[var].data) and datetime_to_cdftt2000) or (
                _is_datetime64_array(d[var].data) and datetime64_to_cdftt2000
            ):
                var_data = _datetime_to_cdf_time(d[var], cdf_epoch=cdf_epoch, cdf_epoch16=cdf_epoch16)
            elif unix_time_to_cdf_time:
                if _is_istp_epoch_variable(var) or (
                    DATATYPES_TO_STRINGS[cdf_data_type] in ("CDF_EPOCH", "CDF_EPOCH16", "CDF_TIME_TT2000")
                ):
                    var_data = _unixtime_to_cdf_time(d[var].data, cdf_epoch=cdf_epoch, cdf_epoch16=cdf_epoch16)

            # Grab the attributes from xarray, and attempt to convert VALIDMIN and VALIDMAX to the same data type as the variable
            var_att_dict = {}
            for att in d[var].attrs:
                var_att_dict[att] = d[var].attrs[att]
                if (_is_datetime_array(d[var].attrs[att]) and datetime_to_cdftt2000) or (
                    _is_datetime64_array(d[var].attrs[att]) and datetime64_to_cdftt2000
                ):
                    att_data = _datetime_to_cdf_time(d[var], cdf_epoch=cdf_epoch, cdf_epoch16=cdf_epoch16, attribute_name=att)
                    var_att_dict[att] = [att_data, DATATYPES_TO_STRINGS[cdf_data_type]]
                elif unix_time_to_cdf_time:
                    if "TIME_ATTRS" in d[var].attrs:
                        if att in d[var].attrs["TIME_ATTRS"]:
                            if DATATYPES_TO_STRINGS[cdf_data_type] in ("CDF_EPOCH", "CDF_EPOCH16", "CDF_TIME_TT2000"):
                                att_data = _unixtime_to_cdf_time(d[var].attrs[att], cdf_epoch=cdf_epoch, cdf_epoch16=cdf_epoch16)
                                var_att_dict[att] = [att_data, DATATYPES_TO_STRINGS[cdf_data_type]]
                elif (att == "VALIDMIN" or att == "VALIDMAX" or att == "FILLVAL") and istp:
                    var_att_dict[att] = [d[var].attrs[att], DATATYPES_TO_STRINGS[cdf_data_type]]

            var_spec = {
                "Variable": var,
                "Data_Type": cdf_data_type,
                "Num_Elements": cdf_num_elements,
                "Rec_Vary": record_vary,
                "Dim_Sizes": list(dim_sizes),
                "Compress": compression,
            }

            x.write_var(var_spec, var_attrs=var_att_dict, var_data=var_data)

    x.close()

    return
