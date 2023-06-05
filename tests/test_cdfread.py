import pathlib

import pytest

from cdflib import CDF


@pytest.mark.parametrize("fname", ["psp_fld_l2_mag_rtn_1min_20200104_v02.cdf", "de2_ion2s_rpa_19830213_v01.cdf"])
def test_read(fname):
    fname = (pathlib.Path(__file__) / ".." / "testfiles" / fname).resolve()
    cdf = CDF(fname)

    info = cdf.cdf_info()

    # Smoke test variable access
    for var in info.zVariables:
        cdf.varattsget(var)
        cdf.varget(var)

    with CDF(fname) as cdf:
        cdf.cdf_info()


def test_nonexist_file_errors(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        CDF(tmp_path / "nonexist.cdf")
