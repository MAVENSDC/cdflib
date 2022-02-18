import pathlib

import cdflib

fname = (pathlib.Path(__file__) / '..' / 'testfiles' /
         'psp_fld_l2_mag_rtn_1min_20200104_v02.cdf')


def test_read():
    cdf = cdflib.CDF(fname)

    info = cdf.cdf_info()
    assert isinstance(info, dict)

    varatts = cdf.varattsget('psp_fld_l2_mag_RTN_1min')
    assert isinstance(varatts, dict)


def test_context():
    with cdflib.CDF(fname) as cdf:
        cdf.cdf_info()
