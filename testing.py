import pds2_cdf
import pytplot
import numpy as np

rbsp_file = pds2_cdf.CDF("C:/temp/mavencdfs/rbsp-a-rbspice_lev-3_esrhelt_20170619_v1.1.9-00.cdf")

print(rbsp_file.attget(0,0))

print(rbsp_file.attget("UNITS",5))

print(pds2_cdf.cdfepoch.encode(rbsp_file.varget(variable='Epoch')))
print(rbsp_file.epochrange("Epoch", starttime = pds2_cdf.cdfepoch.compute_tt2000([2017,6,19,5,5,5]), endtime = pds2_cdf.cdfepoch.compute_tt2000([2017,6,19,6,6,6])))


