import pathlib

import cdflib

fname = pathlib.Path(__file__) / ".." / "testfiles" / "fa_esa_l2_eeb_00000000_v01.cdf"


def test_read():
    cdf = cdflib.CDF(fname)

    cdf.cdf_info()
    varatts = cdf.varattsget("eflux")
    assert isinstance(varatts, dict)


def test_context():
    with cdflib.CDF(fname) as cdf:
        cdf.cdf_info()
