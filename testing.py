import pds2_cdf
import pytplot
import numpy as np

swea_cdf_file = pds2_cdf.CDF("C:/temp/rbsp-a-rbspice_lev-3_esrhelt_20170619_v1.1.9-00.cdf")
print(swea_cdf_file.varattsget(variable='Epoch'))
#asdf = swea_cdf_file.attget("UNITS",4)
#print(asdf)
#swea_cdf_file.close()
#asdf_time = swea_cdf_file.varget(0)
#asdf_data = swea_cdf_file.varget(14)
#fge_data = swea_cdf_file.varget()
#print(fge_data)
#print(fge_time)
 
#asdf = np.array(asdf_time)
#asdf = asdf/1000000000.0
#asdf = asdf + 946100000
 
#pytplot.store_data('the_fge', data={'x':asdf, 'y':asdf_data[:,:,0]})
#pytplot.store_data('the_fge', data={'x':fge_time, 'y':fge_data})
#pytplot.tplot('the_fge')

#from pds2_cdf import cdfepoch

#x = cdfepoch.CDFepoch()

#print(x.findepochrange([60670644589000.0,61670644589000.0, 62670644589000.0,63670644589000.0,64670644589000.0,65670644589000.0,66670644589000.0,67670644589000.0,68670644589000.0,69670644589000.0], starttime=61770644589000.0, endtime=75670644589000.0))