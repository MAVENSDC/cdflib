import os

import numpy as np
import pytest
import xarray as xr

from cdflib.xarray import xarray_to_cdf
from cdflib.xarray.xarray_to_cdf import ISTPError

sample_global_attributes = {
    "Project": "Hail Mary",
    "Source_name": "Thin Air",
    "Discipline": "None",
    "Data_type": "counts",
    "Descriptor": "Midichlorians in unicorn blood",
    "Data_version": "3.14",
    "Logical_file_id": "SEVENTEEN",
    "PI_name": "Darth Vader",
    "PI_affiliation": "Dark Side",
    "TEXT": "AHHHHH",
    "Instrument_type": "Banjo",
    "Mission_group": "Impossible",
    "Logical_source": ":)",
    "Logical_source_description": ":(",
}
sample_variable_attributes = {
    "CATDESC": "data",
    "DISPLAY_TYPE": "spectrogram",
    "FIELDNAM": "test",
    "FORMAT": "test",
    "UNITS": "test",
    "VALIDMIN": 0,
    "VALIDMAX": 10,
    "FILLVAL": np.int64(-9223372036854775808),
}
sample_data_variable_attributes = sample_variable_attributes | {"VAR_TYPE": "data", "LABLAXIS": "test"}
sample_support_variable_attributes = sample_variable_attributes | {"VAR_TYPE": "support_data"}


def test_istp_dimension_attribute_checker():
    # Create a bare-minimum ISTP compliant file
    pytest.importorskip("xarray")

    var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
    var_dims = ["epoch", "direction"]
    data = xr.Variable(var_dims, var_data, sample_data_variable_attributes | {"DEPEND_0": "epoch", "DEPEND_1": "direction"})
    epoch_data = [1, 2, 3]
    epoch_dims = ["epoch"]
    epoch = xr.Variable(epoch_dims, epoch_data, sample_support_variable_attributes)
    dir_data = [1, 2, 3]
    dir_dims = ["direction"]
    direction = xr.Variable(dir_dims, dir_data, sample_support_variable_attributes)

    ds = xr.Dataset(data_vars={"data": data, "epoch": epoch, "direction": direction}, attrs=sample_global_attributes)

    xarray_to_cdf(ds, "hello.cdf", auto_fix_depends=False, terminate_on_warning=True)
    os.remove("hello.cdf")


def test_istp_dimension_attribute_checker_with_typo():
    # Put an extra "n" on the end of "DEPEND_1":"directionn" from the last test,
    # and make sure it fails
    pytest.importorskip("xarray")

    var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
    var_dims = ["epoch", "direction"]
    data = xr.Variable(var_dims, var_data, sample_data_variable_attributes | {"DEPEND_0": "epoch", "DEPEND_1": "directionn"})
    epoch_data = [1, 2, 3]
    epoch_dims = ["epoch"]
    epoch = xr.Variable(epoch_dims, epoch_data, sample_support_variable_attributes)
    dir_data = [1, 2, 3]
    dir_dims = ["direction"]
    direction = xr.Variable(dir_dims, dir_data, sample_support_variable_attributes)

    ds = xr.Dataset(data_vars={"data": data, "epoch": epoch, "direction": direction}, attrs=sample_global_attributes)
    with pytest.raises(ISTPError):
        xarray_to_cdf(ds, "hello.cdf", auto_fix_depends=False, terminate_on_warning=True)

    if os.path.exists("hello.cdf"):
        os.remove("hello.cdf")


def test_istp_support_data_has_depends():
    # We're going to test that a support_data variable is allowed to have its own DEPEND_{i}
    pytest.importorskip("xarray")

    var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
    var_dims = ["epoch", "direction"]
    data = xr.Variable(var_dims, var_data, sample_data_variable_attributes | {"DEPEND_0": "epoch", "DEPEND_1": "direction"})
    support_data = [1, 2, 3]
    support_dims = ["direction"]
    support = xr.Variable(support_dims, support_data, sample_support_variable_attributes | {"DEPEND_1": "direction"})
    epoch_data = [1, 2, 3]
    epoch_dims = ["epoch"]
    epoch = xr.Variable(epoch_dims, epoch_data, sample_support_variable_attributes)
    dir_data = [1, 2, 3]
    dir_dims = ["direction"]
    direction = xr.Variable(dir_dims, dir_data, sample_support_variable_attributes)

    ds = xr.Dataset(
        data_vars={"data": data, "epoch": epoch, "direction": direction, "support": support}, attrs=sample_global_attributes
    )

    xarray_to_cdf(ds, "hello.cdf", auto_fix_depends=False, terminate_on_warning=True)
    os.remove("hello.cdf")


def test_istp_support_data_has_depends_expected_failure():
    # We're going to mimic the previous test, but give support a DEPEND_0 of "epoch".
    # This should make it fail, because it does not have enough dimensions
    pytest.importorskip("xarray")

    var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
    var_dims = ["epoch", "direction"]
    data = xr.Variable(var_dims, var_data, sample_data_variable_attributes | {"DEPEND_0": "epoch", "DEPEND_1": "direction"})
    support_data = [1, 2, 3]
    support_dims = ["direction"]
    support = xr.Variable(
        support_dims, support_data, sample_support_variable_attributes | {"DEPEND_0": "epoch", "DEPEND_1": "direction"}
    )
    epoch_data = [1, 2, 3]
    epoch_dims = ["epoch"]
    epoch = xr.Variable(epoch_dims, epoch_data, sample_support_variable_attributes)
    dir_data = [1, 2, 3]
    dir_dims = ["direction"]
    direction = xr.Variable(dir_dims, dir_data, sample_support_variable_attributes)

    ds = xr.Dataset(
        data_vars={"data": data, "epoch": epoch, "direction": direction, "support": support}, attrs=sample_global_attributes
    )

    with pytest.raises(ISTPError):
        xarray_to_cdf(ds, "hello.cdf", auto_fix_depends=False, terminate_on_warning=True)

    if os.path.exists("hello.cdf"):
        os.remove("hello.cdf")
