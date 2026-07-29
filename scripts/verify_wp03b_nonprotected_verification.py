#!/usr/bin/env python3
"""Independent historical and A1/P1 WP-0.3B boundary verifier."""
import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

from wp03b_path_boundary import changed_paths

BASELINE = "7f26b643fde4c99263384c402547e9d6c606c99e"
P1_BASELINE = "32da9010e555887d7aab8231ee827df9bcaabfce"
ORIGINAL_CONTRACT = "4b05d9a8f7f91dc6e476c9942639524213541d3f887452d4fb369715bc9f89a6"
ORIGINAL_RESULT = "80d0a91d6456ff1219e74f0503f3e6846c9974b3ed868cff19f6f9da943cde90"
P1_CONTRACT_PATH = "validation/contracts/WP_0_3B_A1_P1_PREEXECUTION_CORRECTION_CONTRACT.json"
RESULT_PATH = "validation/results/WP_0_3B_A1_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json"

P1_PRE = frozenset({
    ".github/workflows/static-validation.yml", "PACKAGE_QA_STATUS.json",
    "SOURCE_PACKAGE_MANIFEST.json",
    "docs/PROJECT_STATE.md",
    "docs/verification/WP_0_3B_NONPROTECTED_EXTRACTION_REFERENCES.md",
    "scripts/generate_source_manifest.py",
    "scripts/verify_wp03b_nonprotected_verification.py",
    "scripts/wp03b_path_boundary.py", "tests/test_wp03b_boundary.py",
    "tests/test_wp03b_moroney2017.py",
    "tests/test_wp03b_observables.py", "tools/reference/wp03b/canonical_run.py",
    "tools/reference/wp03b/moroney2017.py",
    "tools/reference/wp03b/observables.py",
    "validation/amendments/WP_0_3B_A1_P1_PREEXECUTION_CORRECTION.json",
    P1_CONTRACT_PATH,
    "validation/evidence/MORONEY2016_EQUATIONS_87_97_GOVERNED_TRANSCRIPTION.json",
})
P1_FINAL = P1_PRE | {RESULT_PATH}

FROZEN = {
    "validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json":
        "75a79e9972176668a8bfdb574ea16cbf39373a9ea11078009bc7b997c2f76859",
    "validation/wp02/WP02_001_CLOSURE_CONTRACT.json":
        "2c898dd91e558ce62006dc81de9cff20bb633b52a89f6fa5a44c5edcda50d57a",
    "config/reference_R0.json":
        "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
    "config/reconstruction_R1_waszkiewicz_9bar.json":
        "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
    "config/reconstruction_WP02A_waszkiewicz_9bar.json":
        "81a9089061d762aaf785a7764cebb8e0947e4f3c14bb833d58a204d2c816407e",
    "config/reconstruction_WP02A_waszkiewicz_8bar.json":
        "ac87cfdff2862401b33ac01fa31d87bf966e062cecd153ce59ab4a9518feb57e",
}
MODULES = ("canonical_run.py", "liang2021.py", "matias2023.py",
           "moroney2017.py", "moroney2017_derivation.py", "observables.py",
           "provenance.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reachable(root, commit):
    return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                          cwd=root, stdout=subprocess.DEVNULL).returncode == 0


def _all_pass(value):
    if isinstance(value, str) and value in {"PASS", "FAIL"}:
        return value == "PASS"
    if isinstance(value, dict):
        if "status" in value and value["status"] != "PASS":
            return False
        return all(_all_pass(v) for k, v in value.items()
                   if k not in {"diagnostics", "endpoint_roundoff_diagnostic"})
    if isinstance(value, list):
        return all(_all_pass(v) for v in value)
    return True


def evaluate_p1(contract, repository_paths, frozen_hashes, original_hashes,
                result, current_modules, evidence_hashes=None,
                expected_implementation=None):
    result_present = result is not None
    expected = P1_FINAL if result_present else P1_PRE
    checks = {
        "contract_path_sets_equal_independent_constants":
            set(contract["preexecution_paths"]) == P1_PRE and
            set(contract["final_result_only_paths"]) == {RESULT_PATH},
        "repository_path_set_exact": repository_paths == expected,
        "historical_artifacts_unchanged":
            original_hashes == (ORIGINAL_CONTRACT, ORIGINAL_RESULT),
        "frozen_scientific_hashes": frozen_hashes == FROZEN,
        "threshold_not_relaxed":
            contract["moroney"]["refinement_ratio_maximum"] == 0.35 and
            contract["moroney"]["composite_ratio_maximum"] == 0.35,
        "physical_validation_bounded":
            "physical validation is established" in contract["claim_ceiling"],
    }
    if not result_present:
        checks["preexecution_result_absent"] = True
        return checks
    identity = result.get("identity", {})
    executions = result.get("execution_counts", {})
    gates = result.get("component_gates", {})
    checks.update({
        "result_schema":
            result.get("schema_version") == contract["result"]["schema_version"],
        "result_contract_binding":
            identity.get("p1_contract_sha256") == contract["_observed_sha256"],
        "result_module_hashes":
            identity.get("module_sha256") == current_modules,
        "result_evidence_bindings":
            evidence_hashes is not None and
            identity.get("amendment_sha256") == evidence_hashes["amendment"] and
            identity.get("transcription_sha256") == evidence_hashes["transcription"] and
            identity.get("derivation_sha256") == evidence_hashes["derivation"],
        "result_implementation_binding":
            expected_implementation is not None and
            (identity.get("implementation_commit"),
             identity.get("implementation_tree")) == expected_implementation,
        "result_historical_bindings":
            identity.get("original_contract_sha256") == ORIGINAL_CONTRACT and
            identity.get("original_failed_result_sha256") == ORIGINAL_RESULT,
        "all_component_gates_present":
            set(gates) == set(contract["gate_inventory"]),
        "all_component_gates_pass": _all_pass(gates),
        "matias_present": "matias2023" in result,
        "observables_have_subgates":
            isinstance(gates.get("observables"), dict) and
            set(gates.get("observables", {})) ==
            set(contract["gate_inventory"]["observables"]),
        "execution_accounting":
            executions == {"amended_canonical": 1, "openfoam": 0,
                           "protected_access": 0, "puckworks_code": 0,
                           "scientific_scores": 0, "source_or_holdout_fits": 0,
                           "wp02_analyzer": 0},
        "final_disposition":
            result.get("overall_disposition") ==
            contract["result"]["required_disposition"],
        "physical_validation":
            result.get("physical_validation") == "NOT_ESTABLISHED",
        "runtime_wp02_coupling":
            result.get("runtime_wp02_coupling") is False,
    })
    return checks


def verify(root):
    contract_path = root / P1_CONTRACT_PATH
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["_observed_sha256"] = sha(contract_path)
    result_path = root / RESULT_PATH
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    module_hashes = {name: sha(root / "tools/reference/wp03b" / name)
                     for name in MODULES}
    evidence_hashes = {
        "amendment": sha(root/"validation/amendments/WP_0_3B_A1_MORONEY_VERIFICATION_AMENDMENT.json"),
        "transcription": sha(root/"validation/evidence/MORONEY2016_EQUATIONS_87_97_GOVERNED_TRANSCRIPTION.json"),
        "derivation": sha(root/"validation/evidence/MORONEY2016_SECOND_ORDER_COMPOSITE_DERIVATION.json")}
    expected = None
    if result is not None:
        result_commit = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "-1", "--",
             RESULT_PATH], cwd=root, text=True, capture_output=True,
            check=True).stdout.strip()
        parent = subprocess.run(["git", "rev-parse", result_commit+"^"],
                                cwd=root, text=True, capture_output=True,
                                check=True).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", parent+"^{tree}"], cwd=root,
                              text=True, capture_output=True,
                              check=True).stdout.strip()
        expected = (parent, tree)
    checks = evaluate_p1(
        contract, changed_paths(root, P1_BASELINE),
        {path: sha(root/path) for path in FROZEN},
        (sha(root/"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json"),
         sha(root/"validation/results/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_RESULT.json")),
        result, module_hashes, evidence_hashes, expected)
    checks["preserved_commits_reachable"] = all(_reachable(root, c) for c in
        ("d0180a84bed7a81b62ec43dee02e6150e89c3f21",
         "78356b181fc1d61935721a4d6d7469a7420a5cae", P1_BASELINE))
    passed = all(checks.values())
    state = ("AMENDED_CANONICAL_RESULT_PRESENT_AND_VERIFIED" if result
             else "PREEXECUTION_FROZEN_AWAITING_CANONICAL_RESULT")
    return {"schema_version": "espresso.public.wp_0_3b_a1_p1_boundary.v1",
            "status": state if passed else "FAIL", "checks": checks,
            "changed_paths": sorted(changed_paths(root, P1_BASELINE))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
