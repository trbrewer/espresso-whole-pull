#!/usr/bin/env python3
"""Thin research consumer of an explicitly pinned Puckworks mass-delivery model.

Queries use synthetic requested beverage intervals. No native solver is involved.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = ROOT/'docs/analysis/sci_md_mass_delivery_001/HANDOFF.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, expression):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', expression], text=True).strip()


def load_producer(producer, handoff_path=DEFAULT_HANDOFF):
    """No installed/local Puckworks import search: verify and load the named file."""
    producer = Path(producer).resolve()
    handoff = json.loads(Path(handoff_path).read_text())
    if git(producer, 'HEAD') != handoff['producer_commit'] or git(producer, 'HEAD^{tree}') != handoff['producer_tree']:
        raise ValueError('producer revision/tree mismatch')
    for relative, expected in handoff['producer_files'].items():
        path = (producer/relative).resolve()
        if not path.is_relative_to(producer) or not path.is_file() or sha(path) != expected:
            raise ValueError('producer file hash/path mismatch')
    kernel = producer/handoff['kernel_path']
    artifact = producer/handoff['model_path']
    if handoff['kernel_path'] not in handoff['producer_files'] or handoff['model_path'] not in handoff['producer_files']:
        raise ValueError('unbound kernel or model')
    name = '_ewp_explicit_mass_delivery_producer'
    spec = importlib.util.spec_from_file_location(name, kernel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    model = module.Model.load(artifact)
    if model.model_id != handoff['model_id'] or model.version != handoff['model_version'] or model.family != 'MASS':
        raise ValueError('model identity mismatch')
    if model.units != handoff['units'] or list(model.domain_kg) != handoff['domain_kg']:
        raise ValueError('model units/domain mismatch')
    if not {'RESEARCH_ONLY', 'SOURCE_INTERNAL', 'TARGET_EXPOSED', 'PHYSICAL_VALIDATION_NOT_ESTABLISHED'} <= set(model.claims):
        raise ValueError('claim limits missing')
    return model, handoff


def demonstrate(producer, handoff=DEFAULT_HANDOFF, stop_kg=.04):
    model, pin = load_producer(producer, handoff)
    # Synthetic requests, no measured or reconstructed shot is represented here.
    delivery = model.predict([0., .01, .02], [.01, .02, .03])
    return {'producer_commit': pin['producer_commit'], 'producer_tree': pin['producer_tree'],
            'model_id': model.model_id, 'model_sha256': pin['producer_files'][pin['model_path']],
            'query_class': 'SYNTHETIC_REQUESTED_MASS_INTERVALS',
            'interval_solute_kg': delivery.solute_kg.tolist(),
            'interval_TDS_percent': delivery.tds_percent.tolist(),
            'conditional_stop_mass_kg': stop_kg,
            'modeled_solute_to_stop_kg': float(model.cumulative_solute(stop_kg)),
            'supported_domain_kg': list(model.domain_kg), 'claims': list(model.claims),
            'rights': model.rights, 'native_solver_runs': 0,
            'interpretation': 'Conditional on achieving requested beverage mass; modeled gaps are not measured cup totals.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--producer', type=Path, required=True, help='explicit checkout at HANDOFF producer revision')
    p.add_argument('--handoff', type=Path, default=DEFAULT_HANDOFF)
    p.add_argument('--stop-kg', type=float, default=.04)
    args = p.parse_args()
    print(json.dumps(demonstrate(args.producer, args.handoff, args.stop_kg), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
