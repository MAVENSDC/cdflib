"""
##################
CDF Astropy Epochs
##################

@author: Bryan Harter
"""
import numpy as np
from typing import Sequence, List, Union
import datetime
from datetime import timezone
from astropy.time import Time, TimeFormat
from astropy.time.formats import erfa, TimeFromEpoch


class CDFEpoch(TimeFromEpoch):
    name = 'cdf_epoch'
    unit = 1.0 / (erfa.DAYSEC * 1000) # Milliseconds
    epoch_val = '0000-01-01 00:00:00'
    epoch_val2 = None
    epoch_scale = 'utc'
    epoch_format = 'iso'

class CDFEpoch16(TimeFromEpoch):
    name = 'cdf_epoch16'
    unit = 1.0 / (erfa.DAYSEC) # Seconds
    epoch_val = '0000-01-01 00:00:00'
    epoch_val2 = None
    epoch_scale = 'utc'
    epoch_format = 'iso'

class CDFTT2000(TimeFromEpoch):
    name = 'cdf_tt2000'
    unit = 1.0 / (erfa.DAYSEC * 1000 * 1000 * 1000) #Nanoseconds
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
    def convert_to_astropy(epochs):  # @NoSelf
        if isinstance(epochs, (int, np.int64)):
            return Time(epochs, format='cdf_tt2000', precision=9)
        elif isinstance(epochs, (float, np.float64)):
            return Time(epochs, format='cdf_epoch', precision=9)
        elif isinstance(epochs, (complex, np.complex128)):
            return Time(epochs.real, epochs.imag/1000000000000.0, format='cdf_epoch16', precision=9)
        elif isinstance(epochs, (list, np.ndarray)):
            if isinstance(epochs[0], (int, np.int64)):
                return Time(epochs, format='cdf_tt2000', precision=9)
            elif isinstance(epochs[0], (float, np.float64)):
                return Time(epochs, format='cdf_epoch', precision=9)
            elif isinstance(epochs[0], (complex, np.complex128)):
                return Time(epochs.real, epochs.imag/1000000000000.0, format='cdf_epoch16', precision=9)
        elif isinstance(epochs, TimeFromEpoch):
            return epochs

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
        #Returns either a single array, or a array of arrays depending on the input
        epochs = CDFAstropy.convert_to_astropy(epochs)
        if epochs.format=='cdf_tt2000':
            return CDFAstropy.breakdown_tt2000(epochs, to_np)
        elif epochs.format=='cdf_epoch':
            return CDFAstropy.breakdown_epoch(epochs, to_np)
        elif epochs.format=='cdf_epoch16':
            return CDFAstropy.breakdown_epoch16(epochs, to_np)
        raise TypeError('Not sure how to handle type {}'.format(type(epochs)))


    def to_datetime(self, cdf_time) -> List[datetime.datetime]:
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
                remainder_seconds = (d[6]/1000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_epoch)
            if len(d) == 9:
                remainder_seconds = (d[6]/1000.0) + (d[7]/1000000.0) + (d[8]/1000000000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_tt2000)
            if len(d) == 10:
                remainder_seconds = (d[6]/1000.0) + (d[7]/1000000.0) + (d[8]/1000000000.0) + (d[9]/1000000000000.0)
                astrotime = Time(unix_seconds, remainder_seconds, format='unix', precision=9)
                cdf_time.append(astrotime.cdf_epoch16)
        if to_np:
            return np.array(cdf_time)
        else:
            return cdf_time

    def findepochrange(epochs, starttime=None, endtime=None):  # @NoSelf
        if isinstance(starttime, list):
            start = CDFAstropy.compute(starttime)
        if isinstance(endtime, list):
            end = CDFAstropy.compute(endtime)

        epochs = CDFAstropy.convert_to_astropy(epochs)

        epochs_as_np = epochs.value
        epochs_range = (epochs_as_np > start) * (epochs_as_np < end)
        indices = epochs_as_np.where(epochs_range)
        return min(indices), max(indices)

    @staticmethod
    def breakdown_tt2000(tt2000, to_np: bool = False):
        tt2000strings = tt2000.iso
        if not isinstance(tt2000strings, list):
            tt2000strings = [tt2000strings]
        times = []
        for t in tt2000strings:
            time_as_list = []
            time_as_list.append(int(t[0:4]))  # year
            time_as_list.append(int(t[5:7]))  # month
            time_as_list.append(int(t[8:10]))  # day
            time_as_list.append(int(t[11:13]))  # hour
            time_as_list.append(int(t[14:16]))  # minute
            time_as_list.append(int(t[17:19]))  # second
            decimal_seconds = float(t[19:])
            milliseconds = decimal_seconds*1000
            time_as_list.append(int(milliseconds)) # milliseconds
            microseconds = (milliseconds % 1) * 1000
            time_as_list.append(int(microseconds)) # microseconds
            nanoseconds = (microseconds % 1) * 1000
            time_as_list.append(int(nanoseconds))  # microseconds
            times.append(time_as_list)

        return times

    @staticmethod
    def breakdown_epoch16(epochs, to_np: bool = False):  # @NoSelf
        epoch16strings = epochs.iso
        if not isinstance(epoch16strings, list):
            epoch16strings = [epoch16strings]
        times = []
        for t in epoch16strings:
            time_as_list = []
            time_as_list.append(int(t[0:4]))  # year
            time_as_list.append(int(t[5:7]))  # month
            time_as_list.append(int(t[8:10]))  # day
            time_as_list.append(int(t[11:13]))  # hour
            time_as_list.append(int(t[14:16]))  # minute
            time_as_list.append(int(t[17:19]))  # second
            decimal_seconds = float(t[19:])
            milliseconds = decimal_seconds*1000
            time_as_list.append(int(milliseconds)) # milliseconds
            microseconds = (milliseconds % 1) * 1000
            time_as_list.append(int(microseconds)) # microseconds
            nanoseconds = (microseconds % 1) * 1000
            time_as_list.append(int(nanoseconds))  # nanoseconds
            picoseconds = (nanoseconds % 1) * 1000
            time_as_list.append(int(picoseconds))  # picoseconds
            times.append(time_as_list)

        return times

    @staticmethod
    def breakdown_epoch(epochs, to_np: bool = False):  # @NoSelf
        epochstrings = epochs.iso
        if not isinstance(epochstrings, list):
            epochstrings = [epochstrings]
        times = []
        for t in epochstrings:
            time_as_list = []
            time_as_list.append(int(t[0:4]))  # year
            time_as_list.append(int(t[5:7]))  # month
            time_as_list.append(int(t[8:10]))  # day
            time_as_list.append(int(t[11:13]))  # hour
            time_as_list.append(int(t[14:16]))  # minute
            time_as_list.append(int(t[17:19]))  # second
            decimal_seconds = float(t[19:])
            milliseconds = decimal_seconds*1000
            time_as_list.append(int(milliseconds)) # milliseconds
            times.append(time_as_list)
        return times

    @staticmethod
    def parse(value, to_np: bool = False):  # @NoSelf
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
        if not isinstance(value, list):
            value = [value]

        time_list = []

        # Determine the input format
        if len(value[0].split("-")[0]) == 2:
            time_format = '%d-%b-Y %H:%M:%S'
        else:
            time_format = '%d-%b-Y %H:%M:%S'

        # Set precision
        if len(value[0] == 24):
            p = 9
        else:
            p = 9

        for t in value:
            sec = datetime.strptime(t[0:20].lower(), strftime=time_format).replace(tzinfo=timezone.utc).timestamp()
            subs = t[20:].replace(".", "")
            if len(subs) == 3:
                time_list.append(Time(sec, float(subs), format='unix', precision=p).cdf_epoch)
            if len(subs) == 12:
                time_list.append(Time(sec, float(subs), format='unix', precision=p).cdf_epoch16)
            if len(subs) == 9:
                time_list.append(Time(sec, float(subs), format='unix', precision=p).cdf_epoch16)

        times = np.array(time_list)
        if not to_np:
            return times.tolist()
        else:
            return times

    def getVersion():  # @NoSelf
        """
        Prints the code version.
        """
        print('epochs version:', str(CDFAstropy.version) + '.' +
              str(CDFAstropy.release) + '.'+str(CDFAstropy.increment))
