import pathlib

import cdflib


def test_read():
    fname = (pathlib.Path(__file__) / '..' / 'testfiles' /
             'psp_fld_l2_mag_rtn_1min_20200104_v02.cdf')
    cdflib.CDF(fname)
