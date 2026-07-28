# Espresso puck whole-pull reference v0.1.4

**Target:** OpenFOAM Foundation 12 on 64-bit Linux  
**Release role:** WP-0.1F no-physics-change freeze finalization  
**Routine R0 execution:** 32 MPI ranks by default  
**Controlling strategy:** `docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md`

Version 0.1.4 converts the numerically qualified v0.1.3 WP-0.1 baseline into an acyclic, cryptographically bound release record. It does **not** add or retune governing physics.

The OpenFOAM solver source, reduced verification mathematics, physical scenario projections, Make contracts, initial fields, and finite-volume discretization dictionaries are checked against the target-qualified v0.1.3 source contract. A passing no-physics-change report requires all 28 comparisons to pass.

## Required workflow

Use a fresh extraction of the archive:

```bash
unzip espresso_puck_whole_pull_reference_v0_1_4_openfoam12.zip
cd espresso_puck_whole_pull_reference_v0_1_4_openfoam12
```

Run the reference model:

```bash
./Allrun
```

Then run the complete numerical qualification and freeze finalization:

```bash
./Allverify
```

The reference is frozen only when standard `./Allverify` completes and creates:

```text
cases/reference_R0_20g_58mm_9bar/
  ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
```

A passing `./Allrun` by itself establishes a successful reference execution, but deliberately leaves:

```text
reference_freeze_status: NOT_FROZEN
```

`./Allrun` invokes the newly built solver through its recorded absolute `FOAM_USER_APPBIN` path, rather than resolving a same-named program through `PATH`. Standard `./Allverify` then reuses and verifies those **exact executable bytes and that exact absolute path**; it does not silently rebuild or qualify a different linker product. `./Allrun` also archives byte-identical executable contents at:

```text
cases/reference_R0_20g_58mm_9bar/preflight/espressoWholePullFoam_v0_1_4
```

The terminal manifest binds that portable copy so the freeze remains auditable even if the OpenFOAM user-application directory later changes.

## OpenFOAM environment

The scripts require:

```text
WM_PROJECT=OpenFOAM
WM_PROJECT_VERSION=12
```

The standard Foundation user installation is detected automatically, including:

```text
$HOME/OpenFOAM/OpenFOAM-12/etc/bashrc
/opt/openfoam12/etc/bashrc
```

A nonstandard environment can be selected explicitly:

```bash
OPENFOAM_BASHRC=/path/to/OpenFOAM-12/etc/bashrc ./Allrun
```

The routine R0 default is 32 ranks, selected from the qualified v0.1.3 rank study for the 131,072-cell mesh. Override it where required:

```bash
NPROCS=16 ./Allrun
NPROCS=64 ./Allrun
```

The standard qualification matrix itself retains the predeclared 1-, 16-, 32-, and 64-rank comparisons.

## What `./Allrun` performs

`./Allrun`:

1. removes prior reference, fixture, qualification, and freeze runtime products;
2. loads and verifies OpenFOAM Foundation 12;
3. verifies the source-package manifest;
4. runs static package validation;
5. proves no governing-physics change from qualified v0.1.3;
6. runs the Python test suite;
7. normalizes unsafe future timestamps;
8. clean-builds `espressoWholePullFoam` and records source/executable provenance;
9. runs the mandatory heterogeneous two-layer pressure fixture;
10. generates and checks the 256 × 512 × 1 reference wedge mesh;
11. runs the 30 s R0 simulation, in parallel by default;
12. reconstructs the requested field history;
13. generates traces, field index, scientific-input manifest, acceptance report, timings, and one machine-readable run-status file.

The primary operational artifact is:

```text
cases/reference_R0_20g_58mm_9bar/
  ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
```

On a successful reference run, preserve at least:

```text
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_TRACES_V0_1_4.csv
ESPRESSO_WHOLE_PULL_REFERENCE_CASE_MANIFEST_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_FIELD_INDEX_V0_1_4.json
ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json
reference_R0.foam
```

## What standard `./Allverify` performs

Standard `./Allverify` first verifies that the source inputs and the exact `./Allrun` executable are unchanged. It then executes ten qualification simulations:

```text
time-step family
  256 × 512, Δt = 0.020 s, 32 ranks
  256 × 512, Δt = 0.010 s, 32 ranks
  256 × 512, Δt = 0.005 s, 32 ranks

mesh family
  128 × 256, Δt = 0.010 s, 16 ranks
  512 × 1024, Δt = 0.010 s, 64 ranks

rank family
  256 × 512, Δt = 0.010 s, 1 rank
  256 × 512, Δt = 0.010 s, 16 ranks
  256 × 512, Δt = 0.010 s, 64 ranks
  plus the 32-rank time-step reference above

heterogeneous pressure fixture
  64 × 128, 1 rank
  64 × 128, 16 ranks
```

The aggregate report applies nine required gates covering individual-run acceptance, time-step sensitivity, mesh sensitivity, reference-rank equivalence, and layered-fixture serial/parallel equivalence.

After those gates pass, `./Allverify`:

1. repeats the no-physics-change verification;
2. finalizes the reference acceptance and run-status records with the qualification path, hash, and PASS state;
3. verifies all reference fields and all ten qualification acceptance reports;
4. generates one terminal freeze manifest **last**;
5. performs a read-only verification of that terminal manifest;
6. writes no package artifact after the terminal manifest.

The controlling qualification and freeze artifacts are:

```text
qualification/
  ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json
  ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv
  ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json

cases/reference_R0_20g_58mm_9bar/
  ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
```

The terminal manifest must report:

```text
status:                         PASS
implementation_status:          PASS
code_verification_status:       PASS
numerical_qualification_status: PASS
release_provenance_status:      PASS
reference_freeze_status:        FROZEN / QUALIFIED
physical_validation_status:     NOT_ESTABLISHED
next_scientific_milestone:      WP-0.1R
```

## Freeze/provenance architecture

The v0.1.4 provenance graph is intentionally acyclic:

```text
source package + scientific inputs
                ↓
exact OpenFOAM executable
                ↓
reference/fixture outputs + reconstructed fields
                ↓
standard qualification matrix
                ↓
qualified acceptance + finalized run status
                ↓
terminal freeze manifest generated last
```

The case manifest hashes only immutable scientific inputs. It does not hash acceptance or qualification outputs. The terminal freeze manifest binds the final source package, build, scenario, environment, scientific-input manifest, reference results, field index and contents, fixture result, qualification report and per-run acceptances, and finalization record.

## No-physics-change scope

Version 0.1.4 preserves the v0.1.3 WP-0.1 model:

- initially dry sharp-front wetting;
- exact piecewise-linear positive pressure-ramp integration;
- saturated Darcy flow;
- static porosity and permeability fields in R0;
- one effective soluble inventory;
- conservative advection–dispersion and extraction;
- explicit retained water, dissolved solute, remaining solid, and cup accumulation;
- fixed 93 °C liquid properties;
- the calibrated R0 permeability and all other physical parameters;
- the straight-sided wedge correction and B0 verification mathematics.

Release-only changes include:

- acyclic scientific-input and terminal freeze manifests;
- automatic post-qualification finalization;
- exact reference-executable reuse verification;
- explicit concentration-cap, remaining-inventory, retained-water, and cumulative-mass monotonicity gates;
- successful `relative error:` metrics classified as information rather than failures;
- 32 ranks as the routine R0 default;
- stronger source, artifact, field, qualification, and cross-link verification.

## Expected regression envelope

The target-qualified v0.1.3 reference result provides the regression expectation for unchanged physics:

```text
first drip                         4.711696185 s
final outlet flow                  1.482675972 mL/s
cup beverage mass at 30 s         40.957867 g
time to 40 g                       29.374480 s
cumulative TDS                    11.689306 %
extraction yield                  23.938453 %
```

The exact controlling v0.1.4 values are those recorded by the target-system acceptance and freeze manifests. R0 remains a calibration scenario: its permeability was selected to place the simplified reference calculation near an approximately 40 g endpoint.

## Claim ceiling

A fully successful v0.1.4 workflow supports this claim:

> The bounded WP-0.1 R0 OpenFOAM implementation is code-verified, numerically qualified under its declared analytical, reduced-twin, time-step, mesh, heterogeneous-pressure, and MPI-decomposition gates, and bound into an internally consistent immutable release record.

It does **not** establish independent validation for a real coffee, grinder, puck, basket, or machine. The current extraction parameters are engineering assumptions; gas, capillary hysteresis, heat transfer, swelling, poroelasticity, fines, clogging, damage, channeling, multispecies chemistry, and detailed machine coupling remain outside WP-0.1.

## Smoke profile

An orchestration-only smoke profile is available:

```bash
PROFILE=smoke ./Allverify
```

Smoke mode verifies and reuses the exact `./Allrun` executable but runs a reduced, profile-isolated matrix. It cannot qualify, finalize, overwrite, or freeze the standard reference.

## Cleaning

After copying the reports and any desired fields:

```bash
./Allclean
```

`./Allclean` removes generated cases, numerical time directories, processor directories, qualification runs, reports, logs, preflight/build records, and solver build products. Source, configurations, templates, tests, documentation, and bundled predecessor evidence remain.

## Further documentation

- `docs/FREEZE_FINALIZATION_SPECIFICATION_V0_1_4.md`
- `docs/PATCH_NOTES_V0_1_4.md`
- `docs/MODEL_SPECIFICATION.md`
- `docs/ASSUMPTIONS_AND_CLAIM_CEILING.md`
- `docs/RUNBOOK_AND_TROUBLESHOOTING.md`
- `docs/QA_STATUS.md`
- `docs/BASELINE_V0_1_3_QUALIFICATION.md`
- `docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md`
