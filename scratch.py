#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0.nc")
cdflib.xarray_to_cdf(c, 'mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms1_fpi_brst_l2_des-moms_20151016130334_v3.3.0-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4.nc")
cdflib.xarray_to_cdf(c, 'mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_epd-eis_srvy_l2_extof_20160809_v3.0.4-created-from-netcdf-input.cdf')
#

#

### GOOD ONE FOR DEMO?!

import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mms2_fgm_srvy_l2_20160809_v4.47.0.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mms2_fgm_srvy_l2_20160809_v4.47.0.nc")
cdflib.xarray_to_cdf(c, 'mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mms2_fgm_srvy_l2_20160809_v4.47.0-created-from-netcdf-input.cdf')
#

#

### REALLY GOOD EXAMPLE

import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
c = xr.load_dataset("C:/Work/cdf_test_files/MGITM_LS180_F130_150615.nc")
for var in c:
    c[var].attrs['VAR_TYPE'] = 'data'
c = c.rename({'Latitude':'latitude', 'Longitude':'longitude'})
c['longitude'].attrs['VAR_TYPE'] = 'support_data'
c['latitude'].attrs['VAR_TYPE'] = 'support_data'
c['altitude'].attrs['VAR_TYPE'] = 'support_data'

cdflib.xarray_to_cdf(c, 'MGITM_LS180_F130_150615-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('MGITM_LS180_F130_150615-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('MGITM_LS180_F130_150615-created-from-netcdf-input.cdf')
#

#

### ANOTHER REALLY GOOD EXAMPLE

import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
c = xr.load_dataset("C:/Work/cdf_test_files/dn_magn-l2-hires_g17_d20211219_v1-0-1.nc")
for var in c:
    c[var].attrs['VAR_TYPE'] = 'data'
c['coordinate'].attrs['VAR_TYPE'] = 'support_data'
c['time'].attrs['VAR_TYPE'] = 'support_data'
c['time_orbit'].attrs['VAR_TYPE'] = 'support_data'
cdflib.xarray_to_cdf(c, 'dn_magn-l2-hires_g17_d20211219_v1-0-1-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('dn_magn-l2-hires_g17_d20211219_v1-0-1-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('dn_magn-l2-hires_g17_d20211219_v1-0-1-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os
c = xr.load_dataset("C:/Work/cdf_test_files/SABER_L2B_2021020_103692_02.07.nc")
for var in c:
    c[var].attrs['VAR_TYPE'] = 'data'
c['event'].attrs['VAR_TYPE'] = 'support_data'
c['sclatitude'].attrs['VAR_TYPE'] = 'support_data'
c['sclongitude'].attrs['VAR_TYPE'] = 'support_data'
c['scaltitude'].attrs['VAR_TYPE'] = 'support_data'
cdflib.xarray_to_cdf(c, 'SABER_L2B_2021020_103692_02.07-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('SABER_L2B_2021020_103692_02.07-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('SABER_L2B_2021020_103692_02.07-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_euv_l3_minute_20201130_v14_r02.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_euv_l3_minute_20201130_v14_r02-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_euv_l3_minute_20201130_v14_r02-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_euv_l3_minute_20201130_v14_r02-created-from-cdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_lpw_l2_lpiv_20180717_v02_r02.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_lpw_l2_lpiv_20180717_v02_r02.nc")
cdflib.xarray_to_cdf(c, 'mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_lpiv_20180717_v02_r02-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_lpw_l2_lpnt_20180717_v03_r01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_lpw_l2_lpnt_20180717_v03_r01.nc")
cdflib.xarray_to_cdf(c, 'mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_lpnt_20180717_v03_r01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_lpw_l2_mrgscpot_20180717_v02_r01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_lpw_l2_mrgscpot_20180717_v02_r01.nc")
cdflib.xarray_to_cdf(c, 'mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_lpw_l2_mrgscpot_20180717_v02_r01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_sep_l2_anc_20210501_v06_r00.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_sep_l2_anc_20210501_v06_r00-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_sep_l2_anc_20210501_v06_r00-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_sep_l2_anc_20210501_v06_r00-created-from-cdf-input.cdf')
#


#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_sep_l2_s2-raw-svy-full_20191231_v04_r05.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_sep_l2_s2-raw-svy-full_20191231_v04_r05-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_sep_l2_s2-raw-svy-full_20191231_v04_r05-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_sep_l2_s2-raw-svy-full_20191231_v04_r05-created-from-cdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_sta_l2_d1-32e4d16a8m_20201130_v02_r04.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_sta_l2_d1-32e4d16a8m_20201130_v02_r04-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_sta_l2_d1-32e4d16a8m_20201130_v02_r04-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_sta_l2_d1-32e4d16a8m_20201130_v02_r04-created-from-cdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_swe_l2_arc3d_20180717_v04_r02.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_swe_l2_arc3d_20180717_v04_r02-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_swe_l2_arc3d_20180717_v04_r02-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swe_l2_arc3d_20180717_v04_r02-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_swe_l2_arc3d_20180717_v04_r02.nc")
cdflib.xarray_to_cdf(c, 'mvn_swe_l2_arc3d_20180717_v04_r02-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_swe_l2_arc3d_20180717_v04_r02-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swe_l2_arc3d_20180717_v04_r02-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_swe_l2_svyspec_20180718_v04_r04.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_swe_l2_svyspec_20180718_v04_r04-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_swe_l2_svyspec_20180718_v04_r04-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swe_l2_svyspec_20180718_v04_r04-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_swe_l2_svyspec_20180718_v04_r04.nc")
cdflib.xarray_to_cdf(c, 'mvn_swe_l2_svyspec_20180718_v04_r04-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_swe_l2_svyspec_20180718_v04_r04-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swe_l2_svyspec_20180718_v04_r04-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_swi_l2_finearc3d_20180720_v01_r01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_swi_l2_finearc3d_20180720_v01_r01.nc")
cdflib.xarray_to_cdf(c, 'mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swi_l2_finearc3d_20180720_v01_r01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/mvn_swi_l2_onboardsvyspec_20180720_v01_r01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/mvn_swi_l2_onboardsvyspec_20180720_v01_r01.nc")
cdflib.xarray_to_cdf(c, 'mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('mvn_swi_l2_onboardsvyspec_20180720_v01_r01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/omni_hro2_1min_20151001_v01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'omni_hro2_1min_20151001_v01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('omni_hro2_1min_20151001_v01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('omni_hro2_1min_20151001_v01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/omni_hro2_1min_20151001_v01.nc")
cdflib.xarray_to_cdf(c, 'omni_hro2_1min_20151001_v01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('omni_hro2_1min_20151001_v01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('omni_hro2_1min_20151001_v01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

c = xr.load_dataset("C:/Work/cdf_test_files/raids_nirs_20100823_v1.1.nc")
cdflib.xarray_to_cdf(c, 'raids_nirs_20100823_v1.1-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('raids_nirs_20100823_v1.1-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('raids_nirs_20100823_v1.1-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/rbsp-a_magnetometer_1sec-gsm_emfisis-l3_20190122_v1.6.2.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'rbsp-a_magnetometer_1sec-gsm_emfisis-l3_20190122_v1.6.2-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('rbsp-a_magnetometer_1sec-gsm_emfisis-l3_20190122_v1.6.2-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('rbsp-a_magnetometer_1sec-gsm_emfisis-l3_20190122_v1.6.2-created-from-cdf-input.cdf')

#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

c = xr.load_dataset("C:/Work/cdf_test_files/see__L3_2021009_012_01.ncdf")
cdflib.xarray_to_cdf(c, 'see__L3_2021009_012_01.ncdfhello2.cdf')
d = cdflib.cdf_to_xarray('see__L3_2021009_012_01.ncdfhello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('see__L3_2021009_012_01.ncdfhello2.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

c = xr.load_dataset("C:/Work/cdf_test_files/see__xps_L2A_2021006_012_02.ncdf")
cdflib.xarray_to_cdf(c, 'see__xps_L2A_2021006_012_02.ncdfhello2.cdf')
d = cdflib.cdf_to_xarray('see__xps_L2A_2021006_012_02.ncdfhello2.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('see__xps_L2A_2021006_012_02.ncdfhello2.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

c = xr.load_dataset("C:/Work/cdf_test_files/sgpsondewnpnC1.nc")
cdflib.xarray_to_cdf(c, 'sgpsondewnpnC1-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('sgpsondewnpnC1-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('sgpsondewnpnC1-created-from-netcdf-input.cdf')
#


import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a = cdflib.cdf_to_xarray("C:/Work/cdf_test_files/thc_l2_sst_20210709_v01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'thc_l2_sst_20210709_v01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('thc_l2_sst_20210709_v01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('thc_l2_sst_20210709_v01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/thc_l2_sst_20210709_v01.nc")
cdflib.xarray_to_cdf(c, 'thc_l2_sst_20210709_v01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('thc_l2_sst_20210709_v01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('thc_l2_sst_20210709_v01-created-from-netcdf-input.cdf')


#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/thg_l2_mag_amd_20070323_v01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'thg_l2_mag_amd_20070323_v01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('thg_l2_mag_amd_20070323_v01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('thg_l2_mag_amd_20070323_v01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/thg_l2_mag_amd_20070323_v01.nc")
cdflib.xarray_to_cdf(c, 'thg_l2_mag_amd_20070323_v01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('thg_l2_mag_amd_20070323_v01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('thg_l2_mag_amd_20070323_v01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/wi_elsp_3dp_20210115_v01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'wi_elsp_3dp_20210115_v01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('wi_elsp_3dp_20210115_v01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('wi_elsp_3dp_20210115_v01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/wi_elsp_3dp_20210115_v01.nc")
cdflib.xarray_to_cdf(c, 'wi_elsp_3dp_20210115_v01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('wi_elsp_3dp_20210115_v01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('wi_elsp_3dp_20210115_v01-created-from-netcdf-input.cdf')
#

#
import cdflib
import xarray as xr
import numpy as np
from cdflib.epochs import CDFepoch as cdfepoch
import os

a =  cdflib.cdf_to_xarray("C:/Work/cdf_test_files/wi_k0_spha_20210121_v01.cdf", to_unixtime=True, fillval_to_nan=True)
cdflib.xarray_to_cdf(a, 'wi_k0_spha_20210121_v01-created-from-cdf-input.cdf', from_unixtime=True)
b = cdflib.cdf_to_xarray('wi_k0_spha_20210121_v01-created-from-cdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('wi_k0_spha_20210121_v01-created-from-cdf-input.cdf')

c = xr.load_dataset("C:/Work/cdf_test_files/wi_elsp_3dp_20210115_v01.nc")
cdflib.xarray_to_cdf(c, 'wi_k0_spha_20210121_v01-created-from-netcdf-input.cdf')
d = cdflib.cdf_to_xarray('wi_k0_spha_20210121_v01-created-from-netcdf-input.cdf', to_unixtime=True, fillval_to_nan=True)
os.remove('wi_k0_spha_20210121_v01-created-from-netcdf-input.cdf')
#




import cdflib
import xarray as xr
import os
var_data = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
var_dims = ['epoch', 'direction']
data = xr.Variable(var_dims, var_data)
epoch_data = [1, 2, 3]
epoch_dims = ['epoch']
epoch = xr.Variable(epoch_dims, epoch_data)
ds = xr.Dataset(data_vars={'data': data, 'epoch': epoch})
cdflib.xarray_to_cdf(ds, 'hello.cdf')
os.remove('hello.cdf')
global_attributes = {'Project': 'Hail Mary',
                     'Source_name': 'Thin Air',
                     'Discipline': 'None',
                     'Data_type': 'counts',
                     'Descriptor': 'Midichlorians in unicorn blood',
                     'Data_version': '3.14',
                     'Logical_file_id': 'SEVENTEEN',
                     'PI_name': 'Darth Vader',
                     'PI_affiliation': 'Dark Side',
                     'TEXT': 'AHHHHH',
                     'Instrument_type': 'Banjo',
                     'Mission_group': 'Impossible',
                     'Logical_source': ':)',
                     'Logical_source_description': ':('}
data = xr.Variable(var_dims, var_data)
epoch = xr.Variable(epoch_dims, epoch_data)
ds = xr.Dataset(data_vars={'data': data, 'epoch': epoch}, attrs=global_attributes)
cdflib.xarray_to_cdf(ds, 'hello.cdf')
os.remove('hello.cdf')
dir_data = [1, 2, 3]
dir_dims = ['direction']
direction = xr.Variable(dir_dims, dir_data)
ds = xr.Dataset(data_vars={'data': data, 'epoch': epoch, 'direction':direction}, attrs=global_attributes)
cdflib.xarray_to_cdf(ds, 'hello.cdf')
os.remove('hello.cdf')
