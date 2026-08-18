# Package file tree — v0.1.4

This tree is the historical v0.1.4 package view. Current navigation:

- [Project state](PROJECT_STATE.md)
- [Program state and forward plan](PROGRAM_STATE_AND_FORWARD_PLAN.md)
- [Claim ceiling](CLAIM_CEILING.md)
- [Puckworks integration](PUCKWORKS_INTEGRATION.md)
- [Controlling strategy](strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md)
- [Concise roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
- [XSV-TAICHI-001 closure-parity authority](verification/XSV_TAICHI_001_SATURATED_HYDRAULIC_CLOSURE_PARITY.md)
- [XSV-TAICHI-002 synthetic morphology screen](verification/XSV_TAICHI_002_SYNTHETIC_MORPHOLOGY_AND_REQUIRED_PERMEABILITY_COLLAPSE_SCREEN.md)
- [XSV-TAICHI-002 exact-head review correction](verification/XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.md)
  - Includes G9 reducer-v4 frozen-identity and deterministic-package closure;
    machine records live under `verification/cases/xsv_taichi_002/`.
- [Strategy v1.6 historical snapshot](strategy/history/whole_pull_modeling_and_simulation_strategy_v1_6.md)
- [Post-WP03 validation plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md)
- [VAL-CORPUS-001 protocol](validation/VAL_CORPUS_001_PROTOCOL.md)
- [VAL-CORPUS-001 comparison atlas](validation/VAL_CORPUS_001_EXISTING_EVIDENCE_COMPARISON_ATLAS.md)
- [WP03-002 diagnostic protocol](wp03/WP03_002_DIAGNOSTIC_PROTOCOL.md)
- [WP03-002 exact-head-review correction protocol](wp03/WP03_002_EXACT_HEAD_REVIEW_CORRECTION_PROTOCOL.md)
- [WP03-002 reproduction and diagnosis](wp03/WP03_002_REPRODUCTION_AND_DIAGNOSIS.md)
- [WP03-002 results](wp03/WP03_002_RESULTS.md)

Machine-readable WP03-002 exact-head evidence is in
`validation/wp03/WP03_002_GATE_EVIDENCE.json`,
`validation/wp03/WP03_002_PROTOCOL_COMPLIANCE.json`, and
`validation/wp03/WP03_002_VERIFICATION.json`.

XSV-TAICHI-002 machine records, the immutable historical execution runtime,
versioned review reducer, corrected result, review record, artifact manifest,
plot-source table, and ten SVG files are under
`verification/cases/xsv_taichi_002/`.

VAL-CORPUS-001 machine-readable records, reduced results, and figures are
under `validation/cases/val_corpus_001/`. The preserved original records sit
beside the prospective review-correction protocol/addendum, corrected v2
bundle and overlays, final-analysis addendum, self-contained V3 bundle and
overlays, compact comparison table, double-reduction reproducibility record,
status-separated execution ledger, v2 external-artifact manifest, and three
corrected figures. Complete successful, failed, and invalidated runtime
products remain outside Git.
- [VAL-001 source adapters and comparisons](validation/VAL_001_SOURCE_ADAPTERS_AND_COMPONENT_COMPARISONS.md)

VAL-001 framework code is under `tools/validation/val001/`, governed records
are under `validation/val001/`. The original analyzer is retained for audit;
`scripts/run_val001_corrected_comparison.py` is the corrected governed runner,
and ordinary tests use synthetic fixtures only.

```text
.
├── Allrun
├── Allverify
├── Allclean
├── Allwmake
├── README.md
├── VERSION
├── LICENSE
├── PACKAGE_QA_STATUS.json
├── SOURCE_PACKAGE_MANIFEST.json
├── config/
│   ├── reference_R0.json
│   └── fixture_layered_pressure.json
├── solver/espressoWholePullFoam/
│   ├── espressoWholePullFoam.C
│   └── Make/
│       ├── files
│       └── options
├── cases/
│   ├── reference_R0_20g_58mm_9bar/
│   │   ├── 0.orig/
│   │   ├── preflight/ [runtime; includes archived exact solver after Allrun]
│   │   └── system/
│   │       ├── fvSchemes
│   │       └── fvSolution
│   └── fixture_layered_pressure_v0_1_4/
│       ├── 0.orig/
│       └── system/
│           ├── fvSchemes
│           └── fvSolution
├── scripts/
│   ├── artifact_utils.py
│   ├── clean_case.sh
│   ├── espresso_reference_math.py
│   ├── finalize_reference_freeze.py
│   ├── freeze_contract.py
│   ├── generate_freeze_manifest.py
│   ├── generate_source_manifest.py
│   ├── lib/openfoam_env.sh
│   ├── normalize_timestamps.py
│   ├── postprocess.py
│   ├── postprocess_layered_fixture.py
│   ├── prepare_case.py
│   ├── run_qualification.py
│   ├── static_validate.py
│   ├── verify_build_provenance.py
│   ├── verify_freeze_manifest.py
│   ├── verify_no_physics_change.py
│   ├── verify_source_manifest.py
│   ├── write_build_provenance.py
│   └── write_run_status.py
├── tests/
│   └── test_reference_case.py
├── qualification/
│   └── [runtime products created by Allverify]
├── baseline_evidence/
│   ├── v0_1_2/
│   │   └── ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_2.json
│   └── v0_1_3/
│       ├── target run/acceptance/qualification evidence
│       └── source_contract/
│           ├── solver and reduced mathematics
│           ├── reference and fixture configurations
│           ├── Make contract
│           ├── initial fields
│           └── fvSchemes/fvSolution
└── docs/
    ├── ASSUMPTIONS_AND_CLAIM_CEILING.md
    ├── BASELINE_V0_1_2_RESULT.md
    ├── BASELINE_V0_1_3_QUALIFICATION.md
    ├── FILE_TREE.md
    ├── FREEZE_FINALIZATION_SPECIFICATION_V0_1_4.md
    ├── MODEL_SPECIFICATION.md
    ├── NUMERICAL_HARDENING_SPECIFICATION_V0_1_3.md
    ├── OPENFOAM12_COMPATIBILITY.md
    ├── PATCH_NOTES_V0_1_1.md
    ├── PATCH_NOTES_V0_1_2.md
    ├── PATCH_NOTES_V0_1_3.md
    ├── PATCH_NOTES_V0_1_4.md
    ├── QA_STATUS.md
    ├── RUNBOOK_AND_TROUBLESHOOTING.md
    └── source_strategy/
        └── espresso_puck_modeling_and_simulation_strategy_v1_2.md
```

Generated case dictionaries, meshes, time directories, processor directories, logs, reports, traces, preflight records, qualification runs, and build products are excluded from the source-package manifest and removed by `./Allclean`.

VAL-CORPUS-002 Stage B0 adds
`scripts/val_corpus_002_b0_tooling.py`,
`tests/test_val_corpus_002_b0_tooling.py`, its append-only tooling protocol and
report under `docs/validation/`, and direct-reference, deterministic
configuration-inventory, and access-barrier records under
`validation/cases/val_corpus_002/`. Complete solver products remain external.
Stage B2 final reporting adds `scripts/val_corpus_002_b2_reporting.py`, the
closed final-result schema and portable result/audit/summary records under the
same case directory, five deterministic, quantitatively labeled SVG figures
with explicit non-overlapping layout bands under its `figures/`
subdirectory, and the substantive result report under `docs/validation/`.


VAL-001 post-result controls include `tools/validation/val001/invocation.py`,
`source_identity.py`, the governed schema registry, the invocation event
journal, the post-result execution lock, the hardening freeze, and standalone
historical re-expressions under `validation/val001/results/historical/`.
The completion layer adds
`validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json`, the deterministic
`VAL_001_INVOCATION_SUMMARY_V2.json`, and non-writing inventory and journal
verification scripts under `scripts/`.
The final schema taxonomy is recorded in
`validation/val001/VAL_001_DEEP_SCHEMA_COVERAGE_MATRIX.json`; generated closed
families live in `validation/val001/schemas/deep_record_families.schema.json`
and are checked by `scripts/verify_val001_deep_schema_coverage.py`.
VAL-001 administrative closure adds
explicit schema specifications, an executable semantic-profile registry, a
machine-readable mutation inventory, and an external candidate-root protocol.
`VAL_001_ADMINISTRATIVE_CLOSURE_SPECIFICATION.json`, the explicit semantic
profile registry, administrative freeze and canonical-lock schemas,
`tools/validation/val001/administrative.py`, and non-writing administrative
and external-artifact verifiers. Full OpenFOAM products remain outside Git.
The successor provenance layer adds the normative contract registry,
schema-provenance transition matrix, immutable profile-assignment registry,
schema-taxonomy specification, mutation execution coverage, successor freeze,
and historical V4 consumed lock under `validation/val001/`.

VAL-CASE-001 case-specific artifacts are under
`validation/cases/val_case_001/`, with the frozen protocol, bounded correction
addendum, scientific report, and review disposition under
`docs/validation/cases/`. Complete generated OpenFOAM cases, meshes, fields,
processor directories, executables, traces, and logs remain outside Git.
The persistent imported-evidence authority is
`docs/validation/VAL_PUCKWORKS_001_BASE_TEMPORAL_CROSS_VALIDATION_AND_CUP_MASS_LINEAGE.md`;
its exact upstream JSON records live under
`validation/external/puckworks_base_temporal_cv/` and selected upstream plots
under `docs/evidence/puckworks_base_temporal_cv/figures/`.
# OBS-001 additions

- `scripts/sci_lc_001a_obs_001_diagnostics.py`
- `scripts/sci_lc_001a_obs_001_no_physics.py`
- `scripts/sci_lc_001a_obs_001_no_feedback.py`
- `tests/test_sci_lc_001a_obs_001.py`
- `validation/cases/sci_lc_001a_obs_001/SCHEMA_CONTRACTS.json`
- `docs/analysis/sci_lc_001a/obs_001/`
