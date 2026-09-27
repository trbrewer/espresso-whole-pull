#!/usr/bin/env python3
"""Thin isolated consumer of the exact task-006 Puckworks research runtime."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_006/HANDOFF.json'
RUNTIME = 'puckworks/analysis/conditional_tail_delivery.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, expression):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', expression], text=True).strip()


def load_producer(producer, arm='C2', handoff_path=HANDOFF):
    producer = Path(producer).resolve()
    pin = json.loads(Path(handoff_path).read_text())
    if arm not in ('C0','C1','C2'):
        raise ValueError('DECLARED_ARM_REQUIRED')
    if git(producer,'HEAD') != pin['producer_commit'] or git(producer,'HEAD^{tree}') != pin['producer_tree']:
        raise ValueError('EXACT_EVALUATED_PRODUCER_REQUIRED')
    if pin['runtime_modules'] != [RUNTIME] or set(pin['models']) != {'C0','C1','C2'}:
        raise ValueError('COMPLETE_RUNTIME_AND_MODEL_MATRIX_REQUIRED')
    required = {RUNTIME} | {m['path'] for m in pin['models'].values()}
    if set(pin['producer_files']) != required:
        raise ValueError('EXACT_BOUND_FILE_SET_REQUIRED')
    for relative, expected in pin['producer_files'].items():
        path = (producer/relative).resolve()
        if not path.is_relative_to(producer) or not path.is_file() or sha(path) != expected:
            raise ValueError('PRODUCER_FILE_HASH_OR_PATH_MISMATCH')
    # Explicit single-module loading: no Puckworks package init or installed fallback.
    name = '_ewp_conditional_tail_'+pin['producer_commit']
    spec = importlib.util.spec_from_file_location(name, producer/RUNTIME)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if module.VERSION != pin['schema'] or module.UNITS != pin['units'] or list(module.CLAIMS) != pin['claims']:
        raise ValueError('RUNTIME_CONTRACT_MISMATCH')
    model = module.Model.load(producer/pin['models'][arm]['path'])
    if (model.arm != arm or model.sha256 != pin['models'][arm]['model_sha256']
            or model.domain_kg != pin['domain_kg'][1] or model.rights != pin['rights']):
        raise ValueError('MODEL_IDENTITY_DOMAIN_OR_RIGHTS_MISMATCH')
    return module, model, pin


def predict(producer, early_inputs, queries, *, arm='C2', stop_kg=None, handoff_path=HANDOFF):
    module, model, pin = load_producer(producer, arm, handoff_path)
    inputs = module.EarlyInput.from_dict(early_inputs)
    if not isinstance(queries,list) or any(not isinstance(q,dict) or set(q) != {'start_kg','end_kg'} for q in queries):
        raise ValueError('COORDINATE_ONLY_QUERY_REQUIRED')
    state = model.condition(inputs)
    result = state.predict_intervals([q['start_kg'] for q in queries], [q['end_kg'] for q in queries])
    return {'input_class':inputs.input_class,'producer_commit':pin['producer_commit'],
        'producer_tree':pin['producer_tree'],'model_sha256':model.sha256,'arm':arm,
        'state':state.to_dict(),'predictions':[asdict(p) for p in result],
        'remaining_solute':asdict(state.remaining_solute(stop_kg)) if stop_kg is not None else None,
        'claims':list(module.CLAIMS),'rights':model.rights,'native_ewp_runs':0,
        'production_dependency_lock_changed':False}


def demonstrate(producer, arm='C2', handoff_path=HANDOFF):
    module, _, _ = load_producer(producer,arm,handoff_path)
    inputs = module.EarlyInput(arm,(.004,.004,.15,.10)[:len(module.feature_names(arm))],'SYNTHETIC')
    return predict(producer,inputs.to_dict(),[{'start_kg':.008,'end_kg':.02},
        {'start_kg':.02,'end_kg':.04}],arm=arm,stop_kg=.04,handoff_path=handoff_path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer',required=True,type=Path)
    parser.add_argument('--handoff',type=Path,default=HANDOFF)
    parser.add_argument('--arm',choices=('C0','C1','C2'),default='C2')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--synthetic',action='store_true')
    mode.add_argument('--early-inputs',type=Path)
    parser.add_argument('--queries',type=Path)
    parser.add_argument('--stop-kg',type=float)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.synthetic:
        result=demonstrate(args.producer,args.arm,args.handoff)
    else:
        if not args.queries or not args.output:
            parser.error('--early-inputs requires --queries and a private --output')
        path=args.output.resolve()
        if any((p/'.git').exists() for p in (path,*path.parents)):
            parser.error('source-derived state and predictions must remain outside Git')
        module,_,_=load_producer(args.producer,args.arm,args.handoff)
        result=predict(args.producer,module.strict_json(args.early_inputs.read_text()),
            module.strict_json(args.queries.read_text()),arm=args.arm,stop_kg=args.stop_kg,handoff_path=args.handoff)
    if args.output:
        with args.output.open('x') as stream:
            json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
        print('Research result saved; delivery is conditional on supplied beverage mass.')
    else:
        print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
