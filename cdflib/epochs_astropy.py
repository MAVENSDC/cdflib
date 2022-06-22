"""
##################
CDF Astropy Epochs
##################

@author: Bryan Harter
"""
import datetime
from datetime import timezone
from typing import List

import numpy as np
from astropy.time import Time
from astropy.time.formats import TimeFromEpoch, erfa

__all__ = ['CDFAstropy']


class CDFEpoch(TimeFromEpoch):
    name = 'cdf_epoch'
    unit = 1.0 / (erfa.DAYSEC * 1000)  # Milliseconds
    epoch_val = '0000-01-01 00:00:00'
    epoch_val2 = None
    epoch_scale = 'utc'
    epoch_format = 'iso'


class CDFEpoch16(TimeFromEpoch):
    name = 'cdf_epoch16'
    unit = 1.0 / (erfa.DAYSEC)  # Seconds
    epoch_val = '0000-01-01 00:00:00'
    epoch_val2 = None
    epoch_scale = 'utc'
    epoch_format = 'iso'


class CDFTT2000(TimeFromEpoch):
    name = 'cdf_tt2000'
    unit = 1.0 / (erfa.DAYSEC * 1e9)  # Nanoseconds
    epoch_val = '2000-01-01 12:00:00'
    epoch_val2 = None
    epoch_scale = 'tt'
    epoch_format = 'iso'


class CDFAstropy:
    """
    Class to encapsulate astropy time routines with CDF class.
    """

    version = 3
    release = 7
    increment = 0

    @staticmethod
    def convert_to_astropy(epochs, format=None):
        """
        Convert CDF epochs to astropy time objects.

        Returns
        -------
        astropy.time.Time
        """
        # If already in Astropy time Units, do nothing
        if isinstance(epochs, Time):
            return epochs

        # If format is specified, then force it to do that
        if format is not None:
            return Time(epochs, format=format, precision=9)

        if isinstance(epochs, (list, np.ndarray)):
            t = type(epochs[0])
        else:
            t = type(epochs)

        # Determine best format for the input type
        if t in (int, np.int64):
            return Time(epochs, format='cdf_tt2000', precision=9)
        elif t in (complex, np.complex128):
            return Time(epochs.real, epochs.imag / 1000000000000.0, format='cdf_epoch16', precision=9)
        elif t in (float, np.float64):
            return Time(epochs, format='cdf_epoch', precision=9)
        else:
            raise TypeError('Not sure how to handle type {}'.format(type(epochs)))

    @staticmethod
    def encode(epochs, iso_8601: bool = True):  # @NoSelf
        epochs = CDFAstropy.convert_to_astropy(epochs)
        if iso_8601:
            return epochs.iso
        else:
            return epochs.strftime('%d-%b-%Y %H:%M:%S.%f')

    @staticmethod
    def breakdown(epochs, to_np: bool = False):
        # Returns either a single array, or a array of arrays depending on the input
        epochs = CDFAstropy.convert_to_astropy(epochs)
        if epochs.format == 'cdf_tt2000':
            return CDFAstropy.breakdown_tt2000(epochs, to_np)
        elif epochs.format == 'cdf_epoch':
            return CDFAstropy.breakdown_epoch(epochs, to_np)
        elif epochs.format == 'cdf_epoch16':
            return CDFAstropy.breakdown_epoch16(epochs, to_np)
        raise TypeError('Not sure how to handle type {}'.format(type(epochs)))

    @staticmethod
    def to_datetime(cdf_time) -> List[datetime.datetime]:
        cdf_time = CDFAstropy.convert_to_astropy(cdf_time)
        return cdf_time.datetime

    @staticmethod
    def unixtime(cdf_time, to_np: bool = False):  # @NoSelf
        """
        Encodes the epoch(s) into seconds after 1970-01-01.  Precision is only
        kept to the nearest microsecond.

        If to_np is True, then the values will be returned in a numpy array.
        """
        epochs = CDFAstropy.convert_to_astropy(cdf_time)
        if to_np:
            return epochs.unix
        else:
            return epochs.unix.tolist()

    @staticmethod
    def compute(datetimes, to_np: bool = False):  # @NoSelf
        if not isinstance(datetimes[0], list):
            datetimes = [datetimes]
        cdf_time = []
        for d in datetimes:
            unix_seconds = datetime.datetime(d[0], d[1], d[2], d[3], d[4], d[5]).replace(tzinfo=timezone.utc).timestamp()
            if len(d) == 7:
                remainder_seconds = (d[6] / 1000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_epoch)
            if len(d) == 9:
                remainder_seconds = (d[6] / 1000.0) + (d[7] / 1000000.0) + (d[8] / 1000000000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_tt2000)
            if len(d) == 10:
                remainder_seconds = (d[6] / 1000.0) + (d[7] / 1000000.0) + (d[8] / 1000000000.0) + (d[9] / 1000000000000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_epoch16)
        if to_np:
            return np.array(cdf_time)
        else:
            return cdf_time

    @staticmethod
    def findepochrange(epochs, starttime=None, endtime=None):  # @NoSelf
        if isinstance(starttime, list):
            start = CDFAstropy.compute(starttime)
        if isinstance(endtime, list):
            end = CDFAstropy.compute(endtime)

        epochs = CDFAstropy.convert_to_astropy(epochs)

        epochs_as_np = epochs.value
        indices = np.where((epochs_as_np >= start) & (epochs_as_np <= end))
        return min(indices[0]), max(indices[0])

    @staticmethod
    def breakdown_tt2000(tt2000, to_np: bool = False):
        tt2000strings = tt2000.iso
        if not isinstance(tt2000strings, (list, np.ndarray)):
            tt2000strings = [tt2000strings]
        times = []
        for t in tt2000strings:
            date, time = t.split(" ")
            yyyy, mon, dd = date.split("-")
            hhmmss, decimal_seconds = time.split(".")
            decimal_seconds = "." + decimal_seconds
            hh, mm, ss = hhmmss.split(":")
            time_as_list = []
            time_as_list.append(int(yyyy))  # year
            time_as_list.append(int(mon))  # month
            time_as_list.append(int(dd))  # day
            time_as_list.append(int(hh))  # hour
            time_as_list.append(int(mm))  # minute
            time_as_list.append(int(ss))  # second
            decimal_seconds = float(decimal_seconds)
            milliseconds = decimal_seconds * 1000
            time_as_list.append(int(milliseconds))  # milliseconds
            microseconds = (milliseconds % 1) * 1000
            time_as_list.append(int(microseconds))  # microseconds
            nanoseconds = (microseconds % 1) * 1000
            time_as_list.append(int(nanoseconds))  # microseconds
            times.append(time_as_list)

        return times

    @staticmethod
    def breakdown_epoch16(epochs, to_np: bool = False):  # @NoSelf
        epoch16strings = epochs.iso
        if not isinstance(epoch16strings, (list, np.ndarray)):
            epoch16strings = [epoch16strings]
        times = []
        for t in epoch16strings:
            time_as_list: List[int] = []
            date, time = t.split(" ")
            yyyy, mon, dd = date.split("-")
            hhmmss, decimal_seconds = time.split(".")
            decimal_seconds = "." + decimal_seconds
            hh, mm, ss = hhmmss.split(":")
            time_as_list = []
            time_as_list.append(int(yyyy))  # year
            time_as_list.append(int(mon))  # month
            time_as_list.append(int(dd))  # day
            time_as_list.append(int(hh))  # hour
            time_as_list.append(int(mm))  # minute
            time_as_list.append(int(ss))  # second
            decimal_seconds = float(decimal_seconds)
            milliseconds = decimal_seconds * 1000
            time_as_list.append(int(milliseconds))  # milliseconds
            microseconds = (milliseconds % 1) * 1000
            time_as_list.append(int(microseconds))  # microseconds
            nanoseconds = (microseconds % 1) * 1000
            time_as_list.append(int(nanoseconds))  # nanoseconds
            picoseconds = (nanoseconds % 1) * 1000
            time_as_list.append(int(picoseconds))  # picoseconds
            times.append(time_as_list)

        return times

    @staticmethod
    def breakdown_epoch(epochs, to_np: bool = False):  # @NoSelf
        epochstrings = epochs.iso
        if not isinstance(epochstrings, (list, np.ndarray)):
            epochstrings = [epochstrings]
        times = []
        for t in epochstrings:
            date, time = t.split(" ")
            yyyy, mon, dd = date.split("-")
            hhmmss, decimal_seconds = time.split(".")
            decimal_seconds = "." + decimal_seconds
            hh, mm, ss = hhmmss.split(":")
            time_as_list = []
            time_as_list.append(int(yyyy))  # year
            time_as_list.append(int(mon))  # month
            time_as_list.append(int(dd))  # day
            time_as_list.append(int(hh))  # hour
            time_as_list.append(int(mm))  # minute
            time_as_list.append(int(ss))  # second
            decimal_seconds = float(decimal_seconds)
            milliseconds = decimal_seconds * 1000
            time_as_list.append(int(milliseconds))  # milliseconds
            times.append(time_as_list)
        return times

    @staticmethod
    def parse(value, to_np: bool = False):  # @NoSelf
        """
        Parses the provided date/time string(s) into CDF epoch value(s).

        For CDF_EPOCH:
                'yyyy-mm-dd hh:mm:ss.xxx' (in iso_8601). The string is the output
                from encode function.

        For CDF_EPOCH16:
                The string has to be in the form of
                'yyyy-mm-dd hh:mm:ss.mmmuuunnnppp' (in iso_8601). The string is
                the output from encode function.

        For TT2000:
                The string has to be in the form of
                'yyyy-mm-dd hh:mm:ss.mmmuuunnn' (in iso_8601). The string is
                the output from encode function.

        Specify to_np to True, if the result should be in numpy class.
        """
        if not isinstance(value, (list, np.ndarray)):
            value = [value]

        time_list = []

        for t in value:
            date, subs = t.split(".")
            if len(subs) == 3:
                time_list.append(Time(t, precision=9).cdf_epoch)
            if len(subs) == 12:
                time_list.append(Time(t, precision=9).cdf_epoch16)
            if len(subs) == 9:
                time_list.append(int(Time(t, precision=9).cdf_tt2000))

        if not to_np:
            return time_list
        else:
            return np.array(time_list)
