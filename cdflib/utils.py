from numbers import Number
from typing import Union

import numpy as np
import numpy.typing as npt


def _squeeze_or_scalar(arr: npt.ArrayLike) -> Union[npt.NDArray, Number]:
    arr = np.squeeze(arr)
    if arr.ndim == 0:
        return arr[()]
    else:
        return arr


def _squeeze_or_scalar_real(arr: npt.ArrayLike) -> Union[npt.NDArray, float]:
    arr = np.squeeze(arr)
    if arr.ndim == 0:
        return arr[()]
    else:
        return arr


def _squeeze_or_scalar_complex(arr: npt.ArrayLike) -> Union[npt.NDArray, complex]:
    arr = np.squeeze(arr)
    if arr.ndim == 0:
        return arr[()]
    else:
        return arr
