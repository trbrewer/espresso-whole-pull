#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate():
    authority = json.loads((ROOT / "provenance/LOCAL_DATA_CORPUS_AUTHORITY.json").read_text())
    with (ROOT / "docs/analysis/data_leverage/SOURCE_FAMILY_COVERAGE.csv").open(newline="") as handle:
        coverage = list(csv.DictReader(handle))
    visualizer = json.loads((ROOT / "docs/analysis/data_leverage/VISUALIZER_LOCAL_CORPUS_STATUS.json").read_text())
    brief = json.loads((ROOT / "docs/analysis/espresso_corpus_leverage_002/WASZKIEWICZ_DYNAMIC_HYD_TASK_BRIEF.json").read_text())
    assert len(coverage) == 39 and len({r["family_id"] for r in coverage}) == 39
    assert all(r["registered"] == "true" and r["primary_opportunity_or_exclusion"] for r in coverage)
    assert authority["material_families"] == authority["mapped_or_registered_families"] == 39
    assert authority["unregistered_material_families"] == 0
    assert visualizer["unique_records"] == 23169 and not visualizer["usable_population_chemistry"]
    assert visualizer["plausible_nonzero_tds_before_joint_checks"] == 8
    assert visualizer["plausible_nonzero_ey_before_joint_checks"] == 9
    assert "NOT_PREDICTIVELY_QUALIFIED" in visualizer["hydraulic_result"]
    assert not visualizer["raw_redistribution_permitted"] and not visualizer["private_data_permitted"]
    assert brief["authority"]["physical_brews"] == 56 and brief["authority"]["controlled_conditions"] == 11
    assert brief["authority"]["independent_unit"] == "physical_brew" and not brief["execution_in_c1"]
    assert all(len(authority[key]) == 64 for key in ("manifest_sha256", "available_data_register_sha256", "local_corpus_family_index_sha256", "visualizer_permission_status_sha256", "telisromero_authority_sha256"))
    return authority


if __name__ == "__main__":
    validate()
    print("local data corpus authority: PASS")
