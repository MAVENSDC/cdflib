from pathlib import Path
from . import cdfread
from . import cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401

# This function determines if we are reading or writing a file


def CDF(path, cdf_spec=None, delete: bool=False, validate=None):
    path = Path(path).expanduser()

    if path.is_file():
        if delete:
            path.unlink()
            return
        else:
            return cdfread.CDF(path, validate=validate)
    else:
        return cdfwrite.CDF(path, cdf_spec=cdf_spec, delete=delete)
