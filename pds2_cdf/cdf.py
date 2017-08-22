"""
pds_cdf.py

    This is a python script to read CDF files
without needing to install the CDF NASA library.
    This Python code only supports V3 CDFs (not compressed at the CDF-level).
    This code is based on Python 3. 

    Creates a CDF file variable, and then access the variable with 
the commands:

CDF Inquiry:  cdf_info()
              Returns a dictionary that shows the basic CDF information. This
              information includes:
              ['CDF']: the name of the CDF
              ['Version']: the version of the CDF
              ['Encoding']: the endianness of the CDF
              ['Majority']: the row/column majority
              ['zVariables']: the dictionary for zVariable numbers and their
                              corresponding names
              ['rVariables']: the dictionary for rVariable numbers and their
                              corresponding names
              ['Attributes']: the dictionary for attribute numbers and their
                              corresponding names and scopes


Variable Information:
              var_info(variable)
              Returns a dictionary that shows the basic variable information.
              This information includes:
              ['Variable']: the name of the variable
              ['Num']: the variable number
              ['Var_Type']: the variable type: zVariable or rVariable
              ['Data_Type']: the variable's CDF data type
              ['Num_Elements']: the number of elements of the variable
              ['Num_Dims']: the dimensionality of the variable record
              ['Dim_Sizes']: the shape of the variable record
              ['Sparse']: the variable's record sparseness
              ['Last_Rec']: the maximum written record number (0-based)


Attribute Inquiry:  attinq( attribute )
                    Returns a python dictionary of attribute information
                   
Get Attribute(s):   attget( attribute, entry_number|variable_name [,to_dict=True] )
                    Returns the value of the attribute at the entry number
                    provided.  For a variable attribute, variable name can be
                    used, instead of its corresponding entry number. By
                    default, it returns a 'numpy.ndarray', 'list' or 'str' 
                    class object, depending on the attribute data and its data
                    type. If to_dict is set as True, a dictionary is returned
                    with the following defined keys:
                    ['Item_Size']: the number of bytes for each entry value
                    ['Num_Items']: total number of values extracted
                    ['Data_Type']: the CDF data type
                    ['Data']: retrieved attribute data as a scalar value, a
                              list of values or a string

                    varattsget(variable)
                    Unlike attget, which returns a single attribute entry value,
                    this function returns all of the variable attribute entries,
                    in a dictionary (in the form of 'attribute': value pair) for
                    a variable. If there is no entry found, None is returned.
                   
                    globalattsget()
                    This function returns all of the global attribute entries,
                    in a dictionary (in the form of 'attribute': {entry: value}
                    pair) from a CDF. If there is no entry found, None is
                    returned.
                   
Variable Inquiry:   varinq( variable )
                    Returns a python dictionary of variable information 
                   
Get Variable:       varget( variable, [epoch=None], [[starttime=None, 
                            endtime=None] | [startrec=None, endrec = None]],
                            [,to_dict=True])
                    Returns the variable data. Variable can be entered either
                    a name or a variable number. By default, it returns a
                    'numpy.ndarray' or 'list' class object, depending on the
                    data type, with the variable data and its specification.
                    If to_dict is set as True, a dictionary is returned
                    with the following defined keys for the output:
                    ['Rec_Ndim']: the dimension number of each variable record
                    ['Rec_Shape']: the shape of the variable record dimensions
                    ['Num_Records']: the number of the retrieved records
                    ['Item_Size']: the number of bytes for each data value
                    ['Data_Type']: the CDF data type
                    ['Data']: retrieved variable data, a list of values
                              reflecting how they are stored in the file.
                    By default, the full variable data is returned. To acquire
                    only a portion of the data for a record-varying variable,
                    either the time or record (0-based) range can be specified.
                    'epoch' can be used to specify which time variable this 
                    variable depends on and is to be searched for the time range.
                    For the ISTP-compliant CDFs, the time variable will come from
                    the attribute 'DEPEND_0' from this variable. The function will
                    automatically search for it thus no need to specify 'epoch'.
                    If either the start or end time is not specified,
                    the possible minimum or maximum value for the specific epoch
                    data type is assumed. If either the start or end record is not
                    specified, the range starts at 0 or/and ends at the last of the
                    written data.  

Note: CDF's CDF_EPOCH16 data type uses 2 8-byte doubles for each data value.
      In Python, each vale is presented as a complex or numpy.complex128.

Get epoch range:    epochrange( epoch, [starttime=None, endtime=None])
                    Returns a list of the record numbers, representing the
                    corresponding starting and ending records within the time
                    range from the epoch data. A None is returned if there is no
                    data either written or found in the time range.

Sample use - 

    import pds_cdf
    swea_cdf_file = pds_cdf.CDF('/path/to/swea_file.cdf')
    swea_cdf_file.cdf_info()
    x = swea_cdf_file.varget('NameOfVariable')
    swea_cdf_file.close()

@author: Bryan Harter
"""


import numpy as np
import sys
import struct
import gzip
import hashlib
import pds2_cdf.cdfepoch.CDFepoch as cdfepoch

class CDF(object):
    def __init__(self, path, validate=None):
        
        #READ FIRST INTERNAL RECORDS
        try:
            f = open(path, 'rb')
        except:
            try:
                f = open(path+'.cdf', 'rb')
            except:
                print('CDF:',path,' not found')
                return
            
        self.file = f
        self.file.seek(0)
        magic_number = f.read(4).hex()
        if magic_number != 'cdf30001':
            print('Not a CDF V3 file or a non-supported CDF!')
            return
        compressed_bool = f.read(4).hex()
        self._compressed = not (compressed_bool == '0000ffff')
        
        cdr_info = self._read_cdr(self.file.tell())
        gdr_info = self._read_gdr(self.file.tell())

        if cdr_info['md5'] and (validate != None):
            if not self._md5_validation(gdr_info['eof']):
                print('This file fails the md5 checksum....')
                f.close()
                return

        if not cdr_info['format']:
            print('This package does not support multi-format CDF')
            f.close()
            return

        if cdr_info['encoding']==3 or cdr_info['encoding']==14 or \
           cdr_info['encoding']==15:
            print('This package does not support CDFs with this '+\
                  self._encoding_token(cdr_info['encoding'])+' encoding') 
            f.close()
            return

        #SET GLOBAL VARIABLES
        self._path = path
        self._version = cdr_info['version']
        self._encoding = cdr_info['encoding']
        self._majority = cdr_info['majority']
        self._copyright = cdr_info['copyright']
        self._first_zvariable = gdr_info['first_zvariable']
        self._first_rvariable = gdr_info['first_rvariable']
        self._first_adr = gdr_info['first_adr']
        self._num_zvariable = gdr_info['num_zvariables']
        self._num_rvariable = gdr_info['num_rvariables']
        self._rvariables_num_dims = gdr_info['rvariables_num_dims']
        self._rvariables_dim_sizes = gdr_info['rvariables_dim_sizes']
        self._num_att = gdr_info['num_attributes']

    def close(self):
        self.file.close()

    def cdf_info(self):
        mycdf_info = {}
        mycdf_info['CDF'] = self._path
        mycdf_info['Version'] = self._version
        mycdf_info['Encoding'] = self._endian()
        mycdf_info['Majority'] = self._major_token(self._majority)
        if self._num_zvariable > 0:
            mycdf_info['zVariables'] = self._get_Variables(self._first_zvariable,
                                                           self._num_zvariable)
        else:
            mycdf_info['zVariables'] = {}
        if self._num_rvariable > 0:
            mycdf_info['rVariables'] = self._get_Variables(self._first_rvariable,
                                                           self._num_rvariable)
        else:
            mycdf_info['rVariables'] = {}
        mycdf_info['Attributes'] = self._get_Attributes()
        mycdf_info['Copyright'] = self._copyright
        return mycdf_info

    def var_info(self, variable):
        if (isinstance(variable, int) and self._num_zvariable > 0 and 
            self._num_rvariable > 0):
            print('This CDF has both r and z variables. Use variable name')
            return
        if self._num_zvariable > 0:
            position = self._first_zvariable
            num_variable = self._num_zvariable
        else:
            position = self._first_rvariable
            num_variable = self._num_rvariable
        if isinstance(variable, str):
            for z in range(0, num_variable):
                name, vdr_next = self._read_vdr_fast(position)
                if name.strip() == variable.strip():
                    vdr_info = self._read_vdr(position)
                    var = {}
                    var['Variable'] = name
                    var['Num'] = z
                    var['Var_Type'] = self._variable_token(vdr_info['section_type'])
                    var['Data_Type'] = self._datatype_token(vdr_info['data_type'])
                    var['Num_Elements'] = vdr_info['num_elements']
                    var['Num_Dims'] = vdr_info['num_dims']
                    var['Dim_Sizes'] = vdr_info['dim_sizes']
                    var['Sparse'] = self._sparse_token(vdr_info['sparse'])
                    var['Last_Rec'] = vdr_info['max_records']
                    return var
                else:
                    position = vdr_next
            print('Variable: \''+variable+'\' not found...')
        elif isinstance(variable, int):
            if (variable < 0 or variable > num_variable):
                print('No variable by this number:',variable)
                return
            for _ in range(0, variable):
                name, next_vdr = self._read_vdr_fast(position)
                position = next_vdr
            vdr_info = self._read_vdr(position)
            var = {}
            var['Variable'] = vdr_info['name']
            var['Num'] = vdr_info['variable_number']
            var['Var_Type'] = self._variable_token(vdr_info['section_type'])
            var['Data_Type'] = self._datatype_token(vdr_info['data_type'])
            var['Num_Elements'] = vdr_info['num_elements']
            var['Num_Dims'] = vdr_info['num_dims']
            var['Dim_Sizes'] = vdr_info['dim_sizes']
            var['Sparse'] = self._sparse_token(vdr_info['sparse'])
            var['Last_Rec'] = vdr_info['max_records']
            return var
        else:
            print('Please set variable keyword equal to the name or ',
                  'number of an variable')
            for x in range(0, num_variable):
                name, next_vdr = self._read_vdr_fast(position)
                print('NAME: '+name+' NUMBER: '+str(x))
                position=next_vdr

    def attinq(self, attribute = None):
        position = self._first_adr
        if isinstance(attribute, str):
            for _ in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                if name.strip() == attribute.strip():
                    return self._read_adr(position)
                position = next_adr
            print('No attribute by this name:',attribute)
            return
        elif isinstance(attribute, int):
            if (attribute < 0 or attribute > self._num_zvariable):
                print('No attribute by this number:',attribute)
                return
            for _ in range(0, attribute):
                name, next_adr = self._read_adr_fast(position)
                position = next_adr
            return self._read_adr(position)
        else:
            print('Please set attribute keyword equal to the name or ',
                  'number of an attribute')
            for x in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                print('NAME: '+name+' NUMBER: '+str(x))
                position=next_adr
                
    def attget(self, attribute = None, entry_num = None, to_dict = False):
        
        #Starting position
        position = self._first_adr
        
        #Return Dictionary or Numpy
        to_np = True
        if to_dict:
            to_np = False
            
        #Get Correct ADR 
        if isinstance(attribute, str):
            if isinstance(entry_num, int):
                if (self._num_zvariable > 0 and self._num_rvariable > 0):
                    print('This CDF has both r and z variables. Use variable name')
                    return
            for _ in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                if (name.strip() == attribute.strip()):
                    adr_info = self._read_adr(position)   
                else:
                    position = next_adr            
        elif isinstance(attribute, int):
            if (attribute < 0) or (attribute > self._num_att):
                print('No attribute by this number:',attribute)
                return
            if not isinstance(entry_num, int):
                print('Entry has to be a number...')
                return
            for _ in range(0, attribute):
                name, next_adr = self._read_adr_fast(position)
                position = next_adr
            adr_info = self._read_adr(position)
        else:
            print('Please set attribute keyword equal to the name or ',
                  'number of an attribute')
            for x in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                print('NAME:'+name+' NUMBER: '+str(x))
                position=next_adr
                    
                    
        #Find the correct entry from entry_num
        if adr_info['scope'] == 1:
            if not isinstance(entry_num, int):
                print('Global entry should be a number')
                return
            num_entry_string = 'num_gr_entry'
            first_entry_string = 'first_gr_entry'
            max_entry_string = 'max_gr_entry'
        else:
            var_num = -1
            zvar = False
            if isinstance(entry_num, str):
                # a zVariable?
                positionx = self._first_zvariable
                for x in range(0, self._num_zvariable):
                    name, vdr_next = self._read_vdr_fast(positionx)
                    if (name.strip() == entry_num.strip()):
                        var_num = x
                        zvar = True
                        break
                    positionx = vdr_next
                if var_num == -1:
                    # a rVariable?
                    positionx = self._first_rvariable
                    for x in range(0, self._num_rvariable):
                        name, vdr_next = self._read_vdr_fast(positionx)
                        if (name.strip() == entry_num.strip()):
                            var_num = x
                            break
                        positionx = vdr_next
                if var_num == -1:
                    print('No variable by this name:',entry_num)
                    return
                entry_num = var_num
            else:
                if self._num_zvariable > 0:
                    zvar = True
            if zvar:
                num_entry_string = 'num_z_entry'
                first_entry_string = 'first_z_entry'
                max_entry_string = 'max_z_entry'
            else:
                num_entry_string = 'num_gr_entry'
                first_entry_string = 'first_gr_entry'
                max_entry_string = 'max_gr_entry'
        if entry_num > adr_info[max_entry_string]:
            print('The entry does not exist')
            return
        return self._get_attdata(adr_info, entry_num, num_entry_string,
                              first_entry_string, to_np)

        print('No attribute by this name:',attribute)
        return

    def varinq(self, variable = None):
        position = self._first_zvariable
        if isinstance(variable, str):
            for _ in range(0, self._num_zvariable):
                name, vdr_next = self._read_vdr_fast(position)
                if name.strip() == variable.strip():
                    return self._read_vdr(position)
                position = vdr_next
            print('No variable by this name:',variable)
            return
        elif isinstance(variable, int):
            if (variable < 0 or variable > self._num_zvariable):
                print('No variable by this number:',variable)
                return
            for _ in range(0, variable):
                name, next_vdr = self._read_vdr_fast(position)
                position = next_vdr
            return self._read_vdr(position)
        else:
            print('Please set variable keyword equal to the name or ',
                  'number of an variable')
            for x in range(0, self._num_zvariable):
                name, next_vdr = self._read_vdr_fast(position)
                print('NAME: '+name+' NUMBER: '+str(x))
                position=next_vdr
                
    def varget(self, variable = None, epoch = None, starttime = None, 
               endtime = None, startrec = 0, endrec = None, 
               to_dict = False, record_only=False):
        
        if (isinstance(variable, int) and self._num_zvariable > 0 and 
            self._num_rvariable > 0):
            print('This CDF has both r and z variables. Use variable name')
            return
        
        to_np = False
        if (to_dict != True):
            to_np = True
        
        if ((starttime != None or endtime != None) and
            (startrec != None or endrec != None)):
            print('Can\'t specify both time and record range')
            return
        
        if isinstance(variable, str):
            # check for zvariables first
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
                return self._get_vardata(position, num_variable, variable,
                                         epoch=epoch, starttime=starttime, endtime=endtime, 
                                         startrec=startrec, endrec=endrec, to_np=to_np, 
                                         record_only=record_only)
            # check for rvariables later
            if self._num_rvariable > 0:
                position = self._first_rvariable
                num_variable = self._num_rvariable
                return self._get_vardata(position, num_variable, variable,
                                         epoch=epoch, starttime=starttime, endtime=endtime, 
                                         startrec=startrec, endrec=endrec, to_np=to_np, 
                                         record_only=record_only)
            print('No variable by this name:',variable)
            return
        elif isinstance(variable, int):
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
            else:
                position = self._first_rvariable
                num_variable = self._num_rvariable
            if (variable < 0 or variable >= num_variable):
                print('No variable by this number:',variable)
                return None
            for _ in range(0, variable):
                name, next_vdr = self._read_vdr_fast(position)
                position = next_vdr
            vdr_info = self._read_vdr(position)
            if (vdr_info['max_records'] < 0):
                print('No data is written for this variable')
                return None
            return self._read_vardata(vdr_info, epoch=epoch, starttime=starttime, endtime=endtime,
                                      startrec=startrec, endrec=endrec, to_np=to_np, record_only=record_only)
        else:
            print('Please set variable keyword equal to the name or ',
                  'number of an variable')
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
                print('zVariables:')
                for x in range(0, num_variable):
                    name, next_vdr = self._read_vdr_fast(position)
                    print('  NAME: '+name+' NUMBER: '+str(x))
                    position=next_vdr
            if self._num_rvariable > 0:
                position = self._first_rvariable
                num_variable = self._num_rvariable
                print('rVariables:')
                for x in range(0, num_variable):
                    name, next_vdr = self._read_vdr_fast(position)
                    print('  NAME: '+name+' NUMBER: '+str(x))
                    position=next_vdr

    def epochrange(self, epoch = None, starttime = None, endtime = None):
        return self.varget(variable=epoch, starttime=starttime, endtime=endtime, record_only=True)

    def globalattsget(self):
        return self._read_globalatts()

    def varattsget(self, variable = None):
        if (isinstance(variable, int) and 
            self._num_zvariable > 0 and
            self._num_rvariable > 0):
            print('This CDF has both r and z variables. Use variable name')
            return None
        if isinstance(variable, str):
            if self._num_zvariable > 0:
                return self._get_varatts(self._first_zvariable,
                                         self._first_zvariable, variable, 1)
            if self._num_rvariable > 0:
                return self._get_varatts(self._first_rvariable,
                                         self._first_rvariable, variable, 0)
            print('No variable by this name:',variable)
            return None
        elif isinstance(variable, int):
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
                zVar = 1
            else:
                position = self._first_rvariable
                num_variable = self._num_rvariable
                zVar = 0
            if (variable < 0 or variable >= num_variable):
                print('No variable by this number:',variable)
                return None
            for _ in range(0, variable):
                name, next_vdr = self._read_vdr_fast(position)
                position = next_vdr
            vdr_info = self._read_vdr(position)
            return self._read_varatts(variable, zVar)
        else:
            print('Please set variable keyword equal to the name or',
                  '  number of an variable')
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
                print('zVariables:')
                for x in range(0, num_variable):
                    name, next_vdr = self._read_vdr_fast(position)
                    print('  NAME: '+name+' NUMBER: '+str(x))
                    position=next_vdr
            if self._num_rvariable > 0:
                position = self._first_rvariable
                num_variable = self._num_rvariable
                print('rVariables:')
                for x in range(0, num_variable):
                    name, next_vdr = self._read_vdr_fast(position)
                    print('  NAME: '+name+' NUMBER: '+str(x))
                    position=next_vdr

    def _md5_validation(self, file_size):
        '''
        Verifies the MD5 checksum.  
        Only used in the __init__() function
        '''
        md5 = hashlib.md5()
        block_size = 16384
        remaining = file_size
        self.file.seek(0)
        while (remaining > block_size):
            data = self.file.read(block_size)
            remaining = remaining - block_size
            md5.update(data)
        if (remaining > 0):
            data = self.file.read(remaining)
            md5.update(data)
        existing_md5 = self.file.read(16).hex()
        return (md5.hexdigest() == existing_md5)

    def _encoding_token(self, encoding):
        encodings = { 1: 'NETWORK',
                      2: 'SUN',
                      3: 'VAX',
                      4: 'DECSTATION',
                      5: 'SGi',
                      6: 'IBMPC',
                      7: 'IBMRS',
                      9: 'PPC',
                      11: 'HP',
                      12: 'NeXT',
                      13: 'ALPHAOSF1',
                      14: 'ALPHAVMSd',
                      15: 'ALPHAVMSg',
                      16: 'ALPHAVMSi'}
        return encodings[encoding]

    def _major_token(self, major):
        majors = { 1: 'Row_major',
                   2: 'Column_major'}
        return majors[major]

    def _scope_token(self, scope):
        scopes = { 1: 'Global',
                   2: 'Variable'}
        return scopes[scope]

    def _variable_token(self, variable):
        variables = { 3: 'rVariable',
                      8: 'zVariable'}
        return variables[variable]

    def _datatype_token(self, datatype):
        datatypes = { 1: 'CDF_INT1',
                      2: 'CDF_INT2',
                      4: 'CDF_INT4',
                      8: 'CDF_INT8',
                     11: 'CDF_UINT1',
                     12: 'CDF_UINT2',
                     14: 'CDF_UINT4',
                     21: 'CDF_REAL4',
                     22: 'CDF_REAL8',
                     31: 'CDF_EPOCH',
                     32: 'CDF_EPOCH16',
                     33: 'CDF_TIME_TT2000',
                     41: 'CDF_BYTE',
                     44: 'CDF_FLOAT',
                     45: 'CDF_DOUBLE',
                     51: 'CDF_CHAR',
                     52: 'CDF_UCHAR' }
        return datatypes[datatype]

    def _sparse_token(self, sparse):
        sparses = { 0: 'No_sparse',
                    1: 'Pad_sparse',
                    2: 'Prev_sparse'}
        return sparses[sparse]

    def _read_cdr(self, byte_loc):
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big')
        section_type = int.from_bytes(f.read(4),'big')
        gdr_loc=int.from_bytes(f.read(8),'big')
        version=int.from_bytes(f.read(4),'big')
        release=int.from_bytes(f.read(4),'big')
        encoding = int.from_bytes(f.read(4),'big')
        
        #FLAG
        #
        #0 The majority of variable values within a variable record. Variable records are described in Chapter 4. Set indicates row-majority. Clear indicates column-majority.
        #1 The file format of the CDF. Set indicates single-file. Clear indicates multi-file.
        #2 The checksum of the CDF. Set indicates a checksum method is used.
        #3 The MD5 checksum method indicator. Set indicates MD5 method is used for the checksum. Bit 2 must be set.
        #4 Reserved for another checksum method. Bit 2 must be set and bit 3 must be clear .\
        
        flag = int.from_bytes(f.read(4),'big')
        flag_bits = '{0:032b}'.format(flag)
        row_majority = (flag_bits[31]=='1')
        single_format = (flag_bits[30]=='1')
        md5 = (flag_bits[29]=='1' and flag_bits[28]=='1')

        nothing1 = int.from_bytes(f.read(4),'big')
        nothing2 = int.from_bytes(f.read(4),'big')
        increment = int.from_bytes(f.read(4),'big')
        nothing3=int.from_bytes(f.read(4),'big')
        nothing4=int.from_bytes(f.read(4),'big')
        #Copyright, we will always be here at byte 64.  We know the length of the CDR from the GDR offset,
        #so the length to read is 320-64, or 256
        length_of_copyright = byte_loc+(block_size-64)
        #print('length copyright=',length_of_copyright)
        copyright = f.read(length_of_copyright).decode('utf-8')
        copyright = copyright.replace('\x00', '')
        
        cdr_info={}
        cdr_info['encoding'] = encoding
        cdr_info['copyright'] = copyright
        cdr_info['version'] = str(version) + '.' + str(release) + '.' + \
                              str(increment)
        if row_majority:
            cdr_info['majority'] = 1
        else:
            cdr_info['majority'] = 2
        cdr_info['format'] = single_format
        cdr_info['md5'] = md5
        
        return cdr_info
    
    def _read_gdr(self, byte_loc):
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big')
        section_type = int.from_bytes(f.read(4),'big')
        first_rvariable = int.from_bytes(f.read(8),'big', signed=True)
        first_zvariable = int.from_bytes(f.read(8),'big', signed=True)
        first_adr = int.from_bytes(f.read(8),'big', signed=True)
        eof = int.from_bytes(f.read(8),'big', signed=True)
        num_rvariable = int.from_bytes(f.read(4),'big', signed=True)
        num_att = int.from_bytes(f.read(4),'big', signed=True)
        rMaxRec = int.from_bytes(f.read(4),'big', signed=True)
        num_rdim = int.from_bytes(f.read(4),'big', signed=True)
        num_zvariable = int.from_bytes(f.read(4),'big', signed=True)
        first_unused = int.from_bytes(f.read(8),'big', signed=True)
        nothing1 = int.from_bytes(f.read(4),'big', signed=True)
        #YYYMMDD form
        leapsecondlastupdate = int.from_bytes(f.read(4),'big', signed=True)
        nothing2 = int.from_bytes(f.read(4),'big', signed=True)
        
        #rDimSizes, depends on Number of dimensions for r variables
        #A bunch of 4 byte integers in a row.  Length is (size of GDR) - 84
        #In this case. there is nothing
        rdim_sizes=[]
        for _ in range(0, num_rdim):
            rdim_sizes.append(int.from_bytes(f.read(4),'big', signed=True))
        
        gdr_info = {}
        gdr_info['first_zvariable'] = first_zvariable
        gdr_info['first_rvariable'] = first_rvariable
        gdr_info['first_adr'] = first_adr
        gdr_info['num_zvariables'] = num_zvariable
        gdr_info['num_rvariables'] = num_rvariable
        gdr_info['num_attributes'] = num_att 
        gdr_info['rvariables_num_dims'] = num_rdim 
        gdr_info['rvariables_dim_sizes'] = rdim_sizes
        gdr_info['eof'] = eof
        
        return gdr_info
    
    def _get_varatts(self, position, num_variable, variable, zVar):
        for _ in range(0, num_variable):
            name, vdr_next = self._read_vdr_fast(position)
            if name.strip() == variable.strip():
                vdr_info = self._read_vdr(position)
                return self._read_varatts(vdr_info['variable_number'], zVar)
            position = vdr_next

    def _read_globalatts(self):
        f = self.file
        byte_loc = self._first_adr
        return_dict = None
        for _ in range(0, self._num_att):
            f.seek(byte_loc+28, 0)
            scope = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+12, 0)
            next_adr_loc = int.from_bytes(f.read(8),'big', signed=True)
            if (scope != 1):
                #skip variable
                byte_loc = next_adr_loc
                continue
            f.seek(byte_loc+20, 0)
            entry_head = int.from_bytes(f.read(8),'big', signed=True)
            f.seek(byte_loc+36, 0)
            num_entry = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+68, 0) 
            name = str(f.read(256).decode('utf-8'))
            name = name.replace('\x00', '')
            entry = self._get_gaedr(entry_head, num_entry)
            if (entry != None):
                if (return_dict == None):
                    return_dict = {}
                return_dict[name] = entry
            byte_loc = next_adr_loc
 
        return return_dict

    def _read_varatts(self, var_num, zVar):
        f = self.file
        byte_loc = self._first_adr
        return_dict = None
        for _ in range(0, self._num_att):
            f.seek(byte_loc+28, 0)
            scope = int.from_bytes(f.read(4),'big', signed=True)
            num = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+12, 0)
            next_adr_loc = int.from_bytes(f.read(8),'big', signed=True)
            if (scope == 1):
                #skip global
                byte_loc = next_adr_loc
                continue
            if (zVar == 1):
                f.seek(byte_loc+48, 0)
                entry_head = int.from_bytes(f.read(8),'big', signed=True)
                num_entry = int.from_bytes(f.read(4),'big', signed=True)
            else:
                f.seek(byte_loc+20, 0)
                entry_head = int.from_bytes(f.read(8),'big', signed=True)
                f.seek(byte_loc+36, 0)
                num_entry = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+68, 0) 
            #Name
            name = str(f.read(256).decode('utf-8'))
            name = name.replace('\x00', '')
            entry = self._get_vaedr(entry_head, num_entry, var_num)
            if (entry != None):
                if (return_dict == None):
                    return_dict = {}
                return_dict[name] = entry
            byte_loc = next_adr_loc
 
        return return_dict

    def _read_adr(self, byte_loc):
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big')
        #Type of internal record
        section_type = int.from_bytes(f.read(4),'big')
        
        #Position of next ADR
        next_adr_loc = int.from_bytes(f.read(8),'big', signed=True)
        
        #Position of next agrADR
        position_next_gr_entry = int.from_bytes(f.read(8),'big', signed=True)
        
        #Scope, 1 is global 2 is variable
        scope = int.from_bytes(f.read(4),'big', signed=True)
        
        #This attributes number
        num = int.from_bytes(f.read(4),'big', signed=True)
        
        #Number of grEntries
        num_gr_entry=int.from_bytes(f.read(4),'big', signed=True)
        
        #Maximum number of grEntries
        MaxEntry=int.from_bytes(f.read(4),'big', signed=True)
        
        #Literally nothing
        empty1 = int.from_bytes(f.read(4),'big', signed=True)
        
        #File offset to first Attribute zEntry Descriptor Record
        position_next_z_entry =int.from_bytes(f.read(8),'big', signed=True)
        #Number of z entries
        num_z_entry=int.from_bytes(f.read(4),'big', signed=True)
        
        #Maximum number of z entries
        MaxZEntry= int.from_bytes(f.read(4),'big', signed=True)
        
        #Literally nothing
        empty2 = int.from_bytes(f.read(4),'big', signed=True)
        
        #Name
        name = str(f.read(256).decode('utf-8'))
        name = name.replace('\x00', '')
        
        #Build the return dictionary
        return_dict = {}
        #return_dict['section_type'] = section_type
        return_dict['scope'] = scope
        return_dict['next_adr_location'] = next_adr_loc
        return_dict['attribute_number'] = num
        return_dict['num_gr_entry'] = num_gr_entry 
        return_dict['max_gr_entry'] = MaxEntry
        return_dict['num_z_entry'] = num_z_entry 
        return_dict['max_z_entry'] = MaxZEntry
        return_dict['first_z_entry'] = position_next_z_entry
        return_dict['first_gr_entry'] = position_next_gr_entry 
        return_dict['name'] = name
        
        return return_dict

    def _read_adr_fast(self, byte_loc):
        f = self.file
        #Position of next ADR
        f.seek(byte_loc+12, 0)
        next_adr_loc = int.from_bytes(f.read(8),'big', signed=True)
        #Name
        f.seek(byte_loc+68, 0)
        name = str(f.read(256).decode('utf-8'))
        name = name.replace('\x00', '')
        
        return name, next_adr_loc

    def _read_aedr_fast(self, byte_loc):
        f = self.file
        f.seek(byte_loc+12, 0)
        next_aedr = int.from_bytes(f.read(8),'big', signed=True)
        
        #Variable number or global entry number
        f.seek(byte_loc+28, 0)
        entry_num = int.from_bytes(f.read(4),'big', signed=True)
        
        return entry_num, next_aedr
             
    def _read_aedr(self, byte_loc, to_np):
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big')
        section_type = int.from_bytes(f.read(4),'big')     
        next_aedr = int.from_bytes(f.read(8),'big', signed=True)
        
        #Attribute number, should be zero for first one
        att_num = int.from_bytes(f.read(4),'big', signed=True)
        
        #Data type of this attribute
        data_type = int.from_bytes(f.read(4),'big', signed=True)
        
        #Variable number or global entry number
        entry_num = int.from_bytes(f.read(4),'big', signed=True)
        
        #Number of elements
        #Length of string if string, otherwise its the number of numbers
        num_elements = int.from_bytes(f.read(4),'big', signed=True)

        num_strings = int.from_bytes(f.read(4),'big', signed=True)
        if (num_strings < 1):
            num_strings = 1
           
        #Literally nothing
        nothing1 = int.from_bytes(f.read(4),'big', signed=True)
        nothing2 = int.from_bytes(f.read(4),'big', signed=True)
        nothing3 = int.from_bytes(f.read(4),'big', signed=True)
        nothing4 = int.from_bytes(f.read(4),'big', signed=True)
        
        #Always will have 56 bytes before the data
        byte_stream = f.read(block_size - 56)
        if (to_np):
            entry = self._read_data(byte_stream, data_type, 1, num_elements)
        else:
            if (data_type == 51 or data_type == 52):
                entry = str(byte_stream[0:num_elements].decode('utf-8'))
            else:
                if (data_type == 32):
                    #Data type 32 is Epoch16, which is always 2 doubles
                    entry = self._convert_data(byte_stream, data_type, 1,
                                               2, num_elements)
                else:
                    entry = self._convert_data(byte_stream, data_type, 1,
                                               1, num_elements)
        
        return entry, data_type, num_elements, num_strings
             
    def _get_gaedr(self, byte_loc, num_entry):
        f = self.file
        if (num_entry == 0):
            return None
        return_dict = {}
        for _ in range(0, num_entry):
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8),'big')
            f.seek(byte_loc+12, 0)
            next_aedr = int.from_bytes(f.read(8),'big', signed=True)
            f.seek(byte_loc+24, 0)
            data_type = int.from_bytes(f.read(4),'big', signed=True)
            num = int.from_bytes(f.read(4),'big', signed=True)
            num_elements = int.from_bytes(f.read(4),'big', signed=True)
            num_strings = int.from_bytes(f.read(4),'big', signed=True)
            if (num_strings < 1):
                num_strings = 1
            f.seek(byte_loc+56, 0)
            byte_stream = f.read(block_size - 56)
            if (data_type == 51 or data_type == 52):
                if num_strings == 1:
                    return_dict[num] = str(byte_stream[0:num_elements].
                                           decode('utf-8'))
                else:
                    return_dict[num] = str(byte_stream[0:num_elements].
                                           decode('utf-8')).split('\\N ')
            else:
                if (data_type == 32):
                    return_dict[num] = self._convert_data(byte_stream, data_type,
                                                          1, 2, num_elements)
                else:
                    return_dict[num] = self._convert_data(byte_stream, data_type,
                                                          1, 1, num_elements)
            byte_loc = next_aedr
        return return_dict
        
    def _get_vaedr(self, byte_loc, num_entry, var_num):
        f = self.file
        for _ in range(0, num_entry):
            f.seek(byte_loc+28, 0)
            entry_num = int.from_bytes(f.read(4),'big', signed=True)
            if (entry_num != var_num):
                f.seek(byte_loc+12, 0)
                byte_loc = int.from_bytes(f.read(8),'big', signed=True)
                continue
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8),'big')
            f.seek(byte_loc+24, 0)
            data_type = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+32, 0)
            num_elements = int.from_bytes(f.read(4),'big', signed=True)
            num_strings = int.from_bytes(f.read(4),'big', signed=True)
            if (num_strings < 1):
                num_strings = 1
            f.seek(byte_loc+56, 0)
            byte_stream = f.read(block_size - 56)
            if (data_type == 51 or data_type == 52):
                if num_strings == 1:
                    return str(byte_stream[0:num_elements].decode('utf-8'))
                else:
                    return str(byte_stream[0:num_elements].decode('utf-8')).split('\\N ')
            else:
                if (data_type == 32):
                    return self._convert_data(byte_stream, data_type, 1,
                                           2, num_elements)
                else:
                    return self._convert_data(byte_stream, data_type, 1,
                                           1, num_elements)
        return None
        
    def _read_vdr(self, byte_loc):
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big')
        
        #Type of internal record
        section_type = int.from_bytes(f.read(4),'big')
        next_vdr = int.from_bytes(f.read(8),'big', signed=True)
    
        data_type = int.from_bytes(f.read(4),'big', signed=True)
        
        max_rec = int.from_bytes(f.read(4),'big', signed=True)
        
        head_vxr = int.from_bytes(f.read(8),'big', signed=True)
        last_vxr = int.from_bytes(f.read(8),'big', signed=True)
        
        flags = int.from_bytes(f.read(4),'big', signed=True)
        
        flag_bits = '{0:032b}'.format(flags)
        
        record_variance_bool = (flag_bits[31]=='1') 
        pad_bool = (flag_bits[30]=='1')
        compression_bool = (flag_bits[29]=='1') 
        
        sparse = int.from_bytes(f.read(4),'big', signed=True)
        nothing1 = int.from_bytes(f.read(4),'big', signed=True)
        nothing2 = int.from_bytes(f.read(4),'big', signed=True)
        nothing3 = int.from_bytes(f.read(4),'big', signed=True)
    
        num_elements = int.from_bytes(f.read(4),'big', signed=True)
        
        var_num = int.from_bytes(f.read(4),'big', signed=True)
        
        CPRorSPRoffset = int.from_bytes(f.read(8),'big', signed=True)
        
        blocking_factor = int.from_bytes(f.read(4),'big', signed=True)
        
        name = str(f.read(256).decode('utf-8'))
        name = name.replace('\x00', '')
        
        zdim_sizes = []
        dim_sizes = []
        dim_varys = []
        if (section_type == 8):
            #zvariable
            num_dims = int.from_bytes(f.read(4),'big', signed=True)
            for _ in range(0, num_dims):
                zdim_sizes.append(int.from_bytes(f.read(4),'big', signed=True))
            for _ in range(0, num_dims):
                dim_varys.append(int.from_bytes(f.read(4),'big', signed=True))
            adj = 0
            #Check for "False" dimensions, and delete them
            for x in range(0, num_dims):
                y = num_dims - x - 1
                if (dim_varys[y]==0):
                    del zdim_sizes[y]
                    del dim_varys[y]
                    adj = adj + 1
            num_dims = num_dims - adj
        else:
            #rvariable
            for _ in range(0, self._rvariables_num_dims):
                dim_varys.append(int.from_bytes(f.read(4),'big', signed=True))
            for x in range(0, self._rvariables_num_dims):
                if (dim_varys[x]!=0):
                    dim_sizes.append(self._rvariables_dim_sizes[x])
            num_dims = len(dim_sizes)
        #Only set if pad value is in the flags
        if (sparse == 1):
            if pad_bool:
                pad = f.read((block_size - (f.tell() - byte_loc)))
            else:
                pad = self._default_pad(data_type)
        
        return_dict = {}
        return_dict['data_type'] = data_type
        return_dict['section_type'] = section_type
        return_dict['next_vdr_location'] = next_vdr
        return_dict['variable_number'] = var_num
        return_dict['head_vxr'] = head_vxr
        return_dict['last_vxr'] = last_vxr
        return_dict['max_records'] = max_rec
        return_dict['name'] = name
        return_dict['num_dims'] = num_dims
        if (section_type == 8):
            return_dict['dim_sizes'] = zdim_sizes
        else:
            return_dict['dim_sizes'] = dim_sizes
        if (sparse == 1):
            return_dict['pad'] = pad
        return_dict['compression_bool'] = compression_bool
        return_dict['record_vary'] = record_variance_bool
        return_dict['num_elements'] = num_elements
        return_dict['sparse'] = sparse
        
        return return_dict
            
    def _get_Attributes(self):
        f = self.file
        attrs = {}
        byte_loc = self._first_adr
        for x in range(0, self._num_att):
            f.seek(byte_loc+12, 0)
            next_adr = int.from_bytes(f.read(8),'big', signed=True)
            f.seek(byte_loc+28, 0)
            scope = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+68, 0)
            name = str(f.read(256).decode('utf-8'))
            name = name.replace('\x00', '')
            attr = {}
            attr[name] = self._scope_token(int(scope))
            attrs[x] = attr 
            byte_loc = next_adr
        return attrs
            
    def _get_Variables(self, byte_loc, num_vars):
        f = self.file
        vars = {}
        for x in range(0, num_vars):
            f.seek(byte_loc+12, 0)
            next_vdr = int.from_bytes(f.read(8),'big', signed=True)
            f.seek(byte_loc+84, 0)
            name = str(f.read(256).decode('utf-8'))
            name = name.replace('\x00', '')
            vars[x] = name
            byte_loc = next_vdr
        return vars
            
    def _read_vdr_fast(self, byte_loc):
        f = self.file
        f.seek(byte_loc+12, 0)
        next_vdr = int.from_bytes(f.read(8),'big', signed=True)
        f.seek(byte_loc+84, 0)
        name = str(f.read(256).decode('utf-8'))
        name = name.replace('\x00', '')
        return name, next_vdr
            
    def _read_vxrs(self, byte_loc, vvr_offsets=[], vvr_start=[], vvr_end=[]):
        
        f = self.file
        f.seek(byte_loc, 0)
        block_size = int.from_bytes(f.read(8),'big', signed=True)
        #Type of internal record
        section_type = int.from_bytes(f.read(4),'big')
        next_vxr_pos = int.from_bytes(f.read(8),'big', signed=True)
        num_ent = int.from_bytes(f.read(4),'big', signed=True)
        num_ent_used = int.from_bytes(f.read(4),'big', signed=True)

        for ix in range(0, num_ent_used):
            f.seek(byte_loc+28+4*ix, 0)
            num_start = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+28+(4*num_ent)+(4*ix), 0)
            num_end = int.from_bytes(f.read(4),'big', signed=True)
            f.seek(byte_loc+28+(8*num_ent)+(8*ix), 0)
            rec_offset = int.from_bytes(f.read(8),'big', signed=True)
            type_offset = 8 + rec_offset
            f.seek(type_offset, 0)
            next_type = int.from_bytes(f.read(4),'big', signed=True)
            if next_type == 6: 
                vvr_offsets, vvr_start, vvr_end = self._read_vxrs(rec_offset, 
                                                                  vvr_offsets=vvr_offsets, 
                                                                  vvr_start=vvr_start, 
                                                                  vvr_end=vvr_end)
            else: 
                vvr_offsets.extend([rec_offset])
                vvr_start.extend([num_start])
                vvr_end.extend([num_end])
                
        if next_vxr_pos != 0:
            vvr_offsets, vvr_start, vvr_end = self._read_vxrs(next_vxr_pos, 
                                                              vvr_offsets=vvr_offsets, 
                                                              vvr_start=vvr_start, 
                                                              vvr_end=vvr_end)
            
        return vvr_offsets, vvr_start, vvr_end

    def _read_vvrs(self, vdr_dict, vvr_offs, vvr_start, vvr_end, to_np):
        '''
        Reads in all VVRS that are pointed to in the VVR_OFFS array.  
        
        Creates a large byte array of all values called "bytes".
        
        Decodes the bytes, then returns them.  
        '''
        
        
        f = self.file
        numBytes = self._type_size(vdr_dict['data_type'],
                                   vdr_dict['num_elements'])
        numValues = self._num_values(vdr_dict)
        bytes = b''
        
        for vvr_num in range(0, len(vvr_offs)):
            f.seek(vvr_offs[vvr_num], 0)
            block_size = int.from_bytes(f.read(8),'big')
            section_type = int.from_bytes(f.read(4),'big')
            if section_type==7:
                data_size = block_size - 12
            elif section_type==13:
                f.read(12)
                data_size = block_size - 24
            if vvr_num ==0:
                if (vvr_start[vvr_num] != 0):
                    fillRecs = vvr_start[vvr_num]
                    for _ in range(0, fillRecs*numValues):
                        bytes += vdr_dict['pad']
                if section_type==13:
                    bytes += gzip.decompress(f.read(data_size))
                elif section_type==7:
                    bytes += f.read(data_size)
                pre_data = bytes[len(bytes)-numBytes*numValues:]
            else:
                fillRecs = vvr_start[vvr_num] - vvr_end[vvr_num -1] - 1
                if (vdr_dict['sparse']==1):
                    for _ in range(0, fillRecs*numValues):
                        bytes += vdr_dict['pad']
                elif (vdr_dict['sparse']==2):
                    for _ in range(0, fillRecs):
                        bytes += pre_data
                if section_type==13:
                    bytes += gzip.decompress(f.read(data_size))
                elif section_type==7:
                    bytes += f.read(data_size)
                pre_data = bytes[len(bytes)-numBytes*numValues:]
        
        if (to_np):
            y = self._read_data(bytes, vdr_dict['data_type'],
                               vdr_dict['max_records']+1,
                               vdr_dict['num_elements'],
                               dimensions=vdr_dict['dim_sizes'])
        else:
            y = self._convert_data(bytes, vdr_dict['data_type'], 
                                   vdr_dict['max_records']+1,
                                   self._num_values(vdr_dict),
                                   vdr_dict['num_elements'])
        return y

    def _convert_option(self):
        '''
        Determines how to convert CDF byte ordering to the system 
        byte ordering.  
        '''
        
        if sys.byteorder=='little' and self._encoding =='big-endian':
            #big->little
            order = '>'
        elif sys.byteorder=='big' and self._encoding =='little-endian':
            #little->big
            order = '<'
        else:
            #no conversion
            order = '='
        return order

    def _endian(self):
        '''
        Determines endianess of the CDF file
        Only used in __init__
        '''
        if (self._encoding==1 or self._encoding==2 or self._encoding==5 or 
            self._encoding==7 or self._encoding==9 or self._encoding==11 or
            self._encoding==12):
            return 'big-endian'
        else:
            return 'little-endian'

    def _convert_type(self, data_type):
        '''
        CDF data types to python struct data types
        '''
        if (data_type == 1) or (data_type == 41):
            dt_string = 'b'
        elif data_type == 2:
            dt_string = 'h'
        elif data_type == 4:
            dt_string = 'i'
        elif (data_type == 8) or (data_type == 33):
            dt_string = 'q'
        elif data_type == 11:
            dt_string = 'B'
        elif data_type == 12:
            dt_string = 'H'
        elif data_type == 14:
            dt_string = 'I'
        elif (data_type == 21) or (data_type == 44):
            dt_string = 'f'
        elif (data_type == 22) or (data_type == 45) or (data_type == 31):
            dt_string = 'd'
        elif (data_type == 32):
            dt_string = 'd'
        elif (data_type == 51) or (data_type == 52):
            dt_string = 's'
        return dt_string

    def _default_pad(self, data_type):
        '''
        The default pad values by CDF data type 
        '''
        order = self._convert_option()
        if (data_type == 1) or (data_type == 41):
            pad_value = struct.pack(order+'b', -127)
        elif data_type == 2:
            pad_value = struct.pack(order+'h', -32767)
        elif data_type == 4:
            pad_value = struct.pack(order+'i', -2147483647)
        elif (data_type == 8) or (data_type == 33):
            pad_value = struct.pack(order+'q', -9223372036854775807)
        elif data_type == 11:
            pad_value = struct.pack(order+'B', 254)
        elif data_type == 12:
            pad_value = struct.pack(order+'H', 65534)
        elif data_type == 14:
            pad_value = struct.pack(order+'I', 4294967294)
        elif (data_type == 21) or (data_type == 44):
            pad_value = struct.pack(order+'f', -1.0E30)
        elif (data_type == 22) or (data_type == 45) or (data_type == 31):
            pad_value = struct.pack(order+'d', -1.0E30)
        elif (data_type == 32):
            pad_value = struct.pack(order+'d', -1.0E30)
        elif (data_type == 51) or (data_type == 52):
            pad_value = struct.pack(order+'c', ' ')
        return pad_value

    def _convert_data(self, data, data_type, num_recs, num_values, num_elems):
        '''
        Converts byte stream data of type data_type to a list of data.
        '''
        if data_type == 32:
            num_values = num_values*2
        
        if (data_type == 51 or data_type == 52):
            return [data[i:i+num_elems].decode('utf-8') for i in
                    range(0, num_recs*num_values*num_elems, num_elems)]
        else:
            tofrom = self._convert_option()
            dt_string = self._convert_type(data_type)
            form = tofrom + str(num_recs*num_values*num_elems) + dt_string
            value_len = self._type_size(data_type, num_elems)
            return list(struct.unpack_from(form, 
                                           data[0:num_recs*num_values*value_len]))

    def _read_data(self, bytes, data_type, num_recs, num_elems, dimensions=None):
        ##DATA TYPES
        #
        #1 - 1 byte signed int
        #2 - 2 byte signed int
        #4 - 4 byte signed int
        #8 - 8 byte signed int
        #11 - 1 byte unsigned int
        #12 - 2 byte unsigned int
        #14 - 4 byte unsigned int
        #41 - same as 1
        #21 - 4 byte float
        #22 - 8 byte float (double)
        #44 - same as 21
        #45 - same as 22
        #31 - double representing milliseconds
        #32 - 2 doubles representing milliseconds
        #33 - 8 byte signed integer representing nanoseconds from J2000
        #51 - signed character
        #52 - unsigned character
        
        
        #NEED TO CONSTRUCT DATA TYPES FOR ARRAYS
        #
        #SOMETHING LIKE:
        #
        #  dt = np.dtype('>(48,4,16)f4')
        
        #TODO:
        #Do += for all data_types
        
        squeeze_needed = False
        dt_string = self._convert_option()
        if dimensions!=None:
            if (len(dimensions) == 1):
                dimensions.append(1)
                squeeze_needed = True
            dt_string += '(' 
            count = 0
            for dim in dimensions:
                count += 1
                dt_string += str(dim)
                if count < len(dimensions):
                    dt_string += ','
            dt_string += ')'

        if data_type==52 or data_type==51:
            #string
            if dimensions==None:
                ret = bytes[0:num_recs*num_elems].decode('utf-8')
            else:
                count = 1
                for x in range (0, len(dimensions)):
                    count = count * dimensions[x]
                strings = []
                if (len(dimensions) == 0):
                    strings =  [bytes[i:i+num_elems].decode('utf-8') for i in
                                range(0, num_recs*count*num_elems, num_elems)]
                else:
                    for x in range (0, num_recs):
                        onerec = []
                        onerec =  [bytes[i:i+num_elems].decode('utf-8') for i in
                                   range(x*count*num_elems, (x+1)*count*num_elems,
                                        num_elems)]
                        strings.append(onerec)
                ret = strings
            return ret
        else:
            if (data_type == 1) or (data_type == 41):
                dt_string += 'i1'
            elif data_type == 2:
                dt_string += 'i2'
            elif data_type == 4:
                dt_string += 'i4'
            elif (data_type == 8) or (data_type == 33):
                dt_string += 'i8'
            elif data_type == 11:
                dt_string += 'u1'
            elif data_type == 12:
                dt_string += 'u2'
            elif data_type == 14:
                dt_string += 'u4'
            elif (data_type == 21) or (data_type == 44):
                dt_string += 'f'
            elif (data_type == 22) or (data_type == 45) or (data_type == 31):
                dt_string += 'd'
            elif (data_type == 32):
                dt_string += 'c16'
            else:
                print('NOT IMPLEMENTED!!!')
                return
            dt = np.dtype(dt_string)
            ret = np.frombuffer(bytes, dtype=dt, count=num_recs*num_elems)
            ret.setflags('WRITEABLE')
        
        if squeeze_needed:
            ret = np.squeeze(ret)
            
        return ret

    def _type_size(self, data_type, num_elms):
        ##DATA TYPES
        #
        #1 - 1 byte signed int
        #2 - 2 byte signed int
        #4 - 4 byte signed int
        #8 - 8 byte signed int
        #11 - 1 byte unsigned int
        #12 - 2 byte unsigned int
        #14 - 4 byte unsigned int
        #41 - same as 1
        #21 - 4 byte float
        #22 - 8 byte float (double)
        #44 - same as 21
        #45 - same as 22
        #31 - double representing milliseconds
        #32 - 2 doubles representing milliseconds
        #33 - 8 byte signed integer representing nanoseconds from J2000
        #51 - signed character
        #52 - unsigned character
        
        if (data_type == 1) or (data_type == 11) or (data_type == 41):
            return 1
        elif (data_type == 2) or (data_type == 12):
            return 2
        elif (data_type == 4) or (data_type == 14):
            return 4
        elif (data_type == 8) or (data_type == 33):
            return 8
        elif (data_type == 21) or (data_type == 44):
            return 4
        elif (data_type == 22) or (data_type == 31) or (data_type == 45):
            return 8
        elif (data_type == 32):
            return 16
        elif (data_type == 51) or (data_type == 52):
            return num_elms
        else:
            print('NOT IMPLEMENTED!!!')
            return 0
    
    def _num_values(self, vdr_dict):
        '''
        Returns the number of values from a given VDR dictionary
        
        Multiplies the dimension sizes of each dimension in the 
        variable
        '''
        values = 1
        for x in range(0, vdr_dict['num_dims']):
            values = values * vdr_dict['dim_sizes'][x]
        return values
    
    def _get_attdata(self, adr_info, entry_num, num_entry, first_entry, to_np):
        position = adr_info[first_entry]
        for _ in range(0, adr_info[num_entry]):
            got_entry_num, next_aedr = self._read_aedr_fast(position)
            if entry_num == got_entry_num:
                value, data_type, num_elms, num_strs = self._read_aedr(position, to_np)
                if (not to_np):
                    new_dict = {}
                    new_dict['Item_Size'] = self._type_size(data_type, num_elms)
                    new_dict['Data_Type'] = self._datatype_token(data_type)
                    if (data_type == 51 or data_type == 52):
                        new_dict['Num_Items'] = num_strs
                    else:
                        new_dict['Num_Items'] = num_elms
                    if (data_type == 51 or data_type == 52) and (num_strs > 1):
                        new_dict['Data'] = value.split('\\N ')
                    elif (data_type == 32):
                        new_dict['Data'] = complex(value[0], value[1])
                    else:
                        new_dict['Data'] = value
                    return new_dict
                else:
                    if (data_type == 51 or data_type == 52):
                        if (num_strs > 1):
                            return value.split('\\N ')
                        else:
                            return value
                    else:
                        return value
            else:
                position = next_aedr
        print('The entry does not exist')
        return
 
    def _get_vardata(self, position, num_variable, variable,
                     starttime=None, endtime=None, startrec=0, 
                     endrec=None, to_np=False, epoch=None, record_only=False):

        for _ in range(0, num_variable):
            name, vdr_next = self._read_vdr_fast(position)
            if name.strip() == variable.strip():
                vdr_info = self._read_vdr(position)
                if (vdr_info['max_records'] < 0):
                    print('No data is written for this variable')
                    return
                return self._read_vardata(vdr_info, starttime=starttime,
                                          endtime=endtime, startrec=startrec, endrec=endrec, 
                                          to_np=to_np, epoch=epoch, record_only=record_only)
            position = vdr_next
        print('No variable by this name:',variable)
        return None

    def _read_vardata(self, vdr_info, epoch=None, starttime=None, endtime=None,
                      startrec=0, endrec=None, to_np=True, record_only = False):

        #Error checking
        if startrec:
            if (startrec  < 0):
                print('Invalid start recond')
                return None
        
        if endrec:
            if (endrec  < 0) or (endrec > vdr_info['max_records']) or (endrec < startrec):
                print('Invalid end recond')
                return None
        else:
            endrec = vdr_info['max_records']
            
            
        vvr_offsets, vvr_start, vvr_end = self._read_vxrs(vdr_info['head_vxr'], 
                                                          vvr_offsets=[], 
                                                          vvr_start=[], 
                                                          vvr_end=[])
        
        data = self._read_vvrs(vdr_info, vvr_offsets, vvr_start, vvr_end, to_np)

        if (vdr_info['record_vary']):
            #Record varying
            if (starttime != None or endtime != None):
                recs = self._findtimerecords(vdr_info['name'], starttime, endtime, epoch = epoch)
                if (recs == None):
                    return None
                if (isinstance(recs, tuple)):
                    # back from np.where command for CDF_EPOCH and TT2000
                    idx = recs[0]
                    if (len(idx) == 0):
                        #no records in range
                        return None
                    else:
                        startrec = idx[0]
                        endrec = idx[len(idx)-1]
                else:
                    startrec = recs[0]
                    endrec = recs[1]
        else:
            startrec = 0
            endrec = 0
            
        if record_only:
            return [startrec, endrec]
            
        if (not to_np):
            new_dict = {}
            new_dict['Rec_Ndim'] = vdr_info['num_dims']
            new_dict['Rec_Shape'] = vdr_info['dim_sizes']
            new_dict['Num_Records'] = vdr_info['max_records'] + 1
            new_dict['Item_Size'] = self._type_size(vdr_info['data_type'], 
                                                   vdr_info['num_elements'])
            new_dict['Data_Type'] = self._datatype_token(vdr_info['data_type'])
            if (vdr_info['record_vary']):
                num_values = self._num_values(vdr_info)
                if (vdr_info['data_type'] == 32):
                    data2 = data[num_values*startrec*2:
                                 num_values*(endrec+1)*2]
                    datax = []
                    totals = num_values*(endrec-startrec+1)*2
                    for y in range (0, totals, 2):
                        datax.append(complex(data2[y], data2[y+1]))
                    new_dict['Data'] = datax
                else:
                    new_dict['Data'] = data[num_values*startrec:
                                            num_values*(endrec+1)]
            else:
                new_dict['Data'] = data
            return new_dict
        else:
            if (vdr_info['record_vary']):
                return data[startrec:endrec+1]
            else:
                return data

    def _findtimerecords(self, var_name, starttime, endtime, epoch=None):
        
        if (epoch != None):
            vdr_info = self.varinq(epoch)
            if (vdr_info == None):
                print('Epoch not found')
                return None
            if (vdr_info['data_type'] == 31 or vdr_info['data_type'] == 32 or
                vdr_info['data_type'] == 33):
                epochtimes = self.varget(epoch)
        else:
            vdr_info = self.varinq(var_name)
            if (vdr_info['data_type'] == 31 or vdr_info['data_type'] == 32 or
                vdr_info['data_type'] == 33):
                epochtimes = self.varget(var_name)
            else:
                #acquire depend_0 variable
                dependVar = self.attget('DEPEND_0', var_name)
                if (dependVar == None):
                    print('No corresponding epoch from \'DEPEND_0\' attribute ',
                          'for variable:',var_name)
                    print('Use \'epoch\' argument to specify its time-based variable')
                    return None
                vdr_info = self.varinq(dependVar)
                if (vdr_info['data_type'] != 31 and vdr_info['data_type'] != 32
                    and vdr_info['data_type'] != 33):
                    print('Corresponding variable from \'DEPEND_0\' attribute ',
                          'for variable:',var_name,' is not a CDF epoch type')
                    return None
                self._read_vxr(vdr_info['head_vxr'])
                epochtimes = self.varget(dependVar)
                
        return self._findrangerecords(vdr_info['data_type'], epochtimes,
                                      starttime, endtime)

    def _findrangerecords(self, data_type, epochtimes, starttime, endtime):
        if (data_type == 31 or data_type == 32 or data_type == 33):
            #CDF_EPOCH or CDF_EPOCH16 or CDF_TIME_TT2000
            newEpoch = cdfepoch()
            recs = newEpoch.findepochrange(epochtimes, starttime, endtime)
        else:
            print('Not a CDF epoch type...')
            return None
        return recs

