"""
CDF Class
#########

To begin accessing the data within a CDF file, first create a new CDF class.
This can be done with the following commands::

    import cdflib

    cdf_file = cdflib.CDF('/path/to/cdf_file.cdf')

Then, you can call various functions on the variable.  For example::

    x = cdf_file.varget("NameOfVariable", startrec=0, endrec=150)

This command will return all data inside of the variable "Variable1", from
records 0 to 150.

Sample use::


    import cdflib
    swea_cdf_file = cdflib.CDF('/path/to/swea_file.cdf')
    swea_cdf_file.cdf_info()
    x = swea_cdf_file.varget('NameOfVariable')
    swea_cdf_file.close()
    cdflib.cdfread.CDF.getVersion()

@author: Bryan Harter, Michael Liu
"""
import gzip
import hashlib
import os
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

import cdflib.epochs as epoch

__all__ = ['CDF']


class CDF:
    """
    Main CDF class.

    Parameters
    ----------
    path : Path, str
        Path to CDF file.
    validate : bool, optional
        If True, validate the MD5 checksum of the CDF file.
    string_encoding : str, optional
        The encoding used to read strings. Defaults to 'ascii', which is what
        the CDF internal format description prescribes as the encoding for
        character strings. Other encodings may have been used to create files
        however, and this keyword argument gives users the flexibility to read
        those files.
    """
    version = 3
    release = 7
    increment = 0

    def __init__(self, path, validate=False, string_encoding='ascii'):

        path = Path(path).expanduser()
        if not path.is_file():
            path = path.with_suffix('.cdf')
            if not path.is_file():
                raise FileNotFoundError(f'{path} not found')

        self.file = path
        self.string_encoding = string_encoding

        with self.file.open('rb') as f:
            magic_number = f.read(4).hex()
            compressed_bool = f.read(4).hex()

        if magic_number not in ('cdf30001', 'cdf26002', '0000ffff'):
            raise OSError(f'{path} is not a CDF file or a non-supported CDF!')

        self.cdfversion = 3 if magic_number == 'cdf30001' else 2

        self._compressed = not (compressed_bool == '0000ffff')
        self.compressed_file = None
        self.temp_file = None

        if self._compressed:
            self._uncompress_file(path)
            if self.temp_file is None:
                raise OSError("Decompression was unsuccessful.  Only GZIP compression is currently supported.")

            self.compressed_file = self.file
            self.file = self.temp_file

        if (self.cdfversion == 3):
            cdr_info, foffs = self._read_cdr(8)
            gdr_info = self._read_gdr(foffs)
        else:
            cdr_info, foffs = self._read_cdr2(8)
            gdr_info = self._read_gdr2(foffs)

        if cdr_info['md5'] and validate:
            if not self._md5_validation():
                raise OSError('This file fails the md5 checksum.')

        if not cdr_info['format']:
            raise OSError('This package does not support multi-format CDF')

        if cdr_info['encoding'] in (3, 14, 15):
            raise OSError('This package does not support CDFs with this ' +
                          self._encoding_token(cdr_info['encoding']) +
                          ' encoding')

        # SET GLOBAL VARIABLES
        self._post25 = cdr_info['post25']
        self._version = cdr_info['version']
        self._encoding = cdr_info['encoding']
        self._majority = self._major_token(cdr_info['majority'])
        self._copyright = cdr_info['copyright']
        self._md5 = cdr_info['md5']
        self._first_zvariable = gdr_info['first_zvariable']
        self._first_rvariable = gdr_info['first_rvariable']
        self._first_adr = gdr_info['first_adr']
        self._num_zvariable = gdr_info['num_zvariables']
        self._num_rvariable = gdr_info['num_rvariables']
        self._rvariables_num_dims = gdr_info['rvariables_num_dims']
        self._rvariables_dim_sizes = gdr_info['rvariables_dim_sizes']
        self._num_att = gdr_info['num_attributes']
        self._num_rdim = gdr_info['rvariables_num_dims']
        self._rdim_sizes = gdr_info['rvariables_dim_sizes']
        if (self.cdfversion == 3):
            self._leap_second_updated = gdr_info['leapsecond_updated']

        if self.compressed_file is not None:
            self.compressed_file = None

    def __del__(self):
        # This implicitly will delete a temporary uncompressed file if we
        # created it earlier.
        if self.temp_file is not None:
            os.remove(self.temp_file)

    def __getitem__(self, variable: str) -> np.ndarray:
        return self.varget(variable)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def close(self):
        pass

    def cdf_info(self):
        """
        Returns a dictionary that shows the basic CDF information.

        This information includes

                +---------------+--------------------------------------------------------------------------------+
                | ['CDF']       | the name of the CDF                                                            |
                +---------------+--------------------------------------------------------------------------------+
                | ['Version']   | the version of the CDF                                                         |
                +---------------+--------------------------------------------------------------------------------+
                | ['Encoding']  | the endianness of the CDF                                                      |
                +---------------+--------------------------------------------------------------------------------+
                | ['Majority']  | the row/column majority                                                        |
                +---------------+--------------------------------------------------------------------------------+
                | ['zVariables']| a list of the names of the zVariables                                          |
                +---------------+--------------------------------------------------------------------------------+
                | ['rVariables']| a list of the names of the rVariables                                          |
                +---------------+--------------------------------------------------------------------------------+
                | ['Attributes']| a list of dictionary objects that contain {attribute_name : scope}             |
                +---------------+--------------------------------------------------------------------------------+
                | ['Checksum']  | the checksum indicator                                                         |
                +---------------+--------------------------------------------------------------------------------+
                | ['Num_rdim']  | the number of dimensions, applicable only to rVariables                        |
                +---------------+--------------------------------------------------------------------------------+
                | ['rDim_sizes'] | the dimensional sizes, applicable only to rVariables                          |
                +----------------+-------------------------------------------------------------------------------+
                | ['Compressed']| CDF is compressed at the file-level                                            |
                +---------------+--------------------------------------------------------------------------------+
                | ['LeapSecondUpdated']| The last updated for the leap second table, if applicable               |
                +---------------+--------------------------------------------------------------------------------+

        """
        mycdf_info = {}
        mycdf_info['CDF'] = self.file
        mycdf_info['Version'] = self._version
        mycdf_info['Encoding'] = self._encoding
        mycdf_info['Majority'] = self._majority
        mycdf_info['rVariables'], mycdf_info['zVariables'] = self._get_varnames()
        mycdf_info['Attributes'] = self._get_attnames()
        mycdf_info['Copyright'] = self._copyright
        mycdf_info['Checksum'] = self._md5
        mycdf_info['Num_rdim'] = self._num_rdim
        mycdf_info['rDim_sizes'] = self._rdim_sizes
        mycdf_info['Compressed'] = self._compressed
        if (self.cdfversion > 2):
            mycdf_info['LeapSecondUpdated'] = self._leap_second_updated
        return mycdf_info

    def varinq(self, variable):
        """
        Returns a dictionary that shows the basic variable information.

        This information includes
                +-----------------+--------------------------------------------------------------------------------+
                | ['Variable']    | the name of the variable                                                       |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Num']         | the variable number                                                            |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Var_Type']    | the variable type: zVariable or rVariable                                      |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Data_Type']   | the variable's CDF data type                                                   |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Num_Elements']| the number of elements of the variable                                         |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Num_Dims']    | the dimensionality of the variable record                                      |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Dim_Sizes']   | the shape of the variable record                                               |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Sparse']      | the variable's record sparseness                                               |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Last_Rec']    | the maximum written record number (0-based)                                    |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Dim_Vary']    | the dimensional variance(s)                                                    |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Rec_Vary']    | the record variance                                                            |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Pad']         | the padded value if set                                                        |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Compress']    | the GZIP compression level, 0 to 9. 0 if not compressed                        |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Block_Factor']| the blocking factor if the variable is compressed                              |
                +-----------------+--------------------------------------------------------------------------------+

        Parameters
        ----------
        variable :
        """
        vdr_info = self.varget(variable=variable, inq=True)
        if vdr_info is None:
            raise KeyError(f"Variable {variable} not found.")

        var = {}
        var['Variable'] = vdr_info['name']
        var['Num'] = vdr_info['variable_number']
        var['Var_Type'] = self._variable_token(vdr_info['section_type'])
        var['Data_Type'] = vdr_info['data_type']
        var['Data_Type_Description'] = self._datatype_token(vdr_info['data_type'])
        var['Num_Elements'] = vdr_info['num_elements']
        var['Num_Dims'] = vdr_info['num_dims']
        var['Dim_Sizes'] = vdr_info['dim_sizes']
        var['Sparse'] = self._sparse_token(vdr_info['sparse'])
        var['Last_Rec'] = vdr_info['max_records']
        var['Rec_Vary'] = vdr_info['record_vary']
        var['Dim_Vary'] = vdr_info['dim_vary']
        if ('pad' in vdr_info):
            var['Pad'] = vdr_info['pad']
        var['Compress'] = vdr_info['compression_level']
        if ('blocking_factor' in vdr_info):
            var['Block_Factor'] = vdr_info['blocking_factor']

        return var

    def attinq(self, attribute=None):
        """
        Get attribute information.

        Parameters
        ----------
        attribute : str, int
            Attribute to get information for.

        Returns
        -------
        dict
            Dictionary of attribution infromation.
        """
        position = self._first_adr
        if isinstance(attribute, str):
            for _ in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                if name.strip().lower() == attribute.strip().lower():
                    return self._read_adr(position)

                position = next_adr
            raise KeyError(f'No attribute {attribute}')

        elif isinstance(attribute, int):
            if (attribute < 0 or attribute > self._num_zvariable):
                raise KeyError(f'No attribute {attribute}')
            for _ in range(0, attribute):
                name, next_adr = self._read_adr_fast(position)
                position = next_adr

            return self._read_adr(position)
        else:
            raise ValueError('attribute keyword must be a string or integer')

    def print_attrs(self):
        """
        Print all attribute information.
        """
        attrs = self._get_attnames()
        print(attrs)
        for x in range(0, self._num_att):
            name = list(attrs[x].keys())[0]
            print('NAME: ' + name + ', NUMBER: ' + str(x) + ', SCOPE: ' + attrs[x][name])
        return attrs

    def attget(self, attribute=None, entry=None, to_np=True):
        """
        Returns the value of the attribute at the entry number provided.

        A variable name can be used instead of its corresponding
        entry number.

        Parameters
        ----------
        attribute : str, int, optional
            Attribute name or number to get.
        entry : int, optional
        tp_np : bool, optional
            If True, return a numpy array.

        Returns
        -------
        dict
            A dictionary is returned with the following defined keys

            +-----------------+--------------------------------------------------------------------------------+
            | ['Item_Size']   | the number of bytes for each entry value                                       |
            +-----------------+--------------------------------------------------------------------------------+
            | ['Num_Items']   | total number of values extracted                                               |
            +-----------------+--------------------------------------------------------------------------------+
            | ['Data_Type']   | the CDF data type                                                              |
            +-----------------+--------------------------------------------------------------------------------+
            | ['Data']        | retrieved attribute data as a scalar value, a numpy array or a string          |
            +-----------------+--------------------------------------------------------------------------------+

        """
        # Starting position
        position = self._first_adr

        # Get Correct ADR
        adr_info = None
        if isinstance(attribute, str):
            for _ in range(0, self._num_att):
                name, next_adr = self._read_adr_fast(position)
                if name.strip().lower() == attribute.strip().lower():
                    adr_info = self._read_adr(position)
                    if isinstance(entry, str) and adr_info['scope'] == 1:
                        # If the user has specified a string entry, they are obviously looking for a variable attribute.
                        # Filter out any global attributes that may have the same name.
                        adr_info = None
                        position = next_adr
                        continue
                    break
                else:
                    position = next_adr

            if adr_info is None:
                raise KeyError(f'No attribute {attribute} for entry {entry}')

        elif isinstance(attribute, int):
            if (attribute < 0) or (attribute > self._num_att):
                raise KeyError(f'No attribute {attribute}')
            if not isinstance(entry, int):
                raise TypeError(f'{entry} has to be a number.')

            for _ in range(0, attribute):
                name, next_adr = self._read_adr_fast(position)
                position = next_adr
            adr_info = self._read_adr(position)
        else:
            raise ValueError('Please set attribute keyword equal to '
                             'the name or number of an attribute')

        # Find the correct entry from the "entry" variable
        if adr_info['scope'] == 1:
            if not isinstance(entry, int):
                raise ValueError('"entry" must be an integer')
            num_entry_string = 'num_gr_entry'
            first_entry_string = 'first_gr_entry'
            max_entry_string = 'max_gr_entry'
            entry_num = entry
        else:
            var_num = -1
            zvar = False
            if isinstance(entry, str):
                # a zVariable?
                positionx = self._first_zvariable
                for x in range(0, self._num_zvariable):
                    name, vdr_next = self._read_vdr_fast(positionx)
                    if (name.strip().lower() == entry.strip().lower()):
                        var_num = x
                        zvar = True
                        break
                    positionx = vdr_next
                if var_num == -1:
                    # a rVariable?
                    positionx = self._first_rvariable
                    for x in range(0, self._num_rvariable):
                        name, vdr_next = self._read_vdr_fast(positionx)
                        if (name.strip().lower() == entry.strip().lower()):
                            var_num = x
                            break
                        positionx = vdr_next
                if var_num == -1:
                    raise ValueError(
                        f'No variable by this name: {entry}')
                entry_num = var_num
            else:
                if (self._num_zvariable > 0 and self._num_rvariable > 0):
                    raise ValueError('This CDF has both r and z variables. '
                                     'Use variable name instead')
                if self._num_zvariable > 0:
                    zvar = True
                entry_num = entry
            if zvar:
                num_entry_string = 'num_z_entry'
                first_entry_string = 'first_z_entry'
                max_entry_string = 'max_z_entry'
            else:
                num_entry_string = 'num_gr_entry'
                first_entry_string = 'first_gr_entry'
                max_entry_string = 'max_gr_entry'
        if entry_num > adr_info[max_entry_string]:
            raise ValueError('The entry does not exist')
        return self._get_attdata(adr_info, entry_num, adr_info[num_entry_string],
                                 adr_info[first_entry_string], to_np=to_np)

    def varget(self, variable=None, epoch=None, starttime=None,
               endtime=None, startrec=0, endrec=None,
               record_range_only=False, inq=False, expand=False,
               to_np=True):
        """
        Returns the variable data.

        Parameters
        ----------
        variable: str
            Variable name to fetch.
        startrec: int
            Index of the first record to get.
        endrec : int
            Index of the last record to get. All records from *startrec* to
            *endrec* inclusive are fetched.

        Notes
        -----
        Variable can be entered either
        a name or a variable number. By default, it returns a
        'numpy.ndarray' or 'list' class object, depending on the
        data type, with the variable data and its specification.

        If "expand" is set as True, a dictionary is returned
        with the following defined keys for the output

                +-----------------+--------------------------------------------------------------------------------+
                | ['Rec_Ndim']         | the dimension number of each variable record                              |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Rec_Shape']        | the shape of the variable record dimensions                               |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Num_Records']      | the total number of records                                               |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Records_Returned'] | the number of records retrieved                                           |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Data_Type']        | the CDF data type                                                         |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Data']             | retrieved variable data                                                   |
                +-----------------+--------------------------------------------------------------------------------+
                | ['Real_Records']     | Record numbers for real data for sparse record variable in list           |
                +-----------------+--------------------------------------------------------------------------------+

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

        The start (and end) time should be presented in a list as:
        [year month day hour minute second millisec] for CDF_EPOCH
        [year month day hour minute second millisec microsec nanosec picosec] for CDF_EPOCH16
        [year month day hour minute second millisec microsec nanosec] for CDF_TIME_TT2000
        If not enough time components are presented, only the last item can have the floating
        portion for the sub-time components.

        Note: CDF's CDF_EPOCH16 data type uses 2 8-byte doubles for each data value.
        In Python, each value is presented as a complex or numpy.complex128.
        """
        if (isinstance(variable, int) and self._num_zvariable > 0 and
                self._num_rvariable > 0):
            raise ValueError('This CDF has both r and z variables. '
                             'Use variable name instead')

        if ((starttime is not None or endtime is not None) and
                (startrec != 0 or endrec is not None)):
            raise ValueError('Can\'t specify both time and record range')

        if isinstance(variable, str):
            # Check z variables for the name, then r variables
            position = self._first_zvariable
            num_variables = self._num_zvariable
            vdr_info = None
            for zVar in [1, 0]:
                for _ in range(0, num_variables):
                    name, vdr_next = self._read_vdr_fast(position)
                    if name.strip().lower() == variable.strip().lower():
                        vdr_info = self._read_vdr(position)
                        break
                    position = vdr_next
                position = self._first_rvariable
                num_variables = self._num_rvariable
            if vdr_info is None:
                raise ValueError(f"Variable name '{variable}' not found.")
        elif isinstance(variable, int):
            if self._num_zvariable > 0:
                position = self._first_zvariable
                num_variable = self._num_zvariable
                # zVar = True
            elif self._num_rvariable > 0:
                position = self._first_rvariable
                num_variable = self._num_rvariable
                # zVar = False
            if (variable < 0 or variable >= num_variable):
                raise ValueError(
                    f'No variable by this number: {variable}')
            for _ in range(0, variable):
                name, next_vdr = self._read_vdr_fast(position)
                position = next_vdr
            vdr_info = self._read_vdr(position)
        else:
            raise ValueError('Please set variable keyword equal to '
                             'the name or number of an variable')

        if inq:
            return vdr_info
        else:
            if (vdr_info['max_records'] < 0):
                raise ValueError(f'No records found for variable {variable}')

            return self._read_vardata(vdr_info, epoch=epoch, starttime=starttime, endtime=endtime,
                                      startrec=startrec, endrec=endrec, record_range_only=record_range_only,
                                      expand=expand, to_np=to_np)

    def epochrange(self, epoch=None, starttime=None, endtime=None):
        """
        Get epoch range.

        Returns a list of the record numbers, representing the
        corresponding starting and ending records within the time
        range from the epoch data. A None is returned if there is no
        data either written or found in the time range.

        Parameters
        ----------
        epoch :
        starttime :
        endtime :
        """
        return self.varget(variable=epoch, starttime=starttime,
                           endtime=endtime, record_range_only=True)

    def globalattsget(self, expand=False, to_np=True):
        """
        Gets all global attributes.

        This function returns all of the global attribute entries,
        in a dictionary (in the form of ``'attribute': {entry: value}``
        pairs) from a CDF. If there is no entry found, None is
        returned. If expand is entered with non-False, then each
        entry's data type is also returned in a list form as
        [entry, 'CDF_xxxx']. For attributes without any entries,
        they will also return with ``None`` value.

        Parameters
        ----------
        expand : bool, optional
        to_np : bool, optional
            If True, return a numpy array.
        """
        byte_loc = self._first_adr
        return_dict = {}
        for _ in range(self._num_att):
            adr_info = self._read_adr(byte_loc)

            if (adr_info['scope'] != 1):
                byte_loc = adr_info['next_adr_location']
                continue
            if (adr_info['num_gr_entry'] == 0):
                if (expand is not False):
                    return_dict[adr_info['name']] = None
                byte_loc = adr_info['next_adr_location']
                continue
            if (expand is False):
                entries = []
            else:
                entries = {}
            aedr_byte_loc = adr_info['first_gr_entry']
            for _ in range(adr_info['num_gr_entry']):
                aedr_info = self._read_aedr(aedr_byte_loc, to_np=to_np)
                entryData = aedr_info['entry']
                if (expand is False):
                    entries.append(entryData)
                else:
                    entryWithType = []
                    if (isinstance(entryData, str)):
                        entryWithType.append(entryData)
                    else:
                        dataType = aedr_info['data_type']
                        if (len(entryData.tolist()) == 1):
                            if (dataType != 31 and dataType != 32 and dataType != 33):
                                entryWithType.append(entryData.tolist()[0])
                            else:
                                if (dataType != 33):
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()[0],
                                                                               iso_8601=False))
                                else:
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()[0]))
                        else:
                            if (dataType != 31 and dataType != 32 and dataType != 33):
                                entryWithType.append(entryData.tolist())
                            else:
                                if (dataType != 33):
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist(),
                                                                               iso_8601=False))
                                else:
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()))
                    entryWithType.append(self._datatype_token(aedr_info['data_type']))
                    entries[aedr_info['entry_num']] = entryWithType
                aedr_byte_loc = aedr_info['next_aedr']

            if (len(entries) != 0):
                if (expand is False):
                    if (len(entries) == 1):
                        return_dict[adr_info['name']] = entries[0]
                    else:
                        return_dict[adr_info['name']] = entries
                else:
                    return_dict[adr_info['name']] = entries
            byte_loc = adr_info['next_adr_location']

        return return_dict

    def varattsget(self, variable=None, expand=False, to_np=True):
        """
        Gets all variable attributes.

        Unlike attget, which returns a single attribute entry value,
        this function returns all of the variable attribute entries,
        in a dictionary (in the form of 'attribute': value pair) for
        a variable. If there is no entry found, None is returned.
        If no variable name is provided, a list of variables are printed.
        If expand is entered with non-False, then each entry's data
        type is also returned in a list form as [entry, 'CDF_xxxx'].
        For attributes without any entries, they will also return with
        None value.

        Parameters
        ----------
        variable :
        expand : bool, optional
        to_np: bool, optional
            If True, return a numpy array.
        """
        if (isinstance(variable, int) and self._num_zvariable > 0 and self._num_rvariable > 0):
            raise ValueError('This CDF has both r and z variables. Use variable name')
        if isinstance(variable, str):
            position = self._first_zvariable
            num_variables = self._num_zvariable
            for zVar in [1, 0]:
                for _ in range(0, num_variables):
                    name, vdr_next = self._read_vdr_fast(position)
                    if name.strip().lower() == variable.strip().lower():
                        vdr_info = self._read_vdr(position)
                        return self._read_varatts(vdr_info['variable_number'], zVar, expand, to_np=to_np)
                    position = vdr_next
                position = self._first_rvariable
                num_variables = self._num_rvariable
            raise ValueError(f'No variable by this name: {variable}')
        elif isinstance(variable, int):
            if self._num_zvariable > 0:
                num_variable = self._num_zvariable
                zVar = True
            else:
                num_variable = self._num_rvariable
                zVar = False
            if (variable < 0 or variable >= num_variable):
                raise ValueError(f'No variable by this number: {variable}')
            return self._read_varatts(variable, zVar, expand, to_np=to_np)
        else:
            raise ValueError('Please set variable keyword equal to '
                             'the name or number of an variable')

    def _uncompress_file(self, path):
        """
        Writes the current file into a file in the temporary directory.

        If that doesn't work, create a new file in the CDFs directory.
        """

        with self.file.open('rb') as f:
            if (self.cdfversion == 3):
                data_start, data_size, cType, _ = self._read_ccr(8)
            else:
                data_start, data_size, cType, _ = self._read_ccr2(8)

            if cType != 5:
                return
            f.seek(data_start)
            decompressed_data = gzip.decompress(f.read(data_size))

        self.temp_file = Path(tempfile.NamedTemporaryFile(suffix='.cdf').name)
        with self.temp_file.open('wb') as g:
            g.write(bytearray.fromhex('cdf30001'))
            g.write(bytearray.fromhex('0000ffff'))
            g.write(decompressed_data)

    def _read_ccr(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            f.seek(byte_loc+12)
            cproffset = int.from_bytes(f.read(8), 'big')

        data_start = byte_loc + 32
        data_size = block_size - 32
        cType, cParams = self._read_cpr(cproffset)

        return data_start, data_size, cType, cParams

    def _read_ccr2(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            f.seek(byte_loc+8)
            cproffset = int.from_bytes(f.read(4), 'big')

        data_start = byte_loc + 20
        data_size = block_size - 20
        cType, cParams = self._read_cpr2(cproffset)

        return data_start, data_size, cType, cParams

    def _read_cpr(self, byte_loc):
        if self.cdfversion == 3:
            return self._read_cpr3(byte_loc)
        else:
            return self._read_cpr2(byte_loc)

    def _read_cpr3(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            cpr = f.read(block_size-8)

        cType = int.from_bytes(cpr[4:8], 'big')
        cParams = int.from_bytes(cpr[16:20], 'big')

        return cType, cParams

    def _read_cpr2(self, byte_loc):

        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            cpr = f.read(block_size-4)

        cType = int.from_bytes(cpr[4:8], 'big')
        cParams = int.from_bytes(cpr[16:20], 'big')

        return cType, cParams

    def _md5_validation(self) -> bool:
        """
        Verifies the MD5 checksum.
        Only used in the __init__() function
        """
        fn = self.file if self.compressed_file is None else self.compressed_file

        md5 = hashlib.md5()
        block_size = 16384
        with fn.open('rb') as f:
            f.seek(-16, 2)
            remaining = f.tell()  # File size minus checksum size
            f.seek(0)
            while (remaining > block_size):
                data = f.read(block_size)
                remaining = remaining - block_size
                md5.update(data)

            if (remaining > 0):
                data = f.read(remaining)
                md5.update(data)

            existing_md5 = f.read(16).hex()

        return md5.hexdigest() == existing_md5

    @staticmethod
    def _encoding_token(encoding):
        encodings = {1: 'NETWORK',
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

    @staticmethod
    def _major_token(major):
        majors = {1: 'Row_major',
                  2: 'Column_major'}
        return majors[major]

    @staticmethod
    def _scope_token(scope):
        scopes = {1: 'Global',
                  2: 'Variable'}
        return scopes[scope]

    @staticmethod
    def _variable_token(variable):
        variables = {3: 'rVariable',
                     8: 'zVariable'}
        return variables[variable]

    @staticmethod
    def _datatype_token(datatype):
        datatypes = {1: 'CDF_INT1',
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
                     52: 'CDF_UCHAR'}
        return datatypes[datatype]

    @staticmethod
    def _sparse_token(sparse):
        sparses = {0: 'No_sparse',
                   1: 'Pad_sparse',
                   2: 'Prev_sparse'}
        return sparses[sparse]

    def _get_varnames(self):
        zvars = []
        rvars = []
        if self._num_zvariable > 0:
            position = self._first_zvariable
            num_variable = self._num_zvariable
            for _ in range(0, num_variable):
                name, next_vdr = self._read_vdr_fast(position)
                zvars.append(name)
                position = next_vdr
        if self._num_rvariable > 0:
            position = self._first_rvariable
            num_variable = self._num_rvariable
            for _ in range(0, num_variable):
                name, next_vdr = self._read_vdr_fast(position)
                rvars.append(name)
                position = next_vdr
        return rvars, zvars

    def _get_attnames(self):
        attrs = []
        position = self._first_adr
        for _ in range(0, self._num_att):
            attr = {}
            adr_info = self._read_adr(position)
            attr[adr_info['name']] = self._scope_token(int(adr_info['scope']))
            attrs.append(attr)
            position = adr_info['next_adr_location']
        return attrs

    def _read_cdr(self, byte_loc: int):
        """
        Read a CDF descriptor record (CDR).
        """
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            cdr = f.read(block_size-8)
            foffs = f.tell()
        # _ = int.from_bytes(cdr[0:4],'big') #Section Type
        # gdroff = int.from_bytes(cdr[4:12], 'big')  # GDR Location
        version = int.from_bytes(cdr[12:16], 'big')
        if version not in (2, 3):
            raise ValueError(f'CDF version {version} not handled')

        release = int.from_bytes(cdr[16:20], 'big')
        encoding = int.from_bytes(cdr[20:24], 'big')

        # FLAG
        #
        # 0 The majority of variable values within a variable record.
        #   Variable records are described in Chapter 4. Set indicates
        #   row-majority. Clear indicates column-majority.
        # 1 The file format of the CDF. Set indicates single-file.
        #   Clear indicates multi-file.
        # 2 The checksum of the CDF. Set indicates a checksum method is used.
        # 3 The MD5 checksum method indicator.
        #   Set indicates MD5 method is used for the checksum. Bit 2 must be set.
        # 4 Reserved for another checksum method.
        #   Bit 2 must be set and bit 3 must be clear.

        flag = int.from_bytes(cdr[24:28], 'big')
        flag_bits = f'{flag:032b}'
        row_majority = (flag_bits[31] == '1')
        single_format = (flag_bits[30] == '1')
        md5 = (flag_bits[29] == '1' and flag_bits[28] == '1')
        increment = int.from_bytes(cdr[36:40], 'big')
        cdfcopyright = cdr[48:].decode(self.string_encoding)
        cdfcopyright = cdfcopyright.replace('\x00', '')

        cdr_info = {}
        cdr_info['encoding'] = encoding
        cdr_info['copyright'] = cdfcopyright
        cdr_info['version'] = str(version) + '.' + str(release) + '.' +  \
            str(increment)
        if row_majority:
            cdr_info['majority'] = 1
        else:
            cdr_info['majority'] = 2
        cdr_info['format'] = single_format
        cdr_info['md5'] = md5
        cdr_info['post25'] = True

        return cdr_info, foffs

    def _read_cdr2(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            cdr = f.read(block_size-4)
            foffs = f.tell()

        # gdroff = int.from_bytes(cdr[4:8], 'big')  # GDR Location
        version = int.from_bytes(cdr[8:12], 'big')
        release = int.from_bytes(cdr[12:16], 'big')
        encoding = int.from_bytes(cdr[16:20], 'big')
        flag = int.from_bytes(cdr[20:24], 'big')
        flag_bits = f'{flag:032b}'
        row_majority = (flag_bits[31] == '1')
        single_format = (flag_bits[30] == '1')
        md5 = (flag_bits[29] == '1' and flag_bits[28] == '1')
        increment = int.from_bytes(cdr[32:36], 'big')
        cdfcopyright = cdr[44:].decode(self.string_encoding)
        cdfcopyright = cdfcopyright.replace('\x00', '')

        cdr_info = {}
        cdr_info['encoding'] = encoding
        cdr_info['copyright'] = cdfcopyright
        cdr_info['version'] = str(version) + '.' + str(release) + '.' + \
            str(increment)
        if row_majority:
            cdr_info['majority'] = 1
        else:
            cdr_info['majority'] = 2
        cdr_info['format'] = single_format
        cdr_info['md5'] = md5
        if (version == 2 and release >= 5):
            cdr_info['post25'] = True
        else:
            cdr_info['post25'] = False

        return cdr_info, foffs

    def _read_gdr(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')  # Block Size
            gdr = f.read(block_size-8)

        first_rvariable = int.from_bytes(gdr[4:12], 'big', signed=True)
        first_zvariable = int.from_bytes(gdr[12:20], 'big', signed=True)
        first_adr = int.from_bytes(gdr[20:28], 'big', signed=True)
        eof = int.from_bytes(gdr[28:36], 'big', signed=True)
        num_rvariable = int.from_bytes(gdr[36:40], 'big', signed=True)
        num_att = int.from_bytes(gdr[40:44], 'big', signed=True)
        num_rdim = int.from_bytes(gdr[48:52], 'big', signed=True)
        num_zvariable = int.from_bytes(gdr[52:56], 'big', signed=True)
        leapSecondlastUpdated = int.from_bytes(gdr[68:72], 'big', signed=True)
        # rDimSizes, depends on Number of dimensions for r variables
        # A bunch of 4 byte integers in a row.  Length is (size of GDR) - 84
        # In this case. there is nothing
        rdim_sizes = []
        for x in range(0, num_rdim):
            ioff = 76 + x * 4
            rdim_sizes.append(int.from_bytes(gdr[ioff:ioff+4], 'big',
                                             signed=True))

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
        gdr_info['leapsecond_updated'] = leapSecondlastUpdated

        return gdr_info

    def _read_gdr2(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')  # Block Size
            gdr = f.read(block_size-4)

        first_rvariable = int.from_bytes(gdr[4:8], 'big', signed=True)
        first_zvariable = int.from_bytes(gdr[8:12], 'big', signed=True)
        first_adr = int.from_bytes(gdr[12:16], 'big', signed=True)
        eof = int.from_bytes(gdr[16:20], 'big', signed=True)
        num_rvariable = int.from_bytes(gdr[20:24], 'big', signed=True)
        num_att = int.from_bytes(gdr[24:28], 'big', signed=True)
        num_rdim = int.from_bytes(gdr[32:36], 'big', signed=True)
        num_zvariable = int.from_bytes(gdr[36:40], 'big', signed=True)
        rdim_sizes = []
        for x in range(0, num_rdim):
            ioff = 56 + x * 4
            rdim_sizes.append(int.from_bytes(gdr[ioff:ioff+4], 'big',
                                             signed=True))

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

    def _read_varatts(self, var_num, zVar, expand, to_np=True):
        byte_loc = self._first_adr
        return_dict = {}
        for z in range(0, self._num_att):
            adr_info = self._read_adr(byte_loc)
            if (adr_info['scope'] == 1):
                byte_loc = adr_info['next_adr_location']
                continue
            if (zVar):
                byte_loc = adr_info['first_z_entry']
                num_entry = adr_info['num_z_entry']
            else:
                byte_loc = adr_info['first_gr_entry']
                num_entry = adr_info['num_gr_entry']
            found = 0
            for _ in range(0, num_entry):
                entryNum, byte_next = self._read_aedr_fast(byte_loc)
                if (entryNum != var_num):
                    byte_loc = byte_next
                    continue
                aedr_info = self._read_aedr(byte_loc, to_np=to_np)
                entryData = aedr_info['entry']
                if (expand is False):
                    return_dict[adr_info['name']] = entryData
                else:
                    entryWithType = []
                    if (isinstance(entryData, str)):
                        entryWithType.append(entryData)
                    else:
                        dataType = aedr_info['data_type']
                        if (dataType != 31 and dataType != 32 and dataType != 33):
                            if (len(entryData.tolist()) == 1):
                                entryWithType.append(entryData.tolist()[0])
                            else:
                                entryWithType.append(entryData.tolist())
                        else:
                            if (len(entryData.tolist()) == 1):
                                if (dataType != 33):
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()[0],
                                                                               iso_8601=False))
                                else:
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()[0]))
                            else:
                                if (dataType != 33):
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist(),
                                                                               iso_8601=False))
                                else:
                                    entryWithType.append(epoch.CDFepoch.encode(entryData.tolist()))
                    entryWithType.append(self._datatype_token(aedr_info['data_type']))
                    return_dict[adr_info['name']] = entryWithType
                found = 1
                break
            byte_loc = adr_info['next_adr_location']
            if (found == 0 and expand is not False):
                return_dict[adr_info['name']] = None
        return return_dict

    def _read_adr(self, position):
        """
        Read an attribute descriptor record (ADR).
        """
        if (self.cdfversion == 3):
            return self._read_adr3(position)
        else:
            return self._read_adr2(position)

    def _read_adr3(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')  # Block Size
            adr = f.read(block_size - 8)
        next_adr_loc = int.from_bytes(adr[4:12], 'big', signed=True)
        position_next_gr_entry = int.from_bytes(adr[12:20], 'big', signed=True)
        scope = int.from_bytes(adr[20:24], 'big', signed=True)
        num = int.from_bytes(adr[24:28], 'big', signed=True)
        num_gr_entry = int.from_bytes(adr[28:32], 'big', signed=True)
        MaxEntry = int.from_bytes(adr[32:36], 'big', signed=True)
        position_next_z_entry = int.from_bytes(adr[40:48], 'big', signed=True)
        num_z_entry = int.from_bytes(adr[48:52], 'big', signed=True)
        MaxZEntry = int.from_bytes(adr[52:56], 'big', signed=True)

        name = str(adr[60:315].decode(self.string_encoding))
        name = name.replace('\x00', '')

        # Build the return dictionary
        return_dict = {}
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

    def _read_adr2(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')  # Block Size
            adr = f.read(block_size - 4)

        next_adr_loc = int.from_bytes(adr[4:8], 'big', signed=True)
        position_next_gr_entry = int.from_bytes(adr[8:12], 'big', signed=True)
        scope = int.from_bytes(adr[12:16], 'big', signed=True)
        num = int.from_bytes(adr[16:20], 'big', signed=True)
        num_gr_entry = int.from_bytes(adr[20:24], 'big', signed=True)
        MaxEntry = int.from_bytes(adr[24:28], 'big', signed=True)
        position_next_z_entry = int.from_bytes(adr[32:36], 'big', signed=True)
        num_z_entry = int.from_bytes(adr[36:40], 'big', signed=True)
        MaxZEntry = int.from_bytes(adr[40:44], 'big', signed=True)

        name = str(adr[48:112].decode(self.string_encoding))
        name = name.replace('\x00', '')

        # Build the return dictionary
        return_dict = {}
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

    def _read_adr_fast(self, position):
        """
        Read an attribute descriptor record (ADR).
        """
        if (self.cdfversion == 3):
            return self._read_adr_fast3(position)
        else:
            return self._read_adr_fast2(position)

    def _read_adr_fast3(self, byte_loc):
        with self.file.open('rb') as f:
            # Position of next ADR
            f.seek(byte_loc + 12, 0)
            next_adr_loc = int.from_bytes(f.read(8), 'big', signed=True)
            # Name
            f.seek(byte_loc + 68, 0)
            name = str(f.read(256).decode(self.string_encoding))

        name = name.replace('\x00', '')

        return name, next_adr_loc

    def _read_adr_fast2(self, byte_loc):
        with self.file.open('rb') as f:
            # Position of next ADR
            f.seek(byte_loc + 8, 0)
            next_adr_loc = int.from_bytes(f.read(4), 'big', signed=True)
            # Name
            f.seek(byte_loc + 52, 0)
            name = str(f.read(64).decode(self.string_encoding))

        name = name.replace('\x00', '')

        return name, next_adr_loc

    def _read_aedr_fast(self, byte_loc):
        if self.cdfversion == 3:
            return self._read_aedr_fast3(byte_loc)
        else:
            return self._read_aedr_fast2(byte_loc)

    def _read_aedr_fast3(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc + 12, 0)
            next_aedr = int.from_bytes(f.read(8), 'big', signed=True)

            # Variable number or global entry number
            f.seek(byte_loc + 28, 0)
            entry_num = int.from_bytes(f.read(4), 'big', signed=True)

        return entry_num, next_aedr

    def _read_aedr_fast2(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc + 8, 0)
            next_aedr = int.from_bytes(f.read(4), 'big', signed=True)

            # Variable number or global entry number
            f.seek(byte_loc+20, 0)
            entry_num = int.from_bytes(f.read(4), 'big', signed=True)

        return entry_num, next_aedr

    def _read_aedr(self, byte_loc, to_np=True):
        if self.cdfversion == 3:
            return self._read_aedr3(byte_loc, to_np)
        else:
            return self._read_aedr2(byte_loc, to_np)

    def _read_aedr3(self, byte_loc, to_np=True):
        """
        Reads an Attribute Entry Descriptor Record at a specific byte location.

        """
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            aedr = f.read(block_size-8)

        next_aedr = int.from_bytes(aedr[4:12], 'big', signed=True)
        data_type = int.from_bytes(aedr[16:20], 'big', signed=True)

        # Variable number or global entry number
        entry_num = int.from_bytes(aedr[20:24], 'big', signed=True)

        # Number of elements
        # Length of string if string, otherwise its the number of numbers
        num_elements = int.from_bytes(aedr[24:28], 'big', signed=True)

        # Supposed to be reserved space
        num_strings = int.from_bytes(aedr[28:32], 'big', signed=True)
        if (num_strings < 1):
            num_strings = 1

        # Literally nothing
        # _ = int.from_bytes(aedr[32:36],'big', signed=True) #Nothing
        # _ = int.from_bytes(aedr[36:40],'big', signed=True) #Nothing
        # _ = int.from_bytes(aedr[40:44],'big', signed=True) #Nothing
        # _ = int.from_bytes(aedr[44:48],'big', signed=True) #Nothing

        byte_stream = aedr[48:]
        if to_np:
            entry = self._read_data(byte_stream, data_type, 1, num_elements)
        else:
            if (data_type == 32):
                entry = self._convert_data(byte_stream, data_type, 1, 2, num_elements)
            else:
                entry = self._convert_data(byte_stream, data_type, 1, 1, num_elements)

        return_dict = {}
        return_dict['entry'] = entry
        return_dict['data_type'] = data_type
        return_dict['num_elements'] = num_elements
        return_dict['num_strings'] = num_strings
        return_dict['next_aedr'] = next_aedr
        return_dict['entry_num'] = entry_num

        return return_dict

    def _read_aedr2(self, byte_loc, to_np=True):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            aedr = f.read(block_size - 4)

        next_aedr = int.from_bytes(aedr[4:8], 'big', signed=True)
        data_type = int.from_bytes(aedr[12:16], 'big', signed=True)

        # Variable number or global entry number
        entry_num = int.from_bytes(aedr[16:20], 'big', signed=True)
        # Number of elements
        # Length of string if string, otherwise its the number of numbers
        num_elements = int.from_bytes(aedr[20:24], 'big', signed=True)
        byte_stream = aedr[44:]
        if to_np:
            entry = self._read_data(byte_stream, data_type, 1, num_elements)
        else:
            if (data_type == 32):
                entry = self._convert_data(byte_stream, data_type, 1, 2, num_elements)
            else:
                entry = self._convert_data(byte_stream, data_type, 1, 1, num_elements)
        return_dict = {}
        return_dict['entry'] = entry
        return_dict['data_type'] = data_type
        return_dict['num_elements'] = num_elements
        # return_dict['num_strings'] = num_strings
        return_dict['next_aedr'] = next_aedr
        return_dict['entry_num'] = entry_num
        return return_dict

    def _read_vdr(self, byte_loc):
        """
        Read a variable descriptor record (VDR).
        """
        if self.cdfversion == 3:
            return self._read_vdr3(byte_loc)
        else:
            return self._read_vdr2(byte_loc)

    def _read_vdr3(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            vdr = f.read(block_size - 8)
        # Type of internal record
        section_type = int.from_bytes(vdr[0:4], 'big')
        next_vdr = int.from_bytes(vdr[4:12], 'big', signed=True)
        data_type = int.from_bytes(vdr[12:16], 'big', signed=True)
        max_rec = int.from_bytes(vdr[16:20], 'big', signed=True)
        head_vxr = int.from_bytes(vdr[20:28], 'big', signed=True)
        last_vxr = int.from_bytes(vdr[28:36], 'big', signed=True)
        flags = int.from_bytes(vdr[36:40], 'big', signed=True)

        flag_bits = f'{flags:032b}'

        record_variance_bool = (flag_bits[31] == '1')
        pad_bool = (flag_bits[30] == '1')
        compression_bool = (flag_bits[29] == '1')

        sparse = int.from_bytes(vdr[40:44], 'big', signed=True)
        num_elements = int.from_bytes(vdr[56:60], 'big', signed=True)
        var_num = int.from_bytes(vdr[60:64], 'big', signed=True)
        CPRorSPRoffset = int.from_bytes(vdr[64:72], 'big', signed=True)
        blocking_factor = int.from_bytes(vdr[72:76], 'big', signed=True)
        name = str(vdr[76:332].decode(self.string_encoding))
        name = name.replace('\x00', '')

        zdim_sizes = []
        dim_sizes = []
        dim_varys = []
        if (section_type == 8):
            # zvariable
            num_dims = int.from_bytes(vdr[332:336], 'big', signed=True)
            for x in range(0, num_dims):
                ioff = 336 + 4 * x
                zdim_sizes.append(int.from_bytes(vdr[ioff:ioff+4], 'big',
                                                 signed=True))
            coff = 336 + 4 * num_dims
            for x in range(0, num_dims):
                dim_varys.append(int.from_bytes(vdr[coff+4*x:coff+4*x+4],
                                                'big', signed=True))
            adj = 0
            # Check for "False" dimensions, and delete them
            for x in range(0, num_dims):
                y = num_dims - x - 1
                if (dim_varys[y] == 0):
                    del zdim_sizes[y]
                    del dim_varys[y]
                    adj = adj + 1
            num_dims = num_dims - adj
            coff = 336 + 8 * num_dims
        else:
            # rvariable
            for x in range(0, self._rvariables_num_dims):
                ioff = 332 + 4 * x
                dim_varys.append(int.from_bytes(vdr[ioff:ioff+4], 'big',
                                                signed=True))
            for x in range(0, self._rvariables_num_dims):
                if (dim_varys[x] != 0):
                    dim_sizes.append(self._rvariables_dim_sizes[x])
            num_dims = len(dim_sizes)
            coff = 332 + 4 * self._rvariables_num_dims
        # Only set if pad value is in the flags
        if pad_bool:
            byte_stream = vdr[coff:]
            pad = self._read_data(byte_stream, data_type, 1, num_elements)

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
        if (pad_bool):
            return_dict['pad'] = pad
        return_dict['compression_bool'] = compression_bool
        if (compression_bool):
            ctype, cparm = self._read_cpr(CPRorSPRoffset)
            return_dict['compression_level'] = cparm
        else:
            return_dict['compression_level'] = 0
        return_dict['blocking_factor'] = blocking_factor
        return_dict['dim_vary'] = dim_varys
        return_dict['record_vary'] = record_variance_bool
        return_dict['num_elements'] = num_elements
        return_dict['sparse'] = sparse
        return return_dict

    def _read_vdr2(self, byte_loc):

        if (self._post25 is True):
            toadd = 0
        else:
            toadd = 128
        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            vdr = f.read(block_size-4)
        # Type of internal record
        section_type = int.from_bytes(vdr[0:4], 'big')
        next_vdr = int.from_bytes(vdr[4:8], 'big', signed=True)
        data_type = int.from_bytes(vdr[8:12], 'big', signed=True)
        max_rec = int.from_bytes(vdr[12:16], 'big', signed=True)
        head_vxr = int.from_bytes(vdr[16:20], 'big', signed=True)
        last_vxr = int.from_bytes(vdr[20:24], 'big', signed=True)
        flags = int.from_bytes(vdr[24:28], 'big', signed=True)
        flag_bits = f'{flags:032b}'
        record_variance_bool = (flag_bits[31] == '1')
        pad_bool = (flag_bits[30] == '1')
        compression_bool = (flag_bits[29] == '1')
        sparse = int.from_bytes(vdr[28:32], 'big', signed=True)

        num_elements = int.from_bytes(vdr[44+toadd:48+toadd], 'big', signed=True)
        var_num = int.from_bytes(vdr[48+toadd:52+toadd], 'big', signed=True)
        CPRorSPRoffset = int.from_bytes(vdr[52+toadd:56+toadd], 'big',
                                        signed=True)
        blocking_factor = int.from_bytes(vdr[56+toadd:60+toadd], 'big',
                                         signed=True)
        name = str(vdr[60+toadd:124+toadd].decode(self.string_encoding))
        name = name.replace('\x00', '')
        zdim_sizes = []
        dim_sizes = []
        dim_varys = []
        if (section_type == 8):
            # zvariable
            num_dims = int.from_bytes(vdr[124+toadd:128+toadd], 'big',
                                      signed=True)
            for x in range(0, num_dims):
                xoff = 128 + toadd + 4*x
                zdim_sizes.append(int.from_bytes(vdr[xoff:xoff+4], 'big',
                                                 signed=True))
            coff = 128 + toadd + 4 * num_dims
            for x in range(0, num_dims):
                icoff = coff + 4 * x
                if (int.from_bytes(vdr[icoff:icoff+4], 'big', signed=True) == 0):
                    dim_varys.append(False)
                else:
                    dim_varys.append(True)
            adj = 0
            # Check for "False" dimensions, and delete them
            for x in range(0, num_dims):
                y = num_dims - x - 1
                if (dim_varys[y] == 0 or dim_varys[y] == False):
                    del zdim_sizes[y]
                    del dim_varys[y]
                    adj = adj + 1
            num_dims = num_dims - adj
            coff = 128 + toadd + 8 * num_dims
        else:
            # rvariable
            for x in range(0, self._rvariables_num_dims):
                ix = 124 + toadd + 4 * x
                if (int.from_bytes(vdr[ix:ix+4], 'big', signed=True) == 0):
                    dim_varys.append(False)
                else:
                    dim_varys.append(True)
            for x in range(0, len(dim_varys)):
                dim_sizes.append(self._rvariables_dim_sizes[x])
            num_dims = len(dim_sizes)
            coff = 124 + toadd + 4 * self._rvariables_num_dims
        # Only set if pad value is in the flags
        if pad_bool:
            byte_stream = vdr[coff:]
            try:
                pad = self._read_data(byte_stream, data_type, 1, num_elements)
            except Exception:
                if (data_type == 51 or data_type == 52):
                    pad = ' ' * num_elements

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
        if (pad_bool):
            return_dict['pad'] = pad
        return_dict['compression_bool'] = compression_bool
        if (compression_bool):
            ctype, cparm = self._read_cpr(CPRorSPRoffset)
            return_dict['compression_level'] = cparm
        else:
            return_dict['compression_level'] = 0
        return_dict['blocking_factor'] = blocking_factor
        return_dict['dim_vary'] = dim_varys
        return_dict['record_vary'] = record_variance_bool
        return_dict['num_elements'] = num_elements
        return_dict['sparse'] = sparse
        return return_dict

    def _read_vdr_fast(self, byte_loc):
        if self.cdfversion == 3:
            return self._read_vdr_fast3(byte_loc)
        else:
            return self._read_vdr_fast2(byte_loc)

    def _read_vdr_fast3(self, byte_loc):
        with self.file.open('rb') as f:
            f.seek(byte_loc+12, 0)
            next_vdr = int.from_bytes(f.read(8), 'big', signed=True)
            f.seek(byte_loc+84, 0)
            name = str(f.read(256).decode(self.string_encoding))

        name = name.replace('\x00', '')

        return name, next_vdr

    def _read_vdr_fast2(self, byte_loc):
        if self._post25:
            toadd = 0
        else:
            toadd = 128

        with self.file.open('rb') as f:
            f.seek(byte_loc+8, 0)
            next_vdr = int.from_bytes(f.read(4), 'big', signed=True)
            f.seek(byte_loc+toadd+64, 0)
            name = str(f.read(64).decode(self.string_encoding))

        name = name.replace('\x00', '')

        return name, next_vdr

    def _read_vxrs(self, byte_loc, vvr_offsets=[], vvr_start=[], vvr_end=[]):

        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(8), 'big', signed=True)  # Block Size
            vxrs = f.read(block_size-8)

            next_vxr_pos = int.from_bytes(vxrs[4:12], 'big', signed=True)
            num_ent = int.from_bytes(vxrs[12:16], 'big', signed=True)
            num_ent_used = int.from_bytes(vxrs[16:20], 'big', signed=True)
            # coff = 20
            for ix in range(0, num_ent_used):
                soffset = 20 + 4 * ix
                num_start = int.from_bytes(vxrs[soffset:soffset+4], 'big',
                                           signed=True)
                eoffset = 20 + 4 * num_ent + 4 * ix
                num_end = int.from_bytes(vxrs[eoffset:eoffset+4], 'big', signed=True)
                ooffset = 20 + 2 * 4 * num_ent + 8 * ix
                rec_offset = int.from_bytes(vxrs[ooffset:ooffset+8], 'big',
                                            signed=True)
                type_offset = 8 + rec_offset
                f.seek(type_offset, 0)
                next_type = int.from_bytes(f.read(4), 'big', signed=True)
                if next_type == 6:
                    vvr_offsets, vvr_start, vvr_end = self._read_vxrs(rec_offset,
                                                                      vvr_offsets=vvr_offsets, vvr_start=vvr_start, vvr_end=vvr_end)
                else:
                    vvr_offsets.extend([rec_offset])
                    vvr_start.extend([num_start])
                    vvr_end.extend([num_end])

        if next_vxr_pos != 0:
            vvr_offsets, vvr_start, vvr_end = self._read_vxrs(next_vxr_pos,
                                                              vvr_offsets=vvr_offsets, vvr_start=vvr_start, vvr_end=vvr_end)

        return vvr_offsets, vvr_start, vvr_end

    def _read_vxrs2(self, byte_loc, vvr_offsets=[], vvr_start=[], vvr_end=[]):

        with self.file.open('rb') as f:
            f.seek(byte_loc, 0)
            block_size = int.from_bytes(f.read(4), 'big', signed=True)
            vxrs = f.read(block_size-4)

            next_vxr_pos = int.from_bytes(vxrs[4:8], 'big', signed=True)
            num_ent = int.from_bytes(vxrs[8:12], 'big', signed=True)
            num_ent_used = int.from_bytes(vxrs[12:16], 'big', signed=True)
            # coff = 16
            for ix in range(0, num_ent_used):
                soffset = 16 + 4 * ix
                num_start = int.from_bytes(vxrs[soffset:soffset+4], 'big',
                                           signed=True)
                eoffset = 16 + 4 * num_ent + 4 * ix
                num_end = int.from_bytes(vxrs[eoffset:eoffset+4], 'big', signed=True)
                ooffset = 16 + 2 * 4 * num_ent + 4 * ix
                rec_offset = int.from_bytes(vxrs[ooffset:ooffset+4], 'big',
                                            signed=True)
                type_offset = 4 + rec_offset
                f.seek(type_offset, 0)
                next_type = int.from_bytes(f.read(4), 'big', signed=True)
                if next_type == 6:
                    vvr_offsets, vvr_start, vvr_end = self._read_vxrs2(rec_offset,
                                                                       vvr_offsets=vvr_offsets, vvr_start=vvr_start, vvr_end=vvr_end)
                else:
                    vvr_offsets.extend([rec_offset])
                    vvr_start.extend([num_start])
                    vvr_end.extend([num_end])

        if next_vxr_pos != 0:
            vvr_offsets, vvr_start, vvr_end = self._read_vxrs2(next_vxr_pos,
                                                               vvr_offsets=vvr_offsets, vvr_start=vvr_start, vvr_end=vvr_end)
        return vvr_offsets, vvr_start, vvr_end

    def _read_vvrs(self, vdr_dict, vvr_offs, vvr_start, vvr_end, startrec, endrec, to_np=True):
        """
        Reads in all VVRS that are pointed to in the VVR_OFFS array.
        Creates a large byte array of all values called "byte_stream".
        Decodes the byte_stream, then returns them.
        """

        numBytes = self._type_size(vdr_dict['data_type'],
                                   vdr_dict['num_elements'])
        numValues = self._num_values(vdr_dict)
        totalRecs = endrec - startrec + 1
        firstBlock = -1
        lastBlock = -1
        totalBytes = numBytes * numValues * totalRecs
        byte_stream = bytearray(totalBytes)
        pos = 0
        if (vdr_dict['sparse'] == 0):
            for vvr_num in range(0, len(vvr_offs)):
                if (vvr_end[vvr_num] >= startrec and firstBlock == -1):
                    firstBlock = vvr_num
                if (vvr_end[vvr_num] >= endrec):
                    lastBlock = vvr_num
                    break
            for vvr_num in range(firstBlock, (lastBlock+1)):
                if (self.cdfversion == 3):
                    var_block_data = self._read_vvr_block(vvr_offs[vvr_num])
                else:
                    var_block_data = self._read_vvr_block2(vvr_offs[vvr_num])
                asize = len(var_block_data)
                byte_stream[pos:pos+asize] = var_block_data
                pos = pos + asize
            startPos = (startrec - vvr_start[firstBlock]) * numBytes * numValues
            stopOff = (vvr_end[lastBlock] - endrec) * numBytes * numValues
            byte_stream = byte_stream[startPos:len(byte_stream)-stopOff]
        else:
            # with sparse records
            if ('pad' in vdr_dict):
                # use default pad value
                filled_data = self._convert_np_data(vdr_dict['pad'],
                                                    vdr_dict['data_type'],
                                                    vdr_dict['num_elements'])
            else:
                filled_data = self._convert_np_data(
                    self._default_pad(vdr_dict['data_type'],
                                      vdr_dict['num_elements']),
                    vdr_dict['data_type'],
                    vdr_dict['num_elements'])
            cur_block = -1
            rec_size = numBytes * numValues
            for rec_num in range(startrec, (endrec+1)):
                block, prev_block = self._find_block(vvr_start, vvr_end,
                                                     cur_block, rec_num)
                if (block > -1):
                    record_off = rec_num - vvr_start[block]
                    if (cur_block != block):
                        if (self.cdfversion == 3):
                            var_block_data = self._read_vvr_block(vvr_offs[block])
                        else:
                            var_block_data = self._read_vvr_block2(vvr_offs[block])
                        cur_block = block
                    xoff = record_off * rec_size
                    byte_stream[pos:pos+rec_size] = var_block_data[xoff:
                                                                   xoff+rec_size]
                else:
                    if (vdr_dict['sparse'] == 1):
                        # use defined pad or default pad
                        byte_stream[pos:pos+rec_size] = filled_data * numValues
                    else:
                        # use previous physical record
                        if (prev_block != -1):
                            if (self.cdfversion == 3):
                                var_prev_block_data = self._read_vvr_block(
                                    vvr_offs[prev_block])
                            else:
                                var_prev_block_data = self._read_vvr_block2(
                                    vvr_offs[prev_block])
                            lastRecOff = (vvr_end[prev_block] -
                                          vvr_start[prev_block]) * rec_size
                            byte_stream[pos:pos+rec_size] = var_prev_block_data[lastRecOff:]
                        else:
                            byte_stream[pos:pos+rec_size] = filled_data * numValues
                pos = pos + rec_size
                if (block > -1):
                    cur_block = block
        dimensions = []
        var_vary = vdr_dict['dim_vary']
        var_sizes = vdr_dict['dim_sizes']
        for x in range(0, vdr_dict['num_dims']):
            if (var_vary[x] == 0):
                continue
            dimensions.append(var_sizes[x])
        if to_np:
            y = self._read_data(byte_stream, vdr_dict['data_type'],
                                totalRecs, vdr_dict['num_elements'],
                                dimensions)
        else:
            if (vdr_dict['data_type'] == 32):
                y = self._convert_data(byte_stream, vdr_dict['data_type'],
                                       totalRecs, self._num_values(vdr_dict)*2,
                                       vdr_dict['num_elements'])
            else:
                y = self._convert_data(byte_stream, vdr_dict['data_type'],
                                       totalRecs, self._num_values(vdr_dict),
                                       vdr_dict['num_elements'])

        return y

    def _convert_option(self):
        """
        Determines how to convert CDF byte ordering to the system
        byte ordering.
        """

        if sys.byteorder == 'little' and self._endian() == 'big-endian':
            # big->little
            order = '>'
        elif sys.byteorder == 'big' and self._endian() == 'little-endian':
            # little->big
            order = '<'
        else:
            # no conversion
            order = '='
        return order

    def _endian(self) -> str:
        """
        Determines endianess of the CDF file
        Only used in __init__
        """
        if (self._encoding == 1 or self._encoding == 2 or self._encoding == 5 or
            self._encoding == 7 or self._encoding == 9 or self._encoding == 11 or
                self._encoding == 12):
            return 'big-endian'
        else:
            return 'little-endian'

    @staticmethod
    def _type_size(data_type, num_elms):
        # DATA TYPES
        #
        # 1 - 1 byte signed int
        # 2 - 2 byte signed int
        # 4 - 4 byte signed int
        # 8 - 8 byte signed int
        # 11 - 1 byte unsigned int
        # 12 - 2 byte unsigned int
        # 14 - 4 byte unsigned int
        # 41 - same as 1
        # 21 - 4 byte float
        # 22 - 8 byte float (double)
        # 44 - same as 21
        # 45 - same as 22
        # 31 - double representing milliseconds
        # 32 - 2 doubles representing milliseconds
        # 33 - 8 byte signed integer representing nanoseconds from J2000
        # 51 - signed character
        # 52 - unsigned character

        if (isinstance(data_type, int)):
            if ((data_type == 1) or (data_type == 11) or (data_type == 41)):
                return 1
            elif ((data_type == 2) or (data_type == 12)):
                return 2
            elif ((data_type == 4) or (data_type == 14)):
                return 4
            elif ((data_type == 8) or (data_type == 33)):
                return 8
            elif ((data_type == 21) or (data_type == 44)):
                return 4
            elif ((data_type == 22) or (data_type == 31) or (data_type == 45)):
                return 8
            elif (data_type == 32):
                return 16
            elif ((data_type == 51) or (data_type == 52)):
                return num_elms
        elif (isinstance(data_type, str)):
            data_typeU = data_type.upper()
            if ((data_typeU == 'CDF_INT1') or (data_typeU == 'CDF_UINT1') or
                    (data_typeU == 'CDF_BYTE')):
                return 1
            elif ((data_typeU == 'CDF_INT2') or (data_typeU == 'CDF_UINT2')):
                return 2
            elif ((data_typeU == 'CDF_INT4') or (data_typeU == 'CDF_UINT4')):
                return 4
            elif ((data_typeU == 'CDF_INT8') or (data_typeU == 'CDF_TIME_TT2000')):
                return 8
            elif ((data_typeU == 'CDF_REAL4') or (data_typeU == 'CDF_FLOAT')):
                return 4
            elif ((data_typeU == 'CDF_REAL8') or (data_typeU == 'CDF_DOUBLE') or
                  (data_typeU == 'CDF_EPOCH')):
                return 8
            elif (data_typeU == 'CDF_EPOCH16'):
                return 16
            elif ((data_typeU == 'CDF_CHAR') or (data_typeU == 'CDF_UCHAR')):
                return num_elms
        else:
            raise TypeError('Unknown data type....')

    def _read_data(self, byte_stream, data_type, num_recs, num_elems, dimensions=None):
        """
        This is the primary routine that converts streams of bytes into usable data.

        To do so, we need the bytes, the type of data, the number of records,
        the number of elements in a record, and dimension information.
        """

        squeeze_needed = False
        # If the dimension is [n], it needs to be [n,1]
        # for the numpy dtype.  This requires us to squeeze
        # the matrix later, to get rid of this extra dimension.
        dt_string = self._convert_option()
        if dimensions != None:
            if self._majority == 'Column_major':
                dimensions = list(reversed(dimensions))
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
        if data_type == 52 or data_type == 51:
            # string
            if dimensions is None:
                byte_data = bytearray(byte_stream[0:num_recs*num_elems])
                # In each record, check for the first '\x00' (null character).
                # If found, make all the characters after it null as well.
                for x in range(0, num_recs):
                    y = x * num_elems
                    z = byte_data[y:y+num_elems].find(b'\x00')
                    if (z > -1 and z < (num_elems - 1)):
                        byte_data[y + z + 1:y + num_elems] = b'\x00' * (num_elems - z - 1)
                ret = byte_data[0:num_recs*num_elems].decode(self.string_encoding).replace('\x00', '')
            else:
                # Count total number of strings
                count = 1
                for x in range(0, len(dimensions)):
                    count = count * dimensions[x]
                strings = []
                if (len(dimensions) == 0):
                    for i in range(0, num_recs*count*num_elems, num_elems):
                        string1 = byte_stream[i:i+num_elems].decode(self.string_encoding).\
                            replace('\x00', '')
                        strings.append(string1)
                else:
                    for x in range(0, num_recs):
                        onerec = []
                        for i in range(x*count*num_elems, (x+1)*count*num_elems,
                                       num_elems):
                            string1 = byte_stream[i:i+num_elems].decode(self.string_encoding)\
                                .replace('\x00', '')
                            onerec.append(string1)
                        strings.append(onerec)
                ret = strings
                ret = np.array(ret).reshape((num_recs,) + tuple(dimensions))
                if self._majority == 'Column_major':
                    axes = [0] + list(range(len(dimensions), 0, -1))
                    ret = np.transpose(ret, axes=axes)
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
            dt = np.dtype(dt_string)
            ret = np.frombuffer(byte_stream, dtype=dt, count=num_recs*num_elems)
            try:
                ret.setflags('WRITEABLE')
            except ValueError:
                # If we can't set the writable flag, just continue
                pass

        if squeeze_needed:
            ret = np.squeeze(ret, axis=(ret.ndim-1))
            if dimensions is not None:
                dimensions.pop()

        # Put the data into system byte order
        if self._convert_option() != '=':
            ret = ret.byteswap().newbyteorder()

        if self._majority == 'Column_major':
            if dimensions is not None:
                axes = [0] + list(range(len(dimensions), 0, -1))
            else:
                axes = None
            ret = np.transpose(ret, axes=axes)

        return ret

    def _num_values(self, vdr_dict):
        """
        Returns the number of values in a record, using a given VDR
        dictionary. Multiplies the dimension sizes of each dimension,
        if it is varying.
        """
        values = 1
        for x in range(0, vdr_dict['num_dims']):
            if (vdr_dict['dim_vary'][x] != 0):
                values = values * vdr_dict['dim_sizes'][x]
        return values

    def _get_attdata(self, adr_info, entry_num, num_entry, first_entry, to_np=True):
        position = first_entry
        for _ in range(0, num_entry):
            got_entry_num, next_aedr = self._read_aedr_fast(position)
            if entry_num == got_entry_num:
                aedr_info = self._read_aedr(position, to_np=to_np)
                return_dict = {}
                return_dict['Item_Size'] = self._type_size(aedr_info['data_type'],
                                                           aedr_info['num_elements'])
                return_dict['Data_Type'] = self._datatype_token(aedr_info['data_type'])

                return_dict['Num_Items'] = aedr_info['num_elements']
                return_dict['Data'] = aedr_info['entry']
                if (aedr_info['data_type'] == 51 or aedr_info['data_type'] == 52):
                    if 'num_strings' in aedr_info:
                        return_dict['Num_Items'] = aedr_info['num_strings']
                        if (aedr_info['num_strings'] > 1):
                            return_dict['Data'] = aedr_info['entry'].split('\\N ')
                if not to_np and (aedr_info['data_type'] == 32):
                    return_dict['Data'] = complex(aedr_info['entry'][0],
                                                  aedr_info['entry'][1])
                return return_dict
            else:
                position = next_aedr

        raise KeyError('The entry does not exist')

    def _read_vardata(self, vdr_info, epoch=None, starttime=None, endtime=None,
                      startrec=0, endrec=None, record_range_only=False,
                      expand=False, to_np=True):

        # Error checking
        if startrec:
            if (startrec < 0):
                raise ValueError('Invalid start recond')
            if not (vdr_info['record_vary']):
                startrec = 0

        if not (endrec is None):
            if ((endrec < 0) or (endrec > vdr_info['max_records']) or
                    (endrec < startrec)):
                raise ValueError('Invalid end recond')
            if not (vdr_info['record_vary']):
                endrec = 0
        else:
            endrec = vdr_info['max_records']
        if (self.cdfversion == 3):
            vvr_offsets, vvr_start, vvr_end = self._read_vxrs(vdr_info['head_vxr'],
                                                              vvr_offsets=[], vvr_start=[], vvr_end=[])
        else:
            vvr_offsets, vvr_start, vvr_end = self._read_vxrs2(vdr_info['head_vxr'],
                                                               vvr_offsets=[], vvr_start=[], vvr_end=[])

        if (vdr_info['record_vary']):
            # Record varying
            if (starttime != None or endtime != None):
                recs = self._findtimerecords(vdr_info['name'], starttime,
                                             endtime, epoch=epoch)
                if recs is None:
                    return
                if len(recs) == 0:
                    return
                else:
                    startrec = recs[0]
                    endrec = recs[-1]
        else:
            startrec = 0
            endrec = 0

        data = self._read_vvrs(vdr_info, vvr_offsets, vvr_start, vvr_end,
                               startrec, endrec, to_np=to_np)
        if record_range_only:
            return [startrec, endrec]
        if (expand):
            new_dict = {}
            new_dict['Rec_Ndim'] = vdr_info['num_dims']
            new_dict['Rec_Shape'] = vdr_info['dim_sizes']
            new_dict['Num_Records'] = vdr_info['max_records'] + 1
            new_dict['Records_Returned'] = endrec - startrec
            new_dict['Item_Size'] = self._type_size(vdr_info['data_type'],
                                                    vdr_info['num_elements'])
            new_dict['Data_Type'] = self._datatype_token(vdr_info['data_type'])
            new_dict['Data'] = data
            if (vdr_info['sparse']):
                blocks = len(vvr_start)
                physical_recs = []
                for x in range(0, blocks):
                    for y in range(vvr_start[x], vvr_end[x] + 1):
                        physical_recs.append(y)
                new_dict['Real_Records'] = physical_recs
            return new_dict
        else:
            if (vdr_info['record_vary']):
                return data
            else:
                return data[0]

    def _findtimerecords(self, var_name, starttime, endtime, epoch=None):

        if (epoch != None):
            vdr_info = self.varinq(epoch)
            if (vdr_info == None):
                raise ValueError('Epoch not found')
            if (vdr_info['Data_Type'] == 31 or vdr_info['Data_Type'] == 32 or
                    vdr_info['Data_Type'] == 33):
                epochtimes = self.varget(epoch)
        else:
            vdr_info = self.varinq(var_name)
            if (vdr_info['Data_Type'] == 31 or vdr_info['Data_Type'] == 32 or
                    vdr_info['Data_Type'] == 33):
                epochtimes = self.varget(var_name)
            else:
                # acquire depend_0 variable
                dependVar = self.attget('DEPEND_0', var_name)
                if (dependVar is None):
                    raise ValueError(
                        "No corresponding epoch from 'DEPEND_0' attribute "
                        "for variable: {}".format(var_name) +
                        "Use 'epoch' argument to specify its time-based "
                        "variable")

                vdr_info = self.varinq(dependVar['Data'])
                if (vdr_info['Data_Type'] != 31 and vdr_info['Data_Type'] != 32
                        and vdr_info['Data_Type'] != 33):
                    raise ValueError(
                        "Corresponding variable from 'DEPEND_0' attribute "
                        "for variable: {}".format(var_name) +
                        ' is not a CDF epoch type')
                epochtimes = self.varget(dependVar['Data'])

        return self._findrangerecords(vdr_info['Data_Type'], epochtimes,
                                      starttime, endtime)

    def _findrangerecords(self, data_type, epochtimes, starttime, endtime):
        if (data_type == 31 or data_type == 32 or data_type == 33):
            # CDF_EPOCH or CDF_EPOCH16 or CDF_TIME_TT2000
            recs = epoch.CDFepoch.findepochrange(epochtimes, starttime, endtime)
        else:
            raise ValueError('Not a CDF epoch type')
        return recs

    def _convert_type(self, data_type):
        """
        CDF data types to python struct data types
        """
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

    def _default_pad(self, data_type, num_elms):
        """
        The default pad values by CDF data type
        """
        order = self._convert_option()
        if (data_type == 51 or data_type == 52):
            return str(' '*num_elms)
        if (data_type == 1) or (data_type == 41):
            pad_value = struct.pack(order+'b', -127)
            dt_string = 'i1'
        elif data_type == 2:
            pad_value = struct.pack(order+'h', -32767)
            dt_string = 'i2'
        elif data_type == 4:
            pad_value = struct.pack(order+'i', -2147483647)
            dt_string = 'i4'
        elif (data_type == 8) or (data_type == 33):
            pad_value = struct.pack(order+'q', -9223372036854775807)
            dt_string = 'i8'
        elif data_type == 11:
            pad_value = struct.pack(order+'B', 254)
            dt_string = 'u1'
        elif data_type == 12:
            pad_value = struct.pack(order+'H', 65534)
            dt_string = 'u2'
        elif data_type == 14:
            pad_value = struct.pack(order+'I', 4294967294)
            dt_string = 'u4'
        elif (data_type == 21) or (data_type == 44):
            pad_value = struct.pack(order+'f', -1.0E30)
            dt_string = 'f'
        elif (data_type == 22) or (data_type == 45) or (data_type == 31):
            pad_value = struct.pack(order+'d', -1.0E30)
            dt_string = 'd'
        else:
            # (data_type == 32):
            pad_value = struct.pack(order+'2d', *[-1.0E30, -1.0E30])
            dt_string = 'c16'

        dt = np.dtype(dt_string)
        ret = np.frombuffer(pad_value, dtype=dt, count=1)
        try:
            ret.setflags('WRITEABLE')
        except Exception:
            #TODO: Figure out why we need to array set to writeable
            pass
        return ret

    def _convert_np_data(self, data, data_type, num_elems):
        """
        Converts a single np data into byte stream.
        """
        if (data_type == 51 or data_type == 52):
            if (data == ''):
                return ('\x00'*num_elems).encode()
            else:
                return data.ljust(num_elems, '\x00').encode(self.string_encoding)
        elif (data_type == 32):
            data_stream = data.real.tobytes()
            data_stream += data.imag.tobytes()
            return data_stream
        else:
            return data.tobytes()

    def _read_vvr_block(self, offset):
        """
        Returns a VVR or decompressed CVVR block
        """
        with self.file.open('rb') as f:
            f.seek(offset, 0)
            block_size = int.from_bytes(f.read(8), 'big')
            block = f.read(block_size-8)

        section_type = int.from_bytes(block[0:4], 'big')
        if section_type == 13:
            # a CVVR
            compressed_size = int.from_bytes(block[8:16], 'big')
            return gzip.decompress(block[16:16+compressed_size])
        elif section_type == 7:
            # a VVR
            return block[4:]

    def _read_vvr_block2(self, offset):
        """
        Returns a VVR or decompressed CVVR block
        """
        with self.file.open('rb') as f:
            f.seek(offset, 0)
            block_size = int.from_bytes(f.read(4), 'big')
            block = f.read(block_size-4)

        section_type = int.from_bytes(block[0:4], 'big')
        if section_type == 13:
            # a CVVR
            compressed_size = int.from_bytes(block[8:12], 'big')
            return gzip.decompress(block[12:12+compressed_size])
        elif section_type == 7:
            # a VVR
            return block[4:]

    @staticmethod
    def _find_block(starts, ends, cur_block, rec_num):
        """
        Finds the block that rec_num is in if it is found. Otherwise it returns -1.
        It also returns the block that has the physical data either at or
        preceeding the rec_num.
        It could be -1 if the preceeding block does not exists.
        """
        total = len(starts)
        if (cur_block == -1):
            cur_block = 0
        for x in range(cur_block, total):
            if (starts[x] <= rec_num and ends[x] >= rec_num):
                return x, x
            if (starts[x] > rec_num):
                break
        return -1, x-1

    def _convert_data(self, data, data_type, num_recs, num_values, num_elems):
        """
        Converts data to the appropriate type using the struct.unpack method,
        rather than using numpy.
        """

        if (data_type == 51 or data_type == 52):
            return [data[i:i+num_elems].decode(self.string_encoding) for i in
                    range(0, num_recs*num_values*num_elems, num_elems)]
        else:
            tofrom = self._convert_option()
            dt_string = self._convert_type(data_type)
            form = tofrom + str(num_recs * num_values * num_elems) + dt_string
            value_len = self._type_size(data_type, num_elems)
            return list(struct.unpack_from(form,
                                           data[0:num_recs*num_values*value_len]))

    @staticmethod
    def getVersion():
        """
        Prints the code version and last modified date.
        """
        print('CDFread version:', str(self.version) + '.' + str(self.release) +
              '.' + str(self.increment))
        print('Date: 2018/01/11')
