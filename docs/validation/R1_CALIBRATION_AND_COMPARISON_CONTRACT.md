# R1 Calibration and Comparison Contract

## Authority and scope

Task: `WP01R-003` / issue #5. Declaration:
`NO_GOVERNING_PHYSICS_CHANGE`.

Status: `FROZEN_FOR_WP01R_004`; effective when merged to `main`.

This contract binds Puckworks commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`, and the merged
[Waszkiewicz dossier](../evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md), whose
disposition is `READY_FOR_WP01R_003_WITH_DECLARED_GAPS`. The
[authoritative JSON](../../validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json)
contains all 42 source-quantity roles, formulas, selectors, gates, and exact
identities.

Issue #5 contains conflicting generated form text. Its substantive
`NO_GOVERNING_PHYSICS_CHANGE` declaration controls; the issue is not edited.

R1 is a source-linked, existing-physics reconstruction and attempted
falsification of the frozen R0 sharp-front plus uniform-Darcy architecture
under the Waszkiewicz 18.5 g / 9-bar-reference rig context. It does not
implement Waszkiewicz poroelasticity and is not independent validation. The
static pressure–flow relation calibrates the hydraulic scale; five per-shot
flow shapes are protected. No post-run retuning is permitted.

## Frozen scenario

Hardware context remains a nominal 58 mm basket. The hydraulic computation
uses a 56 mm bed diameter, 0.028 m radius, and
`pi * 0.028^2 = 0.002463008640414398 m2`. With central dry dose `0.0185 kg`,
approximate bed depth `0.010 m`, and inherited solid density `1400 kg/m3`,
mass closure gives initial porosity `0.46349007886296223`. This is a derived
engineering scenario value, not measured Waszkiewicz porosity or `Phi_m`.

Liquid properties are `363.15 K` (a property-reference mapping, not a measured
temperature trace), density `965 kg/m3`, dynamic viscosity `0.000315 Pa s`,
and effective solute diffusivity `1e-9 m2/s`. Density and diffusivity are
inherited R0 engineering assumptions.

The central case retains the straight-sided 5-degree wedge, `256 x 512 x 1`
mesh, `0.02 s` step, 32 routine MPI ranks, `scotch` decomposition, and 1 s
field snapshots. The reduced flow trace is written every solver step or no
coarser than 0.1 s.

## Pressure and time

The source 9 bar value is a grouping label, not a constant solver boundary.
Locked rows 900–999 give:

- late mean line/pump-side pressure: `9.12039023 bar` gauge;
- late mean basket/puck-inlet pressure: `8.709024190000001 bar` gauge;
- late mean line-to-basket loss: `0.411366039999999 bar`;
- late mean observed mass flow: `1.86335566 g/s`.

R1 uses basket-top `870902.419 Pa` gauge and basket-bottom `0 Pa` gauge. From
solver time 0 to 3 s, pressure ramps linearly from zero; afterward it remains
constant. This inherited R0 mapping does not reproduce the measured machine
transient. The measured line trace and brewer-loss adapter remain context,
not additional active resistance.

Source trace time zero follows source pressure stabilization. It maps to
solver time 3 s:

`solver_time = source_time + 3 s`.

Thus source indices 100–899 (`10.01001–89.98999 s`) map to solver
`13.01001–92.98999 s`; normalization indices 900–999
(`90.09009–100 s`) map to solver `93.09009–103 s`. End time is 103 s.
The fixed source-processing first-drop offset of 8 s is excluded. Post-run
shifting, feature alignment, dynamic time warping, smoothing changes, or
amplitude/pressure rescaling are forbidden.

## One calibration degree of freedom

The locked static fit supplies fixed inputs:

- `P_c = 12.391550000000002 bar`;
- `Q_c = 1.8969919954879988 g/s`.

For `x = P_basket/P_c`,
`q_hat = x(4 - 6x + 4x^2 - x^3)` and `q_eq = Q_c q_hat`, giving
`q_eq = 1.8821959328386835 g/s`. Analytical Darcy inversion gives:

`K = ((q_eq/1000)/rho) mu h / (A delta_p)`

and central `K = 2.8642613245723525e-15 m2`. Saturated and wetting
permeabilities are both this value, an explicit engineering simplification.
Uniform permeability is the single active solver calibration degree of
freedom. There are zero optimizer or post-run calibration iterations.

The covariance-diagonal source-fit values generate only a nonprobabilistic
corner envelope, `2.56903088781814e-15` to
`3.110578602953478e-15 m2`. It is not a confidence interval, posterior, or
permission to replace the central case.

The existing sharp-front formula predicts first drip at
`4.426434882126959 s` from solver time zero. This is numerical verification
and plausibility only, not comparison to the excluded 8 s source offset.

## Protected flow-shape comparison

Exactly shots `9-1`, `9-2`, `9-3`, `9-4`, and `9-5` are protected. Each
observed and predicted trace is normalized by its own mean over indices
900–999. The unsmoothed prediction is linearly interpolated onto source times.
Metrics over indices 100–899 are normalized RMSE and Pearson correlation.

All gates must hold:

- median normalized RMSE `<= 0.15`;
- at least 4/5 shots have RMSE `<= 0.20`;
- median Pearson `r >= 0.95`;
- at least 4/5 shots have `r >= 0.90`.

Undefined Pearson correlation is `FAIL`. Locked source-only diagnostics are
maximum pairwise normalized-shot RMSE `0.17374032155590768` and minimum
pairwise `r = 0.9399097878989583`. These are pre-run engineering tolerances,
not confidence limits or independent-validation thresholds. Protected traces
cannot select permeability, time shift, pressure, smoothing, or amplitude.

The central simulated late mean must reproduce the static target within 2%.
The observed late mean differs from that target by `1.0009729863919606%`,
within a predeclared 5% source-reconciliation plausibility check; it is not
used to refit permeability.

## Chemistry, dispositions, and claim ceiling

R1 retains R0 one-solute assumptions—extractable fraction `0.28`, extraction
rate `0.15 1/s`, and capacity `180 kg/m3`—only to exercise conservation and
machine-to-cup outputs. TDS, EY, solute mass, and retained inventories are
reported as plausibility outputs. None is protected or physically validated.

Contract integrity, case generation, numerical verification, conservation,
calibration reproduction, protected flow shape, chemistry plausibility, and
overall comparison have separate statuses. A numerically successful run may
fail the protected comparison. Such failure is a scientific residual, not a
software failure, and cannot trigger retuning or mutate R0.

The maximum claim is `SOURCE_LINKED_RECONSTRUCTION_PASS` or
`SOURCE_LINKED_RECONSTRUCTION_FAIL`: a within-campaign test of the existing
numerically qualified architecture for one rig condition. It does not
establish independent physical validation, transfer, poroelastic or chemistry
validation, evolving structure, channeling, fines, or taste prediction.

No R1 case, solver change, fitting, Puckworks execution, or OpenFOAM execution
is authorized or performed here. Once merged, issue #6 may implement this
frozen contract without changing it.
