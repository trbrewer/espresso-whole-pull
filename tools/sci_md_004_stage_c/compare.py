from __future__ import annotations

import csv
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-30)


def maximum_column_difference(
    first: list[dict[str, str]], second: list[dict[str, str]], column: str
) -> float:
    if len(first) != len(second):
        raise ValueError(f"row-count mismatch for {column}")
    return max(abs(float(a[column]) - float(b[column])) for a, b in zip(first, second))
