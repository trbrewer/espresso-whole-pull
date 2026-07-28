# Waszkiewicz R1 Source, Quantity, and Evidence Dossier

## Scope and status

This WP01R-002 dossier records the source facts needed to define a distinct
Waszkiewicz-linked R1 scenario. Change declaration:
`NO_GOVERNING_PHYSICS_CHANGE`.

Status: `COMPLETE_WITH_REGISTERED_GAPS`.

This is a source dossier only. It does not freeze prescribed or calibration
inputs, choose protected comparisons, fit parameters, implement an R1 case, or
run OpenFOAM. Those decisions begin with issue #5.

The controlling dependency is Puckworks commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`, reviewed under
`REVIEWED_MAIN_AT_RECORDED_UTC_CUTOFF`.

Primary source identifiers:

- Waszkiewicz et al., “Under pressure: Poroelastic regulation of flow in
  espresso brewing”
- journal DOI `10.1063/5.0319611`
- arXiv `2512.21528`
- data DOI `10.5281/zenodo.18046315`

The [machine-readable dossier](../../validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json)
contains 17 source-artifact records, 37 quantity records, four pressure nodes,
five time nodes, and 16 registered missing-data or ambiguity records.

## Source condition

The source campaign reports:

- dry dose: 18.50 ± 0.05 g;
- nominal basket: 58 mm;
- hydraulic bed diameter: 56 mm, represented by the separately recorded
  0.028 m radius;
- approximate initial bed height: 0.010 m;
- Sanremo Zoe machine;
- Fiorenzato F64 grinder at device setting 1.9;
- one Brazilian light-medium roast;
- 20 kg reported tamp load and WDT preparation;
- a processed 9 bar reference-pressure condition.

The 58 mm basket and 56 mm bed diameter are not interchangeable. The former is
nominal hardware size; the latter defines the source hydraulic flow area.

The source constants table gives pure-water viscosity
`3.15e-4 Pa s` at a nominal 90 °C reference. It does not establish a measured
brew-temperature trace, and concentration-dependent liquor viscosity is not
represented.

## Quantity classification

Each machine-readable quantity is classified as exactly one of:

- direct observation;
- source-reported parameter;
- digitized value;
- derived value;
- fitted parameter;
- engineering assumption;
- unavailable.

Candidate roles are proposals only and carry
`NOT_FROZEN_BY_WP01R_002`. Issue #5 must decide prescribed, calibrated,
excluded, and protected-comparison roles before fitting or execution.

Key fitted quantities retained as fitted—not observations—include:

- `P_c = 12.391550000000002 ± 2.9758249059787327 bar`;
- `Q_c = 1.8969919954879988 ± 0.1471316135226419 g/s`;
- TDS sigmoid `k_t`, `l_t`, and `m_t`;
- dissolved-mass sigmoid `k_m`, `l_m`, and `m_m`;
- the 8.0 s first-drop offset;
- brewer pressure-loss coefficients `a`, `b`, and `c`.

The derived `Phi_m ≈ 0.1220` is `k_m/m0`; it is not a direct porosity
measurement. Wet-bed Young’s modulus and effective pore diameter are
unavailable as source inputs.

## Pressure nodes

The dossier preserves four distinct pressure semantics:

1. `REFERENCE_PRESSURE_BIN`: a derived condition label based on median
   line/pump-side `p2`, rounded to 0.5 bar with documented source corrections.
2. `LINE_OR_PUMP_SIDE_GAUGE`: the measured `pressure__bar` trace.
3. `BASKET_OR_PUCK_INLET_GAUGE`: `basket_pressure__bar`, derived by subtracting
   the fitted brewer pressure loss from line pressure.
4. `LINE_TO_BASKET_PRESSURE_DROP`: the fitted quadratic adapter
   `delta_p = a Q² + b Q + c`.

The 9 bar label is therefore not a constant basket-pressure boundary. In the
committed 9 bar mean trace, line pressure spans approximately
8.6663–9.315005 bar and the derived basket pressure spans approximately
8.383076–9.031585 bar. Issue #5 must freeze the downstream boundary/node
contract.

## Flow, mass, TDS, and time semantics

The deposited flow quantity is mass flow in g/s, derived from the source scale
trace after alignment, Savitzky–Golay smoothing, differentiation, and
interpolation. It is not a directly deposited volumetric-flow observable.
Conversion to m3/s or mL/s requires an explicit liquid-density assumption,
which this dossier does not select.

The mean trace supplies:

- measured scale mass in g;
- derived mass-flow rate in g/s;
- measured line pressure in bar gauge;
- derived basket pressure in bar gauge;
- standard-error columns for aggregated quantities.

The 9 bar condition contains five per-brew trajectories. Across the full
deposit, 57 records represent 56 distinct brews. `12-8-6.txt` is an exact
prefix of `12-8-6_alt.txt`; source-aggregate reproduction retains the alias,
while shot-as-experimental-unit analyses exclude it. The 13 bar condition
therefore contains seven records representing six brews.

Time is not a single interchangeable coordinate:

- source trace zero is the sample after the last early out-of-tolerance `p2`;
- processed traces use 1000 points over 0–100 s;
- TDS values are twelve five-second fraction midpoints from 2.5–57.5 s;
- the dissolved-mass fit carries an 8.0 s first-drop offset;
- the source equilibrium definition uses 110–120 s, while Puckworks records a
  100 s endpoint alternative because an ended shot contaminates the longer
  window.

Mapping these coordinates to solver time is an issue #5 contract decision.

The TDS fractions are direct observations with replicate information, but the
first fraction has one replicate and no standard deviation. Their exact
downstream mass/volume and wet/dry basis remains unresolved.

## Processing and digitization history

No figure digitization is used in this dossier.

The formatted source tables are byte-exact repository pulls from the public
Zenodo deposit. Puckworks’ per-brew table is a documented independent
re-expression of the source reduction:

- pressure-bin assignment;
- source time alignment;
- truncation at 100 s;
- pressure conversion;
- Savitzky–Golay mass derivative, window 31 and polynomial order 1;
- fitted brewer pressure-loss subtraction;
- interpolation onto the common grid.

The source’s GPLv3 producer code was not ingested or executed in this task.
Committed Puckworks outputs were inspected statically.

## Rights and redistribution

- Puckworks repository code: MIT.
- Waszkiewicz deposited data: CC-BY-4.0 with attribution.
- AIP journal article: citation-only; no article text, tables, or figures are
  redistributed.
- Source analysis code: GPLv3, not ingested or executed.
- Some outward-use rights remain `NOT_REVIEWED` per Puckworks.

No Puckworks dataset, code, paper text, figure, or other rights-restricted
material is vendored here. The JSON records paths, Git blobs, SHA-256
identities, short semantics, and rights status.

## Missing-data and ambiguity register

The dossier retains rather than silently resolves:

- no rights-cleared journal/preprint equation reconciliation;
- missing shot-matched TDS;
- incomplete identity and rationale for source-excluded brews;
- unresolved downstream TDS basis;
- no measured brew-temperature trace;
- no wet-bed Young’s modulus;
- no effective pore diameter;
- incomplete coffee identity and condition metadata;
- incomplete uncertainties for nominal constants and brewer coefficients;
- 58 mm basket versus 56 mm hydraulic-bed geometry;
- reference-pressure bin versus measured line and derived basket pressure;
- mass-flow versus density-dependent volumetric conversion;
- source/TDS/first-drop/solver time-origin mapping;
- source 110–120 s equilibrium definition versus the 100 s endpoint
  alternative;
- calibration-role authorization;
- protected-comparison selection.

## Acceptance and next task

Every candidate quantity has a source location; units, bases, pressure nodes,
time nodes, uncertainty, processing, and rights status are explicit.
Digitized values are distinguishable from reported values—there are zero
digitized values here—and fitted quantities are distinct from observations.
Conflicts and unavailable values remain registered.

WP01R-002 therefore completes the issue #4 source dossier without increasing
the claim ceiling. R0 remains a
`NUMERICALLY_QUALIFIED_CALIBRATION_BASELINE`; physical validation remains
`NOT_ESTABLISHED`.

Next: issue #5 must freeze the R1 prescribed/calibrated/protected-comparison
contract before any fitting or R1 implementation.
