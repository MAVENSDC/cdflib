import pds2_cdf
import pytplot
swea_cdf_file = pds2_cdf.CDF('C:/temp/tha_l1_fgm_20090101_v01.cdf')
asdf = swea_cdf_file.attget("UNITS",0)
#asdf2 = swea_cdf_file.globalattsget()
print(asdf)
swea_cdf_file.close()
#fge_data = swea_cdf_file.varget('tha_fge')
#pytplot.store_data('the_fge', data={'x':fge_time, 'y':fge_data})
#pytplot.tplot('the_fge')