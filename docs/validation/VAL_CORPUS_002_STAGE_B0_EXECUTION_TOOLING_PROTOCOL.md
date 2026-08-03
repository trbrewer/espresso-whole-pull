# VAL-CORPUS-002 Stage B0 Execution Tooling Protocol

**Status:** `FROZEN_PROSPECTIVE_TOOLING_CONTRACT`  
**Authority:** `EWP-VAL-CORPUS-002-STAGE-B0-TOOLING-CORRECTED-PARITY-2026-08-03`  
**Change declaration:** `SOURCE_SCENARIO_CHANGE_ONLY`  
**Evidence class:** `RECONSTRUCTION_OR_CALIBRATION`  
**Governing physics:** unchanged  
**Stage B1/B2:** not authorized

This append-only contract freezes the case-local tooling before implementation.
It does not authorize OpenFOAM preparation, build, decomposition or execution;
solver-result access; fitting; optimizer invocation against the solver;
model-versus-source scoring; transfer-result access; or protected scoring.

## Tool and record inventory

The implementation is limited to `scripts/val_corpus_002_*.py`,
`tests/test_val_corpus_002_*.py`, and records below
`validation/cases/val_corpus_002/`. The canonical external tooling workspace is
`<VAL_CORPUS_002_RUNTIME_ROOT>/`, resolving at execution time to
`/home/tim/espresso-development/.val-corpus-002-runtime/`; absolute host paths
must not be committed in generated portable records.

The tool suite will provide deterministic configuration materialization,
runtime/executable identity verification, external-artifact inventories,
fixed-mass and interval reducers, two clock presentations, predecessor parity,
synthetic golden-section mechanics, calibration and production reductions,
axis contrasts, finite-range sensitivity, the source-only species limitation
audit, and fail-closed result-access and claim-ceiling enforcement.

## Canonical configuration and P2 templates

Canonical JSON is UTF-8, object keys sorted lexicographically, separators
`,` and `:` without optional whitespace, no NaN or Infinity, and one terminal
newline. SHA-256 is over those exact bytes. Deterministic inventory counts are:

- 45 final production identities;
- 30 numeric P0/P1 configurations available before calibration;
- 15 typed P2 templates (14 Schmieder and one Waszkiewicz);
- 9 sensitivity identities, with 8 new executions when exact baseline reuse
  is valid; and
- at most 128 optimizer evaluations.

Every P2 template contains exactly one typed object
`{"type":"P2_EXTRACTION_RATE_S_INVERSE","value":"UNMATERIALIZED"}` at the
extraction-rate scalar. Materialization requires an approved canonical
pre-materialization hash and the exact frozen P2 manifest, changes only that
object to a finite numeric scalar inside the frozen bounds, and rejects zero,
multiple or missing placeholders and every other byte-semantic change. The
single frozen P2 value applies to all cases and hydraulic modes. Each numeric
configuration, template, sensitivity identity, and Experiment-7/H1 calibration
template receives an exact canonical hash.

## Direct-content parity binding

The reference binding class is `DIRECT_CONTENT_ADDRESS`. The normalized path
is
`<WP03_002_REVIEW_ROOT>/corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv`,
where `<WP03_002_REVIEW_ROOT>` resolves read-only to
`/home/tim/espresso-development/.wp03-002-exact-head-review`.

Frozen trace identity:

- SHA-256: `bb3a5d2214b3eaf0cec2d76be0c90f56b2454cfa1982b2770841b499ed1db30a`;
- bytes: `2796444`;
- header SHA-256: `27eb008688cb84f98f5b7f877aa73d745f4b3e28ce5c99f95673ed222c854831`;
- first timestamp: `0.02 s`;
- final timestamp: `29.9999999999994 s`;
- reference configuration SHA-256:
  `09abbfdc0115a59b9452048f1ac2dcdbaf7707c91c31b166c998eab78ecf28b5`;
- executable SHA-256:
  `e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6`;
- case scientific-input manifest SHA-256:
  `2687a4f7b0693bf41173eecc6332e95be9e5f8cc62f7bd4957323556d45ea778`;
- scientific-input bundle SHA-256:
  `b4930f327466f201ddaab002373ec16e51075ea90e8621963afc056180bef770`;
- corrected-run execution-record SHA-256:
  `5a08518c0cbe6935f17b4826c473c7b494e1c4650c9efda733af903199422875`;
- build-provenance SHA-256:
  `5a27f0b6e2e2599e1a7174f314b4f702c571b97ead262580a7a4769a52b9fcd4`;
- source bundle SHA-256:
  `79935492c9dd2058407fca3feb469ca77de98cf132a08d1cf9814fc74b20efb8`;
- source-and-executable bundle SHA-256:
  `3281e033171309db79b2b9f155f45f2644927cb2253ebf122fe8903665c11157`;
- historical manifest status:
  `EXCLUDED_AS_DOWNSTREAM_ARTIFACT_BY_DESIGN`.

The historical manifest and trace remain unmodified. Historical-manifest
membership is not required.

## Predecessor parity

The future 63-second P0 trace is compared at every retained reference state in
the inclusive common domain `[0.02, 29.9999999999994] s`. The terminal value is
accepted as 30 seconds under the `1e-12 s` time tolerance. Exact timestamps are
preferred; otherwise deterministic linear interpolation between the nearest
bracketing candidate samples is used. Extrapolation and insertion of a `t=0`
parity row are prohibited.

Fields and absolute tolerances are:

| Trace field | Absolute tolerance |
|---|---:|
| `time_s` | `1e-12 s` |
| `inlet_pressure_Pa` | `1e-6 Pa` |
| `outlet_flow_m3_s` | `1e-16 m3/s` |
| `cup_water_mass_kg` | `1e-12 kg` |
| `cup_solute_mass_kg` | `1e-12 kg` |
| `cup_beverage_mass_kg` | `1e-12 kg` |
| `remaining_extractable_mass_kg` | `1e-12 kg` |
| `dissolved_in_puck_mass_kg` | `1e-12 kg` |
| `volumeWeightedMechanicalPorosity` | `1e-12` |
| `volumeWeightedPermeabilityM2` | `1e-25 m2` |

Each field passes exactly when
`abs(candidate-reference) <= absolute_tolerance + 1e-10*abs(reference)`.
Missing, duplicate, nonfinite, unordered, out-of-domain, unbracketed, or
schema-incompatible data fail closed.

Initial-state parity is separate and exact. It binds simulation start time,
initial fields, configuration, geometry/mesh, executable, chemistry,
pressure-ramp, timestep, and numerical/control identities. Trace values do not
substitute for these checks.

## Observation operators

Fixed-mass observations preserve time order. Finite nonnegative cumulative
masses must be nondecreasing. Equal beverage-mass plateaus are allowed only
when solute mass is unchanged within `1e-12 kg` and collapse to the last
time-ordered sample. Exact target matches are used; otherwise the first
strictly increasing adjacent mass pair is linearly interpolated. Mass sorting
and extrapolation are prohibited.

For Waszkiewicz intervals, water rate is
`density_kg_m3*outlet_flow_m3_s`, solute rate is
`totalSoluteFluxKgS`, and beverage rate is their sum. Values in
`[-1e-15,0] kg/s` become zero; lower or nonfinite values fail. Each 5-second
TDS value is the trapezoidal integral of solute rate divided by the
trapezoidal integral of beverage rate. Endpoints must be exact or bracketed.

Only this interval reducer may prepend an exact boundary sample at `t=0` with
zero water rate, solute rate, and cup inventories, and only after exact checks
that the case starts at zero, cup inventories are zero, the initial wetting
state has no outlet flow, initial dissolved concentration is zero, and outlet
solute flux is zero. It supplies the left boundary of `[0,5] s`; it is neither
an observed/retained row nor usable for parity.

The same interval values feed both the native and fixed `+3 s` presentations.
The reduced source clock remains a separate diagnostic using
`t=M/(rho Q)`, `M_s=M_0(1-exp(-kt))`, `TDS=M_s/M`, and `EY=M_s/dose`.

## Optimizer mechanics

P2 uses deterministic golden-section minimization on the frozen closed bounds.
The two initial interior points are evaluated in ascending parameter order;
all subsequent uncached points are evaluated in deterministic algorithm order.
Exact hexadecimal floating-point keys prevent duplicate evaluations. Cached
points do not consume the 128-evaluation limit. The stopping rule and final
selection use the frozen absolute/relative interval tolerances; endpoints are
evaluated when required for boundary selection. Failed or nonfinite model
evaluations are retained with infinite objective and a typed failure reason.
If all selectable points fail, the optimization fails. Equal objective values
use the lower-rate tie break. The final point is the lowest objective among all
valid evaluated points, subject to that tie break. Limit exhaustion returns a
typed nonconverged record and never silently promotes a fit.

Every trace row records sequence, rate, hexadecimal rate key, cache status,
objective or null, evaluation status/reason, active bounds and interior points,
decision, and final-selection status. Synthetic tests cover an interior and a
boundary minimum, ties, repeated points, failed and nonfinite evaluations, and
evaluation-limit exhaustion. No solver invocation is permitted in B0.

## Metrics and sensitivity

Calibration reduction is restricted to Experiment-7/H1 and the frozen
three-mass objective. Production reduction reports source and model values,
absolute error, declared-denominator relative error, three-mass RMSE,
standardized residual only where source SD exists, replicate count/range/SD,
and paired H0/H1 error ratios without epsilon floors. Axis contrasts are
high-minus-low flow, coarse-minus-fine setting, and high-minus-low temperature
at each brew ratio.

Waszkiewicz reports unweighted RMSE, MAE, bias, and early/middle/late residuals
over frozen windows. Uncertainty weighting is secondary and only uses supplied
uncertainty. The source-only species audit never treats named species as solver
outputs.

Finite-range one-at-a-time sensitivity is
`[ln(y_high)-ln(y_low)]/[ln(p_high)-ln(p_low)]`; missing, nonfinite, or
nonpositive inputs fail. It reports the 3-output by 4-parameter matrix,
singular values, declared rank tolerance, rank, correlations, and equifinality
warning. It is `NOT_STRUCTURAL_IDENTIFIABILITY`.

## Artifact and access barriers

External inventories use normalized portable paths, regular-file type, bytes,
SHA-256, and a deterministic aggregate over sorted entries. Symlinks,
unexpected members, hash mismatches, and local absolute paths in committed
records fail. Generated OpenFOAM products remain external and untracked.

The result-access state machine begins at `B0_SYNTHETIC_ONLY`. It refuses all
model-result paths. B1 requires separate authority and exposes only
Experiment-7/H1 calibration observations/results. Transfer results remain
inaccessible until an exact P2 calibration manifest and optimizer trace are
frozen. P2 materialization then requires one identical rate across all cases
and modes. Transfer observations cannot enter calibration, and no
post-transfer refit transition exists.

Historical Waszkiewicz hydraulic comparison fields are inert provenance. The
tooling refuses protected flow-series loading, historical protected-shape
scoring, protected shot identifiers as chemistry evidence, and any execution
command requesting those comparisons. Only chemistry preparation and
predecessor parity are admissible.

All reports retain:

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
OPENFOAM: NOT_RUN_IN_STAGE_B0
CALIBRATION: NOT_EXECUTED
GOVERNED_SCORING: NOT_PERFORMED
STAGE_B1: NOT_STARTED
```

Any identity, schema, access, parity, completion, conservation, or claim-ceiling
failure stops before later-stage access. Completion of B0 ends at
`VAL_CORPUS_002_STAGE_B0_TOOLING_COMPLETE_PENDING_REVIEW`.
