#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RESULTS=${1:-"$ROOT/docs/analysis/sci_md_011/CLOSURE_ORACLE_RESULTS.csv"}
RECEIPT=${2:-"$ROOT/docs/analysis/sci_md_011/CLOSURE_ORACLE_RECEIPT.json"}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
(cd "$ROOT/tests/fixtures/sci_md_011_closure_oracle" && wmake)
"$(command -v sciMd011ClosureOracle)" >"$TMP/production.csv"
PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT" "$TMP/production.csv" "$RESULTS" "$RECEIPT" <<'PY'
import csv,hashlib,json,math,sys
from pathlib import Path
root,source,out,receipt=map(Path,sys.argv[1:]);sys.path.insert(0,str(root/'scripts'))
import sci_md_011_core as c
rows=[];max_abs=max_rel=0.0
with source.open() as f:
 for raw in csv.reader(f):
  phi,x,prod_phi,prod_f0=map(float,raw);py_phi=c.fphi(x,phi);py_f0=c.f0(x)
  ae_phi=abs(prod_phi-py_phi);ae_f0=abs(prod_f0-py_f0);re_phi=ae_phi/max(abs(prod_phi),abs(py_phi),1.0);re_f0=ae_f0/max(abs(prod_f0),abs(py_f0),1.0);max_abs=max(max_abs,ae_phi,ae_f0);max_rel=max(max_rel,re_phi,re_f0)
  rows.append({'phi':repr(phi),'x':repr(x),'production_fphi':repr(prod_phi),'python_fphi':repr(py_phi),'fphi_absolute_error':repr(ae_phi),'fphi_relative_error':repr(re_phi),'production_f0':repr(prod_f0),'python_f0':repr(py_f0),'f0_absolute_error':repr(ae_f0),'f0_relative_error':repr(re_f0)})
fields=list(rows[0]);out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tol=1e-12
data={'task_id':'SCI-MD-011','production_source_path':'solver/espressoWholePullFoam/poroelasticCompaction.H','production_source_sha256':sha(root/'solver/espressoWholePullFoam/poroelasticCompaction.H'),'oracle_source_sha256':sha(root/'tests/fixtures/sci_md_011_closure_oracle/sci_md_011_closure_oracle.C'),'runner_sha256':sha(root/'scripts/run_sci_md_011_closure_oracle.sh'),'tested_phi_values':sorted({float(r['phi']) for r in rows}),'tested_x_values':sorted({float(r['x']) for r in rows}),'row_count':len(rows),'maximum_absolute_error':max_abs,'maximum_relative_error':max_rel,'absolute_tolerance':tol,'relative_tolerance':tol,'results_sha256':sha(out),'pass':max_abs<=tol and max_rel<=tol}
receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
if not data['pass']:raise SystemExit('oracle parity failure')
print(json.dumps(data,sort_keys=True))
PY
