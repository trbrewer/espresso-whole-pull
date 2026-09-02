#!/usr/bin/env python3
import csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMME = ROOT / "provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json"
LEDGER = ROOT / "docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv"

def validate():
    data = json.loads(PROGRAMME.read_text())
    try:
        import jsonschema
        schema = json.loads((ROOT / "schemas/existing_data_leverage_programme.schema.json").read_text())
        jsonschema.validate(data, schema)
    except ImportError:
        pass
    by_id = {item["opportunity_id"]: item for item in data["opportunities"]}
    assert len(by_id) == len(data["opportunities"])
    assert not data["laboratory_gate"]["operation_authorized"]
    assert data["current_priority"] in by_id
    selected = by_id[data["current_priority"]]
    selected_is_open = selected["status"] in {"READY", "ACTIVE"}
    selected_is_completed_owner_decision = (
        selected["status"].startswith("COMPLETE_")
        and data.get("last_completed_opportunity_review") == data["current_priority"]
        and not data["laboratory_gate"]["operation_authorized"]
        and data["laboratory_gate"]["separate_owner_authorization_required"]
        and data["home_lab_status"] == "DEFER_HOME_LAB_PENDING_SEPARATE_EXECUTION_AUTHORIZATION"
    )
    assert selected_is_open or selected_is_completed_owner_decision, (
        "current priority must be ready/active or the completed task awaiting a separate owner decision"
    )
    assert data["current_claim_ceiling"] == selected["claim_ceiling"]
    for item in by_id.values():
        if item["status"] in {"READY", "ACTIVE"}:
            assert item["data_families"] and item["scientific_question"]
        if item["status"].startswith("COMPLETE_"):
            assert item["completion_evidence"]
        if item["status"] == "EXHAUSTED_FOR_NAMED_DECISION" or item["exhausted_for_decision"]:
            assert item["exhaustion_decision"]
            assert item["completion_evidence"]
            assert item["notes"] != "source-internal only"
    with LEDGER.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames and all(None not in row for row in rows)
    assert rows and all(row["opportunity_id"] in by_id for row in rows)
    selected_rows = [row for row in rows if row["opportunity_id"] == data["current_priority"]]
    assert len(selected_rows) == 1
    assert selected_rows[0]["current_status"] == selected["status"]
    public = [PROGRAMME, LEDGER, ROOT / "docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md"]
    assert all("/home/" not in path.read_text() for path in public)
    state = (ROOT / "docs/PROJECT_STATE.md").read_text()
    assert "EXISTING_DATA_LEVERAGE_PROGRAMME" in state and "DATA_LEVERAGE_LEDGER" in state
    return data

if __name__ == "__main__":
    validate()
    print("existing-data-leverage programme: PASS")
