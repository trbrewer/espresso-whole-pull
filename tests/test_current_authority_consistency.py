from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CURRENT_MARKERS = {
    "README.md": (
        "progressed through VAL-CORPUS-002",
        "No\n> validation, data-planning, solver, or next-mechanism task is active",
        "current scientific gate is additional independent data",
        "Physical validation\n> is **NOT_ESTABLISHED**",
    ),
    "docs/PROJECT_STATE.md": (
        "VAL-CORPUS-002 is `COMPLETE_APPROVED_AND_MERGED`",
        "Active validation case: `NONE`",
        "Active data-planning task: `NONE`",
        "Active solver task: `NONE`",
        "`ADDITIONAL_INDEPENDENT_DATA_REQUIRED`",
        "VAL-CASE-002 is `NOT_STARTED`",
        "Experimental commissioning: `NOT_AUTHORIZED`",
        "New governing physics is\n`NOT_YET_JUSTIFIED`",
        "Physical validation: `NOT_ESTABLISHED`",
    ),
    "docs/QA_STATUS.md": (
        "Merged VAL-CORPUS-002 Stage B2 disposition",
        "No\nvalidation case, data-planning task, solver task, or mechanism-selection task\nis active",
        "`ADDITIONAL_INDEPENDENT_DATA_REQUIRED`",
        "Physical\nvalidation remains `NOT_ESTABLISHED`",
    ),
    "docs/PROGRAM_STATE_AND_FORWARD_PLAN.md": (
        "| Aggregate extraction and cup-chemistry transfer | Partial / source-specific only | VAL-CORPUS-002 completed the governed assessment: local reconstruction and partial directional transfer were observed, but grind-sign reversal, hydraulic target-coverage mismatch, and cross-source time-shape failure remain; general transfer and physical validation are not established |",
        "`PACKAGE_QA_STATUS.json` is the machine-readable exact-head authority for current Python-test and focused current-authority-consistency counts; this handoff deliberately does not duplicate mutable totals. Confirm live pass/fail status from exact-head CI; counts elsewhere in explicitly bounded history remain historical.",
        "VAL_CORPUS_002:\n  COMPLETE_APPROVED_AND_MERGED",
        "ACTIVE_VALIDATION_CASE:\n  NONE",
        "ACTIVE_DATA_PLANNING_TASK:\n  NONE",
        "ACTIVE_SOLVER_TASK:\n  NONE",
        "CURRENT_SCIENTIFIC_GATE:\n  ADDITIONAL_INDEPENDENT_DATA_REQUIRED",
        "VAL_CASE_002:\n  NOT_STARTED",
        "EXPERIMENTAL_COMMISSIONING:\n  NOT_AUTHORIZED",
        "PROTECTED_OR_HOLDOUT_SCORING:\n  NOT_AUTHORIZED",
        "NEW_GOVERNING_PHYSICS:\n  NOT_YET_JUSTIFIED",
        "PHYSICAL_VALIDATION:\n  NOT_ESTABLISHED",
    ),
    "docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md": (
        "VAL-CORPUS-001, WP03-002, and VAL-CORPUS-002 are complete, approved, and\nmerged",
        "ACTIVE_VALIDATION_CASE:\n  NONE",
        "ACTIVE_DATA_PLANNING_TASK:\n  NONE",
        "ACTIVE_SOLVER_TASK:\n  NONE",
        "CURRENT_SCIENTIFIC_GATE:\n  ADDITIONAL_INDEPENDENT_DATA_REQUIRED",
        "VAL_CASE_002:\n  NOT_STARTED",
        "EXPERIMENTAL_COMMISSIONING:\n  NOT_AUTHORIZED",
        "PROTECTED_OR_HOLDOUT_SCORING:\n  NOT_AUTHORIZED",
        "NEW_GOVERNING_PHYSICS:\n  NOT_YET_JUSTIFIED",
        "PHYSICAL_VALIDATION:\n  NOT_ESTABLISHED",
    ),
}

FORBIDDEN_CURRENT_MARKERS = (
    "VAL_CORPUS_002_STAGE_B2_SENSITIVITY_COLOUR_KEY_CORRECTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW",
    "RESULT_COMPLETE_PENDING_EXACT_HEAD_REVIEW",
    "VAL_CORPUS_002_EXTRACTION_AND_CUP_CHEMISTRY",
    "VAL-CORPUS-002 remains to be executed",
    "VAL-CORPUS-002 is not started",
    "VAL-CORPUS-002 is the active next",
    "WP03-002 is pending exact-head review",
    "merge and any next mechanism are not authorized",
    "Aggregate extraction transfer | Not yet adequately assessed",
    "Required next corpus tranche",
    "452/452 PASS",
    "4 focused current-authority consistency tests",
    "Current Python suite | `452/452 PASS`, including 4 focused current-authority consistency tests",
)


HISTORICAL_SECTION_HEADINGS = (
    "# 11. WP03-002 detailed execution plan — `HISTORICAL_EXECUTED_AND_CONSUMED`",
    "# 12. Risks and controls — `HISTORICAL_EXECUTED_AND_CONSUMED`",
    "# 13. Human-owner authority template for WP03-002 — `HISTORICAL_EXECUTED_AND_CONSUMED`",
    "# 14. Resume block for WP03-002 — `HISTORICAL_EXECUTED_AND_CONSUMED`",
)


def historical_program_sections(text: str) -> tuple[str, ...]:
    """Return sections 11-14 after independently validating each boundary."""
    sections = []
    for index, heading in enumerate(HISTORICAL_SECTION_HEADINGS):
        start = text.find(heading)
        if start < 0:
            raise AssertionError(f"program handoff lacks historical boundary: {heading}")
        next_heading = (
            HISTORICAL_SECTION_HEADINGS[index + 1]
            if index + 1 < len(HISTORICAL_SECTION_HEADINGS)
            else "# 15. New-conversation bootstrap"
        )
        end = text.find(next_heading, start + len(heading))
        if end < 0:
            raise AssertionError(f"program handoff lacks boundary after: {heading}")
        section = text[start:end]
        if "NOT_CURRENT_AUTHORITY" not in section:
            raise AssertionError(f"historical section is not explicitly non-current: {heading}")
        sections.append(section)
    return tuple(sections)


def current_program_text(text: str) -> str:
    """Exclude only the explicitly bounded executed-history sections 11-14."""
    historical_program_sections(text)
    start = text.index(HISTORICAL_SECTION_HEADINGS[0])
    resume = text.index("# 15. New-conversation bootstrap", start)
    return text[:start] + text[resume:]


def current_authorities_pass(texts: dict[str, str], qa: dict) -> bool:
    if qa.get("current_governance_milestone") != "VAL_CORPUS_002_COMPLETE_APPROVED_AND_MERGED":
        return False
    if qa.get("canonical_identity_role") != "LAST_SUBSTANTIVE_SCIENTIFIC_MERGE_BASE":
        return False
    if qa.get("live_repository_identity") != "RESOLVE_HEAD_AND_TREE_FROM_GIT":
        return False
    if qa.get("release_qualification") != "PASS":
        return False
    checks = qa.get("current_repository_checks", {})
    python_count = checks.get("python_test_count")
    focused_count = checks.get("current_authority_consistency_test_count")
    if type(python_count) is not int or python_count <= 0:
        return False
    if type(focused_count) is not int or focused_count <= 0:
        return False
    if focused_count > python_count:
        return False
    for key, expected in (
        ("active_validation_case", "NONE"),
        ("active_data_planning_task", "NONE"),
        ("active_solver_task", "NONE"),
        ("current_scientific_gate", "ADDITIONAL_INDEPENDENT_DATA_REQUIRED"),
        ("experimental_commissioning", "NOT_AUTHORIZED"),
        ("protected_or_holdout_scoring", "NOT_AUTHORIZED"),
        ("general_whole_solver_physical_validation", "NOT_ESTABLISHED"),
    ):
        if qa.get(key) != expected:
            return False
    val = qa.get("val_corpus_002", {})
    if val.get("status") != "COMPLETE_APPROVED_AND_MERGED":
        return False
    if val.get("val_case_002") != "NOT_STARTED":
        return False
    if val.get("new_governing_physics") != "NOT_YET_JUSTIFIED":
        return False
    if val.get("physical_validation") != "NOT_ESTABLISHED":
        return False
    xsv = qa.get("xsv_taichi_001", {})
    result_path = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if qa.get("active_cross_solver_verification_task") != "XSV-TAICHI-002":
        return False
    for key, expected in (
        ("status", "EXECUTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW"),
        ("scientific_disposition", result.get("scientific_disposition")),
        ("package_disposition", result.get("package_disposition")),
        ("overall_compatibility_disposition", result.get("overall_disposition")),
        ("latest_authorization_id", "XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04"),
        ("current_scientific_gate", "ADDITIONAL_INDEPENDENT_DATA_REQUIRED"),
        ("human_owner_independent_data_route_decision", "STILL_REQUIRED"),
        ("xsv_taichi_002", "STARTED_AUTHORIZED"),
        ("physical_validation", "NOT_ESTABLISHED"),
    ):
        if xsv.get(key) != expected:
            return False
    execution = xsv.get("retained_numerical_execution", {})
    if execution != {"lbm_governed_runs": 19, "openfoam_governed_runs": 8,
                      "openfoam_process_attempts": 9,
                      "protocol_invalid_pre_solve_attempts": 1,
                      "additional_execution_during_correction": 0}:
        return False
    if xsv.get("corrected_result_sha256") != hashlib.sha256(result_path.read_bytes()).hexdigest():
        return False
    if "overall_scientific_disposition" in xsv:
        return False
    xsv2 = qa.get("xsv_taichi_002", {})
    for key, expected in (
        ("status", "G0_PROTOCOL_BOOTSTRAP_AND_PROSPECTIVE_FREEZE"),
        ("authorization_id", "XSV-TAICHI-002-SYNTHETIC-MORPHOLOGY-COLLAPSE-SCREEN-2026-08-05"),
        ("issue", 60),
        ("planned_scored_cuda_identities", 22),
        ("absolute_process_attempt_ceiling", 24),
        ("current_scientific_gate", "ADDITIONAL_INDEPENDENT_DATA_REQUIRED"),
        ("physical_validation", "NOT_ESTABLISHED"),
        ("merge_authority", "NOT_GRANTED"),
    ):
        if xsv2.get(key) != expected:
            return False
    if xsv2.get("pull_request") != "BOOTSTRAP_PENDING" and not isinstance(xsv2.get("pull_request"), int):
        return False
    if xsv2.get("retained_numerical_execution") != {
        "taichi_cuda_runs": 0, "openfoam_runs": 0, "geometry_generations": 0
    }:
        return False

    for path, markers in CURRENT_MARKERS.items():
        text = texts[path]
        if any(marker not in text for marker in markers):
            return False
        if path.endswith("PROGRAM_STATE_AND_FORWARD_PLAN.md"):
            try:
                current = current_program_text(text)
            except AssertionError:
                return False
        else:
            current = text
        if any(marker in current for marker in FORBIDDEN_CURRENT_MARKERS):
            return False
    return True


class CurrentAuthorityConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.texts = {
            path: (ROOT / path).read_text(encoding="utf-8")
            for path in CURRENT_MARKERS
        }
        cls.qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text(encoding="utf-8"))

    def test_designated_current_authorities_agree(self) -> None:
        self.assertTrue(current_authorities_pass(self.texts, self.qa))

    def test_each_required_semantic_fails_closed_when_removed(self) -> None:
        for path, markers in CURRENT_MARKERS.items():
            for marker in markers:
                with self.subTest(path=path, marker=marker):
                    changed = dict(self.texts)
                    changed[path] = changed[path].replace(marker, "REMOVED_CURRENT_AUTHORITY")
                    self.assertFalse(current_authorities_pass(changed, self.qa))

    def test_machine_authority_fails_closed_on_stale_state(self) -> None:
        for key, stale in (
            ("active_validation_case", "VAL_CORPUS_002_PENDING_REVIEW"),
            ("active_data_planning_task", "VAL_DATA_001"),
            ("active_solver_task", "WP03_002_PENDING_REVIEW"),
            ("current_scientific_gate", "VAL_CORPUS_002_EXECUTION"),
        ):
            with self.subTest(key=key):
                changed = dict(self.qa)
                changed[key] = stale
                self.assertFalse(current_authorities_pass(self.texts, changed))

        checks = self.qa["current_repository_checks"]
        for python_count, focused_count in (
            (0, checks["current_authority_consistency_test_count"]),
            (checks["python_test_count"], 0),
            (1, 2),
            (True, 1),
            (1, True),
        ):
            with self.subTest(python_count=python_count, focused_count=focused_count):
                changed = dict(self.qa)
                changed["current_repository_checks"] = {
                    **checks,
                    "python_test_count": python_count,
                    "current_authority_consistency_test_count": focused_count,
                }
                self.assertFalse(current_authorities_pass(self.texts, changed))

        changed = dict(self.qa)
        changed["release_qualification"] = "FAIL"
        self.assertFalse(current_authorities_pass(self.texts, changed))
        for stale_xsv in (
            {"status": "G0_PROTOCOL_FREEZE_PENDING_EXACT_HEAD_CI"},
            {"retained_numerical_execution": "NONE"},
            {"corrected_result_sha256": ""},
            {"current_scientific_gate": "XSV_TAICHI_001_EXECUTION"},
            {"scientific_disposition": "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES"},
            {"package_disposition": "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED"},
            {"overall_compatibility_disposition": "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED"},
            {"overall_scientific_disposition": "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES"},
        ):
            changed = dict(self.qa)
            changed["xsv_taichi_001"] = {**self.qa["xsv_taichi_001"], **stale_xsv}
            self.assertFalse(current_authorities_pass(self.texts, changed))

    def test_executed_protocol_sections_remain_explicitly_historical(self) -> None:
        text = self.texts["docs/PROGRAM_STATE_AND_FORWARD_PLAN.md"]
        sections = historical_program_sections(text)
        self.assertEqual(len(sections), 4)
        for heading, section in zip(HISTORICAL_SECTION_HEADINGS, sections):
            with self.subTest(heading=heading):
                self.assertTrue(section.startswith(heading))
                self.assertIn("NOT_CURRENT_AUTHORITY", section)
        current = current_program_text(text)
        self.assertNotIn("Merge is not authorized.", current)

    def test_stale_aggregate_transfer_row_fails_closed(self) -> None:
        path = "docs/PROGRAM_STATE_AND_FORWARD_PLAN.md"
        corrected = CURRENT_MARKERS[path][0]
        stale = "| Aggregate extraction transfer | Not yet adequately assessed | Required next corpus tranche |"
        changed = dict(self.texts)
        changed[path] = changed[path].replace(corrected, stale)
        self.assertFalse(current_authorities_pass(changed, self.qa))

    def test_section_12_historical_boundary_mutations_fail_closed(self) -> None:
        path = "docs/PROGRAM_STATE_AND_FORWARD_PLAN.md"
        text = self.texts[path]
        heading = HISTORICAL_SECTION_HEADINGS[1]
        for mutated in (
            text.replace(heading, "# 12. Risks and controls", 1),
            text.replace(
                "`NOT_CURRENT_AUTHORITY`. This table records controls used by the completed",
                "This table records controls used by the completed",
                1,
            ),
        ):
            with self.subTest(mutation=mutated == text):
                changed = dict(self.texts)
                changed[path] = mutated
                self.assertFalse(current_authorities_pass(changed, self.qa))


if __name__ == "__main__":
    unittest.main()
