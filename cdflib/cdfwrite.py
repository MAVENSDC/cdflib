import binascii
import hashlib
import io
import logging
import math
import numbers
import pathlib
import platform as pf
import struct
import sys
from functools import wraps
from numbers import Number
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

import cdflib.epochs as cdfepoch
from cdflib._gzip_wrapper import gzip_deflate
from cdflib.logging import logger

__all__ = ["CDF"]


def is_open(func):
    @wraps(func)
    def ensure_open(self, *args, **kwargs):
        if self.is_closed:
            raise OSError("This file is already closed, and can no longer be modified.")
        else:
            return func(self, *args, **kwargs)

    return ensure_open


class CDF:
    """
    Creates an empty CDF file.

    Parameters
    ----------
    path :
        The path name of the CDF (with or without .cdf extension)
    cdf_spec : dict
        The optional specification of the CDF file.

        The keys for the dictionary are:

        - ['Majority']: 'row_major' or 'column_major', or its
          corresponding value. The default is 'column_major'.
        - ['Encoding']: Data encoding scheme. See the CDF
          documentation about the valid values.
          Can be in string or its numeric corresponding value.
          The default is 'host', which will be determined when
          the script runs.
        - ['Checksum']: Whether to set the data validation upon
          file creation. The default is False.
        - ['rDim_sizes']: The dimensional sizes, applicable
          only to rVariables.
        - ['Compressed']: Whether to compress the CDF at the file
          level. A value of 0-9 or True/False, the
          default is 0/False.
    """

    version = 3
    release = 7
    increment = 0

    CDF_VAR_NAME_LEN256 = 256
    CDF_ATTR_NAME_LEN256 = 256

    CDF_COPYRIGHT_LEN = 256
    # CDF_STATUSTEXT_LEN = 200
    CDF_PATHNAME_LEN = 512

    CDF_INT1 = 1
    CDF_INT2 = 2
    CDF_INT4 = 4
    CDF_INT8 = 8
    CDF_UINT1 = 11
    CDF_UINT2 = 12
    CDF_UINT4 = 14
    CDF_REAL4 = 21
    CDF_REAL8 = 22
    CDF_EPOCH = 31
    CDF_EPOCH16 = 32
    CDF_TIME_TT2000 = 33
    CDF_BYTE = 41
    CDF_FLOAT = 44
    CDF_DOUBLE = 45
    CDF_CHAR = 51
    CDF_UCHAR = 52

    NETWORK_ENCODING = 1
    SUN_ENCODING = 2
    VAX_ENCODING = 3
    DECSTATION_ENCODING = 4
    SGi_ENCODING = 5
    IBMPC_ENCODING = 6
    IBMRS_ENCODING = 7
    HOST_ENCODING = 8
    PPC_ENCODING = 9
    HP_ENCODING = 11
    NeXT_ENCODING = 12
    ALPHAOSF1_ENCODING = 13
    ALPHAVMSd_ENCODING = 14
    ALPHAVMSg_ENCODING = 15
    ALPHAVMSi_ENCODING = 16
    ARM_LITTLE_ENCODING = 17
    ARM_BIG_ENCODING = 18

    VARY = -1
    NOVARY = 0

    ROW_MAJOR = 1
    COLUMN_MAJOR = 2

    # SINGLE_FILE = 1
    # MULTI_FILE = 2

    NO_CHECKSUM = 0
    MD5_CHECKSUM = 1
    OTHER_CHECKSUM = 2

    GLOBAL_SCOPE = 1
    VARIABLE_SCOPE = 2

    # NO_COMPRESSION = 0
    # RLE_COMPRESSION = 1
    # HUFF_COMPRESSION = 2
    # AHUFF_COMPRESSION = 3
    GZIP_COMPRESSION = 5

    # RLE_OF_ZEROs	= 0
    # NO_SPARSEARRAYS = 0
    NO_SPARSERECORDS = 0
    PAD_SPARSERECORDS = 1
    PREV_SPARSERECORDS = 2
    V3magicNUMBER_1 = "cdf30001"
    V3magicNUMBER_2 = "0000ffff"
    V3magicNUMBER_2c = "cccc0001"
    CDR_ = 1
    GDR_ = 2
    rVDR_ = 3
    ADR_ = 4
    AgrEDR_ = 5
    VXR_ = 6
    VVR_ = 7
    zVDR_ = 8
    AzEDR_ = 9
    CCR_ = 10
    CPR_ = 11
    SPR_ = 12
    CVVR_ = 13

    NUM_VXR_ENTRIES = 7
    NUM_VXRlvl_ENTRIES = 3

    UUIR_BASE_SIZE64 = 12
    UIR_BASE_SIZE64 = 28
    CDR_BASE_SIZE64 = 56
    GDR_BASE_SIZE64 = 84
    zVDR_BASE_SIZE64 = 88 + CDF_VAR_NAME_LEN256
    rVDR_BASE_SIZE64 = 84 + CDF_VAR_NAME_LEN256
    VXR_BASE_SIZE64 = 28
    VVR_BASE_SIZE64 = 12
    ADR_BASE_SIZE64 = 68 + CDF_ATTR_NAME_LEN256
    AEDR_BASE_SIZE64 = 56
    CCR_BASE_SIZE64 = 32
    CPR_BASE_SIZE64 = 24
    SPR_BASE_SIZE64 = 24
    CVVR_BASE_SIZE64 = 24

    # BLOCKING_BYTES = 131072
    BLOCKING_BYTES = 65536

    level = 0

    def __init__(self, path: Union[str, Path], cdf_spec: Optional[Dict[str, Any]] = None, delete: bool = False):
        path = pathlib.Path(path).expanduser()

        major = 1
        if cdf_spec is not None:
            major = cdf_spec.get("Majority", major)
            if isinstance(major, str):
                major = self._majority_token(major)

            encoding = cdf_spec.get("Encoding", 8)  # default is host
            if isinstance(encoding, str):
                encoding = self._encoding_token(encoding)

            checksum = cdf_spec.get("Checksum", False)

            cdf_compression = cdf_spec.get("Compressed", 0)
            if isinstance(cdf_compression, int):
                if not 0 <= cdf_compression <= 9:
                    cdf_compression = 0
            else:
                cdf_compression = 6 if cdf_compression else 0

            rdim_sizes: Optional[List[int]] = cdf_spec.get("rDim_sizes", None)
            num_rdim: int = len(rdim_sizes) if rdim_sizes is not None else 0

        else:
            encoding = 8
            checksum = False
            cdf_compression = 0
            num_rdim = 0
            rdim_sizes = None

        if major not in [1, 2]:
            raise RuntimeError(f"Bad major: {major}")

        osSystem = pf.system()
        osMachine = pf.uname()[5]
        if encoding == 8:
            if osSystem != "SunOS" or osMachine != "sparc":
                self._encoding = self.IBMPC_ENCODING
            else:
                self._encoding = self.SUN_ENCODING
        else:
            self._encoding = encoding
            if self._encoding == -1:
                raise OSError("Bad encoding.")
        if not isinstance(checksum, bool):
            raise ValueError("Bad checksum.")

        if path.suffix != ".cdf":
            path = path.with_suffix(".cdf")
        if len(str(path)) > self.CDF_PATHNAME_LEN:
            raise OSError("CDF:", path, " longer than allowed length.")
        if path.is_file():
            if not delete:
                raise OSError("file: ", path, " already exists....\n", "Delete it or specify the 'delete=False' option.")
            else:
                path.unlink()

        self.path = path

        self.compressed_file = path.with_suffix(".tmp") if cdf_compression > 0 else None

        # Dictionary objects, these contains name, offset, and dimension information
        self.zvarsinfo: Dict[int, Tuple[str, int, int, List[int], List[bool]]] = {}
        self.rvarsinfo: Dict[int, Tuple[str, int, int, List[int], List[bool]]] = {}

        # Dictionary object, contains name, offset, and scope (global or variable)
        self.attrsinfo: Dict[int, Tuple[str, int, int]] = {}

        self.gattrs: List[str] = []  # List of global attributes
        self.vattrs: List[str] = []  # List of variable attributes
        self.attrs: List[str] = []  # List of ALL attributes
        self.zvars: List[str] = []  # List of z variable names
        self.rvars: List[str] = []  # List of r variable names
        self.checksum = checksum  # Boolean, whether or not to include the checksum at the end
        self.compression = cdf_compression  # Compression level (or True/False)
        self.num_rdim = num_rdim  # Number of r dimensions
        self.rdim_sizes = rdim_sizes  # Size of r dimensions
        self.majority = major

        with path.open("wb") as f:
            f.write(binascii.unhexlify(self.V3magicNUMBER_1))
            f.write(binascii.unhexlify(self.V3magicNUMBER_2))

            self.cdr_head = self._write_cdr(f, major, self._encoding, checksum)
            self.gdr_head = self._write_gdr(f)
            self.offset = f.tell()

        self.is_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return

    def close(self) -> None:
        """
        Closes the CDF Class.

            1. If compression was set, this is where the compressed file is
               written.
            2. If a checksum is needed, this will place the checksum at the end
               of the file.

        """
        if self.is_closed:
            return

        if self.compressed_file is None:
            with self.path.open("rb+") as f:
                f.seek(0, 2)
                eof = f.tell()
                self._update_offset_value(f, self.gdr_head + 36, 8, eof)
                if self.checksum:
                    f.write(self._md5_compute(f))
                self.is_closed = True
            return

        with self.path.open("rb+") as f:
            f.seek(0, 2)
            eof = f.tell()
            self._update_offset_value(f, self.gdr_head + 36, 8, eof)

            with self.compressed_file.open("wb+") as g:
                g.write(bytearray.fromhex(self.V3magicNUMBER_1))
                g.write(bytearray.fromhex(self.V3magicNUMBER_2c))
                self._write_ccr(f, g, self.compression)

                if self.checksum:
                    g.seek(0, 2)
                    g.write(self._md5_compute(g))

        self.path.unlink()  # NOTE: for Windows this is necessary
        self.compressed_file.rename(self.path)
        self.is_closed = True

    @is_open
    def write_globalattrs(self, globalAttrs):
        """
        Writes the global attributes.

        Parameters
        ----------
        globalAttrs: dict
            Global attribute name(s) and their value(s) pair(s).

            The value(s) is a dictionary of entry number and value pair(s).
            For example::

                globalAttrs={}
                globalAttrs['Global1']={0: 'Global Value 1'}
                globalAttrs['Global2']={0: 'Global Value 2'}

            For a non-string value, use a list with the value and its
            CDF data type. For example::

                globalAttrs['Global3']={0: [12, 'cdf_int4']}
                globalAttrs['Global4']={0: [12.34, 'cdf_double']}

            If the data type is not provided, a corresponding
            CDF data type is assumed::

                globalAttrs['Global3']={0: 12}     as 'cdf_int4'
                globalAttrs['Global4']={0: 12.34}  as 'cdf_double'

            CDF allows multi-values for non-string data for an attribute::

                globalAttrs['Global5']={0: [[12.34,21.43], 'cdf_double']}

            For multi-entries from a global variable, they should be
            presented in this form::

                GA6={}
                GA6[0]='abcd'
                GA6[1]=[12, 'cdf_int2']
                GA6[2]=[12.5, 'cdf_float']
                GA6[3]=[[0,1,2], 'cdf_int8']
                globalAttrs['Global6']=GA6
                ....
                f.write_globalattrs(globalAttrs)
        """
        if not (isinstance(globalAttrs, dict)):
            raise ValueError("Global attribute(s) not in dictionary form")
        dataType = None
        numElems = None
        with self.path.open("rb+") as f:
            f.seek(0, 2)  # EOF (appending)
            for attr, entry in globalAttrs.items():
                if attr in self.gattrs:
                    raise ValueError(f"Global attribute: {attr} already exists.")

                if attr in self.vattrs:
                    logging.warning(f"Attribute: {attr} already defined as a variable attribute.")
                    continue

                attrNum, offsetADR = self._write_adr(f, True, attr)
                entries = 0
                if entry is None:
                    continue
                entryNumMaX = -1
                poffset = -1
                for entryNum, value in entry.items():
                    if entryNumMaX < entryNum:
                        entryNumMaX = entryNum
                    if hasattr(value, "__len__") and not isinstance(value, str):
                        if len(value) == 2:
                            # Check if the second value is a valid data type
                            value2 = value[1]
                            dataType = self._datatype_token(value2)
                            if dataType > 0:
                                # Data Type found
                                data = value[0]
                                if dataType == self.CDF_CHAR or dataType == self.CDF_UCHAR:
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        logger.warning("Invalid global attribute value")
                                        return
                                    numElems = len(data)
                                elif dataType == self.CDF_EPOCH or dataType == self.CDF_EPOCH16 or dataType == self.CDF_TIME_TT2000:
                                    cvalue = []
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        numElems = len(data)
                                        for x in range(0, numElems):
                                            if isinstance(data[x], str):
                                                cvalue.append(cdfepoch.CDFepoch.parse(data[x]))
                                            else:
                                                cvalue.append(data[x])
                                        data = cvalue
                                    else:
                                        if isinstance(data, str):
                                            data = cdfepoch.CDFepoch.parse(data)
                                        numElems = 1
                                else:
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        numElems = len(data)
                                    else:
                                        numElems = 1
                            else:
                                # Data type not found, both values are data.
                                data = value
                                numElems, dataType = self._datatype_define(value[0])
                                numElems = len(value)
                        else:
                            # Length greater than 2, so it is all data.
                            data = value
                            numElems, dataType = self._datatype_define(value[0])
                            numElems = len(value)
                    else:
                        # Just one value
                        data = value
                        numElems, dataType = self._datatype_define(value)
                        if numElems is None:
                            logger.warning("Unknown data")
                            return

                    offset = self._write_aedr(f, True, attrNum, entryNum, data, dataType, numElems, None)
                    if entries == 0:
                        # ADR's AgrEDRhead
                        self._update_offset_value(f, offsetADR + 20, 8, offset)
                    else:
                        # ADR's ADRnext
                        self._update_offset_value(f, poffset + 12, 8, offset)

                    poffset = offset
                    entries = entries + 1
                # ADR's NgrEntries
                self._update_offset_value(f, offsetADR + 36, 4, entries)
                # ADR's MAXgrEntry
                self._update_offset_value(f, offsetADR + 40, 4, entryNumMaX)

    @is_open
    def write_variableattrs(self, variableAttrs):
        """
        Writes a variable's attributes, provided the variable already exists.

        Parameters
        ----------
        variableAttrs : dict
            Variable attribute name and its entry value pair(s).
            The entry value is also a dictionary of variable id and value
            pair(s).  Variable id can be the variable name or its id number
            in the file. Use write_var function if the variable does not exist.
            For example::

                variableAttrs={}
                entries_1={}
                entries_1['var_name_1'] = 'abcd'
                entries_1['var_name_2'] = [12, 'cdf_int4']
                ....
                variableAttrs['attr_name_1']=entries_1
                entries_2={}
                entries_2['var_name_1'] = 'xyz'
                entries_2['var_name_2'] = [[12, 34], 'cdf_int4']
                ....
                variableAttrs['attr_name_2']=entries_2
                ....
                ....
                f.write_variableattrs(variableAttrs)
        """
        if not (isinstance(variableAttrs, dict)):
            raise ValueError("Variable attribute(s) not in dictionary form")
        dataType = None
        numElems = None
        with self.path.open("rb+") as f:
            f.seek(0, 2)  # EOF (appending)
            for attr, attrs in variableAttrs.items():
                if not (isinstance(attr, str)):
                    raise ValueError("Attribute name must be a string")
                    return
                if attr in self.gattrs:
                    raise ValueError(f"Variable attribute: {attr}" + " is already a global variable")
                    return
                if attr in self.vattrs:
                    attrNum = self.vattrs.index(attr)
                    offsetA = self.attrsinfo[attrNum][2]
                else:
                    attrNum, offsetA = self._write_adr(f, False, attr)
                entries = 0
                if attrs is None:
                    continue
                if not (isinstance(attrs, dict)):
                    raise ValueError("An attribute" "s attribute(s) not in dictionary form")
                entryNumX = -1
                poffset = -1
                for entryID, value in attrs.items():
                    if isinstance(entryID, str) and (not (entryID in self.zvars) and not (entryID in self.rvars)):
                        raise KeyError(f"{entryID} not found in the CDF")

                    if isinstance(entryID, numbers.Number) and (len(self.zvars) > 0 and len(self.rvars) > 0):
                        raise ValueError(f"{entryID} can not be used as the CDF has both zVariables and rVariables")

                    if isinstance(entryID, str):
                        try:
                            entryNum = self.zvars.index(entryID)
                            zVar = True
                        except Exception:
                            try:
                                entryNum = self.rvars.index(entryID)
                                zVar = False
                            except Exception:
                                raise KeyError(f"{entryID} not found")
                    else:
                        entryNum = int(entryID)
                        if len(self.zvars) > 0 and len(self.rvars) > 0:
                            raise ValueError(
                                "Can not use integer form for variable id as there ", "are both zVariables and rVaribales"
                            )
                        if len(self.zvars) > 0:
                            if entryNum >= len(self.zvars):
                                raise ValueError("Variable id: ", entryID, " not found")
                            else:
                                zVar = True
                        else:
                            if entryNum >= len(self.rvars):
                                raise ValueError("Variable id: ", entryID, " not found")
                            else:
                                zVar = False
                    if entryNum > entryNumX:
                        entryNumX = entryNum
                    if hasattr(value, "__len__") and not isinstance(value, str):
                        if len(value) == 2:
                            value2 = value[1]
                            dataType = self._datatype_token(value2)
                            if dataType > 0:
                                data = value[0]
                                if dataType == self.CDF_CHAR or dataType == self.CDF_UCHAR:
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        raise ValueError("Invalid variable attribute value")
                                    numElems = len(data)
                                elif dataType == self.CDF_EPOCH or dataType == self.CDF_EPOCH16 or dataType == self.CDF_TIME_TT2000:
                                    cvalue = []
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        numElems = len(data)
                                        for x in range(0, numElems):
                                            if isinstance(data[x], str):
                                                avalue = cdfepoch.CDFepoch.parse(data[x])
                                            else:
                                                avalue = data[x]
                                            if dataType == self.CDF_EPOCH16:
                                                cvalue.append(avalue.real)
                                                cvalue.append(avalue.imag)
                                            else:
                                                cvalue.append(avalue)
                                                data = cvalue
                                    else:
                                        if isinstance(data, str):
                                            data = cdfepoch.CDFepoch.parse(data)
                                        numElems = 1
                                else:
                                    if isinstance(data, list) or isinstance(data, tuple):
                                        numElems = len(data)
                                    else:
                                        numElems = 1
                            else:
                                data = value
                                numElems, dataType = self._datatype_define(value[0])
                                numElems = len(value)
                        else:
                            data = value
                            numElems, dataType = self._datatype_define(value[0])
                            numElems = len(value)
                    else:
                        data = value
                        numElems, dataType = self._datatype_define(value)
                        if numElems is None:
                            logger.warning("Unknown data")
                            return
                    offset = self._write_aedr(f, False, attrNum, entryNum, data, dataType, numElems, zVar)
                    if entries == 0:
                        if zVar:
                            # ADR's AzEDRhead
                            self._update_offset_value(f, offsetA + 48, 8, offset)
                        else:
                            # ADR's AgrEDRhead
                            self._update_offset_value(f, offsetA + 20, 8, offset)
                    else:
                        # ADR's ADRnext
                        self._update_offset_value(f, poffset + 12, 8, offset)
                    poffset = offset
                    entries = entries + 1
                if zVar:
                    # ADR's NzEntries
                    self._update_offset_value(f, offsetA + 56, 4, entries)
                    # ADR's MAXzEntry
                    self._update_offset_value(f, offsetA + 60, 4, entryNumX)
                else:
                    # ADR's NgrEntries
                    self._update_offset_value(f, offsetA + 36, 4, entries)
                    # ADR's MAXgrEntry
                    self._update_offset_value(f, offsetA + 40, 4, entryNumX)

    @is_open
    def write_var(self, var_spec, var_attrs=None, var_data=None):
        """
        Writes a variable, along with variable attributes and data.

        Parameters
        ----------
        var_spec : dict
            The specifications of the variable.

            The required/optional keys for creating a variable:
            Required keys:

            - ['Variable']: The name of the variable
            - ['Data_Type']: the CDF data type
            - ['Num_Elements']: The number of elements. Always 1 the
              for numeric type. The char length for string type.
            - ['Rec_Vary']: Record variance

            For zVariables:

            - ['Dim_Sizes']: The dimensional sizes for zVariables only.
              Use [] for 0-dimension. Each and
              every dimension is varying for zVariables.

            For rVariables:

            - ['Dim_Vary']: The dimensional variances for rVariables only.

            Optional keys:

            - ['Var_Type']: Whether the variable is a zVariable or
              rVariable. Valid values: "zVariable" and
              "rVariable". The default is "zVariable".
            - ['Sparse']: Whether the variable has sparse records.
              Valid values are "no_sparse", "pad_sparse",
              and "prev_sparse". The default is 'no_sparse'.
            - ['Compress']: Set the gzip compression level (0 to 9), 0 for
              no compression. The default is to compress
              with level 6 (done only if the compressed
              data is less than the uncompressed data).
            - ['Block_Factor']: The blocking factor, the number of
              records in a chunk when the variable is compressed.
            - ['Pad']: The padded value (in bytes, numpy.ndarray or string)

        var_attrs : dict
            {attribute:value} pairs.

            The attribute is the name of a variable attribute.
            The value can have its data type specified for the
            numeric data. If not, based on Python's type, a
            corresponding CDF type is assumed: CDF_INT4 for int,
            CDF_DOUBLE for float, CDF_EPOCH16 for complex and
            and CDF_INT8 for long.

            For example, the following defined attributes will
            have the same types in the CDF::

                var_attrs= { 'attr1':  'value1',
                          'attr2':  12.45,
                          'attr3':  [3,4,5],
                          .....
                        }

            With data type (in the list form)::

                var_attrs= { 'attr1':  'value1',
                          'attr2':  [12.45, 'CDF_DOUBLE'],
                          'attr3':  [[3,4,5], 'CDF_INT4'],
                          .....
                        }

        var_data :
            The data for the variable. If the variable is
            a regular variable without sparse records, it must
            be in a single structure of bytes, or numpy.ndarray
            for numeric variable, or str or list of strs for
            string variable.
            If the variable has sparse records, var_data should
            be presented in a list/tuple with two elements,
            the first being a list/tuple that contains the
            physical record number(s), the second being the variable
            data in bytes, numpy.ndarray, or a list of strings. Variable
            data can have just physical records' data (with the same
            number of records as the first element) or have data from both
            physical records and virtual records (which with filled data).
            The var_data has the form::

                [[rec_#1,rec_#2,rec_#3,...],
                [data_#1,data_#2,data_#3,...]]

            See the sample for its setup.

        """
        if not isinstance(var_spec, dict):
            raise TypeError("Variable should be in dictionary form.")

        # Get variable info from var_spec
        try:
            dataType = int(var_spec["Data_Type"])
            numElems = int(var_spec["Num_Elements"])
            name = var_spec["Variable"]
            recVary = var_spec["Rec_Vary"]
        except Exception as e:
            raise ValueError("Missing/invalid required spec for creating variable.") from e
        # Get whether or not it is a z variable
        var_type = var_spec.setdefault("Var_Type", "zvariable")
        if var_type.lower() == "zvariable":
            zVar = True
        else:
            var_spec["Var_Type"] = "rVariable"
            zVar = False

        if dataType == self.CDF_CHAR or dataType == self.CDF_UCHAR:
            if numElems < 1:
                raise ValueError("Invalid Num_Elements for string data type variable")
        else:
            if numElems != 1:
                raise ValueError("Invalid Num_Elements for numeric data type variable")
        # If its a z variable, get the dimension info
        # Otherwise, use r variable info
        if zVar:
            try:
                dimSizes = var_spec["Dim_Sizes"]
                numDims = len(dimSizes)
                dimVary = []
                for _ in range(0, numDims):
                    dimVary.append(True)
            except Exception:
                raise ValueError("Missing/invalid required spec for creating variable.")
        else:
            dimSizes = self.rdim_sizes
            numDims = self.num_rdim
            try:
                dimVary = var_spec["Dim_Vary"]
                if len(dimVary) != numDims:
                    raise ValueError("Invalid Dim_Vary size for the rVariable.")
            except Exception:
                raise ValueError("Missing/invalid required spec for Dim_Vary for rVariable")
        # Get Sparseness info
        sparse = self._sparse_token(var_spec.get("Sparse", "no_sparse"))
        # Get compression info
        compression = var_spec.get("Compress", 6)
        if isinstance(compression, int):
            if not 0 <= compression <= 9:
                compression = 0
        else:
            compression = 6 if compression else 0

        # Get blocking factor
        blockingfactor = int(var_spec.get("Block_Factor", 1))

        # Get pad value
        pad = var_spec.get("Pad", None)
        if hasattr(pad, "__len__"):
            pad = pad[0]

        if name in self.zvars or name in self.rvars:
            raise ValueError(f"{name} already exists")

        with self.path.open("rb+") as f:
            f.seek(0, 2)  # EOF (appending)
            varNum, offset = self._write_vdr(
                f, dataType, numElems, numDims, dimSizes, name, dimVary, recVary, sparse, blockingfactor, compression, pad, zVar
            )
            # Update the GDR pointers if needed
            if zVar:
                if len(self.zvars) == 1:
                    # GDR's zVDRhead
                    self._update_offset_value(f, self.gdr_head + 20, 8, offset)
            else:
                if len(self.rvars) == 1:
                    # GDR's rVDRhead
                    self._update_offset_value(f, self.gdr_head + 12, 8, offset)

            # Write the variable attributes
            if var_attrs is not None:
                self._write_var_attrs(f, varNum, var_attrs, zVar)

            # Write the actual data to the file
            if not (var_data is None):
                if sparse == 0:
                    varMaxRec = self._write_var_data_nonsparse(
                        f, zVar, varNum, dataType, numElems, recVary, compression, blockingfactor, var_data
                    )
                else:
                    notsupport = False
                    if not isinstance(var_data, (list, tuple)):
                        notsupport = True

                    if notsupport or len(var_data) != 2:
                        logger.warning(
                            "Sparse record #s and data are not of list/tuple form:\n"
                            " [ [rec_#1, rec_#2, rec_#3,    ],\n"
                            "   [data_#1, data_#2, data_#3, ....] ]"
                        )
                        return

                    # Format data into: [[recstart1, recend1, data1],
                    #                   [recstart2,recend2,data2], ...]
                    var_data = self._make_sparse_blocks(var_spec, var_data[0], var_data[1])

                    for block in var_data:
                        varMaxRec = self._write_var_data_sparse(f, zVar, varNum, dataType, numElems, recVary, block)
                # Update GDR MaxRec if writing an r variable
                if not zVar:
                    # GDR's rMaxRec
                    f.seek(self.gdr_head + 52)
                    maxRec = int.from_bytes(f.read(4), "big", signed=True)
                    if maxRec < varMaxRec:
                        self._update_offset_value(f, self.gdr_head + 52, 4, varMaxRec)

    def _write_var_attrs(self, f: io.BufferedWriter, varNum: int, var_attrs: Dict[str, Any], zVar: bool) -> None:
        """
        Writes ADRs and AEDRs for variables

        Parameters:
            f : file
                The open CDF file
            varNum : int
                The variable number for adding attributes
            var_attrs : dict
                A dictionary object full of variable attributes
            zVar : bool
                True if varNum is referencing a z variable

        Returns: None
        """

        if not isinstance(var_attrs, dict):
            raise TypeError("Variable attribute(s) should be in dictionary form.")

        for attr, entry in var_attrs.items():
            if attr in self.gattrs:
                logger.warning(f"Attribute: {attr}" + " already defined as a global attribute... Skip")
                continue

            if not (attr in self.attrs):
                attrNum, offset = self._write_adr(f, False, attr)
                if len(self.attrs) == 0:
                    # GDR's ADRhead
                    # TODO: fix this, grid_offset doesn't exsit
                    self._update_offset_value(f, self.grid_offset + 28, 8, offset)  # type: ignore
            else:
                attrNum = self.attrs.index(attr)
                offset = self.attrsinfo[attrNum][2]

            if entry is None:
                continue

            # Check if dataType was provided
            dataType = 0
            if hasattr(entry, "__len__") and not isinstance(entry, str):
                items = len(entry)
                if items == 2:
                    dataType = self._datatype_token(entry[1])

            if dataType > 0:
                # CDF data type defined in entry
                data = entry[0]
                if self._checklistofNums(data):
                    # All are numbers
                    if hasattr(data, "__len__") and not isinstance(data, str):
                        numElems = len(data)
                    else:
                        numElems = 1
                else:
                    # Then string(s) -- either in CDF_type or epoch in string(s)
                    if dataType == self.CDF_CHAR or dataType == self.CDF_UCHAR:
                        if hasattr(data, "__len__") and not isinstance(data, str):
                            items = len(data)
                            odata = data
                            data = ""
                            for x in range(0, items):
                                if x > 0:
                                    data += "\\N "
                                    data += odata[x]
                                else:
                                    data = odata[x]
                        numElems = len(data)
                    elif dataType == self.CDF_EPOCH or dataType == self.CDF_EPOCH16 or dataType == self.CDF_TIME_TT2000:
                        cvalue = []
                        if hasattr(data, "__len__") and not isinstance(data, str):
                            numElems = len(data)
                            for x in range(0, numElems):
                                cvalue.append(cdfepoch.CDFepoch.parse(data[x]))
                            data = cvalue
                        else:
                            data = cdfepoch.CDFepoch.parse(data)
                            numElems = 1
            else:
                # No data type defined...
                data = entry
                if hasattr(data, "__len__") and not isinstance(data, str):
                    numElems, dataType = self._datatype_define(entry[0])
                    if dataType == self.CDF_CHAR or dataType == self.CDF_UCHAR:
                        data = ""
                        for x in range(0, len(entry)):
                            if x > 0:
                                data += "\\N "
                                data += entry[x]
                            else:
                                data = entry[x]
                    numElems = len(data)
                else:
                    numElems, dataType = self._datatype_define(entry)

            offset = self._write_aedr(f, False, attrNum, varNum, data, dataType, numElems, zVar)

            self._update_aedr_link(f, attrNum, zVar, varNum, offset)

    def _write_var_data_nonsparse(
        self,
        f: io.BufferedWriter,
        zVar: bool,
        var: int,
        dataType: int,
        numElems: int,
        recVary: bool,
        compression: int,
        blockingfactor: int,
        indata: Union[np.ndarray, bytearray, Dict[str, np.ndarray]],
    ) -> int:
        """
        Creates VVRs and the corresponding VXRs full of "indata" data.
        If there is no compression, creates exactly one VXR and VVR
        If there is compression

        Parameters
        ----------
        f : file
            The open CDF file
        zVar : bool
            True if this is z variable data
        var : str
            The name of the variable
        dataType : int
            the CDF variable type
        numElems : int
            number of elements in each record
        recVary : bool
            True if each record is unque
        compression : int
            The amount of compression
        blockingfactor: int
            The size (in number of records) of a VVR data block
        indata : varies
            the data to write, should be a numpy or byte array

        Returns
        -------
        recs : int
            The number of records
        """

        numValues = self._num_values(zVar, var)
        dataTypeSize = self._datatype_size(dataType, numElems)
        if isinstance(indata, dict):
            indata = indata["Data"]

        # Deal with EPOCH16 data types
        if dataType == self.CDF_EPOCH16:
            epoch16 = []
            if hasattr(indata, "__len__") and not isinstance(indata, str):
                adata = indata[0]
                if isinstance(adata, complex):
                    recs = len(indata)
                    for x in range(0, recs):
                        epoch16.append(indata[x].real)
                        epoch16.append(indata[x].imag)
                    indata = np.array(epoch16)
            else:
                if isinstance(indata, complex):
                    epoch16.append(indata.real)
                    epoch16.append(indata.imag)
                    indata = epoch16

        # Convert to byte stream
        recs, data = self._convert_data(dataType, numElems, numValues, indata)

        if not recVary and len(data) != 0:
            recs = 1
        if zVar:
            vdr_offset = self.zvarsinfo[var][1]
        else:
            vdr_offset = self.rvarsinfo[var][1]

        usedEntries = 0
        numVXRs = 0
        if compression > 0:
            default_blockingfactor = math.ceil(self.BLOCKING_BYTES / (numValues * dataTypeSize))
            # If the given blocking factor is too small, use the default one
            # Will re-adjust if the records are less than this computed BF.
            if blockingfactor < default_blockingfactor:
                blockingfactor = default_blockingfactor
            if blockingfactor == 0:
                blockingfactor = 1

            # Update the blocking factor
            f.seek(vdr_offset + 80, 0)
            # VDR's BlockingFactor
            self._update_offset_value(f, vdr_offset + 80, 4, blockingfactor)

            # set blocking factor
            if recs < blockingfactor:
                blockingfactor = recs
            blocks = math.ceil(recs / blockingfactor)
            nEntries = self.NUM_VXR_ENTRIES
            VXRhead = None

            # Loop through blocks, create VVRs/CVVRs
            for x in range(0, blocks):
                startrec = x * blockingfactor
                startloc = startrec * numValues * dataTypeSize
                endrec = (x + 1) * blockingfactor - 1
                if endrec > (recs - 1):
                    endrec = recs - 1
                endloc = (endrec + 1) * numValues * dataTypeSize
                if endloc > len(data):
                    endrec = recs - 1
                    endloc = len(data)
                bdata = data[startloc:endloc]
                cdata = gzip_deflate(bdata, compression)
                if len(cdata) < len(bdata):
                    n1offset = self._write_cvvr(f, cdata)
                else:
                    n1offset = self._write_vvr(f, bdata)
                if x == 0:
                    # Create a VXR
                    VXRoffset = self._write_vxr(f)
                    VXRhead = VXRoffset
                    numVXRs = 1
                    self._update_vdr_vxrheadtail(f, vdr_offset, VXRoffset)
                if usedEntries < nEntries:
                    # Use the exisitng VXR
                    usedEntries = self._use_vxrentry(f, VXRoffset, startrec, endrec, n1offset)
                else:
                    # Create a new VXR and an upper level VXR, if needed.
                    # Two levels of VXRs are the maximum, which is simpler
                    # to implement.
                    savedVXRoffset = VXRoffset
                    VXRoffset = self._write_vxr(f)
                    numVXRs += 1
                    usedEntries = self._use_vxrentry(f, VXRoffset, startrec, endrec, n1offset)
                    # Edit the VXRnext field of the previous VXR
                    self._update_offset_value(f, savedVXRoffset + 12, 8, VXRoffset)
                    # Edit the VXRtail of the VDR
                    self._update_offset_value(f, vdr_offset + 36, 8, VXRoffset)

            # After we're done with the blocks, check the way
            # we have VXRs set up
            if numVXRs > self.NUM_VXRlvl_ENTRIES:
                newvxrhead, newvxrtail = self._add_vxr_levels_r(f, VXRhead, numVXRs)
                self._update_offset_value(f, vdr_offset + 28, 8, newvxrhead)
                self._update_offset_value(f, vdr_offset + 36, 8, newvxrtail)
        else:
            # Create one VVR and VXR, with one VXR entry
            offset = self._write_vvr(f, data)
            VXRoffset = self._write_vxr(f)
            usedEntries = self._use_vxrentry(f, VXRoffset, 0, recs - 1, offset)
            self._update_vdr_vxrheadtail(f, vdr_offset, VXRoffset)

        # VDR's MaxRec
        self._update_offset_value(f, vdr_offset + 24, 4, recs - 1)

        return recs - 1

    def _write_var_data_sparse(
        self,
        f: io.BufferedWriter,
        zVar: bool,
        var: int,
        dataType: int,
        numElems: int,
        recVary: bool,
        oneblock: Tuple[int, int, np.ndarray],
    ) -> int:
        """
        Writes a VVR and a VXR for this block of sparse data

        Parameters:
            f : file
                The open CDF file
            zVar : bool
                True if this is for a z variable
            var : int
                The variable number
            dataType : int
                The CDF data type of this variable
            numElems : int
                The number of elements in each record
            recVary : bool
                True if the value varies across records
            oneblock: list
                A list of data in the form [startrec, endrec, [data]]

        Returns:
            recend : int
                Just the "endrec" value input by the user in "oneblock"
        """

        rec_start = oneblock[0]
        rec_end = oneblock[1]
        indata = oneblock[2]
        numValues = self._num_values(zVar, var)

        # Convert oneblock[2] into a byte stream
        _, data = self._convert_data(dataType, numElems, numValues, indata)

        # Gather dimension information
        if zVar:
            vdr_offset = self.zvarsinfo[var][1]
        else:
            vdr_offset = self.rvarsinfo[var][1]

        # Write one VVR
        offset = self._write_vvr(f, data)
        f.seek(vdr_offset + 28, 0)

        # Get first VXR
        vxrOne = int.from_bytes(f.read(8), "big", signed=True)
        foundSpot = 0
        usedEntries = 0
        currentVXR = 0

        # Search through VXRs to find an open one
        while foundSpot == 0 and vxrOne > 0:
            # have a VXR
            f.seek(vxrOne, 0)
            currentVXR = f.tell()
            f.seek(vxrOne + 12, 0)
            vxrNext = int.from_bytes(f.read(8), "big", signed=True)
            nEntries = int.from_bytes(f.read(4), "big", signed=True)
            usedEntries = int.from_bytes(f.read(4), "big", signed=True)
            if usedEntries == nEntries:
                # all entries are used -- check the next vxr in link
                vxrOne = vxrNext
            else:
                # found a vxr with an vailable entry spot
                foundSpot = 1

        # vxrOne == 0 from vdr's vxrhead vxrOne == -1 from a vxr's vxrnext
        if vxrOne == 0 or vxrOne == -1:
            # no available vxr... create a new one
            currentVXR = self._create_vxr(f, rec_start, rec_end, vdr_offset, currentVXR, offset)
        else:
            self._use_vxrentry(f, currentVXR, rec_start, rec_end, offset)

        # Modify the VDR's MaxRec if needed
        f.seek(vdr_offset + 24, 0)
        recNumc = int.from_bytes(f.read(4), "big", signed=True)
        if rec_end > recNumc:
            self._update_offset_value(f, vdr_offset + 24, 4, rec_end)

        return rec_end

    def _create_vxr(self, f: io.BufferedWriter, recStart: int, recEnd: int, currentVDR: int, priorVXR: int, vvrOffset: int) -> int:
        """
        Create a VXR AND use a VXR

        Parameters:
            f : file
                The open CDF file
            recStart : int
                The start record of this block
            recEnd : int
                The ending record of this block
            currentVDR : int
                The byte location of the variables VDR
            priorVXR : int
                The byte location of the previous VXR
            vvrOffset : int
                The byte location of ther VVR

        Returns:
            vxroffset : int
                The byte location of the created vxr

        """
        # add a VXR, use an entry, and link it to the prior VXR if it exists
        vxroffset = self._write_vxr(f)
        self._use_vxrentry(f, vxroffset, recStart, recEnd, vvrOffset)
        if priorVXR == 0:
            # VDR's VXRhead
            self._update_offset_value(f, currentVDR + 28, 8, vxroffset)
        else:
            # VXR's next
            self._update_offset_value(f, priorVXR + 12, 8, vxroffset)
        # VDR's VXRtail
        self._update_offset_value(f, currentVDR + 36, 8, vxroffset)
        return vxroffset

    def _use_vxrentry(self, f: io.BufferedWriter, VXRoffset: int, recStart: int, recEnd: int, offset: int) -> int:
        """
        Adds a VVR pointer to a VXR
        """
        # Select the next unused entry in a VXR for a VVR/CVVR
        f.seek(VXRoffset + 20)
        # num entries
        numEntries = int.from_bytes(f.read(4), "big", signed=True)
        # used entries
        usedEntries = int.from_bytes(f.read(4), "big", signed=True)
        # VXR's First
        self._update_offset_value(f, VXRoffset + 28 + 4 * usedEntries, 4, recStart)
        # VXR's Last
        self._update_offset_value(f, VXRoffset + 28 + 4 * numEntries + 4 * usedEntries, 4, recEnd)
        # VXR's Offset
        self._update_offset_value(f, VXRoffset + 28 + 2 * 4 * numEntries + 8 * usedEntries, 8, offset)
        # VXR's NusedEntries
        usedEntries += 1
        self._update_offset_value(f, VXRoffset + 24, 4, usedEntries)
        return usedEntries

    def _add_vxr_levels_r(self, f: io.BufferedWriter, vxrhead: int, numVXRs: int) -> Tuple[int, int]:
        """
        Build a new level of VXRs... make VXRs more tree-like

        From:

        VXR1 -> VXR2 -> VXR3 -> VXR4 -> ... -> VXRn

        To:
                           new VXR1
                         /    |    \
                        VXR2 VXR3 VXR4
                       /      |      \
                             ...
                    VXR5  ..........  VXRn

        Parameters
        ----------
        f : file
            The open CDF file
        vxrhead : int
            The byte location of the first VXR for a variable
        numVXRs : int
            The total number of VXRs

        Returns
        -------
        newVXRhead : int
            The byte location of the newest VXR head
        newvxroff : int
            The byte location of the last VXR head
        """
        newNumVXRs = int(numVXRs / self.NUM_VXRlvl_ENTRIES)
        remaining = int(numVXRs % self.NUM_VXRlvl_ENTRIES)
        vxroff = vxrhead
        prevxroff = -1
        if remaining != 0:
            newNumVXRs += 1
        self.level += 1
        for x in range(0, newNumVXRs):
            newvxroff = self._write_vxr(f, numEntries=self.NUM_VXRlvl_ENTRIES)
            if x > 0:
                self._update_offset_value(f, prevxroff + 12, 8, newvxroff)
            else:
                newvxrhead = newvxroff
            prevxroff = newvxroff
            if x == (newNumVXRs - 1):
                if remaining == 0:
                    endEntry = self.NUM_VXRlvl_ENTRIES
                else:
                    endEntry = remaining
            else:
                endEntry = self.NUM_VXRlvl_ENTRIES
            for _ in range(0, endEntry):
                recFirst, recLast = self._get_recrange(f, vxroff)
                self._use_vxrentry(f, newvxroff, recFirst, recLast, vxroff)
                vxroff = self._read_offset_value(f, vxroff + 12, 8)
        vxroff = vxrhead

        # Break the horizontal links
        for x in range(0, numVXRs):
            nvxroff = self._read_offset_value(f, vxroff + 12, 8)
            self._update_offset_value(f, vxroff + 12, 8, 0)
            vxroff = nvxroff

        # Iterate this process if we're over NUM_VXRlvl_ENTRIES
        if newNumVXRs > self.NUM_VXRlvl_ENTRIES:
            return self._add_vxr_levels_r(f, newvxrhead, newNumVXRs)
        else:
            return newvxrhead, newvxroff

    def _update_vdr_vxrheadtail(self, f: io.BufferedWriter, vdr_offset: int, VXRoffset: int) -> None:
        """
        This sets a VXR to be the first and last VXR in the VDR
        """
        # VDR's VXRhead
        self._update_offset_value(f, vdr_offset + 28, 8, VXRoffset)
        # VDR's VXRtail
        self._update_offset_value(f, vdr_offset + 36, 8, VXRoffset)

    def _get_recrange(self, f: io.BufferedWriter, VXRoffset: int) -> Tuple[int, int]:
        """
        Finds the first and last record numbers pointed by the VXR
        Assumes the VXRs are in order
        """
        f.seek(VXRoffset + 20)
        # Num entries
        numEntries = int.from_bytes(f.read(4), "big", signed=True)
        # used entries
        usedEntries = int.from_bytes(f.read(4), "big", signed=True)
        # VXR's First record
        firstRec = int.from_bytes(f.read(4), "big", signed=True)
        # VXR's Last record
        f.seek(VXRoffset + 28 + (4 * numEntries + 4 * (usedEntries - 1)))
        lastRec = int.from_bytes(f.read(4), "big", signed=True)
        return firstRec, lastRec

    @staticmethod
    def _majority_token(major: str) -> int:
        """
        Returns the numberical type for a CDF row/column major type
        """
        majors = {"ROW_MAJOR": 1, "COLUMN_MAJOR": 2}
        try:
            return majors[major.upper()]
        except Exception:
            logger.warning(f"bad major.... {major}")
            return 0

    @staticmethod
    def _encoding_token(encoding: str) -> int:
        """
        Returns the numberical type for a CDF encoding type
        """
        encodings = {
            "NETWORK_ENCODING": 1,
            "SUN_ENCODING": 2,
            "VAX_ENCODING": 3,
            "DECSTATION_ENCODING": 4,
            "SGI_ENCODING": 5,
            "IBMPC_ENCODING": 6,
            "IBMRS_ENCODING": 7,
            "HOST_ENCODING": 8,
            "PPC_ENCODING": 9,
            "HP_ENCODING": 11,
            "NEXT_ENCODING": 12,
            "ALPHAOSF1_ENCODING": 13,
            "ALPHAVMSD_ENCODING": 14,
            "ALPHAVMSG_ENCODING": 15,
            "ALPHAVMSI_ENCODING": 16,
            "ARM_LITTLE_ENCODING": 17,
            "ARM_BIG_ENCODING": 18,
        }
        try:
            return encodings[encoding.upper()]
        except Exception:
            logger.warning(f"bad encoding.... {encoding}")
            return 0

    @staticmethod
    def _datatype_token(datatype: str) -> int:
        """
        Returns the numberical type for a CDF data type
        """
        datatypes = {
            "CDF_INT1": 1,
            "CDF_INT2": 2,
            "CDF_INT4": 4,
            "CDF_INT8": 8,
            "CDF_UINT1": 11,
            "CDF_UINT2": 12,
            "CDF_UINT4": 14,
            "CDF_REAL4": 21,
            "CDF_REAL8": 22,
            "CDF_EPOCH": 31,
            "CDF_EPOCH16": 32,
            "CDF_TIME_TT2000": 33,
            "CDF_BYTE": 41,
            "CDF_FLOAT": 44,
            "CDF_DOUBLE": 45,
            "CDF_CHAR": 51,
            "CDF_UCHAR": 52,
        }
        try:
            return datatypes[datatype.upper()]
        except Exception:
            return 0

    def _datatype_define(self, value: Union[str, int, float, complex, np.ndarray]) -> Tuple[int, int]:
        if isinstance(value, str):
            return len(value), self.CDF_CHAR
        else:
            numElems = 1
            if isinstance(value, int):
                return numElems, self.CDF_INT8
            elif isinstance(value, float):
                return numElems, self.CDF_DOUBLE
            elif isinstance(value, complex):
                return numElems, self.CDF_EPOCH16
            elif hasattr(value, "dtype"):
                # We are likely dealing with a numpy number at this point
                if value.dtype.type in (np.int8, np.int16, np.int32, np.int64):
                    return numElems, self.CDF_INT8
                elif value.dtype.type == np.complex128:
                    return numElems, self.CDF_EPOCH16
                elif value.dtype.type in (np.uint8, np.uint16, np.uint32, np.uint64):
                    return numElems, self.CDF_UINT4
                elif value.dtype.type in (np.float16, np.float32, np.float64):
                    return numElems, self.CDF_DOUBLE
                elif value.dtype.type == np.str_:
                    return numElems, self.CDF_CHAR
                else:
                    logger.warning("Invalid data type for data.... Skip")
                    return None, None
            else:
                logger.warning("Invalid data type for data.... Skip")
                return None, None

    @staticmethod
    def _datatype_size(datatype: int, numElms: int) -> int:
        """
        Gets datatype size

        Parameters:
            datatype : int
                CDF variable data type
            numElms : int
                number of elements

        Returns:
            numBytes : int
                The number of bytes for the data
        """
        sizes = {1: 1, 2: 2, 4: 4, 8: 8, 11: 1, 12: 2, 14: 4, 21: 4, 22: 8, 31: 8, 32: 16, 33: 8, 41: 1, 44: 4, 45: 8, 51: 1, 52: 1}
        try:
            if isinstance(datatype, int):
                if datatype == 51 or datatype == 52:
                    return numElms
                else:
                    return sizes[datatype] * numElms
            else:
                datatype = datatype.upper()
                if datatype == "CDF_INT1" or datatype == "CDF_UINT1" or datatype == "CDF_BYTE":
                    return 1 * numElms
                elif datatype == "CDF_INT2" or datatype == "CDF_UINT2":
                    return 2 * numElms
                elif datatype == "CDF_INT4" or datatype == "CDF_UINT4":
                    return 4 * numElms
                elif datatype == "CDF_INT8" or datatype == "CDF_TIME_TT2000":
                    return 8 * numElms
                elif datatype == "CDF_REAL4" or datatype == "CDF_FLOAT":
                    return 4 * numElms
                elif datatype == "CDF_REAL8" or datatype == "CDF_DOUBLE" or datatype == "CDF_EPOCH":
                    return 8 * numElms
                elif datatype == "CDF_EPOCH16":
                    return 16 * numElms
                elif datatype == "CDF_CHAR" or datatype == "CDF_UCHAR":
                    return numElms
                else:
                    return -1
        except Exception:
            return -1

    @staticmethod
    def _sparse_token(sparse: str) -> int:
        """
        Returns the numerical CDF value for sparseness.
        """

        sparses = {"no_sparse": 0, "pad_sparse": 1, "prev_sparse": 2}
        try:
            return sparses[sparse.lower()]
        except Exception:
            return 0

    def _write_cdr(self, f: io.BufferedWriter, major: int, encoding: int, checksum: int) -> int:
        f.seek(0, 2)
        byte_loc = f.tell()
        block_size = self.CDR_BASE_SIZE64 + self.CDF_COPYRIGHT_LEN
        section_type = self.CDR_
        gdr_loc = block_size + 8
        version = self.version
        release = self.release
        flag = 0
        if major == 1:
            flag = self._set_bit(flag, 0)
        flag = self._set_bit(flag, 1)
        if checksum:
            flag = self._set_bit(flag, 2)
            flag = self._set_bit(flag, 3)
        rfuA = 0
        rfuB = 0
        increment = self.increment
        identifier = 2
        rfuE = -1
        copy_right = (
            "\nCommon Data Format (CDF)\nhttps://cdf.gsfc.nasa.gov\n"
            + "Space Physics Data Facility\n"
            + "NASA/Goddard Space Flight Center\n"
            + "Greenbelt, Maryland 20771 USA\n"
            + "(User support: gsfc-cdf-support@lists.nasa.gov)\n"
        )

        cdr = bytearray(block_size)
        cdr[0:8] = struct.pack(">q", block_size)
        cdr[8:12] = struct.pack(">i", section_type)
        cdr[12:20] = struct.pack(">q", gdr_loc)
        cdr[20:24] = struct.pack(">i", version)
        cdr[24:28] = struct.pack(">i", release)
        cdr[28:32] = struct.pack(">i", encoding)
        cdr[32:36] = struct.pack(">i", flag)
        cdr[36:40] = struct.pack(">i", rfuA)
        cdr[40:44] = struct.pack(">i", rfuB)
        cdr[44:48] = struct.pack(">i", increment)
        cdr[48:52] = struct.pack(">i", identifier)
        cdr[52:56] = struct.pack(">i", rfuE)
        tofill = self.CDF_COPYRIGHT_LEN - len(copy_right)
        cdr[56:block_size] = (copy_right + "\0" * tofill).encode()
        f.write(cdr)

        return byte_loc

    def _write_gdr(self, f: io.BufferedWriter) -> int:
        f.seek(0, 2)
        byte_loc = f.tell()
        block_size = self.GDR_BASE_SIZE64 + 4 * self.num_rdim
        section_type = self.GDR_
        first_rvariable = 0
        first_zvariable = 0
        first_adr = 0
        eof = byte_loc + block_size
        num_rvariable = 0
        num_att = 0
        rMaxRec = -1
        num_rdim = self.num_rdim
        num_zvariable = 0
        UIR_head = 0
        rfuC = 0
        leapsecondlastupdate = 20170101
        rfuE = -1

        gdr = bytearray(block_size)
        gdr[0:8] = struct.pack(">q", block_size)
        gdr[8:12] = struct.pack(">i", section_type)
        gdr[12:20] = struct.pack(">q", first_rvariable)
        gdr[20:28] = struct.pack(">q", first_zvariable)
        gdr[28:36] = struct.pack(">q", first_adr)
        gdr[36:44] = struct.pack(">q", eof)
        gdr[44:48] = struct.pack(">i", num_rvariable)
        gdr[48:52] = struct.pack(">i", num_att)
        gdr[52:56] = struct.pack(">i", rMaxRec)
        gdr[56:60] = struct.pack(">i", num_rdim)
        gdr[60:64] = struct.pack(">i", num_zvariable)
        gdr[64:72] = struct.pack(">q", UIR_head)
        gdr[72:76] = struct.pack(">i", rfuC)
        gdr[76:80] = struct.pack(">i", leapsecondlastupdate)
        gdr[80:84] = struct.pack(">i", rfuE)
        if num_rdim > 0:
            for i in range(0, num_rdim):
                gdr[84 + i * 4 : 84 + (i + 1) * 4] = struct.pack(">i", self.rdim_sizes[i])
        f.write(gdr)

        return byte_loc

    def _write_adr(self, f: io.BufferedWriter, gORv: bool, name: str) -> Tuple[int, int]:
        """
        Writes and ADR to the end of the file.

        Additionally, it will update the offset values to either the previous ADR
        or the ADRhead field in the GDR.

        Parameters
        ----------
        f : file
            The open CDF file
        gORv : bool
            True if a global attribute, False if variable attribute
        name : str
            name of the attribute

        Returns
        -------
        num : int
            The attribute number
        byte_loc : int
            The current location in file f
        """

        f.seek(0, 2)
        byte_loc = f.tell()
        block_size = self.ADR_BASE_SIZE64
        section_type = self.ADR_
        nextADR = 0
        headAgrEDR = 0
        if gORv:
            scope = 1
        else:
            scope = 2
        num = len(self.attrs)
        ngrEntries = 0
        maxgrEntry = -1
        rfuA = 0
        headAzEDR = 0
        nzEntries = 0
        maxzEntry = -1
        rfuE = -1

        adr = bytearray(block_size)
        adr[0:8] = struct.pack(">q", block_size)
        adr[8:12] = struct.pack(">i", section_type)
        adr[12:20] = struct.pack(">q", nextADR)
        adr[20:28] = struct.pack(">q", headAgrEDR)
        adr[28:32] = struct.pack(">i", scope)
        adr[32:36] = struct.pack(">i", num)
        adr[36:40] = struct.pack(">i", ngrEntries)
        adr[40:44] = struct.pack(">i", maxgrEntry)
        adr[44:48] = struct.pack(">i", rfuA)
        adr[48:56] = struct.pack(">q", headAzEDR)
        adr[56:60] = struct.pack(">i", nzEntries)
        adr[60:64] = struct.pack(">i", maxzEntry)
        adr[64:68] = struct.pack(">i", rfuE)
        tofill = 256 - len(name)
        adr[68:324] = (name + "\0" * tofill).encode()
        f.write(adr)
        info = (name, scope, byte_loc)
        self.attrsinfo[num] = info
        if scope == 1:
            self.gattrs.append(name)
        else:
            self.vattrs.append(name)

        self.attrs.append(name)
        if num > 0:
            # ADR's ADRnext
            self._update_offset_value(f, self.attrsinfo[num - 1][2] + 12, 8, byte_loc)
        else:
            # GDR's ADRhead
            self._update_offset_value(f, self.gdr_head + 28, 8, byte_loc)

        # GDR's NumAttr
        self._update_offset_value(f, self.gdr_head + 48, 4, num + 1)

        return num, byte_loc

    def _write_aedr(
        self,
        f: io.BufferedWriter,
        gORz: bool,
        attrNum: int,
        entryNum: int,
        value: Union[Number, np.ndarray],
        pdataType: int,
        pnumElems: int,
        zVar: bool,
    ) -> int:
        """
        Writes an aedr into the end of the file.

        Parameters
        ----------
        f : file
            The current open CDF file
        gORz : bool
            True if this entry is for a global or z variable, False if r variable
        attrNum : int
            Number of the attribute this aedr belongs to.
        entryNum : int
            Number of the entry
        value :
            The value of this entry
        pdataType : int
            The CDF data type of the value
        pnumElems : int
            Number of elements in the value.
        zVar : bool
            True if this entry belongs to a z variable

        Returns
        -------
        byte_loc : int
            This current location in the file after writing the aedr.
        """
        f.seek(0, 2)
        byte_loc = f.tell()
        if gORz or zVar != True:
            section_type = self.AgrEDR_
        else:
            section_type = self.AzEDR_
        nextAEDR = 0

        if pdataType is None:
            # Figure out Data Type if not supplied
            if not isinstance(value, Number):
                avalue = value[0]
            else:
                avalue = value
            if isinstance(avalue, int):
                pdataType = self.CDF_INT8
            elif isinstance(avalue, float):
                pdataType = self.CDF_FLOAT
            elif isinstance(avalue, complex):
                pdataType = self.CDF_EPOCH16
            else:
                # assume a boolean
                pdataType = self.CDF_INT1

        if pnumElems is None:
            # Figure out number of elements if not supplied
            if isinstance(value, str):
                pdataType = self.CDF_CHAR
                pnumElems = 1 if len(value) == 0 else len(value)
            else:
                if hasattr(value, "__len__") and not isinstance(value, str):
                    pnumElems = len(value)
                else:
                    pnumElems = 1

        dataType = pdataType
        numElems = pnumElems

        rfuB = 0
        rfuC = 0
        rfuD = -1
        rfuE = -1
        if gORz:
            numStrings = 0
        else:
            if isinstance(value, str):
                numStrings = value.count("\\N ") + 1
            else:
                numStrings = 0
        recs, cdata = self._convert_data(dataType, numElems, 1, value)
        if dataType == 51:
            numElems = 1 if len(cdata) == 0 else len(cdata)
        if len(cdata) == 0:
            value_size = 1
            cdata = "\x00".encode()
        else:
            value_size = len(cdata)
        block_size = value_size + 56
        aedr = bytearray(block_size)
        aedr[0:8] = struct.pack(">q", block_size)
        aedr[8:12] = struct.pack(">i", section_type)
        aedr[12:20] = struct.pack(">q", nextAEDR)
        aedr[20:24] = struct.pack(">i", attrNum)
        aedr[24:28] = struct.pack(">i", dataType)
        aedr[28:32] = struct.pack(">i", entryNum)
        aedr[32:36] = struct.pack(">i", numElems)
        aedr[36:40] = struct.pack(">i", numStrings)
        aedr[40:44] = struct.pack(">i", rfuB)
        aedr[44:48] = struct.pack(">i", rfuC)
        aedr[48:52] = struct.pack(">i", rfuD)
        aedr[52:56] = struct.pack(">i", rfuE)
        aedr[56:block_size] = cdata
        f.write(aedr)

        return byte_loc

    def _write_vdr(
        self,
        f: io.BufferedWriter,
        cdataType: int,
        numElems: int,
        numDims: int,
        dimSizes: List[int],
        name: str,
        dimVary: List[bool],
        recVary: bool,
        sparse: int,
        blockingfactor: int,
        compression: int,
        pad: str,
        zVar: bool,
    ) -> Tuple[int, int]:
        """
        Writes a VDR block to the end of the file.

        Parameters
        ----------
        f : file
            The open CDF file
        cdataType : int
            The CDF data type
        numElems : int
            The number of elements in the variable
        numDims : int
            The number of dimensions in the variable
        dimSizes : int
            The size of each dimension
        name : str
            The name of the variable
        dimVary : array of bool
            Bool array of size numDims.
            True if a dimension is physical, False if a dimension is not physical
        recVary : bool
            True if each record is unique
        sparse : bool
            True if using sparse records
        blockingfactor: int
            No idea
        compression : int
            The level of compression between 0-9
        pad : num
            The pad values to insert
        zVar : bool
            True if this variable is a z variable

        Returns
        -------
        num : int
            The number of the variable
        byte_loc : int
            The current byte location within the file
        """

        if zVar:
            block_size = self.zVDR_BASE_SIZE64
            section_type = self.zVDR_
        else:
            block_size = self.rVDR_BASE_SIZE64
            section_type = self.rVDR_

        nextVDR = 0
        dataType = cdataType
        if dataType == -1:
            raise ValueError("Bad data type.")

        maxRec = -1
        headVXR = 0
        tailVXR = 0
        flags = 0
        if recVary:
            flags = self._set_bit(flags, 0)
        flags = self._set_bit(flags, 1)
        sRecords = sparse
        rfuB = 0
        rfuC = -1
        rfuF = -1
        if zVar:
            num = len(self.zvars)
        else:
            num = len(self.rvars)

        if compression > 0:
            offsetCPRorSPR = self._write_cpr(f, self.GZIP_COMPRESSION, compression)
            flags = self._set_bit(flags, 2)
        else:
            offsetCPRorSPR = -1

        if blockingfactor is None:
            blockingFactor = 1
        else:
            blockingFactor = blockingfactor

        # Increase the block size to account for "zDimSizes" and "DimVarys" fields
        if numDims > 0:
            if zVar:
                block_size = block_size + numDims * 8
            else:
                block_size = block_size + numDims * 4

        # Determine pad value
        if pad is not None:
            if dataType == 51 or dataType == 52:
                # pad needs to be the correct number of elements
                if len(pad) < numElems:
                    pad += "\0" * (numElems - len(pad))
                elif len(pad) > numElems:
                    pad = pad[:numElems]
                pad_bytes = pad.encode()
            else:
                dummy, pad_bytes = self._convert_data(dataType, numElems, 1, pad)
        else:
            pad_bytes = self._default_pad(dataType, numElems)

        f.seek(0, 2)
        byte_loc = f.tell()
        block_size += len(pad_bytes)
        vdr = bytearray(block_size)
        # if (dataType == 51):
        #    numElems = len(pad)
        vdr[0:8] = struct.pack(">q", block_size)
        vdr[8:12] = struct.pack(">i", section_type)
        vdr[12:20] = struct.pack(">q", nextVDR)
        vdr[20:24] = struct.pack(">i", dataType)
        vdr[24:28] = struct.pack(">i", maxRec)
        vdr[28:36] = struct.pack(">q", headVXR)
        vdr[36:44] = struct.pack(">q", tailVXR)
        vdr[44:48] = struct.pack(">i", flags)
        vdr[48:52] = struct.pack(">i", sRecords)
        vdr[52:56] = struct.pack(">i", rfuB)
        vdr[56:60] = struct.pack(">i", rfuC)
        vdr[60:64] = struct.pack(">i", rfuF)
        vdr[64:68] = struct.pack(">i", numElems)
        vdr[68:72] = struct.pack(">i", num)
        vdr[72:80] = struct.pack(">q", offsetCPRorSPR)
        vdr[80:84] = struct.pack(">i", blockingFactor)
        tofill = 256 - len(name)
        vdr[84:340] = (name + "\0" * tofill).encode()
        if zVar:
            vdr[340:344] = struct.pack(">i", numDims)
            if numDims > 0:
                for i in range(0, numDims):
                    vdr[344 + i * 4 : 344 + (i + 1) * 4] = struct.pack(">i", dimSizes[i])
                ist = 344 + numDims * 4
                for i in range(0, numDims):
                    vdr[ist + i * 4 : ist + (i + 1) * 4] = struct.pack(">i", self.VARY)
            ist = 344 + 8 * numDims
        else:
            if numDims > 0:
                for i in range(0, numDims):
                    if dimVary[i] or dimVary[i] != 0:
                        vdr[340 + i * 4 : 344 + i * 4] = struct.pack(">i", self.VARY)
                    else:
                        vdr[340 + i * 4 : 344 + i * 4] = struct.pack(">i", self.NOVARY)
            ist = 340 + 4 * numDims
        vdr[ist:block_size] = pad_bytes
        f.write(vdr)

        # Set variable info

        if not zVar:
            numDims = self.num_rdim
            dimSizes = self.rdim_sizes

        info = (name, byte_loc, numDims, dimSizes, dimVary)

        # Update the pointers from the CDR/previous VDR
        if zVar:
            self.zvarsinfo[num] = info
            self.zvars.append(name)
            if num > 0:
                # VDR's VDRnext
                self._update_offset_value(f, self.zvarsinfo[num - 1][1] + 12, 8, byte_loc)
            # GDR's NzVars
            self._update_offset_value(f, self.gdr_head + 60, 4, num + 1)
        else:
            self.rvarsinfo[num] = info
            self.rvars.append(name)
            if num > 0:
                # VDR's VDRnext
                self._update_offset_value(f, self.rvarsinfo[num - 1][1] + 12, 8, byte_loc)
            # GDR's NrVars
            self._update_offset_value(f, self.gdr_head + 44, 4, num + 1)

        return num, byte_loc

    def _write_vxr(self, f: io.BufferedWriter, numEntries: Optional[int] = None) -> int:
        """
        Creates a VXR at the end of the file.
        Returns byte location of the VXR
        The First, Last, and Offset fields will need to be filled in later
        """

        f.seek(0, 2)
        byte_loc = f.tell()
        section_type = self.VXR_
        nextVXR = 0
        if numEntries is None:
            nEntries = self.NUM_VXR_ENTRIES
        else:
            nEntries = int(numEntries)
        block_size = self.VXR_BASE_SIZE64 + (4 + 4 + 8) * nEntries
        nUsedEntries = 0
        firsts = [-1] * nEntries
        lasts = [-1] * nEntries
        offsets = [-1] * nEntries

        vxr = bytearray(block_size)
        vxr[0:8] = struct.pack(">q", block_size)
        vxr[8:12] = struct.pack(">i", section_type)
        vxr[12:20] = struct.pack(">q", nextVXR)
        vxr[20:24] = struct.pack(">i", nEntries)
        vxr[24:28] = struct.pack(">i", nUsedEntries)
        estart = 28 + 4 * nEntries
        vxr[28:estart] = struct.pack(">%si" % nEntries, *firsts)
        eend = estart + 4 * nEntries
        vxr[estart:eend] = struct.pack(">%si" % nEntries, *lasts)
        vxr[eend:block_size] = struct.pack(">%sq" % nEntries, *offsets)
        f.write(vxr)
        return byte_loc

    def _write_vvr(self, f: io.BufferedWriter, data: bytes) -> int:
        """
        Writes a vvr to the end of file "f" with the byte stream "data".
        """
        f.seek(0, 2)
        byte_loc = f.tell()
        block_size = self.VVR_BASE_SIZE64 + len(data)
        section_type = self.VVR_

        vvr1 = bytearray(12)
        vvr1[0:8] = struct.pack(">q", block_size)
        vvr1[8:12] = struct.pack(">i", section_type)
        f.write(vvr1)
        f.write(data)

        return byte_loc

    def _write_cpr(self, f: io.BufferedWriter, cType: int, parameter: int) -> int:
        """
        Write compression info to the end of the file in a CPR.
        """
        f.seek(0, 2)
        byte_loc = f.tell()
        block_size = self.CPR_BASE_SIZE64 + 4
        section_type = self.CPR_
        rfuA = 0
        pCount = 1

        cpr = bytearray(block_size)
        cpr[0:8] = struct.pack(">q", block_size)
        cpr[8:12] = struct.pack(">i", section_type)
        cpr[12:16] = struct.pack(">i", cType)
        cpr[16:20] = struct.pack(">i", rfuA)
        cpr[20:24] = struct.pack(">i", pCount)
        cpr[24:28] = struct.pack(">i", parameter)
        f.write(cpr)

        return byte_loc

    def _write_cvvr(self, f: io.BufferedWriter, data: Any) -> int:
        """
        Write compressed "data" variable to the end of the file in a CVVR
        """
        f.seek(0, 2)
        byte_loc = f.tell()
        cSize = len(data)
        block_size = self.CVVR_BASE_SIZE64 + cSize
        section_type = self.CVVR_
        rfuA = 0

        cvvr1 = bytearray(24)
        cvvr1[0:8] = struct.pack(">q", block_size)
        cvvr1[8:12] = struct.pack(">i", section_type)
        cvvr1[12:16] = struct.pack(">i", rfuA)
        cvvr1[16:24] = struct.pack(">q", cSize)
        f.write(cvvr1)
        f.write(data)

        return byte_loc

    def _write_ccr(self, f: io.BufferedWriter, g: io.BufferedWriter, level: int) -> None:
        """
        Write a CCR to file "g" from file "f" with level "level".
        Currently, only handles gzip compression.

        Parameters:
            f : file
                Uncompressed file to read from
            g : file
                File to read the compressed file into
            level : int
                The level of the compression from 0 to 9

        Returns: None

        """
        f.seek(8)
        data = f.read()
        uSize = len(data)
        section_type = self.CCR_
        rfuA = 0
        cData = gzip_deflate(data, level)
        block_size = self.CCR_BASE_SIZE64 + len(cData)
        cprOffset = 0
        ccr1 = bytearray(32)
        # ccr1[0:4] = binascii.unhexlify(CDF.V3magicNUMBER_1)
        # ccr1[4:8] = binascii.unhexlify(CDF.V3magicNUMBER_2c)
        ccr1[0:8] = struct.pack(">q", block_size)
        ccr1[8:12] = struct.pack(">i", section_type)
        ccr1[12:20] = struct.pack(">q", cprOffset)
        ccr1[20:28] = struct.pack(">q", uSize)
        ccr1[28:32] = struct.pack(">i", rfuA)
        g.seek(0, 2)
        g.write(ccr1)
        g.write(cData)
        cprOffset = self._write_cpr(g, self.GZIP_COMPRESSION, level)
        self._update_offset_value(g, 20, 8, cprOffset)

    def _convert_option(self) -> str:
        """
        Determines which symbol to use for numpy conversions
        > : a little endian system to big endian ordering
        < : a big endian system to little endian ordering
        = : No conversion
        """
        data_endian = "little"
        if (
            self._encoding == 1
            or self._encoding == 2
            or self._encoding == 5
            or self._encoding == 7
            or self._encoding == 9
            or self._encoding == 11
            or self._encoding == 12
            or self._encoding == 18
        ):
            data_endian = "big"
        if sys.byteorder == "little" and data_endian == "big":
            # big->little
            order = ">"
        elif sys.byteorder == "big" and data_endian == "little":
            # little->big
            order = "<"
        else:
            # no conversion
            order = "="

        return order

    @staticmethod
    def _convert_type(data_type: int) -> str:
        """
        Converts CDF data types into python types
        """
        if data_type in (1, 41):
            dt_string = "b"
        elif data_type == 2:
            dt_string = "h"
        elif data_type == 4:
            dt_string = "i"
        elif data_type in (8, 33):
            dt_string = "q"
        elif data_type == 11:
            dt_string = "B"
        elif data_type == 12:
            dt_string = "H"
        elif data_type == 14:
            dt_string = "I"
        elif data_type in (21, 44):
            dt_string = "f"
        elif data_type in (22, 45, 31):
            dt_string = "d"
        elif data_type == 32:
            dt_string = "d"
        elif data_type in (51, 52):
            dt_string = "s"
        else:
            dt_string = ""

        return dt_string

    @staticmethod
    def _convert_nptype(data_type: int, data: Any) -> bytes:
        """
        Converts "data" of CDF type "data_type" into a numpy array
        """
        if data_type in (1, 41):
            return np.int8(data).tobytes()
        elif data_type == 2:
            return np.int16(data).tobytes()
        elif data_type == 4:
            return np.int32(data).tobytes()
        elif (data_type == 8) or (data_type == 33):
            return np.int64(data).tobytes()
        elif data_type == 11:
            return np.uint8(data).tobytes()
        elif data_type == 12:
            return np.uint16(data).tobytes()
        elif data_type == 14:
            return np.uint32(data).tobytes()
        elif (data_type == 21) or (data_type == 44):
            return np.float32(data).tobytes()
        elif (data_type == 22) or (data_type == 45) or (data_type == 31):
            return np.float64(data).tobytes()
        elif data_type == 32:
            return np.complex128(data).tobytes()
        elif ((data_type) == 51) or ((data_type) == 52):
            utf8_bytes = np.asarray(data).astype("U").tobytes()
            return utf8_bytes.decode().replace("\x00", "").encode("ASCII")
        else:
            return data

    def _default_pad(self, data_type: int, numElems: int) -> bytes:
        """
        Determines the default pad data for a "data_type"
        """
        order = self._convert_option()
        if (data_type == 1) or (data_type == 41):
            pad_value = struct.pack(order + "b", -127)
        elif data_type == 2:
            pad_value = struct.pack(order + "h", -32767)
        elif data_type == 4:
            pad_value = struct.pack(order + "i", -2147483647)
        elif (data_type == 8) or (data_type == 33):
            pad_value = struct.pack(order + "q", -9223372036854775807)
        elif data_type == 11:
            pad_value = struct.pack(order + "B", 254)
        elif data_type == 12:
            pad_value = struct.pack(order + "H", 65534)
        elif data_type == 14:
            pad_value = struct.pack(order + "I", 4294967294)
        elif (data_type == 21) or (data_type == 44):
            pad_value = struct.pack(order + "f", -1.0e30)
        elif (data_type == 22) or (data_type == 45):
            pad_value = struct.pack(order + "d", -1.0e30)
        elif data_type == 31:
            pad_value = struct.pack(order + "d", 0.0)
        elif data_type == 32:
            pad_value = struct.pack(order + "2d", *[0.0, 0.0])
        elif (data_type == 51) or (data_type == 52):
            tmpPad = str(" " * numElems).encode()
            form = str(numElems)
            pad_value = struct.pack(form + "b", *tmpPad)
        return pad_value

    def _convert_data(self, data_type: int, num_elems: int, num_values: int, indata: Any) -> Tuple[int, bytes]:
        """
        Converts "indata" into a byte stream

        Parameters
        ----------
        data_type : int
            The CDF file data type

        num_elems : int
            The number of elements in the data

        num_values : int
            The number of values in each record

        indata : (varies)
            The data to be converted

        Returns
        -------
        recs : int
            The number of records generated by converting indata
        odata : byte stream
            The stream of bytes to write to the CDF file
        """

        recSize = self._datatype_size(data_type, num_elems) * num_values
        if isinstance(indata, list) or isinstance(indata, tuple):
            if (num_values != 1) and (len(indata) != num_values):
                raise Exception("Use numpy for inputting multidimensional arrays")
            size = len(indata)
            if data_type == self.CDF_CHAR or data_type == self.CDF_UCHAR:
                odata = ""
                for x in range(0, size):
                    adata = indata[x]
                    if isinstance(adata, list) or isinstance(adata, tuple):
                        size2 = len(adata)
                        for y in range(0, size2):
                            odata += adata[y].ljust(num_elems, "\x00")
                    else:
                        size2 = 1
                        odata += adata.ljust(num_elems, "\x00")
                recs = int((size * size2) / num_values)
                return recs, odata.encode()
            else:
                tofrom = self._convert_option()
                dt_string = self._convert_type(data_type)
                recs = int(size / num_values)
                if data_type == self.CDF_EPOCH16 and isinstance(indata[0], complex):
                    complex_data = []
                    for x in range(0, recs):
                        acomplex = indata[x]
                        complex_data.append(acomplex.real)
                        complex_data.append(acomplex.imag)
                    size = 2 * size
                    indata = complex_data
                if data_type == self.CDF_EPOCH16 and not isinstance(indata[0], complex):
                    recs = int(recs / 2)
                form = tofrom + str(size) + dt_string
                return recs, struct.pack(form, *indata)
        elif isinstance(indata, bytes):
            tofrom = self._convert_option()
            recs = int(len(indata) / recSize)
            dt_string = self._convert_type(data_type)
            size = recs * num_values * num_elems
            if data_type == self.CDF_EPOCH16:
                size = size * 2
            form = str(size) + dt_string
            form2 = tofrom + form
            datau = struct.unpack(form, indata)
            return recs, struct.pack(form2, *datau)
        elif isinstance(indata, np.ndarray):
            if data_type == self.CDF_CHAR or data_type == self.CDF_UCHAR:
                size = indata.size
                odata = ""
                if size >= 1:
                    for x in range(0, size):
                        if hasattr(indata, "len"):
                            adata = indata[x]
                        else:
                            adata = indata
                        if isinstance(adata, list) or isinstance(adata, tuple):
                            size2 = len(adata)
                            for y in range(0, size2):
                                odata += str(adata[y]).ljust(num_elems, "\x00")
                        elif isinstance(adata, np.ndarray):
                            size2 = adata.size
                            for y in range(0, size2):
                                if hasattr(adata, "len"):
                                    bdata = adata[y]
                                else:
                                    bdata = adata
                                odata += str(bdata).ljust(num_elems, "\x00")
                        else:
                            size2 = 1
                            odata += str(adata).ljust(num_elems, "\x00")
                else:
                    adata = ""
                    size2 = 1
                    odata += str(adata).ljust(num_elems, "\x00")
                recs = int((size * size2) / num_values)
                return recs, odata.encode()
            else:
                tofrom = self._convert_option()
                npdata = self._convert_nptype(data_type, indata)
                if indata.size == 0:  # Check if the data being read in is zero size
                    recs = 0
                elif indata.size == num_values * num_elems:  # Check if only one record is being read in
                    recs = 1
                else:
                    recs = len(indata)
                dt_string = self._convert_type(data_type)
                if data_type == self.CDF_EPOCH16:
                    num_elems = 2 * num_elems
                form = str(recs * num_values * num_elems) + dt_string
                form2 = tofrom + str(recs * num_values * num_elems) + dt_string
                datau = struct.unpack(form, npdata)
                return recs, struct.pack(form2, *datau)
        elif isinstance(indata, str):
            return 1, indata.ljust(num_elems, "\x00").encode()
        else:
            tofrom = self._convert_option()
            dt_string = self._convert_type(data_type)
            if data_type == self.CDF_EPOCH16:
                num_elems = 2 * num_elems
            try:
                recs = int(len(indata) / recSize)
            except Exception:
                recs = 1
            if data_type == self.CDF_EPOCH16:
                complex_data = []
                if recs > 1:
                    for x in range(0, recs):
                        acomplex = indata[x]
                        complex_data.append(acomplex.real)
                        complex_data.append(acomplex.imag)
                else:
                    complex_data.append(indata.real)
                    complex_data.append(indata.imag)
                indata = complex_data
            form = tofrom + str(recs * num_values * num_elems) + dt_string
            if recs * num_values * num_elems > 1:
                return recs, struct.pack(form, *indata)
            else:
                return recs, struct.pack(form, indata)

    def _num_values(self, zVar: bool, varNum: int) -> int:
        """
        Determines the number of values in a record.
        Set zVar=True if this is a zvariable.
        """
        values = 1
        if zVar:
            numDims = self.zvarsinfo[varNum][2]
            dimSizes = self.zvarsinfo[varNum][3]
            dimVary = self.zvarsinfo[varNum][4]
        else:
            numDims = self.rvarsinfo[varNum][2]
            dimSizes = self.rvarsinfo[varNum][3]
            dimVary = self.rvarsinfo[varNum][4]
        if numDims < 1:
            return values
        else:
            for x in range(0, numDims):
                if zVar:
                    values = values * dimSizes[x]
                else:
                    if dimVary[x] != 0:
                        values = values * dimSizes[x]
            return values

    def _read_offset_value(self, f: io.BufferedWriter, offset: int, size: int) -> int:
        """
        Reads an integer value from file "f" at location "offset".
        """
        f.seek(offset, 0)
        if size == 8:
            return int.from_bytes(f.read(8), "big", signed=True)
        else:
            return int.from_bytes(f.read(4), "big", signed=True)

    def _update_offset_value(self, f: io.BufferedWriter, offset: int, size: int, value: Any) -> None:
        """
        Writes "value" into location "offset" in file "f".
        """
        f.seek(offset, 0)
        if size == 8:
            f.write(struct.pack(">q", value))
        else:
            f.write(struct.pack(">i", value))

    def _update_aedr_link(self, f: io.BufferedWriter, attrNum: int, zVar: bool, varNum: int, offset: int) -> None:
        """
        Updates variable aedr links

        Parameters
        ----------
        f : file
            The open CDF file
        attrNum : int
            The number of the attribute to change
        zVar : bool
            True if we are updating a z variable attribute
        varNum : int
            The variable number associated with this aedr
        offset : int
            The offset in the file to the AEDR
        """

        # The offset to this AEDR's ADR
        adr_offset = self.attrsinfo[attrNum][2]

        # Get the number of entries
        if zVar:
            f.seek(adr_offset + 56, 0)
            # ADR's NzEntries
            entries = int.from_bytes(f.read(4), "big", signed=True)
            # ADR's MAXzEntry
            maxEntry = int.from_bytes(f.read(4), "big", signed=True)
        else:
            f.seek(adr_offset + 36, 0)
            # ADR's NgrEntries
            entries = int.from_bytes(f.read(4), "big", signed=True)
            # ADR's MAXgrEntry
            maxEntry = int.from_bytes(f.read(4), "big", signed=True)

        if entries == 0:
            # If this is the first entry, update the ADR to reflect
            if zVar:
                # AzEDRhead
                self._update_offset_value(f, adr_offset + 48, 8, offset)
                # NzEntries
                self._update_offset_value(f, adr_offset + 56, 4, 1)
                # MaxzEntry
                self._update_offset_value(f, adr_offset + 60, 4, varNum)
            else:
                # AgrEDRhead
                self._update_offset_value(f, adr_offset + 20, 8, offset)
                # NgrEntries
                self._update_offset_value(f, adr_offset + 36, 4, 1)
                # MaxgrEntry
                self._update_offset_value(f, adr_offset + 40, 4, varNum)
        else:
            if zVar:
                f.seek(adr_offset + 48, 0)
                head = int.from_bytes(f.read(8), "big", signed=True)
            else:
                f.seek(adr_offset + 20, 0)
                head = int.from_bytes(f.read(8), "big", signed=True)
            aedr = head
            previous_aedr = head
            done = False
            # For each entry, re-adjust file offsets if needed
            for _ in range(0, entries):
                f.seek(aedr + 28, 0)
                # Get variable number for entry
                num = int.from_bytes(f.read(4), "big", signed=True)
                if num > varNum:
                    # insert an aedr to the chain
                    # AEDRnext
                    self._update_offset_value(f, previous_aedr + 12, 8, offset)
                    # AEDRnext
                    self._update_offset_value(f, offset + 12, 8, aedr)
                    done = True
                    break
                else:
                    # move to the next aedr in chain
                    f.seek(aedr + 12, 0)
                    previous_aedr = aedr
                    aedr = int.from_bytes(f.read(8), "big", signed=True)

            # If no link was made, update the last found aedr
            if not done:
                self._update_offset_value(f, previous_aedr + 12, 8, offset)

            if zVar:
                self._update_offset_value(f, adr_offset + 56, 4, entries + 1)
                if maxEntry < varNum:
                    self._update_offset_value(f, adr_offset + 60, 4, varNum)
            else:
                self._update_offset_value(f, adr_offset + 36, 4, entries + 1)
                if maxEntry < varNum:
                    self._update_offset_value(f, adr_offset + 40, 4, varNum)

    @staticmethod
    def _set_bit(value: int, bit: int) -> int:
        return value | (1 << bit)

    @staticmethod
    def _clear_bit(value: int, bit: int) -> int:
        return value & ~(1 << bit)

    @staticmethod
    def _checklistofstrs(obj: Any) -> bool:
        return bool(obj) and all(isinstance(elem, str) for elem in obj)

    @staticmethod
    def _checklistofNums(obj: Any) -> bool:
        if hasattr(obj, "__len__"):
            return bool(obj) and all(isinstance(elem, numbers.Number) for elem in obj)
        else:
            return isinstance(obj, numbers.Number)

    def _md5_compute(self, f: io.BufferedWriter) -> bytes:
        """
        Computes the checksum of the file
        """
        md5 = hashlib.md5()
        block_size = 16384
        f.seek(0, 2)
        remaining = f.tell()
        f.seek(0)

        while remaining > block_size:
            data = f.read(block_size)
            remaining = remaining - block_size
            md5.update(data)

        if remaining > 0:
            data = f.read(remaining)
            md5.update(data)

        return md5.digest()

    @staticmethod
    def _make_blocks(records) -> List[Tuple[int, int]]:  # type: ignore[no-untyped-def]
        """
        Organizes the physical records into blocks in a list by
        placing consecutive physical records into a single block, so
        lesser VXRs will be created.
          [[start_rec1,end_rec1,data_1], [start_rec2,enc_rec2,data_2], ...]

        Parameters
        ----------
        records: list
            A list of records that there is data for

        Returns
        -------
        sparse_blocks: list of list
            A list of ranges we have physical values for.

        Example:
            Input: [1,2,3,4,10,11,12,13,50,51,52,53]
            Output: [[1,4],[10,13],[50,53]]
        """

        sparse_blocks = []
        total = len(records)
        if total == 0:
            return []

        x = 0
        while x < total:
            recstart = records[x]
            y = x
            recnum = recstart

            # Find the location in the records before the next gap
            # Call this value "y"
            while (y + 1) < total:
                y = y + 1
                nextnum = records[y]
                diff = nextnum - recnum
                if diff == 1:
                    recnum = nextnum
                else:
                    y = y - 1
                    break

            if (y + 1) == total:
                recend = records[total - 1]
            else:
                recend = records[y]
            x = y + 1
            sparse_blocks.append((recstart, recend))

        return sparse_blocks

    def _make_sparse_blocks(self, variable, records, data: List[Tuple[int, int, np.ndarray]]):  # type: ignore[no-untyped-def]
        """
        Handles the data for the variable with sparse records.
        Organizes the physical record numbers into blocks in a list:
          [[start_rec1,end_rec1,data_1], [start_rec2,enc_rec2,data_2], ...]
        Place consecutive physical records into a single block

        If all records are physical, this calls _make_sparse_blocks_with_physical

        If any records are virtual, this calls _make_sparse_blocks_with_virtual

        Parameters:
            variable : dict
                the variable dictionary, with 'Num_Dims', 'Dim_Sizes',
                'Data_Type', 'Num_Elements' key words, typically
                returned from a call to cdf read's varinq('variable',
                expand=True)

            records : list
                a list of physical records

            data : varies
                bytes array, numpy.ndarray or list of str form with all physical
                data or embedded virtual data (returned from call to
                varget('variable') for a sparse variable)

        Returns:
            sparse_blocks: list
                A list of sparse records/data in the form
                [[start_rec1,end_rec1,data_1], [start_rec2,enc_rec2,data_2], ...]
        """

        if isinstance(data, dict):
            try:
                data = data["Data"]
            except Exception:
                logger.warning("Unknown dictionary.... Skip")
                return None
        if isinstance(data, np.ndarray):
            if len(records) == len(data):
                # All are physical data
                return self._make_sparse_blocks_with_physical(variable, records, data)
            elif len(records) < len(data):
                # There are some virtual data
                return self._make_sparse_blocks_with_virtual(variable, records, data)
            else:
                logger.warning("Invalid sparse data... " "Less data than the specified records... Skip")
        elif isinstance(data, bytes):
            record_length = len(records)
            for z in range(0, variable["Num_Dims"]):
                record_length = record_length * variable["Dim_Sizes"][z]
            if record_length == len(data):
                # All are physical data
                return self._make_sparse_blocks_with_physical(variable, records, data)
            elif record_length < len(data):
                # There are some virtual data
                return self._make_sparse_blocks_with_virtual(variable, records, data)
            else:
                logger.warning("Invalid sparse data... " "Less data than the specified records... Skip")
        elif isinstance(data, list):
            if isinstance(data[0], list):
                if not (all(isinstance(el, str) for el in data[0])):
                    raise RuntimeError("Can not handle list data.... ", "Only support list of str...")
            else:
                if not (all(isinstance(el, str) for el in data)):
                    raise RuntimeError("Can not handle list data.... ", "Only support list of str...")
            record_length = len(records)
            # for z in range(0, variable['Num_Dims']):
            #    record_length = record_length * variable['Dim_Sizes'][z]
            if record_length == len(data):
                # All are physical data
                return self._make_sparse_blocks_with_physical(variable, records, data)
            elif record_length < len(data):
                # There are some virtual data
                return self._make_sparse_blocks_with_virtual(variable, records, data)
            else:
                logger.warning("Invalid sparse data... ", "Less data than the specified records... Skip")
        else:
            logger.warning("Invalid sparse data... ", "Less data than the specified records... Skip")
        return

    def _make_sparse_blocks_with_virtual(self, variable, records, data) -> List[Tuple[int, int, np.ndarray]]:  # type: ignore[no-untyped-def]
        """
        Handles the data for the variable with sparse records.
        Organizes the physical record numbers into blocks in a list:
          [[start_rec1,end_rec1,data_1], [start_rec2,enc_rec2,data_2], ...]
        Place consecutive physical records into a single block

        Parameters:
            variable: dict
                the variable, returned from varinq('variable', expand=True)
            records: list
                a list of physical records
            data: varies
                bytes array, numpy.ndarray or list of str form with vitual data
                embedded, returned from varget('variable') call
        """

        # Gather the ranges for which we have physical data
        sparse_blocks = self._make_blocks(records)

        sparse_data = []
        if isinstance(data, np.ndarray):
            for sblock in sparse_blocks:
                # each block in this list: [starting_rec#, ending_rec#, data]
                starting = sblock[0]
                ending = sblock[1] + 1
                sparse_data.append((sblock[0], sblock[1], data[starting:ending]))
            return sparse_data
        elif isinstance(data, bytes):
            y = 1
            for z in range(0, variable["Num_Dims"]):
                y = y * variable["Dim_Sizes"][z]
            y = y * self._datatype_size(variable["Data_Type"], variable["Num_Elements"])
            for x in sparse_blocks:
                # each block in this list: [starting_rec#, ending_rec#, data]
                starting = sblock[0] * y
                ending = (sblock[1] + 1) * y
                sparse_data.append((sblock[0], sblock[1], np.array(data[starting:ending])))
            return sparse_data
        elif isinstance(data, list):
            for x in sparse_blocks:
                # each block in this list: [starting_rec#, ending_rec#, data]
                asparse = []
                asparse.append(sblock[0])
                asparse.append(sblock[1])
                records = x[1] - x[0] + 1
                datax = []
                ist = sblock[0]
                for z in range(0, records):
                    datax.append(data[ist + z])
                sparse_data.append((sblock[0], sblock[1], np.array(datax)))
            return sparse_data
        else:
            logger.warning("Can not handle data... Skip")
            return None

    def _make_sparse_blocks_with_physical(self, variable, records, data) -> List[Tuple[int, int, np.ndarray]]:  # type: ignore[no-untyped-def]
        # All records are physical... just a single block
        #   [[0,end_rec,data]]

        # Determine if z variable
        if variable["Var_Type"].lower() == "zvariable":
            zVar = True
        else:
            zVar = False

        # Determine dimension information
        numDims = len(variable["Dim_Sizes"])
        if zVar:
            numValues = 1
            for x in range(0, numDims):
                numValues = numValues * variable["Dim_Sizes"][x]
        else:
            for x in range(0, numDims):
                if variable["Dim_Vary"][x] != 0:
                    numValues = numValues * variable["Dim_Sizes"][x]

        # Determine blocks
        sparse_blocks = self._make_blocks(records)

        # Create a list in the form of [[0,100, [data]], ...]
        sparse_data = []
        recStart = 0
        for sblock in sparse_blocks:
            recs = sblock
            totalRecs = recs[1] - recs[0] + 1
            recEnd = recStart + totalRecs
            sparse_data.append((recs[0], recs[1], data[recStart:recEnd]))
            recStart = recStart + totalRecs

        return sparse_data
