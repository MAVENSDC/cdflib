
'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(x, 'hello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('hello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello.cdf')

asdf = xr.load_dataset("C:/Work/cdf_test_files/mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.nc")
cdflib.xarray_to_cdf(asdf, 'hello2.cdf')
z = cdflib.cdf_to_xarray('hello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello2.cdf')
'''

'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(x, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf')

asdf = xr.load_dataset("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.nc")
cdflib.xarray_to_cdf(asdf, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf')
z = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf')
'''

'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(x, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello.cdf')

asdf = xr.load_dataset("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.nc")
cdflib.xarray_to_cdf(asdf, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf')
z = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdfhello2.cdf')
'''

'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

x = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms2_fgm_srvy_l2_20160809_v4.47.0.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(x, 'mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello.cdf', from_unixtime=True)
y = cdflib.cdf_to_xarray('mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello.cdf')

asdf = xr.load_dataset("C:/Work/cdf_test_files/mms2_fgm_srvy_l2_20160809_v4.47.0.nc")
cdflib.xarray_to_cdf(asdf, 'mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello2.cdf')
z = cdflib.cdf_to_xarray('mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_fgm_srvy_l2_20160809_v4.47.0.cdfhello2.cdf')
'''


'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

asdf = xr.load_dataset("C:/Work/cdf_test_files/dn_magn-l2-hires_g17_d20211219_v1-0-1.nc")
for var in asdf:
    asdf[var].attrs['VAR_TYPE'] = 'data'

cdflib.xarray_to_cdf(asdf, 'hello4.cdf')
z = cdflib.cdf_to_xarray('hello4.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello4.cdf')
'''


'''
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
asdf = xr.load_dataset("C:/Work/cdf_test_files/MGITM_LS180_F130_150615.nc")
for var in asdf:
    asdf[var].attrs['VAR_TYPE'] = 'data'
asdf['Longitude'].attrs['VAR_TYPE'] = 'support_data'
asdf['Latitude'].attrs['VAR_TYPE'] = 'support_data'
asdf['altitude'].attrs['VAR_TYPE'] = 'support_data'
asdf['latitude'] = asdf['Latitude']
asdf['longitude'] = asdf['Longitude']
cdflib.xarray_to_cdf(asdf, 'hellohello.cdf')
z = cdflib.cdf_to_xarray('hellohello.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hellohello.cdf')
'''


import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
asdf = xr.load_dataset("C:/Work/cdf_test_files/dn_magn-l2-hires_g17_d20211219_v1-0-1.nc")
for var in asdf:
    asdf[var].attrs['VAR_TYPE'] = 'data'
asdf['coordinate'].attrs['VAR_TYPE'] = 'support_data'
asdf['time'].attrs['VAR_TYPE'] = 'support_data'
asdf['time_orbit'].attrs['VAR_TYPE'] = 'support_data'
cdflib.xarray_to_cdf(asdf, 'hello5.cdf')
z = cdflib.cdf_to_xarray('hello5.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello5.cdf')



'''

# WHY DOES THIS CREATE A NEW DIMENSION FOR THE EVENT!!!

import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
asdf = xr.load_dataset("C:/Work/cdf_test_files/SABER_L2B_2021020_103692_02.07.nc")
for var in asdf:
    asdf[var].attrs['VAR_TYPE'] = 'data'
asdf['event'].attrs['VAR_TYPE'] = 'support_data'
asdf['sclatitude'].attrs['VAR_TYPE'] = 'support_data'
asdf['sclongitude'].attrs['VAR_TYPE'] = 'support_data'
asdf['scaltitude'].attrs['VAR_TYPE'] = 'support_data'
cdflib.xarray_to_cdf(asdf, 'hello6.cdf')
z = cdflib.cdf_to_xarray('hello6.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('hello6.cdf')
'''