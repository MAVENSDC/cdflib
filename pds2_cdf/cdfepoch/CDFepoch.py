"""
CDFepoch.py

    This is a python script to handle CDF epochs.

    There are three (3) epoch data types in CDF: CDF_EPOCH, CDF_EPOCH16 and 
    CDF_TIME_TT2000. CDF_EPOCH is milliseconds since Year 0. CDF_EPOCH16
    is picoseconds since Year 0. CDF_TIME_TT2000 (TT2000 as short) is 
    nanoseconds since J2000 with leap seconds. CDF_EPOCH is a single double
    (as float in Python), CDF_EPOCH16 is 2-doubles (as complex in Python),
    and TT2000 is 8-byte integer (as int in Python). In Numpy, they are 
    np.float64, np.complex128 and np.int64, respectively. All these epoch
    values can come from CDF.varget function.

    Four main functions are provided:

      encode (epochs, iso_8601=None) 
         Encodes the epoch(s) into UTC string(s).
         For CDF_EPOCH: The input should be either a float or list of floats
                        (in numpy, a np.float64 or a np.ndarray of np.float64)
                        Each epoch is encoded, by default to a ISO 8601 form:
                        2004-05-13T15:08:11.022 
                        Or, if iso_8601 is set to False,
                        13-May-2004 15:08:11.022
         For CDF_EPOCH16: The input should be either a complex or list of 
                          complex
                          (in numpy, a np.complex128 or a np.ndarray of 
                           np.complex128)
                          Each epoch is encoded, by default to a ISO 8601 form:
                          2004-05-13T15:08:11.022033044055
                          Or, if iso_8601 is set to False,
                          13-May-2004 15:08:11.022.033.044.055
         For TT2000: The input should be either an int or list of ints
                     (in numpy, a np.int64 or a np.ndarray of np.int64)
                     Each epoch is encoded, by default to a ISO 8601 form:
                     2008-02-02T06:08:10.012014016
                     Or, if iso_8601 is set to False,
                     02-Feb-2008 06:08:10.012.014.016

      breakdown (epochs, to_np=None)
         Breaks down the epoch(s) into UTC components. 
         For CDF_EPOCH: they are 7 date/time components: year, month, day,
                        hour, minute, second, and millisecond
         For CDF_EPOCH16: they are 10 date/time components: year, month, day,
                          hour, minute, second, and millisecond, microsecond,
                          nanosecond, and picosecond.
         For TT2000: they are 9 date/time components: year, month, day,
                     hour, minute, second, millisecond, microsecond, 
                     nanosecond.
         Specify to_np to True, if the result should be in numpy class.

      compute (datetimes, to_np=None)
      compute_epoch (datetimes, to_np=None)
      compute_epoch16 (datetimes, to_np=None)
      compute_tt2000 (datetimes, to_np=None)
         Computes the provided date/time components into CDF epoch value(s).
         For computing into CDF_EPOCH value, each date/time elements should
         have exactly seven (7) components, as year, month, day, hour, minute,
         second and millisecond, in a list. For example:
         [[2017,1,1,1,1,1,111],[2017,2,2,2,2,2,222]]
         Or, call function compute_epoch directly, instead, with at least three
         (3) (up to seven) components. The last component, if
         not the 7th, can be a float that can have a fraction of the unit.
         For CDF_EPOCH16, they should have exactly ten (10) components, as year,
         month, day, hour, minute, second, millisecond, microsecond, nanosecond
         and picosecond, in a list. For example:
         [[2017,1,1,1,1,1,123,456,789,999],[2017,2,2,2,2,2,987,654,321,999]]
         Or, call function compute_epoch directly, instead, with at least three
         (3) (up to ten) components. The last component, if
         not the 10th, can be a float that can have a fraction of the unit.
         Each TT2000 typed date/time should have exactly nine (9) components, as 
         year, month, day, hour, minute, second, millisecond, microsecond and
         nanosecond, in a list.  For example:
         [[2017,1,1,1,1,1,123,456,789],[2017,2,2,2,2,2,987,654,321]]
         Or, call function compute_tt2000 directly, instead, with at least three
         (3) (up to nine) components. The last component, if
         not the 9th, can be a float that can have a fraction of the unit.
         Specify to_np to True, if the result should be in numpy class.

      findepochrange (epochs, starttime=None, endtime=None)
         Finds the record range within the start and end time from values 
         of a CDF epoch data type. It returns a list of record numbers. 
         If the start time is not provided, then it is 
         assumed to be the minimum possible value. If the end time is not 
         provided, then the maximum possible value is assumed. The epoch is
         assumed to be in the chronological order. The start and end times
         should have the proper number of date/time components, corresponding
         to the epoch's data type.

@author: Michael Liu
"""

import numpy as np, sys, struct, itertools, math

class CDFepoch(object):

    _monthToken = [    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    JulianDateJ2000_12h =    2451545
    J2000Since0AD12h =       730485
    J2000Since0AD12hSec = 63113904000.0
    J2000Since0AD12hMilsec = 63113904000000.0
    J2000LeapSeconds =    32.0
    dT =                 32.184
    dTinNanoSecs =         32184000000
    MJDbase =             2400000.5
    SECinNanoSecs =         1000000000
    SECinNanoSecsD =      1000000000.0
    DAYinNanoSecs =         int(86400000000000)
    HOURinNanoSecs =        int(3600000000000)
    MINUTEinNanoSecs =      int(60000000000)
    T12hinNanoSecs =        int(43200000000000)
    # Julian days for 1707-09-22 and 2292-04-11, the valid TT2000 range
    JDY17070922 =           2344793
    JDY22920411 =           2558297
    DEFAULT_TT2000_PADVALUE  = int(-9223372036854775807)
    FILLED_TT2000_VALUE      = int(-9223372036854775808)
    NERA1 = 14

    #LASTLEAPSECONDDAY = 20170101

    LTS = [ [ 1960,  1,  1,  1.4178180, 37300.0, 0.0012960 ],
            [ 1961,  1,  1,  1.4228180, 37300.0, 0.0012960 ],
            [ 1961,  8,  1,  1.3728180, 37300.0, 0.0012960 ],
            [ 1962,  1,  1,  1.8458580, 37665.0, 0.0011232 ],
            [ 1963, 11,  1,  1.9458580, 37665.0, 0.0011232 ],
            [ 1964,  1,  1,  3.2401300, 38761.0, 0.0012960 ],
            [ 1964,  4,  1,  3.3401300, 38761.0, 0.0012960 ],
            [ 1964,  9,  1,  3.4401300, 38761.0, 0.0012960 ],
            [ 1965,  1,  1,  3.5401300, 38761.0, 0.0012960 ],
            [ 1965,  3,  1,  3.6401300, 38761.0, 0.0012960 ],
            [ 1965,  7,  1,  3.7401300, 38761.0, 0.0012960 ],
            [ 1965,  9,  1,  3.8401300, 38761.0, 0.0012960 ],
            [ 1966,  1,  1,  4.3131700, 39126.0, 0.0025920 ],
            [ 1968,  2,  1,  4.2131700, 39126.0, 0.0025920 ],
            [ 1972,  1,  1, 10.0,           0.0, 0.0       ],
            [ 1972,  7,  1, 11.0,           0.0, 0.0       ],
            [ 1973,  1,  1, 12.0,           0.0, 0.0       ],
            [ 1974,  1,  1, 13.0,           0.0, 0.0       ],
            [ 1975,  1,  1, 14.0,           0.0, 0.0       ],
            [ 1976,  1,  1, 15.0,           0.0, 0.0       ],
            [ 1977,  1,  1, 16.0,           0.0, 0.0       ],
            [ 1978,  1,  1, 17.0,           0.0, 0.0       ],
            [ 1979,  1,  1, 18.0,           0.0, 0.0       ],
            [ 1980,  1,  1, 19.0,           0.0, 0.0       ],
            [ 1981,  7,  1, 20.0,           0.0, 0.0       ],
            [ 1982,  7,  1, 21.0,           0.0, 0.0       ],
            [ 1983,  7,  1, 22.0,           0.0, 0.0       ],
            [ 1985,  7,  1, 23.0,           0.0, 0.0       ],
            [ 1988,  1,  1, 24.0,           0.0, 0.0       ],
            [ 1990,  1,  1, 25.0,           0.0, 0.0       ],
            [ 1991,  1,  1, 26.0,           0.0, 0.0       ],
            [ 1992,  7,  1, 27.0,           0.0, 0.0       ],
            [ 1993,  7,  1, 28.0,           0.0, 0.0       ],
            [ 1994,  7,  1, 29.0,           0.0, 0.0       ],
            [ 1996,  1,  1, 30.0,           0.0, 0.0       ],
            [ 1997,  7,  1, 31.0,           0.0, 0.0       ],
            [ 1999,  1,  1, 32.0,           0.0, 0.0       ],
            [ 2006,  1,  1, 33.0,           0.0, 0.0       ],
            [ 2009,  1,  1, 34.0,           0.0, 0.0       ],
            [ 2012,  7,  1, 35.0,           0.0, 0.0       ],
            [ 2015,  7,  1, 36.0,           0.0, 0.0       ],
            [ 2017,  1,  1, 37.0,           0.0, 0.0       ] ]
    NDAT = len(LTS)

    NST = None
    currentDay = -1
    currentJDay = -1
    currentLeapSeconds = -1

    def encode(self, epochs, iso_8601=None):

        if (isinstance(epochs, int) or isinstance(epochs, np.int64)):
            return CDFepoch.encode_tt2000(epochs, iso_8601)
        elif (isinstance(epochs, float) or isinstance(epochs, np.float64)):
            return CDFepoch.encode_epoch(epochs, iso_8601)
        elif (isinstance(epochs, complex) or isinstance(epochs, np.complex128)):
            return CDFepoch.encode_epoch16(epochs, iso_8601)
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
            if (isinstance(epochs[0], int) or isinstance(epochs[0], np.int64)):
                return CDFepoch.encode_tt2000(epochs, iso_8601)
            elif (isinstance(epochs[0], float) or 
                  isinstance(epochs[0], np.float64)):
                return CDFepoch.encode_epoch(epochs, iso_8601)
            elif (isinstance(epochs[0], complex) or 
                  isinstance(epochs[0], np.complex128)):
                return CDFepoch.encode_epoch16(epochs, iso_8601)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def breakdown(self, epochs, to_np=None):

        if (isinstance(epochs, int) or isinstance(epochs, np.int64)):
            return CDFepoch.breakdown_tt2000(epochs, to_np)
        elif (isinstance(epochs, float) or isinstance(epochs, np.float64)):
            return CDFepoch.breakdown_epoch(epochs, to_np)
        elif (isinstance(epochs, complex) or isinstance(epochs, np.complex128)):
            return CDFepoch.breakdown_epoch16(epochs, to_np)
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
            if (isinstance(epochs[0], int) or isinstance(epochs[0], np.int64)):
                return CDFepoch.breakdown_tt2000(epochs, to_np)
            elif (isinstance(epochs[0], float) or 
                 isinstance(epochs[0], np.float64)):
                return CDFepoch.breakdown_epoch(epochs, to_np)
            elif (isinstance(epochs[0], complex) or
                     isinstance(epochs[0], np.complex128)):
                return CDFepoch.breakdown_epoch16(epochs, to_np)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def compute(self, datetimes, to_np=None):

        if (not isinstance(datetimes, list) and
           not isinstance(datetimes, np.ndarray)):
            print('datetime must be in list form')
            return None
        if (isinstance(datetimes[0], int)):
            items = len(datetimes)
            if (items == 7):
                return CDFepoch.compute_epoch(datetimes, to_np)
            elif (items == 10):
                return CDFepoch.compute_epoch16(datetimes, to_np)
            elif (items == 9):
                return CDFepoch.compute_tt2000(datetimes, to_np)
            else:
                print('Unknown input')
                return None
        elif (isinstance(datetimes[0], list) or
              isinstance(datetimes[0], np.ndarray)):
            items = len(datetimes[0])
            if (items == 7):
                return CDFepoch.compute_epoch(datetimes, to_np)
            elif (items == 10):
                return CDFepoch.compute_epoch16(datetimes, to_np)
            elif (items == 9):
                return CDFepoch.compute_tt2000(datetimes, to_np)
            else:
                print('Unknown input')
                return None
        else:
            print('Unknown input')
            return None

    def findepochrange(self, epochs, starttime = None, endtime = None):

        if (isinstance(epochs, float) or isinstance(epochs, np.float64)):
            return CDFepoch.epochrange_epoch(epochs, starttime, endtime)
        elif (isinstance(epochs, int) or isinstance(epochs, np.int64)):
            return CDFepoch.epochrange_tt2000(epochs, starttime, endtime)
        elif (isinstance(epochs, complex) or isinstance(epochs, np.complex128)):
            return CDFepoch.epochrange_epoch16(epochs, starttime, endtime)
        elif (isinstance(epochs, list)  or isinstance(epochs, np.ndarray)):
            if (isinstance(epochs[0], float) or
               isinstance(epochs[0], np.float64)):
                return CDFepoch.epochrange_epoch(epochs, starttime, endtime)
            elif (isinstance(epochs[0], int) or
               isinstance(epochs[0], np.int64)):
                return CDFepoch.epochrange_tt2000(epochs, starttime, endtime)
            elif (isinstance(epochs[0], complex) or
               isinstance(epochs[0], np.complex128)):
                return CDFepoch.epochrange_epoch16(epochs, starttime, endtime)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def encode_tt2000(self, tt2000, iso_8601=None):
    
        if (isinstance(tt2000, int) or isinstance(tt2000, np.int64)):
            new_tt2000 = [tt2000]
        elif (isinstance(tt2000, list) or isinstance(tt2000, np.ndarray)):
            new_tt2000 = tt2000
        else:
            print('type...',type(tt2000))
            print('Bad input')
            return None
        count = len(new_tt2000)
        encodeds = []
        for x in range (0, count):
            nanoSecSinceJ2000 = new_tt2000[x]
            if nanoSecSinceJ2000 == CDFepoch.FILLED_TT2000_VALUE:
                if (iso_8601 == None or iso_8601 != False):
                    return '9999-12-31T23:59:59.999999999'
                else:
                    return '31-Dec-9999 23:59:59.999.999.999'
            if nanoSecSinceJ2000 == CDFepoch.DEFAULT_TT2000_PADVALUE:
                if (iso_8601 == None or iso_8601 != False):
                    return '0000-01-01T00:00:00.000000000'
                else:
                    return '01-Jan-0000 00:00:00.000.000.000'
            datetime = CDFepoch.breakdown_tt2000(nanoSecSinceJ2000)
            ly = datetime[0]
            lm = datetime[1]
            ld = datetime[2]
            lh = datetime[3]
            ln = datetime[4]
            ls = datetime[5]
            ll = datetime[6]
            lu = datetime[7]
            la = datetime[8]
            if (iso_8601 == None or iso_8601 != False):
                # yyyy-mm-ddThh:mm:ss.mmmuuunnn 
                encoded = str(ly).zfill(4)
                encoded += '-'
                encoded += str(lm).zfill(2)
                encoded += '-'
                encoded += str(ld).zfill(2)
                encoded += 'T'
                encoded += str(lh).zfill(2)
                encoded += ':'
                encoded += str(ln).zfill(2)
                encoded += ':'
                encoded += str(ls).zfill(2)
                encoded += '.'
                encoded += str(ll).zfill(3)
                encoded += str(lu).zfill(3)
                encoded += str(la).zfill(3)
            else:
                # dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn 
                encoded = str(ld).zfill(2)
                encoded += '-'
                encoded += CDFepoch._monthToken[lm-1]
                encoded += '-'
                encoded += str(ly).zfill(4)
                encoded += ' '
                encoded += str(lh).zfill(2)
                encoded += ':'
                encoded += str(ln).zfill(2)
                encoded += ':'
                encoded += str(ls).zfill(2)
                encoded += '.'
                encoded += str(ll).zfill(3)
                encoded += '.'
                encoded += str(lu).zfill(3)
                encoded += '.'
                encoded += str(la).zfill(3)
        
            if (count == 1):
                return encoded
            else:
                encodeds.append(encoded)
        return encodeds

    def breakdown_tt2000(self, tt2000, to_np=None):

        if (isinstance(tt2000, int) or isinstance(tt2000, np.int64)):
            new_tt2000 = [tt2000]
        elif (isinstance(tt2000, list) or isinstance(tt2000, np.ndarray)):
            new_tt2000 = tt2000
        else:
            print('Bad input data')
            return None
        count = len(new_tt2000)
        toutcs = []
        for x in range (0, count):
            nanoSecSinceJ2000 = new_tt2000[x]
            toPlus = 0.0
            t3 = nanoSecSinceJ2000
            datx = CDFepoch._LeapSecondsfromJ2000(nanoSecSinceJ2000)
            if (nanoSecSinceJ2000 > 0):
                secSinceJ2000 = int(nanoSecSinceJ2000/CDFepoch.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 * 
                                              CDFepoch.SECinNanoSecs)
                secSinceJ2000 = secSinceJ2000 - 32
                secSinceJ2000 = secSinceJ2000 + 43200
                nansec = nansec - 184000000
            else:
                nanoSecSinceJ2000 = nanoSecSinceJ2000 + CDFepoch.T12hinNanoSecs
                nanoSecSinceJ2000 = nanoSecSinceJ2000 - CDFepoch.dTinNanoSecs
                secSinceJ2000 = int(nanoSecSinceJ2000/CDFepoch.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 *
                                              CDFepoch.SECinNanoSecs)
            if (nansec < 0):
                nansec = CDFepoch.SECinNanoSecs + nansec
                secSinceJ2000 = secSinceJ2000 - 1
        
            t2 = secSinceJ2000 * CDFepoch.SECinNanoSecs + nansec
        
            if (datx[0] > 0.0):
                secSinceJ2000 = secSinceJ2000 - int(datx[0])
                epoch = CDFepoch.J2000Since0AD12hSec + secSinceJ2000
                if (datx[1] == 0.0):
                    date1 = self._EPOCHbreakdownTT2000 (epoch)
                else:
                    epoch = epoch - 1
                    date1 = self._EPOCHbreakdownTT2000 (epoch)
                    date1[5] = date1[5] + 1
                ye1 = date1[0]
                mo1 = date1[1]
                da1 = date1[2]
                ho1 = date1[3]
                mi1 = date1[4]
                se1 = date1[5]
            else:
                epoch = secSinceJ2000 + CDFepoch.J2000Since0AD12hSec
                xdate1 = self._EPOCHbreakdownTT2000 (epoch)
                tmpNanosecs = CDFepoch.compute_tt2000 (xdate1[0],
                                                       xdate1[1],
                                                       xdate1[2],
                                                       xdate1[3],
                                                       xdate1[4],
                                                       xdate1[5],
                                                       0, 0, nansec)
                if (tmpNanosecs != t3):
                    dat0 = self._LeapSecondsfromYMD(self, xdate1[0], xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int(float(tmpx/CDFepoch.SECinNanoSecsD))
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                if (nansec < 0):
                    nansec = CDFepoch.SECinNanoSecs + nansec
                    tmpy = tmpy - 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate1 = self._EPOCHbreakdownTT2000(epoch)
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate1[0], 
                                                          xdate1[1], 
                                                          xdate1[2], 
                                                          xdate1[3], 
                                                          xdate1[4], 
                                                          xdate1[5], 
                                                          0, 0, nansec)
                if (tmpNanosecs != t3):
                    dat0 = self._LeapSecondsfromYMD(xdate1[0], xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int((1.0*tmpx)/CDFepoch.SECinNanoSecsD)
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                    if (nansec < 0):
                        nansec = CDFepoch.SECinNanoSecs + nansec
                        tmpy = tmpy - 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate1 = self._EPOCHbreakdownTT2000 (epoch)
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate1[0],
                                                        xdate1[1],
                                                        xdate1[2],
                                                        xdate1[3],
                                                        xdate1[4],
                                                        xdate1[5],
                                                        0, 0, nansec);
                ye1 = int(xdate1[0])
                mo1 = int(xdate1[1])
                da1 = int(xdate1[2])
                ho1 = int(xdate1[3])
                mi1 = int(xdate1[4])
                se1 = int(xdate1[5])
            ml1 = int(nansec / 1000000)
            tmp1 = nansec - 1000000 * ml1
            if (ml1 > 1000):
                ml1 = ml1 - 1000
                se1 = se1 + 1
            ma1 = int(tmp1 / 1000)
            na1 = int(tmp1 - 1000 * ma1)
            datetime = []
            datetime.append(ye1)
            datetime.append(mo1)
            datetime.append(da1)
            datetime.append(ho1)
            datetime.append(mi1)
            datetime.append(se1)
            datetime.append(ml1)
            datetime.append(ma1)
            datetime.append(na1)
            if (count == 1):
                if (to_np == None):
                    return datetime
                else:
                    return np.array(datetime)
            else:
                toutcs.append(datetime)
        if (to_np == None):
            return toutcs
        else:
            return np.array(toutcs)
    
    def compute_tt2000(self, datetimes, to_np=None):
    
        if (not isinstance(datetimes, list)):
            print('datetime must be in list form')
            return None
        if (isinstance(datetimes[0], int)):
            new_datetimes= [datetimes]
            count = 1
        else:
            count = len(datetimes)
            new_datetimes= datetimes
        nanoSecSinceJ2000s = []
        for x in range (0, count):
            datetime = new_datetimes[x]
            year = int(datetime[0])
            month = int(datetime[1])
            items = len(datetime)
            if (items > 8):
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(datetime[8])
            elif (items == 8):
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(1000.0 * (datetime[7] - usec))
            elif (items == 7):
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                xxx = float(1000.0 * (datetime[6] - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items == 6):
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                xxx = float(1000.0 * (datetime[5] - second))
                msec = int(xxx)
                xxx = float(1000.0 * (xxx - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items == 5):
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                xxx = float(60.0 * (datetime[4] - minute))
                second = int(xxx)
                xxx = float(1000.0 * (xxx - second))
                msec = int(xxx)
                xxx = float(1000.0 * (xxx - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items == 4):
                day = int(datetime[2])
                hour = int(datetime[3])
                xxx = float(60.0 * (datetime[3] - hour))
                minute = int(xxx)
                xxx = float(60.0 * (xxx - minute))
                second = int(xxx)
                xxx = float(1000.0 * (xxx - second))
                msec = int(xxx)
                xxx = float(1000.0 * (xxx - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items == 3):
                day = int(datetime[2])
                xxx = float(24.0 * (datetime[2] - day))
                hour = int(xxx)
                xxx = float(60.0 * (xxx - hour))
                minute = int(xxx)
                xxx = float(60.0 * (xxx - minute))
                second = int(xxx)
                xxx = float(1000.0 * (xxx - second))
                msec = int(xxx)
                xxx = float(1000.0 * (xxx - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            else:
                print('Invalid tt2000 components')
                return None
            if (month == 0):
                month = 1
            if (year == 9999 and month == 12 and day == 31 and hour == 23 and
                minute == 59 and second == 59 and msec == 999 and
                usec == 999 and nsec == 999):
                nanoSecSinceJ2000 = CDFepoch.FILLED_TT2000_VALUE 
            elif (year == 0 and month == 1 and day == 1 and hour == 0 and
                  minute == 0 and second == 0 and msec == 0 and usec == 0 and
                  nsec == 0):
                nanoSecSinceJ2000 = CDFepoch.DEFAULT_TT2000_PADVALUE
            else:
                iy = 10000000 * month + 10000 * day + year
                if (iy != CDFepoch.currentDay):
                    CDFepoch.currentDay = iy
                    CDFepoch.currentLeapSeconds = CDFepoch._LeapSecondsfromYMD(year, month, day)
                    CDFepoch.currentJDay = CDFepoch._JulianDay(year,month,day)
                jd = CDFepoch.currentJDay
                jd = jd - CDFepoch.JulianDateJ2000_12h
                subDayinNanoSecs = int(hour*CDFepoch.HOURinNanoSecs+
                                       minute*CDFepoch.MINUTEinNanoSecs+
                                       second*CDFepoch.SECinNanoSecs+msec*1000000+
                                       usec*1000+nsec)
                nanoSecSinceJ2000 = int(jd * CDFepoch.DAYinNanoSecs + 
                                        subDayinNanoSecs)
                t2 = int(CDFepoch.currentLeapSeconds * CDFepoch.SECinNanoSecs)
                if (nanoSecSinceJ2000 < 0):
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + 
                                            CDFepoch.dTinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 - 
                                            CDFepoch.T12hinNanoSecs)
                else:
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 - 
                                            CDFepoch.T12hinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + 
                                            CDFepoch.dTinNanoSecs)
            if (count == 1):
                if (to_np == None):
                    return int(nanoSecSinceJ2000)
                else:
                    return np.array(int(nanoSecSinceJ2000))
            else:
                nanoSecSinceJ2000s.append(int(nanoSecSinceJ2000))  
        if (to_np == None):
            return nanoSecSinceJ2000s
        else:
            return np.array(nanoSecSinceJ2000s)

    def _LeapSecondsfromYMD(self, year, month, day):
    
        j = -1
        m = 12 * year + month
        for i, _ in reversed(list(enumerate(CDFepoch.LTS))):
            n = 12 * CDFepoch.LTS[i][0] + CDFepoch.LTS[i][1]
            if (m >= n):
                j = i
                break
        if (j == -1):
            return 0.0
        da = CDFepoch.LTS[j][3]
        if (j < CDFepoch.NERA1):
            jda = CDFepoch._JulianDay(year, month, day)
            da =  da + ((jda - self.MJDbase) - CDFepoch.LTS[j][4]) * CDFepoch.LTS[j][5]
        return da
    
    def _LeapSecondsfromJ2000(self, nanosecs):
    
      da = []
      da.append(0.0)
      da.append(0.0)
      j = -1;
      if (CDFepoch.NST == None):
         CDFepoch._LoadLeapNanoSecondsTable()
      for i, line in reversed(list(enumerate(CDFepoch.NST))):
        if (nanosecs >= CDFepoch.NST[i]):
          j = i;
          if (i < (CDFepoch.NDAT - 1)):
            if ((nanosecs + 1000000000) >= CDFepoch.NST[i+1]):
               da[1] = 1.0;
          break;
      if (j == -1):
         return da
      da[0] = CDFepoch.LTS[j][3];
      return da;
    
    def _LoadLeapNanoSecondsTable(self):
    
       CDFepoch.NST = []
       for ix in range(0, CDFepoch.NERA1):
           CDFepoch.NST.append(CDFepoch.FILLED_TT2000_VALUE)
       for ix in range(CDFepoch.NERA1, CDFepoch.NDAT):
           CDFepoch.NST.append(CDFepoch.compute_tt2000([int(CDFepoch.LTS[ix][0]), \
                                                        int(CDFepoch.LTS[ix][1]), \
                                                        int(CDFepoch.LTS[ix][2]), \
                                                        0, 0, 0, 0, 0, 0]))


    def _EPOCHbreakdownTT2000(self, epoch):
    
       second_AD = epoch;
       minute_AD = second_AD / 60.0;
       hour_AD = minute_AD / 60.0;
       day_AD = hour_AD / 24.0;

       jd = int(1721060 + day_AD);
       l=jd+68569
       n=int(4*l/146097)
       l=l-int((146097*n+3)/4)
       i=int(4000*(l+1)/1461001)
       l=l-int(1461*i/4)+31
       j=int(80*l/2447)
       k=l-int(2447*j/80)
       l=int(j/11)
       j=j+2-12*l
       i=100*(n-49)+i+l

       date = [];
       date.append(i)
       date.append(j)
       date.append(k)
       date.append(int(hour_AD % 24.0))
       date.append(int(minute_AD % 60.0))
       date.append(int(second_AD % 60.0))
       return date;

    def epochrange_tt2000(self, epochs, starttime = None, endtime = None):

        if (isinstance(epochs, int) or isinstance(epochs, np.int64)):
           new2_epochs = [epochs]
        elif (isinstance(epochs, list)  or isinstance(epochs, np.ndarray)):
           if (isinstance(epochs[0], int) or \
               isinstance(epochs[0], np.int64)):
              new2_epochs = epochs
           else:
              print('Bad data')
              return None
        else:
           print('Bad data')
           return None
        if (starttime == None):
           stime = int(-9223372036854775807)
        else:
           if (isinstance(starttime, int) or isinstance(starttime, np.int64)):
              stime = starttime
           elif (isinstance(starttime, list)):
              stime = CDFepoch.compute_tt2000(starttime)
           else:
              print('Bad start time')
              return None
        if (endtime != None):
           if (isinstance(endtime, int) or isinstance(endtime, np.int64)):
              etime = endtime
           elif (isinstance(endtime, list)):
              etime = CDFepoch.compute_tt2000(endtime)
           else:
              print('Bad end time')
              return None
        else:
           etime = int(9223372036854775807)
        if (stime > etime):
           print('Invalid start/end time')
           return None
        if (isinstance(epochs, list)):
           new_epochs = np.array(epochs)
        else:
           new_epochs = epochs
        return np.where(np.logical_and(new_epochs>=stime, new_epochs<=etime))


    def encode_epoch16(self, epochs, iso_8601=None):

        if (isinstance(epochs, complex) or \
            isinstance(epochs, np.complex128)):
           new_epochs = [epochs]
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
           new_epochs = epochs
        else:
           print('Bad data')
           return None
        count = len(new_epochs)
        encodeds = []
        for x in range(0, count):
           #complex
           if ((new_epochs[x].real == -1.0E31) and (new_epochs[x].imag == -1.0E31)):
              if (iso_8601 == None or iso_8601 != False):
                 encode = '9999-12-31T23:59:59.999999999999'
              else:
                 encoded = '31-Dec-9999 23:59:59.999.999.999.999'
           else:
              encoded = CDFepoch._encodex_epoch16 (new_epochs[x], iso_8601)
           if (count == 1):
              return encoded
           else:
              encodeds.append(encoded)
        return encodeds
	
    def _encodex_epoch16(self, epoch16, iso_8601=None): 

        components = CDFepoch.breakdown_epoch16(epoch16)
        if (iso_8601 == None or iso_8601 != False):
           # year-mm-ddThh:mm:ss.mmmuuunnnppp 
           encoded = str(components[0]).zfill(4) 
           encoded += '-'
           encoded += str(components[1]).zfill(2)
           encoded += '-'
           encoded += str(components[2]).zfill(2)
           encoded += 'T'
           encoded += str(components[3]).zfill(2)
           encoded += ':'
           encoded += str(components[4]).zfill(2)
           encoded += ':'
           encoded += str(components[5]).zfill(2)
           encoded += '.'
           encoded += str(components[6]).zfill(3)
           encoded += str(components[7]).zfill(3)
           encoded += str(components[8]).zfill(3)
           encoded += str(components[9]).zfill(3)
        else:
           # dd-mmm-year hh:mm:ss.mmm.uuu.nnn.ppp 
           encoded = str(components[2]).zfill(2)
           encoded += '-'
           encoded += CDFepoch._monthToken[components[1]-1]
           encoded += '-'
           encoded += str(components[0]).zfill(4)
           encoded += ' '
           encoded += str(components[3]).zfill(2)
           encoded += ':'
           encoded += str(components[4]).zfill(2)
           encoded += ':'
           encoded += str(components[5]).zfill(2)
           encoded += '.'
           encoded += str(components[6]).zfill(3)
           encoded += '.'
           encoded += str(components[7]).zfill(3)
           encoded += '.'
           encoded += str(components[8]).zfill(3)
           encoded += '.'
           encoded += str(components[9]).zfill(3)
        return encoded

    def _JulianDay(self, y, m, d):

        a1 = int(7*(int(y+int((m+9)/12)))/4)
        a2 = int(3*(int(int(y+int((m-9)/7))/100)+1)/4)
        a3 = int(275*m/9)
        return (367*y - a1 - a2 + a3 + d + 1721029)

    def compute_epoch16(self, datetimes, to_np=None):

        if (not isinstance(datetimes, list)):
           print('Bad input')
           return None
        if (not isinstance(datetimes[0], list)):
           new_dates = []
           new_dates = [datetimes]
        else:
           new_dates = datetimes
        count = len(new_dates)
        if (count == 0):
           return None
        epochs = []
        for x in range(0, count):
           epoch = []
           date = new_dates[x]
           items = len(date)
           year = date[0]
           month = date[1]
           if (items > 9):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(date[6])
              usec = int(date[7])
              nsec = int(date[8])
              psec = int(date[9])
           elif (items == 9):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(date[6])
              usec = int(date[7])
              nsec = int(date[8])
              psec = int(1000.0 * (date[8] - nsec))
           elif (items == 8):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(date[6])
              usec = int(date[7])
              xxx = int(1000.0 * (date[7] - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           elif (items == 7):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(date[6])
              xxx = float(1000.0 * (date[6] - msec))
              usec = int(xxx)
              xxx = int(1000.0 * (xxx - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           elif (items == 6):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              xxx = float(1000.0 * (date[5] - second))
              msec = int(xxx)
              xxx = float(1000.0 * (xxx - msec))
              usec = int(xxx)
              xxx = int(1000.0 * (xxx - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           elif (items == 5):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              xxx = float(60.0 * (date[4] - minute))
              second = int(xxx)
              xxx = float(1000.0 * (xxx - second))
              msec = int(xxx)
              xxx = float(1000.0 * (xxx - msec))
              usec = int(xxx)
              xxx = int(1000.0 * (xxx - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           elif (items == 4):
              day = int(date[2])
              hour = int(date[3])
              xxx = float(60.0 * (date[3] - hour))
              minute = int(xxx)
              xxx = float(60.0 * (xxx - minute))
              second = int(xxx)
              xxx = float(1000.0 * (xxx - second))
              msec = int(xxx)
              xxx = float(1000.0 * (xxx - msec))
              usec = int(xxx)
              xxx = int(1000.0 * (xxx - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           elif (items == 3):
              day = int(date[2])
              xxx = float(24.0 * (date[2] - day))
              hour = int(xxx)
              xxx = float(60.0 * (xxx - hour))
              minute = int(xxx)
              xxx = float(60.0 * (xxx - minute))
              second = int(xxx)
              xxx = float(1000.0 * (xxx - second))
              msec = int(xxx)
              xxx = float(1000.0 * (xxx - msec))
              usec = int(xxx)
              xxx = int(1000.0 * (xxx - usec))
              nsec = int(xxx)
              psec = int(1000.0 * (xxx - nsec))
           else:
              print('Invalid epoch16 components')
              return None
           if (year < 0):
              print('Illegal epoch field')
              return
           if (year == 9999 and month == 12 and day == 31 and hour == 23 and \
               minute == 59 and second == 59 and msec == 999 and \
               usec == 999 and nsec == 999 and psec == 999):
               epoch.append(-1.0E31)
               epoch.append(-1.0E31)
           elif ((year > 9999) or (month < 0 or month > 12) or \
                 (hour < 0 or hour > 23) or (minute < 0 or minute > 59) or \
                 (second < 0 or second > 59) or (msec < 0 or msec > 999) or \
                 (usec < 0 or usec > 999) or (nsec < 0 or nsec > 999) or \
                 (psec < 0 or psec > 999)):
                epoch = CDFepoch._computeEpoch16(year, month, day, hour, \
                                                 minute, second, msec, \
                                                 usec, nsec, psec)
           else:
              if (month == 0):
                 if (day < 1 or day > 366):
                    epooch = CDFepoch._computeEpoch16(year,month,day,hour,\
                                                      minute,second,msec,\
                                                      usec,nsec,psec)
              else:
                 if (day < 1 or day > 31):
                    epooch = CDFepoch._computeEpoch16(year,month,day,hour,\
                                                      minute,second,msec,\
                                                      usec,nsec,psec)
              if (month == 0):
                 daysSince0AD = CDFepoch._JulianDay(year,1,1) + (day-1) - \
                                1721060
              else:
                 daysSince0AD = CDFepoch._JulianDay(year,month,day) - 1721060
              secInDay = (3600 * hour) + (60 * minute) + second 
              epoch16_0 = float(86400.0 * daysSince0AD) + float(secInDay)
              epoch16_1 = float(psec) + float(1000.0 * nsec) + \
                          float(1000000.0 * usec) + float(1000000000.0 * msec)
              epoch.append(epoch16_0)
              epoch.append(epoch16_1)
           cepoch = complex(epoch[0], epoch[1])
           if (count == 1):
              if (to_np == None):
                 return cepoch
              else:
                 return np.array(cepoch)
           else:
              epochs.append(cepoch)
        if (to_np == None):
           return epochs
        else:
           return np.array(epochs)

    def breakdown_epoch16(self, epochs, to_np=None):

        if (isinstance(epochs, complex) or \
            isinstance(epochs, np.complex128)):
           new_epochs = [epochs]
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
           new_epochs = epochs
        else:
           print('Bad data')
           return
        count = len(new_epochs)
        components = []
        for x in range(0, count):
           component = []
           epoch16 = []
           #complex
           epoch16.append(new_epochs[x].real)
           epoch16.append(new_epochs[x].imag)
           if ((epoch16[0] == -1.0E31) and (epoch16[1] == -1.0E31)):
              component.append(9999)
              component.append(12)
              component.append(31)
              component.append(23)
              component.append(59)
              component.append(59)
              component.append(999)
              component.append(999)
              component.append(999)
              component.append(999)
           else:
              if (epoch16[0] < 0.0):
                 epoch16[0] = -epoch16[0]
              if (epoch16[1] < 0.0):
                 epoch16[1] = -epoch16[1]
              second_AD = epoch16[0]
              minute_AD = second_AD / 60.0
              hour_AD = minute_AD / 60.0
              day_AD = hour_AD / 24.0
              jd = int(1721060 + day_AD)
              l=jd+68569
              n=int(4*l/146097)
              l=l-int((146097*n+3)/4)
              i=int(4000*(l+1)/1461001)
              l=l-int(1461*i/4)+31
              j=int(80*l/2447)
              k=l-int(2447*j/80)
              l=int(j/11)
              j=j+2-12*l
              i=100*(n-49)+i+l
              component.append(i)
              component.append(j)
              component.append(k)
              component.append(int(hour_AD % 24.0))
              component.append(int(minute_AD % 60.0))
              component.append(int(second_AD % 60.0))
              msec = epoch16[1]
              component_9 = int(msec % 1000.0)
              msec = msec / 1000.0
              component_8 = int(msec % 1000.0)
              msec = msec / 1000.0
              component_7 = int(msec % 1000.0)
              msec = msec / 1000.0
              component.append(int(msec))
              component.append(component_7)
              component.append(component_8)
              component.append(component_9)
           if (count == 1):
              if (to_np == None):
                return component
              else:
                return np.array(component)
           else:
              components.append(component)
        if (to_np == None):
           return components
        else:
           return np.array(components)
    
    def _computeEpoch16(self, y, m, d, h, mn, s, ms, msu, msn, msp):
    
        if (m == 0):
           daysSince0AD = CDFepoch._JulianDay(y,1,1) + (d-1) - 1721060
        else:
           if (m < 0):
              y = y - 1
              m = 13 + m
           daysSince0AD = CDFepoch._JulianDay(y,m,d) - 1721060
        if (daysSince0AD < 0):
           print('Illegal epoch')
           return None
        epoch = []
        epoch.append(float(86400.0 * daysSince0AD + 3600.0 * h + 60.0 * mn) + float(s))
        epoch.append(float(msp) + float(1000.0 * msn) + \
                     float(1000000.0 * msu) + math.pow(10.0, 9) * ms)
        if (epoch[1] < 0.0 or epoch[1] >= math.pow(10.0, 12)):
           if (epoch[1] < 0.0):
              sec = int(epoch[1] / math.pow(10.0, 12))
              tmp = epoch[1] - sec * math.pow(10.0, 12)
              if (tmp != 0.0 and tmp != -0.0):
                 epoch[0] = epoch[0] + sec - 1
                 epoch[1] = math.pow(10.0, 12.0) + tmp
              else:
                 epoch[0] = epoch[0] + sec
                 epoch[1] = 0.0
           else:
              sec = int(epoch[1] / math.pow(10.0, 12))
              tmp = epoch[1] - sec * math.pow(10.0, 12)
              if (tmp != 0.0 and tmp != -0.0):
                 epoch[1] = tmp
                 epoch[0] = epoch[0] + sec
              else:
                 epoch[1] = 0.0
                 epoch[0] = epoch[0] + sec
        if (epoch[0] < 0.0):
           print('Illegal epoch')
           return None
        else:
          return epoch

    def epochrange_epoch16(self, epochs, starttime = None, endtime = None):

        if (isinstance(epochs, complex) or isinstance(epochs, np.complex128)):
           new_epochs = [epochs]
        elif (isinstance(epochs, list)  or isinstance(epochs, np.ndarray)):
           if (isinstance(epochs[0], complex) or \
               isinstance(epochs[0], np.complex128)):
              new_epochs = epochs
           else:
              print('Bad data')
              return None
        else:
           print('Bad data')
           return None
        if (starttime == None):
           stime = []
           stime.append(-1.0E31)
           stime.append(-1.0E31)
        else:
           if (isinstance(starttime, complex) or \
               isinstance(starttime, np.complex128)):
              stime = []
              stime.append(starttime.real)
              stime.append(starttime.imag)
           elif (isinstance(starttime, list)):
              sstime = CDFepoch.compute_epoch16(starttime)
              stime = []
              stime.append(sstime.real)
              stime.append(sstime.imag)
           else:
              print('Bad start time')
              return None
        if (endtime != None):
           if (isinstance(endtime, complex) or \
               isinstance(endtime, np.complex128)):
              etime = []
              etime.append(endtime.real)
              etime.append(endtime.imag)
           elif (isinstance(endtime, list)):
              eetime = CDFepoch.compute_epoch16(endtime)
              etime = []
              etime.append(eetime.real)
              etime.append(eetime.imag)
           else:
              print('Bad start time')
              return None
        else:
           etime = []
           etime.append(1.0E31)
           etime.append(1.0E31)
        if (stime[0] > etime[0] or (stime[0] == etime[0] and stime[1] > etime[1])):
           print('Invalid start/end time')
           return None
        count = len(new_epochs)
        epoch16 = []
        for x in range(0, count):
           epoch16.append(new_epochs[x].real)
           epoch16.append(new_epochs[x].imag)
        count = count * 2
        indx = []
        if (epoch16[0] > etime[0] or (epoch16[0] == etime[0] and \
                                      epoch16[1] > etime[1])):
           return None
        if (epoch16[count-2] < stime[0] or \
            (epoch16[count-2] == stime[0] and \
             epoch16[count-1] < stime[1])):
           return None
        for x in range(0, count, 2):
           if (epoch16[x] < stime[0]):
              continue
           elif (epoch16[x] == stime[0]):
                if (epoch16[x+1] < stime[1]):
                   continue
                else:
                   indx.append(int(x/2))
                   break
           else:
              indx.append(int(x/2))
              break
        if (len(indx) == 0):
           indx.append(0)
        hasadded = 0
        for x in range(0, count, 2):
           if (epoch16[x] < etime[0]):
              continue
           elif (epoch16[x] == etime[0]):
                if (epoch16[x+1] > etime[1]):
                   indx.append(int(x/2))
                   hasadded = 1
                   break
           else:
              indx.append(int((x-1)/2))
              hasadded = 1
              break
        if (hasadded == 0):
           indx.append(int(count/2)-1)
        return indx

    def encode_epoch(self, epochs, iso_8601=None):

        if (isinstance(epochs, float) or isinstance(epochs, np.float64)):
           new_epochs = [epochs]
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
           new_epochs = epochs
        else:
           print('Bad data')
           return None
        count = len(new_epochs)
        encodeds = []
        for x in range(0, count):
           epoch = new_epochs[x]
           if (epoch == -1.0E31):
              if (iso_8601 == None or iso_8601 != False):
                 encoded = '9999-12-31T23:59:59.999'
              else:
                 encoded = '31-Dec-9999 23:59:59.999'
           else:
              encoded = CDFepoch._encodex_epoch (epoch, iso_8601)
           if (count == 1):
              return encoded
           encodeds.append(encoded)
        return encodeds

    def _encodex_epoch(self, epoch, iso_8601=None):

        components = CDFepoch.breakdown_epoch(epoch)
        if (iso_8601 == None or iso_8601 != False):
           # year-mm-ddThh:mm:ss.mmm
           encoded = str(components[0]).zfill(4)
           encoded += '-'
           encoded += str(components[1]).zfill(2)
           encoded += '-'
           encoded += str(components[2]).zfill(2)
           encoded += 'T'
           encoded += str(components[3]).zfill(2)
           encoded += ':'
           encoded += str(components[4]).zfill(2)
           encoded += ':'
           encoded += str(components[5]).zfill(2)
           encoded += '.'
           encoded += str(components[6]).zfill(3)
        else:
           # dd-mmm-year hh:mm:ss.mmm
           encoded = str(components[2]).zfill(2)
           encoded += '-'
           encoded += CDFepoch._monthToken[components[1]-1]
           encoded += '-'
           encoded += str(components[0]).zfill(4)
           encoded += ' '
           encoded += str(components[3]).zfill(2)
           encoded += ':'
           encoded += str(components[4]).zfill(2)
           encoded += ':'
           encoded += str(components[5]).zfill(2)
           encoded += '.'
           encoded += str(components[6]).zfill(3)
        return encoded

    def compute_epoch(self, dates, to_np=None):

        if (not isinstance(dates, list)):
           print('Bad input')
           return None
        if (not isinstance(dates[0], list)):
           new_dates = []
           new_dates = [dates]
        else:
           new_dates = dates
        count = len(new_dates)
        if (count == 0):
           return None
        epochs = []
        for x in range(0, count):
           date = new_dates[x]
           year = date[0]
           month = date[1]
           items = len(date)
           if (items > 6):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(date[6])
           elif (items == 6):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              second = int(date[5])
              msec = int(1000.0 * (date[5] - second))
           elif (items == 5):
              day = int(date[2])
              hour = int(date[3])
              minute = int(date[4])
              xxx = float(60.0 * (date[4] - minute))
              second = int(xxx)
              msec = int(1000.0 * (xxx - second))
           elif (items == 4):
              day = int(date[2])
              hour = int(date[3])
              xxx = float(60.0 * (date[3] - hour))
              minute = int(xxx)
              xxx = float(60.0 * (xxx - minute))
              second = int(xxx)
              msec = int(1000.0 * (xxx - second))
           elif (items == 3):
              day = int(date[2])
              xxx = float(24.0 * (date[2] - day))
              hour = int(xxx)
              xxx = float(60.0 * (xxx - hour))
              minute = int(xxx)
              xxx = float(60.0 * (xxx - minute))
              second = int(xxx)
              msec = int(1000.0 * (xxx - second))
           else:
              print('Invalid epoch components')
              return None
           if (year == 9999 and month == 12 and day == 31 and hour == 23 and \
               minute == 59 and second == 59 and msec == 999):
              epochs.append(-1.0E31)
           if (year < 0):
              print('ILLEGAL_EPOCH_FIELD')
              return None
           if ((year > 9999) or (month < 0 or month > 12) or
               (hour < 0 or hour > 23) or (minute < 0 or minute > 59) or
               (second < 0 or second > 59) or (msec < 0 or msec > 999)):
              epochs.append(CDFepoch._computeEpoch(year,month,day,hour,minute,\
                                                   second,msec))
           if (month == 0):
              if (day < 1 or day > 366):
                 epochs.append(CDFepoch._computeEpoch(year,month,day,hour,\
                                                      minute,second,msec))
           else:
              if (day < 1 or day > 31):
                 epochs.append(CDFepoch._computeEpoch(year,month,day,hour,\
                                                      minute,second,msec))
           if (hour == 0 and minute == 0 and second == 0):
              if (msec < 0 or msec > 86399999):
                 epochs.append(CDFepoch._computeEpoch(year,month,day,hour,\
                                                      minute,second,msec))

           if (month == 0):
              daysSince0AD = CDFepoch._JulianDay(year,1,1) + (day-1) - 1721060
           else:
              daysSince0AD = CDFepoch._JulianDay(year,month,day) - 1721060
           if (hour == 0 and minute == 0 and second == 0):
              msecInDay = msec
           else:
              msecInDay = (3600000 * hour) + (60000 * minute) + \
                          (1000 * second) + msec
           if (count == 1):
              if (to_np == None):
                 return (86400000.0*daysSince0AD+msecInDay)
              else:
                 return np.array((86400000.0*daysSince0AD+msecInDay))
           epochs.append(86400000.0*daysSince0AD+msecInDay)
        if (to_np == None):
           return epochs
        else:
           return np.array(epochs)

    def _computeEpoch(self, y, m, d, h, mn, s, ms):

        if (m == 0):
           daysSince0AD = CDFepoch._JulianDay(y,1,1) + (d-1) - 1721060
        else:
           if (m < 0):
              --y
              m = 13 + m
           daysSince0AD = CDFepoch._JulianDay(y,m,d) - 1721060
        if (daysSince0AD < 1):
           print('ILLEGAL_EPOCH_FIELD')
           return None
        msecInDay = float(3600000.0 * h + 60000.0 * mn + 1000.0 * s) + float(ms)
        msecFromEpoch =  float(86400000.0 * daysSince0AD + msecInDay)
        if (msecFromEpoch < 0.0):
          return -1.0
        else:
          return msecFromEpoch

    def breakdown_epoch(self, epochs, to_np=None):

        if (isinstance(epochs, float) or isinstance(epochs, np.float64)):
           new_epochs = [epochs]
        elif (isinstance(epochs, list) or isinstance(epochs, np.ndarray)):
           new_epochs = epochs
        else:
           print('Bad data')
           return None
        count = len(new_epochs)
        components = []
        for x in range (0, count):
           component = []
           epoch = new_epochs[x]
           if (epoch == -1.0E31):
              component.append(9999)
              component.append(12)
              component.append(31)
              component.append(23)
              component.append(59)
              component.append(59)
              component.append(999)
           else:
              if (epoch < 0.0):
                 epoch = -epochs
              if (isinstance(epochs, int)):
                 epoch = float(epoch)
              msec_AD = epoch
              second_AD = msec_AD / 1000.0
              minute_AD = second_AD / 60.0
              hour_AD = minute_AD / 60.0
              day_AD = hour_AD / 24.0
              jd = int(1721060 + day_AD)
              l=jd+68569
              n=int(4*l/146097)
              l=l-int((146097*n+3)/4)
              i=int(4000*(l+1)/1461001)
              l=l-int(1461*i/4)+31
              j=int(80*l/2447)
              k=l-int(2447*j/80)
              l=int(j/11)
              j=j+2-12*l
              i=100*(n-49)+i+l
              component.append(i)
              component.append(j)
              component.append(k)
              component.append(int(hour_AD % 24.0))
              component.append(int(minute_AD % 60.0))
              component.append(int(second_AD % 60.0))
              component.append(int(msec_AD % 1000.0))
           if (count == 1):
              if (to_np == None):
                 return component
              else:
                 return np.array(component)
           else:
              components.append(component)
        if (to_np == None):
           return components
        else:
           return np.array(components)

    def epochrange_epoch(self, epochs, starttime = None, endtime = None):

        if (isinstance(epochs, float) or isinstance(epochs, np.float64)):
           new2_epochs = [epochs]
        elif (isinstance(epochs, list)  or isinstance(epochs, np.ndarray)):
           if (isinstance(epochs[0], float) or \
               isinstance(epochs[0], np.float64)):
              new2_epochs = epochs
           else:
              print('Bad data')
              return None
        else:
           print('Bad data')
           return None
        if (starttime == None):
           stime = 0.0
        else:
          if (isinstance(starttime, float) or isinstance(starttime, int) or \
              isinstance(starttime, np.float64)):
             stime = starttime
          elif (isinstance(starttime, list)):
             stime = CDFepoch.compute_epoch(starttime)
          else:
             print('Bad start time')
             return None
        if (endtime != None):
           if (isinstance(endtime, float) or isinstance(endtime, int) or \
               isinstance(endtime, np.float64)):
              etime = endtime
           elif (isinstance(endtime, list)):
              etime = CDFepoch.compute_epoch(endtime)
           else:
              print('Bad end time')
              return None
        else:
           etime = 1.0E31
        if (stime > etime):
           print('Invalid start/end time')
           return None
        if (isinstance(epochs, list)):
           new_epochs = np.array(epochs)
        else:
           new_epochs = epochs
        return np.where(np.logical_and(new_epochs>=stime, new_epochs<=etime))

