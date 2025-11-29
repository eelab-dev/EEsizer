"""Small headless runner to exercise the Optimizer with MockLLM.

Usage (from repo root):
  python scripts/headless_optimize.py --netlist initial_circuit_netlist/inv.cir --target '{"gain":1.0}'

This script reads a netlist file, constructs an Optimizer using MockLLM,
runs one iteration, and writes outputs to runs/headless_run.json and best_netlist.cir
"""
from __future__ import annotations

import argparse
import json
import os
import datetime

from eesizer.agents.optimizer import Optimizer
from eesizer.llm.mock import MockLLM


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--netlist", required=True, help="Path to base netlist file")
    p.add_argument("--target", required=False, help='JSON string of targets, e.g. "{\"gain\":1.0}"')
    p.add_argument("--run-dir", required=False, default="runs/headless", help="Output run directory")
    p.add_argument("--max-iters", required=False, type=int, default=1, help="Maximum iterations to run")
    p.add_argument("--iter-timeout", required=False, type=int, default=30, help="Per-iteration timeout in seconds")
    args = p.parse_args()

    with open(args.netlist, "r", encoding="utf-8") as f:
        base = f.read()

    targets = {}
    if args.target:
        try:
            targets = json.loads(args.target)
        except Exception:
            print("Failed to parse --target JSON; proceeding with empty targets")

    # ensure run dir
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(args.run_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)

    # configure a simple tool_chain: build AC netlist and attempt to run ngspice
    tool_chain = {"tool_calls": [{"name": "ac_simulation"}, {"name": "run_ngspice"}, {"name": "ac_gain"}, {"name":"unity_bandwidth"}]}

    llm = MockLLM()
    cfg = {"targets": targets, "tool_chain": tool_chain, "run_dir": run_dir, "iter_timeout": args.iter_timeout}
    optimizer = Optimizer(base_netlist=base, llm_provider=llm, config=cfg)

    print(f"Running headless optimizer ({args.max_iters} iteration(s)) with MockLLM...")
    out = optimizer.run(max_iters=args.max_iters)

    # write outputs
    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    best_net = out.get("best_netlist") or out.get("best_result", {}).get("netlist_text")
    if best_net:
        best_path = os.path.join(run_dir, "best_netlist.cir")
        with open(best_path, "w", encoding="utf-8") as f:
            f.write(best_net)
        print(f"Wrote best netlist to {best_path}")
    else:
        print("No best netlist produced; writing original as base_netlist.cir")
        base_path = os.path.join(run_dir, "base_netlist.cir")
        with open(base_path, "w", encoding="utf-8") as f:
            f.write(base)

    print(f"Summary written to {summary_path}")
    print("Done.")


if __name__ == "__main__":
    main()
