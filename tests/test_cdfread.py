import os
import cdflib


def test_read():
    fname = 'helios.cdf'
    if not os.path.exists(fname):
        import urllib.request
        urllib.request.urlretrieve(
            'http://helios-data.ssl.berkeley.edu/data/E1_experiment/New_proton_corefit_data_2017/cdf/helios1/1974/h1_1974_346_corefit.cdf',
            fname)
    cdf = cdflib.CDF(fname)
