import pytest
from eesizer.agents.orchestrator import Orchestrator


class Dummy:
    pass


def fake_run_once_factory(responses):
    """Return a fake run_once bound method that yields responses sequentially.
    responses: list of dicts to return for each call
    """

    # use a closure-level index so sequential calls across instances advance
    index = {"i": 0}

    def fake_run_once(self, netlist_text, tool_chain):
        i = index["i"]
        index["i"] = i + 1
        if i < len(responses):
            return responses[i]
        return responses[-1]

    return fake_run_once


def test_optimize_selects_best_based_on_ac_gain(monkeypatch):
    # Prepare two dummy netlists
    net1 = ".title var1\n* variant 1\n"
    net2 = ".title var2\n* variant 2\n"

    # Responses simulate run_once outputs with different ac_gain_db
    responses = [
        {"success": True, "ac_gain_db": 12.0},
        {"success": True, "ac_gain_db": 6.0},
    ]

    # Monkeypatch Orchestrator.run_once to our fake
    monkeypatch.setattr(Orchestrator, "run_once", fake_run_once_factory(responses))

    orch = Orchestrator(run_dir="output/test_orch_opt")
    res = orch.optimize([net1, net2], {"tool_calls": []}, run_dir_base="output/test_orch_opt")

    assert res["best_index"] == 0
    assert res["best_result"]["variant_index"] == 0
    assert len(res["all_results"]) == 2
    assert res["all_results"][0]["score"] == pytest.approx(12.0)
    assert res["all_results"][1]["score"] == pytest.approx(6.0)


def test_optimize_handles_errors(monkeypatch):
    net1 = ".title var1\n"
    responses = [
        {"success": False, "error": "sim failed"},
    ]
    monkeypatch.setattr(Orchestrator, "run_once", fake_run_once_factory(responses))

    orch = Orchestrator(run_dir="output/test_orch_opt_err")
    res = orch.optimize([net1], {"tool_calls": []}, run_dir_base="output/test_orch_opt_err")

    assert res["best_index"] == 0 or res["best_index"] is None
    assert isinstance(res["all_results"], list)
    assert res["all_results"][0].get("score") is not None
