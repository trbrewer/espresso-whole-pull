#!/usr/bin/env python3
"""Reduce corrected WP03-002 traces with frozen VAL-CORPUS-001 metrics."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import val_corpus_001 as corpus


SNAPSHOT_COMMIT = "9c52c94edb27b461b6e7a4d471d29f3cef9d053e"
SNAPSHOT_TREE = "44d6539096648777f78c4db83f0985d5bd16e352"


def git_value(path: Path, revision: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", revision], text=True
    ).strip()


def ordering(ids, source, model):
    descending = lambda values: [
        ids[i] for i in sorted(range(3), key=lambda j: values[j], reverse=True)
    ]
    return {
        "source_order": descending(source),
        "model_order": descending(model),
        "spearman": corpus.spearman3(source, model),
    }


def overlap_thirds(overlay, source_rows):
    """Supplement the frozen full metric with thirds of the valid 0--27 s overlap."""
    result = {}
    fields = {
        "pressure": (2, 3, "basket_pressure_std__bar"),
        "flow": (4, 5, "mass_flow_rate_std__g_per_s"),
        "mass": (6, 7, "mass_std__g"),
    }
    selected = source_rows[: len(overlay)]
    for quantity, (observed_index, modeled_index, sigma_key) in fields.items():
        result[quantity] = {}
        for label, low, high in (
            ("early", 0.0, 9.0),
            ("middle", 9.0, 18.0),
            ("late", 18.0, 27.000001),
        ):
            indices = [i for i, row in enumerate(overlay) if low <= row[0] < high]
            result[quantity][label] = corpus.metric(
                [overlay[i][observed_index] for i in indices],
                [overlay[i][modeled_index] for i in indices],
                [float(selected[i][sigma_key]) for i in indices],
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if git_value(args.snapshot, "HEAD") != SNAPSHOT_COMMIT:
        raise RuntimeError("evidence snapshot commit mismatch")
    if git_value(args.snapshot, "HEAD^{tree}") != SNAPSHOT_TREE:
        raise RuntimeError("evidence snapshot tree mismatch")

    execution = corpus.load(args.run_root / "EXECUTION_RECORD.json")
    attempts = {item["id"]: item for item in execution["attempts"]}
    evidence = corpus.read_csv(
        args.snapshot / "puckworks/data/waszkiewicz2025/traces_time_dependent.csv"
    )
    groups = {
        bar: [
            row for row in evidence
            if float(row["reference_pressure_round__bar"]) == bar
        ]
        for bar in (5, 9, 11)
    }
    rows = []
    overlays = {}
    ids = [f"WASZ-{bar}-COMPACT" for bar in (5, 9, 11)]
    for bar, case_id in zip((5, 9, 11), ids):
        attempt = attempts[case_id]
        if attempt["status"] != "COMPLETED":
            raise RuntimeError(f"corrected attempt incomplete: {case_id}")
        trace = args.run_root / "cases" / case_id / "postProcessing/wholePull/0/traces.csv"
        metrics, overlay = corpus.windows_metrics(
            groups[bar], corpus.read_csv(trace), 965.0, solver_end=30.0
        )
        overlays[case_id] = overlay
        rows.append(
            {
                "id": case_id,
                "pressure_bar": bar,
                "config_sha256": attempt["config_sha256"],
                "trace_sha256": corpus.sha256(trace),
                "duration_s": attempt["duration_s"],
                "metrics": metrics,
                "valid_overlap_thirds": overlap_thirds(overlay, groups[bar]),
                "endpoint": {
                    "source_pressure_bar": overlay[-1][2],
                    "model_pressure_bar": overlay[-1][3],
                    "source_flow_g_s": overlay[-1][4],
                    "model_flow_g_s": overlay[-1][5],
                    "source_mass_g": overlay[-1][6],
                    "model_mass_g": overlay[-1][7],
                },
            }
        )

    source_flow = [row["endpoint"]["source_flow_g_s"] for row in rows]
    model_flow = [row["endpoint"]["model_flow_g_s"] for row in rows]
    source_mass = [row["endpoint"]["source_mass_g"] for row in rows]
    model_mass = [row["endpoint"]["model_mass_g"] for row in rows]
    accepted = corpus.load(
        args.root
        / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_RESULT_BUNDLE_V3.json"
    )
    baselines = []
    for row in accepted["r1_waszkiewicz_rows"]:
        if row["roles"]["pressure_node_scenario"] != "MEASURED_TERMINAL_BASKET_PRESSURE":
            continue
        baselines.append(
            {
                "id": row["id"],
                "branch": row["branch"],
                "pressure_bar": row["source_group_bar"],
                "pressure_rmse_bar": row["metrics"]["pressure"]["full"]["rmse"],
                "flow_rmse_g_s": row["metrics"]["flow"]["full"]["rmse"],
                "mass_rmse_g": row["metrics"]["mass"]["full"]["rmse"],
            }
        )
    result = {
        "schema_version": "espresso.wp03_002.corrected_comparison.v1",
        "task": "WP03-002",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "executable_sha256": execution["executable_sha256"],
        "evidence_snapshot": {"commit": SNAPSHOT_COMMIT, "tree": SNAPSHOT_TREE},
        "metric_contract": {
            "source_time_window_s": [0.0, 27.0],
            "model_time_window_s": [3.0, 30.0],
            "alignment": "solver_time=source_time+3.0s",
            "interpolation": "linear within domain; no extrapolation",
            "density_kg_m3": 965.0,
        },
        "corrected_compaction": rows,
        "ordering": {
            "flow": ordering(ids, source_flow, model_flow),
            "mass": ordering(ids, source_mass, model_mass),
        },
        "accepted_v3_baselines": baselines,
        "scientific_interpretation": (
            "The numerical defect is corrected and all three cases complete. "
            "Finite-porosity compaction remains a source-linked reconstruction "
            "and does not establish physical validation."
        ),
        "physical_validation": "NOT_ESTABLISHED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
