# Package file tree — v0.1.4

This tree is the historical v0.1.4 package view. Current navigation:

- [Project state](PROJECT_STATE.md)
- [Claim ceiling](CLAIM_CEILING.md)
- [Puckworks integration](PUCKWORKS_INTEGRATION.md)
- [Controlling strategy](strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md)
- [Concise roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
- [Post-WP03 validation plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md)
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

VAL-001 post-result controls include `tools/validation/val001/invocation.py`,
`source_identity.py`, the governed schema registry, the invocation event
journal, the post-result execution lock, the hardening freeze, and standalone
historical re-expressions under `validation/val001/results/historical/`.
The completion layer adds
`validation/val001/VAL_001_GOVERNED_RECORD_INVENTORY.json`, the deterministic
`VAL_001_INVOCATION_SUMMARY_V2.json`, and non-writing inventory and journal
verification scripts under `scripts/`.
