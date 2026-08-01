"""Normative VAL-001 schemas generated without governed record instances."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .framework import ContractError, canonical_json, load_json
from .schema import lint_schema

NORMATIVE_REGISTRY = "validation/val001/VAL_001_NORMATIVE_SCHEMA_CONTRACT_REGISTRY.json"
EXPLICIT_REGISTRY = "validation/val001/VAL_001_EXPLICIT_SCHEMA_SPECIFICATION_REGISTRY.json"
ASSIGNMENT_REGISTRY = "validation/val001/VAL_001_IMMUTABLE_PROFILE_ASSIGNMENT_REGISTRY.json"
TRANSITION_MATRIX = "validation/val001/VAL_001_SCHEMA_PROVENANCE_TRANSITION_MATRIX.json"
TAXONOMY = "validation/val001/VAL_001_SCHEMA_TAXONOMY_AND_COUNTING_SPECIFICATION.json"
MUTATION_INVENTORY = "validation/val001/VAL_001_EXPLICIT_MUTATION_INVENTORY.json"
MUTATION_COVERAGE = "validation/val001/VAL_001_MUTATION_EXECUTION_COVERAGE.json"

ALLOWED_ORIGINS = {
    "NORMATIVE_CLASS_CONTRACT",
    "NORMATIVE_VERSION_CONTRACT",
    "NORMATIVE_RECORD_CONTRACT",
}


def load_normative_registry(root: Path) -> dict[str, Any]:
    registry = load_json(root / NORMATIVE_REGISTRY)
    contracts = registry.get("contracts", [])
    by_id = {item["normative_contract_id"]: item for item in contracts}
    by_spec = {item["specification_id"]: item for item in contracts}
    if len(by_id) != len(contracts) or len(by_spec) != len(contracts):
        raise ContractError("VAL001_DUPLICATE_NORMATIVE_CONTRACT")
    for contract in contracts:
        if contract.get("origin") not in ALLOWED_ORIGINS:
            raise ContractError("VAL001_PROHIBITED_NORMATIVE_CONTRACT_ORIGIN")
        if not contract.get("authoritative_source_references"):
            raise ContractError("VAL001_NORMATIVE_CONTRACT_WITHOUT_AUTHORITY")
        lint_schema(contract["governing_schema"])
    bindings = registry.get("record_bindings", [])
    if len({item["path"] for item in bindings}) != len(bindings):
        raise ContractError("VAL001_DUPLICATE_NORMATIVE_RECORD_BINDING")
    used = {item["specification_id"] for item in bindings}
    unknown = used - set(by_spec)
    if unknown:
        raise ContractError(f"VAL001_UNKNOWN_NORMATIVE_SPECIFICATION:{sorted(unknown)}")
    unused = set(by_spec) - used
    if unused:
        raise ContractError(f"VAL001_UNREFERENCED_CURRENT_SPECIFICATION:{sorted(unused)}")
    return registry


def generated_explicit_registry(root: Path) -> dict[str, Any]:
    """Generate the compatibility registry from normative contracts only."""
    normative = load_normative_registry(root)
    specifications = []
    for contract in normative["contracts"]:
        specifications.append({
            "specification_id": contract["specification_id"],
            "normative_contract_id": contract["normative_contract_id"],
            "origin": contract["origin"],
            "record_class": contract["record_class"],
            "record_version": contract["record_version"],
            "schema": contract["governing_schema"],
            "schema_id": contract["schema_id"],
            "schema_path": NORMATIVE_REGISTRY,
            "schema_version": contract["schema_version"],
            "scope": contract["scope"],
            "semantic_profile_id": contract["semantic_profile_id"],
        })
    return {
        "schema_version": "espresso.val001.explicit_schema_specification_registry.v2",
        "record_id": "VAL001-EXPLICIT-SCHEMA-SPECIFICATION-REGISTRY-2",
        "allowed_origins": sorted(ALLOWED_ORIGINS),
        "prohibited_origins": [
            "INSTANCE_INFERENCE",
            "STRUCTURAL_SIGNATURE_INFERENCE",
            "FILENAME_INFERENCE",
            "COPIED_INFERRED_SCHEMA_WITH_RELABELLED_ORIGIN",
        ],
        "specifications": specifications,
        "record_bindings": normative["record_bindings"],
        "counts": {
            "current_normative_specifications": len(specifications),
            "current_referenced_specifications": len({b["specification_id"] for b in normative["record_bindings"]}),
            "current_unreferenced_specifications": 0,
            "instance_inferred_governing_schemas": 0,
            "copied_inferred_governing_schemas": 0,
            "structural_signature_governing_schemas": 0,
            "filename_selected_governing_schemas": 0,
        },
    }


def verify_generated_registry(root: Path) -> dict[str, int]:
    expected = canonical_json(generated_explicit_registry(root))
    actual = canonical_json(load_json(root / EXPLICIT_REGISTRY))
    if expected != actual:
        raise ContractError("VAL001_GOVERNING_SCHEMA_REGISTRY_NOT_NORMATIVELY_REPRODUCIBLE")
    registry = load_normative_registry(root)
    return {
        "normative_contracts": len(registry["contracts"]),
        "governing_schemas_reproducible_without_record_instances": len(registry["contracts"]),
        "instance_inferred": 0,
        "copied_inferred": 0,
        "structural_signature": 0,
        "filename_selected": 0,
    }


def schema_digest(schema: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(schema)).hexdigest()


def taxonomy_counts(root: Path) -> dict[str, Any]:
    normative = load_normative_registry(root)
    assignments = load_json(root / ASSIGNMENT_REGISTRY)["assignments"]
    schema_counts: dict[str, int] = {}
    for item in assignments:
        schema_counts[item["schema_id"]] = schema_counts.get(item["schema_id"], 0) + 1
    schema_documents = sum(1 for item in assignments if item["record_class"] == "SCHEMA")
    administrative = sum(1 for schema_id in schema_counts if any(token in schema_id for token in (
        "schema_document", "invocation_event", "inventory", "registry", "coverage", "closure", "mutation"
    )))
    return {
        "current_normative_specifications": len(normative["contracts"]),
        "current_referenced_specifications": len({item["specification_id"] for item in assignments}),
        "current_unreferenced_specifications": 0,
        "governing_schema_families": len(schema_counts),
        "schema_documents": schema_documents,
        "administrative_meta_schema_families": administrative,
        "schema_assignments": [{"schema_id": key, "record_count": schema_counts[key]} for key in sorted(schema_counts)],
    }
