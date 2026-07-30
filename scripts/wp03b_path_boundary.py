"""Shared Git path collection for WP-0.3B boundaries."""
import json
import subprocess
from pathlib import Path

STATIC_REPORT = "cases/reference_R0_20g_58mm_9bar/preflight/STATIC_VALIDATION_REPORT_V0_2_0.json"


def _git(root, *args):
    run = subprocess.run(["git", *args], cwd=root, text=True,
                         capture_output=True, check=True)
    return set(filter(None, run.stdout.splitlines()))


def is_current_untracked_static_report(root, path):
    """Recognize only the exact untracked report emitted by static_validate."""
    if path != STATIC_REPORT:
        return False
    tracked = _git(root, "ls-files", "--", path)
    staged = _git(root, "diff", "--cached", "--name-only", "--", path)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard", "--", path)
    report = Path(root) / path
    if tracked or staged or untracked != {path} or not report.is_file():
        return False
    try:
        value = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (value.get("schema_version") ==
            "espresso.whole_pull.static_validation.v0.2.0"
            and value.get("status") == "PASS")


def changed_paths(root, baseline):
    tracked = _git(root, "diff", "--name-only", baseline)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    ignored = {p for p in untracked if is_current_untracked_static_report(root, p)}
    return tracked | (untracked - ignored)


def changed_paths_between(root, baseline, endpoint):
    """Collect a closed historical boundary independent of later tasks."""
    return _git(root, "diff", "--name-only", baseline, endpoint)
