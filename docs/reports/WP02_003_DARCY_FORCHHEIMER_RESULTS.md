# WP02-003 Darcy–Forchheimer Results

## Disposition and scope

`SOLVER_BEARING_WORK_PACKAGE_COMPLETE_PR_OPEN` after the branch pull request is
opened. This work is a `GOVERNING_PHYSICS_CHANGE` with evidence roles
`CODE_VERIFICATION`, `NUMERICAL_QUALIFICATION`, and
`SYNTHETIC_MECHANISM_DIAGNOSTIC`.

The optional saturated law is

```text
-grad(p) = (mu/k) q + (rho/k_I) |q| q
```

Darcy remains the default. The existing sharp-front wetting branch is
unchanged, and paired cases have identical first-drip histories. The source
model uses the fixed Wadsworth 2026 ceramics-fit coefficients with the
documented implicit SI convention. The locked card's `0.0161–0.0639` worked
espresso band uses the separately named Zhou closure, so its disposition here
is `SOURCE_RANGE_CONTEXT_ONLY`, not source reproduction.

## Verification

Foundation OpenFOAM 12 compiled the production solver. The retained executable
SHA-256 is
`1c73648e550e3af6fd8a3aabf6792df9240f61fd7dec711f954360a301023b50`.

All fail-closed gates passed after retaining and correcting one fixture defect:
the first coarse layered fixture inherited probe windows sized for the
256-cell mesh and selected no cells. The flow result itself passed; a corrected
compact fixture widened only those probe windows. The first failed
adjudication remains in the external governed run.

| Gate | Result |
|---|---:|
| scalar positive-root relative error | `1.47e-16` |
| uniform OpenFOAM flow relative error | `2.47e-13` |
| uniform pressure-decomposition relative error | `2.54e-13` |
| layered OpenFOAM flow relative error | `6.37e-13` |
| layered interface-pressure relative error | `6.61e-13` |
| machine operating-point maximum relative error | `4.66e-12` |
| Darcy-limit finest relative error | `3.04e-10` |
| maximum machine/field flux mismatch | `4.97e-12` |
| maximum fine-pair physical-output change | `4.19e-4` |
| maximum water residual | `3.81e-15 kg` |
| maximum solute residual | `2.32e-11 kg` |
| nonlinear failures / bracket failures / fallbacks | `0 / 0 / 0` |

Conservation residuals approaching zero use the predeclared absolute
comparisons: the fine-pair changes were `2.75e-19 m3` for machine water and
`2.31e-11 kg` for solute. No tolerance was relaxed.

## Executed cases

All cases used 131,072 cells, 32 MPI ranks, and `dt=0.02 s` except the declared
DF-3 refinements.

| Case | Flow / k_I model | Runtime | Peak RSS | max / weighted Fo | inertial fraction | first drip | mean saturated flow | cup mass | TDS | EY |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DF-0 | Darcy / none | 5.14 s | 66,884 kB | 0 / 0 | 0 | 4.71170 s | 1.48268 mL/s | 40.9579 g | 11.6893% | 23.9385% |
| DF-1 | Forchheimer / Wadsworth | 10.58 s | 66,796 kB | 0.7628 / 0.7628 | 0.4327 | 4.71170 s | 0.84107 mL/s | 23.9914 g | 14.4770% | 17.3662% |
| DF-2 | Darcy / none | 30.26 s | 66,888 kB | 0 / 0 | 0 | 8.90055 s | 1.17118 mL/s | 27.6357 g | 13.7916% | 19.0570% |
| DF-3 | Forchheimer / Wadsworth | 45.15 s | 66,912 kB | 0.7454 / 0.7298 | 0.4218 | 8.90055 s | 0.80376 mL/s | 19.1693 g | 14.7061% | 14.0953% |
| DF-4 | Forchheimer / constant low-Fo | 55.07 s | 66,896 kB | 0.01591 / 0.01564 | 0.01540 | 8.90055 s | 1.15981 mL/s | 27.3805 g | 13.8321% | 18.9364% |
| DF-5 | Forchheimer / constant high-Fo | 52.36 s | 66,728 kB | 0.3341 / 0.3277 | 0.2468 | 8.90055 s | 0.97171 mL/s | 23.0928 g | 14.4028% | 16.6301% |
| DF-6 | Forchheimer / Wadsworth + WP02 | 62.88 s | 66,940 kB | 1.29e6 / 1.228 | 0.5441 | 8.90055 s | 0.06364 mL/s | 1.53576 g | 15.7025% | 1.20577% |

## Interpretation

At the current Darcy-calibrated R0 effective permeability, the fixed
Wadsworth ceramics fit predicts a transitional-to-high inertial regime:
`k_I=2.26279e-12 m` and `Fo≈0.76` under fixed basket pressure. It cuts
post-saturation flow by about 43%, cup mass by about 41%, and EY by about 27%;
TDS rises because much less water reaches the cup while extraction continues.

Machine coupling moves the operating point. Compared with DF-2, DF-3 raises
upstream and basket pressure but cannot restore the Darcy flow; mean
post-saturation flow falls about 31%, cup mass about 31%, and EY about 26%.
The low-Fo fixture (`Fo≈0.016`) remains close to Darcy. The high-Fo fixture
shows the expected nonlinear resistance and a roughly 25% inertial pressure
fraction.

DF-6 is a warning, not an improved prediction. The existing WP02 multiplier
temporarily drives `k` far below its initial value. Re-evaluating the
exponential ceramics closure consistently drives minimum `k_I` to
`2.38e-36 m`, produces a very large instantaneous Fo, and nearly arrests
production. Combining a second resistance mechanism with a permeability
previously selected under Darcy assumptions is therefore not presently
compatible as a predictive model without new identification and likely
recalibration. No retuning was performed.

Separating real Darcian and inertial resistance requires simultaneous,
time-resolved pressure at the upstream and basket nodes, outlet flow, puck
geometry, temperature-dependent viscosity and density, and independently
characterized puck state across multiple imposed flow or pressure levels.
Repeated steady or quasi-steady points spanning low and higher flow are needed
to identify the linear and quadratic coefficients separately. Permeability
evolution must be independently constrained so it is not confounded with the
quadratic term.

## Claim boundary

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
HOLDOUT_ACQUISITION: NOT_PERFORMED
PROTECTED_SCORING: NOT_PERFORMED
RESULT_CLASS: NUMERICAL_VERIFICATION_AND_SYNTHETIC_MECHANISM_DIAGNOSTIC
```
