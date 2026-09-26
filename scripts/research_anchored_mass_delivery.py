#!/usr/bin/env python3
"""Thin exact-pinned research consumer of a single early-assay update.

All numerical implementation remains in the explicitly supplied producer. The
offline example uses SYNTHETIC_ANCHOR_INPUT, never a reproduced physical shot.
"""
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
DEFAULT_HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_003/HANDOFF.json'
RUNTIME = ('puckworks/analysis/mass_delivery.py',
           'puckworks/analysis/conditioned_mass_delivery.py',
           'puckworks/analysis/anchored_mass_delivery.py')
FAMILIES = ('MASS', 'EMPIRICAL', 'SETTING_EMPIRICAL')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, expression):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', expression], text=True).strip()


def load_producer(producer, family, handoff_path=DEFAULT_HANDOFF):
    if family not in FAMILIES:
        raise ValueError('EXPLICIT_FROZEN_BASE_REQUIRED')
    producer = Path(producer).resolve()
    pin = json.loads(Path(handoff_path).read_text())
    if git(producer, 'HEAD') != pin['producer_commit'] or git(producer, 'HEAD^{tree}') != pin['producer_tree']:
        raise ValueError('PRODUCER_REVISION_OR_TREE_MISMATCH')
    if tuple(pin['runtime_modules']) != RUNTIME or set(pin['models']) != set(FAMILIES):
        raise ValueError('COMPLETE_RUNTIME_AND_MODEL_MATRIX_REQUIRED')
    required = set(RUNTIME) | {m['path'] for m in pin['models'].values()}
    if not required <= set(pin['producer_files']):
        raise ValueError('UNBOUND_RUNTIME_DEPENDENCY_OR_MODEL')
    for relative, expected in pin['producer_files'].items():
        path = (producer/relative).resolve()
        if not path.is_relative_to(producer) or not path.is_file() or sha(path) != expected:
            raise ValueError('PRODUCER_FILE_HASH_OR_PATH_MISMATCH')
    # Reuse the established empty-path namespace loading pattern. Package
    # initializers and installed Puckworks modules cannot enter the runtime.
    namespace = '_ewp_anchored_mass_delivery_'+pin['producer_commit']
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
    kernel, conditioned, anchored = modules
    if conditioned.kernel is not kernel or anchored.kernel is not kernel or anchored.conditioned is not conditioned:
        raise ValueError('TRANSITIVE_RUNTIME_IDENTITY_MISMATCH')
    if anchored.VERSION != pin['state_schema'] or anchored.UNITS != pin['state_units']:
        raise ValueError('ANCHORED_STATE_CONTRACT_MISMATCH')
    if not set(pin['required_state_claims']) <= set(anchored.CLAIMS):
        raise ValueError('ANCHORED_CLAIM_LIMITS_MISSING')
    model = pin['models'][family]
    base = anchored.FrozenBase.load(producer/model['path'])
    data = anchored.strict_json(base.artifact_json)
    if (base.model_id != model['model_id'] or base.sha256 != pin['producer_files'][model['path']]
            or data['family'] != model['family'] or data['version'] != model['version']
            or data['units'] != model['units'] or data['domain_kg'] != pin['base_domain_kg']
            or data['rights'] != pin['source_rights']):
        raise ValueError('BASE_IDENTITY_UNITS_SUPPORT_OR_RIGHTS_MISMATCH')
    if not {'RESEARCH_ONLY', 'SOURCE_INTERNAL', 'TARGET_EXPOSED',
            'PHYSICAL_VALIDATION_NOT_ESTABLISHED'} <= set(data['claims']):
        raise ValueError('BASE_CLAIM_LIMITS_MISSING')
    if family == 'SETTING_EMPIRICAL' and any(data[k] != pin[k] for k in
            ('feature_definitions', 'setting_hull', 'source_code_semantics')):
        raise ValueError('NOMINAL_SETTING_SEMANTICS_MISMATCH')
    return anchored, base, pin


def demonstrate(producer, family='MASS', stop_kg=.04, handoff_path=DEFAULT_HANDOFF):
    module, base, pin = load_producer(producer, family, handoff_path)
    setting = module.NominalSetting(362.15, 2.) if family == 'SETTING_EMPIRICAL' else None
    state = module.anchor(base, module.synthetic_observation(), setting=setting)
    queries = (module.IntervalQuery(.004, .01), module.IntervalQuery(.01, .02))
    return {'input_class': 'SYNTHETIC_ANCHOR_INPUT', 'base_model_id': base.model_id,
        'base_sha256': base.sha256, 'producer_commit': pin['producer_commit'],
        'producer_tree': pin['producer_tree'], 'alpha': state.alpha,
        'predictions': [asdict(p) for p in state.predict_intervals(queries)],
        'conditional_remaining': asdict(state.remaining_solute(stop_kg)),
        'future_domain_kg': state.future_domain_kg, 'claims': state.claims,
        'base_rights': pin['source_rights'], 'native_ewp_runs': 0,
        'interpretation': 'Fitted base plus synthetic observation; not a reproduced physical shot.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument('--model', choices=FAMILIES, default='MASS')
    parser.add_argument('--stop-kg', type=float, default=.04)
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.producer, args.model, args.stop_kg, args.handoff),
                     indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
