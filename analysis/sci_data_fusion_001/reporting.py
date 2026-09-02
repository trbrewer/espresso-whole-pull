def render_result(decision,authority,uncertainties):
    lines=["# SCI-DATA-FUSION-001 result","",f"## Exact scientific disposition","",f"`{decision['disposition']}`","","## Direct answer","","The deterministic component results below answer the bounded cross-corpus question without pooling source rows or claiming physical validation.",""]
    for component in decision["component_results"]:
        lines += [f"### {component['quantity_id']}","",f"- Component result: `{component['component_result']}`",f"- Candidates / eligible lineages: {component['candidate_count']} / {component['eligible_lineage_count']}",f"- Pairwise semantic result: {len(component.get('compatibility_findings',[]))} frozen comparisons",f"- Common support or conflict: {component.get('common_support') or component.get('conflicts') or 'none'}",f"- Baseline status: `{component['baseline_status']}`",f"- Narrowing status: `{component.get('narrowing_status','NOT_EVALUATED')}`",f"- Blockers: {len(component.get('blockers',[]))}",f"- Propagation status: `NOT_EXECUTED_UNLESS_FROZEN_GATE_PASSES`",""]
    lines += ["## Uncertainty","",f"Typed eligible uncertainty records: {len(uncertainties)}. Numerical pooling is prohibited.","","## Authority and nonclaims","",f"EWP base: `{authority['frozen_ewp_base']['commit']}` / `{authority['frozen_ewp_base']['tree']}`. Puckworks: `{authority['puckworks']['commit']}` / `{authority['puckworks']['tree']}`.","","This result does not claim whole-model or physical validation, universal transfer, a universal prior, improved predictive accuracy, production readiness, or production adoption.","","## Next action","",f"The frozen closeout mapping selects the consequence for `{decision['disposition']}`; it does not authorize adoption, OpenFOAM, or laboratory work.",""]
    return "\n".join(lines)

def render_reproduction(authority):
    return f"""# Reproduction

Run only after an independent audit record passes the exact-head, exact-tree, and freeze-content-manifest checks:

```sh
python3 -m analysis.sci_data_fusion_001.run execute --root . --puckworks-root \"$EWP_SCI_DATA_FUSION_001_PUCKWORKS_ROOT\" --output docs/analysis/sci_data_fusion_001 --audit-record /path/to/audit.json
```

Required EWP base: `{authority['frozen_ewp_base']['commit']}` / `{authority['frozen_ewp_base']['tree']}`.
Required Puckworks authority: `{authority['puckworks']['commit']}` / `{authority['puckworks']['tree']}`.

Verify with `verify-freeze`, run the focused and full Python lanes, and use `scripts/replay_sci_data_fusion_001_freeze.py` for deterministic immutable-package replay. Results are written under `docs/analysis/sci_data_fusion_001/`. OpenFOAM and laboratory work are neither required nor authorized.
"""
