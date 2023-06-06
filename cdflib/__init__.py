import logging
from pathlib import Path

from cdflib.cdfread import CDF
from . import cdfread, cdfwrite
from .epochs import CDFepoch as cdfepoch  # noqa: F401

logger = logging.getLogger(__name__)

__all__ = ["CDF"]


try:
    from ._version import version as __version__
except Exception:
    __version__ = "unknown"
