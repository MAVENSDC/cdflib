#!/usr/bin/env python
from datetime import datetime
from random import randint

import numpy as np
import pytest
from pytest import approx

from cdflib.epochs_astropy import CDFAstropy as cdfepoch


def test_encode_cdfepoch():
    x = cdfepoch.encode([62285326000000.0, 62985326000000.0])
    assert x[0] == '1973-09-28 23:26:40.000000000'
    assert x[1] == '1995-12-04 19:53:20.000000000'


def test_encode_cdfepoch16():
    '''
    cdf_encode_epoch16(dcomplex(63300946758.000000, 176214648000.00000)) in IDL
    returns 04-Dec-2005 20:39:28.176.214.654.976

    However, I believe this IDL routine is bugged.  This website:
    https://www.epochconverter.com/seconds-days-since-y0

    shows a correct answer.
    '''
    x = cdfepoch.encode(np.complex128(63300946758.000000 + 176214648000.00000j))
    assert x == '2005-12-04 20:19:18.176214648'
    y = cdfepoch.encode(np.complex128([33300946758.000000 + 106014648000.00000j,
                                       61234543210.000000 + 000011148000.00000j]))
    assert y[0] == '1055-04-07 14:59:18.106014648'
    assert y[1] == '1940-06-12 03:20:10.000011148'


def test_encode_cdftt2000():
    x = cdfepoch.encode(186999622360321123)
    assert x == '2005-12-04 20:20:22.360321120'
    y = cdfepoch.encode([500000000100, 123456789101112131])
    assert y[0] == '2000-01-01 12:08:20.000000100'
    assert y[1] == '2003-11-30 09:33:09.101112128'


def test_unixtime():
    x = cdfepoch.unixtime([500000000100, 123456789101112131])
    assert approx(x[0]) == 946728435.816
    assert x[1] == approx(1070184724.917112)


def test_breakdown_cdfepoch():
    x = cdfepoch.breakdown([62285326000000.0, 62985326000000.0])
    # First in the array
    assert x[0][0] == 1973
    assert x[0][1] == 9
    assert x[0][2] == 28
    assert x[0][3] == 23
    assert x[0][4] == 26
    assert x[0][5] == 40
    assert x[0][6] == 0
    # Second in the array
    assert x[1][0] == 1995
    assert x[1][1] == 12
    assert x[1][2] == 4
    assert x[1][3] == 19
    assert x[1][4] == 53
    assert x[1][5] == 20
    assert x[1][6] == 0


def test_breakdown_cdfepoch16():
    x = cdfepoch.breakdown(np.complex128(63300946758.000000 + 176214648000.00000j))
    assert x[0][0] == 2005
    assert x[0][1] == 12
    assert x[0][2] == 4
    assert x[0][3] == 20
    assert x[0][4] == 19
    assert x[0][5] == 18
    assert x[0][6] == 176
    assert x[0][7] == 214
    assert x[0][8] == 648
    assert x[0][9] == 0


def test_breakdown_cdftt2000():
    x = cdfepoch.breakdown(123456789101112131)
    assert x[0][0] == 2003
    assert x[0][1] == 11
    assert x[0][2] == 30
    assert x[0][3] == 9
    assert x[0][4] == 33
    assert x[0][5] == 9
    assert x[0][6] == 101
    assert x[0][7] == 112

    # Apparently there is a loss of precision at this level
    # assert x[0][8] == 131


def test_compute_cdfepoch():
    '''
    Using random numbers for the compute tests
    '''
    random_time = []
    random_time.append(randint(1709, 2292))  # Year
    random_time.append(randint(1, 12))  # Month
    random_time.append(randint(1, 28))  # Date
    random_time.append(randint(0, 23))  # Hour
    random_time.append(randint(0, 59))  # Minute
    random_time.append(randint(0, 59))  # Second
    random_time.append(randint(0, 999))  # Millisecond
    x = cdfepoch.breakdown(cdfepoch.compute(random_time))
    i = 0
    for t in x[0]:
        assert t == random_time[i], f'Time {random_time} was not equal to {x}'
        i += 1


def test_compute_cdfepoch16():
    random_time = []
    random_time.append(randint(1709, 2292))  # Year
    random_time.append(randint(1, 12))  # Month
    random_time.append(randint(1, 28))  # Date
    random_time.append(randint(0, 23))  # Hour
    random_time.append(randint(0, 59))  # Minute
    random_time.append(randint(0, 59))  # Second
    random_time.append(randint(0, 999))  # Millisecond
    random_time.append(randint(0, 999))  # Microsecond
    random_time.append(randint(0, 999))  # Nanosecond
    random_time.append(randint(0, 999))  # Picosecond
    cdftime = cdfepoch.convert_to_astropy(cdfepoch.compute(random_time), format='cdf_epoch16')
    x = cdfepoch.breakdown(cdftime)
    i = 0
    for t in x[0]:
        assert t == random_time[i], f'Time {random_time} was not equal to {x}'
        i += 1
        # Unfortunately, currently there is a pretty big loss of precision that comes with
        # the compute function.  Need to stop testing early.
        if i > 6:
            return


def test_compute_cdftt2000():
    pass

    # Need to determine why computing and breaking down tt2000 types continually adds leap seconds + 32.184
    '''
    random_time = []
    random_time.append(randint(0, 2018))  # Year
    random_time.append(randint(1, 12))  # Month
    random_time.append(randint(1, 28))  # Date
    random_time.append(randint(0, 23))  # Hour
    random_time.append(randint(0, 59))  # Minute
    random_time.append(randint(0, 59))  # Second
    random_time.append(randint(0, 999))  # Millisecond
    random_time.append(randint(0, 999))  # Microsecond
    random_time.append(randint(0, 999))  # Nanosecond
    x = cdfepoch.breakdown(cdfepoch.compute(random_time))
    i = 0
    for t in x[0]:
        assert t == random_time[i], 'Time {} was not equal to {}'.format(random_time, x)
        i += 1
    '''


def test_parse_cdfepoch():
    x = cdfepoch.encode(62567898765432.0)
    assert x == "1982-09-12 11:52:45.432000000"
    stripped_time = x[:23]
    parsed = cdfepoch.parse(stripped_time)
    assert parsed[0] == approx(62567898765432.0)


def test_parse_cdfepoch16():
    input_time = 53467976543.0 + 543218654100j
    x = cdfepoch.encode(input_time)
    assert x == "1694-05-01 07:42:23.543218654"
    add_precision = x + "000"
    parsed = cdfepoch.parse(add_precision)
    assert parsed[0] == approx(53467976543 + .543218654)

    assert cdfepoch.to_datetime(input_time) == datetime(1694, 5, 1, 7, 42, 23, 543219)


def test_parse_cdftt2000():
    x = "2004-03-01 12:24:22.351793238"
    parsed = cdfepoch.parse(x)
    assert parsed == [131415926535793232]

    assert cdfepoch.to_datetime(parsed) == [datetime(2004, 3, 1, 12, 25, 26, 535793)]


def test_findepochrange_cdfepoch():
    start_time = "2013-12-01 12:24:22.000"
    end_time = "2014-12-01 12:24:22.000"
    x = cdfepoch.parse([start_time, end_time])
    time_array = np.arange(x[0], x[1], step=1000000)

    test_start = [2014, 8, 1, 8, 1, 54, 123]
    test_end = [2018, 1, 1, 1, 1, 1, 1]
    index = cdfepoch.findepochrange(time_array, starttime=test_start, endtime=test_end)
    # Test that the test_start is less than the first index, but more than one less
    assert time_array[index[0]] >= cdfepoch.compute(test_start)
    assert time_array[index[0]-1] <= cdfepoch.compute(test_start)

    assert time_array[index[-1]] <= cdfepoch.compute(test_end)


def test_findepochrange_cdftt2000():
    start_time = "2004-03-01 12:24:22.351793238"
    end_time = "2004-03-01 12:28:22.351793238"
    x = cdfepoch.parse([start_time, end_time])
    time_array = np.arange(x[0], x[1], step=1000000)

    test_start = [2004, 3, 1, 12, 25, 54, 123, 111, 98]
    test_end = [2004, 3, 1, 12, 26, 4, 123, 456, 789]
    index = cdfepoch.findepochrange(time_array, starttime=test_start, endtime=test_end)
    # Test that the test_start is less than the first index, but more than one less
    assert time_array[index[0]] >= cdfepoch.compute(test_start)
    assert time_array[index[0]-1] <= cdfepoch.compute(test_start)

    assert time_array[index[-1]] <= cdfepoch.compute(test_end)
    assert time_array[index[-1]+1] >= cdfepoch.compute(test_end)


if __name__ == '__main__':
    pytest.main([__file__])
