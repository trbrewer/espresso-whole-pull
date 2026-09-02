from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .authority import AuthorityError, programme, sha256, verify_ewp, verify_puckworks

CONSUMED = (
    "docs/analysis/xsv_waszkiewicz_dynamic_hyd_001/summary.json",
    "docs/analysis/xsv_waszkiewicz_dynamic_hyd_001/RESULT.md",
    "docs/analysis/ewp_porosity_permeability_prior_001/SOURCE_SUPPORTS.json",
    "docs/analysis/ewp_porosity_permeability_prior_001/EWP_QUANTITY_DEFINITIONS.json",
    "docs/analysis/ewp_porosity_permeability_prior_001/DECISION.json",
    "docs/analysis/ewp_porosity_permeability_prior_001/POROSITY_MATERIALITY.json",
    "docs/analysis/ewp_real_world_boundaries_001/DECISION.json",
    "docs/analysis/ewp_real_world_boundaries_001/MEASUREMENT_MAPPING_LEDGER.csv",
    "docs/analysis/xsv_pannusch_multimodel_001/summary.json",
    "docs/analysis/obs_pannusch_fraction_window_001/summary.json",
    "docs/analysis/sci_md_pannusch_flow_history_001/summary.json",
    "docs/analysis/xsv_pannusch_ewp_input_mapping_001/MAPPING_DECISION.json",
    "docs/analysis/xsv_pannusch_ewp_input_mapping_001/MAPPING_MATRIX.csv",
)


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def prepare(root: Path, puckworks: Path, output: Path) -> None:
    ewp = verify_ewp(root)
    expected = ewp["programme"]["authorities"]
    puck = verify_puckworks(puckworks, expected)
    consumed = []
    for relative in CONSUMED:
        path = root / relative
        if not path.is_file():
            raise AuthorityError(f"missing consumed EWP result: {relative}")
        consumed.append({"path": relative, "sha256": sha256(path)})
    output.mkdir(parents=True, exist_ok=True)
    contract = json.loads((root / "analysis/sci_data_fusion_001/task_contract_template.json").read_text())
    freeze_inputs = json.loads((root / "analysis/sci_data_fusion_001/freeze_inputs.json").read_text())
    dump(output / "TASK_CONTRACT.json", contract)
    dump(output / "DATA_AVAILABILITY_PREFLIGHT.json", {
        "task_id": "SCI-DATA-FUSION-001", "status": "PASS",
        "scope": "registered metadata and already-qualified component artifacts",
        "full_puckworks_register_scan_required": True, "unavailable_is_not_absent": True,
        "external_contact": "PROHIBITED", "home_lab": "PROHIBITED"})
    dump(output / "AUTHORITY.json", {
        "task_id": "SCI-DATA-FUSION-001", "phase": "PRE_EXECUTION_FREEZE",
        "ewp_origin_main_head": ewp["head"], "ewp_origin_main_tree": ewp["tree"],
        "accepted_predecessor_commit": ewp["predecessor"], "puckworks": puck,
        "owner_authorization": "SCI-DATA-FUSION-001-OWNER-AUTHORIZE-BOUNDED-CROSS-CORPUS-COMPONENT-CONSTRAINT-QUALIFICATION-2026-09-02"})
    dump(output / "CONSUMED_RESULT_ARTIFACTS.json", {"artifacts": consumed})
    dump(output / "CANONICAL_QUANTITY_REGISTER.json", {"quantities": freeze_inputs["canonical_quantities"]})
    dump(output / "CANDIDATE_SUPPORT_FREEZE.json", {
        "support_candidates": freeze_inputs["support_candidates"],
        "predeclared_porosity_pair_gates": freeze_inputs["predeclared_porosity_pair_gates"],
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--puckworks-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", choices=("freeze", "execute"), default="freeze")
    parser.add_argument("--audit-record", type=Path)
    args = parser.parse_args()
    root, output = args.root.resolve(), (args.root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    if args.phase == "execute":
        if not args.audit_record or not args.audit_record.is_file():
            raise AuthorityError("Phase B requires an independent exact-freeze audit record")
        raise AuthorityError("Phase B remains unavailable until the accepted audit is bound to this implementation")
    prepare(root, args.puckworks_root.resolve(), output)


if __name__ == "__main__":
    main()
