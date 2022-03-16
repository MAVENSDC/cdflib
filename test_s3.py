""" Simple test of file, url and s3 versions of the same file """
#import sys
#sys.path.insert(0,'.')
import cdflib

fname1 = 'tests/testfiles/mms1.cdf'
fname2 = 'http://ghostlibrary.com/mms1.cdf'
fname3 = "s3://skantunes/mms1.cdf"

cdfin = cdflib.CDF(fname1)
print('obj: ',cdfin)
print('header: ',cdfin.cdf_info())
x=cdfin.varget('mms1_fgm_bdeltahalf_brst_l2')
print('data 1: ',x)
x=cdfin.varget('mms1_fgm_stemp_brst_l2')
print('data 2: ',x)


cdfin2 = cdflib.CDF(fname2)
print('obj: ',cdfin2)
print('header: ',cdfin2.cdf_info())
x=cdfin2.varget('mms1_fgm_bdeltahalf_brst_l2')
print('data 1: ',x)
x=cdfin2.varget('mms1_fgm_stemp_brst_l2')
print('data 2: ',x)

cdfin3 = cdflib.CDF(fname3)
print('obj: ',cdfin3)
print('header: ',cdfin3.cdf_info())
x=cdfin3.varget('mms1_fgm_bdeltahalf_brst_l2')
print('data 1: ',x)
x=cdfin3.varget('mms1_fgm_stemp_brst_l2')
print('data 2: ',x)
