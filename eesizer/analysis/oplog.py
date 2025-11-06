from dataclasses import dataclass
from typing import List


@dataclass
class DeviceBias:
    name: str
    vgs: float
    vth: float

    @property
    def margin(self) -> float:
        return self.vgs - self.vth


def parse_vgs_vth_from_oplog(text: str) -> List[DeviceBias]:
    """Parse a simplified op log produced by ngspice stdout to extract device, vgs, and vth.

    The notebook stores ngspice stdout in op.txt and then filters for lines starting with:
      - 'device' followed by device names
      - 'vgs' values and 'vth' values on subsequent lines

    We accept multiple patterns and return any matched tuples; missing values are skipped.
    """
    if not text:
        return []

    devices: List[str] = []
    vth_vals: List[float] = []
    vgs_vals: List[float] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if parts[0].lower() == "device" and len(parts) > 1:
            devices.extend(parts[1:])
        elif parts[0].lower() == "vth" and len(parts) > 1:
            for val in parts[1:]:
                try:
                    vth_vals.append(float(val))
                except Exception:
                    continue
        elif parts[0].lower() == "vgs" and len(parts) > 1:
            for val in parts[1:]:
                try:
                    vgs_vals.append(float(val))
                except Exception:
                    continue

    n = min(len(devices), len(vgs_vals), len(vth_vals))
    biases: List[DeviceBias] = []
    for i in range(n):
        try:
            biases.append(DeviceBias(name=devices[i], vgs=vgs_vals[i], vth=vth_vals[i]))
        except Exception:
            continue
    return biases
