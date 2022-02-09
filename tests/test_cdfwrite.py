#!/usr/bin/env python
from pathlib import Path

import numpy as np
import pytest

from cdflib import cdfread, cdfwrite

R = Path(__file__).parent
fnbasic = 'testing.cdf'


def cdf_create(fn: Path, spec: dict):
    return cdfwrite.CDF(fn, cdf_spec=spec)


def cdf_read(fn: Path, validate: bool = False):
    return cdfread.CDF(fn, validate=validate)


def test_cdf_creation(tmp_path):

    fn = tmp_path / fnbasic
    cdf_create(fn, {'rDim_sizes': [1]}).close()

    reader = cdf_read(fn)

    # Test CDF info
    info = reader.cdf_info()
    assert info['Majority'] == 'Row_major'


def test_checksum(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic
    tfile = cdf_create(fn, {'Checksum': True})

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 4
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    varatts = {}
    varatts['Attribute1'] = 1
    varatts['Attribute2'] = '500'

    tfile.write_var(var_spec, var_attrs=varatts,
                    var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    tfile.close()

# %% Open the file to read
    reader = cdf_read(fn, validate=True)
    # Test CDF info
    var = reader.varget("Variable1")
    assert (var == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).all()
    # test convenience info
    assert (reader["Variable1"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).all()


def test_checksum_compressed(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic
    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 2
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    varatts = {}
    varatts['Attribute1'] = 1
    varatts['Attribute2'] = '500'

    v = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    tfile = cdf_create(fn, {'Compressed': 6, 'Checksum': True})
    tfile.write_var(var_spec, var_attrs=varatts,
                    var_data=v)

    tfile.close()
# %% Open the file to read
    reader = cdf_read(fn, validate=True)

    var = reader.varget("Variable1")
    assert (var == v).all()

    att = reader.attget("Attribute1", entry=0)
    assert att['Data'] == [1]

    att = reader.attget("Attribute2", entry=0)
    assert att['Data'] == '500'


def test_file_compression(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 2
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    varatts = {}
    varatts['Attribute1'] = 1
    varatts['Attribute2'] = '500'

    v = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    tfile = cdf_create(fn, {'Compressed': 6, 'Checksum': True})
    tfile.write_var(var_spec, var_attrs=varatts,
                    var_data=v)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)
    # Test CDF info
    var = reader.varget("Variable1")
    assert (var == v).all()


def test_globalattrs(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    globalAttrs = {}
    globalAttrs['Global1'] = {0: 'Global Value 1'}
    globalAttrs['Global2'] = {0: 'Global Value 2'}
    globalAttrs['Global3'] = {0: [12, 'cdf_int4']}
    globalAttrs['Global4'] = {0: [12.34, 'cdf_double']}
    globalAttrs['Global5'] = {0: [12.34, 21.43]}

    GA6 = {}
    GA6[0] = 'abcd'
    GA6[1] = [12, 'cdf_int2']
    GA6[2] = [12.5, 'cdf_float']
    GA6[3] = [[0, 1, 2], 'cdf_int8']

    globalAttrs['Global6'] = GA6

    tfile = cdf_create(fn, {'Checksum': True})
    tfile.write_globalattrs(globalAttrs)

    tfile.close()
# %% Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    attrib = reader.attinq('Global2')
    assert attrib['num_gr_entry'] == 1

    attrib = reader.attinq('Global6')
    assert attrib['num_gr_entry'] == 4

    entry = reader.attget('Global6', 3)
    assert entry['Data_Type'] == 'CDF_INT8'

    for x in [0, 1, 2]:
        assert entry['Data'][x] == x


def test_create_zvariable(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic
    vs = {}
    vs['Variable'] = 'Variable1'
    vs['Data_Type'] = 1
    vs['Num_Elements'] = 1
    vs['Rec_Vary'] = True
    vs['Dim_Sizes'] = []
    vs['Dim_Vary'] = True

    tfile = cdf_create(fn, {'Checksum': True})
    tfile.write_var(vs, var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
    tfile.close()

# %% Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")
    assert varinfo['Data_Type'] == 1

    var = reader.varget("Variable1")
    assert (var == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).all()


def test_create_rvariable(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic
    vs = {}
    vs['Variable'] = 'Variable1'
    vs['Var_Type'] = 'rvariable'
    vs['Data_Type'] = 12
    vs['Num_Elements'] = 1
    vs['Rec_Vary'] = True
    vs['Dim_Sizes'] = []
    vs['Dim_Vary'] = [True]

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(vs, var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")
    assert varinfo['Data_Type'] == 12

    var = reader.varget("Variable1")
    for x in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        assert var[x] == x


def test_create_zvariable_no_recvory(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = False
    var_spec['Dim_Sizes'] = []
    var_spec['Dim_Vary'] = True

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=np.array([2]))
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")
    assert varinfo['Data_Type'] == 8

    var = reader.varget("Variable1")
    assert var == 2


def test_create_zvariables_with_attributes(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    varatts = {}
    varatts['Attribute1'] = 1
    varatts['Attribute2'] = '500'

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_attrs=varatts,
                    var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    var_spec['Variable'] = 'Variable2'
    varatts2 = {}
    varatts2['Attribute1'] = 2
    varatts2['Attribute2'] = '1000'
    tfile.write_var(var_spec, var_attrs=varatts2,
                    var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    att = reader.attget("Attribute1", entry=0)
    assert att['Data'] == [1]

    att = reader.attget("Attribute2", entry=1)
    assert att['Data'] == '1000'


def test_create_zvariables_then_attributes(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    var_spec['Variable'] = 'Variable2'
    tfile.write_var(var_spec, var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    varatts = {}
    varatts['Attribute1'] = {'Variable1': 1, 'Variable2': 2}
    varatts['Attribute2'] = {0: '500', 1: '1000'}

    tfile.write_variableattrs(varatts)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    att = reader.attget("Attribute1", entry=0)
    assert att['Data'] == [1]

    att = reader.attget("Attribute2", entry=1)
    att['Data'] == '1000'


def test_nonsparse_zvariable_blocking(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Block_Factor'] = 10000
    data = np.linspace(0, 999999, num=1000000)

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=data)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    var = reader.varget("Variable1")
    assert var[99999] == 99999


def test_sparse_virtual_zvariable_blocking(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Block_Factor'] = 10000
    var_spec['Sparse'] = 'pad_sparse'
    data = np.linspace(0, 140000, num=140001)
    physical_records1 = np.linspace(1, 10000, num=10000)
    physical_records2 = np.linspace(20001, 30000, num=10000)
    physical_records3 = np.linspace(50001, 60000, num=10000)
    physical_records4 = np.linspace(70001, 140000, num=70000)
    physical_records = np.concatenate((physical_records1,
                                       physical_records2,
                                       physical_records3,
                                       physical_records4)).astype(int)
    sparse_data = [physical_records, data]

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=sparse_data)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinq = reader.varinq("Variable1")
    var = reader.varget("Variable1")

    pad_num = varinq['Pad'][0]
    assert var[30001] == pad_num
    assert var[70001] == 70001


def test_sparse_zvariable_blocking(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Block_Factor'] = 10000
    var_spec['Sparse'] = 'pad_sparse'
    data = np.linspace(0, 99999, num=100000)
    physical_records1 = np.linspace(1, 10000, num=10000)
    physical_records2 = np.linspace(20001, 30000, num=10000)
    physical_records3 = np.linspace(50001, 60000, num=10000)
    physical_records4 = np.linspace(70001, 140000, num=70000)
    physical_records = np.concatenate((physical_records1,
                                       physical_records2,
                                       physical_records3,
                                       physical_records4)).astype(int)
    sparse_data = [physical_records, data]

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=sparse_data)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    # tfile = cdf_create(fn, {'rDim_sizes': [1]})
    varinq = reader.varinq("Variable1")
    var = reader.varget("Variable1")
    pad_num = varinq['Pad'][0]

    assert var[30001] == pad_num
    assert var[70001] == 30000


def test_sparse_zvariable_pad(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic
    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Sparse'] = 'pad_sparse'
    data = [[200, 3000, 3100, 3500, 4000, 5000, 6000, 10000, 10001, 10002, 20000],
            np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])]

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=data)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinq = reader.varinq("Variable1")
    var = reader.varget("Variable1")
    pad_num = varinq['Pad'][0]

    assert var[100] == pad_num
    assert var[3000] == 1


def test_sparse_zvariable_previous(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Data_Type'] = 8
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Sparse'] = 'prev_sparse'
    data = [[200, 3000, 3100, 3500, 4000, 5000, 6000, 10000, 10001, 10002, 20000],
            np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])]

    tfile = cdf_create(fn, {'rDim_sizes': [1]})
    tfile.write_var(var_spec, var_data=data)
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinq = reader.varinq("Variable1")
    var = reader.varget("Variable1")
    pad_num = varinq['Pad'][0]

    assert var[100] == pad_num
    assert var[6001] == var[6000]


def test_create_2d_rvariable(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Var_Type'] = 'rvariable'
    var_spec['Data_Type'] = 14
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Dim_Vary'] = [True, True]

    tfile = cdf_create(fn, {'rDim_sizes': [2, 2]})
    tfile.write_var(var_spec, var_data=np.array([[[0, 1], [1, 2]],
                                                 [[2, 3], [3, 4]],
                                                 [[4, 5], [5, 6]],
                                                 [[6, 7], [7, 8]],
                                                 [[8, 9], [9, 10]]]))
    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")
    assert varinfo['Data_Type'] == 14

    var = reader.varget("Variable1")
    for x in [0, 1, 2, 3, 4]:
        assert var[x][0][0] == 2*x
        assert var[x][0][1] == 2*x+1
        assert var[x][1][0] == 2*x+1
        assert var[x][1][1] == 2*x+2


def test_create_2d_rvariable_dimvary(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Var_Type'] = 'rvariable'
    var_spec['Data_Type'] = 21
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Dim_Vary'] = [True, False]

    tfile = cdf_create(fn,  {'rDim_sizes': [2, 20]})

    tfile.write_var(var_spec, var_data=np.array([[0, 1],
                                                 [2, 3],
                                                 [4, 5],
                                                 [6, 7],
                                                 [8, 9]]))

    tfile.close()

    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")

    assert varinfo['Data_Type'] == 21
    var = reader.varget("Variable1")
    for x in [0, 1, 2, 3, 4]:
        assert var[x][0] == 2*x
        assert var[x][1] == 2*x+1


def test_create_2d_r_and_z_variables(tmp_path):
    # Setup the test_file
    fn = tmp_path / fnbasic

    var_spec = {}
    var_spec['Variable'] = 'Variable1'
    var_spec['Var_Type'] = 'rvariable'
    var_spec['Data_Type'] = 22
    var_spec['Num_Elements'] = 1
    var_spec['Rec_Vary'] = True
    var_spec['Dim_Sizes'] = []
    var_spec['Dim_Vary'] = [True, False]

    tfile = cdf_create(fn,  {'rDim_sizes': [2, 20]})
    tfile.write_var(var_spec, var_data=np.array([[0, 1],
                                                 [2, 3],
                                                 [4, 5],
                                                 [6, 7],
                                                 [8, 9]]))

    var_spec['Variable'] = 'Variable2'
    var_spec['Var_Type'] = 'zvariable'
    varatts = {}
    varatts['Attribute1'] = 2
    varatts['Attribute2'] = '1000'
    tfile.write_var(var_spec, var_attrs=varatts,
                    var_data=np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    tfile.close()
    # Open the file to read
    reader = cdf_read(fn)

    # Test CDF info
    varinfo = reader.varinq("Variable1")
    assert varinfo['Data_Type'] == 22

    var = reader.varget("Variable1")
    for x in [0, 1, 2, 3, 4]:
        assert var[x][0] == 2*x
        assert var[x][1] == 2*x+1

    var = reader.varget("Variable2")
    assert (var == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).all()

    att = reader.attget("Attribute1", entry='Variable2')
    assert att['Data'] == [2]

    att = reader.attget("Attribute2", entry='Variable2')
    assert att['Data'] == '1000'


if __name__ == '__main__':
    pytest.main([__file__])
