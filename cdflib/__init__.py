from . import cdfread, cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401

try:
    from .epochs_astropy import CDFAstropy as cdfastropy
except Exception:
    pass
'''
try:
    from .cdf_to_xarray import cdf_to_xarray
    from .xarray_to_cdf import xarray_to_cdf
except Exception:
    pass
'''

from .cdf_to_xarray import cdf_to_xarray
from .xarray_to_cdf import xarray_to_cdf

from pathlib import Path

# This function determines if we are reading or writing a file


def CDF(path, cdf_spec=None, delete=False, validate=None, string_encoding='ascii'):
    path = Path(path).expanduser()

    if path.is_file():
        if delete:
            path.unlink()
            return
        else:
            return cdfread.CDF(path, validate=validate, string_encoding=string_encoding)
    else:
        return cdfwrite.CDF(path, cdf_spec=cdf_spec, delete=delete)
