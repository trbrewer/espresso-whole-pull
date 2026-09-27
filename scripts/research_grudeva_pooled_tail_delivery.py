#!/usr/bin/env python3
"""Task-007 thin consumer; exact parent runtime plus exact source adapter, no fitting."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import types

import research_conditional_tail_delivery as parent

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_007/HANDOFF.json'
ADAPTER = 'puckworks/analysis/grudeva_pooled_tail_delivery.py'
PARSER = 'puckworks/analysis/grudeva_clock.py'


def load_adapter(execution_producer, parent_producer, handoff_path=HANDOFF):
    pin = json.loads(Path(handoff_path).read_text())
    root = Path(execution_producer).resolve()
    if (parent.git(root, 'HEAD') != pin['execution_producer_commit']
            or parent.git(root, 'HEAD^{tree}') != pin['execution_producer_tree']):
        raise ValueError('EXACT_TASK_EXECUTION_PRODUCER_REQUIRED')
    if set(pin['adapter_files']) != {ADAPTER, PARSER}:
        raise ValueError('EXACT_ADAPTER_FILES_REQUIRED')
    for name, sha in pin['adapter_files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root) or parent.sha(path) != sha:
            raise ValueError('ADAPTER_OR_PARSER_HASH_MISMATCH')
    parent_handoff = ROOT/pin['parent_handoff_path']
    if parent.sha(parent_handoff) != pin['parent_handoff_sha256']:
        raise ValueError('PARENT_HANDOFF_IDENTITY_MISMATCH')
    runtime, _, old_pin = parent.load_producer(parent_producer, handoff_path=parent_handoff)
    if old_pin['producer_commit'] != pin['immutable_parent_producer_commit'] or old_pin['producer_tree'] != pin['immutable_parent_producer_tree']:
        raise ValueError('IMMUTABLE_PARENT_IDENTITY_MISMATCH')
    source_record = root/'docs/analysis/sci_md_mass_delivery_007/SOURCE.json'
    if parent.sha(source_record) != pin['source_record_sha256']:
        raise ValueError('SOURCE_RECORD_IDENTITY_MISMATCH')
    # Isolated namespace: adapter imports this explicitly verified mathematical
    # runtime; it cannot silently use an installed Puckworks package instead.
    package = '_ewp_pooled_'+pin['execution_producer_commit']
    namespace = types.ModuleType(package); namespace.__path__ = []
    sys.modules[package] = namespace
    sys.modules[package+'.conditional_tail_delivery'] = runtime
    for relative, short in ((PARSER, 'grudeva_clock'), (ADAPTER, 'grudeva_pooled_tail_delivery')):
        spec = importlib.util.spec_from_file_location(package+'.'+short, root/relative)
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    if module.VERSION != pin['adapter_schema']:
        raise ValueError('ADAPTER_SCHEMA_MISMATCH')
    return module, pin, parent_handoff


def predict(execution_producer, parent_producer, early, queries, handoff_path=HANDOFF):
    adapter, pin, old_handoff = load_adapter(execution_producer, parent_producer, handoff_path)
    # Only strict typed arm inputs and coordinate-only queries are accepted.
    inputs = adapter.input_index(early)
    if any((a, q['shot']) not in inputs for a in ('C0', 'C1', 'C2') for q in queries):
        raise ValueError('COMMON_SHOT_SUPPORT_REQUIRED')
    output = {}
    for arm in ('C0', 'C1', 'C2'):
        output[arm] = []
        for query in queries:
            q = adapter.checked_query(query)
            rec = dict(q, status='UNSUPPORTED', prediction=None, feature_extrapolation=[],
                       integration_start_kg=None, integration_end_kg=None, coordinate_allowance_kg=0.)
            try:
                values = inputs[(arm, q['shot'])]
                module, model, _ = parent.load_producer(parent_producer, arm, old_handoff)
                state = model.condition(module.EarlyInput.from_dict(values.to_dict()))
                rec['feature_extrapolation'] = list(state.feature_extrapolation)
                a, b, allowance = adapter.runtime_coordinates(q, state.b_anchor)
                result = parent.predict(parent_producer, values.to_dict(), [{'start_kg': a, 'end_kg': b}],
                                        arm=arm, handoff_path=old_handoff)
                prediction = result['predictions'][0]
                prediction['allowance_kg'] += allowance
                prediction['numerical_qualified'] = prediction['allowance_kg'] <= 1e-9
                rec.update(status='QUALIFIED' if prediction['numerical_qualified'] else 'NUMERICALLY_UNRESOLVED',
                           prediction=prediction, integration_start_kg=a, integration_end_kg=b,
                           coordinate_allowance_kg=allowance)
            except (ValueError, FloatingPointError, OverflowError) as exc:
                rec['status'] = str(exc)
            output[arm].append(rec)
    return output


def demonstrate(execution_producer, parent_producer, handoff_path=HANDOFF):
    adapter, _, _ = load_adapter(execution_producer, parent_producer, handoff_path)
    early = [{'shot': 1, 'arm': a, 'input': adapter.md.EarlyInput(a, (.007, .006, .15, .1)[:len(adapter.md.feature_names(a))], 'SYNTHETIC').to_dict()} for a in adapter.md.ARMS]
    return predict(execution_producer, parent_producer, early,
                   [{'shot': 1, 'vial': 10, 'mass_kg': .002, 'start_kg': .013, 'end_kg': .015}], handoff_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execution-producer', required=True, type=Path)
    parser.add_argument('--parent-producer', required=True, type=Path)
    parser.add_argument('--handoff', default=HANDOFF, type=Path)
    parser.add_argument('--synthetic', action='store_true')
    parser.add_argument('--early-inputs', type=Path); parser.add_argument('--queries', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    module, _, _ = load_adapter(a.execution_producer, a.parent_producer, a.handoff)
    out = module.private(a.output)
    if a.synthetic:
        result = demonstrate(a.execution_producer, a.parent_producer, a.handoff)
    else:
        if not a.early_inputs or not a.queries:
            parser.error('Provide both serialized pooled early inputs and coordinate-only queries.')
        result = predict(a.execution_producer, a.parent_producer, module.read(a.early_inputs), module.read(a.queries), a.handoff)
    module.write(out, result)
    print('Research consumer output saved; no fit, outcome join or production adoption.')


if __name__ == '__main__':
    main()
