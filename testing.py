import pds2_cdf
import pytplot
swea_cdf_file = pds2_cdf.CDF('C:/temp/tha_l1_fgm_20090101_v01.cdf')
#asdf = swea_cdf_file.attget("UNITS",4)
#print(asdf)
#swea_cdf_file.close()
#swea_cdf_file.varinq()
fge_data = swea_cdf_file.varget('tha_fge')
#fge_time = swea_cdf_file.varinq('tha_fge_time')
#print(fge_data)
#print(fge_time)
#pytplot.store_data('the_fge', data={'x':fge_time, 'y':fge_data})
#pytplot.tplot('the_fge')