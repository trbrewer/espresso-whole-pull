"""Raw-string source identity verification; this module contains no metrics."""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any

from .framework import ContractError, canonical_json, sha256

SPEC_VERSION = "VAL001_SELECTED_ROW_CANONICALIZATION_V2"
EXPECTED_SOURCE_SHA256 = "0a789ed20039ff5ea21b7e1773f2f62f74a4122775e2cb3fa12ff6c24c53a831"
EXPECTED_PRESSURES = ["1", "2", "3.5", "4", "5", "6", "7", "8", "9", "11"]


def selected_row_identity(path: Path, expected_source_sha256: str = EXPECTED_SOURCE_SHA256) -> dict[str, Any]:
    if sha256(path) != expected_source_sha256:
        raise ContractError("source identity hash mismatch")
    raw = path.read_bytes().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(raw, newline=""), dialect="excel"))
    if len(rows) != 11:
        raise ContractError("source identity total-row count mismatch")
    selected = [row for row in rows if row.get("domain_status") == "IN_DOMAIN"]
    excluded = [row for row in rows if row.get("domain_status") != "IN_DOMAIN"]
    if len(selected) != 10 or len(excluded) != 1:
        raise ContractError("source identity selected/excluded count mismatch")
    labels = [row["nominal_pressure_bar"].removesuffix(".0") for row in selected]
    if labels != EXPECTED_PRESSURES:
        raise ContractError("source identity pressure labels or order mismatch")
    if excluded[0]["nominal_pressure_bar"].removesuffix(".0") != "13" or excluded[0]["domain_status"] != "OUTSIDE_LOCAL_CONSTITUTIVE_DOMAIN":
        raise ContractError("source identity excluded condition mismatch")
    header = list(rows[0])
    canonical = canonical_json({
        "specification": SPEC_VERSION,
        "encoding": "UTF-8",
        "csv_dialect": "RFC4180_EXCEL",
        "header": header,
        "selection": {"field": "domain_status", "value": "IN_DOMAIN"},
        "rows": [[row[name] for name in header] for row in selected],
    })
    return {
        "specification": SPEC_VERSION,
        "source_sha256": expected_source_sha256,
        "header_rows": 1,
        "total_data_rows": 11,
        "selected_rows": 10,
        "excluded_rows": 1,
        "selected_pressure_labels_bar": labels,
        "excluded_pressure_label_bar": "13",
        "selected_row_canonical_sha256_v2": hashlib.sha256(canonical).hexdigest(),
    }
