from pathlib import Path

from cdflib.cdfread import CDF
from . import cdfread, cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401

try:
    # This is an optional dependency for astropy time conversions
    from .epochs_astropy import CDFAstropy as cdfastropy
except BaseException:
    pass

# Another optional dependency for XArray <-> cdf conversions
from .cdf_to_xarray import cdf_to_xarray
from .xarray_to_cdf import xarray_to_cdf

__all__ = ['CDF', 'xarray_to_cdf', 'cdf_to_xarray']
