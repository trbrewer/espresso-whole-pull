#!/usr/bin/env python3
"""Pinned research consumer; explicit family and constant nominal recipe required.

Loads the wrapper AND reused kernel in a private empty-path module namespace.
Never imports an installed Puckworks package or changes production dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_002/HANDOFF.json'
RUNTIME = ('puckworks/analysis/mass_delivery.py', 'puckworks/analysis/conditioned_mass_delivery.py')
FAMILIES = ('M0', 'MT', 'MF', 'MTF', 'SETTING_AWARE_EMPIRICAL')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, expression):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', expression], text=True).strip()


def load_producer(producer, family, handoff_path=DEFAULT_HANDOFF):
    if family not in FAMILIES:
        raise ValueError('explicit declared model family required')
    producer = Path(producer).resolve()
    pin = json.loads(Path(handoff_path).read_text())
    if git(producer, 'HEAD') != pin['producer_commit'] or git(producer, 'HEAD^{tree}') != pin['producer_tree']:
        raise ValueError('producer revision/tree mismatch')
    if tuple(pin['runtime_modules']) != RUNTIME or set(pin['models']) != set(FAMILIES):
        raise ValueError('complete runtime/model matrix required')
    required = set(RUNTIME) | {v['path'] for v in pin['models'].values()}
    if not required <= set(pin['producer_files']):
        raise ValueError('unbound runtime dependency or model')
    for relative, expected in pin['producer_files'].items():
        path = (producer/relative).resolve()
        if not path.is_relative_to(producer) or not path.is_file() or sha(path) != expected:
            raise ValueError('producer file hash/path mismatch')
    # A namespace with no search path cannot fall back to installed packages.
    namespace = '_ewp_conditioned_mass_delivery_'+pin['producer_commit']
    for name in list(sys.modules):
        if name == namespace or name.startswith(namespace+'.'):
            del sys.modules[name]
    package = types.ModuleType(namespace)
    package.__path__ = []
    sys.modules[namespace] = package
    loaded = []
    for relative in RUNTIME:
        name = namespace+'.'+Path(relative).stem
        spec = importlib.util.spec_from_file_location(name, producer/relative)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        setattr(package, Path(relative).stem, module)
        loaded.append(module)
    kernel, wrapper = loaded
    if wrapper.kernel is not kernel or Path(wrapper.kernel.__file__).resolve() != (producer/RUNTIME[0]).resolve():
        raise ValueError('reused kernel did not resolve to pinned producer')
    expected = pin['models'][family]
    model = wrapper.Model.load(producer/expected['path'])
    if (model.family != family or model.model_id != expected['model_id']
            or model.version != pin['schema_version'] or model.units != pin['units']
            or list(model.domain_kg) != pin['domain_kg']
            or model.feature_definitions != pin['feature_definitions']
            or model.setting_hull != pin['setting_hull']
            or model.source_code_semantics != pin['source_code_semantics']):
        raise ValueError('model identity/contract mismatch')
    required_claims = {'RESEARCH_ONLY', 'SOURCE_INTERNAL', 'TARGET_EXPOSED',
                       'PHYSICAL_VALIDATION_NOT_ESTABLISHED', 'RETROSPECTIVE_MODEL_DEVELOPMENT_COMPARISON'}
    if not required_claims <= set(model.claims):
        raise ValueError('claim limits missing')
    return model, pin


def demonstrate(producer, family, temperature_K, source_flow_setting_code, stop_kg=.04,
                handoff_path=DEFAULT_HANDOFF):
    model, pin = load_producer(producer, family, handoff_path)
    recipe = {'temperature_K': temperature_K, 'source_flow_setting_code': source_flow_setting_code}
    delivery = model.predict([0., .01, .02], [.01, .02, .03], **recipe)
    return {'model_id': model.model_id, 'family': family,
        'producer_commit': pin['producer_commit'], 'producer_tree': pin['producer_tree'],
        'model_sha256': pin['producer_files'][pin['models'][family]['path']],
        'actual_coefficients': model.coefficients, 'nominal_recipe': recipe,
        'query_class': 'SYNTHETIC_REQUESTED_MASS_INTERVALS',
        'interval_solute_kg': delivery.solute_kg.tolist(), 'average_TDS_percent': delivery.tds_percent.tolist(),
        'conditional_stop_mass_kg': stop_kg,
        'modeled_solute_to_stop_kg': float(model.cumulative_solute(stop_kg, **recipe)),
        'domain_kg': list(model.domain_kg), 'setting_hull': model.setting_hull,
        'claims': list(model.claims), 'rights': model.rights, 'native_ewp_runs': 0,
        'interpretation': 'Conditional research output; inspect scientific failures in RESULT.md. No automatic model selection or production use.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument('--model', choices=FAMILIES, required=True)
    parser.add_argument('--temperature-K', type=float, required=True)
    parser.add_argument('--source-flow-setting-code', type=float, required=True)
    parser.add_argument('--stop-kg', type=float, default=.04)
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.producer, args.model, args.temperature_K,
        args.source_flow_setting_code, args.stop_kg, args.handoff), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
