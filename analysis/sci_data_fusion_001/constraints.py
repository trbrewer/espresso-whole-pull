from __future__ import annotations


def narrowing(common: list[float] | None, baseline: list[float] | None) -> dict:
    if baseline is None:
        return {"baseline_status": "NO_AUTHORIZED_NUMERIC_BASELINE", "quantitative_narrowing_claim": False}
    if common is None:
        return {"baseline_status": "AUTHORIZED_BASELINE_AVAILABLE", "common_support_empty": True, "quantitative_narrowing_claim": False}
    if baseline[0] > baseline[1] or common[0] > common[1]:
        raise ValueError("invalid interval")
    subset = baseline[0] <= common[0] and common[1] <= baseline[1]
    bw, cw = baseline[1] - baseline[0], common[1] - common[0]
    return {"baseline_status": "AUTHORIZED_BASELINE_AVAILABLE", "strict_subset": subset and common != baseline,
            "absolute_width_reduction": bw - cw, "relative_width_reduction": (bw - cw) / bw if bw else None,
            "quantitative_narrowing_claim": subset and cw < bw}

