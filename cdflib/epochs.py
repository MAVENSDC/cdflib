"""
##########
CDF Epochs
##########

Importing cdflib also imports the module CDFepoch, which handles
CDF-based epochs.

The following functions can be used to convert back and forth between
ifferent ways to display the date.

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
import datetime
import numpy as np
import math
import re
import numbers
from pathlib import Path
import logging
import urllib.request
import csv
from typing import List, Union, Sequence   # noqa: F401

FILLED_TT2000_VALUE = int(-9223372036854775808)
DEFAULT_TT2000_PADVALUE = int(-9223372036854775807)
MONTH_TOKEN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


class CDFepoch:

    def __init__(self) -> None:
        self.version = 3
        self.release = 7
        self.increment = 0

        self.JulianDateJ2000_12h = 2451545
        self.J2000Since0AD12h = 730485
        self.J2000Since0AD12hSec = 63113904000.0
        self.J2000Since0AD12hMilsec = 63113904000000.0
        self.J2000LeapSeconds = 32.0
        self.dT = 32.184
        self.dTinNanoSecs = 32184000000
        self.MJDbase = 2400000.5
        self.SECinNanoSecs = 1000000000
        self.SECinNanoSecsD = 1000000000.0
        self.DAYinNanoSecs = int(86400000000000)
        self.HOURinNanoSecs = int(3600000000000)
        self.MINUTEinNanoSecs = int(60000000000)
        self.T12hinNanoSecs = int(43200000000000)
        # Julian days for 1707-09-22 and 2292-04-11, the valid TT2000 range
        self.JDY17070922 = 2344793
        self.JDY22920411 = 2558297
        self.DEFAULT_TT2000_PADVALUE = DEFAULT_TT2000_PADVALUE
        self.FILLED_TT2000_VALUE = FILLED_TT2000_VALUE
        self.NERA1 = 14

        # LASTLEAPSECONDDAY = 20170101
        library_path = Path(__file__).parent
        leap_sec_file = library_path / 'CDFLeapSeconds.txt'
        # Attempt to download latest leap second table
        try:
            leapsecond_files_url = "https://cdf.gsfc.nasa.gov/html/CDFLeapSeconds.txt"
            page = urllib.request.urlopen(leapsecond_files_url)

            with leap_sec_file.open("wb") as lsfile:
                lsfile.write(page.read())
        except Exception:
            logging.error("Can't download new leap second table")

        # Attempt to load the leap second table saved in the cdflib
        try:
            self.LTS = []  # type: List[List[Union[int, float]]]
            with leap_sec_file.open('r') as lsfile:
                lsreader = csv.reader(lsfile, delimiter=' ')
                for row in lsreader:
                    if row[0] == ";":
                        continue
                    row = list(filter(('').__ne__, row))

                    self.LTS.append([int(row[0]),
                                     int(row[1]),
                                     int(row[2]),
                                     float(row[3]),
                                     float(row[4]),
                                     float(row[5])])
        except FileNotFoundError:
            print("Can't find leap second table.  Using one built into code.")
            print("Last leap second in built in table is on Jan 01 2017. ")
            # Use a built in leap second table
            self.LTS = [[1960, 1, 1, 1.4178180, 37300.0, 0.0012960],
                        [1961, 1, 1, 1.4228180, 37300.0, 0.0012960],
                        [1961, 8, 1, 1.3728180, 37300.0, 0.0012960],
                        [1962, 1, 1, 1.8458580, 37665.0, 0.0011232],
                        [1963, 11, 1, 1.9458580, 37665.0, 0.0011232],
                        [1964, 1, 1, 3.2401300, 38761.0, 0.0012960],
                        [1964, 4, 1, 3.3401300, 38761.0, 0.0012960],
                        [1964, 9, 1, 3.4401300, 38761.0, 0.0012960],
                        [1965, 1, 1, 3.5401300, 38761.0, 0.0012960],
                        [1965, 3, 1, 3.6401300, 38761.0, 0.0012960],
                        [1965, 7, 1, 3.7401300, 38761.0, 0.0012960],
                        [1965, 9, 1, 3.8401300, 38761.0, 0.0012960],
                        [1966, 1, 1, 4.3131700, 39126.0, 0.0025920],
                        [1968, 2, 1, 4.2131700, 39126.0, 0.0025920],
                        [1972, 1, 1, 10.0, 0.0, 0.0],
                        [1972, 7, 1, 11.0, 0.0, 0.0],
                        [1973, 1, 1, 12.0, 0.0, 0.0],
                        [1974, 1, 1, 13.0, 0.0, 0.0],
                        [1975, 1, 1, 14.0, 0.0, 0.0],
                        [1976, 1, 1, 15.0, 0.0, 0.0],
                        [1977, 1, 1, 16.0, 0.0, 0.0],
                        [1978, 1, 1, 17.0, 0.0, 0.0],
                        [1979, 1, 1, 18.0, 0.0, 0.0],
                        [1980, 1, 1, 19.0, 0.0, 0.0],
                        [1981, 7, 1, 20.0, 0.0, 0.0],
                        [1982, 7, 1, 21.0, 0.0, 0.0],
                        [1983, 7, 1, 22.0, 0.0, 0.0],
                        [1985, 7, 1, 23.0, 0.0, 0.0],
                        [1988, 1, 1, 24.0, 0.0, 0.0],
                        [1990, 1, 1, 25.0, 0.0, 0.0],
                        [1991, 1, 1, 26.0, 0.0, 0.0],
                        [1992, 7, 1, 27.0, 0.0, 0.0],
                        [1993, 7, 1, 28.0, 0.0, 0.0],
                        [1994, 7, 1, 29.0, 0.0, 0.0],
                        [1996, 1, 1, 30.0, 0.0, 0.0],
                        [1997, 7, 1, 31.0, 0.0, 0.0],
                        [1999, 1, 1, 32.0, 0.0, 0.0],
                        [2006, 1, 1, 33.0, 0.0, 0.0],
                        [2009, 1, 1, 34.0, 0.0, 0.0],
                        [2012, 7, 1, 35.0, 0.0, 0.0],
                        [2015, 7, 1, 36.0, 0.0, 0.0],
                        [2017, 1, 1, 37.0, 0.0, 0.0]]

        self.NDAT = len(self.LTS)

        self.NST = None
        self.currentDay = -1
        self.currentJDay = -1
        self.currentLeapSeconds = -1

    def encode(self, epochs, iso_8601: bool=True) -> Union[str, List[str]]:
        """
        Encodes the epoch(s) into UTC string(s).

        For CDF_EPOCH:
                The input should be either a float or list of floats
                (in numpy, a np.float64 or a np.ndarray of np.float64)
                Each epoch is encoded, by default to a ISO 8601 form:
                2004-05-13T15:08:11.022
                Or, if iso_8601 is set to False,
                13-May-2004 15:08:11.022
        For CDF_EPOCH16:
                The input should be either a complex or list of
                complex(in numpy, a np.complex128 or a np.ndarray of np.complex128)
                Each epoch is encoded, by default to a ISO 8601 form:
                2004-05-13T15:08:11.022033044055
                Or, if iso_8601 is set to False,
                13-May-2004 15:08:11.022.033.044.055
        For TT2000:
                The input should be either a int or list of ints
                (in numpy, a np.int64 or a np.ndarray of np.int64)
                Each epoch is encoded, by default to a ISO 8601 form:
                2008-02-02T06:08:10.10.012014016
                Or, if iso_8601 is set to False,
                02-Feb-2008 06:08:10.012.014.016
        """
        if isinstance(epochs, (int, np.int64)):
            return self.encode_tt2000(epochs, iso_8601)
        elif isinstance(epochs, (float, np.float64)):
            return encode_epoch(epochs, iso_8601)
        elif isinstance(epochs, (complex, np.complex128)):
            return encode_epoch16(epochs, iso_8601)
        elif isinstance(epochs, (list, np.ndarray)):
            if isinstance(epochs[0], (int,  np.int64)):
                return self.encode_tt2000(epochs, iso_8601)
            elif isinstance(epochs[0], (float, np.float64)):
                return encode_epoch(epochs, iso_8601)
            elif isinstance(epochs[0], (complex, np.complex128)):
                return encode_epoch16(epochs, iso_8601)
            else:
                raise TypeError('Bad input')
        else:
            raise TypeError('Bad input')

    def breakdown(self, epochs, to_np: bool=False):

        if isinstance(epochs, (int, np.int64)):
            return self.breakdown_tt2000(epochs, to_np)
        elif isinstance(epochs, (float, np.float64)):
            return breakdown_epoch(epochs, to_np)
        elif isinstance(epochs, (complex, np.complex128)):
            return breakdown_epoch16(epochs, to_np)
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (int, np.int64)):
                return self.breakdown_tt2000(epochs, to_np)
            elif isinstance(epochs[0], (float, np.float64)):
                return breakdown_epoch(epochs, to_np)
            elif isinstance(epochs[0], (complex, np.complex128)):
                return breakdown_epoch16(epochs, to_np)
            else:
                raise TypeError('Bad input')
        else:
            raise TypeError('Bad input')

    def unixtime(self, cdf_time, to_np: bool=False):
        """
        Encodes the epoch(s) into seconds after 1970-01-01.  Precision is only
        kept to the nearest microsecond.

        If to_np is True, then the values will be returned in a numpy array.
        """
        time_list = self.breakdown(cdf_time, to_np=False)

        unixtime = [datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5],
                                      microsecond=t[6]*1000+t[7]).replace(
            tzinfo=datetime.timezone.utc).timestamp() for t in time_list]

        return np.array(unixtime) if to_np else unixtime

    def compute(self, datetimes, to_np: bool=False):
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
            raise TypeError('Unknown input')

        if items == 7:
            return compute_epoch(datetimes, to_np)
        elif items == 10:
            return compute_epoch16(datetimes, to_np)
        elif items == 9:
            return self.compute_tt2000(datetimes, to_np)
        else:
            raise ValueError('Bad input')

    def findepochrange(self, epochs, starttime=None, endtime=None):
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
        if isinstance(epochs, (float, np.float64)):
            return self.epochrange_epoch(epochs, starttime, endtime)
        elif isinstance(epochs, (int, np.int64)):
            return self.epochrange_tt2000(epochs, starttime, endtime)
        elif isinstance(epochs, (complex, np.complex128)):
            return self.epochrange_epoch16(epochs, starttime, endtime)
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (float, np.float64)):
                return self.epochrange_epoch(epochs, starttime, endtime)
            elif isinstance(epochs[0], (int, np.int64)):
                return self.epochrange_tt2000(epochs, starttime, endtime)
            elif isinstance(epochs[0], (complex, np.complex128)):
                return self.epochrange_epoch16(epochs, starttime, endtime)
            else:
                raise TypeError('Bad input')
        else:
            raise TypeError('Bad input')

    def encode_tt2000(self, tt2000, iso_8601=None):

        if isinstance(tt2000, (int, np.int64)):
            new_tt2000 = [tt2000]
        elif isinstance(tt2000, (list, np.ndarray)):
            new_tt2000 = tt2000
        else:
            raise TypeError('Bad input')
        count = len(new_tt2000)
        encodeds = []
        for x in range(count):
            nanoSecSinceJ2000 = new_tt2000[x]
            if nanoSecSinceJ2000 == self.FILLED_TT2000_VALUE:
                if iso_8601 is None or iso_8601:
                    return '9999-12-31T23:59:59.999999999'
                else:
                    return '31-Dec-9999 23:59:59.999.999.999'
            if nanoSecSinceJ2000 == self.DEFAULT_TT2000_PADVALUE:
                if iso_8601 is None or iso_8601:
                    return '0000-01-01T00:00:00.000000000'
                else:
                    return '01-Jan-0000 00:00:00.000.000.000'

            datetime = self.breakdown_tt2000(nanoSecSinceJ2000)
            ly = datetime[0]
            lm = datetime[1]
            ld = datetime[2]
            lh = datetime[3]
            ln = datetime[4]
            ls = datetime[5]
            ll = datetime[6]
            lu = datetime[7]
            la = datetime[8]

            if iso_8601 is None or iso_8601:
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
                encoded += MONTH_TOKEN[lm - 1]
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

            if count == 1:
                return encoded
            else:
                encodeds.append(encoded)
        return encodeds

    def breakdown_tt2000(self, tt2000, to_np: bool=False):
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

        if isinstance(tt2000, (int, np.int64)):
            new_tt2000 = [tt2000]
        elif isinstance(tt2000, (list, tuple, np.ndarray)):
            new_tt2000 = tt2000
        else:
            print('Bad input data')
            return None
        count = len(new_tt2000)
        toutcs = []
        for x in range(count):
            nanoSecSinceJ2000 = new_tt2000[x]
            # toPlus = 0.0
            t3 = nanoSecSinceJ2000
            datx = self._LeapSecondsfromJ2000(nanoSecSinceJ2000)
            if (nanoSecSinceJ2000 > 0):
                secSinceJ2000 = int(nanoSecSinceJ2000 / self.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 *
                             self.SECinNanoSecs)
                secSinceJ2000 = secSinceJ2000 - 32
                secSinceJ2000 = secSinceJ2000 + 43200
                nansec = nansec - 184000000
            else:
                nanoSecSinceJ2000 = nanoSecSinceJ2000 + self.T12hinNanoSecs
                nanoSecSinceJ2000 = nanoSecSinceJ2000 - self.dTinNanoSecs
                secSinceJ2000 = int(nanoSecSinceJ2000 / self.SECinNanoSecsD)
                nansec = int(nanoSecSinceJ2000 - secSinceJ2000 *
                             self.SECinNanoSecs)
            if (nansec < 0):
                nansec = self.SECinNanoSecs + nansec
                secSinceJ2000 = secSinceJ2000 - 1
            t2 = secSinceJ2000 * self.SECinNanoSecs + nansec
            if (datx[0] > 0.0):
                # post-1972...
                secSinceJ2000 = secSinceJ2000 - int(datx[0])
                epoch = self.J2000Since0AD12hSec + secSinceJ2000
                if (datx[1] == 0.0):
                    date1 = self._EPOCHbreakdownTT2000(epoch)
                else:
                    epoch = epoch - 1
                    date1 = self._EPOCHbreakdownTT2000(epoch)
                    date1[5] = date1[5] + 1
                ye1 = date1[0]
                mo1 = date1[1]
                da1 = date1[2]
                ho1 = date1[3]
                mi1 = date1[4]
                se1 = date1[5]
            else:
                # pre-1972...
                epoch = secSinceJ2000 + self.J2000Since0AD12hSec
                xdate1 = self._EPOCHbreakdownTT2000(epoch)
                xdate1.append(0)
                xdate1.append(0)
                xdate1.append(nansec)
                tmpNanosecs = self.compute_tt2000(xdate1)
                if (tmpNanosecs != t3):
                    dat0 = self._LeapSecondsfromYMD(xdate1[0],
                                                    xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * self.SECinNanoSecs)
                    tmpy = int(float(tmpx / self.SECinNanoSecsD))
                    nansec = int(tmpx - tmpy * self.SECinNanoSecs)
                if (nansec < 0):
                    nansec = self.SECinNanoSecs + nansec
                    tmpy = tmpy - 1
                    epoch = tmpy + self.J2000Since0AD12hSec
                    xdate1 = self._EPOCHbreakdownTT2000(epoch)
                    xdate1.append(0)
                    xdate1.append(0)
                    xdate1.append(nansec)
                    tmpNanosecs = self.compute_tt2000(xdate1)
                if (tmpNanosecs != t3):
                    dat0 = self._LeapSecondsfromYMD(xdate1[0],
                                                    xdate1[1], xdate1[2])
                    tmpx = t2 - int(dat0 * self.SECinNanoSecs)
                    tmpy = int((1.0 * tmpx) / self.SECinNanoSecsD)
                    nansec = int(tmpx - tmpy * self.SECinNanoSecs)
                    if (nansec < 0):
                        nansec = self.SECinNanoSecs + nansec
                        tmpy = tmpy - 1
                    epoch = tmpy + self.J2000Since0AD12hSec
                    xdate1 = self._EPOCHbreakdownTT2000(epoch)
                    xdate1.append(0)
                    xdate1.append(0)
                    xdate1.append(nansec)
                    tmpNanosecs = self.compute_tt2000(xdate1)
                    if (tmpNanosecs != t3):
                        dat0 = self._LeapSecondsfromYMD(xdate1[0],
                                                        xdate1[1],
                                                        xdate1[2])
                        tmpx = t2 - int(dat0 * self.SECinNanoSecs)
                        tmpy = int((1.0 * tmpx) / self.SECinNanoSecsD)
                        nansec = int(tmpx - tmpy * self.SECinNanoSecs)
                        if (nansec < 0):
                            nansec = self.SECinNanoSecs + nansec
                            tmpy = tmpy - 1
                        epoch = tmpy + self.J2000Since0AD12hSec
                        # One more determination
                        xdate1 = self._EPOCHbreakdownTT2000(epoch)
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
                if not to_np:
                    return datetime
                else:
                    return np.array(datetime)
            else:
                toutcs.append(datetime)

        if not to_np:
            return toutcs
        else:
            return np.array(toutcs)

    def _LeapSecondsfromYMD(self, year, month, day):

        j = -1
        m = 12 * year + month
        for i, _ in reversed(list(enumerate(self.LTS))):
            n = 12 * self.LTS[i][0] + self.LTS[i][1]
            if (m >= n):
                j = i
                break
        if (j == -1):
            return 0.0
        da = self.LTS[j][3]
        # pre-1972
        if (j < self.NERA1):
            jda = _JulianDay(year, month, day)
            da = da + ((jda - self.MJDbase) - self.LTS[j][4]) * self.LTS[j][5]
        return da

    def _LeapSecondsfromJ2000(self, nanosecs):

        da = []
        da.append(0.0)
        da.append(0.0)
        j = -1
        if self.NST is None:
            self._LoadLeapNanoSecondsTable()
        for i, _ in reversed(list(enumerate(self.NST))):
            if (nanosecs >= self.NST[i]):
                j = i
                if i < (self.NDAT - 1):
                    if (nanosecs + 1000000000) >= self.NST[i + 1]:
                        da[1] = 1.0
                break
        if (j <= self.NERA1):
            return da
        da[0] = self.LTS[j][3]
        return da

    def _LoadLeapNanoSecondsTable(self):

        self.NST = []
        for ix in range(self.NERA1):
            self.NST.append(self.FILLED_TT2000_VALUE)
        for ix in range(self.NERA1, self.NDAT):
            self.NST.append(self.compute_tt2000([int(self.LTS[ix][0]),
                                                 int(self.LTS[ix][1]),
                                                 int(self.LTS[ix][2]),
                                                 0, 0, 0, 0, 0, 0]))

    def _EPOCHbreakdownTT2000(self, epoch):

        second_AD = epoch
        minute_AD = second_AD / 60.0
        hour_AD = minute_AD / 60.0
        day_AD = hour_AD / 24.0

        jd = int(1721060 + day_AD)
        L = jd + 68569
        n = int(4 * L / 146097)
        L = L - int((146097 * n + 3) / 4)
        i = int(4000 * (L + 1) / 1461001)
        L = L - int(1461 * i / 4) + 31
        j = int(80 * L / 2447)
        k = L - int(2447 * j / 80)
        L = int(j / 11)
        j = j + 2 - 12 * L
        i = 100 * (n - 49) + i + L

        date = []
        date.append(i)
        date.append(j)
        date.append(k)
        date.append(int(hour_AD % 24.0))
        date.append(int(minute_AD % 60.0))
        date.append(int(second_AD % 60.0))
        return date

    def epochrange_tt2000(self, epochs, starttime=None, endtime=None):

        if isinstance(epochs, (int, np.int64)):
            # new2_epochs = [epochs]
            pass
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (int, np.int64)):
                # new2_epochs = epochs
                pass
            else:
                raise TypeError('Bad data')
        else:
            raise TypeError('Bad data')
        if starttime is None:
            stime = int(-9223372036854775807)
        else:
            if isinstance(starttime, (int, np.int64)):
                stime = starttime
            elif (isinstance(starttime, list)):
                stime = self.compute_tt2000(starttime)
            else:
                raise TypeError('Bad start time')

        if endtime is not None:
            if isinstance(endtime, (int, np.int64)):
                etime = endtime
            elif isinstance(endtime, (list, tuple)):
                etime = self.compute_tt2000(endtime)
            else:
                raise TypeError('Bad end time')
        else:
            etime = int(9223372036854775807)

        if stime > etime:
            raise ValueError('Invalid start/end time')

        if isinstance(epochs, (list, tuple)):
            new_epochs = np.array(epochs)
        else:
            new_epochs = epochs

        return np.where(np.logical_and(new_epochs >= stime, new_epochs <= etime))[0]

    def epochrange_epoch16(self, epochs: Sequence[complex],
                           starttime: Sequence[complex]=None, endtime: Sequence[complex]=None) -> np.ndarray:

        if isinstance(epochs, (complex, np.complex128)):
            new_epochs = [epochs]
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (complex, np.complex128)):
                new_epochs = epochs
            else:
                raise TypeError('Bad data')
        else:
            raise TypeError('Bad data')

        if starttime is None:
            stime = []
            stime.append(-1.0E31)
            stime.append(-1.0E31)
        else:
            if isinstance(starttime, (complex, np.complex128)):
                stime = []
                stime.append(starttime.real)
                stime.append(starttime.imag)
            elif isinstance(starttime, (list, tuple)):
                sstime = compute_epoch16(starttime)
                stime = []
                stime.append(sstime.real)
                stime.append(sstime.imag)
            else:
                raise TypeError('Bad start time')

        if endtime is not None:
            if isinstance(endtime, (complex, np.complex128)):
                etime = []
                etime.append(endtime.real)
                etime.append(endtime.imag)
            elif isinstance(endtime, (list, tuple)):
                eetime = compute_epoch16(endtime)
                etime = []
                etime.append(eetime.real)
                etime.append(eetime.imag)
            else:
                raise TypeError('Bad start time')

        else:
            etime = []
            etime.append(1.0E31)
            etime.append(1.0E31)
        if (stime[0] > etime[0] or (stime[0] == etime[0] and stime[1] > etime[1])):
            raise ValueError('Invalid start/end time')

        count = len(new_epochs)
        epoch16 = []
        for x in range(count):
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
            if (epoch16[x] < stime[0]):
                continue
            elif (epoch16[x] == stime[0]):
                if (epoch16[x + 1] < stime[1]):
                    continue
                else:
                    indx.append(int(x / 2))
                    break
            else:
                indx.append(int(x / 2))
                break
        if (len(indx) == 0):
            indx.append(0)
        hasadded = False
        for x in range(0, count, 2):
            if (epoch16[x] < etime[0]):
                continue
            elif (epoch16[x] == etime[0]):
                if (epoch16[x + 1] > etime[1]):
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

    def epochrange_epoch(self, epochs, starttime=None, endtime=None):

        if isinstance(epochs, (float, np.float64)):
            # new2_epochs = [epochs]
            pass
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (float, np.float64)):
                # new2_epochs = epochs
                pass
            else:
                raise ValueError('Bad data')
        else:
            raise ValueError('Bad data')

        if starttime is None:
            stime = 0.0
        else:
            if isinstance(starttime, (float, int, np.float64)):
                stime = starttime
            elif isinstance(starttime, (list, tuple)):
                stime = compute_epoch(starttime)
            else:
                raise ValueError('Bad start time')
        if endtime is not None:
            if isinstance(endtime, (float, int, np.float64)):
                etime = endtime
            elif isinstance(endtime, (list, tuple)):
                etime = compute_epoch(endtime)
            else:
                raise ValueError('Bad end time')
        else:
            etime = 1.0E31
        if (stime > etime):
            raise ValueError('Invalid start/end time')
        if isinstance(epochs, (list, tuple)):
            new_epochs = np.array(epochs)
        else:
            new_epochs = epochs
        return np.where(np.logical_and(new_epochs >= stime, new_epochs <= etime))[0]

    def parse(self, value, to_np: bool=False):
        """
        Parses the provided date/time string(s) into CDF epoch value(s).

        For CDF_EPOCH:
                The string has to be in the form of 'dd-mmm-yyyy hh:mm:ss.xxx' or
                'yyyy-mm-ddThh:mm:ss.xxx' (in iso_8601). The string is the output
                from encode function.

        For CDF_EPOCH16:
                The string has to be in the form of
                'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn.ppp' or
                'yyyy-mm-ddThh:mm:ss.mmmuuunnnppp' (in iso_8601). The string is
                the output from encode function.

        For TT2000:
                The string has to be in the form of
                'dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn' or
                'yyyy-mm-ddThh:mm:ss.mmmuuunnn' (in iso_8601). The string is
                the output from encode function.

        Specify to_np to True, if the result should be in numpy class.
        """
        if isinstance(value, (list, tuple)) and not isinstance(value[0], str):
            raise TypeError('should be a string or a list of string')
        elif not isinstance(value, (list, tuple, str)):
            raise TypeError('should be a string or a list of string')
        else:
            if isinstance(value, (list, tuple)):
                num = len(value)
                epochs = []
                for x in range(num):
                    epochs.append(self._parse_epoch(value[x]))
                if not to_np:
                    return epochs
                else:
                    return np.array(epochs)
            else:
                if not to_np:
                    return self._parse_epoch(value)
                else:
                    return np.array(self._parse_epoch(value))

    def _parse_epoch(self, value):
        if isinstance(value, (list, tuple)):
            epochs = []
            for x in range(len(value)):
                epochs.append(value[x])
            return epochs
        else:
            if len(value) in (23, 24):
                # CDF_EPOCH
                if value.lower() in ('31-dec-9999 23:59:59.999', '9999-12-31t23:59:59.999'):
                    return -1.0E31
                else:
                    if len(value) == 24:
                        date = re.findall('(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)', value)
                        dd = int(date[0][0])
                        mm = self._month_index(date[0][1])
                        yy = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        ms = int(date[0][6])
                    else:
                        date = re.findall('(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)',
                                          value)
                        yy = int(date[0][0])
                        mm = int(date[0][1])
                        dd = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        ms = int(date[0][6])

                    return compute_epoch([yy, mm, dd, hh, mn, ss, ms])

            elif len(value) == 36 or (len(value) == 32 and value[10].lower() == 't'):
                # CDF_EPOCH16
                if value.lower() in ('31-dec-9999 23:59:59.999.999.999.999', '9999-12-31t23:59:59.999999999999'):
                    return -1.0E31 - 1.0E31j
                else:
                    if len(value) == 36:
                        date = re.findall('(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)',
                                          value)
                        dd = int(date[0][0])
                        mm = self._month_index(date[0][1])
                        yy = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        ms = int(date[0][6])
                        us = int(date[0][7])
                        ns = int(date[0][8])
                        ps = int(date[0][9])
                    else:
                        date = re.findall('(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)',
                                          value)
                        yy = int(date[0][0])
                        mm = int(date[0][1])
                        dd = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        subs = int(date[0][6])
                        ms = int(subs / 1000000000)
                        subms = int(subs % 1000000000)
                        us = int(subms / 1000000)
                        subus = int(subms % 1000000)
                        ns = int(subus / 1000)
                        ps = int(subus % 1000)
                    return compute_epoch16([yy, mm, dd, hh, mn, ss, ms, us, ns, ps])

            elif len(value) == 29 or (len(value) == 32 and value[11] == ' '):
                # CDF_TIME_TT2000
                value = value.lower()
                if value in ('9999-12-31t23:59:59.999999999', '31-dec-9999 23:59:59.999.999.999'):
                    return -9223372036854775808
                elif value in ('0000-01-01t00:00.000000000', '01-jan-0000 00:00.000.000.000'):
                    return -9223372036854775807
                else:
                    if len(value) == 29:
                        date = re.findall('(\d+)\-(\d+)\-(\d+)t(\d+)\:(\d+)\:(\d+)\.(\d+)',
                                          value)
                        yy = int(date[0][0])
                        mm = int(date[0][1])
                        dd = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        subs = int(date[0][6])
                        ms = int(subs / 1000000)
                        subms = int(subs % 1000000)
                        us = int(subms / 1000)
                        ns = int(subms % 1000)
                    else:
                        date = re.findall('(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)',
                                          value)
                        dd = int(date[0][0])
                        mm = self._month_index(date[0][1])
                        yy = int(date[0][2])
                        hh = int(date[0][3])
                        mn = int(date[0][4])
                        ss = int(date[0][5])
                        ms = int(date[0][6])
                        us = int(date[0][7])
                        ns = int(date[0][8])
                    return self.compute_tt2000([yy, mm, dd, hh, mn, ss, ms, us, ns])
            else:
                raise TypeError('Invalid cdf epoch type')

    def getVersion(self):
        """
        Shows the code version.
        """
        print('epochs version: {}.{}.{}'.format(self.version, self.release, self.increment))
        print('Date: 2018/01/11')

    def getLeapSecondLastUpdated(self):
        """
        Shows the latest date a leap second was added to the leap second table.
        """
        print('Leap second last updated: {}-{}-{}'.format(self.LTS[-1][0], self.LTS[-1][1], self.LTS[-1][2]))

    def compute_tt2000(self, datetimes, to_np: bool=False):

        if not isinstance(datetimes, (list, tuple)):
            raise TypeError('datetime must be in list form')

        new_datetimes = [datetimes] if isinstance(datetimes[0], numbers.Number) else datetimes

        count = len(new_datetimes)

        nanoSecSinceJ2000s = []
        for x in range(count):
            datetime = new_datetimes[x]
            year = int(datetime[0])
            month = int(datetime[1])
            items = len(datetime)
            if (items > 8):
                # y m d h m s ms us ns
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(datetime[8])
            elif (items > 7):
                # y m d h m s ms us
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(1000.0 * (datetime[7] - usec))
            elif (items > 6):
                # y m d h m s ms
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                xxx = float(1000.0 * (datetime[6] - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items > 5):
                # y m d h m s
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                xxx = float(1000.0 * (datetime[5] - second))
                msec = int(xxx)
                xxx = float(1000.0 * (xxx - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif (items > 4):
                # y m d h m
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
            elif (items > 3):
                # y m d h
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
            elif (items > 2):
                # y m d
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
                raise ValueError('Invalid tt2000 components')

            if month == 0:
                month = 1

            if (year == 9999 and month == 12 and day == 31 and hour == 23 and
                minute == 59 and second == 59 and msec == 999 and
                    usec == 999 and nsec == 999):
                nanoSecSinceJ2000 = FILLED_TT2000_VALUE
            elif (year == 0 and month == 1 and day == 1 and hour == 0 and
                  minute == 0 and second == 0 and msec == 0 and usec == 0 and
                  nsec == 0):
                nanoSecSinceJ2000 = DEFAULT_TT2000_PADVALUE
            else:
                iy = 10000000 * month + 10000 * day + year
                if (iy != self.currentDay):
                    self.currentDay = iy
                    self.currentLeapSeconds = self._LeapSecondsfromYMD(year, month, day)
                    self.currentJDay = _JulianDay(year, month, day)
                jd = self.currentJDay
                jd = jd - self.JulianDateJ2000_12h
                subDayinNanoSecs = int(hour * self.HOURinNanoSecs +
                                       minute * self.MINUTEinNanoSecs +
                                       second * self.SECinNanoSecs + msec * 1000000 +
                                       usec * 1000 + nsec)
                nanoSecSinceJ2000 = int(jd * self.DAYinNanoSecs +
                                        subDayinNanoSecs)
                t2 = int(self.currentLeapSeconds * self.SECinNanoSecs)
                if (nanoSecSinceJ2000 < 0):
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 +
                                            self.dTinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 -
                                            self.T12hinNanoSecs)
                else:
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 -
                                            self.T12hinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 +
                                            self.dTinNanoSecs)
            if count == 1:
                if not to_np:
                    return int(nanoSecSinceJ2000)
                else:
                    return np.array(int(nanoSecSinceJ2000))
            else:
                nanoSecSinceJ2000s.append(int(nanoSecSinceJ2000))

        if not to_np:
            return nanoSecSinceJ2000s
        else:
            return np.array(nanoSecSinceJ2000s)


def encode_epoch16(epochs: Sequence[complex], iso_8601: bool=True):

    if isinstance(epochs, (complex, np.complex128)):
        new_epochs = [epochs]
    elif isinstance(epochs, (list, tuple, np.ndarray)):
        new_epochs = epochs
    else:
        raise ValueError('Bad data')

    count = len(new_epochs)
    encodeds = []
    for x in range(count):
        # complex
        if (new_epochs[x].real == -1.0E31) and (new_epochs[x].imag == -1.0E31):
            encoded = '9999-12-31T23:59:59.999999999999' if iso_8601 else '31-Dec-9999 23:59:59.999.999.999.999'
        else:
            encoded = _encodex_epoch16(new_epochs[x], iso_8601)
        if (count == 1):
            return encoded
        else:
            encodeds.append(encoded)

    return encodeds


def _encodex_epoch16(epoch16: Sequence[complex], iso_8601: bool=True):

    components = breakdown_epoch16(epoch16)
    if iso_8601:
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
        encoded += MONTH_TOKEN[components[1] - 1]
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


def breakdown_epoch16(epochs: Sequence[complex], to_np: bool=False):

    if isinstance(epochs, (complex, np.complex128)):
        new_epochs = [epochs]
    elif isinstance(epochs, (list, tuple, np.ndarray)):
        new_epochs = epochs
    else:
        raise TypeError('Bad input')

    count = len(new_epochs)
    components = []
    for x in range(count):
        component = []
        epoch16 = []
        # complex
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
            L = jd + 68569
            n = int(4 * L / 146097)
            L = L - int((146097 * n + 3) / 4)
            i = int(4000 * (L + 1) / 1461001)
            L = L - int(1461 * i / 4) + 31
            j = int(80 * L / 2447)
            k = L - int(2447 * j / 80)
            L = int(j / 11)
            j = j + 2 - 12 * L
            i = 100 * (n - 49) + i + L
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
        if count == 1:
            if not to_np:
                return component
            else:
                return np.array(component)
        else:
            components.append(component)
    if not to_np:
        return components
    else:
        return np.array(components)


def encode_epoch(epochs: Sequence[float], iso_8601: bool=True) -> Union[str, List[str]]:

    if isinstance(epochs, (float, np.float64)):
        new_epochs = [epochs]
    elif isinstance(epochs, (list, np.ndarray)):
        new_epochs = epochs
    else:
        raise TypeError('Bad data')

    count = len(new_epochs)
    encodeds = []
    for x in range(count):
        epoch = new_epochs[x]
        if epoch == -1.0E31:
            encoded = '9999-12-31T23:59:59.999' if iso_8601 else '31-Dec-9999 23:59:59.999'
        else:
            encoded = _encodex_epoch(epoch, iso_8601)

        if count == 1:
            return encoded

        encodeds.append(encoded)

    return encodeds


def _encodex_epoch(epoch: Sequence[float], iso_8601: bool=False) -> str:

    components = breakdown_epoch(epoch)
    if iso_8601:
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
        encoded += MONTH_TOKEN[components[1] - 1]
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


def breakdown_epoch(epochs: Sequence[float], to_np: bool=False) -> np.ndarray:

    if isinstance(epochs, (float, np.float64)):
        new_epochs = [epochs]
    elif isinstance(epochs, (list, tuple, np.ndarray)):
        new_epochs = epochs
    else:
        raise TypeError('Bad data')

    count = len(new_epochs)
    components = []
    for x in range(count):
        component = []
        epoch = new_epochs[x]
        if epoch == -1.0E31:
            component.append(9999)
            component.append(12)
            component.append(31)
            component.append(23)
            component.append(59)
            component.append(59)
            component.append(999)
        else:
            if epoch < 0.:
                epoch = -epoch

            if isinstance(epochs, int):
                epoch = float(epoch)

            msec_AD = epoch
            second_AD = msec_AD / 1000.0
            minute_AD = second_AD / 60.0
            hour_AD = minute_AD / 60.0
            day_AD = hour_AD / 24.0
            jd = int(1721060 + day_AD)
            L = jd + 68569
            n = int(4 * L / 146097)
            L = L - int((146097 * n + 3) / 4)
            i = int(4000 * (L + 1) / 1461001)
            L = L - int(1461 * i / 4) + 31
            j = int(80 * L / 2447)
            k = L - int(2447 * j / 80)
            L = int(j / 11)
            j = j + 2 - 12 * L
            i = 100 * (n - 49) + i + L
            component.append(i)
            component.append(j)
            component.append(k)
            component.append(int(hour_AD % 24.0))
            component.append(int(minute_AD % 60.0))
            component.append(int(second_AD % 60.0))
            component.append(int(msec_AD % 1000.0))
        if (count == 1):
            if to_np:
                return np.array(component)
            else:
                return component
        else:
            components.append(component)
    if to_np:
        return np.array(components)
    else:
        return components


def compute_epoch16(datetimes, to_np: bool=False) -> np.ndarray:

    if not isinstance(datetimes, (list, tuple)):
        raise TypeError('Bad input')

    new_dates = datetimes if isinstance(datetimes[0], (list, tuple)) else [datetimes]

    count = len(new_dates)
    if count == 0:
        return None

    epochs = []
    for x in range(count):
        epoch = []
        date = new_dates[x]
        items = len(date)
        year = date[0]
        month = date[1]
        if (items > 9):
            # y m d h m s ms us ns ps
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(date[6])
            usec = int(date[7])
            nsec = int(date[8])
            psec = int(date[9])
        elif (items > 8):
            # y m d h m s ms us ns
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(date[6])
            usec = int(date[7])
            nsec = int(date[8])
            psec = int(1000.0 * (date[8] - nsec))
        elif (items > 7):
            # y m d h m s ms us
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(date[6])
            usec = int(date[7])
            xxx = int(1000.0 * (date[7] - usec))  # type: Union[float, int]
            nsec = int(xxx)
            psec = int(1000.0 * (xxx - nsec))
        elif (items > 6):
            # y m d h m s ms
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
        elif (items > 5):
            # y m d h m s
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
        elif (items > 4):
            # y m d h m
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
        elif (items > 3):
            # y m d h
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
        elif (items > 2):
            # y m d
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
            raise ValueError('Invalid epoch16 components')

        if year < 0:
            raise ValueError('Illegal epoch field')

        if (year == 9999 and month == 12 and day == 31 and hour == 23 and
            minute == 59 and second == 59 and msec == 999 and
                usec == 999 and nsec == 999 and psec == 999):
            epoch.append(-1.0E31)
            epoch.append(-1.0E31)
        elif ((year > 9999) or (month < 0 or month > 12) or
              (hour < 0 or hour > 23) or (minute < 0 or minute > 59) or
              (second < 0 or second > 59) or (msec < 0 or msec > 999) or
              (usec < 0 or usec > 999) or (nsec < 0 or nsec > 999) or
              (psec < 0 or psec > 999)):
            epoch = _computeEpoch16(year, month, day, hour,
                                    minute, second, msec,
                                    usec, nsec, psec)
        else:
            if (month == 0):
                if (day < 1 or day > 366):
                    epoch = _computeEpoch16(year, month, day, hour,
                                            minute, second, msec,
                                            usec, nsec, psec)
            else:
                if (day < 1 or day > 31):
                    epoch = _computeEpoch16(year, month, day, hour,
                                            minute, second, msec,
                                            usec, nsec, psec)
            if (month == 0):
                daysSince0AD = _JulianDay(year, 1, 1) + (day - 1) - 1721060
            else:
                daysSince0AD = _JulianDay(year, month, day) - 1721060
            secInDay = (3600 * hour) + (60 * minute) + second
            epoch16_0 = float(86400.0 * daysSince0AD) + float(secInDay)
            epoch16_1 = float(psec) + float(1000.0 * nsec) + float(1000000.0 * usec) + float(1000000000.0 * msec)
            epoch.append(epoch16_0)
            epoch.append(epoch16_1)
        cepoch = complex(epoch[0], epoch[1])
        if count == 1:
            if not to_np:
                return cepoch
            else:
                return np.array(cepoch)
        else:
            epochs.append(cepoch)

    if not to_np:
        return epochs
    else:
        return np.array(epochs)


def _computeEpoch16(y: int, m: int, d: int, h: int, mn: int, s: int, ms: int, msu: int, msn: int, msp: int):

    if (m == 0):
        daysSince0AD = _JulianDay(y, 1, 1) + (d - 1) - 1721060
    else:
        if (m < 0):
            y = y - 1
            m = 13 + m
        daysSince0AD = _JulianDay(y, m, d) - 1721060

    if daysSince0AD < 0:
        raise ValueError('Illegal epoch')

    epoch = []
    epoch.append(float(86400.0 * daysSince0AD + 3600.0 * h + 60.0 * mn) + float(s))
    epoch.append(float(msp) + float(1000.0 * msn) + float(1000000.0 * msu) + 10.0**9 * ms)
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
        raise ValueError('Illegal epoch')

    return epoch


def compute_epoch(dates: Sequence[Sequence[int]], to_np: bool=False):

    if not isinstance(dates, (list, tuple)):
        raise TypeError('Bad input')

    new_dates = dates if isinstance(dates[0], (list, tuple)) else [dates]

    count = len(new_dates)
    if count == 0:
        return None

    epochs = []
    for x in range(count):
        date = new_dates[x]
        year = date[0]
        month = date[1]
        items = len(date)
        if (items > 6):
            # y m d h m s ms
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(date[6])
        elif (items > 5):
            # y m d h m s
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            second = int(date[5])
            msec = int(1000.0 * (date[5] - second))
        elif (items > 4):
            # y m d h m
            day = int(date[2])
            hour = int(date[3])
            minute = int(date[4])
            xxx = float(60.0 * (date[4] - minute))
            second = int(xxx)
            msec = int(1000.0 * (xxx - second))
        elif (items > 3):
            # y m d h
            day = int(date[2])
            hour = int(date[3])
            xxx = float(60.0 * (date[3] - hour))
            minute = int(xxx)
            xxx = float(60.0 * (xxx - minute))
            second = int(xxx)
            msec = int(1000.0 * (xxx - second))
        elif (items > 2):
            # y m d
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
        if (year == 9999 and month == 12 and day == 31 and hour == 23 and
                minute == 59 and second == 59 and msec == 999):
            epochs.append(-1.0E31)
        if (year < 0):
            print('ILLEGAL_EPOCH_FIELD')
            return None
        if (year > 9999 or not 0 <= month <= 12 or
            not 0 <= hour <= 23 or not 0 <= minute <= 59 or
                not 0 <= second <= 59 or 0 <= msec <= 999):
            epochs.append(_computeEpoch(year, month, day, hour, minute,
                                        second, msec))
        if month == 0:
            if not 1 <= day <= 366:
                epochs.append(_computeEpoch(year, month, day, hour,
                                            minute, second, msec))
        else:
            if not 1 <= day <= 31:
                epochs.append(_computeEpoch(year, month, day, hour,
                                            minute, second, msec))
        if (hour == 0 and minute == 0 and second == 0):
            if not 0 <= msec <= 86399999:
                epochs.append(_computeEpoch(year, month, day, hour,
                                            minute, second, msec))

        if (month == 0):
            daysSince0AD = _JulianDay(year, 1, 1) + (day - 1) - 1721060
        else:
            daysSince0AD = _JulianDay(year, month, day) - 1721060
        if (hour == 0 and minute == 0 and second == 0):
            msecInDay = msec
        else:
            msecInDay = (3600000 * hour) + (60000 * minute) + (1000 * second) + msec
        if (count == 1):
            if not to_np:
                return 86400000.0 * daysSince0AD + msecInDay
            else:
                return np.array((86400000.0 * daysSince0AD + msecInDay))
        epochs.append(86400000.0 * daysSince0AD + msecInDay)
    if (not to_np):
        return epochs
    else:
        return np.array(epochs)


def _computeEpoch(y: int, m: int, d: int, h: int, mn: int, s: int, ms: float):

    if (m == 0):
        daysSince0AD = _JulianDay(y, 1, 1) + (d - 1) - 1721060
    else:
        if (m < 0):
            --y
            m = 13 + m
        daysSince0AD = _JulianDay(y, m, d) - 1721060
    if (daysSince0AD < 1):
        print('ILLEGAL_EPOCH_FIELD')
        return None
    msecInDay = float(3600000.0 * h + 60000.0 * mn + 1000.0 * s) + float(ms)
    msecFromEpoch = float(86400000.0 * daysSince0AD + msecInDay)

    if msecFromEpoch < 0.0:
        return -1.0
    else:
        return msecFromEpoch


def _JulianDay(y: int, m: int, d: int) -> int:

    a1 = int(7 * (int(y + int((m + 9) / 12))) / 4)
    a2 = int(3 * (int(int(y + int((m - 9) / 7)) / 100) + 1) / 4)
    a3 = int(275 * m / 9)
    return (367 * y - a1 - a2 + a3 + d + 1721029)


def _month_index(month: str) -> int:
    return datetime.datetime.strptime(month, '%b').month
