from pathlib import Path

from . import cdfread, cdfwrite
from .cdf_factory import CDF
from .cdf_to_xarray import cdf_to_xarray
from .epochs import CDFepoch as cdfepoch  # noqa: F401
from .epochs_astropy import CDFAstropy as cdfastropy
from .xarray_to_cdf import xarray_to_cdf

__all__ = ['CDF', 'xarray_to_cdf', 'cdf_to_xarray']
