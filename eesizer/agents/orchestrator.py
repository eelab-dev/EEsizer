from typing import List, Dict, Any, Optional
import os
from ..sim.ngspice import NgSpiceSimulator
from ..sim.base import SimulationRequest, SimulationResult
from ..sim.netlist_builders import build_ac_netlist, build_tran_netlist, build_dc_netlist
from ..analysis.metrics import (
    ac_gain_db_from_dat,
    bandwidth_hz_from_dat,
    unity_bandwidth_hz_from_dat,
    phase_margin_deg_from_dat,
    tran_gain_db_from_dat,
)
from ..analysis.oplog import parse_vgs_vth_from_oplog
from ..io.fs import safe_read, safe_write
from ..io.paths import OUTPUT_DIR
import json


class Orchestrator:
    """Lightweight orchestrator to run a tool_chain against a netlist in a namespaced run dir.

    The tool_chain is expected as {"tool_calls": [{"name": "ac_simulation"}, {"name": "run_ngspice"}, {"name": "ac_gain"}, ...]}
    This implementation provides a minimal mapping to the builders and analysis functions.
    """

    def __init__(self, run_dir: Optional[str] = None, signals: Optional[List[str]] = None):
        self.run_dir = run_dir or OUTPUT_DIR
        self.signals = signals or ["out"]
        self.sim = NgSpiceSimulator(run_dir=self.run_dir)

    def run_once(self, netlist_text: str, tool_chain: Dict[str, Any]) -> Dict[str, Any]:
        sim_netlist = netlist_text
        # Ensure run dir exists
        os.makedirs(self.run_dir, exist_ok=True)

        # First pass: build netlist according to sim types
        for call in tool_chain.get("tool_calls", []):
            name = call.get("name", "").lower()
            if name == "ac_simulation":
                sim_netlist = build_ac_netlist(sim_netlist, signals=self.signals, outfile="output_ac.dat")
            elif name in ("transient_simulation", "tran_simulation", "transient"):
                sim_netlist = build_tran_netlist(sim_netlist, signals=self.signals, outfile="output_tran.dat")
            elif name == "dc_simulation":
                sim_netlist = build_dc_netlist(sim_netlist, signals=self.signals, outfile="output_dc.dat")

        # If there is an explicit run_ngspice command in tool_chain, run once
        ran = False
        simreq = SimulationRequest(sim_type="batch", options={})
        for call in tool_chain.get("tool_calls", []):
            name = call.get("name", "").lower()
            if name == "run_ngspice":
                res: SimulationResult = self.sim.run(sim_netlist, simreq)
                ran = True
                break

        if not ran:
            # by default run it once
            res = self.sim.run(sim_netlist, simreq)

        results: Dict[str, Any] = {"success": res.success, "stdout_len": len(res.stdout or "")}

        # Parse vgs/vth summary
        op_path = os.path.join(self.run_dir, "op.txt")
        op_text = safe_read(op_path, default="")
        devices = parse_vgs_vth_from_oplog(op_text)
        results["vgs_summary"] = [{"name": d.name, "vgs": d.vgs, "vth": d.vth, "margin": d.margin} for d in devices]

        # Run analysis items requested
        for call in tool_chain.get("tool_calls", []):
            name = call.get("name", "").lower()
            try:
                if name == "ac_gain":
                    results["ac_gain_db"] = ac_gain_db_from_dat(os.path.join(self.run_dir, "output_ac.dat"))
                elif name == "bandwidth":
                    results["bandwidth_hz"] = bandwidth_hz_from_dat(os.path.join(self.run_dir, "output_ac.dat"))
                elif name == "unity_bandwidth":
                    results["unity_bandwidth_hz"] = unity_bandwidth_hz_from_dat(os.path.join(self.run_dir, "output_ac.dat"))
                elif name == "phase_margin":
                    results["phase_margin_deg"] = phase_margin_deg_from_dat(os.path.join(self.run_dir, "output_ac.dat"))
                elif name == "tran_gain":
                    results["tran_gain_db"] = tran_gain_db_from_dat(os.path.join(self.run_dir, "output_tran.dat"))
            except Exception as e:
                results[f"err_{name}"] = str(e)

        # write a compact JSON summary for downstream consumption
        summary_path = os.path.join(self.run_dir, "run_summary.json")
        try:
            safe_write(summary_path, json.dumps(results, indent=2))
        except Exception:
            pass

        return results

    def optimize(self, netlist_variants: List[str], tool_chain: Dict[str, Any], run_dir_base: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate multiple netlist variants and return the best according to a simple score.

        Parameters
        - netlist_variants: list of netlist text strings to evaluate
        - tool_chain: the tool_chain dict used for each evaluation
        - run_dir_base: if provided, each variant will be written to run_dir_base/variant_{i}

        Returns a dict with keys:
        - "best_index": index of the best variant
        - "best_result": the results dict returned by run_once for the best variant
        - "all_results": list of per-variant result dicts with an added "score" key

        Note: scoring is intentionally simple and configurable by callers in future.
        Current default scoring prefers AC gain (ac_gain_db) then transient gain (tran_gain_db).
        """
        all_results: List[Dict[str, Any]] = []

        def score_result(r: Dict[str, Any]) -> float:
            # Prefer ac_gain_db when available, else tran_gain_db, else fallback to 0
            s = 0.0
            try:
                if "ac_gain_db" in r and isinstance(r["ac_gain_db"], (int, float)):
                    s += float(r["ac_gain_db"]) * 1.0
                elif "tran_gain_db" in r and isinstance(r["tran_gain_db"], (int, float)):
                    s += float(r["tran_gain_db"]) * 0.9
                # small bonus for unity bandwidth if present
                if "unity_bandwidth_hz" in r and isinstance(r["unity_bandwidth_hz"], (int, float)):
                    s += 0.001 * float(r["unity_bandwidth_hz"]) / (1e6)
            except Exception:
                pass
            return s

        best_idx = None
        best_score = float("-inf")
        best_result: Optional[Dict[str, Any]] = None

        for i, net in enumerate(netlist_variants):
            subdir = None
            if run_dir_base:
                subdir = os.path.join(run_dir_base, f"variant_{i}")
            else:
                subdir = self.run_dir

            # create a short-lived orchestrator for each variant so run_dir can be isolated
            orch = Orchestrator(run_dir=subdir, signals=self.signals)
            try:
                res = orch.run_once(net, tool_chain)
            except Exception as e:
                res = {"success": False, "error": str(e)}

            sc = score_result(res)
            res_with_score = dict(res)
            res_with_score["score"] = sc
            res_with_score["variant_index"] = i
            all_results.append(res_with_score)

            if sc > best_score:
                best_score = sc
                best_idx = i
                best_result = res_with_score

        return {"best_index": best_idx, "best_result": best_result, "all_results": all_results}
