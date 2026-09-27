#!/usr/bin/env python3
"""008 thin consumer of an exact source-calibration producer; no copied mathematics."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
import types
from pathlib import Path

import research_conditional_tail_delivery as parent

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_008/HANDOFF.json'
MODULES = ('conditional_tail_delivery', 'grudeva_clock', 'grudeva_pooled_tail_delivery',
           'source_calibrated_tail_delivery', 'grudeva_one_shot_calibration')
PREFIX = 'puckworks/analysis/'


def load_producer(producer, handoff_path=HANDOFF):
    root = Path(producer).resolve(); pin = json.loads(Path(handoff_path).read_text())
    if parent.git(root, 'HEAD') != pin['producer_commit'] or parent.git(root, 'HEAD^{tree}') != pin['producer_tree']:
        raise ValueError('EXACT_EVALUATED_008_PRODUCER_REQUIRED')
    required = {PREFIX+n+'.py' for n in MODULES} | {PREFIX+'grudeva_one_shot_scoring.py'}
    if set(pin['producer_files']) != required:
        raise ValueError('EXACT_RUNTIME_FILE_SET_REQUIRED')
    old = json.loads((ROOT/'docs/analysis/sci_md_mass_delivery_006/HANDOFF.json').read_text())
    pooled = json.loads((ROOT/'docs/analysis/sci_md_mass_delivery_007/HANDOFF.json').read_text())
    if (pin['parent_producer_commit'] != old['producer_commit'] or pin['parent_producer_tree'] != old['producer_tree']
            or pin['parent_model_identities'] != {a: v['model_sha256'] for a, v in old['models'].items()}
            or pin['source_sha256'] != pooled['source_sha256']):
        raise ValueError('ACCEPTED_PARENT_OR_SOURCE_IDENTITY_MISMATCH')
    for relative, expected in (pin['producer_files'] | pin['parent_artifact_byte_hashes']).items():
        path = (root/relative).resolve()
        if not path.is_relative_to(root) or parent.sha(path) != expected:
            raise ValueError('ACTUAL_SOURCE_BYTES_MISMATCH')
        committed = subprocess.check_output(['git', '-C', str(root), 'show', pin['producer_commit']+':'+relative])
        if hashlib.sha256(committed).hexdigest() != expected:
            raise ValueError('COMMITTED_SOURCE_BYTES_MISMATCH')
    if pin['parent_artifact_byte_hashes'] != old['producer_files']:
        raise ValueError('IMMUTABLE_PARENT_ARTIFACT_BYTES_REQUIRED')
    if any(pin['producer_files'][k] != v for k, v in pooled['adapter_files'].items()):
        raise ValueError('ACCEPTED_PARSER_AND_POOLING_REQUIRED')
    package = '_ewp_one_shot_'+pin['producer_commit']
    namespace = types.ModuleType(package); namespace.__path__ = []; sys.modules[package] = namespace
    loaded = {}
    for short in MODULES:
        relative = PREFIX+short+'.py'
        spec = importlib.util.spec_from_file_location(package+'.'+short, root/relative)
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        if Path(inspect.getfile(module)).resolve() != (root/relative).resolve() or parent.sha(inspect.getfile(module)) != pin['producer_files'][relative]:
            raise ValueError('ACTUALLY_IMPORTED_RUNTIME_MISMATCH')
        loaded[short] = module
    task = loaded['grudeva_one_shot_calibration']
    if task.VERSION != pin['adapter_schema'] or task.api.VERSION != pin['wrapper_schema']:
        raise ValueError('CALIBRATION_WRAPPER_SCHEMA_MISMATCH')
    for a, m in old['models'].items():
        if task.md.Model.load(root/m['path']).sha256 != pin['parent_model_identities'][a]:
            raise ValueError('CANONICAL_PARENT_MODEL_MISMATCH')
    return task, pin


def predict(producer, artifacts, early, queries, folds, frozen_f2, binding, handoff_path=HANDOFF):
    task, pin = load_producer(producer, handoff_path)
    identities = {k: task.md.identity(v) for k, v in artifacts.items()}
    if task.md.identity(identities) != pin['calibration_wrapper_identities_sha256']:
        raise ValueError('FROZEN_CALIBRATION_WRAPPER_IDENTITIES_REQUIRED')
    if (binding['parent_models'] != pin['parent_model_identities']
            or binding['source']['files']['exp13.csv'] != pin['source_sha256']
            or binding['accepted_007_prediction_sha256'] != pin['accepted_007_prediction_sha256']):
        raise ValueError('SOURCE_PARENT_OR_F2_BINDING_MISMATCH')
    for name, value in (('early_inputs', early), ('queries', queries), ('folds', folds), ('frozen_f2', frozen_f2)):
        if task.md.identity(value) != pin['prediction_input_identities'][name]:
            raise ValueError('FROZEN_PREDICTION_ROLE_IDENTITY_MISMATCH:'+name)
    return task.predict_matrix(artifacts, early, queries, folds, frozen_f2, binding)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, default=HANDOFF)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args(); task, pin = load_producer(a.producer, a.handoff)
    bundle = a.bundle; target = task.private(a.output)
    if task.digest(bundle/'calibration_manifest.json') != pin['calibration_manifest_sha256']:
        raise ValueError('FROZEN_CALIBRATION_MANIFEST_REQUIRED')
    task.verify_manifest(bundle, 'calibration_manifest.json')
    folds = task.read(bundle/'folds.json')
    # Deliberately read only artifacts, typed inputs and geometry. Neither the
    # outcome projection nor the individual calibration records is opened here.
    artifacts = {f'{j}/{arm}': task.read(bundle/f'calibration-{j:02}-{arm}.json')
                 for j in folds['calibrators'] for arm in ('A0', 'A2', 'M')}
    result = predict(a.producer, artifacts, task.read(bundle/'early_inputs.json'), task.read(bundle/'queries.json'),
                     folds, task.read(bundle/'frozen_f2.json'), task.read(bundle/'source_binding.json'), a.handoff)
    task.write(target, result)
    print('Exact frozen one-shot research predictions saved; no fitting or scoring.')


if __name__ == '__main__':
    main()
