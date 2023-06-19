import csv
import datetime
import math
import os
import re
from typing import List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt

from cdflib.utils import _squeeze_or_scalar_complex, _squeeze_or_scalar_real

LEAPSEC_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "CDFLeapSeconds.txt")

epochs_type = Union[str, List[float], List[int], List[complex], Tuple[float, ...], Tuple[int, ...], Tuple[complex, ...], np.ndarray]


epoch_scalar_types = Union[int, np.int64, float, np.float64, complex, np.complex128]
epoch_list_types = Union[List[int], List[np.int64], List[float], List[np.float64], List[complex], List[np.complex128]]
epoch_types = Union[epoch_scalar_types, epoch_list_types, npt.NDArray]

encoded_type = Union[str, List[str]]

cdf_epoch_type = Union[float, np.float64, List[float], npt.NDArray[np.float64]]
cdf_epoch16_type = Union[complex, np.complex128, List[complex], npt.NDArray[np.complex128]]
cdf_tt2000_type = Union[int, np.int64, List[int], npt.NDArray[np.int64]]


class CDFepoch:
    """
    Convert between CDF-based epochs, np.datetime64, and Unix time.

    There are three (3) epoch data types in CDF:
        1. CDF_EPOCH is milliseconds since Year 0 represented as a
        single double (float in Python),
        2. CDF_EPOCH16 is picoseconds since Year 0 represented as
        2-doubles (complex in Python), and
        3. CDF_TIME_TT2000 (TT2000 as short) is nanoseconds since J2000 with
        leap seconds, represented by an 8-byte integer (int in Python).

    In Numpy, they are np.float64, np.complex128 and np.int64, respectively.
    All these epoch values can come from from CDF.varget function.


    Example
    -------
    >>> import cdflib
    # Convert to an epoch
    >>> epoch = cdflib.cdfepoch.compute_epoch([2017,1,1,1,1,1,111])
    # Convert from an epoch
    >>> time = cdflib.cdfepoch.to_datetime(epoch)  # Or pass epochs via CDF.varget.
    """

    version = 3
    release = 7
    increment = 0

    month_Token = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

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

    LTS = []
    with open(LEAPSEC_FILE) as lsfile:
        lsreader = csv.reader(lsfile, delimiter=" ")
        for csv_row in lsreader:
            if csv_row[0] == ";":
                continue
            csv_row = list(filter(("").__ne__, csv_row))

            row: List[Union[int, float]] = []
            for r in csv_row[:3]:
                row.append(int(r))
            for r in csv_row[3:6]:
                row.append(float(r))
            LTS.append(row)

    NDAT = len(LTS)

    NST: Optional[List[int]] = None
    currentDay = -1
    currentJDay = -1
    currentLeapSeconds: float = -1

    @staticmethod
    def encode(epochs: epoch_types, iso_8601: bool = True) -> encoded_type:
        """
        Converts one or more epochs into UTC strings. The input epoch
        format is deduced from the argument type.

        Parameters
        ----------
        epochs: int, float, list, complex
            One or more ECD epochs in one of three formats:
            1. CDF_EPOCH: The input should be either a float or list of floats
            (in numpy, a np.float64 or a np.ndarray of np.float64)
            2. CDF_EPOCH16: The input should be either a complex or list of
            complex(in numpy, a np.complex128 or a np.ndarray of np.complex128)
            3. TT2000: The input should be either a int or list of ints
            (in numpy, a np.int64 or a np.ndarray of np.int64)

        iso_8601: bool
                The return time format. If ISO 8601 is True, the format is,
                for example, 2008-02-02T06:08:10.10.012014016, otherwise
                the format is 02-Feb-2008 06:08:10.012.014.016.

        """
        epochs = np.array(epochs)
        if epochs.dtype == np.int64:
            return CDFepoch.encode_tt2000(epochs, iso_8601)
        elif epochs.dtype == np.float64:
            return CDFepoch.encode_epoch(epochs, iso_8601)
        elif epochs.dtype == np.complex128:
            return CDFepoch.encode_epoch16(epochs, iso_8601)
        else:
            raise TypeError(f"Not sure how to handle type {epochs.dtype}")

    @staticmethod
    def breakdown(epochs: epoch_types) -> np.ndarray:
        """
        Returns
        -------
        np.ndarray
            1D if scalar input, 2D otherwise.
        """
        epochs = np.array(epochs)
        if epochs.dtype.type == np.int64:
            return CDFepoch.breakdown_tt2000(epochs)
        elif epochs.dtype.type == np.float64:
            return CDFepoch.breakdown_epoch(epochs)
        elif epochs.dtype.type == np.complex128:
            return CDFepoch.breakdown_epoch16(epochs)
        else:
            raise TypeError("Not sure how to handle type {}".format(type(epochs)))

    @staticmethod
    def _compose_date(
        years: npt.NDArray,
        months: npt.NDArray,
        days: npt.NDArray,
        hours: Optional[npt.NDArray] = None,
        minutes: Optional[npt.NDArray] = None,
        seconds: Optional[npt.NDArray] = None,
        milliseconds: Optional[npt.NDArray] = None,
        microseconds: Optional[npt.NDArray] = None,
        nanoseconds: Optional[npt.NDArray] = None,
    ) -> npt.NDArray[np.datetime64]:
        """
        Take date components and return a numpy datetime array.
        """
        years = np.asarray(years) - 1970
        months = np.asarray(months) - 1
        days = np.asarray(days) - 1
        types = ("<M8[Y]", "<m8[M]", "<m8[D]", "<m8[h]", "<m8[m]", "<m8[s]", "<m8[ms]", "<m8[us]", "<m8[ns]")
        vals = (v for v in (years, months, days, hours, minutes, seconds, milliseconds, microseconds, nanoseconds) if v is not None)

        arrays: List[npt.NDArray[np.datetime64]] = [np.array(v, dtype=t) for t, v in zip(types, vals)]
        return np.array(sum(arrays))

    @classmethod
    def to_datetime(cls, cdf_time: epoch_types) -> npt.NDArray[np.datetime64]:
        """
        Converts CDF epoch argument to numpy.datetime64. This method
        converts a scalar, or array-like. Precision is only kept to the
        nearest microsecond.
        """
        times = cls.breakdown(cdf_time)
        times = np.atleast_2d(times)
        return cls._compose_date(*times.T[:9]).astype("datetime64[us]")

    @staticmethod
    def unixtime(cdf_time: npt.ArrayLike) -> Union[float, npt.NDArray]:
        """
        Converts CDF epoch argument into seconds after 1970-01-01. This method
        converts a scalar, or array-like. Precision is only kept to the
        nearest microsecond.
        """
        cdf_time = np.atleast_1d(cdf_time)
        time_list = np.atleast_2d(CDFepoch.breakdown(cdf_time))

        unixtime = []
        utc = datetime.timezone(datetime.timedelta())
        for t in time_list:
            date: List[int] = [0] * 7
            for i in range(0, len(t)):
                if i > 7:
                    continue
                elif i == 6:
                    date[i] = 1000 * t[i]
                elif i == 7:
                    date[i - 1] += t[i]
                else:
                    date[i] = t[i]
            unixtime.append(
                datetime.datetime(date[0], date[1], date[2], date[3], date[4], date[5], date[6], tzinfo=utc).timestamp()
            )
        return _squeeze_or_scalar_real(unixtime)

    @staticmethod
    def compute(datetimes: npt.ArrayLike) -> Union[float, complex, npt.NDArray]:
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
        """

        if not isinstance(datetimes, (list, tuple, np.ndarray)):
            raise TypeError("datetime must be in list form")

        datetimes = np.atleast_2d(datetimes)
        items = datetimes.shape[1]

        if items == 7:
            return _squeeze_or_scalar_real(CDFepoch.compute_epoch(datetimes))
        elif items == 10:
            return _squeeze_or_scalar_complex(CDFepoch.compute_epoch16(datetimes))
        elif items == 9:
            return _squeeze_or_scalar_real(CDFepoch.compute_tt2000(datetimes))
        else:
            raise TypeError("Unknown input")

    @staticmethod
    def findepochrange(
        epochs: epochs_type, starttime: Optional[epoch_types] = None, endtime: Optional[epoch_types] = None
    ) -> np.ndarray:
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
        epochs = np.array(epochs)
        if epochs.dtype == np.int64:
            return CDFepoch.epochrange_tt2000(epochs, starttime, endtime)
        elif epochs.dtype == np.float64:
            return CDFepoch.epochrange_epoch(epochs, starttime, endtime)
        elif epochs.dtype == np.complex128:
            return CDFepoch.epochrange_epoch16(epochs, starttime, endtime)
        else:
            raise TypeError("Bad input")

    @staticmethod
    def encode_tt2000(tt2000: cdf_tt2000_type, iso_8601: bool = True) -> encoded_type:
        new_tt2000 = np.atleast_1d(tt2000)

        count = len(new_tt2000)
        encodeds = []
        for x in range(count):
            nanoSecSinceJ2000 = new_tt2000[x]
            if nanoSecSinceJ2000 == CDFepoch.FILLED_TT2000_VALUE:
                if iso_8601:
                    return "9999-12-31T23:59:59.999999999"
                else:
                    return "31-Dec-9999 23:59:59.999.999.999"
            if nanoSecSinceJ2000 == CDFepoch.DEFAULT_TT2000_PADVALUE:
                if iso_8601:
                    return "0000-01-01T00:00:00.000000000"
                else:
                    return "01-Jan-0000 00:00:00.000.000.000"
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
            if iso_8601:
                # yyyy-mm-ddThh:mm:ss.mmmuuunnn
                encoded = str(ly).zfill(4)
                encoded += "-"
                encoded += str(lm).zfill(2)
                encoded += "-"
                encoded += str(ld).zfill(2)
                encoded += "T"
                encoded += str(lh).zfill(2)
                encoded += ":"
                encoded += str(ln).zfill(2)
                encoded += ":"
                encoded += str(ls).zfill(2)
                encoded += "."
                encoded += str(ll).zfill(3)
                encoded += str(lu).zfill(3)
                encoded += str(la).zfill(3)
            else:
                # dd-mmm-yyyy hh:mm:ss.mmm.uuu.nnn
                encoded = str(ld).zfill(2)
                encoded += "-"
                encoded += CDFepoch.month_Token[lm - 1]
                encoded += "-"
                encoded += str(ly).zfill(4)
                encoded += " "
                encoded += str(lh).zfill(2)
                encoded += ":"
                encoded += str(ln).zfill(2)
                encoded += ":"
                encoded += str(ls).zfill(2)
                encoded += "."
                encoded += str(ll).zfill(3)
                encoded += "."
                encoded += str(lu).zfill(3)
                encoded += "."
                encoded += str(la).zfill(3)

            if count == 1:
                return encoded
            else:
                encodeds.append(encoded)
        return encodeds

    @staticmethod
    def breakdown_tt2000(tt2000: cdf_tt2000_type) -> np.ndarray:
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
        """
        new_tt2000 = np.atleast_1d(tt2000).astype(np.longlong)
        count = len(new_tt2000)
        toutcs = np.zeros((9, count), dtype=int)
        datxs = CDFepoch._LeapSecondsfromJ2000(new_tt2000)

        # Do some computations on arrays to speed things up
        post2000 = new_tt2000 > 0
        nanoSecsSinceJ2000 = new_tt2000.copy()
        nanoSecsSinceJ2000[~post2000] += CDFepoch.T12hinNanoSecs
        nanoSecsSinceJ2000[~post2000] -= CDFepoch.dTinNanoSecs

        secsSinceJ2000 = (nanoSecsSinceJ2000 / CDFepoch.SECinNanoSecsD).astype(np.longlong)
        nansecs = (nanoSecsSinceJ2000 - secsSinceJ2000 * CDFepoch.SECinNanoSecs).astype(np.longlong)

        posNanoSecs = new_tt2000 > 0
        secsSinceJ2000[posNanoSecs] -= 32
        secsSinceJ2000[posNanoSecs] += 43200
        nansecs[posNanoSecs] -= 184000000

        negNanoSecs = nansecs < 0
        nansecs[negNanoSecs] += CDFepoch.SECinNanoSecs
        secsSinceJ2000[negNanoSecs] -= 1

        t2s = secsSinceJ2000 * CDFepoch.SECinNanoSecs + nansecs

        post72 = datxs[:, 0] > 0
        secsSinceJ2000[post72] -= datxs[post72, 0].astype(int)
        epochs = CDFepoch.J2000Since0AD12hSec + secsSinceJ2000

        datxzero = datxs[:, 1] == 0.0
        epochs[post72 & ~datxzero] -= 1
        xdates = CDFepoch._EPOCHbreakdownTT2000(epochs)

        # If 1 second was subtracted, add 1 second back in
        # Be careful not to go 60 or above
        xdates[5, post72 & ~datxzero] += 1
        xdates[4, post72 & ~datxzero] = np.rint(xdates[5, post72 & ~datxzero] / 60.0)
        xdates[5, post72 & ~datxzero] = xdates[5, post72 & ~datxzero] % 60

        # Set toutcs, then loop through and correct for pre-1972
        toutcs[:6, :] = xdates[:6, :]

        for x in np.nonzero(~post72)[0]:
            if datxs[x, 0] <= 0.0:
                # pre-1972...
                epoch = epochs[x]
                t2 = t2s[x]
                t3 = new_tt2000[x]
                nansec = nansecs[x]

                xdate = np.zeros(9)
                xdate[:6] = xdates[:, x]
                xdate[8] = nansec

                tmpNanosecs = CDFepoch.compute_tt2000(xdate)
                if tmpNanosecs != t3:
                    dat0 = CDFepoch._LeapSecondsfromYMD(xdate[0], xdate[1], xdate[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int(float(tmpx / CDFepoch.SECinNanoSecsD))
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                if nansec < 0:
                    nansec = CDFepoch.SECinNanoSecs + nansec
                    tmpy = tmpy - 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate = np.zeros(9)
                    xdate[:6] = CDFepoch._EPOCHbreakdownTT2000(epoch)[:, 0]
                    xdate[8] = nansec
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate)
                if tmpNanosecs != t3:
                    dat0 = CDFepoch._LeapSecondsfromYMD(xdate[0], xdate[1], xdate[2])
                    tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                    tmpy = int((1.0 * tmpx) / CDFepoch.SECinNanoSecsD)
                    nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                    if nansec < 0:
                        nansec = CDFepoch.SECinNanoSecs + nansec
                        tmpy = tmpy - 1
                    epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                    xdate = np.zeros(9)
                    xdate[:6] = CDFepoch._EPOCHbreakdownTT2000(epoch)[:, 0]
                    xdate[8] = nansec
                    tmpNanosecs = CDFepoch.compute_tt2000(xdate)
                    if tmpNanosecs != t3:
                        dat0 = CDFepoch._LeapSecondsfromYMD(xdate[0], xdate[1], xdate[2])
                        tmpx = t2 - int(dat0 * CDFepoch.SECinNanoSecs)
                        tmpy = int((1.0 * tmpx) / CDFepoch.SECinNanoSecsD)
                        nansec = int(tmpx - tmpy * CDFepoch.SECinNanoSecs)
                        if nansec < 0:
                            nansec = CDFepoch.SECinNanoSecs + nansec
                            tmpy = tmpy - 1
                        epoch = tmpy + CDFepoch.J2000Since0AD12hSec
                        # One more determination
                        xdate = CDFepoch._EPOCHbreakdownTT2000(epoch)
                nansecs[x] = nansec
                toutcs[:6, x] = xdate[:6]

        # Finished pre-1972 correction
        ml1 = nansecs // 1000000
        tmp1 = nansecs - (1000000 * ml1)

        overflow = ml1 > 1000
        ml1[overflow] -= 1000
        toutcs[6, :] = ml1
        toutcs[5, overflow] += 1

        ma1 = tmp1 // 1000
        na1 = tmp1 - 1000 * ma1
        toutcs[7, :] = ma1
        toutcs[8, :] = na1

        return np.squeeze(toutcs.T)

    @staticmethod
    def compute_tt2000(datetimes: npt.ArrayLike) -> Union[int, npt.NDArray[np.int64]]:
        if not isinstance(datetimes, (list, tuple, np.ndarray)):
            raise TypeError("datetime must be in list form")

        new_datetimes = np.atleast_2d(datetimes)
        count = len(new_datetimes)
        nanoSecSinceJ2000s = []
        for x in range(count):
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
            elif items > 7:
                # y m d h m s ms us
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                usec = int(datetime[7])
                nsec = int(1000.0 * (datetime[7] - usec))
            elif items > 6:
                # y m d h m s ms
                day = int(datetime[2])
                hour = int(datetime[3])
                minute = int(datetime[4])
                second = int(datetime[5])
                msec = int(datetime[6])
                xxx = float(1000.0 * (datetime[6] - msec))
                usec = int(xxx)
                nsec = int(1000.0 * (xxx - usec))
            elif items > 5:
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
            elif items > 4:
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
            elif items > 3:
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
            elif items > 2:
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
                raise ValueError("Invalid tt2000 components")

            if month == 0:
                month = 1
            if (
                year == 9999
                and month == 12
                and day == 31
                and hour == 23
                and minute == 59
                and second == 59
                and msec == 999
                and usec == 999
                and nsec == 999
            ):
                nanoSecSinceJ2000 = CDFepoch.FILLED_TT2000_VALUE
            elif (
                year == 0
                and month == 1
                and day == 1
                and hour == 0
                and minute == 0
                and second == 0
                and msec == 0
                and usec == 0
                and nsec == 0
            ):
                nanoSecSinceJ2000 = CDFepoch.DEFAULT_TT2000_PADVALUE
            else:
                iy = 10000000 * month + 10000 * day + year
                if iy != CDFepoch.currentDay:
                    CDFepoch.currentDay = iy
                    CDFepoch.currentLeapSeconds = CDFepoch._LeapSecondsfromYMD(year, month, day)
                    CDFepoch.currentJDay = CDFepoch._JulianDay(year, month, day)
                jd = CDFepoch.currentJDay
                jd = jd - CDFepoch.JulianDateJ2000_12h
                subDayinNanoSecs = int(
                    hour * CDFepoch.HOURinNanoSecs
                    + minute * CDFepoch.MINUTEinNanoSecs
                    + second * CDFepoch.SECinNanoSecs
                    + msec * 1000000
                    + usec * 1000
                    + nsec
                )
                nanoSecSinceJ2000 = int(jd * CDFepoch.DAYinNanoSecs + subDayinNanoSecs)
                t2 = int(CDFepoch.currentLeapSeconds * CDFepoch.SECinNanoSecs)
                if nanoSecSinceJ2000 < 0:
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + CDFepoch.dTinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 - CDFepoch.T12hinNanoSecs)
                else:
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 - CDFepoch.T12hinNanoSecs)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + t2)
                    nanoSecSinceJ2000 = int(nanoSecSinceJ2000 + CDFepoch.dTinNanoSecs)

            nanoSecSinceJ2000s.append(int(nanoSecSinceJ2000))

        return np.squeeze(nanoSecSinceJ2000s)

    @staticmethod
    def _LeapSecondsfromYMD(year: int, month: int, day: int) -> float:
        j = -1
        m = 12 * year + month
        for i, _ in reversed(list(enumerate(CDFepoch.LTS))):
            n = 12 * CDFepoch.LTS[i][0] + CDFepoch.LTS[i][1]
            if m >= n:
                j = i
                break
        if j == -1:
            return 0
        da = CDFepoch.LTS[j][3]
        # pre-1972
        if j < CDFepoch.NERA1:
            jda = CDFepoch._JulianDay(year, month, day)
            da = da + ((jda - CDFepoch.MJDbase) - CDFepoch.LTS[j][4]) * CDFepoch.LTS[j][5]
        return da

    @staticmethod
    def _LeapSecondsfromJ2000(nanosecs: npt.ArrayLike) -> npt.NDArray:
        nanosecs = np.atleast_1d(nanosecs)
        da = np.zeros((nanosecs.size, 2))
        j = -1 * np.ones(nanosecs.size, dtype=int)

        if CDFepoch.NST is None:
            CDFepoch._LoadLeapNanoSecondsTable()
        for i, _ in reversed(list(enumerate(CDFepoch.NST))):
            idxs = (j == -1) & (nanosecs >= CDFepoch.NST[i])
            j[idxs] = i
            if i < (CDFepoch.NDAT - 1):
                overflow = nanosecs + 1000000000 >= CDFepoch.NST[i + 1]
                da[overflow, 1] = 1.0
            if np.all(j > 0):
                break

        LTS = np.array(CDFepoch.LTS)
        da[:, 0] = LTS[j, 3]
        da[j <= CDFepoch.NERA1, 0] = 0
        return da

    @staticmethod
    def _LoadLeapNanoSecondsTable() -> None:
        CDFepoch.NST = []
        for ix in range(0, CDFepoch.NERA1):
            CDFepoch.NST.append(CDFepoch.FILLED_TT2000_VALUE)
        for ix in range(CDFepoch.NERA1, CDFepoch.NDAT):
            CDFepoch.NST.append(
                int(
                    CDFepoch.compute_tt2000(
                        [int(CDFepoch.LTS[ix][0]), int(CDFepoch.LTS[ix][1]), int(CDFepoch.LTS[ix][2]), 0, 0, 0, 0, 0, 0]
                    )
                )
            )

    @staticmethod
    def _EPOCHbreakdownTT2000(epoch: npt.ArrayLike) -> npt.NDArray:
        epoch = np.atleast_1d(epoch)

        minute_AD, second_AD = np.divmod(epoch, 60)
        hour_AD, minute_AD = np.divmod(minute_AD, 60)
        day_AD, hour_AD = np.divmod(hour_AD, 24)
        # minute_AD = second_AD / 60.0
        # hour_AD = minute_AD / 60.0
        # day_AD = hour_AD / 24.0

        l = 1721060 + 68569 + day_AD
        n = (4 * l / 146097).astype(int)
        l = l - ((146097 * n + 3) / 4).astype(int)
        i = (4000 * (l + 1) / 1461001).astype(int)
        l = l - (1461 * i / 4).astype(int) + 31
        j = (80 * l / 2447).astype(int)
        k = l - (2447 * j / 80).astype(int)
        l = (j / 11).astype(int)
        j = j + 2 - 12 * l
        i = 100 * (n - 49) + i + l

        date = np.array([i, j, k, hour_AD, minute_AD, second_AD])
        return date

    @staticmethod
    def epochrange_tt2000(
        epochs: cdf_tt2000_type, starttime: Optional[epoch_types] = None, endtime: Optional[epoch_types] = None
    ) -> npt.NDArray:
        if isinstance(epochs, int) or isinstance(epochs, np.int64):
            pass
        elif isinstance(epochs, list) or isinstance(epochs, tuple) or isinstance(epochs, np.ndarray):
            if isinstance(epochs[0], int) or isinstance(epochs[0], np.int64):
                pass
            else:
                raise ValueError("Bad data")
        else:
            raise ValueError("Bad data")
        stime: Union[int, np.int64]
        if starttime is None:
            stime = int(-9223372036854775807)
        else:
            if isinstance(starttime, int) or isinstance(starttime, np.int64):
                stime = starttime
            elif isinstance(starttime, list):
                stime = int(CDFepoch.compute_tt2000(starttime))
            else:
                raise ValueError("Bad start time")
        if endtime is not None:
            if isinstance(endtime, int) or isinstance(endtime, np.int64):
                etime = endtime
            elif isinstance(endtime, list) or isinstance(endtime, tuple):
                etime = int(CDFepoch.compute_tt2000(endtime))
            else:
                raise ValueError("Bad end time")
        else:
            etime = int(9223372036854775807)
        if stime > etime:
            raise ValueError("Invalid start/end time")
        new_epochs = np.array(epochs)
        return np.where(np.logical_and(new_epochs >= stime, new_epochs <= etime))[0]

    @staticmethod
    def encode_epoch16(epochs: cdf_epoch16_type, iso_8601: bool = True) -> encoded_type:
        new_epochs = np.atleast_1d(epochs)

        count = len(new_epochs)
        encodeds = []
        for x in range(count):
            # complex
            if (new_epochs[x].real == -1.0e31) and (new_epochs[x].imag == -1.0e31):
                if iso_8601:
                    encoded = "9999-12-31T23:59:59.999999999999"
                else:
                    encoded = "31-Dec-9999 23:59:59.999.999.999.999"
            else:
                encoded = CDFepoch._encodex_epoch16(new_epochs[x], iso_8601)
            if count == 1:
                return encoded
            else:
                encodeds.append(encoded)
        return encodeds

    @staticmethod
    def _encodex_epoch16(epoch16: cdf_epoch16_type, iso_8601: bool = True) -> str:
        components = CDFepoch.breakdown_epoch16(epoch16)
        if iso_8601:
            # year-mm-ddThh:mm:ss.mmmuuunnnppp
            encoded = str(components[0]).zfill(4)
            encoded += "-"
            encoded += str(components[1]).zfill(2)
            encoded += "-"
            encoded += str(components[2]).zfill(2)
            encoded += "T"
            encoded += str(components[3]).zfill(2)
            encoded += ":"
            encoded += str(components[4]).zfill(2)
            encoded += ":"
            encoded += str(components[5]).zfill(2)
            encoded += "."
            encoded += str(components[6]).zfill(3)
            encoded += str(components[7]).zfill(3)
            encoded += str(components[8]).zfill(3)
            encoded += str(components[9]).zfill(3)
        else:
            # dd-mmm-year hh:mm:ss.mmm.uuu.nnn.ppp
            encoded = str(components[2]).zfill(2)
            encoded += "-"
            encoded += CDFepoch.month_Token[components[1] - 1]
            encoded += "-"
            encoded += str(components[0]).zfill(4)
            encoded += " "
            encoded += str(components[3]).zfill(2)
            encoded += ":"
            encoded += str(components[4]).zfill(2)
            encoded += ":"
            encoded += str(components[5]).zfill(2)
            encoded += "."
            encoded += str(components[6]).zfill(3)
            encoded += "."
            encoded += str(components[7]).zfill(3)
            encoded += "."
            encoded += str(components[8]).zfill(3)
            encoded += "."
            encoded += str(components[9]).zfill(3)
        return encoded

    @staticmethod
    def _JulianDay(y: int, m: int, d: int) -> int:
        a1 = int(7 * (int(y + int((m + 9) / 12))) / 4)
        a2 = int(3 * (int(int(y + int((m - 9) / 7)) / 100) + 1) / 4)
        a3 = int(275 * m / 9)
        return 367 * y - a1 - a2 + a3 + d + 1721029

    @staticmethod
    def compute_epoch16(datetimes: npt.ArrayLike) -> Union[complex, npt.NDArray[np.complex128]]:
        new_dates = np.atleast_2d(datetimes)
        count = len(new_dates)
        epochs = []
        for x in range(count):
            epoch = []
            date = new_dates[x]
            items = len(date)
            year = date[0]
            month = date[1]
            xxx: Union[float, int] = 0
            if items > 9:
                # y m d h m s ms us ns ps
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                second = int(date[5])
                msec = int(date[6])
                usec = int(date[7])
                nsec = int(date[8])
                psec = int(date[9])
            elif items > 8:
                # y m d h m s ms us ns
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                second = int(date[5])
                msec = int(date[6])
                usec = int(date[7])
                nsec = int(date[8])
                psec = int(1000.0 * (date[8] - nsec))
            elif items > 7:
                # y m d h m s ms us
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                second = int(date[5])
                msec = int(date[6])
                usec = int(date[7])
                xxx = int(1000.0 * (date[7] - usec))
                nsec = int(xxx)
                psec = int(1000.0 * (xxx - nsec))
            elif items > 6:
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
            elif items > 5:
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
            elif items > 4:
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
            elif items > 3:
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
            elif items > 2:
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
                raise ValueError("Invalid epoch16 components")

            if year < 0:
                raise ValueError("Illegal epoch field")

            if (
                year == 9999
                and month == 12
                and day == 31
                and hour == 23
                and minute == 59
                and second == 59
                and msec == 999
                and usec == 999
                and nsec == 999
                and psec == 999
            ):
                epoch.append(-1.0e31)
                epoch.append(-1.0e31)
            elif (
                (year > 9999)
                or (month < 0 or month > 12)
                or (hour < 0 or hour > 23)
                or (minute < 0 or minute > 59)
                or (second < 0 or second > 59)
                or (msec < 0 or msec > 999)
                or (usec < 0 or usec > 999)
                or (nsec < 0 or nsec > 999)
                or (psec < 0 or psec > 999)
            ):
                epoch = CDFepoch._computeEpoch16(year, month, day, hour, minute, second, msec, usec, nsec, psec)
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
                epoch16_1 = float(psec) + float(1000.0 * nsec) + float(1000000.0 * usec) + float(1000000000.0 * msec)
                epoch.append(epoch16_0)
                epoch.append(epoch16_1)
            cepoch = complex(epoch[0], epoch[1])
            epochs.append(cepoch)

        return _squeeze_or_scalar_complex(epochs)

    @staticmethod
    def _calc_from_julian(epoch0: npt.ArrayLike, epoch1: npt.ArrayLike) -> npt.NDArray:
        """Calculate the date and time from epoch input

        Parameters
        ----------
        epoch0 : int, float, array-like
            First element of an epoch array (epoch time in seconds)
        epoch1 : float, array-like
            Second element of an epoch array (epoch time in picoseconds)

        Returns
        -------
        out : array-like
            Array of 10 integers (year, month, day, hour, minute, second,
            millisecond, microsecond, nanosecond, picosecond) if a single value
            is input. For array input, the shape is altered by adding another
            axis of length 10 (holding the same values).

        """
        # Cast input as an array for consistent handling of scalars and lists
        second_ce = np.asarray(epoch0)

        # Determine epoch minutes, hours, and days
        minute_ce = second_ce / 60.0
        hour_ce = minute_ce / 60.0
        day_ce = hour_ce / 24.0

        # Calculate the juian day, using integer rounding
        jd = (1721060 + day_ce).astype(int)
        l = jd + 68569
        n = (4 * l / 146097).astype(int)
        l = l - ((146097 * n + 3) / 4).astype(int)
        i = (4000 * (l + 1) / 1461001).astype(int)
        l += 31 - (1461 * i / 4).astype(int)
        j = (80 * l / 2447).astype(int)
        dy = l - (2447 * j / 80).astype(int)

        # Continue to get month and year
        l = (j / 11).astype(int)
        mo = j + 2 - 12 * l
        yr = 100 * (n - 49) + i + l

        # Finish calculating the epoch hours, minutes, and seconds
        hr = (hour_ce % 24.0).astype(int)
        mn = (minute_ce % 60.0).astype(int)
        sc = (second_ce % 60.0).astype(int)

        # Get the fractional seconds
        msec = np.asarray(epoch1)
        ps = (msec % 1000.0).astype(int)
        msec = msec / 1000.0
        ns = (msec % 1000.0).astype(int)
        msec = msec / 1000.0
        mus = (msec % 1000.0).astype(int)
        msec = msec / 1000.0
        ms = msec.astype(int)

        # Recast the output as integers or lists
        if second_ce.shape == ():
            out = np.array([int(yr), int(mo), int(dy), int(hr), int(mn), int(sc), int(ms), int(mus), int(ns), int(ps)])
        else:
            out = np.array([yr, mo, dy, hr, mn, sc, ms, mus, ns, ps]).transpose()
        return out

    @staticmethod
    def breakdown_epoch16(epochs: cdf_epoch16_type) -> npt.NDArray:
        """
        Calculate date and time from epochs

        Parameters
        ----------
        epochs : array-like
            Single, list, tuple, or np.array of epoch values

        Returns
        -------
        components : ndarray
            List or array of date and time values.  The last axis contains
            (in order): year, month, day, hour, minute, second, millisecond,
            microsecond, nanosecond, and picosecond

        Notes
        -----
        If a bad epoch (-1.0e31 for the real and imaginary components) is
        supplied, a fill date of 9999-12-31 23:59:59 and 999 ms, 999 us,
        999 ns, and 999 ps is returned

        """

        if isinstance(epochs, (complex, np.complex128)) or isinstance(epochs, (list, tuple, np.ndarray)):
            new_epochs = np.asarray(epochs)
            if new_epochs.shape == ():
                cshape = []
                new_epochs = np.array([epochs])
            else:
                cshape = list(new_epochs.shape)
        else:
            raise TypeError("Bad data for epochs: {:}".format(type(epochs)))

        cshape.append(10)
        components = np.full(shape=cshape, fill_value=[9999, 12, 31, 23, 59, 59, 999, 999, 999, 999])
        for i, epoch16 in enumerate(new_epochs):
            # Ignore fill values
            if (epoch16.real != -1.0e31) or (epoch16.imag != -1.0e31):
                esec = -epoch16.real if epoch16.real < 0.0 else epoch16.real
                efra = -epoch16.imag if epoch16.imag < 0.0 else epoch16.imag

                if len(components.shape) == 1:
                    components = CDFepoch._calc_from_julian(esec, efra)
                else:
                    components[i] = CDFepoch._calc_from_julian(esec, efra)

        return components

    @staticmethod
    def _computeEpoch16(y: int, m: int, d: int, h: int, mn: int, s: int, ms: int, msu: int, msn: int, msp: int) -> List[float]:
        if m == 0:
            daysSince0AD = CDFepoch._JulianDay(y, 1, 1) + (d - 1) - 1721060
        else:
            if m < 0:
                y = y - 1
                m = 13 + m
            daysSince0AD = CDFepoch._JulianDay(y, m, d) - 1721060
        if daysSince0AD < 0:
            raise ValueError("Illegal epoch")
        epoch = []
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
            raise ValueError("Illegal epoch")
        else:
            return epoch

    @staticmethod
    def epochrange_epoch16(
        epochs: cdf_epoch16_type, starttime: Optional[epoch_types] = None, endtime: Optional[epoch_types] = None
    ) -> Optional[np.ndarray]:
        new_epochs = np.atleast_1d(epochs)

        stime: Tuple[Union[float, np.float64], Union[float, np.float64]]
        etime: Tuple[Union[float, np.float64], Union[float, np.float64]]

        if starttime is None:
            stime = (-1.0e31, -1.0e31)
        else:
            if isinstance(starttime, complex) or isinstance(starttime, np.complex128):
                stime = (starttime.real, starttime.imag)
            elif isinstance(starttime, list):
                sstime = complex(CDFepoch.compute_epoch16(starttime))
                stime = (sstime.real, sstime.imag)
            else:
                raise ValueError("Bad start time")
        if endtime is not None:
            if isinstance(endtime, complex) or isinstance(endtime, np.complex128):
                etime = (endtime.real, endtime.imag)
            elif isinstance(endtime, list):
                eetime = complex(CDFepoch.compute_epoch16(endtime))
                etime = (eetime.real, eetime.imag)
            else:
                raise ValueError("Bad start time")
        else:
            etime = (1.0e31, 1.0e31)
        if stime[0] > etime[0] or (stime[0] == etime[0] and stime[1] > etime[1]):
            raise ValueError("Invalid start/end time")
        count = len(new_epochs)
        epoch16 = []
        for x in range(0, count):
            epoch16.append(new_epochs[x].real)
            epoch16.append(new_epochs[x].imag)
        count = count * 2
        indx = []
        if epoch16[0] > etime[0] or (epoch16[0] == etime[0] and epoch16[1] > etime[1]):
            return None
        if epoch16[count - 2] < stime[0] or (epoch16[count - 2] == stime[0] and epoch16[count - 1] < stime[1]):
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

    @staticmethod
    def encode_epoch(epochs: cdf_epoch_type, iso_8601: bool = True) -> encoded_type:
        new_epochs = np.atleast_1d(epochs)

        count = len(new_epochs)
        encodeds = []
        for x in range(0, count):
            epoch = new_epochs[x]
            if epoch == -1.0e31:
                if iso_8601:
                    encoded = "9999-12-31T23:59:59.999"
                else:
                    encoded = "31-Dec-9999 23:59:59.999"
            else:
                encoded = CDFepoch._encodex_epoch(epoch, iso_8601)
            if count == 1:
                return encoded
            encodeds.append(encoded)
        return encodeds

    @staticmethod
    def _encodex_epoch(epoch: cdf_epoch_type, iso_8601: bool = True) -> str:
        components = CDFepoch.breakdown_epoch(epoch)
        if iso_8601:
            # year-mm-ddThh:mm:ss.mmm
            encoded = str(components[0]).zfill(4)
            encoded += "-"
            encoded += str(components[1]).zfill(2)
            encoded += "-"
            encoded += str(components[2]).zfill(2)
            encoded += "T"
            encoded += str(components[3]).zfill(2)
            encoded += ":"
            encoded += str(components[4]).zfill(2)
            encoded += ":"
            encoded += str(components[5]).zfill(2)
            encoded += "."
            encoded += str(components[6]).zfill(3)
        else:
            # dd-mmm-year hh:mm:ss.mmm
            encoded = str(components[2]).zfill(2)
            encoded += "-"
            encoded += CDFepoch.month_Token[components[1] - 1]
            encoded += "-"
            encoded += str(components[0]).zfill(4)
            encoded += " "
            encoded += str(components[3]).zfill(2)
            encoded += ":"
            encoded += str(components[4]).zfill(2)
            encoded += ":"
            encoded += str(components[5]).zfill(2)
            encoded += "."
            encoded += str(components[6]).zfill(3)
        return encoded

    @staticmethod
    def compute_epoch(dates: npt.ArrayLike) -> Union[float, npt.NDArray]:
        # TODO Add docstring. What is the output format?

        new_dates = np.atleast_2d(dates)
        count = new_dates.shape[0]

        epochs = []
        for x in range(0, count):
            date = new_dates[x]
            year = date[0]
            month = date[1]
            items = len(date)
            if items > 6:
                # y m d h m s ms
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                second = int(date[5])
                msec = int(date[6])
            elif items > 5:
                # y m d h m s
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                second = int(date[5])
                msec = int(1000.0 * (date[5] - second))
            elif items > 4:
                # y m d h m
                day = int(date[2])
                hour = int(date[3])
                minute = int(date[4])
                xxx = float(60.0 * (date[4] - minute))
                second = int(xxx)
                msec = int(1000.0 * (xxx - second))
            elif items > 3:
                # y m d h
                day = int(date[2])
                hour = int(date[3])
                xxx = float(60.0 * (date[3] - hour))
                minute = int(xxx)
                xxx = float(60.0 * (xxx - minute))
                second = int(xxx)
                msec = int(1000.0 * (xxx - second))
            elif items > 2:
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
                raise ValueError("Invalid epoch components")
            if year == 9999 and month == 12 and day == 31 and hour == 23 and minute == 59 and second == 59 and msec == 999:
                epochs.append(-1.0e31)
            if year < 0:
                raise ValueError("ILLEGAL_EPOCH_FIELD")
            if (
                (year > 9999)
                or (month < 0 or month > 12)
                or (hour < 0 or hour > 23)
                or (minute < 0 or minute > 59)
                or (second < 0 or second > 59)
                or (msec < 0 or msec > 999)
            ):
                epochs.append(CDFepoch._computeEpoch(year, month, day, hour, minute, second, msec))
            if month == 0:
                if day < 1 or day > 366:
                    epochs.append(CDFepoch._computeEpoch(year, month, day, hour, minute, second, msec))
            else:
                if day < 1 or day > 31:
                    epochs.append(CDFepoch._computeEpoch(year, month, day, hour, minute, second, msec))
            if hour == 0 and minute == 0 and second == 0:
                if msec < 0 or msec > 86399999:
                    epochs.append(CDFepoch._computeEpoch(year, month, day, hour, minute, second, msec))

            if month == 0:
                daysSince0AD = CDFepoch._JulianDay(year, 1, 1) + (day - 1) - 1721060
            else:
                daysSince0AD = CDFepoch._JulianDay(year, month, day) - 1721060
            if hour == 0 and minute == 0 and second == 0:
                msecInDay = msec
            else:
                msecInDay = (3600000 * hour) + (60000 * minute) + (1000 * second) + msec
            if count == 1:
                return np.array(86400000.0 * daysSince0AD + msecInDay)
            epochs.append(86400000.0 * daysSince0AD + msecInDay)

        return _squeeze_or_scalar_real(epochs)

    @staticmethod
    def _computeEpoch(y: int, m: int, d: int, h: int, mn: int, s: int, ms: int) -> float:
        if m == 0:
            daysSince0AD = CDFepoch._JulianDay(y, 1, 1) + (d - 1) - 1721060
        else:
            if m < 0:
                --y
                m = 13 + m
            daysSince0AD = CDFepoch._JulianDay(y, m, d) - 1721060
        if daysSince0AD < 1:
            raise ValueError("ILLEGAL_EPOCH_FIELD")
        msecInDay = float(3600000.0 * h + 60000.0 * mn + 1000.0 * s) + float(ms)
        msecFromEpoch = float(86400000.0 * daysSince0AD + msecInDay)
        if msecFromEpoch < 0.0:
            return -1.0
        else:
            return msecFromEpoch

    @staticmethod
    def breakdown_epoch(epochs: cdf_epoch_type) -> np.ndarray:
        """Calculate date and time from epochs

        Parameters
        ----------
        epochs : int, float, or array-like
            Single, list, tuple, or np.array of epoch values

        Returns
        -------
        components : list
            List or array of date and time values.  The last axis contains
            (in order): year, month, day, hour, minute, second, and millisecond

        Notes
        -----
        If a bad epoch (-1.0e31) is supplied, a fill date of
        9999-12-31 23:59:59 and 999 ms is returned.

        """
        # Test input and cast it as an array of floats
        if (
            isinstance(epochs, float)
            or isinstance(epochs, np.float64)
            or isinstance(epochs, list)
            or isinstance(epochs, tuple)
            or isinstance(epochs, np.ndarray)
            or isinstance(epochs, int)
        ):
            new_epochs = np.asarray(epochs).astype(float)
            if new_epochs.shape == ():
                cshape = []
                new_epochs = np.array([epochs], dtype=float)
            else:
                cshape = list(new_epochs.shape)
        else:
            raise TypeError("Bad data for epochs: {:}".format(type(epochs)))

        # Initialize output to default values
        cshape.append(7)
        components = np.full(shape=cshape, fill_value=[9999, 12, 31, 23, 59, 59, 999])
        for i, epoch in enumerate(new_epochs):
            # Ignore fill values
            if epoch != -1.0e31:
                esec = -epoch / 1000.0 if epoch < 0.0 else epoch / 1000.0
                date_time = CDFepoch._calc_from_julian(esec, 0.0)

                ms = (epoch % 1000.0).astype(int)
                date_time[..., 6] = int(ms) if ms.shape == () else ms

                if len(components.shape) == 1:
                    components = date_time[..., :7]
                else:
                    components[i] = date_time[..., :7]

        return np.squeeze(components)

    @staticmethod
    def epochrange_epoch(
        epochs: epoch_types, starttime: Optional[epoch_types] = None, endtime: Optional[epoch_types] = None
    ) -> np.ndarray:
        if isinstance(epochs, (float, np.float64)):
            pass
        elif isinstance(epochs, (list, tuple, np.ndarray)):
            if isinstance(epochs[0], (float, np.float64)):
                pass
            else:
                raise TypeError("Bad data")
        else:
            raise TypeError("Bad data")

        stime: Union[float, np.float64]
        if starttime is None:
            stime = 0.0
        else:
            if isinstance(starttime, (float, int, np.float64)):
                stime = starttime
            elif isinstance(starttime, (list, tuple)):
                stime = float(CDFepoch.compute_epoch(starttime))
            else:
                raise TypeError("Bad start time")

        if endtime is not None:
            if isinstance(endtime, (float, int, np.float64)):
                etime = endtime
            elif isinstance(endtime, (list, tuple)):
                etime = float(CDFepoch.compute_epoch(endtime))
            else:
                raise TypeError("Bad end time")
        else:
            etime = 1.0e31
        if stime > etime:
            raise ValueError("Invalid start/end time")

        new_epochs = np.array(epochs)
        return np.where(np.logical_and(new_epochs >= stime, new_epochs <= etime))[0]

    @staticmethod
    def parse(value: Union[str, Tuple[str, ...], List[str]]) -> np.ndarray:
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
        """
        if isinstance(value, (list, tuple)) and not isinstance(value[0], str):
            raise TypeError("should be a string or a list of string")

        elif not isinstance(value, (list, tuple, str)):
            raise TypeError("Invalid value... should be a string or a list of string")
        else:
            if isinstance(value, (list, tuple)):
                num = len(value)
                epochs = []
                for x in range(num):
                    epochs.append(CDFepoch._parse_epoch(value[x]))
                return np.squeeze(epochs)
            else:
                return np.squeeze(CDFepoch._parse_epoch(value))

    @staticmethod
    def _parse_epoch(value: str) -> Union[int, float, complex]:
        if len(value) in (23, 24):
            # CDF_EPOCH
            if value.lower() in ("31-dec-9999 23:59:59.999", "9999-12-31t23:59:59.999"):
                return -1.0e31
            else:
                if len(value) == 24:
                    date = re.findall(r"(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)", value)
                    dd = int(date[0][0])
                    mm = CDFepoch._month_index(date[0][1])
                    yy = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    ms = int(date[0][6])
                else:
                    date = re.findall(r"(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)", value)
                    yy = int(date[0][0])
                    mm = int(date[0][1])
                    dd = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    ms = int(date[0][6])
                return float(CDFepoch.compute_epoch([yy, mm, dd, hh, mn, ss, ms]))
        elif len(value) == 36 or (len(value) == 32 and value[10].lower() == "t"):
            # CDF_EPOCH16
            if value.lower() in ("31-dec-9999 23:59:59.999.999.999.999", "9999-12-31t23:59:59.999999999999"):
                return -1.0e31 - 1.0e31j
            else:
                if len(value) == 36:
                    date = re.findall(r"(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)", value)
                    dd = int(date[0][0])
                    mm = CDFepoch._month_index(date[0][1])
                    yy = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    ms = int(date[0][6])
                    us = int(date[0][7])
                    ns = int(date[0][8])
                    ps = int(date[0][9])
                else:
                    date = re.findall(r"(\d+)\-(\d+)\-(\d+)T(\d+)\:(\d+)\:(\d+)\.(\d+)", value)
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
                return complex(CDFepoch.compute_epoch16([yy, mm, dd, hh, mn, ss, ms, us, ns, ps]))
        elif len(value) == 29 or (len(value) == 32 and value[11] == " "):
            # CDF_TIME_TT2000
            value = value.lower()
            if value == "9999-12-31t23:59:59.999999999" or value == "31-dec-9999 23:59:59.999.999.999":
                return -9223372036854775808
            elif value == "0000-01-01t00:00.000000000" or value == "01-jan-0000 00:00.000.000.000":
                return -9223372036854775807
            else:
                if len(value) == 29:
                    date = re.findall(r"(\d+)\-(\d+)\-(\d+)t(\d+)\:(\d+)\:(\d+)\.(\d+)", value)
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
                    date = re.findall(r"(\d+)\-(.+)\-(\d+) (\d+)\:(\d+)\:(\d+)\.(\d+)\.(\d+)\.(\d+)", value)
                    dd = int(date[0][0])
                    mm = CDFepoch._month_index(date[0][1])
                    yy = int(date[0][2])
                    hh = int(date[0][3])
                    mn = int(date[0][4])
                    ss = int(date[0][5])
                    ms = int(date[0][6])
                    us = int(date[0][7])
                    ns = int(date[0][8])
                return int(CDFepoch.compute_tt2000([yy, mm, dd, hh, mn, ss, ms, us, ns]))
        else:
            raise ValueError("Invalid cdf epoch type...")

    @staticmethod
    def _month_index(month: str) -> int:
        if month.lower() == "jan":
            return 1
        elif month.lower() == "feb":
            return 2
        elif month.lower() == "mar":
            return 3
        elif month.lower() == "apr":
            return 4
        elif month.lower() == "may":
            return 5
        elif month.lower() == "jun":
            return 6
        elif month.lower() == "jul":
            return 7
        elif month.lower() == "aug":
            return 8
        elif month.lower() == "sep":
            return 9
        elif month.lower() == "oct":
            return 10
        elif month.lower() == "nov":
            return 11
        elif month.lower() == "dec":
            return 12
        else:
            return -1
