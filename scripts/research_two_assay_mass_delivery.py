#!/usr/bin/env python3
"""Thin exact-pinned two-assay research consumer. No estimator implementation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_005/HANDOFF.json'
RUNTIME = tuple('puckworks/analysis/'+name+'.py' for name in (
    'mass_delivery', 'conditioned_mass_delivery', 'anchored_mass_delivery', 'two_assay_mass_delivery'))
ARMS = ('TWO_ASSAY_MASS', 'TWO_ASSAY_EXPONENTIAL', 'TWO_ASSAY_FIXED_MASS',
        'TWO_ASSAY_FIXED_EMPIRICAL', 'SECOND_ASSAY_EMPIRICAL', 'FIRST_ASSAY_EMPIRICAL')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, expression):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', expression], text=True).strip()


def load_producer(producer, arm='TWO_ASSAY_MASS', handoff_path=DEFAULT_HANDOFF):
    if arm not in ARMS:
        raise ValueError('EXPLICIT_PREDECLARED_ARM_REQUIRED')
    producer = Path(producer).resolve()
    pin = json.loads(Path(handoff_path).read_text())
    if git(producer, 'HEAD') != pin['producer_commit'] or git(producer, 'HEAD^{tree}') != pin['producer_tree']:
        raise ValueError('PRODUCER_REVISION_OR_TREE_MISMATCH')
    if tuple(pin['runtime_modules']) != RUNTIME or set(pin['models']) != {'MASS', 'EMPIRICAL'}:
        raise ValueError('COMPLETE_RUNTIME_AND_MODEL_MATRIX_REQUIRED')
    required = set(RUNTIME) | {m['path'] for m in pin['models'].values()}
    if not required <= set(pin['producer_files']):
        raise ValueError('UNBOUND_RUNTIME_DEPENDENCY_OR_MODEL')
    for relative, expected in pin['producer_files'].items():
        path = (producer/relative).resolve()
        if not path.is_relative_to(producer) or not path.is_file() or sha(path) != expected:
            raise ValueError('PRODUCER_FILE_HASH_OR_PATH_MISMATCH')
    # Explicit empty-path namespace: no package initializer or installed fallback.
    namespace = '_ewp_two_assay_delivery_'+pin['producer_commit']
    for name in list(sys.modules):
        if name == namespace or name.startswith(namespace+'.'):
            del sys.modules[name]
    package = types.ModuleType(namespace)
    package.__path__ = []
    sys.modules[namespace] = package
    modules = []
    for relative in RUNTIME:
        name = namespace+'.'+Path(relative).stem
        spec = importlib.util.spec_from_file_location(name, producer/relative)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        setattr(package, Path(relative).stem, module)
        modules.append(module)
    kernel, conditioned, legacy, md = modules
    if (conditioned.kernel is not kernel or legacy.kernel is not kernel
            or legacy.conditioned is not conditioned or md.kernel is not kernel or md.legacy is not legacy):
        raise ValueError('TRANSITIVE_RUNTIME_IDENTITY_MISMATCH')
    if md.VERSION != pin['state_schema'] or md.UNITS != pin['state_units'] or tuple(md.ARMS) != ARMS:
        raise ValueError('TWO_ASSAY_STATE_CONTRACT_MISMATCH')
    if not set(pin['required_state_claims']) <= set(md.CLAIMS):
        raise ValueError('REQUIRED_CLAIM_LIMITS_MISSING')
    family = 'MASS' if arm in ARMS[:3] else 'EMPIRICAL'
    model = pin['models'][family]
    base = md.FrozenBase.load(producer/model['path'])
    data = md.strict_json(base.artifact_json)
    if (base.model_id != model['model_id'] or base.sha256 != pin['producer_files'][model['path']]
            or data['family'] != model['family'] or data['version'] != model['version']
            or data['units'] != model['units'] or data['domain_kg'] != pin['base_domain_kg']
            or data['rights'] != pin['source_rights']):
        raise ValueError('BASE_IDENTITY_UNITS_SUPPORT_OR_RIGHTS_MISMATCH')
    return md, base, pin


def predict(producer, observations, queries, *, arm='TWO_ASSAY_MASS', stop_kg=None,
            handoff_path=DEFAULT_HANDOFF):
    md, base, pin = load_producer(producer, arm, handoff_path)
    pair = md.ObservationPair.from_dict(observations)
    if not isinstance(queries, list) or any(not isinstance(q, dict) or set(q) != {'start_kg', 'end_kg'} for q in queries):
        raise ValueError('COORDINATE_ONLY_INTERVAL_QUERIES_REQUIRED')
    state = md.FittedState(base, pair, arm)
    intervals = tuple(md.IntervalQuery(**q) for q in queries)
    return {'input_class': pair.first.input_class, 'producer_commit': pin['producer_commit'],
        'producer_tree': pin['producer_tree'], 'arm': arm, 'state': state.to_dict(),
        'predictions': [asdict(p) for p in state.predict_intervals(intervals)],
        'conditional_remaining': asdict(state.remaining_solute(stop_kg)) if stop_kg is not None else None,
        'claims': list(state.claims), 'base_rights': pin['source_rights'],
        'native_ewp_runs': 0, 'production_dependency_lock_changed': False}


def demonstrate(producer, arm='TWO_ASSAY_MASS', stop_kg=.04, handoff_path=DEFAULT_HANDOFF):
    md, _, _ = load_producer(producer, arm, handoff_path)
    return predict(producer, asdict(md.synthetic_pair()),
        [{'start_kg': .008, 'end_kg': .015}, {'start_kg': .015, 'end_kg': .03}],
        arm=arm, stop_kg=stop_kg, handoff_path=handoff_path)


def private_output(path, producer):
    path = Path(path).resolve()
    if path.is_relative_to(ROOT) or path.is_relative_to(Path(producer).resolve()) or any((p/'.git').exists() for p in path.parents):
        raise ValueError('REAL_STATES_AND_RESULTS_MUST_REMAIN_OUTSIDE_GIT')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument('--arm', choices=ARMS, default=ARMS[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--synthetic', action='store_true')
    mode.add_argument('--observations', type=Path, help='JSON object with first/second typed observations')
    parser.add_argument('--queries', type=Path, help='JSON list of start_kg/end_kg objects')
    parser.add_argument('--stop-kg', type=float)
    parser.add_argument('--output', type=Path, help='exclusive private JSON output; required for supplied observations')
    args = parser.parse_args()
    if args.synthetic:
        if args.queries:
            parser.error('--queries is used with --observations')
        result = demonstrate(args.producer, args.arm, args.stop_kg, args.handoff)
    else:
        if not args.queries or not args.output:
            parser.error('--observations requires --queries and private --output')
        private_output(args.output, args.producer)
        md, _, _ = load_producer(args.producer, args.arm, args.handoff)
        result = predict(args.producer, md.strict_json(args.observations.read_text()),
            md.strict_json(args.queries.read_text()), arm=args.arm, stop_kg=args.stop_kg, handoff_path=args.handoff)
    if args.output:
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
        print('Research result written to the supplied output; no whole-cup or physical-validation claim.')
    else:
        print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
