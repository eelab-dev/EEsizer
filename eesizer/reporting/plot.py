"""Simple plotting utilities to create a multi-panel PDF report for an optimizer run.

Produces:
 - metrics vs iteration (from metrics.csv)
 - placeholder for other panels (can be extended to include Bode plots from AC data)
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
import csv
from typing import List


def _read_metrics_csv(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # convert iteration and numeric fields
            try:
                r["iteration"] = int(r.get("iteration", 0))
            except Exception:
                r["iteration"] = 0
            for k in ("ac_gain_db", "tran_gain_db", "unity_bandwidth_hz", "score"):
                try:
                    if r.get(k) is None or r.get(k) == "":
                        r[k] = None
                    else:
                        r[k] = float(r.get(k))
                except Exception:
                    r[k] = None
            rows.append(r)
    return rows


def make_multi_panel_report(run_dir: str, csv_name: str = "metrics.csv", out_pdf: str = "report.pdf") -> str:
    csv_path = os.path.join(run_dir, csv_name)
    rows = _read_metrics_csv(csv_path)
    if not rows:
        # create an empty PDF with a note
        fig = plt.figure(figsize=(6, 4))
        fig.text(0.5, 0.5, "No metrics available to plot", ha="center", va="center")
        out = os.path.join(run_dir, out_pdf)
        fig.savefig(out)
        plt.close(fig)
        return out

    it = [r["iteration"] for r in rows]
    ac = [r["ac_gain_db"] for r in rows]
    tran = [r["tran_gain_db"] for r in rows]
    ubw = [r["unity_bandwidth_hz"] for r in rows]
    score = [r["score"] for r in rows]

    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    axs = axs.flatten()

    axs[0].plot(it, ac, marker="o")
    axs[0].set_title("AC gain (dB) vs iteration")
    axs[0].set_xlabel("iteration")
    axs[0].set_ylabel("ac_gain_db")

    axs[1].plot(it, tran, marker="o")
    axs[1].set_title("Transient gain (dB) vs iteration")
    axs[1].set_xlabel("iteration")
    axs[1].set_ylabel("tran_gain_db")

    axs[2].plot(it, ubw, marker="o")
    axs[2].set_title("Unity bandwidth (Hz) vs iteration")
    axs[2].set_xlabel("iteration")
    axs[2].set_ylabel("unity_bandwidth_hz")

    axs[3].plot(it, score, marker="o")
    axs[3].set_title("Score vs iteration")
    axs[3].set_xlabel("iteration")
    axs[3].set_ylabel("score")

    fig.tight_layout()
    out = os.path.join(run_dir, out_pdf)
    fig.savefig(out)
    plt.close(fig)
    return out


__all__ = ["make_multi_panel_report"]
