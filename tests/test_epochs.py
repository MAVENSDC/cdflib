#!/usr/bin/env python
import pytest
import unittest
import numpy as np
import cdflib
from random import randint

'''
To check code coverage, first:

pip install pytest-cov

Then

pytest --cov

This will run all unit tests.  To view the coverage results:

coverage report
'''

'''
Each of these results were hand checked using either IDL or
other online resources.
'''


def test_encode_cdfepoch():
    x = cdflib.cdfepoch.encode([62285326000000.0, 62985326000000.0])
    assert x[0] == '1973-09-28T23:26:40.000'
    assert x[1] == '1995-12-04T19:53:20.000'

    y = cdflib.cdfepoch.encode(62975326000002.0, iso_8601=False)
    assert y == '11-Aug-1995 02:06:40.002'


class CDFEpochTestCase(unittest.TestCase):

    def test_encode_cdfepoch16(self):
        '''
        cdf_encode_epoch16(dcomplex(63300946758.000000, 176214648000.00000)) in IDL
        returns 04-Dec-2005 20:39:28.176.214.654.976

        However, I believe this IDL routine is bugged.  This website:
        https://www.epochconverter.com/seconds-days-since-y0

        shows a correct answer.
        '''
        x = cdflib.cdfepoch.encode(np.complex128(63300946758.000000 + 176214648000.00000j))
        self.assertEqual(x, '2005-12-04T20:19:18.176214648000')
        y = cdflib.cdfepoch.encode(np.complex128([33300946758.000000 + 106014648000.00000j,
                                                  61234543210.000000 + 000011148000.00000j]),
                                   iso_8601=False)
        self.assertEqual(y[0], '07-Apr-1055 14:59:18.106.014.648.000')
        self.assertEqual(y[1], '12-Jun-1940 03:20:10.000.011.148.000')

    def test_encode_cdftt2000(self):
        x = cdflib.cdfepoch.encode(186999622360321123)
        self.assertEqual(x, '2005-12-04T20:19:18.176321123')
        y = cdflib.cdfepoch.encode([500000000100, 123456789101112131],
                                   iso_8601=False)
        self.assertEqual(y[0], '01-Jan-2000 12:07:15.816.000.100')
        self.assertEqual(y[1], '30-Nov-2003 09:32:04.917.112.131')

    def test_unixtime(self):
        x = cdflib.cdfepoch.unixtime([500000000100, 123456789101112131])
        self.assertEqual(x[0], 946728435.816)
        self.assertEqual(x[1], 1070184724.917112)

    def test_breakdown_cdfepoch(self):
        x = cdflib.cdfepoch.breakdown([62285326000000.0, 62985326000000.0])
        # First in the array
        self.assertEqual(x[0][0], 1973)
        self.assertEqual(x[0][1], 9)
        self.assertEqual(x[0][2], 28)
        self.assertEqual(x[0][3], 23)
        self.assertEqual(x[0][4], 26)
        self.assertEqual(x[0][5], 40)
        self.assertEqual(x[0][6], 0)
        # Second in the array
        self.assertEqual(x[1][0], 1995)
        self.assertEqual(x[1][1], 12)
        self.assertEqual(x[1][2], 4)
        self.assertEqual(x[1][3], 19)
        self.assertEqual(x[1][4], 53)
        self.assertEqual(x[1][5], 20)
        self.assertEqual(x[1][6], 0)

    def test_breakdown_cdfepoch16(self):
        x = cdflib.cdfepoch.breakdown(np.complex128(63300946758.000000 + 176214648000.00000j))
        self.assertEqual(x[0], 2005)
        self.assertEqual(x[1], 12)
        self.assertEqual(x[2], 4)
        self.assertEqual(x[3], 20)
        self.assertEqual(x[4], 19)
        self.assertEqual(x[5], 18)
        self.assertEqual(x[6], 176)
        self.assertEqual(x[7], 214)
        self.assertEqual(x[8], 648)
        self.assertEqual(x[9], 000)

    def test_breakdown_cdftt2000(self):
        x = cdflib.cdfepoch.breakdown(123456789101112131)
        self.assertEqual(x[0], 2003)
        self.assertEqual(x[1], 11)
        self.assertEqual(x[2], 30)
        self.assertEqual(x[3], 9)
        self.assertEqual(x[4], 32)
        self.assertEqual(x[5], 4)
        self.assertEqual(x[6], 917)
        self.assertEqual(x[7], 112)
        self.assertEqual(x[8], 131)

    def test_compute_cdfepoch(self):
        '''
        Using random numbers for the compute tests
        '''
        random_time = []
        random_time.append(randint(0, 2018))  # Year
        random_time.append(randint(1, 12))  # Month
        random_time.append(randint(1, 28))  # Date
        random_time.append(randint(0, 23))  # Hour
        random_time.append(randint(0, 59))  # Minute
        random_time.append(randint(0, 59))  # Second
        random_time.append(randint(0, 999))  # Millisecond
        x = cdflib.cdfepoch.breakdown(cdflib.cdfepoch.compute(random_time))
        i = 0
        for t in x:
            self.assertEqual(t, random_time[i], 'Time '+str(random_time) + ' was not equal to ' + str(x))
            i += 1

    def test_compute_cdfepoch16(self):
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
        random_time.append(randint(0, 999))  # Picosecond
        x = cdflib.cdfepoch.breakdown(cdflib.cdfepoch.compute(random_time))
        i = 0
        for t in x:
            self.assertEqual(t, random_time[i], 'Time '+str(random_time) + ' was not equal to ' + str(x))
            i += 1

    def test_compute_cdftt2000(self):
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
        x = cdflib.cdfepoch.breakdown(cdflib.cdfepoch.compute(random_time))
        i = 0
        for t in x:
            self.assertEqual(t, random_time[i], 'Time '+str(random_time) + ' was not equal to ' + str(x))
            i += 1

    def test_parse_cdfepoch(self):
        x = cdflib.cdfepoch.encode(62567898765432.0)
        self.assertEqual(x, "1982-09-12T11:52:45.432")
        parsed = cdflib.cdfepoch.parse(x)
        self.assertEqual(parsed, 62567898765432.0)

    def test_parse_cdfepoch16(self):
        input_time = np.complex(53467976543.0, 543218654100)
        x = cdflib.cdfepoch.encode(input_time)
        self.assertEqual(x, "1694-05-01T07:42:23.543218654100")
        parsed = cdflib.cdfepoch.parse(x, to_np=True)
        self.assertEqual(parsed, input_time)

    def test_parse_cdftt2000(self):
        input_time = 131415926535793238
        x = cdflib.cdfepoch.encode(input_time)
        self.assertEqual(x, "2004-03-01T12:24:22.351793238")
        parsed = cdflib.cdfepoch.parse(x)
        self.assertEqual(parsed, input_time)

    def test_findepochrange_cdfepoch(self):
        start_time = "2013-12-01T12:24:22.000"
        end_time = "2014-12-01T12:24:22.000"
        x = cdflib.cdfepoch.parse([start_time, end_time])
        time_array = np.arange(x[0], x[1], step=1000000)

        test_start = [2014, 8, 1, 8, 1, 54, 123]
        test_end = [2018, 1, 1, 1, 1, 1, 1]
        index = cdflib.cdfepoch.findepochrange(time_array, starttime=test_start, endtime=test_end)
        # Test that the test_start is less than the first index, but more than one less
        self.assertGreaterEqual(time_array[index[0]], cdflib.cdfepoch.compute(test_start))
        self.assertLessEqual(time_array[index[0]-1], cdflib.cdfepoch.compute(test_start))

        self.assertLessEqual(time_array[index[-1]], cdflib.cdfepoch.compute(test_end))
        return

    def test_findepochrange_cdftt2000(self):
        start_time = "2004-03-01T12:24:22.351793238"
        end_time = "2004-03-01T12:28:22.351793238"
        x = cdflib.cdfepoch.parse([start_time, end_time])
        time_array = np.arange(x[0], x[1], step=1000000)

        test_start = [2004, 3, 1, 12, 25, 54, 123, 111, 98]
        test_end = [2004, 3, 1, 12, 26, 4, 123, 456, 789]
        index = cdflib.cdfepoch.findepochrange(time_array, starttime=test_start, endtime=test_end)
        # Test that the test_start is less than the first index, but more than one less
        self.assertGreaterEqual(time_array[index[0]], cdflib.cdfepoch.compute(test_start))
        self.assertLessEqual(time_array[index[0]-1], cdflib.cdfepoch.compute(test_start))

        self.assertLessEqual(time_array[index[-1]], cdflib.cdfepoch.compute(test_end))
        self.assertGreaterEqual(time_array[index[-1]+1], cdflib.cdfepoch.compute(test_end))
        return

    def test_findepochrange_cdfepoch16(self):
        start_time = "1978-03-10T03:24:22.351793238462"
        end_time = "1978-06-13T01:28:22.338327950466"
        x = cdflib.cdfepoch.parse([start_time, end_time])
        first_int_step = int((x[1].real - x[0].real) / 1000)
        second_int_step = int((x[1].imag - x[0].imag) / 1000)
        time_array = []
        for i in range(0, 1000):
            time_array.append(x[0]+complex(first_int_step*i, second_int_step*i))

        test_start = [1978, 6, 10, 3, 24, 22, 351, 793, 238, 462]
        test_end = [1978, 6, 12, 23, 11, 1, 338, 341, 416, 466]
        index = cdflib.cdfepoch.findepochrange(time_array, starttime=test_start, endtime=test_end)

        # Test that the test_start is less than the first index, but more than one less
        self.assertGreaterEqual(time_array[index[0]].real, cdflib.cdfepoch.compute(test_start).real)
        self.assertLessEqual(time_array[index[0]-1].real, cdflib.cdfepoch.compute(test_start).real)
        self.assertLessEqual(time_array[index[-1]].real, cdflib.cdfepoch.compute(test_end).real)
        self.assertGreaterEqual(time_array[index[-1]+1].real, cdflib.cdfepoch.compute(test_end).real)


if __name__ == '__main__':
    pytest.main(['-x', __file__])
