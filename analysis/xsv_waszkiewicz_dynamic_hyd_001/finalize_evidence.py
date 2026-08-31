"""Materialize the external review bundle from committed reduced products."""
import hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
E=Path('/home/tim/Documents/review-evidence/xsv-waszkiewicz-dynamic-hyd-001-20260831')
s=json.load((DOC/'summary.json').open())
sections={
'00_EXECUTIVE_RESULT.md':f"# Executive result\n\n`{s['disposition']}`. Fixed resistance is retained because no evolving candidate passed all grouped gates.\n",
'01_AUTHORITY_AND_ENVIRONMENT.md':'# Authority and environment\n\nExact EWP base 992eb00c297a6146b92b632c761ecfa5c6d1e9cd and Puckworks producer a3428a4d4ad571ef3168a70e8a04620fca5d3520. All seven source hashes passed.\n',
'02_DATA_AND_SIGNAL_QUALIFICATION.md':'# Data and signal qualification\n\n56 physical brews, 11 conditions, 57 representations, 57,000 rows. Alias `12-8-6_alt` excluded. Line pressure and scale mass are the direct lanes; basket pressure and SG flow are derived.\n',
'03_METHODS_AND_MODEL_FREEZE.md':'# Methods and model freeze\n\nSee repository METHODS_FREEZE.json and FOLD_MANIFEST.json. Time rows are not replicates.\n',
'04_SOURCE_MODEL_PARITY.md':'# Source model parity\n\nStatic gate PASS (Pc 12.392 bar, Qc 1.897 g/s). Dynamic 9-bar gate PASS (1.6% long-run error, correlation 0.982 after 15 s). Post-fit reconstruction privilege only.\n',
'05_GROUPED_MODEL_RESULTS.md':'# Grouped model results\n\nW-H2 mean LOCO improvement was 27.0%, interval crossed zero, condition signs 6-5, and blocked-time error worsened. Strong gate failed.\n',
'06_PROCESSING_SENSITIVITY.md':'# Processing sensitivity\n\nStart/end-window ranking was materially conditional. Source flow differentiation remains diagnostic, not the primary target.\n',
'07_UNCERTAINTY_AND_ROBUSTNESS.md':'# Uncertainty and robustness\n\n2,000 paired replicates sampled conditions first, then complete physical-brew metrics. No time-row resampling.\n',
'08_RESIDUAL_AND_PARAMETER_FINDINGS.md':'# Residual and parameter findings\n\nParameter estimates were finite with complete coverage. Residual patterns do not prove compaction, channeling, fines migration, fracture, or intrinsic permeability.\n',
'09_NEXT_TASK_DECISION.md':'# Next task decision\n\n`EWP-POROSITY-PERMEABILITY-PRIOR-001`; fallbacks `EWP-REAL-WORLD-BOUNDARIES-001` and `OBS-PANNUSCH-FRACTION-WINDOW-001`.\n'}
for n,t in sections.items():(E/n).write_text(t)
shutil.copy2(DOC/'summary.json',E/'summary.json')
for name,sub in [('FOLD_MANIFEST.json','folds'),('MODEL_COMPARISON_RESULTS.csv','fits'),('LEAVE_ONE_BREW_OUT_RESULTS.csv','predictions'),('LEAVE_ONE_CONDITION_OUT_RESULTS.csv','predictions'),('BLOCKED_TIME_RESULTS.csv','predictions'),('PROCESSING_SENSITIVITY.csv','sensitivity'),('UNCERTAINTY_RESULTS.csv','bootstrap'),('DATA_PROFILE.json','data_profiles'),('DATA_AUTHORITY.json','authority')]: shutil.copy2(DOC/name,E/sub/name)
lines=[]
for p in sorted(x for x in E.rglob('*') if x.is_file() and x.name!='checksums.sha256'):
    lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(E)}")
(E/'checksums.sha256').write_text('\n'.join(lines)+'\n')
