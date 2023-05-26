from typing import Union

import numpy as np
import numpy.typing as npt


def _squeeze_or_scalar_real(arr: npt.ArrayLike) -> Union[npt.NDArray, float]:
    arr = np.squeeze(arr)
    if arr.ndim == 0:
        return arr.item()
    else:
        return arr


def _squeeze_or_scalar_complex(arr: npt.ArrayLike) -> Union[npt.NDArray, complex]:
    arr = np.squeeze(arr)
    if arr.ndim == 0:
        return arr.item()
    else:
        return arr
