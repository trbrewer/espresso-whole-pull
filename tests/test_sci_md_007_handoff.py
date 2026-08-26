import importlib.util
import json
import shutil
import subprocess
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


def resign_export(root, export):
    here = root / "docs/validation/sci_md_007"
    export_path = here / "upstream/SCI_MD_007_EXPORT.json"
    manifest_path = here / "upstream/source_package_manifest.json"
    lock_path = here / "PUCKWORKS_LOCK.json"
    dump(export_path, export)
    manifest = load(manifest_path)
    manifest["outputs"]["docs/analysis/sci_md_007/SCI_MD_007_EXPORT.json"] = MODULE._sha(export_path.read_bytes())
    dump(manifest_path, manifest)
    lock = load(lock_path)
    lock["export_sha256"] = MODULE._sha(export_path.read_bytes())
    lock["source_package_manifest_sha256"] = MODULE._sha(manifest_path.read_bytes())
    dump(lock_path, lock)


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
        self.assertEqual(result["g0_fraction_boundary_parity"], "NOT_RUN_SEPARATE_DEFERRED")

    def test_manifest_structure_tampers_fail(self):
        mutations = {
            "missing export member": lambda m: m["outputs"].pop("docs/analysis/sci_md_007/SCI_MD_007_EXPORT.json"),
            "missing input path": lambda m: m["inputs"].pop(next(iter(m["inputs"]))),
            "missing output path": lambda m: m["outputs"].pop(next(iter(m["outputs"]))),
            "wrong schema": lambda m: m.update(schema_version="1.1.0-R1"),
            "bad member hash": lambda m: m["inputs"].update({next(iter(m["inputs"])): "x"}),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/upstream/source_package_manifest.json"
                manifest = load(path)
                mutation(manifest)
                dump(path, manifest)
                lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
                lock = load(lock_path)
                lock["source_package_manifest_sha256"] = MODULE._sha(path.read_bytes())
                dump(lock_path, lock)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_required_r2_gate_surface_tampers_fail(self):
        mutations = {
            "missing F4 varying groups": lambda e: e["compound_gates"]["caffeine"]["F4"]["quantitative_route"].pop("within_species_varying_groups"),
            "missing F7 leakage": lambda e: e["compound_gates"]["caffeine"]["F7"].pop("publication_leakage"),
            "missing species support": lambda e: e["compound_gates"]["caffeine"]["F7"].pop("species_support_all_folds"),
            "missing roast support": lambda e: e["compound_gates"]["caffeine"]["F7"].pop("harmonized_roast_category_support_all_folds"),
            "missing metric support": lambda e: e["compound_gates"]["caffeine"]["F7"].pop("quantitative_metric_type_support_all_folds"),
            "missing fold intersections": lambda e: e["compound_gates"]["caffeine"]["F7"]["proposed_folds"][0].pop("data_lineage_intersection_ids"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                root = self.with_fixture()
                export = load(root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json")
                mutation(export)
                resign_export(root, export)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_boundary_claim_tampers_fail(self):
        mutations = {
            "claim ceiling": lambda e: e.pop("claim_ceiling"),
            "partial claim ceiling": lambda e: e.update(claim_ceiling=["Physical validation remains NOT_ESTABLISHED."]),
            "Angeloni": lambda e: e.update(source_lineage="Angeloni"),
            "SCI-MD-006": lambda e: e.update(sci_md_006_reopened=True),
            "unexpected predictor": lambda e: e.update(model_stage="MODEL_RUN"),
            "OpenFOAM": lambda e: e.update(openfoam_execution="RUN"),
            "runtime activation": lambda e: e.update(inventory_predictor_activation="ACTIVE"),
            "extractable": lambda e: e.update(extractable_inventory_mapping_status="DIRECTLY_SUPPORTED"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                root = self.with_fixture()
                export = load(root / "docs/validation/sci_md_007/upstream/SCI_MD_007_EXPORT.json")
                mutation(export)
                resign_export(root, export)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_lock_authority_tampers_fail(self):
        mutations = {
            "remote": lambda lock: lock.update(repository="https://example.invalid/puckworks.git"),
            "schema": lambda lock: lock.update(schema_version="v2"),
            "result schema": lambda lock: lock.update(result_schema_version="1.1.0-R1"),
            "cutoff": lambda lock: lock.update(evidence_cutoff_date="2026-08-26"),
            "contract": lambda lock: lock.update(r2_contract_sha256="0" * 64),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
                lock = load(path)
                mutation(lock)
                dump(path, lock)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_contract_and_package_closure_tampers_fail(self):
        cases = (
            "R2_EVIDENCE_PACKAGE_CORRECTION_CONTRACT.json",
            "R2_PACKAGE_AUTHORITY_CLOSURE.json",
        )
        for name in cases:
            with self.subTest(name=name):
                root = self.with_fixture()
                path = root / "docs/validation/sci_md_007/upstream" / name
                payload = load(path)
                if "claim_ceiling" in payload:
                    payload["claim_ceiling"] = payload["claim_ceiling"][:1]
                    lock_field = "r2_contract_sha256"
                else:
                    payload["final_package_status"] = "FAIL"
                    lock_field = "package_authority_closure_sha256"
                dump(path, payload)
                lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
                lock = load(lock_path)
                lock[lock_field] = MODULE._sha(path.read_bytes())
                dump(lock_path, lock)
                self.assertEqual(MODULE.verify(root=root)["status"], "FAIL")

    def test_boundary_evidence_forbidden_paths_fail(self):
        for forbidden in (
            "solver/injected.C",
            "applications/injected.C",
            "runtime/inventory_provider.py",
            "docs/analysis/sci_md_006/injected.json",
            "g0/injected.json",
            "protected/angeloni.json",
        ):
            with self.subTest(forbidden=forbidden):
                temporary = tempfile.TemporaryDirectory()
                self.addCleanup(temporary.cleanup)
                root = Path(temporary.name)
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
                subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
                (root / "README.md").write_text("base\n")
                subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
                subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "base"], check=True)
                base = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                old = MODULE.STARTING_COMMIT
                self.addCleanup(setattr, MODULE, "STARTING_COMMIT", old)
                MODULE.STARTING_COMMIT = base
                path = root / forbidden
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("injected\n")
                self.assertEqual(MODULE.derive_boundary_evidence(root)["status"], "FAIL")

    def test_verifier_claims_only_exported_boolean_reduction(self):
        text = (ROOT / "validation/sci_md_007/verify_handoff.py").read_text()
        self.assertIn("independently reduces the exported Boolean", text)
        self.assertIn("Puckworks\nremains the authority that derives gate primitives", text)
        self.assertNotIn("independent raw-register", text.lower())

    def test_cross_repository_manifest_member_tamper_fails(self):
        if not PUCKWORKS.is_dir():
            self.skipTest("optional cross-repository checkout is unavailable")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        producer = Path(temporary.name) / "producer"
        subprocess.run(["git", "clone", "--quiet", str(PUCKWORKS), str(producer)], check=True)
        subprocess.run(["git", "-C", str(producer), "checkout", "--quiet", "bd811cff2765573b5f9a4c8bf26f95a5a0d6392f"], check=True)
        subprocess.run(["git", "-C", str(producer), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(producer), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(producer), "remote", "set-url", "origin", "https://github.com/trbrewer/puckworks.git"], check=True)
        member = producer / "puckworks/data/sci_md_007/search_log.csv"
        member.write_bytes(member.read_bytes() + b"\n")
        subprocess.run(["git", "-C", str(producer), "add", str(member)], check=True)
        subprocess.run(["git", "-C", str(producer), "commit", "--quiet", "-m", "synthetic manifest member tamper"], check=True)
        root = self.with_fixture()
        lock_path = root / "docs/validation/sci_md_007/PUCKWORKS_LOCK.json"
        lock = load(lock_path)
        lock["commit"] = subprocess.check_output(["git", "-C", str(producer), "rev-parse", "HEAD"], text=True).strip()
        lock["tree"] = subprocess.check_output(["git", "-C", str(producer), "rev-parse", "HEAD^{tree}"], text=True).strip()
        dump(lock_path, lock)
        report = MODULE.verify(producer, root=root)
        self.assertFalse(report["checks"]["cross_repository_manifest_member_closure"])


if __name__ == "__main__":
    unittest.main()
