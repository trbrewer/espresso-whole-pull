#!/usr/bin/env python3
"""Syntax-aware OBS-001 no-physics verifier against the authorized base."""
from __future__ import annotations
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "18641c01ebd4d18636c092f616855eb2659c4a09"
R1_BASE = "7f345f75985f19e44660ee03de1d37065d6d8597"
IMMUTABLE = {
 "validation/cases/sci_lc_001a/SCI_LC_001A_PARAMETER_MATRIX.json":"d71b889732c7f1cbf023e2e814e29044675f744f7171bc39de309140a51b6680",
 "validation/cases/sci_lc_001a/SCI_LC_001A_PARAMETER_MATRIX.csv":"7d74460bee9f91fc7b5fe6f15a14924ca490a4d5f042a51d22c0b85020cd4efb",
 "validation/cases/sci_lc_001a/SCI_LC_001A_PROTOCOL.json":"4fd4d3cc6249401c9e2fb7961ecd74bb0d2f6572b48cc55bffa4be1039333461"}

class Normalize(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name == "_evolved_primitives_observed": return None
        node.args.kwonlyargs = [x for x in node.args.kwonlyargs if x.arg != "diagnostic_observer"]
        if len(node.args.kw_defaults) > len(node.args.kwonlyargs): node.args.kw_defaults = node.args.kw_defaults[:len(node.args.kwonlyargs)]
        return self.generic_visit(node)
    def visit_If(self, node):
        if "diagnostic_observer" in ast.unparse(node.test): return None
        return self.generic_visit(node)
    def visit_Expr(self, node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id in (
                "_emit_diagnostic","_emit_multiplier_diagnostic"):
            return None
        return self.generic_visit(node)
    def visit_Call(self, node):
        node = self.generic_visit(node)
        node.keywords = [x for x in node.keywords if x.arg != "diagnostic_observer"]
        if isinstance(node.func, ast.Name) and node.func.id == "_evolved_primitives_observed":
            node.func.id = "_evolved_primitives"; node.args = node.args[:-1]
        return node

def function(source, name):
    tree=Normalize().visit(ast.parse(source)); ast.fix_missing_locations(tree)
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return ast.dump(node,include_attributes=False)
    raise ValueError(name)

def main():
    checks={}
    for path, expected in IMMUTABLE.items():
        checks[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected
    targets={"scripts/sci_lc_001a_protocol.py":["evolved_resistance_primitives","multiplier_admissibility"],
             "scripts/sci_lc_001a_executor.py":["_evolved_primitives","_dynamic_rhs_core",
                                                "_execute_dynamic_case","_execute_canonical_case"]}
    for path,names in targets.items():
        base=subprocess.run(["git","show",f"{BASE}:{path}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout
        r1_base=subprocess.run(["git","show",f"{R1_BASE}:{path}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout
        candidate=(ROOT/path).read_text()
        for name in names:
            checks[f"normalized_ast:{path}:{name}"]=function(base,name)==function(candidate,name)
            checks[f"r1_delta_normalized_ast:{path}:{name}"]=function(r1_base,name)==function(candidate,name)
    checks.update({"formula_exp_beta_x": "math.exp(beta * value)" in (ROOT/"scripts/sci_lc_001a_protocol.py").read_text(),
      "bounds_0p25_4p0": all(x in (ROOT/"scripts/sci_lc_001a_protocol.py").read_text() for x in ("value < 0.25","value > 4.0")),
      "tolerances": all(x in (ROOT/"scripts/sci_lc_001a_protocol.py").read_text() for x in ("1.0e-12","1.0e-14","1.0e-10")),
      "no_clipping": "OUT_OF_RANGE_NO_CLIPPING" in (ROOT/"scripts/sci_lc_001a_protocol.py").read_text()})
    result={"schema":"ewp.sci_lc_001a.obs_001.no_physics.v1","checks":checks,"passed":sum(checks.values()),"failed":sum(not x for x in checks.values())}
    result["result"]=("OBS_001_NO_PHYSICS_CHANGE_STATIC_VERIFICATION_PASS" if not result["failed"] else "FAIL")
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if not result["failed"] else 1
if __name__=="__main__": raise SystemExit(main())
