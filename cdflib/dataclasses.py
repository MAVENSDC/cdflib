from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

__all__ = ["ADRInfo", "CDFInfo", "CDRInfo", "GDRInfo", "VDRInfo", "AEDR", "VDR", "AEDR", "AttData"]


@dataclass
class ADRInfo:
    scope: int
    next_adr_loc: int
    attribute_number: int
    num_gr_entry: int
    max_gr_entry: int
    num_z_entry: int
    max_z_entry: int
    first_z_entry: int
    first_gr_entry: int
    name: str


@dataclass
class CDFInfo:
    """
    CDF information.

    Parameters
    ----------
    CDF :
        Path to the CDF.
    Version :
        CDF version.
    Encoding :
        Endianness of the CDF.
    Majority :
        Row/column majority.
    zVariables :
        zVariable names.
    rVariables :
        rVariable names.
    Attributes :
        List of dictionary objects that contain {attribute_name : scope}.
    Checksum
        Checksum indicator.
    Num_rdim :
        Number of dimensions for rVariables.
    rDim_sizes :
        Dimensional sizes for rVariables.
    Compressed :
        If CDF is compressed at file level.
    LeapSecondUpdated :
        Last updated leap second table.
    """

    CDF: Union[str, Path]
    Version: str
    Encoding: int
    Majority: str
    rVariables: List[str]
    zVariables: List[str]
    Attributes: List[Dict[str, str]]
    Copyright: str
    Checksum: bool
    Num_rdim: int
    rDim_sizes: List[int]
    Compressed: bool
    LeapSecondUpdate: Optional[int] = None


@dataclass
class CDRInfo:
    encoding: int
    copyright_: str
    version: str
    majority: int
    format_: bool
    md5: bool
    post25: bool


@dataclass
class GDRInfo:
    first_zvariable: int
    first_rvariable: int
    first_adr: int
    num_zvariables: int
    num_rvariables: int
    num_attributes: int
    rvariables_num_dims: int
    rvariables_dim_sizes: List[int]
    eof: int
    leapsecond_updated: Optional[int] = None


@dataclass
class VDRInfo:
    """
    Variable data record info.

    Attributes
    ----------
    Variable : str
        Name of the variable.
    Num : int
        Variable number.
    Var_Type : str
        Variable type: zVariable or rVariable.
    Data_Type : str
        Variable CDF data type.
    Num_Elements : int
        Number of elements of the variable.
    Num_Dims : int
        Dimensionality of variable record.
    Dim_sizes :
        Shape of the variable record.
    Last_Rec :
        Maximum written variable number (0-based).
    Dim_Vary :
        Dimensional variance(s).
    Rec_Vary :
        Record variance.
    Pad :
        Padded value (if set).
    Block_Factor:
        Blocking factor (if variable is compressed).
    """

    Variable: str
    Num: int
    Var_Type: str
    Data_Type: int
    Data_Type_Description: str
    Num_Elements: int
    Num_Dims: int
    Dim_Sizes: List[int]
    Sparse: str
    Last_Rec: int
    Rec_Vary: int
    Dim_Vary: Union[List[int], List[bool]]
    Compress: int
    Pad: Optional[int] = None
    Block_Factor: Optional[int] = None


@dataclass
class AEDR:
    entry: np.ndarray
    data_type: int
    num_elements: int
    next_aedr: int
    entry_num: int
    num_strings: Optional[int] = None


@dataclass
class VDR:
    data_type: int
    section_type: int
    next_vdr_location: int
    variable_number: int
    head_vxr: int
    last_vxr: int
    max_rec: int
    name: str
    num_dims: int
    dim_sizes: List[int]
    compression_bool: bool
    compression_level: int
    blocking_factor: int
    dim_vary: Union[List[int], List[bool]]
    record_vary: int
    num_elements: int
    sparse: int
    pad: Optional[bool] = None


@dataclass
class AttData:
    """
    Attribute data.

    Attributes
    ----------
    Item_size : int
        Number of bytes for each entry value.
    Data_Type : str
        CDF data type.
    Num_Items : int
        Number of values extracted.
    Data : numpy.ndarray
        Data as a scalar value, a numpy array or a string.
    """

    Item_Size: int
    Data_Type: str
    Num_Items: int
    Data: np.ndarray
