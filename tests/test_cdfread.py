import os
import urllib.request
import cdflib


def test_read():
    fname = 'helios.cdf'
    url = ("http://helios-data.ssl.berkeley.edu/data/"
           "E1_experiment/New_proton_corefit_data_2017/"
           "cdf/helios1/1974/h1_1974_346_corefit.cdf")
    if not os.path.exists(fname):
        urllib.request.urlretrieve(url, fname)
    cdflib.CDF(fname)
