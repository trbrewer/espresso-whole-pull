"""Bounded algebra/history audit; no model evolution, fit, or empirical score.

Run with --puckworks-root pointing to the read-only research authority.
The default output is stdout; --output retains the deterministic JSON receipt.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puckworks-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    ewp = Path(__file__).resolve().parents[3]
    pw = args.puckworks_root
    revision = subprocess.check_output(
        ["git", "-C", str(pw), "rev-parse", "HEAD"], text=True
    ).strip()
    assert revision == "58075bbbce548e63d94106c96b918c1464221514"
    rel = "puckworks/data/waszkiewicz2025/"
    trace = pw / rel / "traces_per_brew.csv"
    coeff = pw / rel / "brewer_quadratic_params.csv"
    # Exact reused SCI-MD-010 INPUT_ARTIFACT_REGISTER authorities.
    assert digest(trace) == "55fcc6290113932d863b0b6aa6571ad169e5e32f78920659c2cefe2184abef08"
    assert digest(coeff) == "60da3adf0d29da64a1a4730d5c9997f04d8c6ee7d4d12f8e8d142f4ad0aa3919"
    membership = ewp / "docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv"
    with membership.open() as stream:
        canonical = {r["source_row_id"]: r["group_id"] for r in csv.DictReader(stream)
                     if r["lane_id"] == "L-HYD" and r["role"] == "EVALUATION"}
    assert len(canonical) == 56 and len(set(canonical.values())) == 11
    histories = {shot: {} for shot in canonical}
    with trace.open() as stream:
        for row in csv.DictReader(stream):
            if row["shot_id"] in histories:
                history = histories[row["shot_id"]]
                index = int(row["time_index"])
                assert index not in history
                # Read line pressure only; neither observed flow nor basket pressure.
                history[index] = Decimal(row["pressure__bar"])
    assert all(set(h) == set(range(1000)) for h in histories.values())
    diagnostics = json.loads((ewp / "docs/analysis/sci_md_010/PRESSURE_RESPONSE_DIAGNOSTICS.json").read_text())
    means = diagnostics["HYD_E1_LUMPED_DARCY"]["condition_means"]
    high = sorted((r for r in means if r["line_pressure_bar"] >= 8.5),
                  key=lambda r: r["line_pressure_bar"])
    history_checks = []
    for i, low in enumerate(high):
        for upper in high[i + 1:]:
            pairs = []
            for left in sorted(s for s in canonical if canonical[s] == low["condition_id"]):
                for right in sorted(s for s in canonical if canonical[s] == upper["condition_id"]):
                    index = min(range(1000), key=lambda j: histories[right][j] - histories[left][j])
                    pairs.append((histories[right][index] - histories[left][index], left, right, index))
            gap, left, right, index = min(pairs)
            history_checks.append({
                "lower_group": low["condition_id"], "upper_group": upper["condition_id"],
                "physical_brew_pairs": len(pairs),
                "pairs_with_any_negative_pressure_gap": sum(p[0] < 0 for p in pairs),
                "minimum_gap_bar": str(gap), "witness_source_row_ids": [left, right],
                "witness_time_index": index, "witness_time_s_exact": str(Fraction(100 * index, 999)),
            })
    with coeff.open() as stream:
        parameters = {r["parameter"]: Decimal(r["value"]) for r in csv.DictReader(stream)}
    a, b, h0 = (parameters[k] for k in ("a", "b", "c"))
    assert a > 0 and b > 0 and h0 > 0
    with localcontext() as ctx:
        ctx.prec = 50

        def root(k: Decimal, line: Decimal) -> Decimal:
            if k < 0 or line < h0:
                raise ValueError("outside nonnegative-flow adapter domain")
            if k == 0:
                return Decimal(0)
            linear = 1 + b * k
            return 2 * k * (line - h0) / (linear + (linear**2 + 4 * a * k**2 * (line - h0)).sqrt())

        cases = []
        for k, line in [(Decimal(0), Decimal(1)), (Decimal(1), h0),
                        (Decimal(1), Decimal(9)), (Decimal(1), Decimal(13))]:
            q = root(k, line)
            bed = line - (a*q*q + b*q + h0)
            residual = q - k*bed
            assert abs(residual) < Decimal("1e-45") and bed >= 0 and q >= 0
            cases.append({"K_g_s_bar": str(k), "L_bar": str(line), "q_g_s": str(q),
                          "P_bar": str(bed), "q_minus_KP_g_s": str(residual)})
        try:
            root(Decimal(1), h0 - Decimal("0.01"))
        except ValueError:
            rejected = True
        else:
            rejected = False
        assert rejected
        # Independent central differences of the explicit root vs implicit sensitivities.
        k, line, eps = Decimal(1), Decimal(9), Decimal("0.00001")
        q = root(k, line)
        bed = line - (a*q*q + b*q + h0)
        den = 1 + (2*a*q+b)*k
        err_l = abs((root(k, line+eps)-root(k, line-eps))/(2*eps) - k/den)
        err_k = abs((root(k+eps, line)-root(k-eps, line))/(2*eps) - bed/den)
        assert err_l < Decimal("1e-9") and err_k < Decimal("1e-9")
    # Illustration only: a standard last-point degree-one least-squares filter
    # on 31 gradient samples is not an order-preserving map of those samples.
    weights = [Fraction(1, 31) + Fraction((j-15)*15, 2480) for j in range(31)]
    assert sum(weights) == 1 and sum(j*w for j, w in enumerate(weights)) == 30
    assert weights[0] == Fraction(-29, 496)
    result = {
        "task_id": "SCI-MD-MO-PRESSURE-FEASIBILITY-001",
        "role": "DETERMINISTIC_ALGEBRA_AND_APPLICABILITY_CHECK_NOT_SCORING",
        "status": "PASS",
        "puckworks_revision": revision,
        "input_sha256": {rel+"traces_per_brew.csv": digest(trace),
                         rel+"brewer_quadratic_params.csv": digest(coeff),
                         "docs/analysis/sci_md_010/FOLD_MEMBERSHIP.csv": digest(membership)},
        "canonical_physical_brews": len(canonical), "conditions": 11, "samples_per_brew": 1000,
        "all_canonical_line_pressure_range_bar": [str(min(min(h.values()) for h in histories.values())),
                                                  str(max(max(h.values()) for h in histories.values()))],
        "history_scope": "high groups selected by retained measured condition means >=8.5 bar; source-aligned grid 0..100 s; not pre-alignment physical histories",
        "high_pressure_history_checks": history_checks,
        "adapter_algebra_cases": cases,
        "adapter_cases_role": "arbitrary K=0 or 1 dimensional algebra checks only; not coffee parameterization or feasibility witness",
        "below_intercept_rejected": rejected,
        "sensitivity_abs_errors": {"dq_dL": str(err_l), "dq_dK": str(err_k)},
        "standard_endpoint_linear_filter": {
            "scope": "conditional illustration of the usual polynomial edge fit; not a reconstruction of the accepted observer",
            "first_weight_exact": str(weights[0]), "negative_weights": sum(w < 0 for w in weights),
            "sum_exact": str(sum(weights)), "order_preserving_on_arbitrary_gradient_samples": False},
        "model_trajectories": 0, "fits": 0, "scores": 0,
        "physical_validation": "NOT_ESTABLISHED",
    }
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
