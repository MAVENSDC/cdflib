import unittest
import os
import numpy as np
from cdflib import cdfwrite
from cdflib import cdfread

class CDFReadTestCase(unittest.TestCase):
    
    def setUp(self):
        cdf_spec = {'rDim_sizes':[1]}
        self.test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                      "/testfiles/testing.cdf", cdf_spec=cdf_spec)
        self.test_file_reader = False
        self.compressed_test_file = False
        self.checksum_test_file = False
        return
    
    def tearDown(self):
        if self.test_file_reader:
            self.test_file_reader.close()
        if self.compressed_test_file:
            self.compressed_test_file.close()
            os.remove(os.path.dirname(__file__)+
                      "/testfiles/testing_compression.cdf")
        if self.checksum_test_file:
            self.checksum_test_file.close()
            os.remove(os.path.dirname(__file__)+
                      "/testfiles/testing_checksum.cdf")
        self.test_file.close()
        os.remove(os.path.dirname(__file__)+
                  "/testfiles/testing.cdf")
        return
        
    def test_cdf_creation(self):
        #Setup the test_file
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        test_file_info = self.test_file_reader.cdf_info()
        self.assertEqual(test_file_info['Majority'], 'Column_major')
        
        #Close the reading file
        self.test_file_reader.close()


    def test_globalattrs(self):
        #Setup the test_file
        globalAttrs={}
        globalAttrs['Global1']={0: 'Global Value 1'}
        globalAttrs['Global2']={0: 'Global Value 2'}
        globalAttrs['Global3']={0: [12, 'cdf_int4']}
        globalAttrs['Global4']={0: [12.34, 'cdf_double']}
        globalAttrs['Global5']={0: [12.34,21.43]}
        GA6={}
        GA6[0]='abcd'
        GA6[1]=[12, 'cdf_int2']
        GA6[2]=[12.5, 'cdf_float']
        GA6[3]=[[0,1,2], 'cdf_int8']
        globalAttrs['Global6']=GA6
        self.test_file.write_globalattrs(globalAttrs)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        attrib = self.test_file_reader.attinq('Global2')
        self.assertEqual(attrib['num_gr_entry'], 1)
        attrib = self.test_file_reader.attinq('Global6')
        self.assertEqual(attrib['num_gr_entry'], 4)
        entry = self.test_file_reader.attget('Global6', 3)
        self.assertEqual(entry['Data_Type'], 'CDF_INT8')
        for x in [0,1,2]:
            self.assertEqual(entry['Data'][x], x)
        
        #Close the reading file
        self.test_file_reader.close()

        
    def test_create_zvariable(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 1
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = True
        
        self.test_file.write_var(var_spec, var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 1)
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)
            
        #Close the reading file
        self.test_file_reader.close()

    def test_create_zvariable_no_recvary(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = False
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = True
        
        self.test_file.write_var(var_spec, var_data=np.array([2]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 8)
        var = self.test_file_reader.varget("Variable1")
        self.assertEqual(var, 2)
            
        #Close the reading file
        self.test_file_reader.close()

    def test_create_zvariables_with_attributes(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        varatts = {}
        varatts['Attribute1'] = 1
        varatts['Attribute2'] = '500'
        
        self.test_file.write_var(var_spec, var_attrs=varatts, 
                                 var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))
        
        var_spec['Variable'] = 'Variable2'
        varatts2 = {}
        varatts2['Attribute1'] = 2
        varatts2['Attribute2'] = '1000'
        self.test_file.write_var(var_spec, var_attrs=varatts2, 
                                 var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        att = self.test_file_reader.attget("Attribute1", entry=0)
        self.assertEqual(att['Data'], [1])
        att = self.test_file_reader.attget("Attribute2", entry=1)
        self.assertEqual(att['Data'], '1000')
        
        #Close the reading file
        self.test_file_reader.close()
        
    def test_create_zvariables_then_attributes(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        
        self.test_file.write_var(var_spec, var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))
        
        var_spec['Variable'] = 'Variable2'
        self.test_file.write_var(var_spec, var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))

        varatts = {}
        varatts['Attribute1'] = {'Variable1':1, 'Variable2':2}
        varatts['Attribute2'] = {0:'500', 1:'1000'}
        
        self.test_file.write_variableattrs(varatts)

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        att = self.test_file_reader.attget("Attribute1", entry=0)
        self.assertEqual(att['Data'], [1])
        att = self.test_file_reader.attget("Attribute2", entry=1)
        self.assertEqual(att['Data'], '1000')
        
        #Close the reading file
        self.test_file_reader.close()
    
    def test_sparse_zvariable_pad(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Sparse'] = 'pad_sparse'
        data = [[200,3000,3100,3500,4000,5000,6000,10000,10001,10002,20000], 
                np.array([0,1,2,3,4,5,6,7,8,9,10])]
        self.test_file.write_var(var_spec, var_data=data)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinq = self.test_file_reader.varinq("Variable1")
        var = self.test_file_reader.varget("Variable1")
        pad_num = varinq['Pad'][0]
        self.assertEqual(var[100], pad_num)
        self.assertEqual(var[3000], 1)
        
        #Close the reading file
        self.test_file_reader.close()
        
    def test_sparse_zvariable_previous(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Sparse'] = 'prev_sparse'
        data = [[200,3000,3100,3500,4000,5000,6000,10000,10001,10002,20000], 
                np.array([0,1,2,3,4,5,6,7,8,9,10])]
        self.test_file.write_var(var_spec, var_data=data)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinq = self.test_file_reader.varinq("Variable1")
        var = self.test_file_reader.varget("Variable1")
        pad_num = varinq['Pad'][0]
        self.assertEqual(var[100], pad_num)
        self.assertEqual(var[6001], var[6000])
        
        #Close the reading file
        self.test_file_reader.close()
    
    def test_nonsparse_zvariable_blocking(self):
        #Setup the test_file
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Block_Factor'] = 10000
        data = np.linspace(0, 999999, num=1000000)
        self.test_file.write_var(var_spec, var_data=data)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        var = self.test_file_reader.varget("Variable1")
        self.assertEqual(var[99999], 99999)
        
        #Close the reading file
        self.test_file_reader.close()
        
    def test_sparse_zvariable_blocking(self):
        #Setup the test_file
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
        self.test_file.write_var(var_spec, var_data=sparse_data)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinq = self.test_file_reader.varinq("Variable1")
        var = self.test_file_reader.varget("Variable1")
        pad_num = varinq['Pad'][0]
        self.assertEqual(var[30001], pad_num)
        self.assertEqual(var[70001], 30000)
        
        #Close the reading file
        self.test_file_reader.close()
        
    def test_sparse_virtual_zvariable_blocking(self):
        #Setup the test_file
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
        self.test_file.write_var(var_spec, var_data=sparse_data)
        
        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinq = self.test_file_reader.varinq("Variable1")
        var = self.test_file_reader.varget("Variable1")
        pad_num = varinq['Pad'][0]
        self.assertEqual(var[30001], pad_num)
        self.assertEqual(var[70001], 70001)
        
        #Close the reading file
        self.test_file_reader.close()
    
    def test_file_compression(self):
        #Setup the test_file
        cdf_spec = {'Compressed':True}
        self.compressed_test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                                 "/testfiles/testing_compression.cdf", 
                                                 cdf_spec=cdf_spec)
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 2
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        varatts = {}
        varatts['Attribute1'] = 1
        varatts['Attribute2'] = '500'
        
        self.compressed_test_file.write_var(var_spec, var_attrs=varatts, 
                                 var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))
        
        #Close the file so we can read
        self.compressed_test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing_compression.cdf")
        #Test CDF info
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)

        
        #Close the reading file
        self.test_file_reader.close()
    
    
    def test_checksum(self):
        #Setup the test_file
        cdf_spec = {'Checksum':True}
        self.checksum_test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                               "/testfiles/testing_checksum.cdf", 
                                               cdf_spec=cdf_spec)
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 4
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        varatts = {}
        varatts['Attribute1'] = 1
        varatts['Attribute2'] = '500'
        
        self.checksum_test_file.write_var(var_spec, var_attrs=varatts, 
                                                     var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))
        
        #Close the file so we can read
        self.checksum_test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing_checksum.cdf",
                                            validate=True)
        #Test CDF info
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)

        #Close the reading file
        self.test_file_reader.close()
    
    def test_checksum_compressed(self):
        #Setup the test_file
        cdf_spec = {'Compressed':6, 'Checksum':True}
        self.checksum_test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                               "/testfiles/testing_checksum.cdf", 
                                               cdf_spec=cdf_spec)
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Data_Type'] = 8
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        varatts = {}
        varatts['Attribute1'] = 1
        varatts['Attribute2'] = '500'
        
        self.checksum_test_file.write_var(var_spec, var_attrs=varatts, 
                                                     var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))
        
        #Close the file so we can read
        self.checksum_test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing_checksum.cdf",
                                            validate=True)
        #Test CDF info
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)

        
        #Close the reading file
        self.test_file_reader.close()
    
    def test_create_rvariable(self):
        #Setup the test_file       
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Var_Type'] = 'rvariable'
        var_spec['Data_Type'] = 12
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = [True]
        
        self.test_file.write_var(var_spec, var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 12)
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)
            
        #Close the reading file
        self.test_file_reader.close()
    
    def test_create_2d_rvariable(self):
        #Create a new test_file
        self.test_file.close()
        os.remove(os.path.dirname(__file__)+"/testfiles/testing.cdf")
        cdf_spec = {'rDim_sizes':[2,2]}
        self.test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                      "/testfiles/testing.cdf", cdf_spec=cdf_spec)
        
        #Setup the test_file       
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Var_Type'] = 'rvariable'
        var_spec['Data_Type'] = 14
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = [True, True]
        
        self.test_file.write_var(var_spec, var_data=np.array([[[0,1],[1,2]],
                                                              [[2,3],[3,4]],
                                                              [[4,5],[5,6]],
                                                              [[6,7],[7,8]],
                                                              [[8,9],[9,10]]]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 14)
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4]:
            self.assertEqual(var[x][0][0], 2*x)
            self.assertEqual(var[x][0][1], 2*x+1)
            self.assertEqual(var[x][1][0], 2*x+1)
            self.assertEqual(var[x][1][1], 2*x+2)
            
        #Close the reading file
        self.test_file_reader.close()
        
    def test_create_2d_rvariable_dimvary(self):
        #Create a new test_file
        self.test_file.close()
        os.remove(os.path.dirname(__file__)+"/testfiles/testing.cdf")
        cdf_spec = {'rDim_sizes':[2,20]}
        self.test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                      "/testfiles/testing.cdf", 
                                      cdf_spec=cdf_spec)
        
        #Setup the test_file       
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Var_Type'] = 'rvariable'
        var_spec['Data_Type'] = 21
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = [True, False]
        
        self.test_file.write_var(var_spec, var_data=np.array([[0,1],
                                                              [2,3],
                                                              [4,5],
                                                              [6,7],
                                                              [8,9]]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 21)
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4]:
            self.assertEqual(var[x][0], 2*x)
            self.assertEqual(var[x][1], 2*x+1)
            
        #Close the reading file
        self.test_file_reader.close()
        
    def test_create_2d_r_and_z_variables(self):
        #Create a new test_file
        self.test_file.close()
        os.remove(os.path.dirname(__file__)+"/testfiles/testing.cdf")
        cdf_spec = {'rDim_sizes':[2,20]}
        self.test_file = cdfwrite.CDF(os.path.dirname(__file__)+
                                      "/testfiles/testing.cdf", 
                                      cdf_spec=cdf_spec)
        
        #Setup the test_file       
        var_spec = {}
        var_spec['Variable'] = 'Variable1'
        var_spec['Var_Type'] = 'rvariable'
        var_spec['Data_Type'] = 22
        var_spec['Num_Elements'] = 1
        var_spec['Rec_Vary'] = True
        var_spec['Dim_Sizes'] = []
        var_spec['Dim_Vary'] = [True, False]
        
        self.test_file.write_var(var_spec, var_data=np.array([[0,1],
                                                              [2,3],
                                                              [4,5],
                                                              [6,7],
                                                              [8,9]]))

        var_spec['Variable'] = 'Variable2'
        var_spec['Var_Type'] = 'zvariable'
        varatts = {}
        varatts['Attribute1'] = 2
        varatts['Attribute2'] = '1000'
        self.test_file.write_var(var_spec, var_attrs=varatts, 
                                 var_data=np.array([0,1,2,3,4,5,6,7,8,9,10]))

        #Close the file so we can read
        self.test_file.close()
        
        #Open the file to read
        self.test_file_reader = cdfread.CDF(os.path.dirname(__file__)+
                                            "/testfiles/testing.cdf")
        
        #Test CDF info
        varinfo = self.test_file_reader.varinq("Variable1")
        self.assertEqual(varinfo['Data_Type'], 22)
        var = self.test_file_reader.varget("Variable1")
        for x in [0,1,2,3,4]:
            self.assertEqual(var[x][0], 2*x)
            self.assertEqual(var[x][1], 2*x+1)
        var = self.test_file_reader.varget("Variable2")
        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            self.assertEqual(var[x], x)
        
        att = self.test_file_reader.attget("Attribute1", entry='Variable2')
        self.assertEqual(att['Data'], [2])
        att = self.test_file_reader.attget("Attribute2", entry='Variable2')
        self.assertEqual(att['Data'], '1000')
        
        #Close the reading file
        self.test_file_reader.close()