"""Materialize the external review bundle from committed reduced products."""
import hashlib, json, os, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
E=Path(os.environ.get('XSV_WASZKIEWICZ_EVIDENCE','review-evidence/xsv-waszkiewicz-dynamic-hyd-001'))
for sub in ['folds','fits','predictions','blocked_time','invalid_states','processing','bootstrap','data_profiles','authority','logs','tests','review','figures']:(E/sub).mkdir(parents=True,exist_ok=True)
s=json.load((DOC/'summary.json').open())
sections={
'00_CORRECTION_RESULT.md':f"# C1 correction result\n\n`{s['disposition']}`. `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY`.\n",
'01_CORRECTION_AUTHORITY.md':'# Correction authority\n\nOwner C1 authorization accepted independent review R1. Original candidate 56580bb / c73996f remains in Git history; original freeze/fold hashes are unchanged.\n',
'02_CONDITION_HETEROGENEITY.md':'# Condition heterogeneity\n\nW-H1, W-H2, and W-H3 each improve 6/11 conditions; exact two-sided sign probability 1.0. W-H2 is materially influenced by 1 bar.\n',
'03_BLOCKED_TIME_CORRECTION.md':'# Blocked-time correction\n\nThe original held-prefix-fitted/state-reset result is superseded. Corrected fitting excludes the evaluated brew, continues modeled state from 15 s across 60 s, and leaves W-H0A best.\n',
'04_INVALID_STATE_CORRECTION.md':'# Invalid-state correction\n\nTyped roots fail closed; coverage and failures are explicit. Primary LOCO contains zero invalid roots. Frozen conservative 2x penalty sensitivity is published.\n',
'05_PROCESSING_ROBUSTNESS_CORRECTION.md':'# Processing robustness correction\n\nW-H2 ranks first and adoption fails in every tested window. Effect magnitude varies; broader processing robustness is not established.\n',
'06_SCOPE_AND_CLAIM_CORRECTION.md':'# Scope and claim correction\n\nOnly the frozen bounded forms are rejected for adoption. This does not establish constant resistance or exclude other evolving laws.\n',
'07_PROGRAMME_AND_SUCCESSOR.md':'# Programme and successor\n\n`EWP-POROSITY-PERMEABILITY-PRIOR-001` is ready after C1 merge; source-conditioned Wadsworth and Vaca Guerra lanes remain separate. Home lab is deferred.\n'}
for n,t in sections.items():(E/n).write_text(t)
shutil.copy2(DOC/'summary.json',E/'summary.json')
for name,sub in [('FOLD_MANIFEST.json','folds'),('MODEL_COMPARISON_RESULTS.csv','fits'),('LEAVE_ONE_BREW_OUT_RESULTS.csv','predictions'),('LEAVE_ONE_CONDITION_OUT_RESULTS.csv','predictions'),('CONDITION_DIFFERENCES.csv','predictions'),('CONDITION_INFLUENCE.csv','predictions'),('BLOCKED_TIME_RESULTS.csv','blocked_time'),('BLOCKED_TIME_STATE_AUDIT.csv','blocked_time'),('INVALID_STATE_AUDIT.csv','invalid_states'),('INVALID_STATE_SENSITIVITY.csv','invalid_states'),('MASS_SIGNAL_AUDIT.csv','processing'),('MONOTONE_MASS_SENSITIVITY.csv','processing'),('TRAINING_ROW_RETENTION.csv','processing'),('PROCESSING_SENSITIVITY.csv','processing'),('PROCESSING_ROBUSTNESS.json','processing'),('UNCERTAINTY_RESULTS.csv','bootstrap'),('DATA_PROFILE.json','data_profiles'),('DATA_AUTHORITY.json','authority'),('C1_REVIEW_MANDATED_METHODS_ADDENDUM.json','authority')]: shutil.copy2(DOC/name,E/sub/name)
lines=[]
for p in sorted(x for x in E.rglob('*') if x.is_file() and x.name!='checksums.sha256'):
    lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(E)}")
(E/'checksums.sha256').write_text('\n'.join(lines)+'\n')
