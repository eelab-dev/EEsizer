import subprocess
import os
from .base import Simulator, SimulationRequest, SimulationResult
from ..io.paths import out_path, OUTPUT_DIR
from ..io.fs import safe_write
from ..analysis.oplog import parse_vgs_vth_from_oplog
from ..io.fs import safe_read
import json


class NgSpiceSimulator(Simulator):
    def __init__(self, ngspice_bin: str = None, timeout: int = 300, run_dir: str = None):
        from ..config_models import RunConfig

        cfg = RunConfig()
        self.ngspice_bin = ngspice_bin or cfg.ngspice_bin
        self.timeout = timeout or cfg.timeout_seconds
        self.run_dir = run_dir or OUTPUT_DIR

    def run(self, netlist_text: str, request: SimulationRequest) -> SimulationResult:
        filename = f"netlist_{request.sim_type}.cir"
        cir_path = out_path(filename, run_dir=self.run_dir)
        safe_write(cir_path, netlist_text)
        op_path = out_path("op.txt", run_dir=self.run_dir)
        try:
            # Ensure run_dir exists and execute within it so wrdata writes land here
            os.makedirs(self.run_dir, exist_ok=True)
            # Ensure we pass an absolute path to ngspice to avoid cwd-relative duplication
            cir_path = os.path.abspath(cir_path)
            op_path = os.path.abspath(op_path)
            proc = subprocess.run(
                [self.ngspice_bin, "-b", cir_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.run_dir,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            try:
                safe_write(op_path, out)
            except Exception:
                pass
            # Parse op.txt to extract device Vgs/Vth info and write a compact summary
            try:
                op_text = safe_read(op_path, default="")
                devices = parse_vgs_vth_from_oplog(op_text)
                summary = [ {"name": d.name, "vgs": d.vgs, "vth": d.vth, "margin": d.margin } for d in devices ]
                vgs_json_path = out_path("vgscheck_summary.json", run_dir=self.run_dir)
                vgs_txt_path = out_path("vgscheck.txt", run_dir=self.run_dir)
                safe_write(vgs_json_path, json.dumps(summary, indent=2))
                # backward-compatible short text: list devices where margin < 0 or 'No values...'
                if not summary:
                    safe_write(vgs_txt_path, "No values found where vgs - vth < 0.")
                else:
                    lines = []
                    for s in summary:
                        if s.get("margin", 0) < 0:
                            lines.append(f"{s['name']}: vgs={s['vgs']}, vth={s['vth']}, margin={s['margin']}")
                    safe_write(vgs_txt_path, "\n".join(lines) if lines else "No values found where vgs - vth < 0.")
            except Exception:
                # non-fatal; continue
                pass
            return SimulationResult(success=(proc.returncode == 0), output_files={"op": op_path}, stdout=proc.stdout, stderr=proc.stderr)
        except Exception as e:
            try:
                safe_write(op_path, f"Error running ngspice: {e}")
            except Exception:
                pass
            return SimulationResult(success=False, output_files={}, stdout=None, stderr=str(e))
