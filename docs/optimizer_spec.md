# Optimizer specification — LLM-in-the-loop (extracted from notebook)

This document captures the iterative optimization loop implemented in the original
`agent_gpt_openai.ipynb` notebook, the expected prompts and LLM outputs, the
dataflow per iteration, and a recommended, hardened contract for implementing
the optimizer inside `eesizer.agents`.

Status: implementation target for Task 1 (analysis/spec) — ready for review.

## Overview

The notebook's optimization loop is an LLM-driven iterative process that:

- Runs a candidate circuit netlist through a simulation/analysis pipeline.
- Asks the LLM to analyze the results (analysis prompt).
- Asks the LLM to propose optimization directions (optimization prompt).
- Asks the LLM to produce a sized/updated netlist (sizing prompt).
- Re-runs simulations with the updated netlist and records metrics.
- Repeats until convergence or max iterations.

The goal of the package-level Optimizer is to reproduce this behavior in a
testable, robust, and observable way while removing notebook-only brittleness.

## Key artifacts (per run / per iteration)

- `run_dir/` — namespaced directory for the optimization run.
- `iteration_<n>.json` — full record including inputs, LLM responses, metrics.
- `result_history.csv` — tabular history of selected metrics per iteration.
- `final_netlist.cir` — final produced netlist when optimizer completes.
- `vgscheck_summary.json` — output from op-log parser after each run.

## The notebook iteration (concrete sequence)

1. Start with `base_netlist` (text), `tool_chain` (structured JSON describing sims/analyses), and `targets` (gain, bw, etc.).
2. Run analysis pipeline (netlist builders → ngspice run → parse `.dat` and `op.txt` → metrics).
3. Build `analysis_prompt` containing the metric summary and ask the LLM for an analysis summary.
   - Expected LLM output: free-text analysis summarizing which metrics pass/fail and why.
4. Build `optimizing_prompt` explaining constraints and asking for optimization suggestions.
   - Expected LLM output: free-text suggestions plus optionally structured recommendations.
5. Build `sizing_prompt` asking for a new netlist (or patch). The notebook asked the LLM for the entire updated netlist enclosed in triple backticks.
   - Expected LLM output: a code block containing the updated netlist, or the output may contain noise; the notebook used `extract_code()` to pull the netlist.
6. Extract new netlist text and validate. If invalid, record failure and either retry or stop.
7. Re-run simulation and analysis on the updated netlist; append metrics to history and decide whether to continue.

The loop also wrote histories (`result_history.txt` and a `g2_o3.csv`) and produced plots.

## Prompts (templates — simplified)

Note: the exact notebook prompts were verbose and tuned for the provider. Below are structured templates to reproduce the behavior.

1) Analysis prompt (analysis_prompt)

"""
You ran a circuit simulation and collected these metrics: {metrics_json}.
Please analyze: which metrics meet their targets and which do not. For failures,
give a concise reason and suggest what part of the circuit to change (devices, supply,
stage) and whether to increase/decrease sizing or bias.

Return a JSON object with keys: {status: 'ok'|'issue', reasons: [...], suggestions: [...]}
"""

2) Optimization prompt (optimizing_prompt)

"""
Using the analysis summary: {analysis_summary}, propose actionable design changes
that will move metrics toward targets {targets_json}. Return a JSON array `changes`.
Each change should be: {component: <ref>, action: 'increase'|'decrease'|'replace', param: <name>, value: <numeric or relative>, rationale: <text>}.
"""

3) Sizing prompt (sizing_prompt)

"""
Apply the proposed `changes` to the `base_netlist` and return an updated netlist.
Return only the netlist inside a fenced code block (``` ... ```). If you cannot
produce a full netlist, return a clear JSON with `error` and `reason`.
"""

## Expected LLM outputs / schemas (recommend Pydantic models)

- AnalysisSummary: {
    pass: bool,
    reasons: List[str],
    suggestions: List[SuggestionSummary]
  }

- SuggestionSummary: {
    component: str,
    param: Optional[str],
    action: Literal['increase','decrease','replace','tweak'],
    magnitude: Optional[str],
    rationale: str
  }

- SizingResponse: {
    netlist_text: Optional[str],
    error: Optional[str]
  }

We will validate LLM outputs against these schemas and reject proposals that
don't parse or are missing required fields.

## Error modes and recovery

- LLM returns malformed JSON or no code block: record the failure, optionally retry (configurable retry count), and continue only if parsed proposal is valid.
- Proposed netlist fails simulation (e.g., ngspice exit non-zero or missing outputs): revert to previous netlist and mark iteration as failed.
- LLM suggests an empty netlist or destructive changes: reject automatically and log.

## Dataflow & sequencing diagram (textual)

- Input: base_netlist, tool_chain, targets
  |
  +-> Simulator Runner (NgSpice) -> raw artifacts (.dat, op.txt)
       |
       +-> OpLog Parser -> vgscheck_summary.json
       +-> Metrics Extractor -> metrics_json
  |
  +-> Build analysis_prompt(metrics_json) -> LLM -> analysis_summary
  +-> Build optimizing_prompt(analysis_summary, targets) -> LLM -> suggestions
  +-> Build sizing_prompt(suggestions, base_netlist) -> LLM -> sizing_response
  +-> Extract new_netlist from sizing_response
  +-> Validate & apply -> next iteration or end

## Convergence and stopping rules (recommended)

- `max_iters`: default 10 (configurable).
- Stop early if all metrics meet targets within tolerance.
- Stop if no metric improved in `patience` consecutive iterations (configurable, default 3).
- Stop and rollback if a proposed netlist causes simulator failure.

## Recommended improvements vs notebook

1. Use structured, schema-validated LLM outputs instead of free-text where possible.
2. Prefer small structured diffs plus final netlist instead of only full netlist replacements.
3. Use a `MockLLM` for CI and deterministic testing.
4. Persist iteration artifacts (input netlist, metrics, LLM response) per iteration as JSON for reproducibility.
5. Limit LLM scope: prefer returning a `changes` list with explicit fields (component, param, delta) rather than relying entirely on the model to produce a syntactically perfect netlist.

## Acceptance criteria (for Task 1)

- A canonical specification exists (this file) that documents the notebook loop and the desired hardened behavior.
- Prompt templates and expected schemas are defined.
- Clear error handling, data artifacts, and acceptance rules defined.

## Next actions (brief)

1. Approve this spec.
2. I'll implement `MockLLM` and the Optimizer skeleton (Tasks 3 and 4) to exercise one iteration.

---
Generated by analysis of `agent_test_gpt/agent_gpt_openai.ipynb` and the devdoc.