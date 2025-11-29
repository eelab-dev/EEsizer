import numpy as np
from typing import Tuple


def safe_genfromtxt(path: str, **kwargs) -> np.ndarray:
    try:
        return np.genfromtxt(path, **kwargs)
    except Exception:
        # return a small fallback array
        return np.zeros((2, 2))


def parse_ac_dat(path: str) -> Tuple[np.ndarray, np.ndarray]:
    data = safe_genfromtxt(path, skip_header=1)
    if data.ndim == 1:
        # single row
        data = data.reshape(1, -1)
    freq = data[:, 0]
    real = data[:, 1]
    imag = data[:, 2] if data.shape[1] > 2 else np.zeros_like(real)
    return freq, real + 1j * imag


def parse_tran_dat(path: str) -> Tuple[np.ndarray, np.ndarray]:
    data = safe_genfromtxt(path, skip_header=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    t = data[:, 0]
    out = data[:, 1] if data.shape[1] > 1 else np.zeros_like(t)
    return t, out

