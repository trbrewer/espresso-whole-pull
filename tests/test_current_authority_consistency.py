from __future__ import annotations

import json
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
)


def current_program_text(text: str) -> str:
    """Exclude only the explicitly bounded executed-history sections 11-14."""
    before, separator, remainder = text.partition(
        "# 11. WP03-002 detailed execution plan — `HISTORICAL_EXECUTED_AND_CONSUMED`"
    )
    if not separator:
        raise AssertionError("program handoff lacks the historical section-11 boundary")
    _, resume, after = remainder.partition("# 15. New-conversation bootstrap")
    if not resume:
        raise AssertionError("program handoff lacks the current section-15 boundary")
    self_check = remainder[: len(remainder) - len(after)]
    if "NOT_CURRENT_AUTHORITY" not in self_check:
        raise AssertionError("executed protocol is not explicitly non-current")
    return before + "# 15. New-conversation bootstrap" + after


def current_authorities_pass(texts: dict[str, str], qa: dict) -> bool:
    if qa.get("current_governance_milestone") != "VAL_CORPUS_002_COMPLETE_APPROVED_AND_MERGED":
        return False
    if qa.get("canonical_identity_role") != "LAST_SUBSTANTIVE_SCIENTIFIC_MERGE_BASE":
        return False
    if qa.get("live_repository_identity") != "RESOLVE_HEAD_AND_TREE_FROM_GIT":
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

    for path, markers in CURRENT_MARKERS.items():
        text = texts[path]
        if any(marker not in text for marker in markers):
            return False
        current = current_program_text(text) if path.endswith("PROGRAM_STATE_AND_FORWARD_PLAN.md") else text
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

    def test_executed_protocol_sections_remain_explicitly_historical(self) -> None:
        text = self.texts["docs/PROGRAM_STATE_AND_FORWARD_PLAN.md"]
        self.assertIn("HISTORICAL_EXECUTED_AND_CONSUMED", text)
        self.assertIn("NOT_CURRENT_AUTHORITY", text)
        current = current_program_text(text)
        self.assertNotIn("Merge is not authorized.", current)


if __name__ == "__main__":
    unittest.main()
