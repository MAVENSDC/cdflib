import pathlib

import pytest


@pytest.fixture(params=["psp_fld_l2_mag_rtn_1min_20200104_v02.cdf", "de2_ion2s_rpa_19830213_v01.cdf"])
def cdf_path(request):
    """
    Returns a series of CDF file paths which can be used for smoke testing.
    """
    return (pathlib.Path(__file__) / ".." / "testfiles" / request.param).resolve()
