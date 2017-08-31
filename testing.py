import pds2_cdf
import pytplot
import numpy as np

# rbsp_file = pds2_cdf.CDF("C:/temp/mavencdfs/rbsp-a-rbspice_lev-3_esrhelt_20170619_v1.1.9-00.cdf")
#  
# print(rbsp_file.attget(0,0))
#  
# print(rbsp_file.attget("UNITS",5))
#  
# print(pds2_cdf.cdfepoch.encode(rbsp_file.varget(variable='Epoch')))
# print(rbsp_file.epochrange("Epoch", starttime = pds2_cdf.cdfepoch.compute_tt2000([2017,6,19,5,5,5]), endtime = pds2_cdf.cdfepoch.compute_tt2000([2017,6,19,6,6,6])))

#tha_file= pds2_cdf.CDF("C:/temp/mavencdfs/tha_l1_fgm_20090101_v01.cdf")
#euvl2_file = pds2_cdf.CDF("C:/temp/mavencdfs/mvn_euv_l2_bands_20170725_v09_r03.cdf")
#euvl3_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_euv_l3_minute_20170725_v09_r03.cdf")
#lpw_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_lpw_l2_lpiv_20170725_v02_r02.cdf")
#sepanc_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_sep_l2_anc_20170725_v06_r02.cdf")
#sepl2_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_sep_l2_s1-cal-svy-full_20170725_v04_r04.cdf")
sta_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_sta_l2_db-1024tof_20170725_v01_r05.cdf")
#swe_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_swe_l2_svyspec_20170725_v04_r04.cdf")
#swi_file= pds2_cdf.CDF("C:/temp/mavencdfs/mvn_swi_l2_onboardsvyspec_20170725_v01_r00.cdf")

print(sta_file.globalattsget())