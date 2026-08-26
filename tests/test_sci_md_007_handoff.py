import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

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


class TestSciMd007Handoff(unittest.TestCase):
    def with_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return fixture_root(Path(temporary.name))

    def test_handoff_and_cross_repository_verify_exact_bytes(self):
        self.assertEqual(MODULE.verify()["status"], "PASS")
        if PUCKWORKS.is_dir():
            self.assertEqual(MODULE.verify(PUCKWORKS)["status"], "PASS")

    def test_one_vendored_byte_tamper_fails(self):
        for name in ("SCI_MD_007_EXPORT.json", "source_package_manifest.json"):
            with self.subTest(name=name):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/upstream" / name
                data = path.read_bytes()
                path.write_bytes(data[:-2] + b" " + data[-1:])
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_lock_hash_tamper_fails(self):
        for field in ("export_sha256", "source_package_manifest_sha256"):
            with self.subTest(field=field):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
                lock = load(path)
                lock[field] = "0" * 64
                dump(path, lock)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_semantic_export_tamper_fails(self):
        mutations = {
            "nested gate": lambda e: e["compound_gates"]["caffeine"]["F2"].update(pass_=True),
            "top-level compound": lambda e: e["compound_feasible"].update(caffeine=True),
            "F5": lambda e: e["paired_coverage"]["F5"].update(pass_=True),
            "disposition": lambda e: e.update(scientific_disposition=MODULE.PASS),
            "task": lambda e: e.update(task_id="SCI-MD-008"),
            "schema": lambda e: e.update(schema_version="fake"),
            "operational status": lambda e: e.update(operational_status="INCOMPLETE"),
            "predictor activation": lambda e: e.update(model_stage="COMPLETED_SIMPLE_MODELS"),
            "extractable inference": lambda e: e.update(
                extractable_inventory_mapping_status="DIRECTLY_SUPPORTED"
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json"
                export = load(path)
                mutation(export)
                for node in (
                    export["compound_gates"]["caffeine"]["F2"],
                    export["paired_coverage"]["F5"],
                ):
                    if "pass_" in node:
                        node["pass"] = node.pop("pass_")
                dump(path, export)
                lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
                lock = load(lock_path)
                lock["export_sha256"] = MODULE._sha(path.read_bytes())
                dump(lock_path, lock)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_angeloni_lineage_identifier_fails(self):
        root = self.with_fixture()
        path = root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json"
        export = load(path)
        export["source_lineage"] = "angeloni2023"
        dump(path, export)
        lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
        lock = load(lock_path)
        lock["export_sha256"] = MODULE._sha(path.read_bytes())
        dump(lock_path, lock)
        self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_local_result_tamper_fails(self):
        root = self.with_fixture()
        path = root / "docs/validation/sci_md_007/RESULT.json"
        result = load(path)
        result["inventory_predictor_activation"] = "ACTIVE"
        dump(path, result)
        self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_fake_commit_and_wrong_tree_fail_cross_repository(self):
        if not PUCKWORKS.is_dir():
            self.skipTest("optional cross-repository checkout is unavailable")
        root = self.with_fixture()
        path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
        lock = load(path)
        lock["commit"] = "a" * 40
        lock["tree"] = "b" * 40
        dump(path, lock)
        report = MODULE.verify(PUCKWORKS, root=root)
        self.assertFalse(report["checks"]["cross_repository_commit"])
        self.assertFalse(report["checks"]["cross_repository_tree"])

    def test_result_preserves_claim_ceiling_and_boundaries(self):
        result = load(ROOT / "docs/validation/sci_md_007/RESULT.json")
        self.assertEqual(result["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["change_declaration"], "NO_GOVERNING_PHYSICS_CHANGE")
        self.assertEqual(result["openfoam_execution"], "NOT_RUN")
        self.assertIs(result["angeloni_reuse"], False)
        self.assertIs(result["sci_md_006_reopened"], False)
        self.assertEqual(result["extractable_inventory_mapping_status"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
