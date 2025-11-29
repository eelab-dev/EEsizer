"""Optimizer implementation that uses an LLM provider and the Orchestrator to iterate.

This Optimizer runs iterations of:
  - run orchestrator.run_once(netlist) to collect real metrics
  - call LLM analysis -> suggestions -> sizing
  - evaluate candidate via orchestrator.optimize
Per-iteration artifacts are written under a configurable run_dir.
Supports per-iteration timeout and a maximum number of iterations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
import os
import json
import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from eesizer.agents.orchestrator import Orchestrator
from eesizer.netlist.patch import apply_netlist_replacement, revert_backup, validate_netlist_syntax
from eesizer.reporting.csv_report import append_metrics_csv
from eesizer.reporting.plot import make_multi_panel_report

try:
    from eesizer.llm.mock import MockLLM
except Exception:
    MockLLM = None  # type: ignore

logger = logging.getLogger(__name__)


def _to_serializable(obj: Any):
    """Convert common objects (Pydantic models, dicts) to plain Python types for JSON serialization."""
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    # Pydantic v1
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    if isinstance(obj, dict):
        return obj
    # fallback: return as-is (may be JSON serializable) or stringified
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


class Optimizer:
    """Optimizer for iterative LLM-in-the-loop netlist optimization.

    Inputs:
      - base_netlist: netlist text
      - orchestrator: Orchestrator instance (optional)
      - llm_provider: object implementing call(prompt_type, payload)
      - config: dict with keys: run_dir, iter_timeout, tool_chain, targets

    Returns:
      dict with best_netlist, best_result, history
    """

    def __init__(
        self,
        base_netlist: str,
        orchestrator: Optional[Orchestrator] = None,
        llm_provider: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.base_netlist = base_netlist
        self.orchestrator = orchestrator or Orchestrator()
        self.llm = llm_provider or (MockLLM() if MockLLM is not None else None)
        self.config = config or {}

        # run directory where per-iteration artifacts are written
        run_dir = self.config.get("run_dir")
        if not run_dir:
            ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = os.path.join("runs", "optimizer", ts)
        self.run_dir = run_dir
        os.makedirs(self.run_dir, exist_ok=True)

        # timeout per iteration (seconds)
        self.iter_timeout = int(self.config.get("iter_timeout", 30))

    def run(self, max_iters: int = 1) -> Dict[str, Any]:
        history: List[Dict[str, Any]] = []
        current_netlist = self.base_netlist
        best_netlist = current_netlist
        best_result = None

        for it in range(max_iters):
            logger.info("Optimizer iteration %d", it + 1)
            iter_dir = os.path.join(self.run_dir, f"iteration_{it+1}")
            os.makedirs(iter_dir, exist_ok=True)

            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(self._run_iteration, current_netlist, iter_dir)
                    result = fut.result(timeout=self.iter_timeout)
            except TimeoutError:
                logger.exception("Iteration %d timed out after %s seconds", it + 1, self.iter_timeout)
                history.append({"error": "timeout", "iteration": it + 1})
                break
            except Exception as e:
                logger.exception("Iteration failed: %s", e)
                history.append({"error": str(e), "iteration": it + 1})
                break

            history.append(result)

            orches_best = result.get("orchestrator_best")
            best_idx = result.get("orchestrator_best_index")
            if orches_best is not None:
                if best_idx is not None and isinstance(best_idx, int):
                    # sizing may be a dict or a Pydantic model; handle both
                    sizing_obj = result.get("sizing")
                    netlist_from_sizing = None
                    if sizing_obj is not None:
                        # try attribute access first (Pydantic model)
                        if hasattr(sizing_obj, "netlist_text"):
                            try:
                                netlist_from_sizing = sizing_obj.netlist_text
                            except Exception:
                                netlist_from_sizing = None
                        # fallback to dict-like access
                        if netlist_from_sizing is None and isinstance(sizing_obj, dict):
                            netlist_from_sizing = sizing_obj.get("netlist_text")

                    if best_idx == 1 and netlist_from_sizing:
                        best_netlist = netlist_from_sizing
                    else:
                        best_netlist = current_netlist
                best_result = orches_best

            current_netlist = best_netlist

        final_path = os.path.join(self.run_dir, "final_report.json")
        # Try to write a full report; if serialization fails (models in history), fall back
        try:
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump({"best_netlist": best_netlist, "best_result": best_result, "history": history}, f, indent=2)
        except Exception:
            try:
                # fall back to a minimal report that always contains best_netlist
                with open(final_path, "w", encoding="utf-8") as f:
                    json.dump({"best_netlist": best_netlist}, f, indent=2)
            except Exception:
                pass

        return {"best_netlist": best_netlist, "best_result": best_result, "history": history}

    def _run_iteration(self, netlist_text: str, iter_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run one iteration and persist artifacts into iter_dir.

        Steps:
          1) run orchestrator.run_once to gather real metrics
          2) call LLM analysis -> optimize -> sizing
          3) evaluate variants with orchestrator.optimize
        """
        if self.llm is None:
            raise RuntimeError("No LLM provider configured")

        iter_dir = iter_dir or self.run_dir
        tool_chain = self.config.get("tool_chain", {})

        try:
            metrics = self.orchestrator.run_once(netlist_text, tool_chain)
        except Exception as e:
            metrics = {"error": str(e)}

        try:
            with open(os.path.join(iter_dir, "metrics.json"), "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
        except Exception:
            pass

        analysis_payload = {"metrics": metrics, "targets": self.config.get("targets", {})}
        analysis_raw = self.llm.call("analysis", analysis_payload)
        try:
            # validate analysis response
            from eesizer.llm.validate import validate_analysis

            analysis = validate_analysis(analysis_raw)
        except Exception as e:
            # record invalid analysis and abort this iteration
            try:
                with open(os.path.join(iter_dir, "analysis.json"), "w", encoding="utf-8") as f:
                    json.dump({"invalid": str(e), "raw": analysis_raw}, f, indent=2)
            except Exception:
                pass
            return {"analysis": None, "error": f"analysis_validation_failed: {e}"}
        try:
            with open(os.path.join(iter_dir, "analysis.json"), "w", encoding="utf-8") as f:
                json.dump(_to_serializable(analysis), f, indent=2)
        except Exception:
            pass

        optimize_payload = {"analysis": _to_serializable(analysis)}
        optimize_raw = self.llm.call("optimize", optimize_payload)
        try:
            from eesizer.llm.validate import validate_optimize

            optimize_resp = validate_optimize(optimize_raw)
        except Exception as e:
            try:
                with open(os.path.join(iter_dir, "optimize.json"), "w", encoding="utf-8") as f:
                    json.dump({"invalid": str(e), "raw": optimize_raw}, f, indent=2)
            except Exception:
                pass
            return {"analysis": _to_serializable(analysis), "error": f"optimize_validation_failed: {e}"}
        try:
            with open(os.path.join(iter_dir, "optimize.json"), "w", encoding="utf-8") as f:
                json.dump(_to_serializable(optimize_resp), f, indent=2)
        except Exception:
            pass

        sizing_payload = {
            "base_netlist": netlist_text,
            "changes": [c.model_dump() if hasattr(c, "model_dump") else (c.dict() if hasattr(c, "dict") else c) for c in getattr(optimize_resp, "changes", [])],
        }
        sizing_raw = self.llm.call("sizing", sizing_payload)
        try:
            from eesizer.llm.validate import validate_sizing

            sizing = validate_sizing(sizing_raw)
        except Exception as e:
            try:
                with open(os.path.join(iter_dir, "sizing.json"), "w", encoding="utf-8") as f:
                    json.dump({"invalid": str(e), "raw": sizing_raw}, f, indent=2)
            except Exception:
                pass
            return {"analysis": analysis.dict(), "optimize": optimize_resp.dict(), "error": f"sizing_validation_failed: {e}"}
        try:
            with open(os.path.join(iter_dir, "sizing.json"), "w", encoding="utf-8") as f:
                json.dump(_to_serializable(sizing), f, indent=2)
        except Exception:
            pass

        # sizing may be a Pydantic model or a dict; support both styles
        patched = None
        if hasattr(sizing, "netlist_text"):
            try:
                patched = sizing.netlist_text
            except Exception:
                patched = None
        if patched is None and isinstance(sizing, dict):
            patched = sizing.get("netlist_text")

        if not patched:
            return {"analysis": _to_serializable(analysis), "optimize": _to_serializable(optimize_resp), "sizing": _to_serializable(sizing), "orchestrator_best": None}

        try:
            with open(os.path.join(iter_dir, "patched_netlist.cir"), "w", encoding="utf-8") as f:
                f.write(patched)
        except Exception:
            pass

        # Optionally apply the patched netlist to a target path (atomic replacement)
        backup_path = None
        apply_path = self.config.get("apply_path")
        if apply_path:
            ok, msg = validate_netlist_syntax(patched)
            if not ok:
                # do not apply malformed netlist; record and return
                return {"analysis": analysis, "optimize": optimize_resp, "sizing": sizing, "orchestrator_best": None, "apply_error": msg}
            try:
                backup_path, _ = apply_netlist_replacement(apply_path, patched)
                # persist backup info
                try:
                    with open(os.path.join(iter_dir, "applied_backup.txt"), "w", encoding="utf-8") as f:
                        f.write(backup_path or "")
                except Exception:
                    pass
            except Exception as e:
                return {"analysis": analysis, "optimize": optimize_resp, "sizing": sizing, "orchestrator_best": None, "apply_error": str(e)}

        variants = [netlist_text, patched]
        orch_res = self.orchestrator.optimize(variants, tool_chain=tool_chain)

        try:
            with open(os.path.join(iter_dir, "orchestrator.json"), "w", encoding="utf-8") as f:
                json.dump(_to_serializable(orch_res), f, indent=2)
        except Exception:
            pass

        best_idx = orch_res.get("best_index")
        best_result = orch_res.get("best_result")
        best_netlist = None
        if best_idx is not None and isinstance(best_idx, int) and 0 <= best_idx < len(variants):
            best_netlist = variants[best_idx]

    # Append metrics to CSV
        try:
            metrics_for_csv = {}
            # flatten some known metrics
            if isinstance(metrics, dict):
                metrics_for_csv.update({k: metrics.get(k) for k in ("ac_gain_db", "tran_gain_db", "unity_bandwidth_hz", "score")})
            # include orchestrator best score if present
            if isinstance(orch_res, dict):
                best = orch_res.get("best_result") or {}
                metrics_for_csv["score"] = best.get("score", metrics_for_csv.get("score"))
            append_metrics_csv(self.run_dir, int(iter_dir.split("_")[-1]) if iter_dir else 0, metrics_for_csv)
        except Exception:
            pass

        # If an apply_path was used but the orchestrator chose the original (index 0), revert the applied change
        if apply_path and backup_path is not None:
            try:
                if best_idx == 0:
                    revert_backup(apply_path, backup_path)
            except Exception:
                # log but don't fail the iteration
                pass

        # create a small PDF report for this run_dir
        try:
            make_multi_panel_report(self.run_dir)
        except Exception:
            pass

        return {
            "analysis": _to_serializable(analysis),
            "optimize": _to_serializable(optimize_resp),
            "sizing": _to_serializable(sizing),
            "orchestrator_best": _to_serializable(best_result),
            "orchestrator_best_index": best_idx,
            "best_netlist": best_netlist,
            "all": orch_res.get("all_results") if isinstance(orch_res, dict) else None,
        }


__all__ = ["Optimizer"]
