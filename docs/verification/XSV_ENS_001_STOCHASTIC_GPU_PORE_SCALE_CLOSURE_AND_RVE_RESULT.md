# XSV-ENS-001 stochastic GPU pore-scale closure and RVE result

Status: `EXECUTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW`  
Evidence: `STOCHASTIC_GENERATOR_ENSEMBLE`, `SIMULATED_SYNTHETIC_REFERENCE`,
`POST_OBSERVATION_TARGET_COMPARISON`  
Change: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; repository-local ensemble,
descriptor and reduction machinery is a diagnostic model extension only.

## 1. Executive result

Nominally equivalent overlapping-sphere packs do not support one precise
permeability closure. Across the baseline size cells, Kx coefficients of
variation were 34–69%; at L=40 the 10th-to-90th percentile interval was
0.604–2.779 lu². Porosity alone achieved grouped cross-validated R²=0.206 for
log K. Adding connected porosity, interfacial area, pore-distance and topology
descriptors raised R² to 0.682, but the remaining 95% predictive factor was
about 2.26. A stochastic rather than single-scalar closure is warranted for
this generator.

No synthetic-generator representative volume was resolved. Mean K at L=32,
56 and 72 was similar, but L=40 was 16% below the largest-size mean, spread
continued to change materially, the largest box was only about 3.6 particle
diameters, and same-continuous-geometry spatial convergence was not fully
adjudicated. The dispositions are `NO_SYNTHETIC_GENERATOR_REV_RESOLVED`,
`SYNTHETIC_GENERATOR_VARIANCE_NOT_STABILIZED`,
`GPU_DOMAIN_LIMIT_PREVENTS_REV_ADJUDICATION`, and
`REAL_PUCK_REV_NOT_ASSESSED`.

A static throat-restriction proxy can mathematically produce the SCI-MD-001
resistance requirement without disconnecting the periodic flow domain. At 30%
void restriction, the converged-pair geometric-mean K ratio was 0.3525, but
only two of three pairs crossed 0.373506 and the 95% interval [0.3005, 0.4362]
did not: `TARGET_ATTAINMENT_IN_SOME_REALIZATIONS_ONLY`. At 40% restriction,
all three converged pairs crossed all exact targets; geometric mean was 0.2303,
95% interval [0.1829, 0.2992], and minimum connected-porosity retention was
0.600: `ROBUST_TARGET_ATTAINMENT_WITHOUT_TOPOLOGY_LOSS` under the frozen rule.
This is a capability result for a severe synthetic static transformation, not
evidence that pressure created such a state or that it is supported for real
coffee.

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

The scored matrix contained 172 identities: 162 passed and ten were retained
as nonconverged. The secondary force sweep contained 25 identities: 24 passed
and one was retained as nonconverged. There were no allocation failures, seed
substitutions, or disconnected geometries. Total reported GPU kernel time was
375.7 s. Full evidence is external (944 files, 77,543,142 bytes; ordered-file
aggregate `edc13f16326a711df300251900f99ba308f79ea986bd7c7c3b5bdc934b612fa6`).

## 4. Spatial resolution and finite volume

The accepted generator at 30 µm has a characteristic radius near ten voxels.
Scored box sizes were L=24, 32, 40, 56 and 72, or approximately L/d=1.2–3.6.
The 8 GiB GPU and required resolution prevented the desired L/d≈8 range.
Baseline mean K values were 1.006, 1.765, 1.516, 1.740 and 1.809 lu²;
respective CVs were 0.540, 0.578, 0.686, 0.440 and 0.341. These results show
large finite-sample variability and no qualified variance plateau.

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
| 0.10 | 4 | 0.6108 | 0.5351–0.6748 | none |
| 0.20 | 3 | 0.5130 | 0.4672–0.5869 | none |
| 0.30 | 3 | 0.3525 | 0.3005–0.4362 | 2/3 only |
| 0.40 | 3 | 0.2303 | 0.1829–0.2992 | 3/3, robust frozen rule |

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

Eleven directional triplets completed. Median K_perp/Kx was 0.806, but the
range was 0.296–4.382. Thus transverse communication is not uniformly
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

Grouped cross-validation kept all rows from a geometry together:

| model | grouped CV R²(log K) | RMSE(log K) | nominal 95% factor |
|---|---:|---:|---:|
| porosity and particle-state only | 0.206 | 0.654 | 3.62 |
| porosity plus topology | 0.682 | 0.414 | 2.26 |
| topology plus synthetic fabric/state labels | 0.682 | 0.414 | 2.26 |

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
2.5–2.7-fold resistance increase, but the crossing is transformation-level and
realization dependent, and severe 40% void restriction lacks a physical bound.
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

The boxes span only about 1.2–3.6 characteristic diameters; resolution was not
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
