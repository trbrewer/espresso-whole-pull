from __future__ import annotations
import argparse, csv, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'validation/contracts/SCI_MD_004_STAGE_A_MULTISPECIES.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(path,*args): return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
def load_contract(): return json.loads(CONTRACT.read_text())
def consume(puckworks:Path):
 c=load_contract(); pin=c['scientific_data_pin']
 if git(puckworks,'rev-parse','HEAD')!=pin['commit']: raise ValueError('PUCKWORKS_COMMIT_MISMATCH')
 if git(puckworks,'rev-parse','HEAD^{tree}')!=pin['tree']: raise ValueError('PUCKWORKS_TREE_MISMATCH')
 base=puckworks/'docs/analysis/sci_md_004'
 for name,h in pin['artifact_hashes'].items():
  if sha(base/name)!=h: raise ValueError('ARTIFACT_HASH_MISMATCH:'+name)
 source=json.loads((base/'data_contract.json').read_text())
 if source['holdout_status']!='PROTECTED_EXTERNAL_NO_RETUNING_ENDPOINT_HOLDOUT' or not source['preexisting_exposure']: raise ValueError('HOLDOUT_CLASSIFICATION')
 with (base/'angeloni_conditions.csv').open(newline='') as f: inputs=list(csv.DictReader(f))
 with (base/'angeloni_targets_long.csv').open(newline='') as f: targets=list(csv.DictReader(f))
 if len(inputs)!=66 or not targets or any(x['protected_target']!='True' for x in targets): raise ValueError('SCHEMA_OR_PROTECTION')
 forbidden={'prediction','residual','score'}
 if forbidden & set().union(*(set(x) for x in inputs)): raise ValueError('INPUT_TARGET_LEAKAGE')
 return {'disposition':c['data_sufficiency']['disposition'],'predictions_generated':0,'scores_generated':0,'verified_target_rows':len(targets)}
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['verify']);p.add_argument('--puckworks',type=Path,required=True);a=p.parse_args()
 print(json.dumps(consume(a.puckworks),sort_keys=True))
