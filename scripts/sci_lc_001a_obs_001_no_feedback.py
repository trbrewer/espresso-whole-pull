#!/usr/bin/env python3
"""Independent AST check that OBS-001 values cannot feed scientific control."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/"scripts/sci_lc_001a_executor.py",ROOT/"scripts/sci_lc_001a_protocol.py"]
def main():
 checks={"no_rng":True,"no_monkey_patch":True,"observer_return_unassigned":True,
         "classifier_does_not_read_diagnostics":True,"key_identity_ignores_diagnostics":True,
         "scientific_state_not_assigned_from_diagnostics":True}
 for path in FILES:
  source=path.read_text(); tree=ast.parse(source)
  checks["no_rng"] &= not any(token in source for token in ("random.","numpy.random","np.random"))
  checks["no_monkey_patch"] &= "setattr(" not in source and "__dict__" not in source
  for node in ast.walk(tree):
   if isinstance(node,(ast.Assign,ast.AnnAssign,ast.NamedExpr)) and "diagnostic_observer(" in ast.unparse(node):
    checks["observer_return_unassigned"]=False
   if isinstance(node,ast.FunctionDef) and "classif" in node.name:
    diagnostic_identifiers=[]
    for child in ast.walk(node):
     if isinstance(child,ast.Name) and "diagnostic" in child.id.lower(): diagnostic_identifiers.append(child.id)
     if isinstance(child,ast.Attribute) and "diagnostic" in child.attr.lower(): diagnostic_identifiers.append(child.attr)
    checks["classifier_does_not_read_diagnostics"] &= not diagnostic_identifiers
   if isinstance(node,ast.FunctionDef) and node.name in ("build_plan","record_identity"):
    checks["key_identity_ignores_diagnostics"] &= "sidecar_root" not in ast.unparse(node)
 result={"schema":"ewp.sci_lc_001a.obs_001.no_feedback.v1","checks":checks,
         "passed":sum(checks.values()),"failed":sum(not x for x in checks.values())}
 result["result"]="OBS_001_DIAGNOSTIC_NO_FEEDBACK_STATIC_ANALYSIS_PASS" if not result["failed"] else "FAIL"
 print(json.dumps(result,indent=2,sort_keys=True)); return 0 if not result["failed"] else 1
if __name__=="__main__": raise SystemExit(main())
