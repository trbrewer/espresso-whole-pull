"""Fail-closed helpers for verifying immutable evidence at exact Git objects."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


class AuthorityError(ValueError):
    """An exact Git authority could not be reconstructed or did not match."""


@dataclass(frozen=True)
class GitAuthority:
    commit: str
    tree: str


def _run(repo: Path, *args: str, text: bool = True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=text,
        check=False,
    )


def require_repository(repo: Path) -> Path:
    repo = Path(repo).resolve()
    probe = _run(repo, "rev-parse", "--git-dir")
    if probe.returncode:
        raise AuthorityError("GIT_REPOSITORY_NOT_RESOLVABLE")
    return repo


def verify_authority(repo: Path, authority: GitAuthority) -> None:
    repo = require_repository(repo)
    commit = _run(repo, "cat-file", "-e", f"{authority.commit}^{{commit}}")
    if commit.returncode:
        raise AuthorityError("LOCKED_COMMIT_OBJECT_MISSING")
    tree = _run(repo, "rev-parse", f"{authority.commit}^{{tree}}")
    if tree.returncode or tree.stdout.strip() != authority.tree:
        raise AuthorityError("LOCKED_TREE_MISMATCH")


def require_ancestor(repo: Path, base: str, candidate: str) -> None:
    repo = require_repository(repo)
    result = _run(repo, "merge-base", "--is-ancestor", base, candidate)
    if result.returncode:
        raise AuthorityError("NON_ANCESTOR_AUTHORITY")


def changed_paths(repo: Path, base: GitAuthority, candidate: GitAuthority) -> list[str]:
    verify_authority(repo, base)
    verify_authority(repo, candidate)
    require_ancestor(repo, base.commit, candidate.commit)
    result = _run(repo, "diff", "--name-only", base.commit, candidate.commit)
    if result.returncode:
        raise AuthorityError("HISTORICAL_CHANGED_PATHS_UNAVAILABLE")
    return sorted(result.stdout.splitlines())


def object_bytes(repo: Path, authority: GitAuthority, path: str) -> bytes:
    verify_authority(repo, authority)
    if not path or path.startswith("/") or ".." in Path(path).parts:
        raise AuthorityError("INVALID_LOCKED_OBJECT_PATH")
    result = _run(repo, "show", f"{authority.commit}:{path}", text=False)
    if result.returncode:
        raise AuthorityError("LOCKED_PATH_OBJECT_MISSING")
    return result.stdout


def object_identity(repo: Path, authority: GitAuthority, path: str) -> dict[str, str]:
    data = object_bytes(repo, authority, path)
    mode = _run(repo, "ls-tree", authority.commit, "--", path)
    fields = mode.stdout.strip().split()
    if mode.returncode or len(fields) < 3:
        raise AuthorityError("LOCKED_PATH_IDENTITY_MISSING")
    return {
        "mode": fields[0],
        "object_type": fields[1],
        "blob_id": fields[2],
        "sha256": hashlib.sha256(data).hexdigest(),
    }
