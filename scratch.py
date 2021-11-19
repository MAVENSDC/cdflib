import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

#x = cdf_to_xarray('C:/Work/Code Repos/PyTplot/themis_data/thg/l2/mag/han/2007/thg_l2_mag_han_20070323_v01.cdf')

#x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/rbsp-a-rbspice_lev-3_esrhelt_20190117_v1.1.9-00.cdf", to_unixtime=True, fillval_to_nan=True)
x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_lpw_l2_lpiv_20180717_v02_r02.cdf", to_unixtime=True, fillval_to_nan=True)
print(x)
cdflib.xarray_to_cdf(x, 'hello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('hello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello.cdf')

asdf = xr.load_dataset("C:/Work/cdf_test_files/mvn_lpw_l2_lpiv_20180717_v02_r02.nc")
cdflib.xarray_to_cdf(asdf, 'hello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('hello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello.cdf')


print(y)