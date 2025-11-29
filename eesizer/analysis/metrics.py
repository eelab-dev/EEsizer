from dataclasses import dataclass
from typing import Optional
import numpy as np
from .parsers import parse_ac_dat, parse_tran_dat

@dataclass
class Metrics:
    ac_gain_db: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    unity_bandwidth_hz: Optional[float] = None
    phase_margin_deg: Optional[float] = None
    tran_gain_db: Optional[float] = None
    output_swing_v: Optional[float] = None
    offset_v: Optional[float] = None
    power_w: Optional[float] = None
    cmrr_db: Optional[float] = None
    thd_db: Optional[float] = None


def ac_gain_db_from_dat(path: str) -> float:
    f, v = parse_ac_dat(path)
    if v.size == 0:
        return 0.0
    return float(20 * np.log10(max(1e-30, np.abs(v[0]))))


def bandwidth_hz_from_dat(path: str) -> float:
    f, v = parse_ac_dat(path)
    if v.size == 0:
        return 0.0
    gain0 = 20 * np.log10(max(1e-30, np.abs(v[0])))
    mag_db = 20 * np.log10(np.maximum(1e-30, np.abs(v)))
    half = gain0 - 3.0
    idx = np.where(mag_db >= half)[0]
    if idx.size == 0:
        return 0.0
    return float(f[idx[-1]] - f[idx[0]])


def unity_bandwidth_hz_from_dat(path: str) -> float:
    f, v = parse_ac_dat(path)
    if v.size == 0:
        return 0.0
    mag_db = 20 * np.log10(np.maximum(1e-30, np.abs(v)))
    idx = np.where(mag_db >= 0.0)[0]
    if idx.size == 0:
        return 0.0
    return float(f[idx[-1]] - f[idx[0]])


def phase_margin_deg_from_dat(path: str) -> float:
    f, v = parse_ac_dat(path)
    if v.size == 0:
        return 0.0
    mag_db = 20 * np.log10(np.maximum(1e-30, np.abs(v)))
    phase_deg = np.degrees(np.angle(v))
    # index closest to 0 dB
    idx = int(np.argmin(np.abs(mag_db)))
    phi = float(phase_deg[idx])
    # Normalize to common PM definition when starting phase is near 0° vs 180°
    initial = float(phase_deg[0])
    if np.isclose(initial, 180.0, atol=15.0):
        return phi
    if np.isclose(initial, 0.0, atol=15.0):
        return 180.0 - abs(phi)
    return 0.0


def tran_gain_db_from_dat(path: str, input_pp_v: float = 2e-6) -> float:
    t, out = parse_tran_dat(path)
    if out.size == 0:
        return 0.0
    vmax = float(np.max(out))
    vmin = float(np.min(out))
    vpp = max(1e-30, vmax - vmin)
    return float(20 * np.log10(vpp / max(input_pp_v, 1e-30)))
