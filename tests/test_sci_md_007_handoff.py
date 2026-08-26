import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_sci_md_007", ROOT / "validation/sci_md_007/verify_handoff.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PUCKWORKS = ROOT.parent / "puckworks-sci-md-007"


def fixture_root(tmp_path):
    target = tmp_path / "ewp"
    shutil.copytree(
        ROOT / "docs/validation/sci_md_007", target / "docs/validation/sci_md_007"
    )
    return target


def load(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def test_handoff_and_cross_repository_verify_exact_bytes():
    assert MODULE.verify()["status"] == "PASS"
    assert MODULE.verify(PUCKWORKS)["status"] == "PASS"


@pytest.mark.parametrize(
    "name", ["SCI_MD_007_EXPORT.json", "source_package_manifest.json"]
)
def test_one_vendored_byte_tamper_fails(tmp_path, name):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/upstream" / name
    data = path.read_bytes()
    path.write_bytes(data[:-2] + b" " + data[-1:])
    assert MODULE.verify(root=root)["status"] == "FAIL"


@pytest.mark.parametrize("field", ["export_sha256", "source_package_manifest_sha256"])
def test_lock_hash_tamper_fails(tmp_path, field):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
    lock = load(path)
    lock[field] = "0" * 64
    dump(path, lock)
    assert MODULE.verify(root=root)["status"] == "FAIL"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda e: e["compound_gates"]["caffeine"]["F2"].update(pass_=True),
        lambda e: e["compound_feasible"].update(caffeine=True),
        lambda e: e["paired_coverage"]["F5"].update(pass_=True),
        lambda e: e.update(scientific_disposition=MODULE.PASS),
        lambda e: e.update(task_id="SCI-MD-008"),
        lambda e: e.update(schema_version="fake"),
        lambda e: e.update(operational_status="INCOMPLETE"),
        lambda e: e.update(model_stage="COMPLETED_SIMPLE_MODELS"),
        lambda e: e.update(extractable_inventory_mapping_status="DIRECTLY_SUPPORTED"),
    ],
)
def test_semantic_export_tamper_fails(tmp_path, mutation):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json"
    export = load(path)
    mutation(export)
    # Translate the deliberately awkward key used to avoid Python's reserved word.
    for node in [
        export["compound_gates"]["caffeine"]["F2"],
        export["paired_coverage"]["F5"],
    ]:
        if "pass_" in node:
            node["pass"] = node.pop("pass_")
    dump(path, export)
    lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
    lock = load(lock_path)
    lock["export_sha256"] = MODULE._sha(path.read_bytes())
    dump(lock_path, lock)
    assert MODULE.verify(root=root)["status"] == "FAIL"


def test_angeloni_lineage_identifier_fails(tmp_path):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json"
    export = load(path)
    export["source_lineage"] = "angeloni2023"
    dump(path, export)
    lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
    lock = load(lock_path)
    lock["export_sha256"] = MODULE._sha(path.read_bytes())
    dump(lock_path, lock)
    assert MODULE.verify(root=root)["status"] == "FAIL"


def test_local_result_tamper_fails(tmp_path):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/RESULT.json"
    result = load(path)
    result["inventory_predictor_activation"] = "ACTIVE"
    dump(path, result)
    assert MODULE.verify(root=root)["status"] == "FAIL"


def test_fake_commit_and_wrong_tree_fail_cross_repository(tmp_path):
    root = fixture_root(tmp_path)
    path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
    lock = load(path)
    lock["commit"] = "a" * 40
    lock["tree"] = "b" * 40
    dump(path, lock)
    report = MODULE.verify(PUCKWORKS, root=root)
    assert not report["checks"]["cross_repository_commit"]
    assert not report["checks"]["cross_repository_tree"]


def test_result_preserves_claim_ceiling_and_boundaries():
    result = load(ROOT / "docs/validation/sci_md_007/RESULT.json")
    assert result["physical_validation"] == "NOT_ESTABLISHED"
    assert result["change_declaration"] == "NO_GOVERNING_PHYSICS_CHANGE"
    assert result["openfoam_execution"] == "NOT_RUN"
    assert result["angeloni_reuse"] is False and result["sci_md_006_reopened"] is False
    assert result["extractable_inventory_mapping_status"] == "NOT_ESTABLISHED"
