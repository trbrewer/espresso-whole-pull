from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

TASK_ID = "SCI-DATA-FUSION-001"
AUTHORITY_FILES = {
    "manifest_sha256": "puckworks/data/MANIFEST.csv",
    "available_data_register_sha256": "puckworks/data/AVAILABLE_DATA_REGISTER.json",
    "local_corpus_family_index_sha256": "puckworks/data/LOCAL_CORPUS_FAMILY_INDEX.json",
}


class AuthorityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(root: Path, expression: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", expression], text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise AuthorityError(f"cannot resolve git identity {expression} at {root}") from exc


def programme(root: Path) -> dict:
    return json.loads((root / "provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json").read_text())


def verify_ewp(root: Path) -> dict:
    doc = programme(root)
    selected = doc.get("current_priority")
    task = next((x for x in doc.get("opportunities", []) if x.get("task_id") == TASK_ID), None)
    if selected != TASK_ID or not task or task.get("status") != "READY":
        raise AuthorityError(f"live programme does not select READY {TASK_ID}")
    if task.get("claim_ceiling") != "CROSS_CORPUS_COMPONENT_EVIDENCE":
        raise AuthorityError("claim ceiling mismatch")
    predecessor = "186c13000cfb1a402b220bec8fbb89164bac4686"
    try:
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", predecessor, "HEAD"],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise AuthorityError("accepted predecessor is not reachable from current base") from exc
    return {"programme": doc, "task": task, "head": git_value(root, "HEAD"), "tree": git_value(root, "HEAD^{tree}"), "predecessor": predecessor}


def verify_puckworks(root: Path, expected: dict) -> dict:
    head, tree = git_value(root, "HEAD"), git_value(root, "HEAD^{tree}")
    if head != expected["puckworks_commit"] or tree != expected["puckworks_tree"]:
        raise AuthorityError(f"Puckworks identity mismatch: {head}/{tree}")
    hashes = {}
    for key, relative in AUTHORITY_FILES.items():
        path = root / relative
        if not path.is_file():
            raise AuthorityError(f"missing Puckworks authority file: {relative}")
        hashes[key] = sha256(path)
        if hashes[key] != expected[key]:
            raise AuthorityError(f"Puckworks authority hash mismatch: {relative}")
    return {"commit": head, "tree": tree, **hashes}

