"""CSV reporting helpers for optimizer runs.

Provides a simple append-only CSV writer that writes canonical metric columns per iteration.
"""
from __future__ import annotations

import csv
import os
from typing import Dict, Any, Optional


DEFAULT_COLUMNS = ["iteration", "ac_gain_db", "tran_gain_db", "unity_bandwidth_hz", "score"]


def append_metrics_csv(run_dir: str, iteration: int, metrics: Optional[Dict[str, Any]] = None, filename: str = "metrics.csv") -> str:
    """Append a row of metrics to CSV under run_dir and return the csv path."""
    metrics = metrics or {}
    csv_path = os.path.join(run_dir, filename)
    os.makedirs(run_dir, exist_ok=True)
    write_header = not os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=DEFAULT_COLUMNS)
        if write_header:
            writer.writeheader()
        row = {c: metrics.get(c) for c in DEFAULT_COLUMNS}
        row["iteration"] = iteration
        writer.writerow(row)

    return csv_path


__all__ = ["append_metrics_csv"]
