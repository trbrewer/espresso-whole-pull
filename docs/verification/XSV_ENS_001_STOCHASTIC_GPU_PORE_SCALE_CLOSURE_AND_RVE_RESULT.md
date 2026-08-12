# XSV-ENS-001 stochastic GPU pore-scale closure and RVE result

Status: `EXECUTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW`  
Evidence: `STOCHASTIC_GENERATOR_ENSEMBLE`, `SIMULATED_SYNTHETIC_REFERENCE`,
`POST_OBSERVATION_TARGET_COMPARISON`  
Change: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; repository-local ensemble,
descriptor and reduction machinery is a diagnostic model extension only.

## 1. Executive result

Nominally equivalent overlapping-sphere packs do not support one precise
permeability closure across the tested finite domains. Baseline Kx coefficients
of variation fell from 72.0% at L=24 to 3.63% at L=160, with substantial
spread through L=96. A true measured-porosity-only model achieved
physical-lineage-grouped cross-validated R²=0.408 for log K. Adding connected
porosity, interfacial area, pore-distance and topology descriptors raised R²
to 0.632; the remaining nominal 95% predictive factor was 2.41 with 95.1%
empirical out-of-fold coverage. A stochastic rather than unsupported
single-scalar closure remains warranted until the representative scale and
resolution dependence are resolved.

No synthetic-generator representative volume was resolved. The completion
pass qualified and executed through L=160, approximately eight characteristic
particle diameters. L=128 was mean-equivalent to L=160 under the frozen band,
and both largest sizes met sampling precision, but L=96 did not meet mean
equivalence, the largest-three means retained a monotone trend, variance/CV
continued to fall, and same-continuous-geometry spatial convergence was not
fully adjudicated. The dispositions are `NO_SYNTHETIC_GENERATOR_REV_RESOLVED`,
`SYNTHETIC_GENERATOR_VARIANCE_NOT_STABILIZED`,
`SPATIAL_RESOLUTION_PREVENTS_REV_ADJUDICATION`, and
`REAL_PUCK_REV_NOT_ASSESSED`. The measured GPU limit was not reached.

A static throat-restriction proxy can mathematically produce the SCI-MD-001
resistance requirement without disconnecting the periodic flow domain. After
eight parents were attempted, only six valid pairs remained at 20–40%
restriction. At 40%, all six valid ratios crossed every target, with geometric
mean 0.2102 and 95% interval [0.1728, 0.2587], while minimum connected-porosity
retention was 0.600. This is a strong preliminary capability signal, but the
frozen minimum of eight valid pairs was not met, so its disposition is
`TARGET_ATTAINMENT_UNRESOLVED_UNCERTAINTY`, not robust. It is not evidence that
pressure created such a state or that it is supported for real coffee.

## 2. Questions and SCI-MD-001 relationship

SCI-MD-001 requires apparent-conductance ratios 0.389226 (middle), 0.395294
(late), and the stringent 0.373506 terminal target. XSV-ENS-001 asks whether
static synthetic states can attain those exact ratios, how realization and
finite-volume uncertainty affect that conclusion, and which closures should
be measured next. It is explicitly a `STATIC_STATE_CAPABILITY_COMPARISON` and
`NOT_DYNAMIC_MECHANISM_IDENTIFICATION`.

## 3. Numerical qualification

The accepted XSV-TAICHI-002 anchor reproduced K_gross=1.7919953 lu² versus
1.7919979 lu² (1.45e-6 relative). Across f64 forces 5e-7, 1e-6 and 2e-6,
q/g varied by 2.95e-6 and maximum Mach was 2.41e-4. At g=1e-5, f32 differed
from f64 by 0.0976% in K and 0.0041% in localization CV, with Mach 0.00121.
Broad ensembles therefore used f32 with retained f64 anchors and a fresh
process per solve. The gross-area/void-area identity and half-force convention
were preserved.

The completed primary programme contains 300 attempted identities: 283 passed
and 17 were retained as nonconverged. Three domain-qualification identities
passed. The secondary force sweep retained 24 passes and one nonconvergence.
There were no allocation failures, seed substitutions, or disconnected
geometries. Total reported GPU solver time was 1,035.2 s. External evidence
contains 1,596 files and 466,365,359 bytes with ordered-file aggregate
`3db16287c305b86a4726724723aa0c695ba2c5fa7da425f983667ec270f7e8ca`.

## 4. Spatial resolution and finite volume

The accepted generator at 30 µm has a characteristic radius near ten voxels.
Executed box sizes were L=24, 32, 40, 56, 72, 96, 128 and 160, approximately
L/d=1.2–8.0. Measured qualification at L=96/128/160 retained 91.5%, 89.6% and
85.6% GPU-memory headroom respectively; all passed. The original five sizes
continued to 24 attempted identities because none met 10% precision. L=96
stopped at 12 valid identities; L=128 and L=160 stopped at eight. CV decreased
across the largest sizes from 0.169 to 0.0968 to 0.0363, so variance was not
stable even though the L=128/L=160 mean comparison passed equivalence.

`SPATIAL_DISCRETIZATION: NOT_FULLY_ADJUDICATED`. The programme did not obtain
a defensible three-resolution, same-continuous-geometry series. Consequently
no axial, transverse, localization or topology REV is claimed.

## 5. Morphology and static-state capability

Regenerated solid-fraction states showed the expected strong trend but also
large overlap: mean K was 2.643 at nominal phi_s=0.50, 1.516 at 0.55, 0.849
for seven converged 0.60 cases, and 0.633 at 0.64. These are independently
regenerated states, not a compression trajectory. They do not identify how a
real bed moves between states.

Paired static restriction ratios were:

| Removed baseline void | Converged pairs | geometric mean K/K0 | 95% CI | terminal attainment |
|---:|---:|---:|---:|---|
| 0.10 | 8 | 0.6008 | 0.5565–0.6479 | none |
| 0.20 | 6 | 0.5016 | 0.4613–0.5478 | none; valid n below 8 |
| 0.30 | 6 | 0.3350 | 0.2906–0.3892 | 4/6; uncertainty unresolved |
| 0.40 | 6 | 0.2102 | 0.1728–0.2587 | 6/6; uncertainty unresolved |

Columnar heterogeneity did not simply add resistance. Mean K increased from
1.52 for the comparable L40 uniform ensemble to 1.85–2.78 across tested
heterogeneity amplitudes and lengths, while localization and anisotropy varied.
This falsifies any assumption that scalar heterogeneity amplitude is itself a
monotone resistance closure.

The resolved bimodal arm was not executed: `RESOLVED_BIMODAL_ARM:
NOT_EXECUTED_RESOLUTION_LIMIT`. A meaningful small-radius population could not
be combined with adequate domain-scale sampling on the available GPU without
confounding sub-resolution particles and finite volume.

## 6. Directional permeability and localization

Eleven of 16 directional triplets completed. Their complete-case median
K_perp/Kx was 0.806 and range was 0.296–4.382. Direction-dependent
nonconvergence may bias these descriptive statistics. Transverse communication is not uniformly
negligible in these finite synthetic packs, yet its magnitude and even apparent
ordering are realization- and state-sensitive. These are diagonal directional
components, not a complete tensor. The breadth supports a future lateral-flow
question, but synthetic-generator and resolution uncertainty prevent direct
production closure.

Flow Gini, top-flow shares and normalized entropy changed with K and state.
Their broad realization spread reinforces that one nominal velocity field can
misrepresent localization. No real-puck channeling inference follows.

## 7. Inertial closure

The frozen secondary selection used baseline geometries nearest the 10th,
50th and 90th percentile, one 40% restricted state, and one heterogeneous
state. Five forces from 5e-6 to 8e-5 reached maximum Mach 0.0026–0.0137.
Quadratic fits had positive full-fit coefficients, but leave-one-force-out
coefficients were unstable and often changed sign. Therefore
`INERTIAL_CURVATURE: NOT_RESOLVED_WITHIN_QUALIFIED_FORCE_RANGE`. A fixed
Darcy–Forchheimer coefficient is not supported by this campaign, and inertia
has no demonstrated role in the SCI-MD pressure ordering.

## 8. Stochastic closure discovery

Grouped cross-validation kept identical mask hashes, paired transformations
and their parents, and same-seed common-RNG solid-fraction states in one fold:

| model | grouped CV R²(log K) | RMSE(log K) | nominal 95% factor |
|---|---:|---:|---:|
| measured porosity only | 0.408 | 0.567 | 3.05 |
| porosity plus topology | 0.632 | 0.447 | 2.41 |
| topology plus synthetic fabric/state labels | 0.633 | 0.446 | 2.40 |

Connected porosity, interfacial area, pore-distance and Euler connectivity add
material predictive information. The present fabric/state labels add no
cross-validated improvement beyond those topology descriptors. Remaining
variance is too large for a deterministic K. The provisional recommendation
is a conditional lognormal distribution for Kx with explicit residual
realization variance, and an empirical distribution for K_perp/Kx. Its
interpolation domain is limited to the tested synthetic states; extrapolation
to real coffee, dynamic pressure causation, or subvoxel fines is prohibited.

## 9. Continuum implication and next programme

Static morphology is mathematically capable of exceeding the required
2.5–2.7-fold resistance increase, but robust ensemble attainment is unresolved
because only six of eight attempted pairs were valid at the load-bearing
levels, and severe 40% void restriction lacks a physical bound.
The generator has no established representative-volume regime and higher-order
topology matters much more than porosity alone. The evidence therefore favors
`REAL_GEOMETRY_IMPORT_AND_MICROCT_COMPARISON` before new production physics.
That programme should test whether the large topology/anisotropy spread is an
overlapping-sphere artifact and calibrate defensible morphology bounds.

SCI-LC-001 is scientifically motivated by the non-negligible, highly variable
transverse ratios, and WP04-FIN-001 is motivated by the restriction capability,
but neither should begin from this branch. `NO_NEW_PRODUCTION_PHYSICS_YET`
remains the continuum-integration disposition.

## 10. Limitations and prohibited interpretations

The boxes span about 1.2–8.0 characteristic diameters; resolution was not
fully adjudicated; ten primary and one inertial identity did not converge;
the bimodal proxy was not executable; descriptors are voxelized proxies; and
no morphology range is physically calibrated to coffee. The static
transformation does not reveal whether pressure, fines, swelling, compaction,
or another process produced a state. These results are numerical verification,
synthetic capability, falsification and closure-discovery evidence only.

```text
PHYSICAL_VALIDATION:
  NOT_ESTABLISHED

REAL_COFFEE_REPRESENTATIVE_VOLUME:
  NOT_ESTABLISHED

DYNAMIC_PRESSURE_MECHANISM:
  NOT_IDENTIFIED
```
