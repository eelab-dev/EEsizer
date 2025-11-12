import json
from pathlib import Path

from eesizer.agents.optimizer import Optimizer
from eesizer.llm.mock import MockLLM


class FakeOrchestrator:
    def __init__(self):
        self.signals = ["out"]

    def run_once(self, netlist_text: str, tool_chain: dict):
        # return a simple metrics dict
        return {"ac_gain_db": 0.5, "unity_bandwidth_hz": 1e6, "success": True}

    def optimize(self, variants, tool_chain: dict, run_dir_base: str = None):
        # prefer the patched variant (index 1)
        all_results = []
        for i, v in enumerate(variants):
            all_results.append({"variant_index": i, "ac_gain_db": 0.5 if i == 0 else 1.2, "score": 0.5 if i == 0 else 1.2})
        return {"best_index": 1, "best_result": all_results[1], "all_results": all_results}


def test_headless_runner_writes_artifacts(tmp_path: Path):
    # load a small netlist
    netlist_path = Path("initial_circuit_netlist/inv.cir")
    assert netlist_path.exists()
    base = netlist_path.read_text()

    run_dir = tmp_path / "runs" / "test"
    run_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = FakeOrchestrator()
    llm = MockLLM()

    cfg = {"targets": {"gain": 1.0}, "tool_chain": {"tool_calls": [{"name": "ac_simulation"}]}, "run_dir": str(run_dir), "iter_timeout": 5}
    opt = Optimizer(base_netlist=base, orchestrator=orchestrator, llm_provider=llm, config=cfg)

    out = opt.run(max_iters=1)

    # assert final_report exists
    final = run_dir / "final_report.json"
    assert final.exists()
    data = json.loads(final.read_text())
    assert "best_netlist" in data

    # per-iteration artifacts
    itdir = run_dir / "iteration_1"
    assert (itdir / "metrics.json").exists()
    assert (itdir / "analysis.json").exists()
    assert (itdir / "optimize.json").exists()
    assert (itdir / "sizing.json").exists()
    assert (itdir / "patched_netlist.cir").exists()
    assert (itdir / "orchestrator.json").exists()
