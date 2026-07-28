#!/usr/bin/env python3
"""Write the single machine-readable v0.1.4 success/failure artifact."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PACKAGE_VERSION = "0.1.4"
SCHEMA_VERSION = "espresso.whole_pull.run_status.v0.1.4"
CASE_RELATIVE = Path("cases/reference_R0_20g_58mm_9bar")
FIXTURE_RELATIVE = Path("cases/fixture_layered_pressure_v0_1_4")
DEFAULT_RELATIVE_OUTPUT = CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json"
TIMING_JSON_RELATIVE = CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json"
ACCEPTANCE_RELATIVE = CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json"
FIXTURE_ACCEPTANCE_RELATIVE = FIXTURE_RELATIVE / "ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json"
QUALIFICATION_RELATIVE = Path("qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json")
FREEZE_MANIFEST_RELATIVE = CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json"
SOURCE_MANIFEST_RELATIVE = Path("SOURCE_PACKAGE_MANIFEST.json")
MAX_LOG_TAIL_LINES = 180
MAX_LOG_TAIL_CHARS = 60000
MAX_CLASSIFIED_LINES = 100

SELECTED_ENVIRONMENT_VARIABLES = (
    "WM_PROJECT",
    "WM_PROJECT_VERSION",
    "WM_OPTIONS",
    "WM_ARCH",
    "WM_COMPILER",
    "WM_COMPILER_TYPE",
    "WM_COMPILE_OPTION",
    "WM_LABEL_SIZE",
    "WM_PRECISION_OPTION",
    "WM_MPLIB",
    "WM_PROJECT_DIR",
    "FOAM_SRC",
    "FOAM_INST_DIR",
    "FOAM_USER_APPBIN",
    "FOAM_USER_LIBBIN",
    "OPENFOAM_BASHRC",
    "MPI_LAUNCHER",
    "MPI_ARGS",
)

SAFEGUARD_PATTERNS = (
    re.compile(r"^sigFpe\s*:\s*Enabling floating point exception trapping \(FOAM_SIGFPE\)\.$", re.I),
)
BENIGN_METRIC_PATTERNS = (
    re.compile(
        r"^[A-Za-z][A-Za-z0-9 _./()\-]*relative error:\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?$",
        re.I,
    ),
)
WARNING_PATTERN = re.compile(r"(?:FOAM Warning|\bwarning:|make: Warning:)", re.I)
ISSUE_PATTERN = re.compile(
    r"(?:fatal error:|\berror:|\bERROR\b|FOAM FATAL|MPI_ABORT|"
    r"segmentation fault|floating point exception(?:\s*\(|\s*$)|killed|"
    r"no such file|cannot find|could not open|failed|not found|not detected|"
    r"unbound variable|parameter not set|bad substitution|command not found|"
    r"terminate called|core dumped)",
    re.I,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(path: Optional[Path], root: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError):
        return str(path)


def read_text_lossy(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"<unable to read {path}: {exc}>"


def tail_lines(text: str, count: int = MAX_LOG_TAIL_LINES) -> List[str]:
    lines = text.splitlines()[-count:]
    clipped = [line[-5000:] if len(line) > 5000 else line for line in lines]
    while sum(len(line) + 1 for line in clipped) > MAX_LOG_TAIL_CHARS and clipped:
        clipped.pop(0)
    return clipped


def classify_lines(lines: Iterable[str]) -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {
        "safeguards": [],
        "metrics": [],
        "warnings": [],
        "issues": [],
    }
    seen = {key: set() for key in categories}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        category: Optional[str] = None
        if any(pattern.search(stripped) for pattern in SAFEGUARD_PATTERNS):
            category = "safeguards"
        elif any(pattern.search(stripped) for pattern in BENIGN_METRIC_PATTERNS):
            category = "metrics"
        elif ISSUE_PATTERN.search(stripped):
            category = "issues"
        elif WARNING_PATTERN.search(stripped):
            category = "warnings"
        if category is not None and stripped not in seen[category]:
            seen[category].add(stripped)
            categories[category].append(stripped)
            if len(categories[category]) >= MAX_CLASSIFIED_LINES:
                continue
    return categories


def log_record(path: Path, root: Path, current: bool) -> Dict[str, Any]:
    text = read_text_lossy(path)
    lines = tail_lines(text)
    classes = classify_lines(lines)
    return {
        "path": safe_relative(path, root),
        "current_stage_log": current,
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256(path) if path.is_file() else None,
        "tail_line_count": len(lines),
        "tail": lines,
        "informational_safeguard_lines": classes["safeguards"],
        "informational_metric_lines": classes["metrics"],
        "warning_lines": classes["warnings"],
        "detected_issue_lines": classes["issues"],
    }


def load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"_non_object_json": value}
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def parse_int(value: Optional[str]) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def deduplicate_paths(paths: Iterable[Path]) -> List[Path]:
    result: List[Path] = []
    seen = set()
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path.absolute())
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def artifact_summary(path: Path, root: Path, selected_keys: Iterable[str] = ()) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    value = load_json(path)
    summary: Dict[str, Any] = {
        "path": safe_relative(path, root),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "json_read_error": value.get("_read_error"),
    }
    for key in selected_keys:
        summary[key] = value.get(key)
    return summary


def read_timing_tsv(path: Path, root: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                try:
                    duration = float(row.get("duration_s", ""))
                except ValueError:
                    duration = None
                rows.append(
                    {
                        "stage": row.get("stage"),
                        "start_utc": row.get("start_utc"),
                        "end_utc": row.get("end_utc"),
                        "duration_s": duration,
                        "status": row.get("status"),
                        "exit_code": parse_int(row.get("exit_code")),
                        "log": row.get("log") or None,
                    }
                )
    total = sum(float(row["duration_s"]) for row in rows if row["duration_s"] is not None)
    return {
        "schema_version": "espresso.whole_pull.stage_timings.v0.1.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_tsv": safe_relative(path, root),
        "stage_count": len(rows),
        "sum_of_stage_durations_s": total,
        "stages": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--status", choices=("PASS", "FAIL"), required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--exit-code", default="0")
    parser.add_argument("--command", default="")
    parser.add_argument("--line", default="")
    parser.add_argument("--current-log", default="")
    parser.add_argument("--nprocs", default="")
    parser.add_argument("--available-cpus", default="")
    parser.add_argument("--keep-processors", default="")
    parser.add_argument("--reconstruct", default="")
    parser.add_argument("--timings", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    case = root / CASE_RELATIVE
    fixture = root / FIXTURE_RELATIVE
    case.mkdir(parents=True, exist_ok=True)
    output = args.output or (root / DEFAULT_RELATIVE_OUTPUT)
    output = output.resolve() if output.is_absolute() else (root / output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    current_log: Optional[Path] = None
    if args.current_log:
        candidate = Path(args.current_log)
        current_log = candidate if candidate.is_absolute() else root / candidate

    log_candidates: List[Path] = []
    if current_log is not None:
        log_candidates.append(current_log)
    log_candidates.extend(sorted(case.glob("log.*")))
    log_candidates.extend(sorted(fixture.glob("log.*")))
    log_candidates.extend(sorted((root / "qualification").glob("log.*")))
    logs = [
        log_record(
            path,
            root,
            current_log is not None and path.resolve() == current_log.resolve(),
        )
        for path in deduplicate_paths(log_candidates)
        if path.is_file() or (current_log is not None and path == current_log)
    ]

    classified: Dict[str, List[Dict[str, str]]] = {
        "safeguards": [],
        "metrics": [],
        "warnings": [],
        "issues": [],
    }
    seen = {key: set() for key in classified}
    mapping = {
        "safeguards": "informational_safeguard_lines",
        "metrics": "informational_metric_lines",
        "warnings": "warning_lines",
        "issues": "detected_issue_lines",
    }
    for record in logs:
        for category, record_key in mapping.items():
            for line in record[record_key]:
                key = (record["path"], line)
                if key not in seen[category]:
                    seen[category].add(key)
                    classified[category].append({"log": record["path"], "line": line})

    timing_tsv = args.timings or (case / "stage_timings_v0_1_4.tsv")
    timing_tsv = timing_tsv.resolve() if timing_tsv.is_absolute() else (root / timing_tsv).resolve()
    timing_report = read_timing_tsv(timing_tsv, root)
    timing_json = root / TIMING_JSON_RELATIVE
    timing_json.parent.mkdir(parents=True, exist_ok=True)
    timing_json.write_text(json.dumps(timing_report, indent=2) + "\n", encoding="utf-8")

    acceptance_path = root / ACCEPTANCE_RELATIVE
    fixture_acceptance_path = root / FIXTURE_ACCEPTANCE_RELATIVE
    qualification_path = root / QUALIFICATION_RELATIVE
    source_manifest_path = root / SOURCE_MANIFEST_RELATIVE
    build_provenance_path = case / "preflight/BUILD_PROVENANCE_V0_1_4.json"
    timestamp_path = case / "preflight/TIMESTAMP_NORMALIZATION_V0_1_4.json"
    no_physics_path = case / "preflight/NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json"
    freeze_manifest_path = root / FREEZE_MANIFEST_RELATIVE

    acceptance = artifact_summary(
        acceptance_path,
        root,
        (
            "status",
            "execution_status",
            "all_required_numerical_gates_pass",
            "all_required_b0_parity_gates_pass",
            "all_required_bounded_state_gates_pass",
            "all_required_monotonicity_gates_pass",
            "reference_qualification_status",
            "release_provenance_status",
            "reference_freeze_status",
            "primary_outputs",
        ),
    )
    fixture_acceptance = artifact_summary(
        fixture_acceptance_path,
        root,
        ("status", "execution_status", "all_required_gates_pass", "primary_outputs"),
    )
    qualification = artifact_summary(
        qualification_path,
        root,
        ("status", "all_required_gates_pass", "profile", "gate_summary"),
    )

    expected_outputs = [
        ACCEPTANCE_RELATIVE,
        CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv",
        CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json",
        CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json",
        CASE_RELATIVE / "reference_R0.foam",
        FIXTURE_ACCEPTANCE_RELATIVE,
        TIMING_JSON_RELATIVE,
    ]
    output_presence = {str(path): (root / path).is_file() for path in expected_outputs}

    selected_environment = {
        name: os.environ.get(name)
        for name in SELECTED_ENVIRONMENT_VARIABLES
        if os.environ.get(name) not in (None, "")
    }
    source_manifest = artifact_summary(
        source_manifest_path,
        root,
        ("schema_version", "aggregate_sha256", "file_count"),
    )
    build_provenance = artifact_summary(
        build_provenance_path,
        root,
        ("status", "source_and_executable_bundle_sha256", "executable"),
    )
    timestamp_normalization = artifact_summary(
        timestamp_path,
        root,
        ("status", "normalized_file_count", "maximum_observed_future_offset_s"),
    )
    no_physics_change = artifact_summary(
        no_physics_path,
        root,
        ("status", "qualified_predecessor_version", "governing_physics_change"),
    )
    freeze_manifest = artifact_summary(
        freeze_manifest_path,
        root,
        ("status", "reference_freeze_status", "freeze_finalized_at_utc"),
    )

    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": root.name,
        "package_version": PACKAGE_VERSION,
        "status": args.status,
        "execution_status": "COMPLETED" if args.status == "PASS" else "FAILED",
        "failure_or_completion_stage": args.stage,
        "exit_code": parse_int(args.exit_code),
        "failing_command": args.command or None,
        "failing_line_number": parse_int(args.line),
        "diagnostics": {
            "primary_log": safe_relative(current_log, root),
            "detected_issue_count": len(classified["issues"]),
            "detected_warning_count": len(classified["warnings"]),
            "informational_safeguard_count": len(classified["safeguards"]),
            "informational_metric_count": len(classified["metrics"]),
            "detected_issue_lines": classified["issues"],
            "warning_lines": classified["warnings"],
            "informational_safeguard_lines": classified["safeguards"],
            "informational_metric_lines": classified["metrics"],
            "logs": logs,
            "classification_note": (
                "The exact OpenFOAM FOAM_SIGFPE enablement message and numeric "
                "'relative error:' metric lines are informational. An actual "
                "floating-point exception or explicit failure remains an issue."
            ),
        },
        "runtime": {
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "available_logical_cpus": parse_int(args.available_cpus),
            "requested_mpi_ranks": parse_int(args.nprocs),
            "keep_processor_directories": args.keep_processors or None,
            "reconstruct_mode": args.reconstruct or None,
            "selected_environment": selected_environment,
            "stage_timings": timing_report,
        },
        "provenance": {
            "source_package_manifest": source_manifest,
            "build_provenance": build_provenance,
            "timestamp_normalization": timestamp_normalization,
            "no_physics_change_verification": no_physics_change,
        },
        "artifacts": {
            "this_run_status_file": safe_relative(output, root),
            "stage_timings": artifact_summary(timing_json, root, ("stage_count", "sum_of_stage_durations_s")),
            "layered_pressure_fixture_acceptance": fixture_acceptance,
            "reference_acceptance": acceptance,
            "full_numerical_qualification": qualification,
            "terminal_freeze_manifest": freeze_manifest,
            "expected_output_presence": output_presence,
        },
        "communication": {
            "share_this_file_for_diagnosis": safe_relative(output, root),
            "also_share_on_success": [
                str(ACCEPTANCE_RELATIVE),
                str(CASE_RELATIVE / "ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv"),
            ],
            "note": (
                "This single JSON contains workflow stage, exit code, OpenFOAM/MPI "
                "environment, stage timings, provenance, fixture/reference summaries, "
                "classified diagnostics, and bounded log tails/hashes."
            ),
        },
    }

    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "stage": report["failure_or_completion_stage"],
                "run_status_report": str(output),
                "detected_issue_count": len(classified["issues"]),
                "warning_count": len(classified["warnings"]),
                "informational_safeguard_count": len(classified["safeguards"]),
                "informational_metric_count": len(classified["metrics"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
