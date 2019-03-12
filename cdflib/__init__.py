import os
from . import cdfread
from . import cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401

# This function determines if we are reading or writing a file


def CDF(path, cdf_spec=None, delete=False, validate=None):
    path = os.path.expanduser(path)
    if (os.path.exists(path)):
        if delete:
            os.remove(path)
            return
        else:
            return cdfread.CDF(path, validate=validate)
    else:
        return cdfwrite.CDF(path, cdf_spec=cdf_spec, delete=delete)
