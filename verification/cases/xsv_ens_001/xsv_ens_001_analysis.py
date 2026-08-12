#!/usr/bin/env python3
"""Testable statistical decisions for the XSV-ENS-001 completion pass."""
from __future__ import annotations

import hashlib
import math
from collections import defaultdict

import numpy as np


def bootstrap_log_mean_precision(values, *, seed=20260812, replicates=10000,
                                 relative_half_width_limit=0.10,
                                 minimum_n=8, maximum_n=24):
    values = np.asarray(values, dtype=float)
    if len(values) == 0 or np.any(values <= 0):
        raise ValueError("positive permeability values required")
    logs = np.log(values)
    rng = np.random.default_rng(seed)
    means = np.mean(logs[rng.integers(0, len(logs), (replicates, len(logs)))], axis=1)
    center = float(np.exp(np.mean(logs)))
    low, high = np.exp(np.quantile(means, [0.025, 0.975]))
    relative_half_width = float(max(center - low, high - center) / center)
    precision_met = len(values) >= minimum_n and relative_half_width <= relative_half_width_limit
    if precision_met:
        action = "STOP_PRECISION_MET"
    elif len(values) >= maximum_n:
        action = "STOP_MAXIMUM_N_UNRESOLVED"
    else:
        action = "ADD_NEXT_FROZEN_BATCH"
    return {
        "n": len(values), "geometric_mean": center,
        "bootstrap_95_ci": [float(low), float(high)],
        "relative_half_width": relative_half_width,
        "precision_met": bool(precision_met), "action": action,
    }


class _UnionFind:
    def __init__(self, items): self.parent = {item: item for item in items}
    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.parent[max(ra, rb)] = min(ra, rb)


def assign_physical_lineages(records):
    """Union identical masks, transformations/parents, and same-RNG SF states."""
    ids = [str(r["geometry_id"]) for r in records]
    uf = _UnionFind(ids)
    by_hash = defaultdict(list)
    by_id = {str(r["geometry_id"]): r for r in records}
    for row in records: by_hash[str(row["geometry_sha256"])].append(str(row["geometry_id"]))
    for members in by_hash.values():
        for member in members[1:]: uf.union(members[0], member)
    for row in records:
        gid, parent = str(row["geometry_id"]), str(row.get("parent_id") or "")
        if parent and parent in by_id: uf.union(gid, parent)
    sf_groups = defaultdict(list)
    for row in records:
        if row.get("family") == "SOLID_FRACTION":
            sf_groups[(int(row["L"]), int(row["seed"]), float(row["voxel_um"]))].append(str(row["geometry_id"]))
    for members in sf_groups.values():
        for member in members[1:]: uf.union(members[0], member)
    roots = defaultdict(list)
    for gid in ids: roots[uf.find(gid)].append(gid)
    labels = {}
    for members in roots.values():
        token = "|".join(sorted(members)).encode()
        label = "LINEAGE-" + hashlib.sha256(token).hexdigest()[:16]
        for gid in members: labels[gid] = label
    return labels


def target_disposition(ratios, connected_retentions, *, target=0.373506,
                       minimum_valid_n=8, majority_fraction=0.75,
                       topology_retention_min=0.25, seed=20260812):
    ratios = np.asarray(ratios, dtype=float)
    connected_retentions = np.asarray(connected_retentions, dtype=float)
    if len(ratios) < minimum_valid_n:
        disposition = "TARGET_ATTAINMENT_UNRESOLVED_UNCERTAINTY"
    else:
        rng = np.random.default_rng(seed)
        samples = ratios[rng.integers(0, len(ratios), (10000, len(ratios)))]
        ci = np.exp(np.quantile(np.mean(np.log(samples), axis=1), [0.025, 0.975]))
        robust = ci[1] <= target and np.mean(ratios <= target) >= majority_fraction
        if robust and np.min(connected_retentions) >= topology_retention_min:
            disposition = "ROBUST_TARGET_ATTAINMENT_WITHOUT_TOPOLOGY_LOSS"
        elif robust:
            disposition = "TARGET_ATTAINMENT_ONLY_NEAR_CONNECTIVITY_LOSS"
        elif np.any(ratios <= target):
            disposition = "TARGET_ATTAINMENT_IN_SOME_REALIZATIONS_ONLY"
        else:
            disposition = "TARGET_ATTAINMENT_NOT_REACHED"
    return disposition


def rve_adjudication(size_stats, *, resolution_effect_resolved,
                     gpu_limit_measured, mean_band=(0.90, 1.10),
                     variance_margin=0.15):
    ordered = sorted(size_stats, key=lambda row: row["L"])
    if len(ordered) < 2: raise ValueError("at least two sizes required")
    largest = ordered[-1]
    comparisons = []
    for row in ordered[:-1]:
        # Inputs carry a prospectively bootstrapped ratio interval.
        interval = row["mean_ratio_to_largest_ci"]
        comparisons.append({"L": row["L"], "interval": interval,
                            "equivalent": interval[0] >= mean_band[0] and interval[1] <= mean_band[1]})
    adjacent_ok = comparisons[-1]["equivalent"]
    precision_ok = all(row["sampling_precision_met"] for row in ordered[-2:])
    means = np.array([row["mean_K"] for row in ordered[-3:]], float)
    monotone = bool(np.all(np.diff(means) > 0) or np.all(np.diff(means) < 0))
    mean_stable = adjacent_ok and precision_ok and not monotone and resolution_effect_resolved
    cvs = np.array([row["cv_K"] for row in ordered[-2:]], float)
    variance_stable = mean_stable and abs(cvs[0] / cvs[1] - 1) <= variance_margin
    if mean_stable and variance_stable:
        mean_disp = "SYNTHETIC_GENERATOR_REV_CANDIDATE"
        variance_disp = "SYNTHETIC_GENERATOR_REV_CANDIDATE"
    elif mean_stable:
        mean_disp = "SYNTHETIC_GENERATOR_MEAN_STABILIZATION_ONLY"
        variance_disp = "SYNTHETIC_GENERATOR_VARIANCE_NOT_STABILIZED"
    else:
        mean_disp = "NO_SYNTHETIC_GENERATOR_REV_RESOLVED"
        variance_disp = "SYNTHETIC_GENERATOR_VARIANCE_NOT_STABILIZED"
    if not resolution_effect_resolved:
        limitation = "SPATIAL_RESOLUTION_PREVENTS_REV_ADJUDICATION"
    elif gpu_limit_measured:
        limitation = "GPU_DOMAIN_LIMIT_PREVENTS_REV_ADJUDICATION"
    else:
        limitation = "COMPUTE_OR_RESOLUTION_BOUND_NOT_ESTABLISHED"
    return {"comparisons": comparisons, "adjacent_equivalence": adjacent_ok,
            "sampling_precision_largest_two": precision_ok,
            "monotone_largest_three": monotone,
            "mean_disposition": mean_disp, "variance_disposition": variance_disp,
            "limitation": limitation}
