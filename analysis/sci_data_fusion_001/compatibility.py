from __future__ import annotations

LOAD_BEARING_GATES = (
    "physical_quantity", "reference_state", "unit_basis", "spatial_support",
    "temporal_support", "observation_operator", "population_regime", "lineage",
    "independence_target_exposure", "provenance_rights", "ewp_consumer",
    "no_new_inference",
)


def adjudicate(left: dict, right: dict) -> dict:
    """Fail closed: every gate must be explicitly true; unknown never passes."""
    gates = {name: left.get("pair_gates", {}).get(right["support_id"], {}).get(name) for name in LOAD_BEARING_GATES}
    failed = [name for name, value in gates.items() if value is False]
    unknown = [name for name, value in gates.items() if value is not True and value is not False]
    compatible = not failed and not unknown
    return {"left_support_id": left["support_id"], "right_support_id": right["support_id"], "gates": gates,
            "failed_gates": failed, "unknown_gates": unknown,
            "terminal_compatibility": "COMPATIBLE" if compatible else ("INCOMPATIBLE" if failed else "BLOCKED_SEMANTIC")}


def interval_metrics(left: tuple[float, float], right: tuple[float, float]) -> dict:
    for interval in (left, right):
        if len(interval) != 2 or interval[0] > interval[1]:
            raise ValueError("invalid closed interval")
    lo, hi = max(left[0], right[0]), min(left[1], right[1])
    overlap = max(0.0, hi - lo)
    union = max(left[1], right[1]) - min(left[0], right[0])
    return {"intersection": None if lo > hi else [lo, hi], "overlap_width": overlap,
            "union_width": union, "overlap_fraction": overlap / union if union else 1.0,
            "separation_gap": max(0.0, lo - hi)}


def common_constraint(supports: list[dict], compatibility: list[dict]) -> dict:
    if len({item["lineage_id"] for item in supports}) < 2:
        return {"result": "NEGATIVE_NO_COMMON_SUPPORT", "reason": "FEWER_THAN_TWO_DISTINCT_ELIGIBLE_LINEAGES"}
    if any(row["terminal_compatibility"] != "COMPATIBLE" for row in compatibility):
        return {"result": "COMPLEMENTARY_SOURCE_CONDITIONED_ONLY", "reason": "LOAD_BEARING_COMPATIBILITY_GATE_NOT_PASSED"}
    intervals = [item["interval"] for item in supports]
    lo, hi = max(x[0] for x in intervals), min(x[1] for x in intervals)
    if lo > hi:
        return {"result": "CONFLICT_SAME_SCOPE_SUPPORTS", "common_support": None}
    return {"result": "POSITIVE_COMMON_CONSTRAINT", "common_support": [lo, hi],
            "source_ids": [item["support_id"] for item in supports]}

