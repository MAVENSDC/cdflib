from pathlib import Path

from . import cdfread, cdfwrite
from .cdf_factory import CDF

from .epochs import CDFepoch as cdfepoch  # noqa: F401

try:
    # This is an optional dependency for astropy time conversions
    from .epochs_astropy import CDFAstropy as cdfastropy
except:
    pass

try:
    # Another optional dependency for XArray <-> cdf conversions
    from .xarray_to_cdf import xarray_to_cdf
    from .cdf_to_xarray import cdf_to_xarray
except:
    pass

__all__ = ['CDF', 'xarray_to_cdf', 'cdf_to_xarray']
