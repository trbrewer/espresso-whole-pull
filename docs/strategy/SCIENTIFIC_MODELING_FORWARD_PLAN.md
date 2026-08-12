# Scientific Modeling Forward Plan

Status: enduring scientific handoff; SCI-MD-001 merged complete; XSV-ENS-001
scientific completion pass pending exact-head review.
Change declaration: `NO_GOVERNING_PHYSICS_CHANGE` for this document.

## 1. Executive scientific diagnosis

Espresso Whole Pull (EWP) is already a broad whole-pull modelling platform. Its
present bottleneck is mechanism discrimination, not the ability to add more
equations. Every tested production family reverses the Waszkiewicz terminal
flow and accumulated-mass ordering (`source: 5 bar > 9 bar > 11 bar`), the
fixed Schmieder comparison reverses the tested grind direction at all three
brew ratios, and a locally successful extraction/time-history reconstruction
does not transfer across sources. Physical validation is not established.
These failures are productive scientific targets: sign, ordering, residual
shape, plausibility and transfer precede aggregate error.

## 2. Current merged modelling capabilities

The Foundation OpenFOAM 12 platform includes initially dry sharp-front
wetting; prescribed and machine-coupled pressure; Darcy and
Darcy--Forchheimer saturated flow; axial and radial heterogeneity;
dissolution-indexed effective permeability; quasi-static compaction;
conservative one-solute transport and extraction; cup accumulation; spatial
diagnostics; Taichi/LBM closure work; and sensitivity and identifiability
infrastructure. These are verified or diagnostic capabilities, not proof that
their internal mechanisms represent physical coffee accurately.

## 3. Prioritized forward task sequence

### Completed: SCI-MD-001

**Pressure-ordering and grind-response mechanism discrimination.** Determine
which mechanisms can explain the current sign, ordering and transfer failures,
and what physical behaviour the source requires before selecting new
production physics.

### Completed candidate pending exact-head review: XSV-ENS-001

**Stochastic GPU pore-scale closure and representative-volume assessment.**
Produce ensemble permeability, anisotropy, inertial, transverse-conductance,
localization and uncertainty closures instead of relying on one synthetic
packing. The authorized execution is on
`verification/xsv-ens-001-stochastic-pore-closure-rve`.

The bounded completion pass executed the frozen sequential sampling through
L=160, repaired physical-lineage grouped closure analysis, and removed the
unsupported GPU-limit claim. No synthetic-generator REV was resolved because
the L=96 comparison missed mean equivalence, the largest-size variance trend
continued, and spatial resolution remains unadjudicated. Severe static
restriction remains a strong capability signal but not a robust ensemble
result because only six of eight attempted pairs were valid. Real-geometry
import and microCT comparison remains the provisional next recommendation;
no successor programme is authorized on this branch.

### Next lateral-flow programme: SCI-LC-001

**Lateral equalization and channeling phase diagram.** Determine when imposed
heterogeneity decays, persists or amplifies, using reduced multi-sector models
before selected 3-D continuum cases. It is not executed here.

### First major new production-physics candidate: WP04-TPM-001

**Transient poromechanics.** Test finite-rate deformation,
pressure-dependent consolidation, fluid storage and permeability evolution.
This is a strong candidate, not an automatic choice: SCI-MD-001 must compare
its capability with fines, swelling, machine dynamics, viscosity and lateral
instability.

### Later evidence-selected tasks

| Task | Scientific question | Evidence trigger |
|---|---|---|
| `WP04-UW-001` | Do unsaturated wetting and trapped air control first drip or early hydraulic residuals? | Synchronized pressure/flow/first-drip evidence inconsistent with the sharp-front limit. |
| `WP05-MSX-001` | Does a prescribed-hydraulics multispecies model explain grind and brew-ratio chemistry unavailable to one-solute kinetics? | Repeatable species/fraction trajectories showing aggregate-closure information loss. |
| `WP04-FIN-001` | Can mobile/deposited fines generate the required resistance evolution and recovery? | Credible capability region plus turbidity, retained-fines, deposition or recovery observations. |

## 4. Compute strategy

Analytical inversions and reduced models screen broad parameter spaces;
OpenFOAM tests whole-puck consequences and selected survivors. The 64 physical
CPU cores primarily support concurrent ensembles (normally two 32-rank cases
when I/O and memory permit). The GPU primarily supports pore-scale ensembles
and suitable accelerated reductions. Full 3-D runs are reserved for regions
where models disagree or instability boundaries occur. When realization
variability matters, a controlled ensemble is more informative than one
nominal expensive run.

## 5. Explicit non-priorities

The programme does not prioritize unrestricted tuning of the 9-bar
reconstruction; another single-realization pore-scale study; simultaneous
addition of many mechanisms; full 3-D simulation before reduced screening;
thermal coupling merely because it is implementable; repository-wide
refactoring; governance for its own sake; or cup-mass/extraction-yield
agreement as proof that internal mechanisms are correct.

## 6. Claim boundaries

```text
PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
PROTECTED_OR_HOLDOUT_SCORING:
  NOT_AUTHORIZED
EXPERIMENTAL_COMMISSIONING:
  NOT_AUTHORIZED
CURRENT_VALIDATION_GATE:
  ADDITIONAL_INDEPENDENT_DATA_REQUIRED
CURRENT_DISCOVERY_AND_MECHANISM_DISCRIMINATION_TASK:
  SCI-MD-001_AUTHORIZED_AND_ACTIVE
```

The independent-data gate limits validation claims; it does not prohibit the
authorized post-observation scientific discovery work.

## 7. Restart block

- Resolve the mutable EWP base with Git; SCI-MD-001 began from commit
  `ed77b4c66f85e8169a240bc95109aa181eb94f93`, tree
  `9448eb39f31255a3493a86f4e2758a782ac28b74`.
- Runtime Puckworks lock: commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`,
  tree `1d553e44ee2f7480a5df521560801b478618cc84`.
- Read-only locally available Puckworks evidence reference at task start:
  remote-tracking commit `bafafef3bc3c77599af8551d4e582aedb9b23f08`, tree
  `64ccf86aff4c90d1c513f1614b39e0823f64d6d7`; this is not the runtime lock
  and was not refreshed or executed.
- Active task: `SCI-MD-001` on
  `research/sci-md-001-pressure-grind-mechanism-discrimination`.
- Questions: required pressure-dependent resistance; cause of grind-sign
  reversal; transferable transient residual mechanisms.
- Claim ceiling: post-observation mechanism discrimination and synthetic
  diagnostics; physical validation not established.
- Expected outputs: frozen protocol, inverse requirements, capability matrix,
  reduced screens, bounded confirmations, figures and final result report.
- Always resolve live Git and dependency identities; recorded identities are
  historical anchors, not forever-current mutable state.

## 8. SCI-MD-001 completion disposition

SCI-MD-001 is `CORRECTED_PENDING_EXACT_HEAD_REVIEW`. The source requires
middle-, late-, and terminal-window 11/5 apparent-conductance ratios of
`0.389226`, `0.395294`, and `0.373506` (approximately an equivalent terminal
`C_app proportional to p^-1.174`; only under the fixed-geometry/viscosity
convention is this also `K_app proportional to p^-1.174`). Fixed Darcy,
fixed Darcy--Forchheimer, accepted
quasi-static compaction, static lateral paths, measured-basket-conditioned
machine dynamics, and plausible viscosity-only change are ruled out as
standalone explanations. Generic pressure-dependent resistance and the
relaxing-resistance surrogate are executed mathematical survivors. Swelling,
fines, evolving lateral localization, grind-to-structure mapping, and bimodal
extraction are not structurally excluded, but were not evaluated as
mechanism-specific models.

The selected disposition is `NO_NEW_PRODUCTION_PHYSICS_YET`; transient
poromechanics remains conditional because the executed P2 model is only a
one-state relaxing-resistance surrogate. XSV-ENS-001 is the next scientific
programme and should directly test whether plausible geometry, compression,
fabric, fines or realization changes can create the required 2.5--2.7-fold
axial-resistance increase while quantifying transverse and inertial closures.
See the
[SCI-MD-001 result](../validation/SCI_MD_001_PRESSURE_GRIND_MECHANISM_DISCRIMINATION_RESULT.md).
Pre-correction result-data commit/tree:
`a0f27d8ef65c618ed202fced8a9c980edbe803aa` /
`f7ed1b495245979ca1dc1dc176bbe63d0d0a40aa`. Corrected result authority:
`RESOLVE_FROM_EXACT_REVIEWED_HEAD_AND_TREE`; do not treat the pre-correction
identity as the current result authority.
