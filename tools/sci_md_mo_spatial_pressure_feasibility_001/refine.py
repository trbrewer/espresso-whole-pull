"""Focused refinement of the frozen closest candidate; no new parameter search."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.sci_md_mo_spatial_pressure_feasibility_001.analyze import (
    TIMES, integrate,
)


def run(bundle):
    search = json.loads((bundle / "SEARCH.json").read_text())
    if search["preliminary_witnesses"]:
        raise ValueError("Witness requires interval/crossing assurance, not this null diagnostic")
    candidate = search["closest"]["candidate"]
    times = np.linspace(0, 32, 4097)
    trajectories = {}
    settings = [("DOP853", 1e-11, 1e-13, False), ("Radau", 1e-10, 1e-12, True)]
    results = []
    for method, rtol, atol, independent in settings:
        pair = []
        for pressure in (1., candidate["pressure_high"]):
            sol = integrate(candidate, pressure, method=method, rtol=rtol, atol=atol,
                            max_step=0.0625, independent=independent, times=times)
            pair.append(sol)
        ratio = pair[1]["Q"]/pair[0]["Q"]
        gap = pair[1]["Q"]-pair[0]["Q"]
        j = int(np.argmin(ratio))
        trajectories[method] = pair
        results.append({"method": method, "rtol": rtol, "atol": atol,
                        "max_step": .0625, "independent_hydraulics_and_integral": independent,
                        "samples": len(times), "rhs_evaluations": sum(s["evaluations"] for s in pair),
                        "min_ratio": float(ratio[j]), "theta_min_ratio": float(times[j]),
                        "QL_at_min_ratio": float(pair[0]["Q"][j]),
                        "QH_at_min_ratio": float(pair[1]["Q"][j]),
                        "min_absolute_gap": float(gap.min()), "theta_min_gap": float(times[np.argmin(gap)]),
                        "x_low_final": pair[0]["x"][-1].tolist(),
                        "x_high_final": pair[1]["x"][-1].tolist(),
                        "max_hydraulic_residual": max(s["hydraulic_residual"] for s in pair),
                        "max_solid_balance_error": max(s["solid_balance_error"] for s in pair)})
    # The coarse comparison uses the *retained* exploratory values at the minimum;
    # do not rerun the exploratory integration solely to manufacture a receipt.
    cross = {"max_abs_Q_method_difference": float(max(np.max(np.abs(a["Q"]-b["Q"]))
             for a,b in zip(trajectories["DOP853"], trajectories["Radau"]))),
             "max_abs_x_method_difference": float(max(np.max(np.abs(a["x"]-b["x"]))
             for a,b in zip(trajectories["DOP853"], trajectories["Radau"]))),
             "max_abs_gap_method_difference": float(np.max(np.abs(
                 (trajectories["DOP853"][1]["Q"]-trajectories["DOP853"][0]["Q"])-
                 (trajectories["Radau"][1]["Q"]-trajectories["Radau"][0]["Q"]))))}
    result = {"candidate": candidate, "trajectory_count": 4, "settings_and_results": results,
              "comparison": cross,
              "assurance": "INTER_METHOD_DIFFERENCE_ESTIMATE_NOT_GLOBAL_ERROR_BOUND",
              "scope": "closest completed pair only; no continuous-time or whole-family exclusion",
              "coarse_min_ratio": search["closest"]["minimum_ratio"],
              "coarse_samples": len(TIMES)}
    (bundle / "REFINEMENT.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    run(parser.parse_args().bundle)
