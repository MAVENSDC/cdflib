from pathlib import Path

from . import cdfread, cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401


# This function determines if we are reading or writing a file
def CDF(path, cdf_spec=None, delete=False, validate=None,
        string_encoding='ascii', s3_memlow=False):
    """
    A wrapper function for cdfread and cdfwrite modules.

    If you specify a file that exists, it returns a CDF reading class.
    If you specify a file that does not yet exist, one will be created and this
    function will return a CDF writing class.

    Parameters
    ----------
    path : str
        The path to a cdf file that exists or to one you wish to create
    cdf_spec : dict, optional
        If you are writing a CDF file, this specifies general parameters about
        data is written.  See the cdfwrite class for more details.
    delete : bool, optional
        Delete the file if it exists and return immediately.
    validate : bool, optional
    string_encoding : str, optional
        How strings are encoded in a CDF file that you are reading.
        Another common encoding is 'utf-8'.

    Returns
    -------
    A CDF object that can be used for reading a file (if it exists) or writing to a file (if it does not exist)

    Notes
    -----
    With this library, you cannot both read and write a file at the same time.
    You need to choose one or the other!

    Examples
    --------
    Open an existing CDF file and get some data from a variable
    >>> import cdflib
    >>> cdf_file = cdflib.CDF('/path/to/existing/cdf_file.cdf')
    >>> x = cdf_file.varget("NameOfVariable", startrec = 0, endrec = 150)

    """
    import re

    path_orig = path # S3 mod
    path = Path(path).resolve().expanduser()
    # re.search needed for S3-awareness, cannot path-ize S3 or urls
    if re.search("^http://|^https://|^s3://",path_orig):
        return cdfread.CDF(path_orig, validate=validate, string_encoding=string_encoding, s3_memlow=s3_memlow)
    elif path.is_file():
        if delete:
            path.unlink()
            return
        else:
            return cdfread.CDF(path, validate=validate, string_encoding=string_encoding)
    else:
        return cdfwrite.CDF(path, cdf_spec=cdf_spec, delete=delete)
