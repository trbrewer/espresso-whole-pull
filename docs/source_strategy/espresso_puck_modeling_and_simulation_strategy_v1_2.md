# Puckworks Whole-Pull Multiscale Modeling and Simulation Strategy

**Strategy version:** 1.2  
**Date:** 27 July 2026  
**Status:** Controlling strategy following successful WP-0.1H numerical qualification; immutable release freeze and physical validation remain pending  
**Supersedes:** `espresso_puck_modeling_and_simulation_strategy_v1_1.md` and all earlier strategy versions  
**Repository:** `trbrewer/puckworks`  
**Reviewed repository baseline:** inherited from Version 1.0, `main` at commit `d9ee264`; repository alignment must be refreshed before integration  
**OpenFOAM implementation baseline:** `espresso_puck_whole_pull_reference_v0_1_3_openfoam12`  
**Execution baseline:** OpenFOAM Foundation 12 on the local Linux system; corrected 64-rank R0 reference run plus the standard ten-run numerical-qualification matrix across mesh, time step and MPI rank count  
**Primary whole-puck platform:** OpenFOAM Foundation 12 on the local 64-CPU Linux system, with 128 logical CPUs reported by the run environment  
**Primary pore-scale platform:** Taichi/LBM on NVIDIA A100-SXM4-80GB-class GPU resources  
**Scientific and software backbone:** Puckworks models, data, model cards, contracts, validation gates, rights records, and public product layer  
**WP-0.1 disposition:** **IMPLEMENTATION PASS; BOUNDED CODE VERIFICATION PASS; NUMERICAL QUALIFICATION PASS; IMMUTABLE RELEASE FREEZE PENDING; PHYSICAL VALIDATION NOT YET ESTABLISHED**  
**Next controlling milestone:** a v0.1.4 freeze-finalization and provenance release with no governing-physics change, followed by the R1 source-linked case and formal Puckworks integration

---

## Executive statement

Version 1.0 established the program pivot: build a new, coupled, multiscale, whole-pull espresso simulation rather than indefinitely postponing integration behind pore-scale qualification or reducing the effort to an orchestration layer around existing models. Version 1.1 then recorded the first successful end-to-end OpenFOAM execution and made numerical hardening the immediate critical path.

That numerical-hardening milestone has now been achieved.

On 27 July 2026, `espressoWholePullFoam` version 0.1.3 compiled and completed the corrected R0 reference shot on OpenFOAM Foundation 12, exercised a deliberately heterogeneous layered-pressure fixture, reproduced independent analytical references, agreed with an independently implemented B0 finite-volume twin, and completed the standard ten-run `Allverify` qualification matrix. All ten individual runs passed and all nine aggregate qualification gates passed.

The corrected R0 reference calculation reported:

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
maximum liquid residual            6.00e-16 kg
maximum solute residual             1.84e-13 kg
```

The hardening release corrected the straight-sided-wedge full-cylinder scale, integrated the piecewise-linear pressure ramp exactly, removed the previous half-time-step first-drip bias, disabled ineffective binary compression, normalized unsafe archive timestamps automatically, streamed stage logs, recorded per-stage timing, and improved error classification. The corrected wedge volume, retained pore water, first-drip event and uniform Darcy flow agreed with their independent analytical references to approximately machine precision.

The layered fixture required as many as 122 pressure iterations, converged to a final pressure residual of approximately `8.13e-13`, and reproduced an independent discrete finite-volume flow and two pressure probes. This closes the principal concern that the exact zero-iteration uniform R0 pressure field was the only exercised pressure problem.

The OpenFOAM/B0 parity gates passed for first drip, final flow, cup water, cup solute, total beverage, TDS, extraction yield, retained dissolved solute, remaining extractable inventory and time to 40 g. Most global inventory differences were of order `1e-11` to `1e-12` relative, providing strong code-verification evidence for the bounded WP-0.1 equations. This remains verification of two implementations of the same declared model, not physical validation of real coffee.

The standard qualification campaign established bounded numerical sensitivity under the predeclared acceptance limits:

- the largest 0.020 s versus 0.005 s time-step difference was approximately **0.124%**, in remaining extractable mass;
- the largest 0.010 s versus 0.005 s difference was approximately **0.056%**, in retained dissolved solute;
- the largest 128×256 versus 512×1024 mesh difference was approximately **1.683%**, in retained dissolved solute;
- the largest 256×512 versus 512×1024 mesh difference was approximately **0.560%**, again in retained dissolved solute;
- 1-, 16-, 32- and 64-rank reference outputs agreed to a worst observed relative difference of approximately **2.23e-9**;
- the serial and 16-rank layered fixtures agreed to approximately `1e-12` or better for flow and both pressure probes.

These results qualify the present reference discretization and decomposition under the declared WP-0.1H gates. They do not constitute a formal proof of asymptotic order for every output. The most mesh-sensitive reported state is dissolved solute retained inside the puck; cup-level mass, first-drip, flow, TDS and extraction yield are substantially less sensitive over the tested matrix.

The rank study also provides an operational result. For the 131,072-cell reference case at `Δt = 0.01 s`, the measured solver times were approximately 212.77 s on one rank, 12.29 s on 16 ranks, 7.84 s on 32 ranks and 8.79 s on 64 ranks. Thirty-two ranks are therefore the best tested routine choice for this mesh; 64 ranks remain appropriate for the 512×1024 fine case and for selected equivalence checks.

WP-0.1H is consequently complete at the **code-verification and numerical-qualification level**. The remaining obstacle to an immutable reference freeze is smaller and release-engineering in nature. The reference acceptance report was generated before `Allverify`, so it still records `PENDING_FULL_ALLVERIFY` and contains no qualification-report link even though the subsequent qualification report passed. The case manifest also contains a stale acceptance-report hash because the current artifact design creates a circular dependency between the acceptance report and case manifest. One harmless mesh-volume metric was also misclassified as an issue because its log line contained the word “error.”

Version 1.2 therefore separates two concepts that must not be conflated:

```text
numerical qualification of the bounded WP-0.1 model: PASS
immutable release/provenance freeze of the archive:  PENDING v0.1.4
physical validation against independent coffee data: NOT ESTABLISHED
```

The immediate next release is v0.1.4, a no-new-physics finalization patch. It should break the circular hash chain, finalize the acceptance and run-status records after `Allverify`, add the remaining explicit bounded-state and monotonic-inventory gates, correct the diagnostic false positive, select 32 ranks as the routine R0 default, and generate a terminal freeze manifest after all other controlling artifacts are immutable. A fresh ZIP must then complete `./Allrun` and the standard `./Allverify` before WP-0.1 is formally frozen.

After that small release-engineering pass, the program should move to the distinct R1 source-linked reconstruction and formal Puckworks integration. The physics roadmap remains deliberately progressive: machine/headspace coupling, evolving structure, fines, channeling, thermal transport and multispecies chemistry are added only after the qualified R0 baseline is immutably bound and only to address a named residual, evidence need or engineering decision.

The model program continues to combine four capabilities:

1. **A whole-puck OpenFOAM multiphysics solver** for the machine–puck–basket system, initially dry wetting, pressure-driven porous flow, transport, extraction, and progressively evolving structure.
2. **High-resolution Taichi/LBM simulations** for pore-resolved hydraulics, morphology, fines-scale effects, dispersion, residence time, capture, clogging, and constitutive closure generation.
3. **Puckworks integration** as the authoritative knowledge, evidence, data, validation, semantic-contract, provenance, and model-comparison layer.
4. **Reduced models and surrogates** for independent verification, sensitivity analysis, uncertainty propagation, design exploration, and eventual engineering optimization.

The controlling development philosophy is now:

> **The whole-pull spine is numerically qualified. Freeze it immutably, connect it to source-linked evidence, and then extend it one mechanism at a time without losing conservation, traceability, or a runnable end-to-end model.**

## 1. Why Version 1.2 is a milestone update

### 1.1 What the 0.x program accomplished

The earlier program produced substantial, reusable foundations:

- a high-performance Taichi D3Q19 TRT lattice-Boltzmann implementation;
- one-field streaming and packed active-brick storage;
- a successful full 58 mm, 50 µm-class GPU production calculation;
- solver verification, low-Mach and low-Reynolds controls, memory accounting, convergence controls, and export infrastructure;
- fixed-geometry grid studies and progressively more disciplined SVE campaigns;
- evidence that porosity alone does not define hydraulic representativeness;
- evidence that nested internal crops and their imposed periodic closure can create a methodological ambiguity;
- an M1 geometry-method preflight;
- a B0 continuum numerical-verification framework for pressure nodes, Darcy resistance, filling, conservative transport, and solid–liquid–cup inventory;
- an A1 ingestion design and manufactured self-test;
- increasingly strong Puckworks contracts, model cards, data manifests, validation gates, and linked-model products.

These are not discarded. They remain verified or partially verified components, test ideas and evidence sources of the new architecture.

### 1.2 What Versions 1.0 and 1.1 changed

Version 1.0 corrected two earlier strategic extremes:

- treating synthetic morphology qualification, RVE/SVE promotion and new measured-anchor campaigns as prerequisites for any whole-process integration; and
- treating the future program primarily as orchestration of existing Puckworks models rather than as a new solver-development effort.

It established three controlling truths:

1. **A new whole-pull solver is required.** No registered Puckworks component currently represents a validated, spatially resolved, whole-process machine-to-cup simulation.
2. **Puckworks must remain authoritative.** The new solver must use the repository’s models, datasets, evidence levels, quantities, rights and validation gates rather than inventing an independent scientific universe.
3. **Progressive construction is essential.** The model must begin with a complete but bounded reference shot and add physics in verified increments.

Version 1.1 recorded the first successful Foundation-12 execution and correctly made numerical hardening, reduced-twin verification, discretization studies and reproducibility the immediate critical path.

### 1.3 What v0.1.3 and WP-0.1H have now established

The successful v0.1.3 run and standard qualification campaign establish that the bounded whole-pull architecture is numerically credible on the target system:

- Foundation OpenFOAM 12 compiles and runs the custom solver from a clean package;
- unsafe future timestamps are detected and normalized automatically;
- the 2D axisymmetric wedge case is generated deterministically;
- the exact straight-sided-wedge scale reproduces the nominal cylindrical volume;
- the pressure ramp is integrated exactly and first drip matches the closed-form result;
- the uniform Darcy flow matches its analytical reference;
- a heterogeneous layered fixture requires nonzero pressure iterations and reproduces independent flow and pressure references;
- OpenFOAM and the independent B0 twin agree on all required bounded-model outputs;
- the selected time-step and mesh sensitivity gates pass;
- 1-, 16-, 32- and 64-rank outputs are effectively equivalent;
- the 30 s reference shot remains conservative and bounded after the corrections;
- all expected final fields and reconstructed histories are present;
- a standard ten-run qualification campaign can be executed automatically and summarized in one machine-readable report.

This is a stronger milestone than mere execution. The project now has a **numerically qualified machine-to-cup computational spine** for its declared R0 equations.

### 1.4 What remains unestablished

The completed qualification does not establish:

- that the final archive is yet an immutable, internally self-consistent release record;
- formal source-specific reconstruction of Foster, Waszkiewicz, Cameron or another extraction source;
- independently measured permeability, wetting, extraction or dispersion parameters for R0;
- physical validation of first drip, flow, TDS or extraction yield for a protected real-coffee experiment;
- transfer across coffees, grinders, baskets, machines or recipes;
- validated swelling, compaction, fines migration, clogging or channeling;
- full machine/headspace/basket coupling;
- engineering optimization or taste prediction.

The approximately 40 g result remains a calibration-class endpoint because saturated permeability is the declared R0 hydraulic scale parameter. The extraction rate and concentration ceiling remain engineering assumptions for WP-0.1.

### 1.5 Strategic consequence

The program’s critical path has advanced again:

```text
successful whole-pull implementation
→ numerical hardening and qualification [ACHIEVED]
→ immutable freeze finalization [IMMEDIATE]
→ source-linked R1 reconstruction
→ Puckworks integration
→ one-mechanism-at-a-time physical expansion
→ independent holdouts and transfer.
```

The principal risk is no longer that the baseline equations are numerically uncontrolled. It is now that the project either overstates numerical qualification as physical validation or adds new physics before the qualified baseline is bound into an acyclic, immutable evidence record. Version 1.2 therefore makes a small v0.1.4 freeze-finalization release the immediate task and treats R1 as the next scientific milestone.

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

## 4. First flagship milestone: WP-0.1 numerically qualified

### 4.1 Purpose and current disposition

The first flagship milestone was intended to establish a minimal but complete computational path from pressure application to the cup and then qualify that path numerically before richer physics were added. Both implementation and the declared WP-0.1H qualification campaign have now completed successfully.

Controlling identifiers are:

```text
project package:       espresso_puck_whole_pull_reference_v0_1_3_openfoam12
solver:                espressoWholePullFoam
run status:            ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_3.json
reference acceptance:  ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_3.json
qualification report: ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_3.json
scenario:              reference_R0_20g_58mm_9bar
```

Current milestone disposition:

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
| Time-step qualification | PASS under declared thresholds |
| Mesh qualification | PASS under declared thresholds |
| 1/16/32/64-rank equivalence | PASS |
| Standard ten-run `Allverify` matrix | PASS; 9/9 aggregate gates |
| Numerical qualification of bounded WP-0.1 equations | PASS |
| Immutable release/provenance freeze | PENDING v0.1.4 finalization |
| Source-data reconstruction | NOT YET ESTABLISHED |
| Independent physical validation | NOT ESTABLISHED |

### 4.2 Canonical engineering reference scenario R0 as qualified

| Quantity | Qualified reference definition |
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
| Qualification time steps | 0.020, 0.010 and 0.005 s |
| Qualification meshes | 128×256, 256×512 and 512×1024 |
| Qualification ranks | 1, 16, 32 and 64 for R0; 1 and 16 for the layered fixture |
| Wetting | Sharp-front Darcy storage with exact piecewise-linear pressure integration |
| Saturated hydraulics | Uniform Darcy permeability; permeability is the declared R0 hydraulic calibration parameter |
| Extraction | One representative soluble inventory with spatial transport and exact inventory accounting |
| Primary outputs | First drip, flow, cup water and solute, total beverage mass, TDS, EY, retained inventories, balances and spatial fields |

The case is an engineering reference scenario, not a claim that all parameters describe one measured coffee, grinder, puck and machine experiment.

### 4.3 Corrected R0 outputs

| Output | v0.1.3 result |
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
| Maximum liquid-balance residual | **6.0021 × 10⁻¹⁶ kg** |
| Maximum solute-balance residual | **1.8397 × 10⁻¹³ kg** |
| Maximum estimated saturated pore Courant number | **0.797087** |

The total beverage mass is cup water plus exported dissolved solute. Retained liquid and retained dissolved material remain separately visible and are not silently added to the cup.

### 4.4 Mesh, field and execution quality

The corrected reference run used 131,072 cells, comprising 130,816 hexahedra and 256 prisms at the collapsed axis. `checkMesh -allGeometry -allTopology` retained the excellent mesh properties established in v0.1.2:

| Metric | Result | Interpretation |
|---|---:|---|
| Number of mesh regions | 1 | Correct connected domain |
| Maximum aspect ratio | 1.6059 | Excellent |
| Maximum non-orthogonality | 0° | Excellent |
| Maximum skewness | 0.3308 | Excellent |
| Minimum cell determinant | 0.8940 | Well-posed cells |
| Overall result | `Mesh OK` | PASS |

The corrected straight-sided-wedge scale was `72.0914664839846`. The scaled mesh volume agreed with the nominal cylindrical puck volume to a relative error of approximately `7.12e-16`.

The field index contains 339 files, covers the reconstructed integer time directories from 0 through 30 s, and records no missing final fields. Eleven expected final fields are present: `p`, `U`, `darcyFlux`, `saturation`, `wetMask`, `porosity`, `permeability`, `hydraulicMobility`, `dissolvedConcentration`, `remainingExtractable`, and `localExtractionRate`.

The 64-rank main `Allrun` completed 16 recorded stages in a summed stage duration of approximately 29.63 s, including about 8.68 s to rebuild the solver, 5.65 s for the parallel reference solve and 6.75 s to reconstruct all saved field times.

### 4.5 Numerical-hardening corrections completed

#### A. Straight-sided wedge scaling

The full-cylinder multiplier is now:

\[
\text{sectorScale}=\frac{2\pi}{\sin\theta},
\]

rather than `360/θdeg`. The analytical flow, scaled volume and retained pore-water tests pass to approximately machine precision.

#### B. Exact pressure-ramp integration

The sharp-front update now integrates the positive piecewise-linear pressure history exactly and locates breakthrough within the step. First drip agrees with the closed-form reference of `4.711696185231869 s` to approximately `1.15e-14 s`.

#### C. Heterogeneous pressure exercise

The layered fixture required up to 122 pressure iterations, converged to approximately `8.13e-13`, and matched an independent discrete one-dimensional flow solution and two pressure probes. This provides a meaningful pressure-equation stress test beyond the exact uniform R0 field.

#### D. Operational hardening

The package now:

- uses explicit Foundation 12 headers and source-root discovery;
- detects and normalizes future-dated solver and `Make` files automatically;
- performs clean `wclean`/`wmake` builds;
- streams stage logs while preserving complete files;
- records stage timings, source and executable hashes;
- writes uncompressed binary fields without the previous warning;
- treats `FOAM_SIGFPE` enablement as informational;
- emits a machine-readable run-status report on controlled success and failure.

### 4.6 B0 parity and analytical verification

All required OpenFOAM/B0 parity gates passed. First drip and final flow agreed at approximately machine precision. Cup and inventory outputs generally agreed to relative differences of order `1e-11` to `1e-12`, comfortably within the declared 0.5% inventory tolerance.

This establishes code verification for the bounded WP-0.1 equations and implementation. It does not validate the shared physical assumptions against real coffee.

### 4.7 Standard qualification campaign

The standard campaign completed ten runs and nine aggregate gates:

| Test family | Result | Largest observed difference |
|---|---|---:|
| All individual runs | 10/10 PASS | — |
| `Δt=0.020` versus `0.005 s` | PASS | 0.1242%, remaining extractable mass |
| `Δt=0.010` versus `0.005 s` | PASS | 0.0564%, retained dissolved solute |
| 128×256 versus 512×1024 | PASS | 1.6835%, retained dissolved solute |
| 256×512 versus 512×1024 | PASS | 0.5596%, retained dissolved solute |
| 16 versus 1 rank | PASS | 2.17e-9 relative |
| 32 versus 1 rank | PASS | 2.09e-9 relative |
| 64 versus 1 rank | PASS | 2.23e-9 relative |
| Layered fixture: 16 versus 1 rank | PASS | approximately 9.60e-13 relative for flow |

The tested matrix establishes bounded sensitivity under the predeclared WP-0.1H tolerances. It should not be described as a formal asymptotic-order study for every state variable. Retained dissolved solute is the most mesh-sensitive reported quantity; the cup-level outputs are much less sensitive.

### 4.8 Rank efficiency and routine execution policy

Measured solver times for the 256×512 reference mesh at `Δt=0.01 s` were:

| MPI ranks | Solver time |
|---:|---:|
| 1 | 212.77 s |
| 16 | 12.29 s |
| 32 | **7.84 s** |
| 64 | 8.79 s |

Thirty-two ranks are the best tested routine setting for the reference mesh. Sixty-four ranks were approximately 12% slower in solver time because communication overhead exceeded the benefit of the additional ranks. The fine 512×1024 mesh should continue to use 64 ranks unless a dedicated scaling study indicates otherwise.

### 4.9 Calibration and physical interpretation

The approximately 40 g endpoint is not an independent prediction because saturated permeability is the R0 hydraulic calibration parameter. The correct interpretation is:

> The declared WP-0.1 equations, calibrated hydraulic scale and engineering extraction closure produce a numerically qualified, conservative reference calculation under the bounded R0 assumptions.

The 11.69% TDS and 23.94% extraction yield are internally consistent but depend on the present extraction rate, extractable fraction, dispersion and concentration ceiling. They must not be represented as validated real-coffee chemistry until source-linked reconstruction and held-out comparison are completed.

First drip is a genuine model output and is numerically exact for the declared sharp-front closure, but the closure and wetting permeability have not yet been physically validated against an independent R0 measurement.

### 4.10 Remaining immutable-freeze defects

The remaining issues do not invalidate the numerical qualification, but they prevent the current v0.1.3 artifact set from being the permanent immutable release record:

1. The reference acceptance report was generated before the standard `Allverify` report and therefore still records `PENDING_FULL_ALLVERIFY` with a null qualification link.
2. The case manifest records an earlier acceptance-report hash. The final acceptance report was rewritten after the manifest, exposing a circular provenance dependency.
3. The diagnostic classifier reports the successful line `Mesh-volume relative error: ...` as an issue because it contains the token `error`.
4. Several useful physical-bound and monotonic-inventory gates are implicit rather than explicit.
5. The routine R0 rank default remains 64 even though 32 ranks were the best tested setting.

These are the scope of v0.1.4. No governing equation, calibration parameter or physical closure should change in that release.

### 4.11 Data-linked reference scenario R1

The next physical reconstruction remains distinct from R0 and should reproduce the best-defined Waszkiewicz rig context rather than forcing it into the 20 g engineering reference:

```text
18.5 g dose
58 mm basket
9 bar basket-pressure case
source-specific coffee, grind and calibration constants
source-defined pressure and flow nodes
```

R1 will be the principal pressure–flow reconstruction and comparison case. It should begin immediately after the v0.1.4 freeze-finalization run binds the R0 baseline immutably.

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

The software interfaces should remain additive so these mechanisms can be introduced without replacing the qualified conserved state and output contracts.

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

The executed reference shot uses Darcy flow and should use the Puckworks inertial model as a regime diagnostic before any Forchheimer branch is activated. Forchheimer physics should be activated only when the predicted regime and evidence justify it.

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

The v0.1.3 implementation can:

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

R0 prescribes bed-top pressure directly and sets the declared outlet to ambient gauge pressure. Machine delivery, compliance and downstream resistance are intentionally not yet solved as separate coupled components. The machine-coupled mode must use explicit node names and prevent any pressure drop from being counted both in the machine model and porous bed.

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
| Immutable freeze finalization | NEXT | Acyclic hashes and post-`Allverify` finalization |
| Data-linked R1 reconstruction | AFTER FREEZE | Source-specific comparison |
| Spatial heterogeneity and alternative closures | LATER | Named residual or decision need |
| Dynamic porosity/permeability | LATER | One mechanism at a time |
| Three-dimensional basket | LATER | Defined non-axisymmetric question |

### 6.5 Implemented field outputs

The qualified run reconstructs:

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

Later releases should add derived fields only where they support a scientific question, including pressure gradient, separate Darcy and inertial resistance, residence-time proxies, cumulative local extraction, channel indicators, fines inventories, and deformation state.

### 6.6 Output and communication discipline

The v0.1.3 package produces:

```text
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_3.json
ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_3.json
ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_3.json
ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_3.csv
ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_3.json
ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_3.json
ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_3.json
ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_3.json
ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_3.csv
reference_R0.foam
reconstructed OpenFOAM time directories
stage-specific log.* files
```

The run-status JSON communicates operational success or failure. The reference acceptance JSON records numerical/scientific acceptance of one R0 run. The qualification report records cross-run numerical evidence. The future freeze manifest will bind all controlling artifacts after they are final.

The separation remains controlling:

```text
operational success/failure
≠ single-run numerical acceptance
≠ cross-run numerical qualification
≠ source reconstruction
≠ physical validation.
```

### 6.7 Build and run reproducibility

The v0.1.3 target run confirms that the package now:

- uses explicit Foundation 12 headers rather than the obsolete `fvCFD.H` umbrella include;
- uses `FOAM_SRC` or `${WM_PROJECT_DIR}/src` in shell scripts rather than assuming `LIB_SRC` is exported;
- sources the Foundation environment safely under strict shell options;
- preflights required headers;
- normalizes unsafe future timestamps before dependency generation;
- performs a clean solver rebuild;
- streams and preserves compiler and stage logs;
- records the source-package aggregate, executable hash and build-provenance bundle;
- generates a run-status JSON on controlled success and failure;
- retains `./Allrun`, `./Allverify` and `./Allclean` as stable user entry points.

The remaining reproducibility task is not build execution but final evidence binding: the v0.1.4 artifact chain must be acyclic and must finalize acceptance only after standard qualification passes.

### 6.8 Independent verification twin

The B0 reduced architecture now operates as an independent one-dimensional finite-volume verification twin for:

- uniform Darcy flow;
- exact pressure-ramp integration and first drip;
- conservative one-solute transport;
- solid–liquid–cup inventory;
- retained liquid and dissolved solute;
- time to target beverage mass.

All required v0.1.3 parity gates passed. B0 remains a verification and rapid-sensitivity backend, not a substitute for source-linked physical validation.

### 6.9 Freeze-finalization contract

The final reference artifact chain should be acyclic:

```text
source package + configuration + generated case
                     ↓
solver outputs + traces + field index
                     ↓
reference acceptance + qualification report
                     ↓
final freeze manifest generated last
```

The case manifest should describe and hash scientific inputs, not mutable downstream reports. The acceptance report may hash immutable input and output artifacts. `Allverify` should finalize the reference acceptance and run status with the qualification path, hash and PASS status. The terminal freeze manifest should then hash every controlling artifact and no hashed artifact should be modified afterward.

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

The program must never collapse these into one “validated” label:

1. **Build and execution qualification:** does the package compile and complete on the declared platform?
2. **Code verification:** does the solver solve the declared equations?
3. **Numerical qualification:** are mesh, time-step, convergence, wedge representation and decomposition errors bounded?
4. **Release/provenance qualification:** are the controlling artifacts immutable, internally consistent and cryptographically bound?
5. **Component reconstruction:** does a branch reproduce the source paper or dataset it uses?
6. **Calibration:** were parameters fitted to the observed case?
7. **Independent validation:** does the model predict held-out observations?
8. **Mechanism discrimination:** do interventions distinguish competing explanations?
9. **Transfer:** does performance survive new coffees, grinders, machines, baskets or recipes?
10. **Decision utility:** does the model improve design or recipe choices over simpler baselines?

WP-0.1 has passed questions 1–3 for its bounded equations. Question 4 requires the v0.1.4 finalization patch. Questions 5–10 remain future scientific work.

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

**Current status:** pending. R1 is the first source-linked reconstruction milestone.

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

**Current status:** numerically qualified R0 calibration case. Physical validation is not established.

#### Level V4 — independent and intervention holdouts

**Current status:** not started.

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
| Liquid conservation | PASS |
| Solute conservation | PASS |
| Numerical qualification | PASS |
| Immutable release/provenance freeze | PENDING v0.1.4 |
| Calibrated hydraulic endpoint | YES |
| Source reconstruction | NOT YET |
| Independent validation | NO |
| Transfer qualification | NO |

A 40 g result after selecting permeability as the hydraulic scale parameter is an engineering calibration and cannot be reused as an independent validation gate.

### 9.4 Numerical qualification versus immutable freeze

The v0.1.3 standard report satisfies the declared numerical-qualification requirements:

- corrected wedge scaling;
- exact pressure-ramp integration;
- analytical first-drip and Darcy-flow agreement;
- a layered fixture with nonzero pressure iterations;
- selected time-step and mesh studies;
- serial and rank-count equivalence;
- OpenFOAM/B0 parity;
- clean target-system build and run;
- stage timing and build provenance;
- unchanged conservation and boundedness passes.

The following release-record requirements remain before the archive is frozen:

- remove the circular case-manifest/acceptance hash dependency;
- finalize acceptance and run status after `Allverify` rather than before it;
- include the qualification path, hash and PASS status in the finalized records;
- correct the mesh-volume diagnostic false positive;
- add explicit concentration-cap, remaining-inventory, retained-water-capacity and cumulative-mass monotonicity gates;
- select 32 ranks as the routine reference default;
- execute one fresh-ZIP `./Allrun` and standard `./Allverify`;
- generate one terminal freeze manifest after every other controlling artifact is immutable.

### 9.5 Evidence ceilings for prior and current work

- The A1 artifact is a manufactured self-test and does not supply measured real-coffee parameters.
- The B0 twin verifies numerical architecture and implementation agreement but not real-shot prediction.
- The M1 geometry preflight supplies a method candidate but not a real-coffee morphology or hydraulic closure.
- The M0 SVE campaigns verify numerical and statistical methods but do not establish real-coffee transfer.
- The v0.1.2 run establishes the first end-to-end implementation baseline.
- The v0.1.3 run and standard `Allverify` report establish numerical qualification of the bounded R0 implementation.
- Neither v0.1.2 nor v0.1.3 establishes independent physical validation of permeability, wetting, TDS, extraction yield or transfer.

These ceilings are controlling and must be carried into Puckworks cards, reports and public claims.

## 10. Progressive physics and chemistry roadmap

### Milestone WP-0.1 — Reference whole-pull implementation

**Status:** **COMPLETE**

Implemented physics:

- initially dry sharp-front wetting;
- prescribed bed-top pressure ramp to 9 bar;
- uniform Darcy flow;
- static porosity and permeability fields;
- one representative solute;
- fixed temperature;
- explicit retained and cup inventories;
- machine-readable conservation and acceptance reporting.

Outcome:

- a complete machine-to-cup 30 s calculation;
- corrected first-drip and full-cylinder scaling;
- all declared run-level gates passed;
- a stable end-to-end computational spine.

### Milestone WP-0.1H — Numerical hardening and qualification

**Status:** **NUMERICAL QUALIFICATION COMPLETE; IMMUTABLE FREEZE FINALIZATION PENDING**

Completed:

- exact straight-sided-wedge scaling;
- exact pressure-ramp integration;
- analytical wedge-volume, Darcy-flow and first-drip gates;
- layered heterogeneous-pressure fixture;
- selected time-step and mesh qualification matrix;
- 1/16/32/64-rank equivalence;
- OpenFOAM/B0 parity;
- automatic timestamp normalization and clean Foundation 12 build;
- live logging, stage timings and build provenance;
- standard ten-run `Allverify` campaign with 9/9 aggregate gates passed.

The numerical work originally intended by WP-0.1H is complete. The terminal release record is not yet frozen because of the artifact-finalization issues described below.

### Milestone WP-0.1F — Immutable freeze finalization

**Status:** **IMMEDIATE CRITICAL PATH**

Deliver v0.1.4 with no governing-physics changes:

- break the case-manifest/acceptance circular hash dependency;
- finalize acceptance and run status after standard `Allverify`;
- add the qualification path, hash and PASS status;
- correct the diagnostic false positive;
- add explicit bounded-state and monotonic-inventory gates;
- set 32 ranks as the routine R0 default;
- generate a final freeze manifest last;
- complete a fresh-ZIP `./Allrun` and standard `./Allverify`;
- mark WP-0.1H `FROZEN / QUALIFIED` only after all finalization gates pass.

### Milestone WP-0.1R — Source-linked reference qualification

**Status:** **NEXT SCIENTIFIC MILESTONE AFTER WP-0.1F**

Required work:

- implement R1 as a distinct Waszkiewicz-linked 18.5 g, 58 mm, 9 bar case;
- reconstruct source-defined pressure and flow nodes;
- compare with the relevant Q(t), permeability and poroelastic evidence;
- compare first-drip and wetting behavior with Foster-informed evidence where compatible;
- compare one-solute output with a selected extraction source;
- state calibration inputs, protected comparison outputs and evidence ceilings;
- register reduced artifacts and findings in Puckworks.

### Milestone WP-0.2 — Machine and hydraulic integration

Add:

- pump/headspace compliance;
- explicit machine control profile;
- measured pressure-node adapters;
- Darcy/Forchheimer branch;
- bounded radial/depth heterogeneity;
- uncertainty in permeability and wetting;
- a clear pump–bed operating-point solution rather than prescribed bed-top pressure where data support it.

### Milestone WP-0.3 — Evolving puck

Add as separate branches:

- poroelastic compaction;
- swelling;
- dissolution-driven porosity change;
- concentration-dependent viscosity;
- state-dependent permeability.

Use common observables to compare their effects, and do not hide them inside one generic fitted `K(t)`.

### Milestone WP-0.4 — Fines and channeling

Add:

- Eulerian mobile and bound fines inventories;
- deposition and release;
- local permeability feedback;
- optional Lagrangian particles;
- Taichi-derived capture/clogging closures;
- non-axisymmetric 3D cases for localization;
- channel diagnostics rather than an arbitrary binary “channel” flag.

### Milestone WP-0.5 — Thermal and multispecies chemistry

Add:

- transient energy equation;
- temperature-dependent viscosity and diffusivity;
- multiple soluble species;
- size-dependent intraparticle diffusion;
- partition and equilibrium limits;
- species-specific cup accumulation;
- selected gas effects if evidence requires them.

### Milestone WP-0.6 — Equipment and recipe design

Add:

- basket hole field and outlet geometry;
- bottom paper/filter branches;
- screen and plenum resistance;
- pressure/flow/temperature profile design;
- machine compliance and control;
- grinder/PSD and dose/tamp sensitivity;
- surrogate and robust optimization.

### Milestone WP-1.0 — Evidence-qualified engineering platform

A mature release requires:

- protected holdout performance;
- uncertainty calibration;
- transfer-domain limits;
- simple-baseline comparisons;
- decision-ranking evidence;
- extrapolation rejection;
- public reproducibility.

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
- successful 64-rank full-field R0 execution;
- completed 1/16/32/64-rank reference equivalence study;
- completed coarse/reference/fine mesh study;
- completed three-time-step study;
- completed serial/parallel layered-fixture study.

### 12.2 GPU policy

- use Taichi for high-throughput pore-scale work;
- preserve atomic checkpoints and resumable campaigns;
- keep each monitored campaign bounded;
- use geometry-only preselection before expensive flow;
- use paired/multifidelity designs rather than blind repetition;
- export only fields required for the closure or diagnostic;
- require every campaign to answer a closure, uncertainty or validation question consumed by the whole-pull model.

### 12.3 CPU/OpenFOAM policy after qualification

- preserve the 2D axisymmetric wedge as the regression and qualification baseline;
- use **32 MPI ranks** as the routine default for the 256×512 reference mesh;
- retain 1, 16 and 64 ranks for regression/equivalence checks rather than routine execution;
- use 64 ranks for the 512×1024 fine mesh unless later scaling evidence supports another setting;
- report solver time separately from mesh generation, reconstruction and postprocessing;
- repeat performance runs before making hardware-general scaling claims;
- use mesh and time-step studies only when equations, numerics or sensitive outputs change materially;
- write complete field histories only for reference/review runs and use reduced output for sweeps;
- scale to 3D only for a defined non-axisymmetric question;
- maintain deterministic case generation from versioned configuration;
- store reduced traces and immutable hashes even when large field data remain external.

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

The numerical error budget for the current R0 cup-level outputs is small relative to the unresolved physical-model uncertainty:

- time-step sensitivity is at most approximately 0.124% over the tested endpoints;
- reference-versus-fine mesh sensitivity is at most approximately 0.560%, driven by retained dissolved solute;
- cup mass differs by only approximately 0.005% between reference and fine meshes;
- TDS differs by approximately 0.039%;
- extraction yield differs by approximately 0.044%;
- rank-count differences are of order `1e-9` relative.

The selected 256×512 mesh and 0.02 s main-run step are qualified for the current R0 outputs under the declared thresholds. For future chemistry-focused work, the mesh should be revisited because in-puck retained dissolved solute is the most sensitive quantity.

The time-step sequence is not perfectly monotonic for every output. The correct claim is **bounded time-step sensitivity**, not a demonstrated formal order of convergence.

### 12.6 Measured rank performance

| Ranks | Solver time at 256×512 and `Δt=0.01 s` | Relative interpretation |
|---:|---:|---|
| 1 | 212.77 s | serial reference |
| 16 | 12.29 s | strong speed-up |
| 32 | **7.84 s** | fastest tested |
| 64 | 8.79 s | communication overhead exceeds added compute benefit |

The 32-rank result provides approximately a 27× solver speed-up over serial for this case. These are single measured runs on the present system and should guide local defaults, not be presented as universal scaling laws.

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

### 13.1 Current implementation and proposed repository layout

The successful v0.1.3 package and complete qualification directories should be preserved as raw evidence. The v0.1.4 freeze package should then become the immutable integration baseline. Subject to a fresh review of the current Puckworks main branch, the intended layout remains:

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
```

Large OpenFOAM and Taichi field artifacts may remain outside Git, but reduced results, manifests, validation summaries and immutable checksums belong in Puckworks.

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

The program should use four distinct machine-readable layers:

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
final freeze status and timestamp
```

The terminal freeze manifest is generated last and no artifact it hashes may subsequently be modified.

### 13.4 Acyclic provenance rule

The v0.1.3 case manifest and acceptance report currently hash one another indirectly, so sequential updates make one hash stale. The v0.1.4 design must remove that cycle:

- the **case/scientific-input manifest** hashes only source, configuration and generated case inputs;
- the **field index** hashes field artifacts;
- the **acceptance report** hashes the immutable case manifest, traces and field index;
- the **qualification report** hashes individual acceptance reports;
- the **freeze manifest** hashes all final controlling artifacts and is generated last;
- no earlier artifact needs to contain the freeze-manifest hash.

This order permits every recorded hash to remain true simultaneously.

### 13.5 Baseline preservation and reproducibility

Preserve two evidence states:

1. **v0.1.3 raw qualification evidence**, including the complete case, qualification runs, logs and known metadata defects;
2. **v0.1.4 immutable freeze evidence**, generated by one clean `Allrun` followed by standard `Allverify` and terminal finalization.

The final baseline must record:

- package and source-manifest hashes;
- solver source and executable hashes;
- OpenFOAM build and environment;
- scientific configuration and generated dictionaries;
- run-status, timing, acceptance and qualification hashes;
- reduced traces and field index;
- selected external field-archive identity;
- calibration role and claim ceiling;
- preparation, output-finalization and freeze-finalization timestamps.

### 13.6 Integration rule

Do not merge the solver into Puckworks merely as a large code drop. Integration should include:

- a component/backend card;
- an R0 scenario contract;
- model and data provenance;
- numerical-qualification and validity gates;
- reduced result fixtures;
- a clear rights posture;
- novice-facing execution documentation;
- links to immutable external field artifacts;
- a roadmap entry for R1 and future physics branches;
- explicit separation of numerical qualification, calibration and physical validation.

## 14. Acceptance framework and WP-0.1 disposition

### 14.1 Gates passed by v0.1.3

The corrected R0 run passed:

- Foundation 12 environment selection;
- solver compilation and linking;
- deterministic case preparation;
- automatic timestamp-safety checks;
- `blockMesh` completion;
- full topology and geometry checks;
- exact straight-sided-wedge volume equivalence;
- exact sharp-front first-drip equivalence;
- analytical uniform Darcy-flow equivalence;
- retained-water/cylindrical-volume equivalence;
- heterogeneous layered-pressure fixture;
- 64-rank reference decomposition and 30 s completion;
- bounded pressure and concentration residuals;
- finite and bounded declared trace variables;
- maximum estimated saturated pore Courant of approximately 0.797;
- liquid inventory balance;
- solute inventory balance;
- reconstruction of all requested fields;
- all required OpenFOAM/B0 parity gates;
- creation of the acceptance, trace, manifest, field-index, timing and ParaView artifacts;
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

### 14.3 Remaining gates for immutable release freeze

The v0.1.4 freeze is accepted only when:

- the case/acceptance circular hash dependency is removed;
- `Allverify` finalizes the reference acceptance and run status;
- the final acceptance records `QUALIFIED` and the qualification path/hash;
- the diagnostic issue count excludes successful “relative error” metric lines;
- concentration is explicitly bounded by the declared saturation concentration plus tolerance;
- remaining extractable material is explicitly bounded between zero and the initial inventory;
- retained water is explicitly bounded by saturated pore capacity;
- cumulative inlet water, cup water and cup solute are explicitly monotonic;
- 32 ranks are the routine R0 default while rank overrides remain supported;
- one fresh ZIP completes `./Allrun` and standard `./Allverify`;
- a final freeze manifest is generated last and all its hashes verify;
- no governing-physics, calibration or closure change has been introduced relative to qualified v0.1.3.

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
- every calibrated parameter and the observations used to set it.

### 14.5 Claim ceiling after numerical qualification

The current evidence supports:

> The v0.1.3 OpenFOAM whole-pull reference implementation is numerically qualified across its declared analytical, reduced-twin, heterogeneous-pressure, time-step, mesh and MPI-decomposition tests for a bounded R0 calibration scenario.

It does not support:

- independent validation of the approximately 40 g endpoint;
- validated first-drip, TDS or extraction-yield prediction for a real coffee;
- universal real-coffee prediction;
- validated channeling, fines or evolving structure;
- transfer across coffees or equipment;
- taste prediction;
- engineering optimization.

After v0.1.4 passes, the archive may additionally be called an **immutably frozen numerical baseline**. Physical-validation claims still require R1 and held-out evidence.

### 14.6 Required output files

The final reference package should retain:

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
ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
OpenFOAM field archive / ParaView-readable case
stage-specific build and execution logs
```

The run status communicates execution. The acceptance report governs one reference run. The qualification report governs numerical sensitivity and equivalence. The freeze manifest is the terminal provenance root.

## 15. Validation and experiment strategy

### 15.1 What numerical qualification changes

R0 now provides a numerically qualified model against which evidence can be mapped and physical-model sensitivity can be measured. For the current bounded equations, discretization and decomposition uncertainty are small relative to the unresolved uncertainty in permeability, wetting, extraction kinetics, concentration capacity and real puck evolution.

The qualification campaign also identifies retained dissolved solute as the most mesh-sensitive reported state. Experiments or future source comparisons concerned with in-puck chemistry should therefore receive stricter spatial-resolution review than cup-mass or first-drip studies.

New data should be requested because a named parameter, closure or competing mechanism is load-bearing—not because additional data would be generally interesting.

### 15.2 Use current Puckworks evidence first

The next source-linked work should use and compare with the repository’s available:

- 9-bar flow traces and pressure–flow calibration;
- CT infiltration and first-drip evidence;
- PSD and permeability measurements;
- tamped-permeability references;
- extraction and TDS data;
- species-resolved independent evidence;
- swelling and flow-decay references;
- fines and dynamic-flow signatures;
- liquor property data.

The repository baseline must be refreshed before integration so newer model cards, data, rights records and whole-pull-related work are not missed.

### 15.3 R1 as the first data-linked reconstruction

R1 should be built as a source-specific case rather than by relabelling R0. It must declare:

- the 18.5 g dose and rig geometry;
- coffee and grind descriptors where available;
- pressure measurement node;
- outlet and downstream resistance definition;
- permeability or poroelastic calibration role;
- source Q(t) and uncertainty;
- which observations are used for calibration;
- which features remain comparison or holdout targets.

R1 is the first opportunity to test whether the qualified baseline hydraulic architecture reproduces source-linked dynamics beyond the calibrated R0 endpoint.

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
- acceptance and qualification concepts;
- output and claim ceiling.

Remaining documentation task:

- convert the implemented and qualified configuration into a formal `ESPRESSO_WHOLE_PULL_REFERENCE_SPEC_V0_1.md` aligned with the actual solver and final freeze schema.

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

**Status:** complete at the code-verification/numerical-qualification level.

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

**Status:** immediate next phase.

Deliver v0.1.4 with no governing-physics change:

- acyclic artifact provenance;
- post-`Allverify` acceptance/run-status finalization;
- explicit bounded-state and monotonicity gates;
- corrected issue classification;
- 32-rank reference default;
- fresh-ZIP `Allrun` and standard `Allverify`;
- terminal freeze manifest;
- formal WP-0.1H `FROZEN / QUALIFIED` designation.

### Phase E — Data-linked R1 and Puckworks integration

Implement:

- R1 18.5 g / 58 mm / 9 bar source-specific case;
- Waszkiewicz-linked pressure and flow comparisons;
- Foster-linked wetting comparison where compatible;
- selected extraction-source reconstruction;
- component/backend card;
- scenario and state adapters;
- source and data bindings;
- validation and validity gates;
- CLI/API entry point;
- novice-facing local run guide;
- immutable links to external field artifacts.

### Phase F — Hydraulic and machine expansion

Proceed to WP-0.2 only after the baseline is frozen and R1 exposes the most important hydraulic residuals. Add machine pressure nodes, compliance, flow control, inertial diagnostics and bounded heterogeneity.

### Phase G — Dynamic and multiscale upgrades

Proceed in the milestone order defined in Section 10. Select each new physics branch by sensitivity, evidence and its ability to improve a named holdout or engineering decision.

## 17. Immediate next actions

The following sequence is controlling.

### Preserve the complete v0.1.3 evidence

1. **Do not clean or overwrite the successful v0.1.3 reference case or qualification directories.** Preserve all JSON, CSV, logs, reconstructed fields, qualification-run cases and the layered fixture.
2. **Archive the known-good numerical evidence separately from the future freeze package.** The v0.1.3 data remain the raw evidence even though their final metadata chain is imperfect.
3. **Record the uploaded artifact hashes and source/build provenance.** Preserve the source-package aggregate, executable hash, scientific-input bundle, run-status, acceptance, qualification, timing and field-index identities.

### Build v0.1.4 as a no-physics finalization release

4. **Do not alter governing equations, R0 parameters, calibration, closures or qualification tolerances.** v0.1.4 is a provenance and acceptance-contract patch.
5. **Break the circular hash dependency.** Restrict the case manifest to scientific inputs and generate the terminal freeze manifest last.
6. **Finalize after `Allverify`.** Update the reference acceptance and run status only after the standard qualification report passes; record the qualification path, hash and `PASS` status.
7. **Add explicit physical-bound gates.** Check the concentration ceiling, remaining inventory bounds, retained-water capacity and monotonic cumulative inlet/cup inventories.
8. **Correct diagnostic classification.** Successful metric lines containing “relative error” must not increment the issue count; actual numerical exceptions and failed gates must remain detectable.
9. **Use 32 ranks as the routine R0 default.** Retain explicit `NPROCS` overrides and the qualified 1/16/32/64 regression matrix.
10. **Add distinct timestamps.** Record preparation, output finalization, qualification completion and freeze finalization.

### Requalify and freeze

11. **Extract the v0.1.4 ZIP into a fresh directory and run `./Allrun`.** No manual file edits, timestamp fixes or dictionary changes are permitted.
12. **Run the standard `./Allverify`.** Smoke mode does not qualify the release.
13. **Generate and verify the terminal freeze manifest.** It must bind source, executable, scientific case, traces, fields, acceptance, qualification, timings and environment without any stale hashes.
14. **Mark WP-0.1H `FROZEN / QUALIFIED` only after every finalization gate passes.** Preserve the physical-validation status as `NOT_ESTABLISHED`.
15. **Publish a concise WP-0.1H result note and formal reference specification.** State what was verified, what was calibrated, what remains an engineering assumption and what evidence is still needed.

### Move to source-linked evidence and Puckworks

16. **Refresh the Puckworks repository review.** Confirm current main, model cards, source data, rights, contracts and existing whole-pull-related work.
17. **Implement R1 as a distinct Waszkiewicz-linked case.** Do not modify R0 into a fictitious measured experiment.
18. **Reconstruct one extraction source explicitly.** Use the same hydraulic history to compare at least one alternative closure and expose chemistry sensitivity.
19. **Integrate the frozen solver as a governed backend.** Add cards, manifests, adapters, reduced fixtures, validity findings and external field-artifact links.

### Expand physics only for named needs

20. **Begin WP-0.2 with the most load-bearing source-linked hydraulic residual.** Likely candidates are machine/headspace coupling, pressure-dependent permeability or bounded radial/depth heterogeneity.
21. **Do not add fines, channeling, multispecies chemistry or dynamic geometry merely because the solver can support them.** Add each only for a named residual, closure request, experiment or engineering decision.

## 18. Program risks and controls

| Risk | Consequence | Control |
|---|---|---|
| Numerical qualification is presented as physical validation | Overstated confidence in real-coffee prediction | Preserve the calibration role and `PHYSICAL_VALIDATION_NOT_ESTABLISHED` label in every artifact and public statement |
| Stale `PENDING_FULL_ALLVERIFY` metadata obscures a passed campaign | Confusing or contradictory release record | Finalize acceptance and run status after standard `Allverify` in v0.1.4 |
| Circular manifest/acceptance hashes | One recorded hash becomes false after finalization | Use an acyclic artifact chain and generate a terminal freeze manifest last |
| Successful metric lines are classified as issues | False alarms and reduced trust in diagnostics | Classify by gate status and structured patterns, not the token `error` alone |
| New physics is added before immutable baseline freeze | Regression causes become difficult to identify | Complete WP-0.1F before any governing-physics change |
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
| Repository integration becomes only documentation | New solver loses evidence discipline | Make Puckworks manifests, contracts and gates mandatory run inputs/outputs |
| Puckworks orchestration replaces innovation | No new coupled physics | Keep the OpenFOAM whole-pull solver as the program spine |
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

## 20. Version 1.2 controlling summary

The Puckworks modeling and simulation program now has a numerically qualified whole-process espresso reference solver.

The v0.1.3 Foundation OpenFOAM 12 implementation completed the corrected 30 s R0 calculation, passed exact wedge-volume, first-drip and Darcy-flow checks, exercised a heterogeneous layered pressure problem, agreed with an independent B0 twin, and completed a ten-run time-step, mesh and MPI qualification campaign with all nine aggregate gates passing. Liquid and solute balances close near machine precision, all expected fields are reconstructed, and rank-count differences are negligible across 1, 16, 32 and 64 ranks.

The qualified R0 result is approximately 40.96 g beverage at 30 s, first drip at 4.7117 s, final flow at 1.48268 mL/s, TDS at 11.689% and extraction yield at 23.938%. These values are outputs of a bounded calibration scenario: saturated permeability sets the hydraulic scale and the one-solute extraction closure remains an engineering assumption.

The numerical qualification is complete under the declared WP-0.1H gates. The archive is not yet the permanent frozen baseline because the acceptance report was created before the successful `Allverify` report, the case-manifest/acceptance design creates a stale circular hash, and one successful metric is falsely classified as an issue. These are release-engineering defects, not failures of the numerical campaign.

The immediate task is therefore v0.1.4, with no governing-physics change. It must create an acyclic artifact chain, finalize acceptance after qualification, add explicit bounded-state and monotonicity gates, correct diagnostics, select 32 ranks as the routine R0 default, complete a fresh clean run and standard qualification, and generate one terminal freeze manifest.

After that immutable freeze, the next scientific milestone is R1: a distinct source-linked 18.5 g, 58 mm, 9 bar reconstruction, followed by formal Puckworks integration and one-mechanism-at-a-time physical expansion.

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

> **The bounded whole pull is numerically qualified. Freeze it immutably, test it against source-linked evidence, and then make it more physically complete one mechanism at a time.**

## Appendix A — Controlling evidence from completed work

| Artifact/work | Retained conclusion in Version 1.2 |
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
| v0.1.3 provenance review | Numerical qualification is valid; immutable freeze awaits acyclic finalization in v0.1.4 |

## Appendix B — WP-0.1H qualified reference outputs

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
| Maximum liquid residual | 6.002143227 × 10⁻¹⁶ kg |
| Maximum solute residual | 1.839677287 × 10⁻¹³ kg |
| Maximum pressure final residual | 9.251332404 × 10⁻¹⁵ |
| Maximum concentration final residual | 9.978814165 × 10⁻¹² |
| Maximum concentration iterations | 4 |
| Maximum estimated saturated pore Courant | 0.797086602 |
| Straight-sided wedge scale | 72.091466484 |
| Scaled-volume relative error | 7.115076757 × 10⁻¹⁶ |

### Analytical and reduced-twin checks

| Check | Result |
|---|---:|
| First-drip absolute error versus analytical reference | 1.1546 × 10⁻¹⁴ s |
| Uniform Darcy-flow relative error | 8.2837 × 10⁻¹⁵ |
| Retained-water relative error | 1.1325 × 10⁻¹⁵ |
| Largest required OpenFOAM/B0 global-output relative difference | approximately 4.62 × 10⁻¹¹ |
| Layered fixture maximum pressure iterations | 122 |
| Layered fixture maximum final pressure residual | 8.1303 × 10⁻¹³ |

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

The field index contains 339 files and no missing final fields.

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
- code verification and numerical qualification pass;
- immutable release freeze awaits v0.1.4;
- physical validation is not established.

## Appendix C — Initial Puckworks repository deliverables

```text
docs/WHOLE_PULL_STRATEGY.md

docs/WHOLE_PULL_REFERENCE_SPEC.md

docs/WHOLE_PULL_VALIDATION.md

puckworks/whole_pull/

puckworks/backends/openfoam.py

puckworks/backends/taichi_closure.py

puckworks/backends/reduced_b0.py

solvers/openfoam/espressoWholePullFoam/

solvers/openfoam/cases/reference_R0_20g_58mm_9bar/

solvers/openfoam/cases/waszkiewicz_R1_18p5g_9bar/
```

Exact paths and registration IDs remain subject to a fresh repository review, but the architectural division is controlling.

---

## Appendix D — WP-0.1H v0.1.3 evidence record

| Item | Recorded value |
|---|---|
| Execution date | 27 July 2026 |
| Package | `espresso_puck_whole_pull_reference_v0_1_3_openfoam12` |
| Solver | `espressoWholePullFoam` 0.1.3 |
| OpenFOAM | Foundation 12, build `12-0f458291f1cd` |
| Compiler/options | GCC optimized, double precision, 32-bit labels |
| Main R0 MPI execution | System OpenMPI, 64 ranks |
| Qualification ranks | 1, 16, 32 and 64; layered 1 and 16 |
| Host | `<HOSTNAME>` |
| Logical CPUs reported | 128 |
| Run status | PASS / COMPLETED |
| Reference acceptance | PASS; all numerical and B0 gates pass |
| Standard qualification | PASS / COMPLETED; 9/9 aggregate gates |
| Source-package aggregate SHA-256 | `f70e2e2c03ed041e1320257fa956eb66ca5f6b626d1bd9633d12920a1a7a3b03` |
| Solver executable SHA-256 | `9d8010f70f17597e3f6fdff4977805e7f99b5959895f3f6ca05901caaa6e0448` |
| Source/executable bundle SHA-256 | `95084b82f3d6cf1e262df9da2b60b1e07c0d7b4785270c7e1ffa6deb040d370a` |
| Scientific-input bundle SHA-256 | `3c8abd9af426a7212ddbd6da08426af0c4661868fc6f06506bc28a626809ce2e` |
| Uploaded run-status SHA-256 | `e820fd55c23d8a5325a9ced8993c5577f6dcb3482fd219dc7b75e2e1db41e37d` |
| Uploaded acceptance SHA-256 | `ca7a719f501c913e0db371051bdd16fc2337098e5b6a82a367ffcfb482efa0e1` |
| Uploaded qualification SHA-256 | `56b22c062595613e297b944843aaaef053c7e68328973502344a1087778e8987` |
| Uploaded stage-timings SHA-256 | `d0d6535365fc4d0337cefc0df4d73db6e008843c37c2dc4fd284569dc1e28073` |
| Uploaded field-index SHA-256 | `0d6e8586ffb5ff666c9b70819c20862de3d9cdc98ff735c895f986712593b371` |
| Uploaded case-manifest SHA-256 | `c3dc1350f1ad5aa26c4df46a80456b2061403063cca254ce90c818af0b1b46cd` |
| Uploaded scenario SHA-256 | `f390a4fd150345d8064ee695c3f2c491e75ff8a58b5ec73d675e843d12c8cc31` |
| Numerical disposition | QUALIFIED |
| Physical-validation disposition | NOT ESTABLISHED |
| Freeze caveat | Acceptance metadata predates `Allverify`; case manifest contains a stale acceptance hash; terminal freeze pending v0.1.4 |

The complete v0.1.3 case and qualification directories, rather than this summary alone, are the controlling raw evidence. The future v0.1.4 freeze manifest will become the terminal immutable reference record.

## Appendix E — Completed WP-0.1H verification matrix

| Test family | Cases | Result | Controlling observation |
|---|---|---|---|
| Pressure-ramp time integration | 0.020, 0.010, 0.005 s on reference mesh | PASS | First drip invariant because ramp integration is exact |
| Time-step sensitivity | 0.020/0.010 versus 0.005 s | PASS | Maximum difference 0.1242% |
| Mesh sensitivity | 128×256, 256×512, 512×1024 at 0.010 s | PASS | Maximum reference-versus-fine difference 0.5596% |
| Rank equivalence | 1, 16, 32, 64 ranks | PASS | Worst output difference 2.23e-9 relative |
| Rank efficiency | same reference mesh/time step | COMPLETE | 32 ranks fastest tested |
| Wedge scaling | mesh volume and analytical cylinder | PASS | Relative volume error 7.12e-16 |
| Heterogeneous pressure | layered permeability | PASS | 122 iterations; flow/probes match independent reference |
| B0 parity | matched R0 equations | PASS | All required outputs pass |
| Clean-package reproducibility | fresh v0.1.3 target execution | PASS | No manual timestamp correction required |
| Standard aggregate qualification | ten runs, nine gates | PASS | 9 PASS / 0 FAIL |

The matrix establishes bounded sensitivity for the declared outputs and thresholds. It does not establish physical validity or formal asymptotic convergence order for every state variable.

---

## Appendix F — v0.1.4 immutable-freeze acceptance contract

### Required no-physics changes

- acyclic case, acceptance, qualification and freeze manifests;
- post-qualification finalization of acceptance and run status;
- correct qualification link and hash;
- corrected diagnostics;
- explicit bounded-state and monotonic-inventory gates;
- 32-rank routine R0 default;
- separate preparation, output-finalization, qualification and freeze timestamps.

### Required execution sequence

```text
fresh ZIP extraction
→ ./Allrun
→ standard ./Allverify
→ finalize reference acceptance and run status
→ verify all artifact hashes
→ generate terminal freeze manifest
→ verify terminal freeze manifest
→ mark WP-0.1H FROZEN / QUALIFIED.
```

### Required terminal status

```text
implementation_status:             PASS
code_verification_status:          PASS
numerical_qualification_status:    PASS
release_provenance_status:         PASS
reference_freeze_status:           QUALIFIED / FROZEN
calibration_mode:                  R0 hydraulic calibration
physical_validation_status:        NOT_ESTABLISHED
next_scientific_milestone:         WP-0.1R
```

No solver result should be called the frozen WP-0.1 baseline until this contract passes.
