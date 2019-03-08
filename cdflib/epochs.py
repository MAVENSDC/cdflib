"""
##########
CDF Epochs
##########

Importing cdflib also imports the module CDFepoch, which handles CDF-based epochs.
The following functions can be used to convert back and forth between different ways to display the date.
You can call these functions like so::
    import cdflib
    cdf_file = cdflib.cdfepoch.compute_epoch([2017,1,1,1,1,1,111])

There are three (3) epoch data types in CDF: CDF_EPOCH, CDF_EPOCH16 and
CDF_TIME_TT2000.

- CDF_EPOCH is milliseconds since Year 0.
- CDF_EPOCH16 is picoseconds since Year 0.
- CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with
  leap seconds.

CDF_EPOCH is a single double(as float in Python),
CDF_EPOCH16 is 2-doubles (as complex in Python),
and TT2000 is 8-byte integer (as int in Python).
In Numpy, they are np.float64, np.complex128 and np.int64, respectively.
All these epoch values can come from from CDF.varget function.

@author: Michael Liu
"""

import numpy as np
import math
import re
import numbers
import os
import datetime

from astropy.time import Time


class CDFepoch:

    version = 3
    release = 7
    increment = 0

    month_Token = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    JulianDateJ2000_12h = 2451545
    J2000Since0AD12h = 730485
    J2000Since0AD12hSec = 63113904000.0
    J2000Since0AD12hMilsec = 63113904000000.0
    J2000LeapSeconds = 32.0
    dT = 32.184
    dTinNanoSecs = 32184000000
    MJDbase = 2400000.5
    SECinNanoSecs = 1000000000
    SECinNanoSecsD = 1000000000.0
    DAYinNanoSecs = int(86400000000000)
    HOURinNanoSecs = int(3600000000000)
    MINUTEinNanoSecs = int(60000000000)
    T12hinNanoSecs = int(43200000000000)
    # Julian days for 1707-09-22 and 2292-04-11, the valid TT2000 range
    JDY17070922 = 2344793
    JDY22920411 = 2558297
    DEFAULT_TT2000_PADVALUE = int(-9223372036854775807)
    FILLED_TT2000_VALUE = int(-9223372036854775808)
    NERA1 = 14

    # LASTLEAPSECONDDAY = 20170101

    # Attempt to download latest leap second table
    try:
        import urllib.request
        leapsecond_files_url = "https://cdf.gsfc.nasa.gov/html/CDFLeapSeconds.txt"
        page = urllib.request.urlopen(leapsecond_files_url)
        full_path = os.path.realpath(__file__)
        library_path = os.path.dirname(full_path)
        with open(os.path.join(library_path, 'CDFLeapSeconds.txt'), "wb") as lsfile:
            lsfile.write(page.read())
    except:
        print("Can't download new leap second table")
        pass

    # Attempt to load the leap second table saved in the cdflib
    try:
        import csv
        full_path = os.path.realpath(__file__)
        library_path = os.path.dirname(full_path)
        leap_seconds_file = os.path.join(library_path, 'CDFLeapSeconds.txt')
        LTS = []
        with open(leap_seconds_file) as lsfile:
            lsreader = csv.reader(lsfile, delimiter=' ')
            for row in lsreader:
                if row[0] == ";":
                    continue
                row = list(filter(''.__ne__, row))
                row[0] = int(row[0])
                row[1] = int(row[1])
                row[2] = int(row[2])
                row[3] = float(row[3])
                row[4] = float(row[4])
                row[5] = float(row[5])
                LTS.append(row)
    except:
        print("Can't find leap second table.  Using one built into code.")
        print("Last leap second in built in table is on Jan 01 2017. ")
        # Use a built in leap second table
        LTS = [[1960,  1,  1,  1.4178180, 37300.0, 0.0012960],
               [1961,  1,  1,  1.4228180, 37300.0, 0.0012960],
               [1961,  8,  1,  1.3728180, 37300.0, 0.0012960],
               [1962,  1,  1,  1.8458580, 37665.0, 0.0011232],
               [1963, 11,  1,  1.9458580, 37665.0, 0.0011232],
               [1964,  1,  1,  3.2401300, 38761.0, 0.0012960],
               [1964,  4,  1,  3.3401300, 38761.0, 0.0012960],
               [1964,  9,  1,  3.4401300, 38761.0, 0.0012960],
               [1965,  1,  1,  3.5401300, 38761.0, 0.0012960],
               [1965,  3,  1,  3.6401300, 38761.0, 0.0012960],
               [1965,  7,  1,  3.7401300, 38761.0, 0.0012960],
               [1965,  9,  1,  3.8401300, 38761.0, 0.0012960],
               [1966,  1,  1,  4.3131700, 39126.0, 0.0025920],
               [1968,  2,  1,  4.2131700, 39126.0, 0.0025920],
               [1972,  1,  1, 10.0,           0.0, 0.0],
               [1972,  7,  1, 11.0,           0.0, 0.0],
               [1973,  1,  1, 12.0,           0.0, 0.0],
               [1974,  1,  1, 13.0,           0.0, 0.0],
               [1975,  1,  1, 14.0,           0.0, 0.0],
               [1976,  1,  1, 15.0,           0.0, 0.0],
               [1977,  1,  1, 16.0,           0.0, 0.0],
               [1978,  1,  1, 17.0,           0.0, 0.0],
               [1979,  1,  1, 18.0,           0.0, 0.0],
               [1980,  1,  1, 19.0,           0.0, 0.0],
               [1981,  7,  1, 20.0,           0.0, 0.0],
               [1982,  7,  1, 21.0,           0.0, 0.0],
               [1983,  7,  1, 22.0,           0.0, 0.0],
               [1985,  7,  1, 23.0,           0.0, 0.0],
               [1988,  1,  1, 24.0,           0.0, 0.0],
               [1990,  1,  1, 25.0,           0.0, 0.0],
               [1991,  1,  1, 26.0,           0.0, 0.0],
               [1992,  7,  1, 27.0,           0.0, 0.0],
               [1993,  7,  1, 28.0,           0.0, 0.0],
               [1994,  7,  1, 29.0,           0.0, 0.0],
               [1996,  1,  1, 30.0,           0.0, 0.0],
               [1997,  7,  1, 31.0,           0.0, 0.0],
               [1999,  1,  1, 32.0,           0.0, 0.0],
               [2006,  1,  1, 33.0,           0.0, 0.0],
               [2009,  1,  1, 34.0,           0.0, 0.0],
               [2012,  7,  1, 35.0,           0.0, 0.0],
               [2015,  7,  1, 36.0,           0.0, 0.0],
               [2017,  1,  1, 37.0,           0.0, 0.0]]

    NDAT = len(LTS)

    NST = None
    currentDay = -1
    currentJDay = -1
    currentLeapSeconds = -1

    def encode(epochs, iso_8601=True, unixtime=False):  # @NoSelf
        """
        Encodes the epoch(s) into UTC string(s). If unixtime is specified, outputs time in unix time.

        For CDF_EPOCH:
                The input should be either a float or list of floats
                (in numpy, a np.float64 or a np.ndarray of np.float64)
                Each epoch is encoded, by default to a ISO 8601 form:
                2004-05-13T15:08:11.022
                Or, if iso_8601 is set to False,
                2004-05-13 15:08:11.022
        For CDF_EPOCH16:
                The input should be either a complex or list of
                complex(in numpy, a np.complex128 or a np.ndarray of np.complex128)
                Each epoch is encoded, by default to a ISO 8601 form:
                2004-05-13T15:08:11.022033044055
                Or, if iso_8601 is set to False,
                2004-05-13 15:08:11.022.033.044.055
        For TT2000:
                The input should be either a int or list of ints
                (in numpy, a np.int64 or a np.ndarray of np.int64)
                Each epoch is encoded, by default to a ISO 8601 form:
                2008-02-02T06:08:10.10.012014016
                Or, if iso_8601 is set to False,
                2008-02-02 06:08:10.012.014.016
        """
        if isinstance(epochs, int) or isinstance(epochs, np.int64):
            return CDFepoch.encode_tt2000(epochs, iso_8601, unixtime)
        elif isinstance(epochs, float) or isinstance(epochs, np.float64):
            return CDFepoch.encode_epoch(epochs, iso_8601, unixtime)
        elif isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            return CDFepoch.encode_epoch16(epochs, iso_8601, unixtime)
        elif isinstance(epochs, list) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], int) or isinstance(epochs[0], np.int64):
                return CDFepoch.encode_tt2000(epochs, iso_8601, unixtime)
            elif isinstance(epochs[0], float) or isinstance(epochs[0], np.float64):
                return CDFepoch.encode_epoch(epochs, iso_8601, unixtime)
            elif isinstance(epochs[0], complex) or isinstance(epochs[0], np.complex128):
                return CDFepoch.encode_epoch16(epochs, iso_8601, unixtime)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def breakdown(epochs, to_np=None):  # @NoSelf
        # Returns either a single array, or a array of arrays depending on the input

        if isinstance(epochs, int) or isinstance(epochs, np.int64):
            return CDFepoch.breakdown_tt2000(epochs, to_np)
        elif isinstance(epochs, float) or isinstance(epochs, np.float64):
            return CDFepoch.breakdown_epoch(epochs, to_np)
        elif isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            return CDFepoch.breakdown_epoch16(epochs, to_np)
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], int) or isinstance(epochs[0], np.int64):
                return CDFepoch.breakdown_tt2000(epochs, to_np)
            elif isinstance(epochs[0], float) or isinstance(epochs[0], np.float64):
                return CDFepoch.breakdown_epoch(epochs, to_np)
            elif isinstance(epochs[0], complex) or isinstance(epochs[0], np.complex128):
                return CDFepoch.breakdown_epoch16(epochs, to_np)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def unixtime(cdf_time, to_np=False):  # @NoSelf
        """
        Encodes the epoch(s) into seconds after 1970-01-01.  Precision is only
        kept to the nearest microsecond.

        If to_np is True, then the values will be returned in a numpy array.
        """
        import datetime
        time_list = CDFepoch.breakdown(cdf_time, to_np=False)

        unix_times = CDFepoch.encode(cdf_time, iso_8601=False, unixtime=True)
        if to_np:
            unix_times = np.array(unix_times)
        return unix_times

    def compute(datetimes, to_np=None):  # @NoSelf
        """
        Computes the provided date/time components into CDF epoch value(s).

        For CDF_EPOCH:
                For computing into CDF_EPOCH value, each date/time elements should
                have exactly seven (7) components, as year, month, day, hour, minute,
                second and millisecond, in a list. For example:
                [[2017,1,1,1,1,1,111],[2017,2,2,2,2,2,222]]
                Or, call function compute_epoch directly, instead, with at least three
                (3) first (up to seven) components. The last component, if
                not the 7th, can be a float that can have a fraction of the unit.

        For CDF_EPOCH16:
                They should have exactly ten (10) components, as year,
                month, day, hour, minute, second, millisecond, microsecond, nanosecond
                and picosecond, in a list. For example:
                [[2017,1,1,1,1,1,123,456,789,999],[2017,2,2,2,2,2,987,654,321,999]]
                Or, call function compute_epoch directly, instead, with at least three
                (3) first (up to ten) components. The last component, if
                not the 10th, can be a float that can have a fraction of the unit.

        For TT2000:
                Each TT2000 typed date/time should have exactly nine (9) components, as
                year, month, day, hour, minute, second, millisecond, microsecond,
                and nanosecond, in a list.  For example:
                [[2017,1,1,1,1,1,123,456,789],[2017,2,2,2,2,2,987,654,321]]
                Or, call function compute_tt2000 directly, instead, with at least three
                (3) first (up to nine) components. The last component, if
                not the 9th, can be a float that can have a fraction of the unit.

        Specify to_np to True, if the result should be in numpy class.
        """

        if not isinstance(datetimes, (list, tuple, np.ndarray)):
            raise TypeError('datetime must be in list form')
        if isinstance(datetimes[0], numbers.Number):
            items = len(datetimes)
        elif isinstance(datetimes[0], (list, tuple, np.ndarray)):
            items = len(datetimes[0])
        else:
            print('Unknown input')
            return
        if items == 7:
            return CDFepoch.compute_epoch(datetimes, to_np)
        elif items == 10:
            return CDFepoch.compute_epoch16(datetimes, to_np)
        elif items == 9:
            return CDFepoch.compute_tt2000(datetimes, to_np)
        else:
            print('Unknown input')
            return

    def findepochrange(epochs, starttime=None, endtime=None):  # @NoSelf
        """
        Finds the record range within the start and end time from values
        of a CDF epoch data type. It returns a list of record numbers.
        If the start time is not provided, then it is
        assumed to be the minimum possible value. If the end time is not
        provided, then the maximum possible value is assumed. The epoch is
        assumed to be in the chronological order. The start and end times
        should have the proper number of date/time components, corresponding
        to the epoch's data type.

        The start/end times should be in either be in epoch units, or in the list
        format described in "compute_epoch/epoch16/tt2000" section.
        """
        if isinstance(epochs, float) or isinstance(epochs, np.float64):
            return CDFepoch.epochrange_epoch(epochs, starttime, endtime)
        elif isinstance(epochs, int) or isinstance(epochs, np.int64):
            return CDFepoch.epochrange_tt2000(epochs, starttime, endtime)
        elif isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            return CDFepoch.epochrange_epoch16(epochs, starttime, endtime)
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], float) or isinstance(epochs[0], np.float64):
                return CDFepoch.epochrange_epoch(epochs, starttime, endtime)
            elif isinstance(epochs[0], int) or isinstance(epochs[0], np.int64):
                return CDFepoch.epochrange_tt2000(epochs, starttime, endtime)
            elif isinstance(epochs[0], complex) or isinstance(epochs[0], np.complex128):
                return CDFepoch.epochrange_epoch16(epochs, starttime, endtime)
            else:
                print('Bad input')
                return None
        else:
            print('Bad input')
            return None

    def encode_tt2000(tt2000, iso_8601=None, unixtime=False):  # @NoSelf

        if isinstance(tt2000, int) or isinstance(tt2000, np.int64):
            new_tt2000 = [tt2000]
        elif isinstance(tt2000, list) or isinstance(tt2000, np.ndarray):
            new_tt2000 = tt2000
        else:
            print('Bad input')
        encoded = list()
        for x in new_tt2000:
            epoch, nansec = CDFepoch.breakdown_tt2000(x, encoding=True)
            epoch_astropy = Time(epoch, format='unix')
            base = Time('0000-01-01 00:00:00', scale='tai')
            t = epoch_astropy.unix + base.unix
            tt = Time(t, format='unix')
            if iso_8601:
                encoded.append(tt.isot[:-3] + str(nansec))
            elif not iso_8601 and not unixtime:
                nansec = str(nansec)
                one = nansec[:3]
                two = nansec[3:6]
                three = nansec[6:]
                encoded.append(tt.iso[:-3] + one + '.' + two + '.' + three)
            elif unixtime:
                u_time = float(str(tt.unix)[:-7] + str(nansec)[:3])
                encoded.append(u_time)
        if len(encoded) == 1:
            encoded = encoded[0]
        return encoded

    def breakdown_tt2000(tt2000, to_np=None, encoding=None):  # @NoSelf
        """
        Breaks down the epoch(s) into UTC components.

        For CDF_EPOCH:
                they are 7 date/time components: year, month, day,
                hour, minute, second, and millisecond
        For CDF_EPOCH16:
                they are 10 date/time components: year, month, day,
                hour, minute, second, and millisecond, microsecond,
                nanosecond, and picosecond.
        For TT2000:
                they are 9 date/time components: year, month, day,
                hour, minute, second, millisecond, microsecond,
                nanosecond.

        Specify to_np to True, if the result should be in numpy array.
        """
        if isinstance(tt2000, int) or isinstance(tt2000, np.int64):
            new_tt2000 = [tt2000]
        elif isinstance(tt2000, list) or isinstance(tt2000, tuple) or isinstance(tt2000, np.ndarray):
            new_tt2000 = tt2000
        else:
            print('Bad input data')
            return None
        count = len(new_tt2000)
        toutcs = list()
        for x in range(0, count):
            nanoSecSinceJ2000 = new_tt2000[x]
            toPlus = 0.0
            t3 = nanoSecSinceJ2000
            datx = CDFepoch._LeapSecondsfromJ2000(nanoSecSinceJ2000)
            if nanoSecSinceJ2000 > 0:
                secSinceJ2000 = int(nanoSecSinceJ2000 / CDFepoch.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 * CDFepoch.SECinNanoSecs)
                secSinceJ2000 = secSinceJ2000 - 32
                secSinceJ2000 = secSinceJ2000 + 43200
                nansec = nansec - 184000000
            else:
                nanoSecSinceJ2000 = nanoSecSinceJ2000 + CDFepoch.T12hinNanoSecs
                nanoSecSinceJ2000 = nanoSecSinceJ2000 - CDFepoch.dTinNanoSecs
                secSinceJ2000 = int(nanoSecSinceJ2000 / CDFepoch.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 * CDFepoch.SECinNanoSecs)
            if nansec < 0:
                nansec = CDFepoch.SECinNanoSecs + nansec
                secSinceJ2000 = secSinceJ2000 - 1
            t2 = secSinceJ2000 * CDFepoch.SECinNanoSecs + nansec
            if datx[0] > 0.0:
                # post-1972...
                secSinceJ2000 = secSinceJ2000 - int(datx[0])
                epoch = CDFepoch.J2000Since0AD12hSec + secSinceJ2000
                if datx[1] == 0.0:
                    date1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                else:
                    epoch = epoch - 1
                    date1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                    date1[5] = date1[5] + 1
                ye1 = date1[0]
                mo1 = date1[1]
                da1 = date1[2]
                ho1 = date1[3]
                mi1 = date1[4]
                se1 = date1[5]
                if encoding:
                    return epoch, nansec
            else:
                # pre-1972...
                epoch = secSinceJ2000 + CDFepoch.J2000Since0AD12hSec
                if encoding:
                    return epoch, nansec
                xdate1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                xdate1.append(0)
                xdate1.append(0)
                xdate1.append(nansec)
                tmpNanosecs = CDFepoch.compute_tt2000(xdate1)
                if tmpNanosecs != t3:
                    dat0 = CDFepoch._LeapSecondsfromYMD(xdate1[0],
                                               xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int(float(tmpx / CDFepoch.SECinNanoSecsD))
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                if nansec < 0:
                    nansec = CDFepoch.SECinNanoSecs + nansec
                    tmpy -= 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                    xdate1.append(0)
                    xdate1.append(0)
                    xdate1.append(nansec)
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate1)
                if tmpNanosecs != t3:
                    dat0 = CDFepoch._LeapSecondsfromYMD(xdate1[0],
                                               xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int((1.0 * tmpx) / CDFepoch.SECinNanoSecsD)
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                    if nansec < 0:
                        nansec = CDFepoch.SECinNanoSecs + nansec
                        tmpy = tmpy - 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                    xdate1.append(0)
                    xdate1.append(0)
                    xdate1.append(nansec)
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate1)
                    if tmpNanosecs != t3:
                        dat0 = CDFepoch._LeapSecondsfromYMD(xdate1[0],
                                                   xdate1[1],
                                                   xdate1[2])
                        tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                        tmpy = int((1.0 * tmpx) / CDFepoch.SECinNanoSecsD)
                        nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                        if nansec < 0:
                            nansec = CDFepoch.SECinNanoSecs + nansec
                            tmpy = tmpy - 1
                        epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                        # One more determination
                        xdate1 = CDFepoch._EPOCHbreakdownTT2000(epoch)
                ye1 = int(xdate1[0])
                mo1 = int(xdate1[1])
                da1 = int(xdate1[2])
                ho1 = int(xdate1[3])
                mi1 = int(xdate1[4])
                se1 = int(xdate1[5])
            ml1 = int(nansec / 1000000)
            tmp1 = nansec - 1000000 * ml1
            if ml1 > 1000:
                ml1 = ml1 - 1000
                se1 = se1 + 1
            ma1 = int(tmp1 / 1000)
            na1 = int(tmp1 - 1000 * ma1)
            datetime = list()
            datetime.append(ye1)
            datetime.append(mo1)
            datetime.append(da1)
            datetime.append(ho1)
            datetime.append(mi1)
            datetime.append(se1)
            datetime.append(ml1)
            datetime.append(ma1)
            datetime.append(na1)
            if count == 1:
                if to_np is None:
                    return datetime
                else:
                    return np.array(datetime)
            else:
                toutcs.append(datetime)
        if to_np is None:
            return toutcs
        else:
            return np.array(toutcs)

    def compute_tt2000(datetimes, to_np=None):  # @NoSelf

        if not isinstance(datetimes, list) and not isinstance(datetimes, tuple):
            print('datetime must be in list form')
            return None
        if isinstance(datetimes[0], numbers.Number):
            new_datetimes = [datetimes]
            count = 1
        else:
            count = len(datetimes)
            new_datetimes = datetimes
        nanoSecSinceJ2000s = list()
        for x in range(0, count):
            datetime = new_datetimes[x]
            year = int(datetime[0])
            month = int(datetime[1])
            items = len(datetime)
            if items > 8:
                # y m d h m s ms us ns
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(datetime[8])
            else:
                print('Invalid tt2000 components')
                return None
            if month == 0:
                month = 1
            if year == 9999 and month == 12 and day == 31 and hour == 23 and minute == 59 and second == 59 and \
                    msec == 999 and usec == 999 and nsec == 999:
                nanoSecSinceJ2000 = CDFepoch.FILLED_TT2000_VALUE
            elif year == 0 and month == 1 and day == 1 and hour == 0 and minute == 0 and second == 0 and msec == 0 and \
                    usec == 0 and nsec == 0:
                nanoSecSinceJ2000 = CDFepoch.DEFAULT_TT2000_PADVALUE
            else:
                iy = 10000000 * month + 10000 * day + year
                if iy != CDFepoch.currentDay:
                    CDFepoch.currentDay = iy
                    CDFepoch.currentLeapSeconds = CDFepoch._LeapSecondsfromYMD(year, month, day)
                    CDFepoch.currentJDay = CDFepoch._JulianDay(year, month, day)
                jd = CDFepoch.currentJDay
                jd = jd - CDFepoch.JulianDateJ2000_12h
                subDayinNanoSecs = int(hour * CDFepoch.HOURinNanoSecs +
                                       minute * CDFepoch.MINUTEinNanoSecs +
                                       second * CDFepoch.SECinNanoSecs + msec * 1000000 +
                                       usec * 1000 + nsec)
                nanoSecSinceJ2000 = int(jd * CDFepoch.DAYinNanoSecs +
                                        subDayinNanoSecs)
                t2 = int(CDFepoch.currentLeapSeconds * CDFepoch.SECinNanoSecs)
                if nanoSecSinceJ2000 < 0:
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
            if count == 1:
                if to_np is None:
                    return int(nanoSecSinceJ2000)
                else:
                    return np.array(int(nanoSecSinceJ2000))
            else:
                nanoSecSinceJ2000s.append(int(nanoSecSinceJ2000))
        if to_np is None:
            return nanoSecSinceJ2000s
        else:
            return np.array(nanoSecSinceJ2000s)

    def _LeapSecondsfromYMD(year, month, day):  # @NoSelf
        j = -1
        m = 12 * year + month
        for i, _ in reversed(list(enumerate(CDFepoch.LTS))):
            n = 12 * CDFepoch.LTS[i][0] + CDFepoch.LTS[i][1]
            if m >= n:
                j = i
                break
        if j == -1:
            return 0.0
        da = CDFepoch.LTS[j][3]
        # pre-1972
        if j < CDFepoch.NERA1:
            jda = CDFepoch._JulianDay(year, month, day)
            da = da + ((jda - CDFepoch.MJDbase) - CDFepoch.LTS[j][4]) * CDFepoch.LTS[j][5]
        return da

    def _LeapSecondsfromJ2000(nanosecs):  # @NoSelf
        da = list()
        da.append(0.0)
        da.append(0.0)
        j = -1
        if CDFepoch.NST is None:
            NST = CDFepoch._LoadLeapNanoSecondsTable()
        for i, _ in reversed(list(enumerate(NST))):
            if nanosecs >= NST[i]:
                j = i
                if i < (CDFepoch.NDAT - 1):
                    if (nanosecs + 1000000000) >= NST[i + 1]:
                        da[1] = 1.0
                break
        if j <= CDFepoch.NERA1:
            return da
        da[0] = CDFepoch.LTS[j][3]
        return da

    def _LoadLeapNanoSecondsTable():  # @NoSelf
        NST = list()
        for ix in range(0, CDFepoch.NERA1):
            NST.append(CDFepoch.FILLED_TT2000_VALUE)
        for ix in range(CDFepoch.NERA1, CDFepoch.NDAT):
            NST.append(CDFepoch.compute_tt2000(
                [int(CDFepoch.LTS[ix][0]), int(CDFepoch.LTS[ix][1]), int(CDFepoch.LTS[ix][2]), 0, 0, 0, 0, 0, 0]))
        return NST

    def _EPOCHbreakdownTT2000(epoch):  # @NoSelf
        second_AD = epoch
        minute_AD = second_AD / 60.0
        hour_AD = minute_AD / 60.0
        day_AD = hour_AD / 24.0

        jd = int(1721060 + day_AD)
        l = jd + 68569
        n = int(4 * l / 146097)
        l = l - int((146097 * n + 3) / 4)
        i = int(4000 * (l + 1) / 1461001)
        l = l - int(1461 * i / 4) + 31
        j = int(80 * l / 2447)
        k = l - int(2447 * j / 80)
        l = int(j / 11)
        j = j + 2 - 12 * l
        i = 100 * (n - 49) + i + l

        date = list()
        date.append(i)
        date.append(j)
        date.append(k)
        date.append(int(hour_AD % 24.0))
        date.append(int(minute_AD % 60.0))
        date.append(int(second_AD % 60.0))
        return date

    def epochrange_tt2000(epochs, starttime=None, endtime=None):  # @NoSelf
        if isinstance(epochs, int) or isinstance(epochs, np.int64):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], int) or isinstance(epochs[0], np.int64):
                new_epochs = epochs
            else:
                print('Bad data')
                return None
        else:
            print('Bad data')
            return None
        if starttime is None:
            stime = int(-9223372036854775807)
        else:
            if isinstance(starttime, int) or isinstance(starttime, np.int64):
                stime = starttime
            elif isinstance(starttime, list):
                stime = CDFepoch.compute_tt2000(starttime)
            else:
                print('Bad start time')
                return None
        if endtime is not None:
            if isinstance(endtime, int) or isinstance(endtime, np.int64):
                etime = endtime
            elif isinstance(endtime, list) or isinstance(endtime, tuple):
                etime = CDFepoch.compute_tt2000(endtime)
            else:
                print('Bad end time')
                return None
        else:
            etime = int(9223372036854775807)
        if stime > etime:
            print('Invalid start/end time')
            return None
        if isinstance(new_epochs, list) or isinstance(new_epochs, tuple):
            new_epochs2 = np.array(new_epochs)
        else:
            new_epochs2 = new_epochs
        return np.where(np.logical_and(new_epochs2 >= stime, new_epochs2 <= etime))[0]

    def encode_epoch16(epochs, iso_8601=True, unixtime=False):  # @NoSelf
        if isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            new_epochs = epochs
        else:
            print('Bad data')
            return None
        base = Time('0000-01-01 00:00:00', scale='tai')
        final_epochs = list()
        for epoch16 in new_epochs:
            epoch_m = epoch16.real + base.unix
            t = Time(epoch_m, format='unix', scale='utc')
            if iso_8601:
                final_time = t.isot[:-3] + str(epoch16.imag * 10 ** (-12))[2:].ljust(12, '0')
                final_epochs.append(final_time)
            if not iso_8601 and not unixtime:
                msec = str('{:.12f}'.format(epoch16.imag * 10 ** (-12)))[2:]
                components = [msec[0:3], msec[3:6], msec[6:9], msec[9:12]]
                final_time = t.iso[:-3] + components[0] + '.' + components[1] + '.' + components[2] + '.' + \
                             components[3]
                final_epochs.append(final_time)
            if not iso_8601 and unixtime:
                unix_time = '%.3f' % t.unix
                final_epochs.append(float(unix_time))
        if len(final_epochs) == 1:
            final_epochs = final_epochs[0]
        return final_epochs

    def _JulianDay(y, m, d):  # @NoSelf
        a1 = int(7 * (int(y + int((m + 9) / 12))) / 4)
        a2 = int(3 * (int(int(y + int((m - 9) / 7)) / 100) + 1) / 4)
        a3 = int(275 * m / 9)
        return 367 * y - a1 - a2 + a3 + d + 1721029

    def compute_epoch16(datetimes, to_np=None):  # @NoSelf
        if not isinstance(datetimes, list) and not isinstance(datetimes, tuple):
            print('Bad input')
            return None
        if not isinstance(datetimes[0], list) and not isinstance(datetimes[0], tuple):
            new_dates = [datetimes]
        else:
            new_dates = datetimes
        count = len(new_dates)
        if count == 0:
            return None
        epochs = list()
        for x in range(0, count):
            epoch = list()
            date = new_dates[x]
            year = date[0]
            month = date[1]
            # y m d h m s ms us ns ps
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(date[6])
            usec = int(date[7])
            nsec = int(date[8])
            psec = int(date[9])
            if year < 0:
                print('Illegal epoch field')
                return
            if (year == 9999 and month == 12 and day == 31 and hour == 23 and minute == 59 and second == 59 and
                    msec == 999 and usec == 999 and nsec == 999 and psec == 999):
                epoch.append(-1.0E31)
                epoch.append(-1.0E31)
            elif ((year > 9999) or (month < 0 or month > 12) or (hour < 0 or hour > 23) or (
                    minute < 0 or minute > 59)
                  or (second < 0 or second > 59) or (msec < 0 or msec > 999) or (usec < 0 or usec > 999) or
                  (nsec < 0 or nsec > 999) or (psec < 0 or psec > 999)):
                epoch = CDFepoch._computeEpoch16(year, month, day, hour,
                                        minute, second, msec,
                                        usec, nsec, psec)
            else:
                if month == 0:
                    if day < 1 or day > 366:
                        epoch = CDFepoch._computeEpoch16(year, month, day, hour, minute, second, msec, usec, nsec, psec)
                else:
                    if day < 1 or day > 31:
                        epoch = CDFepoch._computeEpoch16(year, month, day, hour, minute, second, msec, usec, nsec, psec)
                if month == 0:
                    daysSince0AD = CDFepoch._JulianDay(year, 1, 1) + (day - 1) - 1721060
                else:
                    daysSince0AD = CDFepoch._JulianDay(year, month, day) - 1721060
                secInDay = (3600 * hour) + (60 * minute) + second
                epoch16_0 = float(86400.0 * daysSince0AD) + float(secInDay)
                epoch16_1 = float(psec) + float(1000.0 * nsec) + float(1000000.0 * usec) + float(
                    1000000000.0 * msec)
                epoch.append(epoch16_0)
                epoch.append(epoch16_1)
            cepoch = complex(epoch[0], epoch[1])
            if count == 1:
                if to_np is None:
                    return cepoch
                else:
                    return np.array(cepoch)
            else:
                epochs.append(cepoch)
        if to_np is None:
            return epochs
        else:
            return np.array(epochs)

    def breakdown_epoch16(epochs, to_np=None):  # @NoSelf
        if isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            new_epochs = epochs
        else:
            print('Bad data')
            return
        components = list()
        for epoch16 in new_epochs:
            base = Time('0000-01-01 00:00:00', scale='tai')
            epoch_m = epoch16.real + base.unix
            t = Time(epoch_m, format='unix', scale='utc')
            pattern = re.compile(r'([0-9]+)-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]+)')
            m = pattern.match(t.iso).groups()
            year = int(m[0])
            month = int(m[1])
            day = int(m[2])
            hour = int(m[3])
            min = int(m[4])
            sec = int(m[5])
            msec = str('{:.12f}'.format(epoch16.imag * 10 ** (-12)))[2:]
            breakdown = [year, month, day, hour, min, sec, int(msec[0:3]), int(msec[3:6]), int(msec[6:9]),
                         int(msec[9:12])]
            components.append(breakdown)
        if len(components) == 1:
            if to_np is None:
                return components[0]
            elif to_np is not None:
                return np.array(components)
        else:
            if to_np is None:
                return components
            elif to_np is not None:
                components = [np.array(x) for x in components]
                return np.array(components[0])

    def _computeEpoch16(y, m, d, h, mn, s, ms, msu, msn, msp):  # @NoSelf
        if m == 0:
            daysSince0AD = CDFepoch._JulianDay(y, 1, 1) + (d - 1) - 1721060
        else:
            if m < 0:
                y -= 1
                m = 13 + m
            daysSince0AD = CDFepoch._JulianDay(y, m, d) - 1721060
        if daysSince0AD < 0:
            print('Illegal epoch')
            return None
        epoch = list()
        epoch.append(float(86400.0 * daysSince0AD + 3600.0 * h + 60.0 * mn) + float(s))
        epoch.append(float(msp) + float(1000.0 * msn) + float(1000000.0 * msu) + math.pow(10.0, 9) * ms)
        if epoch[1] < 0.0 or epoch[1] >= math.pow(10.0, 12):
            if epoch[1] < 0.0:
                sec = int(epoch[1] / math.pow(10.0, 12))
                tmp = epoch[1] - sec * math.pow(10.0, 12)
                if tmp != 0.0 and tmp != -0.0:
                    epoch[0] = epoch[0] + sec - 1
                    epoch[1] = math.pow(10.0, 12.0) + tmp
                else:
                    epoch[0] = epoch[0] + sec
                    epoch[1] = 0.0
            else:
                sec = int(epoch[1] / math.pow(10.0, 12))
                tmp = epoch[1] - sec * math.pow(10.0, 12)
                if tmp != 0.0 and tmp != -0.0:
                    epoch[1] = tmp
                    epoch[0] = epoch[0] + sec
                else:
                    epoch[1] = 0.0
                    epoch[0] = epoch[0] + sec
        if epoch[0] < 0.0:
            print('Illegal epoch')
            return None
        else:
            return epoch

    def epochrange_epoch16(epochs, starttime=None, endtime=None):  # @NoSelf
        if isinstance(epochs, complex) or isinstance(epochs, np.complex128):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], complex) or isinstance(epochs[0], np.complex128):
                new_epochs = epochs
            else:
                print('Bad data')
                return None
        else:
            print('Bad data')
            return None
        if starttime is None:
            stime = list()
            stime.append(-1.0E31)
            stime.append(-1.0E31)
        else:
            if isinstance(starttime, complex) or isinstance(starttime, np.complex128):
                stime = list()
                stime.append(starttime.real)
                stime.append(starttime.imag)
            elif isinstance(starttime, list) or isinstance(starttime, tuple):
                sstime = CDFepoch.compute_epoch16(starttime)
                stime = list()
                stime.append(sstime.real)
                stime.append(sstime.imag)
            else:
                print('Bad start time')
                return None
        if endtime is not None:
            if isinstance(endtime, complex) or isinstance(endtime, np.complex128):
                etime = list()
                etime.append(endtime.real)
                etime.append(endtime.imag)
            elif isinstance(endtime, list) or isinstance(endtime, tuple):
                eetime = CDFepoch.compute_epoch16(endtime)
                etime = list()
                etime.append(eetime.real)
                etime.append(eetime.imag)
            else:
                print('Bad start time')
                return None
        else:
            etime = list()
            etime.append(1.0E31)
            etime.append(1.0E31)
        if stime[0] > etime[0] or (stime[0] == etime[0] and stime[1] > etime[1]):
            print('Invalid start/end time')
            return None
        count = len(new_epochs)
        epoch16 = []
        for x in range(0, count):
            epoch16.append(new_epochs[x].real)
            epoch16.append(new_epochs[x].imag)
        count = count * 2
        indx = []
        if (epoch16[0] > etime[0] or (epoch16[0] == etime[0] and
                                      epoch16[1] > etime[1])):
            return None
        if (epoch16[count - 2] < stime[0] or
                (epoch16[count - 2] == stime[0] and
                 epoch16[count - 1] < stime[1])):
            return None
        for x in range(0, count, 2):
            if epoch16[x] < stime[0]:
                continue
            elif epoch16[x] == stime[0]:
                if epoch16[x + 1] < stime[1]:
                    continue
                else:
                    indx.append(int(x / 2))
                    break
            else:
                indx.append(int(x / 2))
                break
        if len(indx) == 0:
            indx.append(0)
        hasadded = False
        for x in range(0, count, 2):
            if epoch16[x] < etime[0]:
                continue
            elif epoch16[x] == etime[0]:
                if epoch16[x + 1] > etime[1]:
                    indx.append(int((x - 1) / 2))
                    hasadded = True
                    break
            else:
                indx.append(int((x - 1) / 2))
                hasadded = True
                break
        if not hasadded:
            indx.append(int(count / 2) - 1)
        return np.arange(indx[0], indx[1] + 1, step=1)

    def encode_epoch(epochs, iso_8601=True, unixtime=False):  # @NoSelf
        if isinstance(epochs, float) or isinstance(epochs, np.float64):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, np.ndarray):
            new_epochs = epochs
        else:
            print('Bad data')
            return None
        base = Time('0000-01-01 00:00:00', scale='tai')
        final_times = list()
        for epoch in new_epochs:
            epoch_m = (epoch / np.float(1000)) + base.unix
            t = Time(epoch_m, format='unix')
            if iso_8601:
                final_times.append(t.isot)
            elif not iso_8601 and not unixtime:
                final_times.append(t.iso)
            elif not iso_8601 and unixtime:
                unix_time = '%.3f' % t.unix
                final_times.append(float(unix_time))
        if len(final_times) == 1:
            final_times = final_times[0]
        return final_times

    def compute_epoch(dates, to_np=None):  # @NoSelf
        if not isinstance(dates, list) and not isinstance(dates, tuple):
            print('Bad input')
            return None
        if not isinstance(dates[0], list) and not isinstance(dates[0], tuple):
            new_dates = [dates]
        else:
            new_dates = dates
        count = len(new_dates)
        if count == 0:
            return None
        epochs = list()
        for x in range(0, count):
            date = new_dates[x]
            datetime_date = datetime.datetime(date[0], date[1], date[2], date[3], date[4], date[5])
            datetime_date = datetime_date + datetime.timedelta(milliseconds=date[6])
            astropy_date = Time(datetime_date).unix
            base = abs(Time('0000-01-01 00:00:00').unix)
            epoch = round((astropy_date + abs(base)) * 1000, 1)
            epochs.append(epoch)
        if len(epochs) == 1:
            if to_np is None:
                return epochs[0]
            elif to_np is not None:
                return np.array(epochs)
        else:
            if to_np is None:
                return epochs
            elif to_np is not None:
                components = [np.array(x) for x in epochs]
                return np.array(components[0])

    def _computeEpoch(y, m, d, h, mn, s, ms):  # @NoSelf
        if m == 0:
            daysSince0AD = CDFepoch._JulianDay(y, 1, 1) + (d - 1) - 1721060
        else:
            if m < 0:
                m = 13 + m
            daysSince0AD = CDFepoch._JulianDay(y, m, d) - 1721060
        if daysSince0AD < 1:
            print('ILLEGAL_EPOCH_FIELD')
            return None
        msecInDay = float(3600000.0 * h + 60000.0 * mn + 1000.0 * s) + float(ms)
        msecFromEpoch = float(86400000.0 * daysSince0AD + msecInDay)
        if msecFromEpoch < 0.0:
            return -1.0
        else:
            return msecFromEpoch

    def breakdown_epoch(epochs, to_np=False):  # @NoSelf
        if isinstance(epochs, float) or isinstance(epochs, np.float64):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            new_epochs = epochs
        else:
            print('Bad data')
            return None
        base = Time('0000-01-01 00:00:00', scale='tai')
        components = list()
        for epoch in new_epochs:
            component = list()
            epoch_m = (epoch / np.float(1000)) + base.unix
            t = Time(epoch_m, format='unix')
            pattern = re.compile(r'([0-9]+)-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]+)')
            m = pattern.match(t.iso).groups()
            component.append(int(m[0]))
            component.append(int(m[1]))
            component.append(int(m[2]))
            component.append(int(m[3]))
            component.append(int(m[4]))
            component.append(int(m[5]))
            component.append(int(m[6]))
            components.append(component)
        if len(components) == 1:
            if to_np is None:
                return components[0]
            elif to_np is not None:
                return np.array(components)
        else:
            if to_np is None:
                return components
            elif to_np is not None:
                components = [np.array(x) for x in components]
                return np.array(components[0])

    def epochrange_epoch(epochs, starttime=None, endtime=None):  # @NoSelf
        if isinstance(epochs, float) or isinstance(epochs, np.float64):
            new_epochs = [epochs]
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if (isinstance(epochs[0], float) or
                    isinstance(epochs[0], np.float64)):
                new_epochs = epochs
            else:
                print('Bad data')
                return None
        else:
            print('Bad data')
            return None
        if starttime is None:
            stime = 0.0
        else:
            if isinstance(starttime, float) or isinstance(starttime, int) or isinstance(starttime, np.float64):
                stime = starttime
            elif isinstance(starttime, list) or isinstance(starttime, tuple):
                stime = CDFepoch.compute_epoch(starttime)
            else:
                print('Bad start time')
                return None
        if endtime is not None:
            if isinstance(endtime, float) or isinstance(endtime, int) or isinstance(endtime, np.float64):
                etime = endtime
            elif isinstance(endtime, list) or isinstance(endtime, tuple):
                etime = CDFepoch.compute_epoch(endtime)
            else:
                print('Bad end time')
                return None
        else:
            etime = 1.0E31
        if stime > etime:
            print('Invalid start/end time')
            return None
        if isinstance(new_epochs, list) or isinstance(new_epochs, tuple):
            new_epochs2 = np.array(new_epochs)
        else:
            new_epochs2 = new_epochs
        return np.where(np.logical_and(new_epochs2 >= stime, new_epochs2 <= etime))[0]

    def parse(value, to_np=None):  # @NoSelf
        """
        Parses the provided date/time string(s) into CDF epoch value(s).

        For CDF_EPOCH:
                The string has to be in the form of 'yyyy-mm-dd hh:mm:ss.xxx' or
                'yyyy-mm-ddThh:mm:ss.xxx' (in iso_8601). The string is the output
                from encode function.

        For CDF_EPOCH16:
                The string has to be in the form of
                'yyyy-mm-dd hh:mm:ss.mmm.uuu.nnn.ppp' or
                'yyyy-mm-ddThh:mm:ss.mmmuuunnnppp' (in iso_8601). The string is
                the output from encode function.

        For TT2000:
                The string has to be in the form of
                'yyyy-mm-dd hh:mm:ss.mmm.uuu.nnn' or
                'yyyy-mm-ddThh:mm:ss.mmmuuunnn' (in iso_8601). The string is
                the output from encode function.

        Specify to_np to True, if the result should be in numpy class.
        """
        if isinstance(value, list) or isinstance(value, tuple):
            if not isinstance(value[0], str):
                print('Invalid value... should be a string or a list of strings')
                return None
        if not isinstance(value, list) and not isinstance(value, tuple) and not isinstance(value, str):
            print('Invalid value... should be a string or a list of strings')
            return None
        else:
            if isinstance(value, list) or isinstance(value, tuple):
                num = len(value)
                epochs = []
                for x in range(0, num):
                    epochs.append(CDFepoch._parse_epoch(value[x]))
                if to_np is None:
                    return epochs
                else:
                    return np.array(epochs)
            else:
                if to_np is None:
                    return CDFepoch._parse_epoch(value)
                else:
                    return np.array(CDFepoch._parse_epoch(value))

    def _parse_epoch(value):  # @NoSelf
        if isinstance(value, list) or isinstance(value, tuple):
            epochs = list()
            for x in range(0, len(value)):
                epochs.append(value[x])
            return epochs
        else:
            if len(value) == 23:
                # CDF_EPOCH
                if value.lower() == '9999-12-31t23:59:59.999' or value.lower() == '9999-12-31 23:59:59.999':
                    return -1.0E31
                else:
                    date = re.findall('(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)', value)
                    if not date:
                        date = re.findall('(\d+)\-(\d+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)', value)
                    yy = int(date[0][0])
                    mm = int(date[0][1])
                    dd = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    ms = int(date[0][6])
                return CDFepoch.compute_epoch([yy, mm, dd, hh, mn, ss, ms])
            elif len(value) == 35 or (len(value) == 32):
                # CDF_EPOCH16
                if value.lower() == '9999-12-31 23:59:59.999.999.999.999' or value.lower() == \
                        '9999-12-31t23:59:59.999999999999':
                    return -1.0E31 - 1.0E31j
                else:
                    date = re.findall('(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)', value)
                    if not date:
                        date = re.findall('(\d+)\-(\d+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)', value)
                    yy = int(date[0][0])
                    mm = int(date[0][1])
                    dd = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    if len(date[0]) == 7:
                        subs = int(date[0][6])
                        ms = int(subs / 1000000000)
                        subms = int(subs % 1000000000)
                        us = int(subms / 1000000)
                        subus = int(subms % 1000000)
                        ns = int(subus / 1000)
                        ps = int(subus % 1000)
                    else:
                        ms = int(date[0][6])
                        us = int(date[0][7])
                        ns = int(date[0][8])
                        ps = int(date[0][9])
                return CDFepoch.compute_epoch16([yy, mm, dd, hh, mn, ss, ms, us, ns, ps])
            elif len(value) == 29 or len(value) == 31:
                # CDF_TIME_TT2000
                value = value.lower()
                if value == '9999-12-31t23:59:59.999999999' or value == '9999-12-31 23:59:59.999.999.999':
                    return -9223372036854775808
                elif value == '0000-01-01t00:00.000000000' or value == '0000-01-01 00:00.000.000.000':
                    return -9223372036854775807
                else:
                    date = re.findall('(\d+)\-(\d+)\-(\d+)t(\d+)\:(\d+)\:(\d+)\.(\d+)', value)
                    if not date:
                        date = re.findall('(\d+)\-(\d+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)', value)
                    yy = int(date[0][0])
                    mm = int(date[0][1])
                    dd = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    if len(date[0]) == 7:
                        subs = int(date[0][6])
                        ms = int(subs / 1000000)
                        subms = int(subs % 1000000)
                        us = int(subms / 1000)
                        ns = int(subms % 1000)
                    else:
                        ms = int(date[0][6])
                        us = int(date[0][7])
                        ns = int(date[0][8])
                return CDFepoch.compute_tt2000([yy, mm, dd, hh, mn, ss, ms, us, ns])
            else:
                print('Invalid cdf epoch type...')
                return None

    def getVersion():  # @NoSelf
        """
        Shows the code version.
        """
        print('epochs version:', str(CDFepoch.version) + '.' +
              str(CDFepoch.release) + '.'+str(CDFepoch.increment))

    def getLeapSecondLastUpdated():  # @NoSelf
        """
        Shows the latest date a leap second was added to the leap second table.
        """
        print('Leap second last updated:', str(CDFepoch.LTS[-1][0]) + '-' +
              str(CDFepoch.LTS[-1][1]) + '-' + str(CDFepoch.LTS[-1][2]))
