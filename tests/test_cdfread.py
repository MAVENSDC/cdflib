import pathlib

import cdflib


def test_read():
    fname = (pathlib.Path(__file__) / '..' / 'testfiles' /
             'psp_fld_l2_mag_rtn_1min_20200104_v02.cdf')
    cdf = cdflib.CDF(fname)
    info = cdf.cdf_info()

    assert isinstance(info, dict)

    varatts = cdf.varattsget('psp_fld_l2_mag_RTN_1min')
    assert isinstance(varatts, dict)
