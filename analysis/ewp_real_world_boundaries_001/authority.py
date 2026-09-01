from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

STOP_AUTHORITY = "EWP_REAL_WORLD_BOUNDARIES_001_STOP_PUCKWORKS_AUTHORITY_MISMATCH"
STOP_PROTOCOL = "EWP_REAL_WORLD_BOUNDARIES_001_STOP_PROTOCOL_FREEZE_INVALID"
PUCKWORKS_COMMIT = "a3428a4d4ad571ef3168a70e8a04620fca5d3520"
PUCKWORKS_TREE = "6175b4ad39f45ebcdec32a176e5611bf3b03655b"
FILES = {
    "puckworks/data/MANIFEST.csv": "3f073e3c5b2cbbfb9d94a7a2ebc3b06b2d1755b705c101804a3b7946966fb081",
    "puckworks/data/AVAILABLE_DATA_REGISTER.json": "0c318f43c40361629bb8f25ab4b8ca9f073425ca3ec3a2418bbd8a6cb67a5481",
    "puckworks/data/LOCAL_CORPUS_FAMILY_INDEX.json": "448a1eef0944d0d2b5e0f4ea04b3e5bc8418f315b5a323707f855815f8dcefcd",
    "puckworks/data/VISUALIZER_API_PERMISSION_STATUS.json": "6c9231e80a47643551845191542e1578ecce880a1468774158bb4e8a35e27706",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_puckworks(root: Path) -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    observed = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}
    if observed["commit"] != PUCKWORKS_COMMIT or observed["tree"] != PUCKWORKS_TREE:
        raise RuntimeError(STOP_AUTHORITY)
    observed["files"] = {name: sha256(root / name) for name in FILES}
    if observed["files"] != FILES:
        raise RuntimeError(STOP_AUTHORITY)
    return observed


def verify_protocol(path: Path, expected_hash: str) -> dict:
    if not expected_hash or sha256(path) != expected_hash:
        raise RuntimeError(STOP_PROTOCOL)
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("protocol_id") != "EWP_RWB_001_PROTOCOL_V1":
        raise RuntimeError(STOP_PROTOCOL)
    return body
