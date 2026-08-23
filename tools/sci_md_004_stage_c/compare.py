from __future__ import annotations

import csv
import hashlib
import math
import re
from pathlib import Path
from typing import Iterable


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty CSV: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        result = list(reader)
    if not result:
        raise ValueError(f"CSV has no data rows: {path}")
    return result


def relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-30)


def finite_float(value: str | float, *, label: str = "value") -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"nonfinite {label}: {value!r}")
    return result


def comparison(actual: float, expected: float, *, absolute_floor: float,
               near_zero: float = 1.0e-30) -> dict:
    actual = finite_float(actual, label="actual")
    expected = finite_float(expected, label="expected")
    absolute = abs(actual - expected)
    denominator_near_zero = abs(expected) <= near_zero
    relative = None if denominator_near_zero else absolute / abs(expected)
    return {
        "actual": actual,
        "expected": expected,
        "absolute_difference": absolute,
        "relative_difference": relative,
        "absolute_floor": absolute_floor,
        "denominator_near_zero": denominator_near_zero,
    }


def canonical_openfoam_bytes(path: Path) -> bytes:
    """Canonicalize only OpenFOAM object/location header values."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^(\s*object\s+)\S+(\s*;)", r"\1<OBJECT>\2", text)
    text = re.sub(r'(?m)^(\s*location\s+)"[^"]*"(\s*;)',
                  r'\1"<LOCATION>"\2', text)
    return text.encode()


def canonical_sha256(path: Path) -> str:
    return hashlib.sha256(canonical_openfoam_bytes(path)).hexdigest()


def scalar_internal_values(path: Path, *, cell_count: int | None = None) -> list[float]:
    text = path.read_text(encoding="utf-8")
    uniform = re.search(r"internalField\s+uniform\s+([^;]+);", text)
    if uniform:
        if cell_count is None:
            raise ValueError(f"cell_count required for uniform field: {path}")
        return [finite_float(uniform.group(1), label=str(path))] * cell_count
    match = re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
        text, flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"cannot parse scalar internalField: {path}")
    count = int(match.group(1))
    values = [finite_float(token, label=str(path)) for token in match.group(2).split()]
    if len(values) != count:
        raise ValueError(f"declared/parsed scalar count mismatch: {path}")
    return values


def internal_numeric_values(path: Path, *, cell_count: int | None = None) -> list[float]:
    """Parse scalar or vector internal values into one deterministic flat vector."""
    text = path.read_text(encoding="utf-8")
    uniform = re.search(r"internalField\s+uniform\s+(.+?);", text)
    if uniform:
        if cell_count is None:
            raise ValueError(f"cell_count required for uniform field: {path}")
        tokens = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
                            uniform.group(1))
        return [finite_float(token, label=str(path)) for _ in range(cell_count)
                for token in tokens]
    match = re.search(
        r"internalField\s+nonuniform\s+List<(?:scalar|vector)>\s+(\d+)\s*\((.*?)\)\s*;",
        text, flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"cannot parse numeric internalField: {path}")
    tokens = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
                        match.group(2))
    return [finite_float(token, label=str(path)) for token in tokens]


def scalar_boundary_values(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8")
    boundary = text.split("boundaryField", 1)
    if len(boundary) != 2:
        raise ValueError(f"missing boundaryField: {path}")
    result = {}
    for patch, body in re.findall(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\{([^{}]*)\}",
                                  boundary[1], flags=re.DOTALL):
        value = re.search(r"\bvalue\s+uniform\s+([^;]+);", body)
        if value:
            result[patch] = finite_float(value.group(1), label=f"{path}:{patch}")
    return result


def require_unique_species_times(table: list[dict[str, str]], species: Iterable[str],
                                 times: Iterable[float]) -> None:
    expected = {(sid, float(time)) for time in times for sid in species}
    observed: set[tuple[str, float]] = set()
    for row in table:
        key = (row["species_id"], finite_float(row["time_s"], label="time_s"))
        if key in observed:
            raise ValueError(f"duplicate species/time row: {key}")
        observed.add(key)
        for name, value in row.items():
            if name not in {"species_id", "species_role"}:
                finite_float(value, label=name)
    if observed != expected:
        raise ValueError(
            f"species/time matrix mismatch; missing={sorted(expected-observed)} "
            f"extra={sorted(observed-expected)}"
        )


def maximum_column_difference(
    first: list[dict[str, str]], second: list[dict[str, str]], column: str
) -> float:
    if len(first) != len(second):
        raise ValueError(f"row-count mismatch for {column}")
    return max(abs(float(a[column]) - float(b[column])) for a, b in zip(first, second))
