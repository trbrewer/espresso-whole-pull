# Puckworks Whole-Pull Multiscale Modeling and Simulation Strategy

> **Current execution note (3 September 2026):** SCI-MD-010 is
> `MERGED_COMPLETE`. L-HYD is
> `NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`; reduced E1 is
> `NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`; current full EWP E2 is
> `NOT_ADJUDICATED`. SCI-MD-011 is `MERGED_COMPLETE`, with disposition
> `SCI_MD_011_POROELASTIC_CLOSURE_TEST_BLOCKED_BY_IDENTIFIABILITY_EXECUTION_DOMAIN_OR_EQUIVALENCE_GAP`
> and architecture `NOT_ADJUDICATED`. Finite-Phi E2C is `BLOCKED`; universal
> P1 is `WRONG_PRESSURE_RESPONSE`; current full EWP is `NOT_VALIDATED`.
> SCI-ED-003 remains complete,
> Stage F/D remain unauthorized, and physical validation
> remains `NOT_ESTABLISHED`.
> SCI-MD-012 is complete as the bounded existing-data root diagnosis; its next
> action is `RETIRE_E2C_FROM_CURRENT_DEVELOPMENT_PRIORITY_NO_REPARAMETERIZATION_TEST`.
> SCI-ED-003 remains
> `CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`; its owner decision
> remains bounded and execution requires separate owner authorization.
> Stage F and Stage D are not authorized.

**Strategy version:** 1.7
**Date:** 4 August 2026
**Status:** Controlling technical strategy; current execution is governed by the data-first plan; physical validation is not established
**Supersedes:** strategy v1.6 and all earlier strategy versions
**Repository:** `trbrewer/espresso-whole-pull`; Puckworks remains the external evidence/model/data dependency
**Reviewed Puckworks dependency baseline:** repository `https://github.com/trbrewer/puckworks.git`; commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`; tree `1d553e44ee2f7480a5df521560801b478618cc84`; alignment status `REVIEWED_MAIN_AT_RECORDED_UTC_CUTOFF`. The dependency review, source dossier, calibration/comparison contract, deterministic R1 bridge, and governed WP-0.1R execution are complete.
**OpenFOAM implementation baseline:** `espresso_puck_whole_pull_reference_v0_1_4_openfoam12`, terminal freeze manifest `PASS`
**Execution baseline:** OpenFOAM Foundation 12 on the local Linux system; fresh 32-rank R0 reference run, exact-build reuse, standard ten-run qualification matrix, and terminal acyclic freeze finalization
**Primary whole-puck platform:** OpenFOAM Foundation 12 on the local 64-CPU Linux system, with 128 logical CPUs reported by the run environment
**Primary pore-scale platform:** Taichi/LBM on NVIDIA A100-SXM4-80GB-class GPU resources
**Scientific and software backbone:** Puckworks models, data, model cards, contracts, validation gates, rights records, and public product layer
**WP-0.1 disposition:** **IMPLEMENTATION PASS; BOUNDED CODE VERIFICATION PASS; NUMERICAL QUALIFICATION PASS; RELEASE PROVENANCE PASS; R0 FROZEN / QUALIFIED; PHYSICAL VALIDATION NOT ESTABLISHED**
**Current repository item:** `OWNER_DECISION_PENDING`; no solver, surrogate, or execution task is active

---

## Executive statement

The program now has an executable modular whole-pull solver spanning initially
dry wetting, first drip, prescribed or machine-coupled pressure, Darcy and
Darcy–Forchheimer flow, evolving effective permeability, static axial and
radial heterogeneity, conservative solute transport, spatial extraction
diagnostics, cup accumulation, and saturated quasi-static compaction.

WP03-001 completes the planned first-generation extension sequence before a
validation-led pivot. The limiting issue is no longer whether additional
equations can be implemented. It is whether competing mechanisms can be
identified from real espresso observations.

Compaction, swelling, dissolution-driven porosity, state-dependent
permeability, concentration-dependent viscosity, fines, damage, and channeling
can produce overlapping pressure, flow, cup-mass, TDS, extraction, and
spatial-maldistribution signatures. Adding several such mechanisms without
intervening data comparison would increase flexibility faster than physical
identifiability.

The next program tranche therefore develops source-specific validation
adapters, uncertainty-aware comparisons, sensitivity and identifiability
tools, residual decomposition, mechanism discrimination, ensemble execution,
and experimental design. This is solver development directed at evidence, not
a pause in solver development.

### Cross-solver closure-verification ladder

Taichi/LBM is the pore-scale and closure engine; Foundation OpenFOAM is the
whole-puck continuum consumer. Their interface must preserve explicit units,
pressure-gradient meaning, reference volume and area, porosity convention,
geometry/source identity, and closure provenance. Backend parity, analytical
code verification, closure-interface qualification, and physical validation
are distinct evidence levels.

The gated ladder is:

1. **XSV-TAICHI-001 — saturated hydraulic closure parity.** The first bounded,
   no-governing-physics cross-solver stage freezes synthetic geometries and a
   gross-area Darcy adapter, verifies NumPy/Taichi backend parity and an
   analytical channel, and tests unchanged OpenFOAM uniform, axial-series and
   radial-parallel closure consumption.
2. **XSV-TAICHI-002 — synthetic morphology and required-permeability-collapse
   screen.** Candidate only; not authorized.
3. **XSV-TAICHI-003 — optional same-geometry pore-scale OpenFOAM/Taichi
   comparison.** Future possibility only; not authorized.

Progression is evidence-gated and requires fresh human authority. None of
these stages supplies independent physical data, represents real-coffee
morphology by default, authorizes a new mechanism, or raises the claim
ceiling. `PHYSICAL_VALIDATION = NOT_ESTABLISHED`.

XSV-TAICHI-001 defines the first bounded cross-solver closure-verification
stage. Its live execution and disposition are governed by the
[current project state](../PROJECT_STATE.md), the
[program handoff](../PROGRAM_STATE_AND_FORWARD_PLAN.md), its dedicated
[verification authority](../verification/XSV_TAICHI_001_SATURATED_HYDRAULIC_CLOSURE_PARITY.md),
and its machine result at
`verification/cases/xsv_taichi_001/XSV_TAICHI_001_RESULT.json` when present.
This strategy intentionally carries no mutable result, test total, PR head or
merge identity.

The next governing-physics increment will be selected from observed residuals
and information gaps rather than from implementation convenience. General
physical validation remains `NOT_ESTABLISHED`.

### Completed first-generation extension sequence

WP02-001 through WP02-004 and WP03-001 are complete. They added optional
dissolution-indexed effective permeability, machine/headspace compliance and
an emergent basket-pressure operating point, saturated Darcy–Forchheimer
resistance, static radial flow focusing with zone-resolved extraction, and
saturated quasi-static compaction.

WP03-001 changes mechanical porosity and permeability under effective stress,
composes with the machine operating-point calculation, and is inactive during
wetting. It uses a fixed reference mesh, does not solve solid displacement,
and does not couple mechanical porosity to transport storage. Transient Biot
storage, plasticity, hysteresis, swelling, fines, damage, and dynamic
channeling remain outside that branch.

### Historical Version 1.5 decision

Version 1.5 selected WP02-001 under issue #18 as the first evidence-led WP-0.2
mechanism and identified machine/headspace coupling as its runner-up. That
sequence is now historical: WP02-001, machine coupling, Darcy–Forchheimer
integration, radial heterogeneity, and WP03-001 have all been completed.

Version 1.4 recorded the transition to a clean public solver repository. It changed repository governance, public provenance, CI, licensing documentation, and dependency workflow only. It did not change governing physics, scientific configuration, calibration, numerical schemes, validation thresholds, the scientific roadmap, or the claim ceiling. Exact archival v0.1.4 bytes remain offline; public development begins from the sanitized derivative `v0.1.4-public.1`.

Version 1.0 established the program pivot: build a new, coupled, multiscale, whole-pull espresso simulation rather than indefinitely postponing integration behind pore-scale qualification or reducing the effort to an orchestration layer around existing models. Version 1.1 recorded the first successful end-to-end OpenFOAM execution. Version 1.2 recorded successful numerical hardening and the standard ten-run qualification campaign.

The remaining WP-0.1 release-engineering milestone has now also been achieved.

On 27 July 2026, `espresso_puck_whole_pull_reference_v0_1_4_openfoam12` completed a fresh Foundation OpenFOAM 12 `./Allrun`, the standard `./Allverify`, post-qualification finalization, and terminal manifest generation on the local Linux system. The terminal manifest reports:

```text
implementation status             PASS
code verification status          PASS
numerical qualification status    PASS
release provenance status         PASS
reference qualification status    PASS
reference freeze status           FROZEN / QUALIFIED
WP milestone                      WP-0.1H_COMPLETE
governing-physics change          false
physical validation status        NOT_ESTABLISHED
next scientific milestone         WP-0.1R
```

Version 0.1.4 was deliberately a no-governing-physics-change release. The solver source and reduced-twin mathematics matched the qualified v0.1.3 contract after normalization of version-only tokens; scenario physics projections, Make contracts, initial fields, and discretization dictionaries passed all **28 of 28** no-physics-change comparisons. The release changed provenance, finalization, acceptance and operational defaults—not the bounded R0 equations, calibration, or closure parameters.

The fresh v0.1.4 reference calculation reported:

```text
first drip                         4.711696185 s
final outlet flow                  1.482675972 mL/s
cup water mass at 30 s            36.170176862 g
cup dissolved-solute mass          4.787690621 g
total beverage mass at 30 s       40.957867483 g
time to 40 g                       29.374480171 s
cumulative TDS                    11.689306389 %
extraction yield                  23.938453103 %
retained water                     9.190476190 g
retained dissolved solute          0.192063112 g
remaining extractable material     0.619392295 g
maximum liquid residual            6.04e-16 kg
maximum solute residual             2.60e-13 kg
maximum concentration            174.914487 kg/m3
```

All required single-run gates passed, including explicit concentration-capacity, remaining-inventory, retained-water-capacity, and cumulative-mass monotonicity gates. The analytical first-drip, uniform Darcy-flow, wedge-volume, and retained-water checks agree to approximately machine precision. The layered pressure fixture retained its nontrivial pressure exercise and independent flow/probe checks. OpenFOAM/B0 parity passed for every required bounded-model output.

The standard qualification campaign again completed ten simulations and passed all nine aggregate gates. The tested time-step, mesh, and MPI sensitivity conclusions therefore remain controlling. The largest `0.020 s` versus `0.005 s` difference was approximately 0.124%, the largest reference-versus-fine mesh difference approximately 0.560%, and the largest 1/16/32/64-rank output difference approximately `2.23e-9` relative. Thirty-two MPI ranks remained the fastest measured routine configuration for the 131,072-cell reference case.

The release also completed the missing provenance work. The terminal manifest binds:

- 106 source-package files;
- 19 immutable scientific-input files;
- the exact compiled solver executable and its portable archived copy;
- the reference traces, acceptance, field index, timings and run status;
- 339 reconstructed field files;
- all ten qualification acceptance reports;
- the qualification matrix and freeze-finalization record;
- 20 top-level controlling artifacts.

Key identities include:

```text
aggregate source SHA-256
182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e

compiled and archived solver SHA-256
ada45a5440d08ae8da1a57d65cdf511748a340cd09a045121c59ea83a3d8d6d7

scientific-input bundle SHA-256
d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a

reconstructed-field aggregate SHA-256
9468de231dc2f50ed1db158a0a5520a16e505818f52f44b85d51426232543bfd

controlling-artifact aggregate SHA-256
044f6369014f202dde1755879f3a93d60c7bc5c007358c769e24dacca14d2229
```

The acyclic sequence is now complete:

```text
source package and scientific inputs
                ↓
exact compiled solver executable
                ↓
reference and fixture results
                ↓
standard numerical qualification
                ↓
finalized acceptance and run status
                ↓
terminal freeze manifest generated last.
```

The terminal manifest—not intermediate preterminal status text—is the final authority. One benign diagnostic-classifier false positive remains in the finalized run status: the empty JSON member `"failed_comparisons": []` was listed as a detected issue. It does not represent a failed comparison, did not affect any gate, and does not justify mutating or regenerating the frozen baseline. The classifier should be corrected on the next development branch.

### Historical Version 1.5 immediate sequence

The following paragraphs retain the Version 1.5 sequence for chronology. Every
listed implementation item has since been completed or superseded.

WP-0.1H was complete at the implementation, code-verification, numerical-qualification, and immutable-provenance levels. At that time, this changed the program’s critical path from another R0 release to preserving and registering the qualified baseline and testing the architecture against source-linked evidence.

The immediate program sequence is:

1. merge the reviewed WP01R-006 decision and close issue #8;
2. implement issue #18 as one optional, disabled-by-default saturated effective-permeability branch;
3. verify the independent closed form, locked-Puckworks parity, disabled-branch regression, uniform-pressure fixture, and conservation;
4. execute the unchanged 9-bar source-linked reconstruction;
5. execute one predeclared 8-bar, no-retuning, same-campaign transfer comparison;
6. use the resulting multi-pressure residual—not implementation convenience—to decide whether the next mechanism is machine/headspace coupling, fuller poroelasticity, or another ranked candidate.

The model program continues to combine four capabilities:

1. **A whole-puck OpenFOAM multiphysics solver** for initially dry wetting, pressure-driven porous flow, transport, extraction, retained inventories and progressively evolving structure.
2. **High-resolution Taichi/LBM simulations** for pore-resolved hydraulics, morphology, fines-scale effects, dispersion, residence time, capture, clogging and constitutive closure generation.
3. **Puckworks integration** as the authoritative knowledge, evidence, data, validation, semantic-contract, provenance and model-comparison layer.
4. **Reduced models and surrogates** for independent verification, sensitivity analysis, uncertainty propagation, design exploration and eventual engineering optimization.

The controlling development philosophy is now:

> **Preserve the frozen whole-pull baseline, confront it with source-linked evidence, and extend it one mechanism at a time only when a named residual, experiment or engineering decision requires the added physics.**

### Why the validation pivot occurs after WP03-001

The solver now contains independently selectable hydraulic and structural
hypotheses, and its analytical, regression, conservation, timestep, mesh, and
MPI evidence is sufficiently mature for real-data confrontation. For the
tested cases, discretization and solver uncertainty are generally smaller than
unresolved uncertainty in real permeability, wetting, extraction, machine
response, structural evolution, and transfer.

The post-WP03-001 bottleneck is therefore an
`EPISTEMIC_IDENTIFIABILITY_LIMIT`, not a computational or architectural block.
Compaction, swelling, dissolution-driven porosity change, state-dependent
permeability, concentration-dependent viscosity, fines deposition or release,
and damage or channel formation can all contribute to declining flow, changing
basket pressure, altered cup production, TDS, extraction yield, and spatial
maldistribution. A model that can fit those observations with several
alternative mechanisms is not necessarily better identified or more
predictive.

Unrestricted mechanism accumulation or fitting would promote equifinality
rather than physical understanding. Validation and mechanism discrimination
now have greater information value than another immediate physics branch.
Future physics remains technically possible; evidence will determine which
branch is load-bearing.

### Program cadence after WP03-001

> **After WP03-001, the program must not add two new evolving-puck
> governing-physics mechanisms consecutively without an intervening comparison
> against relevant real espresso evidence.**

This is human program-development guidance. It is not a CI gate, a
static-validation requirement, a merge blocker, or a new repository-governance
framework. It does not prohibit numerical corrections, scientific bug fixes,
source adapters, validation tooling, sensitivity or uncertainty analysis,
identifiability work, or bounded improvements needed to compare an existing
model with measured observables.

The operating cadence is:

```text
verify implementation
-> compare with evidence
-> decompose residuals
-> select one mechanism
-> implement and verify
-> return to evidence
```

## 1. Why Version 1.3 is a milestone update

### 1.1 What the 0.x program accomplished

The earlier program produced substantial, reusable foundations:

- a high-performance Taichi D3Q19 TRT lattice-Boltzmann implementation;
- one-field streaming and packed active-brick storage;
- a successful full 58 mm, 50 µm-class GPU production calculation;
- solver verification, low-Mach and low-Reynolds controls, memory accounting, convergence controls and export infrastructure;
- fixed-geometry grid studies and progressively more disciplined SVE campaigns;
- evidence that porosity alone does not define hydraulic representativeness;
- evidence that nested internal crops and their imposed periodic closure can create a methodological ambiguity;
- an M1 geometry-method preflight;
- a B0 continuum numerical-verification framework for pressure nodes, Darcy resistance, filling, conservative transport and solid–liquid–cup inventory;
- an A1 ingestion design and manufactured self-test;
- increasingly strong Puckworks contracts, model cards, data manifests, validation gates and linked-model products.

These are not discarded. They remain verified or partially verified components, test ideas and evidence sources of the new architecture.

### 1.2 What Versions 1.0–1.2 changed

Version 1.0 corrected two earlier strategic extremes:

- treating synthetic morphology qualification, RVE/SVE promotion and new measured-anchor campaigns as prerequisites for any whole-process integration; and
- treating the future program primarily as orchestration of existing Puckworks models rather than as a new solver-development effort.

It established three controlling truths:

1. **A new whole-pull solver is required.** No registered Puckworks component currently represents a validated, spatially resolved, whole-process machine-to-cup simulation.
2. **Puckworks must remain authoritative.** The new solver must use the repository’s models, datasets, evidence levels, quantities, rights and validation gates rather than inventing an independent scientific universe.
3. **Progressive construction is essential.** The model must begin with a complete but bounded reference shot and add physics in verified increments.

Version 1.1 recorded the first successful Foundation-12 execution. Version 1.2 recorded successful analytical and reduced-twin verification, heterogeneous-pressure exercise, mesh/time-step/rank qualification and the standard ten-run `Allverify` campaign.

### 1.3 What v0.1.4 and WP-0.1F have now established

The v0.1.4 fresh-package run and terminal manifest establish that the bounded whole-pull architecture is not only numerically qualified but also immutably and reproducibly bound:

- Foundation OpenFOAM 12 compiles and runs the custom solver from a clean package;
- future timestamps, environment paths, explicit headers and build inputs are checked automatically;
- the exact compiled executable is copied, hashed and reused throughout standard qualification;
- the 2D axisymmetric wedge case is generated deterministically;
- the exact straight-sided-wedge scale reproduces the nominal cylindrical volume;
- the pressure ramp is integrated exactly and first drip matches the closed-form result;
- the uniform Darcy flow matches its analytical reference;
- a heterogeneous layered fixture requires nonzero pressure iterations and reproduces independent flow and pressure references;
- OpenFOAM and the independent B0 twin agree on every required bounded-model output;
- the selected time-step and mesh sensitivity gates pass;
- 1-, 16-, 32- and 64-rank outputs are effectively equivalent;
- concentration, saturation, retained water, extractable inventory and cumulative masses satisfy explicit bounds;
- the 30 s reference shot remains conservative after all finalization changes;
- all expected final fields and reconstructed histories are present;
- all ten standard qualification simulations and all nine aggregate gates pass;
- all 28 no-governing-physics comparisons against qualified v0.1.3 pass;
- an acyclic terminal manifest binds the source package, exact executable, scientific inputs, reference outputs, field archive, qualification evidence and final statuses.

The project therefore has a **frozen and numerically qualified machine-to-cup computational spine** for the declared R0 equations.

### 1.4 What remains unestablished after WP03-001

The completed freeze does not establish:

- formal source-specific reconstruction of Foster, Waszkiewicz, Cameron or another extraction source;
- independently measured permeability, wetting, extraction or dispersion parameters for R0;
- physical validation of first drip, flow, TDS or extraction yield for a protected real-coffee experiment;
- transfer across coffees, grinders, baskets, machines or recipes;
- validated swelling, compaction, fines migration, clogging or channeling;
- independent physical validation of machine/headspace/basket coupling;
- engineering optimization or taste prediction.

The approximately 40 g result remains a calibration-class endpoint because saturated permeability is the declared R0 hydraulic scale parameter. The extraction rate, extractable fraction, effective dispersion and concentration ceiling remain engineering assumptions for WP-0.1.

Immutable provenance strengthens the evidence record; it does not transform a calibrated scenario into independent validation.

### 1.5 Historical strategic consequence at Version 1.3

The program’s critical path has advanced:

```text
successful whole-pull implementation       [ACHIEVED]
→ numerical hardening and qualification    [ACHIEVED]
→ no-physics-change immutable freeze        [ACHIEVED]
→ archive, reference specification and
  governed Puckworks registration           [IMMEDIATE]
→ source-linked WP-0.1R reconstruction      [IMMEDIATE SCIENTIFIC MILESTONE]
→ evidence-selected hydraulic/machine work
→ one-mechanism-at-a-time physical expansion
→ independent holdouts and transfer.
```

The principal risks are now:

- mutating the only frozen evidence directory;
- confusing a frozen numerical baseline with physical validation;
- overfitting R1 by consuming all source observations as calibration inputs;
- adding new physics before the first source-linked residual is understood;
- integrating code into Puckworks without preserving the exact artifact, evidence and validity contracts.

Version 1.3 therefore treated R0 as a protected baseline and WP-0.1R as the
next scientific test. That chronology is preserved here as historical context;
the current active tranche is post-WP03-001 validation and mechanism
discrimination.

## 2. Program mission, objectives, and definition of success

### 2.1 Mission

Develop the most complete and scientifically defensible open espresso-process simulation platform practicable with the available evidence and compute resources, combining:

- high spatial and temporal resolution;
- a whole-puck, whole-shot multiphysics calculation;
- high-resolution pore-scale closure generation;
- model and data integration through Puckworks;
- transparent uncertainty and evidence limits;
- engineering outputs relevant to recipes, machines, baskets, filters, grinders, and process control.

### 2.2 Primary objectives

The program will:

1. **Simulate the whole espresso process.** Represent machine delivery, initially dry wetting, saturated flow, transport, extraction, cup accumulation, and progressively evolving puck state.
2. **Use the best available evidence.** Parameterize, compare, calibrate, and validate against data and model outputs already recorded in Puckworks before commissioning new evidence.
3. **Create new coupled physics.** Extend beyond existing paper implementations by coupling stages that are currently separate and by introducing spatially resolved, conservative state evolution.
4. **Exploit multiscale computation.** Use Taichi/LBM where pore geometry matters and OpenFOAM where whole-puck multiphysics and evolving fields matter.
5. **Support engineering decisions.** Progress from one reference shot to sensitivity, robust optimization, component comparison, and control-profile design.
6. **Expose disagreement and uncertainty.** Retain alternative closures and mechanisms instead of hiding them inside one fitted time-varying parameter.
7. **Return all work to Puckworks.** Code, adapters, reduced results, validation reports, data references, and documented gaps become part of the repository.

### 2.3 What would make the approach genuinely innovative

A claim of being “groundbreaking” or “the most advanced” should be earned, not asserted. The program should aim to distinguish itself through the combination of:

- **machine-to-cup coupling** in one transient computation;
- **initially dry wetting followed by saturated flow** rather than beginning after first drip;
- **spatially resolved extraction and evolving resistance** rather than only cup endpoints;
- **pore-resolved closure calculations embedded in a whole-puck framework**;
- **explicit alternatives for swelling, poroelastic compaction, fines migration, dissolution, rheology, and channeling**;
- **model/data provenance at every field and closure**;
- **full liquid and solute conservation**;
- **a progressive path from axisymmetric reference shots to non-axisymmetric basket and channeling simulations**;
- **validation against multiple repository evidence families, not one paper or one endpoint**;
- **reproducible open outputs suitable for ParaView, model comparison, and public scrutiny**.

A formal literature and capability benchmark against published SPH, LBM, finite-volume, extraction, and poroelastic espresso models will be required before making a public superlative claim.

### 2.4 Definition of ultimate success

The mature system should accept:

```text
coffee state
+ grinder and measured or inferred PSD
+ dose and packing/tamp state
+ basket/filter geometry
+ machine pressure/flow/temperature control
+ shot termination rule
```

and predict, with declared uncertainty and validity:

```text
machine and bed pressure nodes
+ wetting and first drip
+ spatial saturation and flow
+ beverage flow and mass
+ TDS and extraction yield histories
+ selected species
+ porosity, permeability, deformation, fines and channel indicators
+ retained liquid and post-shot state
+ sensitivity and design recommendations
```

The model becomes an engineering tool only when it performs usefully on protected holdouts and rejects unsupported extrapolation.

---

## 3. The unified multiscale architecture

### 3.1 Four connected layers

```text
┌────────────────────────────────────────────────────────────────────┐
│ Puckworks evidence, models, data, contracts, gates and provenance │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                    canonical state / closures
                                │
┌───────────────────────────────▼────────────────────────────────────┐
│ OpenFOAM whole-puck multiphysics engine                           │
│ machine → wetting → flow → evolution → extraction → cup          │
└───────────────────────┬───────────────────────────┬───────────────┘
                        │                           │
                 closure requests             validation fields
                        │                           │
┌───────────────────────▼────────────────┐   ┌──────▼────────────────┐
│ Taichi/LBM pore-scale engine           │   │ Reduced verification  │
│ morphology, K, dispersion, fines, RTD  │   │ twins and surrogates │
└────────────────────────────────────────┘   └───────────────────────┘
```

### 3.2 Puckworks: knowledge and evidence plane

Puckworks provides:

- model cards and source interpretation;
- registered model implementations;
- typed state and quantity semantics;
- data manifests and evidence levels;
- scientific gates;
- rights-aware execution;
- scenario and product code;
- experimental-gap definitions;
- comparison and public-value outputs.

The new solver will consume this information and return:

- new model components or backends;
- closure artifacts;
- scenario configurations;
- verification and validation gates;
- reduced result bundles;
- field-data checksums;
- explicit data/model/theory gaps.

### 3.3 OpenFOAM: primary whole-puck engine

OpenFOAM is not a fallback. It is the primary system-scale solver because it can support:

- transient porous flow;
- axisymmetric and three-dimensional basket geometry;
- scalar and species transport;
- source terms and reactions;
- heat transfer;
- variable properties;
- Lagrangian particles;
- dynamic porosity and resistance;
- user-defined constitutive laws;
- local CPU parallelism and ParaView-native field output.

The initial baseline is Foundation OpenFOAM 12 on the existing local 64-CPU Linux system. A version change requires a reproducibility review rather than an automatic upgrade.

### 3.4 Taichi/LBM: primary pore-scale and closure engine

Taichi/LBM owns the questions for which explicit geometry matters:

- permeability and permeability tensor;
- pore-throat bottlenecks;
- local velocity heterogeneity;
- residence-time distributions;
- dispersion;
- fines capture, release and clogging;
- morphology sensitivity;
- onset of local channel pathways;
- high-resolution solver-to-continuum closure development.

Taichi may also perform selected full-puck hydraulic calculations at tens-of-microns resolution, but it is not required to carry all chemistry and evolving structure over the full 58 mm puck.

### 3.5 Reduced verification twins and surrogates

A reduced model remains essential for:

- independent numerical verification;
- fast regression tests;
- parameter and sensitivity studies;
- closure inspection;
- uncertainty propagation;
- eventual optimization.

The existing B0 numerical architecture should become a verification twin and reduced backend, not a competing detached project.

### 3.6 One product, modular internals

The mature user-facing product should offer one scenario and one result package, but the internals must retain:

- separate physics modules;
- alternative closures;
- explicit evidence labels;
- replaceable backends;
- provenance and uncertainty;
- no silent model averaging.

This is how the program can incorporate “as much physics and chemistry as possible in a single model” without producing an untestable monolith.

---

## 4. First flagship milestone: WP-0.1 frozen and qualified

### 4.1 Purpose and final WP-0.1H disposition

The first flagship milestone was intended to establish a minimal but complete computational path from pressure application to the cup, qualify the bounded equations numerically, and preserve the accepted implementation as a reproducible baseline before richer physics were added. That milestone is now complete.

Controlling identifiers are:

```text
project package:
  espresso_puck_whole_pull_reference_v0_1_4_openfoam12

solver:
  espressoWholePullFoam 0.1.4

run status:
  ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json

reference acceptance:
  ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json

qualification report:
  ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json

terminal freeze manifest:
  ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json

scenario:
  reference_R0_20g_58mm_9bar
```

Final milestone disposition:

| Dimension | Status |
|---|---|
| OpenFOAM Foundation 12 compilation | PASS |
| Clean case generation and mesh construction | PASS |
| Full mesh topology and geometry checks | PASS |
| Corrected wedge-to-cylinder equivalence | PASS |
| Exact pressure-ramp/first-drip integration | PASS |
| Uniform analytical Darcy-flow check | PASS |
| Layered heterogeneous-pressure fixture | PASS |
| OpenFOAM/B0 reduced-twin parity | PASS |
| Reference R0 execution to 30 s | PASS |
| Field reconstruction and final field set | PASS |
| Liquid and solute conservation | PASS |
| Explicit bounded-state gates | PASS |
| Explicit cumulative-mass monotonicity gates | PASS |
| Time-step qualification | PASS under declared thresholds |
| Mesh qualification | PASS under declared thresholds |
| 1/16/32/64-rank equivalence | PASS |
| Standard ten-run `Allverify` matrix | PASS; 9/9 aggregate gates |
| No-governing-physics verification | PASS; 28/28 comparisons |
| Exact reference executable binding | PASS |
| Release provenance | PASS |
| Immutable R0 freeze | **FROZEN / QUALIFIED** |
| Source-data reconstruction | NOT YET ESTABLISHED |
| Independent physical validation | NOT ESTABLISHED |

### 4.2 Canonical engineering reference scenario R0 as frozen

| Quantity | Frozen reference definition |
|---|---|
| Basket nominal diameter | 58 mm |
| Coffee dose | 20 g |
| Dry bed depth | 9.011660896 mm, derived from dose, area, particle-density assumption and porosity |
| Initial porosity | 0.40 |
| Initial state | Dry intergranular pore volume represented by the sharp-front wetting model |
| Temperature | Fixed and uniform at 93 °C |
| Inlet control | Bed-top pressure ramp from 0 to 9 bar gauge over 3 s |
| Outlet | 0 bar gauge at the declared basket-bottom node |
| Simulated duration | 30 s |
| Geometry | Straight-sided 5° axisymmetric wedge of the 58 mm puck |
| Reference mesh | 256 axial × 512 radial × 1 wedge cell; 131,072 total cells |
| Main-run time step | 0.02 s |
| Routine MPI count | 32 ranks |
| Qualification time steps | 0.020, 0.010 and 0.005 s |
| Qualification meshes | 128×256, 256×512 and 512×1024 |
| Qualification ranks | 1, 16, 32 and 64 for R0; 1 and 16 for the layered fixture |
| Wetting | Sharp-front Darcy storage with exact piecewise-linear pressure integration |
| Saturated hydraulics | Uniform Darcy permeability; permeability is the declared R0 hydraulic calibration parameter |
| Extraction | One representative soluble inventory with spatial transport and exact inventory accounting |
| Primary outputs | First drip, flow, cup water and solute, total beverage mass, TDS, EY, retained inventories, balances and spatial fields |

The case is an engineering reference scenario, not a claim that all parameters describe one measured coffee, grinder, puck and machine experiment.

### 4.3 Frozen R0 outputs

| Output | v0.1.4 frozen result |
|---|---:|
| First drip | **4.711696185 s** |
| Final outlet volume flow | **1.482675972 mL/s** |
| Cup water mass at 30 s | **36.170176862 g** |
| Cup solute mass at 30 s | **4.787690621 g** |
| Total beverage mass at 30 s | **40.957867483 g** |
| Time to 40 g | **29.374480171 s** |
| Cumulative TDS | **11.689306389%** |
| Cup extraction yield | **23.938453103%** |
| Retained water in the puck | **9.190476190 g** |
| Retained dissolved solute | **0.192063112 g** |
| Remaining extractable material | **0.619392295 g** |
| Maximum dissolved concentration | **174.914486977 kg/m³** |
| Maximum liquid-balance residual | **6.0368 × 10⁻¹⁶ kg** |
| Maximum solute-balance residual | **2.5980 × 10⁻¹³ kg** |
| Maximum estimated saturated pore Courant number | **0.797087** |

The total beverage mass is cup water plus exported dissolved solute. Retained liquid and retained dissolved material remain separately visible and are not silently added to the cup.

The tiny v0.1.3-to-v0.1.4 differences in parallel floating-point reductions are far below the qualified MPI-equivalence tolerance and do not represent a physics change.

### 4.4 Mesh, field and execution quality

The frozen reference run used 131,072 cells, comprising 130,816 hexahedra and 256 prisms at the collapsed axis. `checkMesh -allGeometry -allTopology` reported:

| Metric | Result | Interpretation |
|---|---:|---|
| Number of mesh regions | 1 | Correct connected domain |
| Maximum aspect ratio | 1.6059 | Excellent |
| Maximum non-orthogonality | 0° | Excellent |
| Maximum skewness | 0.3308 | Excellent |
| Minimum cell determinant | 0.8940 | Well-posed cells |
| Overall result | `Mesh OK` | PASS |

The straight-sided-wedge scale is `72.0914664839846`. The scaled mesh volume agrees with the nominal cylindrical puck volume to a relative error of approximately `2.28e-15`.

The field index contains 339 files, covers the reconstructed integer time directories from 0 through 30 s, and records no missing final fields. Eleven expected final fields are present: `p`, `U`, `darcyFlux`, `saturation`, `wetMask`, `porosity`, `permeability`, `hydraulicMobility`, `dissolvedConcentration`, `remainingExtractable`, and `localExtractionRate`.

The fresh 32-rank `Allrun` recorded 18 passing stages with a summed duration of approximately 26.54 s. Major stages included approximately 8.66 s to clean-build the solver, 5.21 s for the parallel reference solve, 3.90 s to reconstruct all saved field times, and 4.23 s for the complete mesh check.

### 4.5 Numerical hardening and acceptance controls completed

#### A. Straight-sided wedge scaling

The full-cylinder multiplier is:

\[
\text{sectorScale}=\frac{2\pi}{\sin\theta},
\]

rather than `360/θdeg`. The analytical flow, scaled volume and retained pore-water tests pass to approximately machine precision.

#### B. Exact pressure-ramp integration

The sharp-front update integrates the positive piecewise-linear pressure history exactly and locates breakthrough within the step. First drip agrees with the closed-form reference of `4.711696185231869 s` to approximately `1.15e-14 s`.

#### C. Heterogeneous pressure exercise

The layered fixture requires nonzero pressure iterations and matches an independent discrete one-dimensional flow solution and two pressure probes. This provides a meaningful pressure-equation stress test beyond the exact uniform R0 field.

#### D. Explicit bounded-state and monotonicity gates

The frozen acceptance contract now requires:

- `0 ≤ saturation ≤ 1`;
- nonnegative concentration;
- concentration no greater than the declared 180 kg/m³ capacity plus tolerance;
- remaining extractable inventory between zero and the initial inventory;
- retained water between zero and the saturated pore-water capacity;
- nondecreasing cumulative inlet water;
- nondecreasing cumulative cup water;
- nondecreasing cumulative cup solute;
- finite traces and declared residual/iteration limits.

Every required gate passed.

#### E. Operational and provenance hardening

The package:

- uses explicit Foundation 12 headers and source-root discovery;
- detects and normalizes unsafe future timestamps automatically;
- performs clean `wclean`/`wmake` builds;
- streams stage logs while preserving complete files;
- records stage timings, source and executable hashes;
- writes uncompressed binary fields;
- classifies `FOAM_SIGFPE` enablement as informational;
- binds the exact compiled executable to the reference and standard qualification;
- emits machine-readable status on controlled success and failure;
- finalizes acceptance only after standard qualification passes;
- generates the terminal freeze manifest last.

### 4.6 B0 parity and analytical verification

All required OpenFOAM/B0 parity gates passed. First drip and final flow agree at approximately machine precision. Cup and inventory outputs generally agree at relative differences of order `1e-11` to `1e-10`, comfortably within the declared 0.5% inventory tolerance.

This establishes code verification for the bounded WP-0.1 equations and implementation. It does not validate the shared physical assumptions against real coffee.

### 4.7 Standard qualification campaign

The standard campaign completed ten unique runs and nine aggregate gates:

| Test family | Result | Largest observed difference |
|---|---|---:|
| All individual runs | 10/10 PASS | — |
| `Δt=0.020` versus `0.005 s` | PASS | 0.1242%, remaining extractable mass |
| `Δt=0.010` versus `0.005 s` | PASS | 0.0564%, retained dissolved solute |
| 128×256 versus 512×1024 | PASS | 1.6835%, retained dissolved solute |
| 256×512 versus 512×1024 | PASS | 0.5596%, retained dissolved solute |
| 16 versus 1 rank | PASS | approximately 2.17e-9 relative |
| 32 versus 1 rank | PASS | approximately 2.09e-9 relative |
| 64 versus 1 rank | PASS | approximately 2.23e-9 relative |
| Layered fixture: 16 versus 1 rank | PASS | approximately 9.60e-13 relative for flow |

The tested matrix establishes bounded sensitivity under the predeclared WP-0.1H tolerances. It should not be described as a formal asymptotic-order study for every state variable. Retained dissolved solute is the most mesh-sensitive reported quantity; cup-level outputs are much less sensitive.

### 4.8 Rank efficiency and routine execution policy

Measured solver-stage times for the 256×512 reference mesh at `Δt=0.01 s` in the standard v0.1.4 matrix were:

| MPI ranks | Solver time |
|---:|---:|
| 1 | 220.90 s |
| 16 | 12.66 s |
| 32 | **8.00 s** |
| 64 | 8.87 s |

Thirty-two ranks remain the best tested routine setting for the reference mesh. Sixty-four ranks are valid but slower for this small case because communication overhead exceeds the additional compute benefit. The fine 512×1024 mesh should continue to use 64 ranks unless a dedicated scaling study indicates otherwise.

These are single-run operational observations on the current machine, not a universal strong-scaling law.

### 4.9 Calibration and physical interpretation

The approximately 40 g endpoint is not an independent prediction because saturated permeability is the R0 hydraulic calibration parameter. The correct interpretation is:

> The frozen WP-0.1 equations, calibrated hydraulic scale and engineering extraction closure produce a numerically qualified, conservative reference calculation under the bounded R0 assumptions.

The 11.69% TDS and 23.94% extraction yield are internally consistent but depend on the present extraction rate, extractable fraction, dispersion and concentration ceiling. They must not be represented as validated real-coffee chemistry until source-linked reconstruction and held-out comparison are completed.

First drip is a genuine model output and is numerically exact for the declared sharp-front closure, but the closure and wetting permeability have not yet been physically validated against an independent real-coffee measurement.

### 4.10 Immutable freeze and provenance completed

Version 0.1.4 resolves the v0.1.3 metadata and circular-hash defects without changing governing physics.

The terminal manifest verifies:

- 106 source-package files;
- 19 immutable scientific-input files;
- the runtime and archived executable as byte-identical;
- exact executable reuse throughout standard qualification;
- four primary reference acceptance artifacts;
- 339 reconstructed field files;
- ten qualification acceptance reports;
- three finalization bindings;
- 20 top-level controlling artifacts;
- zero provenance-verification failures.

The controlling identities are:

| Identity | SHA-256 |
|---|---|
| Aggregate source package | `182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e` |
| Compiled/archived solver | `ada45a5440d08ae8da1a57d65cdf511748a340cd09a045121c59ea83a3d8d6d7` |
| Scientific-input bundle | `d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a` |
| Reconstructed-field aggregate | `9468de231dc2f50ed1db158a0a5520a16e505818f52f44b85d51426232543bfd` |
| Controlling-artifact aggregate | `044f6369014f202dde1755879f3a93d60c7bc5c007358c769e24dacca14d2229` |

The terminal manifest is the final authority. Intermediate artifacts that state the terminal manifest is pending reflect their proper position in the acyclic generation sequence and must not be rewritten after the manifest is created.

One benign classifier issue remains: an empty `"failed_comparisons": []` member appears in `detected_issue_lines`. This is a presentation defect only. It should be fixed in the next development branch, but the frozen v0.1.4 records should not be regenerated solely for that reason.

### 4.11 Data-linked reference scenario R1

The next scientific reconstruction remains distinct from R0 and should reproduce the best-defined Waszkiewicz rig context rather than forcing it into the 20 g engineering reference:

```text
18.5 g dose
58 mm basket
9 bar basket-pressure case
source-specific coffee, grind and calibration constants
source-defined pressure and flow nodes
```

R1 is the principal pressure–flow reconstruction and comparison case. It should now begin from a new development branch using the frozen R0 executable, state contracts and verification fixtures as protected regression evidence.

R1 must predeclare:

- the source observations used for parameter setting;
- the outputs reserved for comparison or holdout;
- pressure-node and downstream-resistance definitions;
- uncertainty and digitization treatment;
- rights and provenance;
- which differences represent model-form error rather than numerical error.

### 4.12 Explicit current non-goals

WP-0.1 does not yet claim:

- explicit fines migration;
- spontaneous channel formation;
- validated swelling or compaction;
- multiple chemical species;
- transient heat transfer;
- gas/CO₂ effects;
- non-axisymmetric basket defects;
- universal transfer across coffees, grinders or machines;
- taste prediction;
- final engineering optimization.

The software interfaces should remain additive so these mechanisms can be introduced without replacing or mutating the frozen conserved state and output contracts.

## 5. Governing state and equations for the first model

### 5.1 Minimum spatial state

The implemented WP-0.1 whole-puck solver carries the following minimum spatial state, with some fields static in the first release and designed to become dynamic later:


a. pore pressure

\[
p(r,z,t)
\]

b. liquid saturation or wet-state indicator

\[
S(r,z,t)
\]

c. Darcy/superficial velocity

\[
\mathbf{u}(r,z,t)
\]

d. dissolved-solids concentration

\[
c_\ell(r,z,t)
\]

e. extractable solid inventory

\[
m_s(r,z,t)
\]

f. porosity and permeability

\[
\phi(r,z,t), \qquad \mathbf{K}(r,z,t)
\]

In WP-0.1, porosity and permeability are present as spatial fields but are static and uniform in the executed R0 case. Their field-based representation is retained so that later pressure-, saturation-, structure- and fines-dependent updates are additive rather than architectural rewrites.

### 5.2 Liquid mass conservation

A general form is:

\[
\frac{\partial (\phi S \rho_\ell)}{\partial t}
+ \nabla\cdot(\rho_\ell \mathbf{u})
= q_\ell.
\]

WP-0.1 uses incompressible liquid density. Any future storage, compressibility or retention term introduced through machine/headspace coupling must be explicit.

### 5.3 Flow closure

The baseline saturated relation is:

\[
\mathbf{u}
= -\frac{\mathbf{K} k_r(S)}{\mu}
\left(\nabla p-\rho_\ell\mathbf{g}\right).
\]

Optional inertial extension:

\[
-\nabla p
= \mu\mathbf{K}^{-1}\mathbf{u}
+ \rho_\ell\,\boldsymbol{\beta}_F |\mathbf{u}|\mathbf{u}.
\]

The frozen R0 reference uses Darcy flow. The current solver also provides the
completed optional WP02-003 Darcy–Forchheimer branch and its regime
diagnostics; it remains disabled unless explicitly selected.

### 5.4 Wetting

WP-0.1 uses the simplest model that predicts first drip without forcing it:

- Foster-informed sharp-front pore-volume storage;
- an axial wetting front represented across the axisymmetric mesh;
- saturation and wet-mask activation behind the front;
- no explicit full two-phase air–water solve.

Capillary pressure, radial front variation and a richer Richards or two-phase formulation remain later upgrades if the qualified baseline cannot reproduce first-drip and wetting data with an honest closure.

### 5.5 One-solute extraction and transport

The dissolved phase should satisfy:

\[
\frac{\partial(\phi S c_\ell)}{\partial t}
+ \nabla\cdot
\left(\mathbf{u}c_\ell
- \phi S\mathbf{D}_{\mathrm{eff}}\nabla c_\ell\right)
= R_{\mathrm{ext}}.
\]

The local extractable solid inventory should satisfy:

\[
\frac{\partial m_s}{\partial t}=-R_{\mathrm{ext}}.
\]

WP-0.1 uses an effective one-solute mass-transfer closure, a finite extractable inventory and fixed temperature. Source-linked successor branches may be informed by Cameron, Roman-Corrochano, Pannusch, Mo or Liang and may introduce particle-size populations, intraparticle diffusion, partitioning or alternative equilibrium ceilings.

The critical requirement is not maximum chemical detail. It is exact accounting:

```text
initial extractable solid
= remaining solid
+ dissolved in puck liquid
+ exported to cup
+ declared numerical residual.
```

### 5.6 Cup accumulation

The outlet flux is integrated to obtain:

- beverage mass;
- dissolved-solids mass;
- instantaneous and cumulative TDS;
- extraction yield;
- time to target beverage mass.

Retained liquid and dissolved material inside the puck must remain visible rather than being silently added to the cup.

### 5.7 Later evolving state

The architecture must permit:

\[
\frac{\partial\phi}{\partial t}
= f_{\mathrm{swelling}}
+ f_{\mathrm{compaction}}
+ f_{\mathrm{dissolution}}
+ f_{\mathrm{fines}}
+ f_{\mathrm{damage}},
\]

and:

\[
\mathbf{K}=\mathbf{K}(\phi,\text{PSD},\text{fabric},S,\sigma,
 f_{\mathrm{mobile}},f_{\mathrm{bound}},\text{history}).
\]

Each contribution remains separately switchable and separately validated.

---

## 6. OpenFOAM whole-puck implementation strategy

### 6.1 Implemented solver concept

The custom Foundation OpenFOAM 12 solver is `espressoWholePullFoam`.

The frozen v0.1.4 implementation can:

- read deterministic reference and fixture configurations;
- initialize puck fields and explicit boundary names;
- apply the bed-top pressure ramp and outlet pressure definition;
- integrate the sharp-front wetting pressure history exactly;
- solve saturated Darcy pressure and flux fields;
- run uniform and layered permeability profiles;
- advance dissolved-solids transport and remaining extractable inventory;
- integrate inlet, retained and cup liquid and solute inventories;
- write spatial fields at selected intervals;
- reconstruct requested fields after parallel execution;
- compare the result with analytical references and an independent B0 twin;
- run a standard time-step, mesh and MPI qualification matrix through `./Allverify`;
- emit detailed numerical acceptance and qualification reports;
- emit a single machine-readable run-status JSON covering environment, build, mesh, fixtures, decomposition, MPI execution, reconstruction and postprocessing;
- run through `./Allrun`, qualify through `./Allverify`, and remove generated results through `./Allclean`.

The completed target-system campaign confirms that this architecture is viable and numerically qualified for the bounded WP-0.1 equations.

### 6.2 Implemented initial geometry

The baseline mesh is a 5° straight-sided axisymmetric wedge representing the 58 mm puck:

```text
axial cells:       256
radial cells:      512
wedge cells:         1
total cells:   131,072
bed depth:      9.011660896 mm
outer radius:  29 mm nominal
```

The exact full-cylinder scale is derived from the straight-sided wedge geometry. The current R0 case contains the puck domain and named inlet, outlet, outer-wall, axis and wedge boundaries. Headspace, shower-screen and detailed basket-hole regions are not yet solved as separate fluid domains; their effects are represented through declared boundary conditions and future interface contracts.

Axisymmetry remains the correct regression baseline because it permits depth and radial variation, practical qualification studies, wall effects and future layered fields at modest cost. Three-dimensional geometry should be introduced only for a named non-axisymmetric mechanism such as basket-hole patterning, preparation defects or localized channel growth.

### 6.3 Boundary hierarchy

Every run must distinguish:

```text
pump outlet pressure
headspace / bed-top pressure
puck pressure drop
basket or outlet node
ambient pressure
```

R0 prescribes bed-top pressure directly and sets the declared outlet to
ambient gauge pressure. The completed WP02-002 branch optionally solves
machine delivery, compliance, upstream resistance, and emergent basket
pressure using explicit node names. The prescribed-pressure mode remains the
frozen regression control.

### 6.4 Numerical progression and current status

| Step | Status | Evidence |
|---|---|---|
| Closed-form Darcy and sharp-front preflight | COMPLETE | Analytical references written and passed |
| Uniform axisymmetric wedge case | COMPLETE | Mesh, volume, flow and execution gates pass |
| Whole-pull R0 with one solute and cup accumulation | COMPLETE | 30 s run and acceptance report pass |
| Straight-sided wedge correction | COMPLETE | Volume/flow/retained-water equivalence pass |
| Exact pressure-ramp integration | COMPLETE | First-drip analytical gate pass |
| Layered heterogeneous-pressure fixture | COMPLETE | Nonzero iterations; flow and probe gates pass |
| OpenFOAM/B0 parity | COMPLETE | All required parity outputs pass |
| Time-step qualification | COMPLETE | 0.020/0.010/0.005 s matrix passes |
| Mesh qualification | COMPLETE | 128×256/256×512/512×1024 matrix passes |
| Serial/rank-count equivalence | COMPLETE | 1/16/32/64 reference and 1/16 layered pass |
| No-physics freeze finalization | COMPLETE | 28/28 comparison gates and terminal manifest pass |
| Immutable R0 baseline | **FROZEN / QUALIFIED** | Exact executable, inputs, outputs and qualification bound |
| Data-linked R1 reconstruction | COMPLETE WITH STRUCTURAL RESIDUAL | Source-specific reconstruction; not independent validation |
| Machine and hydraulic integration | COMPLETE THROUGH WP02-004 | Machine coupling, inertial flow, and static heterogeneity |
| Quasi-static compaction | COMPLETE THROUGH WP03-001 | Saturated-only, fixed-mesh, no storage coupling |
| Validation and mechanism discrimination | **ACTIVE** | Source adapters, comparisons, uncertainty, identifiability, residuals |
| Next evolving-puck mechanism | NOT PRESELECTED | Selected from discriminating evidence |
| Three-dimensional basket | LATER | Defined non-axisymmetric question |

### 6.5 Implemented field outputs

The frozen run reconstructs:

```text
p
U
darcyFlux (surface scalar)
saturation
wetMask
porosity
permeability
hydraulicMobility
dissolvedConcentration
remainingExtractable
localExtractionRate
```

Later releases should add derived fields only where they support a scientific question, including pressure gradient, separate Darcy and inertial resistance, residence-time proxies, cumulative local extraction, channel indicators, fines inventories and deformation state.

### 6.6 Output and communication discipline

The v0.1.4 baseline produces and binds:

```text
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv
ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json
ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json
ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json
ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv
ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json
NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json
BUILD_PROVENANCE_V0_1_4.json
BUILD_PROVENANCE_VERIFICATION_V0_1_4.json
portable archived solver executable
reference_R0.foam
339 indexed reconstructed field files
stage-specific log.* files
```

The layers remain distinct:

```text
operational success/failure
≠ single-run numerical acceptance
≠ cross-run numerical qualification
≠ immutable release provenance
≠ source reconstruction
≠ physical validation.
```

The terminal freeze manifest is the provenance root for the frozen R0 baseline. A future R1 or physics branch must produce new versioned artifacts and must not rewrite v0.1.4.

### 6.7 Build, run and archive reproducibility

The v0.1.4 target run confirms that the package:

- uses explicit Foundation 12 headers rather than the obsolete `fvCFD.H` umbrella include;
- uses `FOAM_SRC` or `${WM_PROJECT_DIR}/src` in shell scripts rather than assuming `LIB_SRC` is exported;
- sources the Foundation environment safely under strict shell options;
- preflights required headers;
- normalizes unsafe future timestamps before dependency generation;
- performs a clean solver rebuild;
- streams and preserves compiler and stage logs;
- records the source-package aggregate, executable hash and build-provenance bundle;
- copies the exact solver executable into the case as a portable archive;
- reuses and verifies that executable throughout standard qualification;
- generates run-status JSON on controlled success and failure;
- retains `./Allrun`, `./Allverify` and `./Allclean` as stable user entry points;
- completes terminal finalization without stale circular hashes.

The complete post-`Allverify` directory—not only the JSON summaries—must be archived because it contains the 339 reconstructed fields, executable, individual qualification cases, fixture outputs and logs bound by the terminal manifest.

The frozen directory should be treated as read-only. Future development should begin from the source ZIP or a separate branch/copy.

### 6.8 Independent verification twin

The B0 reduced architecture operates as an independent one-dimensional finite-volume verification twin for:

- uniform Darcy flow;
- exact pressure-ramp integration and first drip;
- conservative one-solute transport;
- solid–liquid–cup inventory;
- retained liquid and dissolved solute;
- time to target beverage mass.

All required v0.1.4 parity gates passed. B0 remains a verification and rapid-sensitivity backend, not a substitute for source-linked physical validation.

### 6.9 Frozen artifact contract and branch rule

The final reference artifact chain is:

```text
source package + immutable scientific inputs
                     ↓
exact compiled and archived executable
                     ↓
reference outputs + traces + field index
                     ↓
standard qualification + no-physics verification
                     ↓
finalized acceptance and run status
                     ↓
terminal freeze manifest generated last
```

No artifact bound by the terminal manifest should be modified in place.

All future work must:

- use a new package and artifact version;
- retain the v0.1.4 terminal manifest as a regression reference;
- record whether governing physics changed;
- rerun the minimum verification set appropriate to that change;
- preserve R0 as the calibration baseline;
- keep R1 and later source-specific cases separate;
- store an external checksum for the complete frozen archive because the terminal manifest cannot self-hash without recreating a cycle.

## 7. Taichi/LBM pore-scale and closure strategy

### 7.1 Role in the mature system

Taichi/LBM should supply closures and local physics to OpenFOAM, including:

\[
\mathbf{K}=\mathbf{K}(\text{morphology},\phi,\text{PSD},\text{fabric},\sigma,S),
\]

\[
\boldsymbol{\beta}_F
=\boldsymbol{\beta}_F(\text{morphology},\phi,\text{direction}),
\]

\[
\mathbf{D}_{\mathrm{disp}}
=\mathbf{D}_{\mathrm{disp}}(\mathbf{u},\text{morphology}),
\]

\[
R_{\mathrm{capture}}
=R_{\mathrm{capture}}(c_f,\mathbf{u},d_f,\text{throat statistics},\text{history}).
\]

### 7.2 Three levels of fines representation

“Explicit fines” can mean three different things:

1. **Eulerian whole-puck fines concentration** in OpenFOAM.
2. **Lagrangian fine particles** transported in the continuum field.
3. **Pore-resolved fine geometry** in selected Taichi microdomains.

The mature architecture should combine them:

```text
whole-puck fines transport
+ local pore-resolved capture/release calculations
+ dynamic porosity/permeability feedback.
```

This is more feasible and more interpretable than attempting a uniformly 5–10 µm, fully particle-resolved 58 mm puck on one GPU.

### 7.3 Use of completed M0 work

The completed Boolean-sphere campaigns remain useful for:

- numerical verification;
- performance and memory engineering;
- uncertainty methods;
- boundary and finite-volume lessons;
- regression fixtures.

They do not supply the default real-coffee permeability.

### 7.4 Morphology ladder

| Family | Role |
|---|---|
| M0 overlapping Boolean spheres | verification and methods |
| M1 non-overlapping/mechanically plausible particles | packing and topology experiments |
| M2 descriptor-conditioned synthetic ensembles | closure sampling |
| M3 image-informed or segmented geometry | reference calculations |
| M4 validated generator across coffee/packing states | product closure ensemble |

The first whole-pull solver does not wait for M4. It begins with measured or literature-informed continuum properties and substitutes higher-quality closures as they become available.

### 7.5 Closure artifact

Every Taichi-derived closure must state:

- source Puckworks commit;
- morphology family and hashes;
- state and descriptor range;
- direction and boundary class;
- grid and domain uncertainty;
- fitted form or table;
- covariance/ensemble representation;
- validation evidence;
- evidence ceiling;
- fallback behavior outside the domain.

---

## 8. Puckworks model and data integration

### 8.1 Puckworks is the scientific backbone, not the final numerical method

The new solver should not replace or bypass the repository. It should turn Puckworks into the evidence and integration plane for a new numerical model.

The reviewed repository contains separate models for grind, packing, machine delivery, wetting, porous flow, puck evolution and extraction; the public Guided Pull currently executes the Cameron extraction chain, while the Espresso Model Relay demonstrates assumption-rich links without claiming a validated whole-process simulator.

The new solver is the program that converts the most useful of those stage models into a coupled, spatially resolved, conservation-controlled system.

### 8.2 Initial model-role matrix

| Puckworks component/evidence | Role in the whole-pull program |
|---|---|
| `foster2025.machine_mode` | machine/headspace/pump delivery mode and pressure-node comparison |
| `foster2025.infiltration` | initial wetting and first-drip baseline |
| `waszkiewicz2025.poroelastic` | saturated pressure–flow and pressure-dependent bed response branch |
| `cameron2020.extraction_bdf` | primary extraction baseline and 20 g/40 g class reference |
| `romancorrochano2017.extraction` | intraparticle diffusion and partition alternative |
| `pannusch2024.solver` / closures | temperature, flow and species-aware extraction branch when adapters are ready |
| `mo2023_2.coupled_bed` | filling-front and swelling-coupled extraction pattern |
| `mo2023_2.swelling` | explicit swelling mechanism branch |
| `fasano2000_partI.fines_migration` | fines transport/deposition/release conceptual branch |
| `waszkiewicz2025.poroelastic` | compaction/deformation and dissolution-coupled flow alternative |
| `brewer2026.streamtube` | heterogeneity and parallel-path comparison |
| `brewer2026.coupled_kappa_t` | mechanism-combination sandbox, not a final closure |
| `wadsworth2026.permeability` | morphology/permeability prior and untamped comparison |
| Vaca Guerra and Roman-Corrochano data | tamped permeability constraints |
| `wadsworth2026.inertial` | Darcy/Forchheimer regime diagnostic |
| `sourcing2026.g10_liquor_rheology` | concentration/temperature-dependent fluid-property branch |
| `brewer2026.lb_reference` / `lb_taichi` | pore-scale closure and cross-solver backends |
| `sourcing2026.g3_pump_characteristic` | pump-envelope constraint |
| `sourcing2026.g1_glassbead_analog` | wetting-shape prior only, not coffee-specific validation |

### 8.3 Integration rules

Every handoff must record:

- quantity and SI unit;
- physical basis and reference volume;
- spatial and temporal basis;
- source model or dataset;
- whether it is measured, fitted, derived, simulated, assumed, or unsupported;
- uncertainty;
- validity findings;
- conversion formula;
- evidence level.

Existing Puckworks contract meanings are not repurposed. Extensions are additive and versioned.

### 8.4 Repository-data-first policy

Before requesting a new experiment, the program must check:

- model cards;
- `puckworks/data/MANIFEST.csv`;
- registered gates;
- source-data constraints;
- `docs/EXPERIMENTAL_DATA_NEEDS.md`;
- available raw or transcribed series;
- rights and redistribution status.

New evidence is commissioned only for a named load-bearing gap.

### 8.5 Rights and reproducibility

The solver may use private or non-redistributable evidence in a local analysis only where rights permit. Public artifacts must fail closed. Large field data may live outside Git but must be referenced by immutable checksums and stable storage.

---

## 9. Verification, calibration, validation, and evidence hierarchy

### 9.1 Separate questions

Every result must distinguish:

1. **Mathematical correctness:** are the declared equations and balances implemented correctly?
2. **Code verification:** do analytical fixtures, manufactured tests and independent implementations agree?
3. **Numerical qualification:** are the selected mesh, time step and decomposition adequate for the declared outputs?
4. **Release reproducibility:** are source, executable, inputs, outputs and qualification evidence immutably bound?
5. **Calibration:** which parameter values are selected using which observations?
6. **Stage reconstruction:** can the model reproduce source-defined wetting, flow or extraction evidence?
7. **Coupled validation:** can the model reproduce independent whole-shot behavior?
8. **Transfer:** does it work across coffee, grinder, machine and basket changes?
9. **Mechanism identification:** can competing physics be distinguished?
10. **Decision utility:** does the model improve design or recipe choices over simpler baselines?

WP-0.1 has passed questions 1–4 for its bounded equations and frozen R0 scenario. Questions 5–10 remain the scientific program.

### 9.2 Verification pyramid and current position

#### Level V0 — mathematical and manufactured fixtures

Required or relevant fixtures include:

- uniform Darcy flow;
- layered hydraulic resistance;
- sharp-front event timing;
- straight-sided-wedge volume scaling;
- conservative scalar transport;
- solid–liquid–cup inventory;
- pump/bed intersection;
- manufactured evolving-porosity cases.

**Current status:** uniform Darcy, layered resistance, sharp-front timing, wedge scaling and conservative inventory fixtures pass. Pump/bed intersection and evolving-porosity fixtures remain for later physics milestones and are not blockers to WP-0.1.

#### Level V1 — OpenFOAM/B0 parity

**Current status:** PASS for all required bounded WP-0.1 outputs. This is code verification, not physical validation.

#### Level V2 — stage reconstruction

- Foster first-drip/infiltration behavior;
- Waszkiewicz pressure–flow and 9-bar Q(t);
- Cameron or alternative extraction trajectories;
- measured tamped-permeability ranges.

**Current status:** source reconstruction is established case-by-case for
WP01R/WP02/WP03 artifacts. Independent component validation remains to be
assessed in the active post-WP03-001 tranche.

#### Level V3 — coupled reference shot

Assess:

- first drip;
- pressure/flow history;
- cup mass at 30 s;
- time to 40 g;
- TDS and EY;
- retained inventories;
- mass and solute conservation;
- numerical sensitivity and rank equivalence.

**Current status:** frozen and numerically qualified R0 calibration case. Physical validation is not established.

#### Level V4 — independent and intervention holdouts

**Current status:** not authorized or started. The current plan prepares
source-specific comparisons and future holdout requirements without opening
protected observations.

#### Level V5 — transfer and engineering decisions

**Current status:** future program milestone.

### 9.3 WP-0.1 acceptance disposition

| Label | WP-0.1 status |
|---|---|
| Package/build qualification | PASS |
| End-to-end execution | PASS |
| Analytical fixture verification | PASS |
| Heterogeneous pressure fixture | PASS |
| OpenFOAM/B0 parity | PASS |
| Mesh/time-step qualification | PASS under declared thresholds |
| Decomposition/rank equivalence | PASS |
| Explicit bounded-state gates | PASS |
| Explicit cumulative-mass monotonicity | PASS |
| Liquid conservation | PASS |
| Solute conservation | PASS |
| Numerical qualification | PASS |
| No-governing-physics verification | PASS; 28/28 |
| Exact executable binding | PASS |
| Release provenance | PASS |
| Immutable release/provenance freeze | **FROZEN / QUALIFIED** |
| Calibrated hydraulic endpoint | YES |
| Source reconstruction | NOT YET |
| Independent validation | NO |
| Transfer qualification | NO |

A 40 g result after selecting permeability as the hydraulic scale parameter is an engineering calibration and cannot be reused as an independent validation gate.

### 9.4 Frozen numerical baseline versus physical validation

The v0.1.4 terminal manifest satisfies the release-reproducibility requirements:

- acyclic scientific-input, acceptance, qualification and terminal-manifest roles;
- post-`Allverify` finalization of acceptance and run status;
- qualification path, size, hash and PASS status in the finalized records;
- explicit concentration-cap, remaining-inventory, retained-water-capacity and cumulative-mass monotonicity gates;
- exact build and executable reuse verification;
- 32-rank routine reference default with qualified overrides;
- fresh-package Foundation-12 `./Allrun`;
- standard `./Allverify`;
- source-package, scientific-input, field-archive and qualification-acceptance verification;
- terminal manifest generated last with every controlling hash simultaneously valid;
- explicit `governing_physics_change=false`.

The resulting claim is stronger than v0.1.3’s numerical qualification but narrower than physical validation:

```text
frozen numerical/calibration baseline       YES
independent real-coffee validation           NO
source-specific reconstruction               NOT YET
transfer qualification                       NO
```

Intermediate records that say the terminal manifest is pending are intentionally preterminal and must remain unchanged to preserve the acyclic hash chain. The terminal manifest is the final authority.

### 9.5 Evidence ceilings for prior and current work

- The A1 artifact is a manufactured self-test and does not supply measured real-coffee parameters.
- The B0 twin verifies numerical architecture and implementation agreement but not real-shot prediction.
- The M1 geometry preflight supplies a method candidate but not a real-coffee morphology or hydraulic closure.
- The M0 SVE campaigns verify numerical and statistical methods but do not establish real-coffee transfer.
- The v0.1.2 run establishes the first end-to-end implementation baseline.
- The v0.1.3 run and standard `Allverify` report establish numerical qualification of the bounded R0 implementation.
- The v0.1.4 terminal manifest establishes no-physics-change, exact-executable, acyclic and immutable provenance for the qualified R0 baseline.
- None of v0.1.2–v0.1.4 establishes independent physical validation of permeability, wetting, TDS, extraction yield or transfer.

These ceilings are controlling and must be carried into Puckworks cards, reports and public claims.

## 10. Progressive physics and chemistry roadmap

### Milestone WP-0.1 — Reference whole-pull implementation

**Status:** **COMPLETE**

The reference implementation established dry-puck sharp-front wetting,
prescribed pressure, uniform Darcy flow, conservative one-solute extraction,
retained inventories, cup accumulation, and the complete machine-to-cup
computational spine.

### Milestone WP-0.1H — Numerical hardening and qualification

**Status:** **COMPLETE — FROZEN / QUALIFIED**

WP-0.1H completed analytical, reduced-twin, conservation, mesh, timestep, MPI,
bounded-state, and immutable-provenance qualification. R0 remains the protected
`FROZEN / QUALIFIED` regression and calibration baseline.

### Milestone WP-0.1R — Source-linked reference qualification

**Status:** **COMPLETE WITH STRUCTURAL RESIDUAL; NOT INDEPENDENT PHYSICAL
VALIDATION**

WP-0.1R reconstructed the source-linked case and exposed structural residuals
under its declared calibration/comparison contract. It did not establish
cross-rig transfer or general physical validation.

### Milestone WP-0.2 — Machine and hydraulic integration

**Status:** **COMPLETE THROUGH WP02-004**

Completed capabilities are:

- optional dissolution-indexed effective permeability;
- lumped machine/headspace compliance and upstream resistance;
- emergent basket pressure;
- saturated Darcy and Darcy–Forchheimer flow;
- uniform, axial-layered, and radial two-zone permeability;
- zone-resolved flow and extraction diagnostics.

### Milestone WP-0.3 — Initial structural branch

**Status:** **WP03-001 COMPLETE**

WP03-001 implements saturated quasi-static effective stress, mechanical
porosity, pressure-dependent permeability, the exact finite-porosity
pressure-flow response, machine coupling, and fixed-reference-mesh deformation
diagnostics. It does not couple mechanical porosity to transport storage or
solve full solid mechanics.

### Active milestone — Post-WP03-001 validation and mechanism discrimination

**Status:** **ACTIVE NEXT PROGRAM TRANCHE**

Required outcomes are:

- source-specific validation adapters and evidence classification;
- explicit calibration/comparison separation;
- uncertainty-aware metrics and real-data component comparisons;
- limited coupled comparisons;
- sensitivity and practical-identifiability assessment;
- a mechanism-comparison matrix and residual decomposition;
- ranked next-physics recommendations;
- targeted experimental requirements.

This tranche is solver development. It builds executable comparison,
uncertainty, ensemble, and discrimination capability rather than adding an
immediate new governing equation.

### Later governing-physics candidates

The following remain candidates, not a predetermined queue:

- transient poroelastic storage or fuller deformation;
- swelling;
- dissolution-driven porosity;
- concentration-dependent viscosity;
- further state-dependent permeability;
- fines migration and deposition;
- damage and dynamic channeling;
- thermal coupling;
- multispecies chemistry.

Their order will be selected from evidence. Later equipment/recipe design and
an evidence-qualified engineering platform remain program goals.

### Residual-led decision framework

| Observed residual or discriminating evidence | Candidate next physics |
|---|---|
| Pressure/flow residual correlated with measured bed compression | Fuller poroelastic deformation or storage |
| Flow decay correlated with measured particle or bed expansion | Swelling |
| Flow changes correlated with concentration or viscosity measurements | Concentration-dependent viscosity |
| Turbidity, captured fines, or deposition evidence | Fines transport |
| Repeatable localized outlet-flow or extraction defects | Non-axisymmetric channeling or damage |
| Temperature-correlated hydraulic or extraction residual | Energy equation |
| Species-specific extraction disagreement | Multispecies chemistry |
| No discriminating evidence | Retain the simpler model and request better data |

This table guides scientific investigation; it does not automatically
authorize a mechanism.

## 11. Mechanism-specific development rules

| Mechanism | First implementation | Upgrade trigger | Validation need |
|---|---|---|---|
| Machine delivery | prescribed bed-top pressure | pressure-node and pump/headspace data required for full coupling | pump/basket pressure and flow traces |
| Wetting | Foster-informed sharp front | baseline misses first drip or CT progression | first drip and time-resolved wetting |
| Saturated flow | Darcy | inertial diagnostic or data shows nonlinearity | multi-pressure Q–P curves |
| Permeability evolution | static plus Waszkiewicz branch | coupled traces require time dependence | pressure/flow/deformation holdouts |
| Extraction | one solute, explicit inventory | multiple species or poor TDS/EY behavior | fractionated TDS/EY and species |
| Swelling | separate Mo-derived branch | independent swelling evidence | bed-height/CT and flow response |
| Fines | Eulerian transport/deposition branch | spatial fines data or strong flow signatures | captured fines, turbidity, post-shot distribution |
| Channeling | heterogeneity and damage indicators | non-axisymmetric residuals/spatial data | local flow/extraction or imaging |
| Thermal | fixed 93 °C | temperature sensitivity materially changes outputs | inlet/in-puck temperature histories |
| Rheology | constant water-like viscosity | local high-TDS viscosity matters | concentration/temperature property data |
| Gas | omitted | age/degassing residual is reproducible | gas/pressure/wetting evidence |

No mechanism may be activated merely because OpenFOAM can solve a corresponding equation.

---

## 12. Compute and resolution strategy

### 12.1 Available resources and demonstrated baseline

- NVIDIA A100-SXM4-80GB-class remote GPU resources;
- Google Colab execution with a practical monitored duration of approximately five hours per campaign invocation;
- local 64-CPU Linux system running OpenFOAM Foundation 12, with 128 logical CPUs reported by the run environment;
- local storage and ParaView post-processing;
- successful fresh-package 32-rank full-field R0 execution;
- exact compiled-executable archive and qualification binding;
- completed 1/16/32/64-rank reference equivalence study;
- completed coarse/reference/fine mesh study;
- completed three-time-step study;
- completed serial/parallel layered-fixture study;
- complete v0.1.4 terminal freeze and provenance record.

### 12.2 GPU policy

- use Taichi for high-throughput pore-scale work;
- preserve atomic checkpoints and resumable campaigns;
- keep each monitored campaign bounded;
- use geometry-only preselection before expensive flow;
- use paired/multifidelity designs rather than blind repetition;
- export only fields required for the closure or diagnostic;
- require every campaign to answer a closure, uncertainty or validation question consumed by the whole-pull model.

### 12.3 CPU/OpenFOAM policy after freeze

- preserve the v0.1.4 2D axisymmetric wedge and terminal manifest as the protected regression baseline;
- use **32 MPI ranks** as the routine default for the 256×512 reference mesh;
- retain 1, 16 and 64 ranks for regression/equivalence checks rather than routine execution;
- use 64 ranks for the 512×1024 fine mesh unless later scaling evidence supports another setting;
- report solver time separately from mesh generation, reconstruction and postprocessing;
- repeat performance runs before making hardware-general scaling claims;
- use mesh and time-step studies when equations, numerics, source cases or sensitive outputs change materially;
- write complete field histories only for reference/review runs and use reduced output for sweeps;
- scale to 3D only for a defined non-axisymmetric question;
- maintain deterministic case generation from versioned configuration;
- store reduced traces and immutable hashes even when large field data remain external;
- never run `./Allclean` on the only archived frozen evidence directory;
- develop R1 and later physics in separate versioned packages.

### 12.4 Completed numerical-qualification matrix

| Run family | Configuration | Outcome |
|---|---|---|
| Time-step coarse | 256×512, `Δt=0.020 s`, 32 ranks | PASS |
| Time-step reference | 256×512, `Δt=0.010 s`, 32 ranks | PASS |
| Time-step fine | 256×512, `Δt=0.005 s`, 32 ranks | PASS |
| Mesh coarse | 128×256, `Δt=0.010 s`, 16 ranks | PASS |
| Mesh fine | 512×1024, `Δt=0.010 s`, 64 ranks | PASS |
| Rank serial | 256×512, `Δt=0.010 s`, 1 rank | PASS |
| Rank 16 | 256×512, `Δt=0.010 s`, 16 ranks | PASS |
| Rank 32 | 256×512, `Δt=0.010 s`, 32 ranks | PASS |
| Rank 64 | 256×512, `Δt=0.010 s`, 64 ranks | PASS |
| Layered serial | 64×128, 1 rank | PASS |
| Layered parallel | 64×128, 16 ranks | PASS |

The standard report contains ten unique runs because the 32-rank `Δt=0.010 s` case serves both the time-step and rank families.

### 12.5 Qualification interpretation

The numerical error budget for the current R0 cup-level outputs is small relative to unresolved physical-model uncertainty:

- time-step sensitivity is at most approximately 0.124% over the tested endpoints;
- reference-versus-fine mesh sensitivity is at most approximately 0.560%, driven by retained dissolved solute;
- cup mass differs by only approximately 0.005% between reference and fine meshes;
- TDS differs by approximately 0.039%;
- extraction yield differs by approximately 0.044%;
- rank-count differences are of order `1e-9` relative.

The selected 256×512 mesh and 0.02 s main-run step are qualified for the current R0 outputs under the declared thresholds. For future chemistry-focused work, the mesh should be revisited because in-puck retained dissolved solute is the most sensitive quantity.

The time-step sequence is not perfectly monotonic for every output. The correct claim is **bounded time-step sensitivity**, not a demonstrated formal order of convergence.

The v0.1.4 freeze does not make this error budget universally transferable. A new source case or governing-physics branch must reconsider the verification matrix when its gradients, timescales or observables differ materially from R0.

### 12.6 Measured rank performance

| Ranks | Solver time at 256×512 and `Δt=0.01 s` | Relative interpretation |
|---:|---:|---|
| 1 | 220.90 s | serial reference |
| 16 | 12.66 s | strong measured speed-up |
| 32 | **8.00 s** | fastest tested |
| 64 | 8.87 s | communication overhead exceeds added compute benefit |

The configured 32-rank routine default is supported by the frozen qualification report. The apparent greater-than-linear 16-rank speed-up is likely influenced by cache, operating-system and one-run measurement effects. These timings guide local operation; they are not a universal strong-scaling claim.

### 12.7 Uniform full-puck pore resolution is not the only path

The successful 50 µm-class full-puck Taichi calculation demonstrates that very high hydraulic resolution is practical. It does not imply that every fine particle and chemical state can be uniformly resolved throughout the whole puck at 5–10 µm on one GPU.

The multiscale strategy remains:

```text
whole puck at continuum or tens-of-microns hydraulic resolution
+ local microdomains at fines-resolving resolution
+ closure exchange between the two.
```

### 12.8 Adaptive information allocation

Spend compute on the question, not on a fixed hierarchy:

- more pore resolution where throats or fines control the closure;
- more whole-puck resolution where radial gradients or channels matter;
- more realizations where stochastic uncertainty dominates;
- more experiments where model-form uncertainty dominates;
- fewer MPI ranks where communication overhead dominates;
- reduced output frequency where storage rather than solver accuracy is limiting.

## 13. Software and repository architecture

### 13.1 Frozen implementation and proposed repository layout

The complete v0.1.4 post-`Allverify` directory is the immutable external R0 baseline. The v0.1.3 package remains useful historical raw qualification evidence, but v0.1.4 is the integration reference.

Subject to a fresh review of the current Puckworks main branch, the intended layout remains:

```text
puckworks/
  whole_pull/
    scenario.py
    contracts.py
    adapters.py
    run.py
    reports.py
    validation.py
  backends/
    openfoam.py
    taichi_closure.py
    reduced_b0.py
  closures/
    hydraulic.py
    wetting.py
    extraction.py
    evolving_bed.py
  data/
    whole_pull_scenarios/
    closure_manifests/

solvers/
  openfoam/
    espressoWholePullFoam/
    cases/
      reference_R0_20g_58mm_9bar/
      waszkiewicz_R1_18p5g_9bar/

notebooks/
  whole_pull_reference_local_or_colab.ipynb

docs/
  WHOLE_PULL_STRATEGY.md
  WHOLE_PULL_REFERENCE_SPEC.md
  WHOLE_PULL_VALIDATION.md
  WP_0_1H_RESULT_NOTE.md
```

Large OpenFOAM and Taichi field artifacts may remain outside Git, but reduced results, manifests, validation summaries, terminal-manifest identity and external archive checksums belong in Puckworks.

### 13.2 One service, multiple interfaces

The same scenario service should support:

- Python API;
- command line;
- local OpenFOAM case generation;
- `Allrun`, `Allverify` and `Allclean` wrappers;
- notebook or guided local control where appropriate;
- JSON and Markdown reports;
- ParaView and reduced visualization products.

No notebook-only equations or hidden manual edits are permitted. A clean-package run must be reproducible from versioned configuration.

### 13.3 Canonical artifact layers

The program uses four distinct machine-readable layers:

1. **Operational run status**

```text
schema and package version
host and OpenFOAM environment
selected MPI ranks
stage status and exit code
failing command and line when applicable
log hashes and bounded tails
artifact presence
stage timings
```

2. **Single-run scientific/numerical acceptance**

```text
solver and scientific-input hashes
scenario and calibration mode
mesh and boundary identities
convergence and conservation
analytical and B0 comparisons
bounded-state and monotonicity gates
primary outputs
physical claim ceiling
trace and field-index hashes
```

3. **Cross-run numerical qualification**

```text
qualification profile and matrix
individual acceptance hashes
time-step and mesh comparisons
rank equivalence and timings
aggregate gate summary
exact executable identity
```

4. **Terminal freeze manifest**

```text
source-package aggregate
solver executable and build bundle
scientific input bundle
run status and stage timings
reference acceptance
qualification report
traces and field index
selected field-archive identity
no-physics-change evidence
final freeze status and timestamp
```

The v0.1.4 terminal manifest has been generated and passed. It is the provenance root for R0.

### 13.4 Acyclic provenance rule

The implemented order is:

- the **scientific-input manifest** hashes only source, configuration and generated case inputs;
- the **field index** hashes field artifacts;
- the **acceptance report** records immutable input/output evidence and is finalized after qualification;
- the **qualification report** binds individual acceptance reports and the exact executable;
- the **run status** is finalized before terminal-manifest generation;
- the **freeze manifest** hashes all final controlling artifacts and is generated last;
- no earlier artifact contains or requires the freeze-manifest self-hash.

This order permits every recorded hash to remain true simultaneously.

Future releases must retain the same acyclic principle, even if schema details change.

### 13.5 Baseline preservation and reproducibility

Preserve three evidence states:

1. **v0.1.3 raw qualification evidence**, including the complete case, qualification runs, logs and known metadata defects;
2. **v0.1.4 frozen source package**, the clean input archive from which the target run was produced;
3. **v0.1.4 complete post-qualification evidence directory**, including fields, exact executable, fixture outputs, individual qualification runs, logs and the terminal manifest.

The full post-qualification directory should be archived before any cleanup, for example as a versioned `tar.gz`, with its external SHA-256 stored separately in Puckworks and durable storage. The external archive checksum is outside the terminal manifest because the manifest cannot hash its own containing archive without creating a new cycle.

The final baseline records:

- package and source-manifest hashes;
- solver source and executable hashes;
- OpenFOAM build and environment;
- scientific configuration and generated dictionaries;
- run-status, timing, acceptance and qualification hashes;
- reduced traces and field index;
- complete field-content aggregate;
- calibration role and claim ceiling;
- preparation, output-finalization, qualification and freeze-finalization timestamps;
- no-physics-change result;
- external archive location and checksum.

The frozen directory is read-only evidence. `./Allclean` should be used only on a working copy.

### 13.6 Integration rule

Do not merge the solver into Puckworks merely as a large code drop. Integration should include:

- a component/backend card;
- an R0 scenario contract;
- the terminal-manifest identity and external archive checksum;
- model and data provenance;
- numerical-qualification and validity gates;
- reduced result fixtures;
- a clear rights posture;
- novice-facing execution documentation;
- links to immutable external field artifacts;
- a roadmap entry and evidence dossier for R1;
- explicit separation of numerical qualification, calibration and physical validation;
- regression tests that compare future branches with frozen R0 without modifying it.

## 14. Acceptance framework and WP-0.1 disposition

### 14.1 Gates passed by v0.1.4

The frozen R0 run passed:

- Foundation 12 environment selection;
- source-package verification;
- 28-part no-governing-physics comparison;
- solver compilation and linking;
- exact executable archive and identity verification;
- deterministic case preparation;
- automatic timestamp-safety checks;
- `blockMesh` completion;
- full topology and geometry checks;
- exact straight-sided-wedge volume equivalence;
- exact sharp-front first-drip equivalence;
- analytical uniform Darcy-flow equivalence;
- retained-water/cylindrical-volume equivalence;
- heterogeneous layered-pressure fixture;
- 32-rank reference decomposition and 30 s completion;
- bounded pressure and concentration residuals;
- finite and bounded declared trace variables;
- concentration below declared capacity;
- remaining extractable inventory bounds;
- retained-water pore-capacity bounds;
- monotonic cumulative inlet water, cup water and cup solute;
- maximum estimated saturated pore Courant of approximately 0.797;
- liquid inventory balance;
- solute inventory balance;
- reconstruction of all requested fields;
- all required OpenFOAM/B0 parity gates;
- creation of acceptance, trace, scientific-input manifest, field-index, timing and ParaView artifacts;
- final operational run-status generation.

### 14.2 Gates passed by the standard qualification report

The standard `Allverify` campaign passed:

- all ten individual run acceptance reports;
- 0.020 versus 0.005 s time-step comparison;
- 0.010 versus 0.005 s time-step comparison;
- coarse-versus-fine mesh comparison;
- reference-versus-fine mesh comparison;
- 16-versus-1-rank equivalence;
- 32-versus-1-rank equivalence;
- 64-versus-1-rank equivalence;
- serial/parallel layered-fixture equivalence.

All nine aggregate gates passed.

### 14.3 Immutable release-freeze gates passed

Version 0.1.4 additionally passed:

- the scientific-input manifest is acyclic and excludes mutable downstream reports;
- acceptance and run status were finalized after standard qualification;
- the final acceptance records qualification path, size, hash, profile and PASS status;
- all required physical-bound and monotonicity gates are explicit;
- 32 ranks are the routine R0 default while rank overrides remain supported;
- runtime and archived executables are byte-identical;
- the exact reference executable was reused in standard qualification;
- the source package, scientific inputs, field archive and qualification acceptances verify;
- no governing-physics change was introduced relative to qualified v0.1.3;
- the terminal freeze manifest was generated last;
- all 20 top-level controlling artifacts verify;
- the final terminal status is `FROZEN / QUALIFIED`.

The empty `"failed_comparisons": []` diagnostic false positive is nonblocking and should be corrected only in a future development version.

### 14.4 Physical and source-comparison outputs

Every source-linked report must include, without forcing a pass unless predeclared:

- first-drip time;
- flow-rate history;
- cumulative cup water, solute and beverage mass;
- time to 40 g;
- pressure histories at defined nodes;
- TDS history;
- extraction yield;
- retained liquid and dissolved solute;
- remaining extractable inventory;
- analytical and reduced-twin comparison;
- Foster comparison where compatible;
- Waszkiewicz 9-bar Q(t) comparison in R1;
- selected extraction-source comparison;
- every calibrated parameter and the observations used to set it;
- source/digitization uncertainty;
- protected comparison or holdout outputs.

### 14.5 Claim ceiling after immutable freeze

The current evidence supports:

> **The v0.1.4 OpenFOAM whole-pull R0 implementation is an immutably bound, numerically qualified calibration baseline for sharp-front wetting, Darcy flow, one-solute extraction and transport, retained inventories, and cup accumulation.**

It does not support:

- independent validation of the approximately 40 g endpoint;
- validated first-drip, TDS or extraction-yield prediction for a real coffee;
- universal real-coffee prediction;
- validated channeling, fines or evolving structure;
- transfer across coffees or equipment;
- taste prediction;
- engineering optimization.

Physical-validation claims require appropriately independent component,
coupled, cross-condition or separately authorized holdout evidence. WP-0.1R
alone is a source-linked reconstruction and cannot establish them.

### 14.6 Required frozen output set

The complete frozen evidence directory retains, at minimum:

```text
SOURCE_PACKAGE_MANIFEST.json

BUILD_PROVENANCE_V0_1_4.json
BUILD_PROVENANCE_VERIFICATION_V0_1_4.json
portable espressoWholePullFoam_v0_1_4 executable

NO_PHYSICS_CHANGE_VERIFICATION_V0_1_4.json
NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json

CASE_SCENARIO_V0_1_4.json
RUN_ENVIRONMENT_V0_1_4.json

ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv
ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json
ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json

ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json
ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv
ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json

ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json

reference_R0.foam
339 indexed reconstructed field files
individual qualification cases and acceptances
stage-specific build and execution logs
```

The run status communicates execution. The acceptance report governs one reference run. The qualification report governs numerical sensitivity and equivalence. The terminal freeze manifest is the final provenance root.

## 15. Validation and experiment strategy

### 15.1 What the frozen baseline changes

R0 now provides a frozen and numerically qualified model against which evidence can be mapped, future code changes can be regressed, and physical-model sensitivity can be measured. For the current bounded equations, discretization and decomposition uncertainty are small relative to the unresolved uncertainty in permeability, wetting, extraction kinetics, concentration capacity and real puck evolution.

The freeze also means that source-linked work can no longer improve R0 by silent retrospective editing. Any scientific change must occur in a new version or a distinct case, with the governing-physics delta declared and the appropriate verification repeated.

The qualification campaign identifies retained dissolved solute as the most mesh-sensitive reported state. Experiments or future source comparisons concerned with in-puck chemistry should therefore receive stricter spatial-resolution review than cup-mass or first-drip studies.

New data should be requested because a named parameter, closure or competing mechanism is load-bearing—not because additional data would be generally interesting.

### 15.2 Use current Puckworks evidence first

The active validation tranche should use and compare with the repository’s
rights-reviewed evidence inventory:

- 9-bar flow traces and pressure–flow calibration;
- CT infiltration and first-drip evidence;
- PSD and permeability measurements;
- tamped-permeability references;
- extraction and TDS data;
- species-resolved independent evidence;
- swelling and flow-decay references;
- fines and dynamic-flow signatures;
- liquor property data.

The recorded dependency lock must not be advanced except by a separately
authorized dependency review. Each adapter must preserve the applicable model
card, data identity, rights status, pressure node, quantity definition and
uncertainty.

### 15.3 Historical R1 reconstruction

R1 was built as a source-specific case rather than by relabelling R0. Its
lessons remain controlling:

- the 18.5 g dose and rig geometry;
- coffee and grind descriptors where available;
- pressure measurement node;
- outlet and downstream resistance definition;
- permeability or poroelastic calibration role;
- source Q(t) and uncertainty;
- which observations are used for calibration;
- which features remain comparison or holdout targets.

R1 demonstrated why source reconstruction, calibration and independent
comparison must remain distinct. Its protected flow-shape residual is
historical evidence, not authorization to reopen protected scoring.

### 15.4 Extraction evidence priority

The current TDS and EY values are highly sensitive to the one-solute closure. Before adding many species, the program should:

1. reproduce one selected extraction source under its own assumptions;
2. compare at least one alternative extraction closure on the same hydraulic history;
3. quantify sensitivity to extractable fraction, mass-transfer rate, dispersion and equilibrium ceiling;
4. distinguish cup-exported solute from dissolved solute retained in the puck;
5. identify observations that discriminate source-rate error from transport or retention error.

### 15.5 Target new experiments at load-bearing gaps

Priority experiment families remain:

- synchronized whole-shot pressure, flow, cup mass and chemistry;
- initially dry first drip and wetting progression;
- same-coffee PSD, packing and permeability;
- poroelastic deformation;
- time-dependent mechanism discrimination;
- species-resolved fractional extraction;
- spatial flow/channeling and local extraction;
- cross-machine, grinder and coffee transfer.

The qualified solver should rank these by sensitivity, identifiability and expected information value.

### 15.6 Calibration and holdouts

The program must predeclare:

- which scenario sets a hydraulic scale parameter;
- which chemistry observations set extraction parameters;
- which trace features remain holdouts;
- which pressure levels test transfer;
- which coffee/equipment changes test generalization.

No dataset may silently serve as both calibration and independent validation. R0’s approximately 40 g endpoint is already consumed as a calibration-class target and cannot be presented as a held-out success.

### 15.7 Model-form uncertainty

Where multiple Puckworks mechanisms fit the same observation, retain an ensemble or branch set until an intervention discriminates them. Do not tune a generic `K(t)` and then call its time dependence swelling, fines, compaction or channeling.

## 16. Direct development plan

### Phase A — Strategy and initial specification

**Status:** substantially complete.

Completed or established:

- Version 1.0 program pivot;
- bounded R0 objective;
- Foundation OpenFOAM 12 baseline;
- one-solute conserved architecture;
- acceptance, qualification and freeze concepts;
- output and claim ceiling.

Remaining documentation task:

- issue a formal `ESPRESSO_WHOLE_PULL_REFERENCE_SPEC_V0_1.md` aligned with the frozen solver, exact scenario, terminal schema and archive identities.

### Phase B — OpenFOAM solver scaffold and first execution

**Status:** complete.

Completed:

- custom solver and deterministic case generator;
- pressure and Darcy solve;
- sharp-front wetting/storage;
- one-solute fields and cup accumulator;
- operational and numerical reports;
- full R0 execution and field reconstruction.

### Phase C — Numerical hardening and qualification

**Status:** complete.

Completed:

- wedge and pressure-ramp corrections;
- analytical gates;
- layered fixture;
- B0 parity;
- time-step, mesh and rank qualification;
- stage timing and build provenance;
- clean target-system execution;
- standard ten-run qualification with all aggregate gates passing.

### Phase D — Immutable freeze finalization

**Status:** complete.

Completed through v0.1.4:

- acyclic artifact provenance;
- post-`Allverify` acceptance/run-status finalization;
- explicit bounded-state and monotonicity gates;
- 32-rank reference default;
- exact executable archive and qualification binding;
- 28/28 no-physics-change verification;
- fresh-package `Allrun` and standard `Allverify`;
- terminal freeze manifest;
- formal WP-0.1H `FROZEN / QUALIFIED` designation.

Remaining operational task:

- archive the complete post-qualification directory and store its external checksum in durable storage and Puckworks.

### Phase E — Data-linked R1 and Puckworks integration

**Status:** complete with a structural residual; not independent physical
validation.

### Phase F — Hydraulic and first structural expansion

**Status:** complete through WP03-001.

WP02-001 through WP02-004 added independently selectable effective-
permeability evolution, machine compliance, inertial resistance and static
radial heterogeneity. WP03-001 added saturated quasi-static compaction.

### Phase G — Validation and mechanism discrimination

**Status:** active next program tranche.

Implement source-specific adapters, rights- and evidence-aware comparison
bundles, uncertainty propagation, sensitivity and identifiability analysis,
residual decomposition, mechanism comparisons and experiment-design
priorities. Compare existing branches before selecting one next
governing-physics increment.

### Phase H — Evidence-selected physics

Resume governing-physics expansion only when the validation residuals and
available measurements identify a load-bearing mechanism. Candidate work
includes fuller poroelastic storage, swelling, viscosity, fines, localized
damage, thermal coupling and multispecies chemistry; this list is not a queue.

## 17. Immediate next actions

The following sequence is controlling:

1. implement the common source-adapter and calibration/comparison ledger;
2. inventory admissible evidence, definitions, rights, uncertainties and
   circularity from the existing lock;
3. perform one wetting or first-drip component comparison;
4. perform one saturated hydraulic and one limited coupled pressure/flow
   comparison;
5. perform one aggregate extraction comparison while preserving the
   one-solute limitation;
6. propagate supported uncertainties and assess parameter sensitivity,
   correlation, equifinality and practical identifiability;
7. compare compatible existing mechanisms on common source-specific cases;
8. decompose residuals by pressure, time, space, apparatus and observable;
9. rank missing measurements by expected information value; and
10. recommend either the simpler existing family, one evidence-supported next
    mechanism, or additional data.

No validation execution, protected access, holdout opening, fitting or
experimental commissioning is authorized by this strategy update.

## 18. Program risks and controls

| Risk | Consequence | Control |
|---|---|---|
| Frozen v0.1.4 evidence is cleaned, moved incompletely or overwritten | Terminal hashes can no longer be independently verified | Archive the entire post-`Allverify` directory, store external checksums, and treat the original as read-only |
| Numerical freeze is presented as physical validation | Overstated confidence in real-coffee prediction | Preserve the calibration role and `PHYSICAL_VALIDATION_NOT_ESTABLISHED` label in every artifact and public statement |
| Intermediate preterminal status text is mistaken for the final disposition | Apparent contradiction in the evidence record | Treat the terminal freeze manifest as final authority and explain the acyclic generation order |
| Empty `failed_comparisons` is treated as a real failure | False alarm and unnecessary baseline regeneration | Record it as a known classifier defect; fix only in the next development version |
| Frozen R0 is silently retuned during R1 | Loss of regression baseline and ambiguous scientific changes | Use a distinct scenario/package; declare every R0-to-R1 change |
| R1 consumes all source observations as calibration | No meaningful source-linked test remains | Predeclare the minimal calibration set and reserve trace features, conditions or pressure levels |
| Source pressure nodes or downstream resistance are misinterpreted | Incorrect apparent model error or false agreement | Build a source apparatus/node dossier before case implementation |
| Digitized traces are treated as exact data | Overconfident calibration and residual interpretation | Preserve raw points, digitization method and uncertainty bounds |
| Puckworks integration uses a stale repository baseline | Duplicate contracts or missed evidence | Refresh current `main`, cards, data and rights before integration |
| Integration becomes only a code dump | New solver loses evidence discipline | Require backend cards, scenario contracts, validity gates, reduced fixtures and immutable artifact links |
| New mechanisms accumulate without evidence comparison | Flexibility and equifinality increase faster than physical identification | Apply the post-WP03-001 cadence rule and select one next mechanism from residual evidence |
| Bounded sensitivity is described as formal order of convergence | Numerical evidence is overstated | Report tested differences and thresholds; do not claim asymptotic order without a dedicated study |
| All 64 ranks are used by default | Slower routine R0 runs and wasted resources | Use 32 ranks for the reference mesh and 64 for the fine mesh unless new scaling evidence changes the policy |
| Retained dissolved solute sensitivity is ignored | Future in-puck chemistry claims may be under-resolved | Revisit mesh qualification when chemistry or retained-state detail becomes decision-critical |
| Successful 40 g calibration is presented as validation | Hydraulic endpoint appears more predictive than it is | Label permeability as the R0 calibration parameter and use R1/holdouts for testing |
| TDS/EY engineering assumptions appear established | Misleading chemistry claims | Reconstruct source closures, run sensitivity and preserve evidence labels |
| Endpoint overfitting | Correct mass with wrong dynamics | Retain first drip, trace shape, retained inventories and other pressure levels as tests |
| Cross-paper parameter mixing | Plausible but fictitious reference case | Keep R0 engineering and R1 source-linked scenarios separate |
| OpenFOAM complexity expands without evidence | Slow, opaque model | Activate equations only for named residuals or decisions |
| Pore-scale work becomes detached | Strong micro-results with no system impact | Require every Taichi campaign to answer a closure or sensitivity request |
| Continuum closure hides mechanisms | Uninterpretable `K(t)` | Separate swelling, compaction, fines, dissolution and rheology branches |
| Uniform explicit fines resolution is infeasible | Memory/time failure | Combine continuum fines transport with local pore-resolved closures |
| Rights prevent public evidence use | Unpublishable outputs | Fail closed and retain local/private evidence status |
| High-fidelity model cannot support design loops | No engineering utility | Build reduced twins and surrogates after evidence qualification |
| “Most advanced” claim precedes proof | Credibility loss | Complete a formal landscape benchmark and demonstrate capabilities first |

## 19. Stop, continue, and pivot rules

### Continue when

- a calculation advances the whole-pull model;
- it closes a load-bearing uncertainty;
- it improves a holdout prediction;
- it discriminates mechanisms;
- it produces a reusable closure;
- it enables an engineering comparison.

### Stop or pause when

- the quantity is not consumed by the whole-pull model;
- the same synthetic-family question is being refined without physical leverage;
- a complex branch does not outperform a simpler baseline;
- the evidence cannot identify the parameters;
- resolution is increasing faster than interpretability;
- the model cannot state which observed residual it is addressing.

### Pivot when

- a measured/hybrid closure is stronger than a pure simulation closure;
- a local pore-scale study is more informative than whole-puck refinement;
- an experiment is more valuable than another computational realization;
- an ensemble is more honest than one selected mechanism;
- a reduced model is sufficient for the intended decision.

---

## 20. Version 1.6 controlling summary

The program has a frozen, numerically qualified R0 and a modular Foundation
OpenFOAM 12 whole-pull solver. WP01R and WP02-001 through WP02-004 added
source-linked reconstruction, effective-permeability evolution, machine
compliance, Darcy–Forchheimer resistance and static spatial heterogeneity.
WP03-001 added saturated quasi-static compaction with pressure-dependent
mechanical porosity and permeability on a fixed reference mesh.

Those branches are numerically verified for their tested domains. They do not
establish physical validation. In particular, WP03-001 does not solve solid
displacement, couple mechanical porosity to transport storage, or include
transient Biot storage, plasticity, hysteresis, swelling, fines, damage or
dynamic channeling.

The active milestone is now:

```text
completed solver sequence          WP-0.1 through WP03-001
active program tranche             source-specific validation and mechanism discrimination
next governing physics             not preselected; residual-led
physical validation                NOT ESTABLISHED
experimental commissioning         NOT AUTHORIZED
protected or holdout scoring       NOT AUTHORIZED
```

The frozen R0 remains a bounded calibration scenario, and source or post-fit
reconstruction remains distinct from independent validation. The validation
tranche will build executable adapters and comparisons, quantify uncertainty
and identifiability, and determine which residuals justify one next mechanism.

The defining architecture remains:

```text
Puckworks knowledge, data, models and validation
                     +
OpenFOAM whole-puck multiphysics
                     +
Taichi/LBM high-resolution pore-scale closures
                     +
reduced verification and decision models.
```

The controlling rule is now:

> **Protect the frozen baseline, compare the existing model family with
> relevant real evidence, decompose residuals, and add one next mechanism only
> when the evidence identifies a load-bearing residual or engineering need.**

## Appendix A — Controlling evidence from completed work

| Artifact/work | Retained conclusion in Version 1.3 |
|---|---|
| Full-puck Taichi/LBM optimization | High-resolution 58 mm hydraulic calculations are computationally credible and reusable |
| v0.7 conditioned SVE | Numerical execution passed; conditioned domain equivalence and precision were not established |
| v0.8 paired nested SVE | Paired design strongly reduced variance; nested equivalence was not established |
| v0.9 boundary/embedding diagnostic | Parent reruns were sound; open-subvolume scalar decomposition was not qualified |
| M1 geometry preflight | A morphology-method candidate exists; real-coffee hydraulic qualification remains open |
| B0 continuum architecture | Provides an independent reduced finite-volume verification twin for bounded WP-0.1 equations |
| A1 manufactured self-test | Data-ingestion pipeline works; no measured real-coffee anchor was established |
| Puckworks Model Relay | Cross-model orchestration and assumption ledgers exist; it is not a validated coupled simulator |
| WP-0.1 OpenFOAM v0.1.2 run | First successful end-to-end Foundation-12 implementation and run-level baseline |
| WP-0.1 OpenFOAM v0.1.3 run | Corrected R0 execution, analytical gates, layered fixture, B0 parity and conservation pass |
| v0.1.3 standard `Allverify` | Ten individual runs and all nine aggregate numerical-qualification gates pass |
| v0.1.4 no-physics verification | All 28 comparisons pass; governing equations and qualified physics are unchanged |
| v0.1.4 fresh `Allrun` | 32-rank reference, bounded-state gates, exact build and full artifact generation pass |
| v0.1.4 standard `Allverify` | Ten runs and 9/9 aggregate gates pass using the exact reference executable |
| v0.1.4 terminal freeze manifest | R0 is `FROZEN / QUALIFIED` with acyclic, verified provenance |
| WP-0.1H freeze-finalization review | Accepts WP-0.1H as complete; physical validation remains not established |

## Appendix B — WP-0.1H frozen reference outputs

### Scalar and trace outputs

| Quantity | Value |
|---|---:|
| First drip | 4.711696185 s |
| Final outlet flow | 1.482675972 mL/s |
| Cup water mass at 30 s | 36.170176862 g |
| Cup solute mass at 30 s | 4.787690621 g |
| Total beverage mass at 30 s | 40.957867483 g |
| Time to 40 g | 29.374480171 s |
| Cumulative TDS | 11.689306389% |
| Extraction yield | 23.938453103% |
| Retained water | 9.190476190 g |
| Retained dissolved solute | 0.192063112 g |
| Remaining extractable mass | 0.619392295 g |
| Maximum dissolved concentration | 174.914486977 kg/m³ |
| Maximum liquid residual | 6.036837696 × 10⁻¹⁶ kg |
| Maximum solute residual | 2.597997228 × 10⁻¹³ kg |
| Maximum pressure final residual | 9.210823584 × 10⁻¹⁵ |
| Maximum concentration final residual | 9.961187341 × 10⁻¹² |
| Maximum concentration iterations | 4 |
| Maximum estimated saturated pore Courant | 0.797086602 |
| Straight-sided wedge scale | 72.091466484 |
| Scaled-volume relative error | 2.276824562 × 10⁻¹⁵ |

### Analytical and reduced-twin checks

| Check | Result |
|---|---:|
| First-drip absolute error versus analytical reference | 1.1546 × 10⁻¹⁴ s |
| Uniform Darcy-flow relative error | 8.2837 × 10⁻¹⁵ |
| Retained-water relative error | 1.1325 × 10⁻¹⁵ |
| All required OpenFOAM/B0 outputs | PASS |
| Layered fixture maximum pressure iterations | 122 in the qualified fixture family |
| Layered serial/parallel flow difference | 9.60 × 10⁻¹³ relative |

### Reconstructed field outputs

- pressure `p`;
- velocity `U`;
- surface `darcyFlux`;
- saturation;
- wet-mask state;
- porosity;
- permeability;
- hydraulic mobility;
- dissolved concentration;
- remaining extractable inventory;
- local extraction rate.

The field index contains 339 files, no missing final fields, and aggregate content SHA-256:

```text
9468de231dc2f50ed1db158a0a5520a16e505818f52f44b85d51426232543bfd
```

### Numerical-qualification summary

| Qualification comparison | Largest difference |
|---|---:|
| `Δt=0.020` versus `0.005 s` | 0.1242% |
| `Δt=0.010` versus `0.005 s` | 0.0564% |
| 128×256 versus 512×1024 | 1.6835% |
| 256×512 versus 512×1024 | 0.5596% |
| Worst 1/16/32/64-rank output difference | 2.23 × 10⁻⁹ relative |
| Layered serial/parallel flow difference | 9.60 × 10⁻¹³ relative |

### Required evidence labels

- R0 is an engineering calibration scenario;
- saturated permeability is the hydraulic calibration parameter;
- TDS and EY remain engineering-closure outputs;
- code verification, numerical qualification and immutable provenance pass;
- R0 is `FROZEN / QUALIFIED`;
- physical validation is not established.

## Appendix C — Initial Puckworks repository deliverables

```text
docs/WHOLE_PULL_STRATEGY.md

docs/WHOLE_PULL_REFERENCE_SPEC.md

docs/WHOLE_PULL_VALIDATION.md

docs/WP_0_1H_RESULT_NOTE.md

puckworks/whole_pull/

puckworks/backends/openfoam.py

puckworks/backends/taichi_closure.py

puckworks/backends/reduced_b0.py

puckworks/data/whole_pull_scenarios/reference_R0_20g_58mm_9bar/

puckworks/data/whole_pull_scenarios/waszkiewicz_R1_18p5g_9bar/

solvers/openfoam/espressoWholePullFoam/

solvers/openfoam/cases/reference_R0_20g_58mm_9bar/

solvers/openfoam/cases/waszkiewicz_R1_18p5g_9bar/
```

Exact paths and registration IDs remain subject to a fresh repository review, but the architectural division is controlling.

---

## Appendix D — WP-0.1H v0.1.4 terminal evidence record

| Item | Recorded value |
|---|---|
| Freeze date | 27 July 2026 |
| Package | `espresso_puck_whole_pull_reference_v0_1_4_openfoam12` |
| Solver | `espressoWholePullFoam` 0.1.4 |
| OpenFOAM | Foundation 12, build `12-0f458291f1cd` |
| Compiler/options | GCC optimized, double precision, 32-bit labels |
| Main R0 MPI execution | System OpenMPI, 32 ranks |
| Qualification ranks | 1, 16, 32 and 64; layered 1 and 16 |
| Host | `<HOSTNAME>` |
| Logical CPUs reported | 128 |
| Run status | PASS / COMPLETED |
| Reference acceptance | PASS; all numerical, B0, bounded-state and monotonicity gates pass |
| Standard qualification | PASS / COMPLETED; 9/9 aggregate gates |
| No-physics verification | PASS; 28/28 comparisons; governing physics unchanged |
| Terminal freeze status | `FROZEN / QUALIFIED` |
| WP milestone | `WP-0.1H_COMPLETE` |
| Physical validation | `NOT_ESTABLISHED` |
| Source-package file count | 106 |
| Scientific-input file count | 19 |
| Indexed field-file count | 339 |
| Qualification acceptance count | 10 |
| Controlling artifact count | 20 |
| Aggregate source SHA-256 | `182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e` |
| Compiled/archived solver SHA-256 | `ada45a5440d08ae8da1a57d65cdf511748a340cd09a045121c59ea83a3d8d6d7` |
| Source/executable bundle SHA-256 | `23e2cc45a5bcff9970e1482ac05296d85a4b630ee7ee088206677b48c76e9c08` |
| Scientific-input bundle SHA-256 | `d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a` |
| Reconstructed-field aggregate SHA-256 | `9468de231dc2f50ed1db158a0a5520a16e505818f52f44b85d51426232543bfd` |
| Qualification executable binding | PASS; exact reference executable reused |
| Controlling-artifact aggregate SHA-256 | `044f6369014f202dde1755879f3a93d60c7bc5c007358c769e24dacca14d2229` |
| Next scientific milestone | `WP-0.1R` |
| Known nonblocking defect | Empty `"failed_comparisons": []` member is falsely classified as an issue |

The complete post-`Allverify` directory, rather than this summary alone, is the controlling evidence. The terminal manifest is the final internal provenance root; the complete external archive requires a separately stored checksum.

## Appendix E — Completed WP-0.1H verification matrix

| Test family | Cases | Result | Controlling observation |
|---|---|---|---|
| Pressure-ramp time integration | 0.020, 0.010, 0.005 s on reference mesh | PASS | First drip invariant because ramp integration is exact |
| Time-step sensitivity | 0.020/0.010 versus 0.005 s | PASS | Maximum difference 0.1242% |
| Mesh sensitivity | 128×256, 256×512, 512×1024 at 0.010 s | PASS | Maximum reference-versus-fine difference 0.5596% |
| Rank equivalence | 1, 16, 32, 64 ranks | PASS | Worst output difference 2.23e-9 relative |
| Rank efficiency | same reference mesh/time step | COMPLETE | 32 ranks fastest tested |
| Wedge scaling | mesh volume and analytical cylinder | PASS | Relative volume error approximately 2.28e-15 |
| Heterogeneous pressure | layered permeability | PASS | Nonzero iterations; flow/probes match independent reference |
| B0 parity | matched R0 equations | PASS | All required outputs pass |
| Clean-package reproducibility | fresh v0.1.4 target execution | PASS | No manual edits or timestamp correction required |
| No-physics verification | v0.1.4 versus qualified v0.1.3 contract | PASS | 28 PASS / 0 FAIL |
| Standard aggregate qualification | ten runs, nine gates | PASS | 9 PASS / 0 FAIL |
| Terminal provenance | source/executable/inputs/results/qualification | PASS | R0 `FROZEN / QUALIFIED` |

The matrix establishes bounded sensitivity and reproducibility for the declared outputs and thresholds. It does not establish physical validity or formal asymptotic convergence order for every state variable.

---

## Appendix F — v0.1.4 frozen-baseline preservation contract

### Final terminal status

```text
implementation_status:             PASS
code_verification_status:          PASS
numerical_qualification_status:    PASS
release_provenance_status:         PASS
reference_qualification_status:    PASS
reference_freeze_status:           FROZEN / QUALIFIED
wp_milestone:                      WP-0.1H_COMPLETE
governing_physics_change:          false
calibration_mode:                  R0 hydraulic calibration
physical_validation_status:        NOT_ESTABLISHED
next_scientific_milestone:         WP-0.1R
```

### Preservation rules

- archive the complete post-qualification directory before cleanup;
- retain the terminal manifest with all files it binds;
- calculate and store an external checksum for the complete archive;
- keep at least two durable copies;
- do not edit, regenerate or partially replace v0.1.4 artifacts;
- use a new version for diagnostic cleanup, R1 or governing-physics changes;
- preserve the exact solver executable and field aggregate;
- retain v0.1.4 as the R0 regression control in Puckworks.

### Development-branch rules

A future branch must declare one of:

```text
NO_GOVERNING_PHYSICS_CHANGE
SOURCE_SCENARIO_CHANGE_ONLY
NUMERICAL_METHOD_CHANGE
GOVERNING_PHYSICS_CHANGE
```

The declaration determines which verification and qualification gates must be repeated. No branch may inherit the `FROZEN / QUALIFIED` label automatically.

---

## Appendix G — WP-0.1R entry contract

### Entry conditions

WP-0.1R may begin because:

- R0 implementation, verification, qualification and freeze are complete;
- the exact R0 solver and outputs are preserved;
- numerical uncertainty is bounded under the declared R0 matrix;
- the next unresolved question is source-linked physical reconstruction, not baseline numerical stability.

### Required source dossier

R1 must include:

```text
source document and supplementary-file identities
rights and redistribution status
18.5 g dose and basket geometry
coffee and grind descriptors
pressure measurement node
outlet/downstream resistance definition
9-bar pressure and Q(t) data
digitization points and uncertainty
permeability/poroelastic parameter definitions
calibration observations
protected comparison or holdout observations
unit and quantity mappings to Puckworks
```

### Minimum R1 report

The first R1 report must provide:

- exact R0-to-R1 scenario differences;
- unchanged and changed solver assumptions;
- calibration ledger;
- pressure and flow comparison at source-defined nodes;
- first-drip/wetting comparison where compatible;
- mass and solute conservation;
- numerical regression against frozen R0 fixtures;
- source uncertainty;
- residual decomposition;
- physical claim ceiling;
- recommendation for the first WP-0.2 mechanism or experiment.

R1 must not be labelled validated merely because one pressure–flow trace can be fitted.
