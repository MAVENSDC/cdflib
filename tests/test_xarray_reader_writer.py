import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import urllib.request
import os

def test_mms():
    fname = 'mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.cdf'
    url = ("https://lasp.colorado.edu/maven/sdc/public/data/sdc/web/cdflib_testing/mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.cdf")
    if not os.path.exists(fname):
        urllib.request.urlretrieve(url, fname)

    a = cdflib.cdf_to_xarray("mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.cdf",
                             to_unixtime=True, fillval_to_nan=True)
    cdflib.xarray_to_cdf(a, 'mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf',
                         from_unixtime=True)
    b = cdflib.cdf_to_xarray('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf',
                             to_unixtime=True, fillval_to_nan=True)
    os.remove('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf')

