import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import verify_wp03b_nonprotected_verification as verifier
import wp03b_path_boundary as paths


class TestBoundary(unittest.TestCase):
    def test_wp03c_stage0_extension_is_independently_exact(self):
        expected = verifier.G1_FINAL | verifier.WP03C_STAGE0
        self.assertTrue(verifier.G1_FINAL <= expected)
        self.assertEqual(expected, verifier.G1_FINAL | verifier.WP03C_STAGE0)
        self.assertNotEqual(expected | {"solver/unauthorized.C"}, expected)

    def contract(self):
        value = json.loads((ROOT/verifier.P1_CONTRACT_PATH).read_text())
        value["_observed_sha256"] = verifier.sha(ROOT/verifier.P1_CONTRACT_PATH)
        return value

    def test_fixed_sets_cannot_be_enlarged(self):
        contract = self.contract()
        self.assertEqual(set(contract["preexecution_paths"]), set(verifier.P1_PRE))
        self.assertEqual(set(contract["final_result_only_paths"]),
                         {verifier.RESULT_PATH})
        for extra in ("solver/espressoWholePullFoam/espressoWholePullFoam.C",
                      "scripts/analyze_wp02.py", "protected/source.csv"):
            changed = set(verifier.P1_PRE)
            changed.add(extra)
            checks = verifier.evaluate_p1(
                contract, changed, verifier.FROZEN,
                (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT),
                None, {})
            self.assertFalse(checks["repository_path_set_exact"])
        omitted = set(verifier.P1_PRE)
        omitted.remove("tools/reference/wp03b/canonical_run.py")
        self.assertFalse(verifier.evaluate_p1(
            contract, omitted, verifier.FROZEN,
            (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT),
            None, {})["repository_path_set_exact"])

    def test_valid_preexecution_state(self):
        checks = verifier.evaluate_p1(
            self.contract(), set(verifier.P1_PRE), verifier.FROZEN,
            (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT),
            None, {})
        self.assertTrue(all(checks.values()))

    def _valid_result(self):
        from tools.reference.wp03b import canonical_run
        result = canonical_run.build_a1_amended_result(
            ROOT, "freeze-commit", "freeze-tree")
        return result

    def test_valid_result_and_adversarial_results(self):
        result = self._valid_result()
        contract = self.contract()
        evidence = {
            "amendment": result["identity"]["amendment_sha256"],
            "transcription": result["identity"]["transcription_sha256"],
            "derivation": result["identity"]["derivation_sha256"]}
        args = (contract, set(verifier.P1_FINAL), verifier.FROZEN,
                (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT))
        checks = verifier.evaluate_p1(
            *args, result, result["identity"]["module_sha256"], evidence,
            ("freeze-commit", "freeze-tree"))
        self.assertTrue(all(checks.values()), checks)
        mutations = []
        bad = copy.deepcopy(result)
        bad["component_gates"]["moroney"]["trajectory_refinement"] = "FAIL"
        mutations.append(("all_component_gates_pass", bad))
        bad = copy.deepcopy(result); bad["identity"]["p1_contract_sha256"] = "0"*64
        mutations.append(("result_contract_binding", bad))
        bad = copy.deepcopy(result); bad["identity"]["module_sha256"]["canonical_run.py"] = "0"*64
        mutations.append(("result_module_hashes", bad))
        bad = copy.deepcopy(result); bad["identity"]["implementation_commit"] = "other"
        mutations.append(("result_implementation_binding", bad))
        bad = copy.deepcopy(result); del bad["matias2023"]
        mutations.append(("matias_present", bad))
        bad = copy.deepcopy(result); bad["component_gates"]["observables"] = {"status": "PASS"}
        mutations.append(("observables_have_subgates", bad))
        bad = copy.deepcopy(result); bad["execution_counts"]["openfoam"] = 1
        mutations.append(("execution_accounting", bad))
        bad = copy.deepcopy(result); bad["physical_validation"] = "ESTABLISHED"
        mutations.append(("physical_validation", bad))
        for gate, bad in mutations:
            got = verifier.evaluate_p1(
                *args, bad, result["identity"]["module_sha256"], evidence,
                ("freeze-commit", "freeze-tree"))
            self.assertFalse(got[gate], gate)

    def test_structured_physical_validation_and_overclaims(self):
        result = self._valid_result()
        contract = self.contract()
        evidence = {
            "amendment": result["identity"]["amendment_sha256"],
            "transcription": result["identity"]["transcription_sha256"],
            "derivation": result["identity"]["derivation_sha256"]}
        governance = {"contract_physical_validation": "NOT_ESTABLISHED",
                      "result_physical_validation": "NOT_ESTABLISHED"}
        base = (contract, set(verifier.G1_FINAL), verifier.FROZEN,
                (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT),
                result, result["identity"]["module_sha256"], evidence,
                ("freeze-commit", "freeze-tree"))
        self.assertTrue(all(verifier.evaluate_p1(
            *base, governance).values()))
        for value, gate in (
                ("ESTABLISHED", "contract_physical_validation"),
                ("PHYSICALLY_VALIDATED", "contract_physical_validation")):
            bad = dict(governance, contract_physical_validation=value)
            self.assertFalse(verifier.evaluate_p1(*base, bad)[gate])
        bad = copy.deepcopy(result); bad["physical_validation"] = "ESTABLISHED"
        args = (contract, set(verifier.G1_FINAL), verifier.FROZEN,
                (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT), bad,
                result["identity"]["module_sha256"], evidence,
                ("freeze-commit", "freeze-tree"), governance)
        self.assertFalse(verifier.evaluate_p1(*args)["physical_validation"])
        for phrase in ("physical validation is established",
                       "independently validated", "experimentally validated"):
            bad = copy.deepcopy(result); bad["claim_ceiling"] = phrase
            args = (contract, set(verifier.G1_FINAL), verifier.FROZEN,
                    (verifier.ORIGINAL_CONTRACT, verifier.ORIGINAL_RESULT), bad,
                    result["identity"]["module_sha256"], evidence,
                    ("freeze-commit", "freeze-tree"), governance)
            self.assertFalse(verifier.evaluate_p1(
                *args)["affirmative_overclaims_absent"])

    def test_historical_builder_reconstructs_failure(self):
        from tools.reference.wp03b import canonical_run
        result = canonical_run.run(ROOT, "historical", "historical-tree")
        self.assertEqual(result["overall_disposition"],
                         "NONPROTECTED_REFERENCE_VERIFICATION_FAIL")
        self.assertEqual(result["moroney2017"]["fine"]["refinement_ratio"], 3.0)
        self.assertEqual(result["moroney2017"]["coarse"]["refinement_ratio"],
                         0.7142857142857143)
        self.assertEqual(result["matias2023"]["status"], "PASS")

    def test_amended_builder_deterministic_and_atomic_preflight(self):
        from tools.reference.wp03b import canonical_run
        a = canonical_run.build_a1_amended_result(ROOT, "freeze", "tree")
        b = canonical_run.build_a1_amended_result(ROOT, "freeze", "tree")
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory)/"missing"/"result.json"
            with self.assertRaises(FileNotFoundError):
                canonical_run.atomic_write_result(missing, a)
            self.assertFalse(missing.exists())

    def test_python38_grammar_for_new_modules(self):
        for relative in (
            "tools/reference/wp03b/canonical_run.py",
            "tools/reference/wp03b/moroney2017.py",
            "tools/reference/wp03b/observables.py",
            "scripts/wp03b_path_boundary.py",
            "scripts/verify_wp03b_nonprotected_verification.py"):
            ast.parse((ROOT/relative).read_text(), filename=relative,
                      feature_version=(3, 8))

    def test_generated_static_report_filter_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.test"],
                           cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root,
                           check=True)
            (root/"seed").write_text("seed")
            subprocess.run(["git", "add", "seed"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
            report = root/paths.STATIC_REPORT
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({
                "schema_version": "espresso.whole_pull.static_validation.v0.2.0",
                "status": "PASS"}))
            self.assertEqual(paths.changed_paths(root, "HEAD"), set())
            other = root/"elsewhere"/"STATIC_VALIDATION_REPORT_V0_2_0.json"
            other.parent.mkdir(); other.write_text(report.read_text())
            self.assertIn(other.relative_to(root).as_posix(),
                          paths.changed_paths(root, "HEAD"))
            other.unlink()
            (root/"arbitrary").write_text("x")
            self.assertIn("arbitrary", paths.changed_paths(root, "HEAD"))
            (root/"arbitrary").unlink()
            subprocess.run(["git", "add", paths.STATIC_REPORT], cwd=root,
                           check=True)
            self.assertIn(paths.STATIC_REPORT, paths.changed_paths(root, "HEAD"))


if __name__ == "__main__":
    unittest.main()
