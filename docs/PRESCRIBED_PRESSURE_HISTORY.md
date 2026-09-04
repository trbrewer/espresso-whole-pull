# Prescribed inlet-pressure histories

The interface enables measured or programmed pressure histories, including ramps,
holds, declines, and zero-pressure tails. Select the generic production mode:

```foam
pressureBoundaryModel prescribedPressureHistory;
prescribedPressureBoundary
{
    scheduleType piecewiseLinear;
    timesS      (0 1 5 20 30);
    pressuresPa (0 100000 900000 900000 0);
}
```

Times are solver seconds and pressures are inlet gauge Pa. Supply equal-length
lists containing at least two finite points, strictly increasing times and
nonnegative pressures. The schedule must cover the complete run interval.
Interpolation is linear between adjacent points. Extrapolation is fatal;
endpoint tolerance recognizes floating-point equality only. Repeated pressure
values are permitted, but duplicate times are not.

Do not include `targetInletPressure` or `pressureRampTime` in history mode.
Conversely, legacy `prescribedPressure` still requires both scalar inputs and
rejects the history dictionary. Mixed definitions produce
`XSV_PRESSURE_001_CONTRACT_CONFLICT`. Prescribed flow and machine compliance
retain their existing contracts.

The solver evaluates the schedule for the existing inlet patch and pressure
trace. Sharp-front wetting uses the exact integral of `max(P(t)-Pf,0)`, split
at knots and front-pressure threshold crossings. Saturation/first-drip timing
locates the crossing segment by exact integration, then uses deterministic
96-iteration bounded bisection for interior crossings. A full-segment integral
returns the exact first positive-support endpoint, including the start of a
zero-area plateau. An unreachable integral is fatal. Compaction
validation uses the largest pressure anywhere in the schedule, including an
interior peak followed by zero pressure.

The canonical JSON case preparation input is:

```json
{
  "hydraulics": {
    "pressure_boundary_model": "prescribedPressureHistory",
    "prescribed_pressure_boundary": {
      "schedule_type": "piecewiseLinear",
      "times_s": [0, 1, 5, 20, 30],
      "pressures_gauge_Pa": [0, 100000, 900000, 900000, 0]
    }
  }
}
```

Retain the other ordinary hydraulics and scenario fields. Remove legacy
`target_inlet_pressure_gauge_Pa` and `pressure_ramp_time_s`. Generated scientific
input manifests bind the schedule-bearing configuration, model dictionary,
solver source and headers, mesh/numerical dictionaries and initial fields.
Execution qualification separately binds the executable hash. The legacy
scalar analytical preview is explicitly inapplicable to history cases.

Convert CSV or external traces into these JSON/OpenFOAM lists outside the
production solver, resolving units and pressure-node meaning in that conversion.
The solver performs no CSV parsing, gain/offset adjustment, smoothing or filtering.
The verification-only pressure-history probe is not a production solver API.

## Numerical qualification

The runner uses generic synthetic cases and requires Foundation OpenFOAM 12.
It expects the previously checked unmodified baseline source at
`qualification_runs/xsv-pressure-001/baseline/pristine` and its archived
executable at `qualification_runs/xsv-pressure-001/baseline/espressoWholePullFoam`.
Recreate that source from the exact commit in `BASELINE_RECEIPT.json` using a
detached worktree, then build and archive its executable before candidate work.
The runner uses that original case renderer for baseline regressions.

```bash
source scripts/lib/openfoam_env.sh
load_openfoam12
python3 scripts/run_xsv_pressure_001_qualification.py \
  --work qualification_runs/xsv-pressure-001/new-run
python3 scripts/validate_xsv_pressure_001.py --root .
python3 -m unittest tests.test_xsv_pressure_001
```

The destination must not exist. Solver and probe builds are cleaned and linked
into the isolated run directory. The probe is verification-only and is not
installed as a production application. Full logs, meshes, executable files and
fields remain in the ignored work directory; committed evidence is compact and
content-hashed. Failed and superseded attempts are retained explicitly.
