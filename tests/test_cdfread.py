import os
import cdflib


def test_read():
    fname = 'messenger.cdf'
    if not os.path.exists(fname):
        import urllib.request
        urllib.request.urlretrieve(
            'ftp://spdf.gsfc.nasa.gov/pub/data/messenger/rtn/2010/messenger_mag_rtn_20100105_v01.cdf',
            fname)
    cdf = cdflib.CDF(fname)
