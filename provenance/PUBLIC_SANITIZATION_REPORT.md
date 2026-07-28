# Public Sanitization Report

Status: **PASS**

This deterministic transformation changed only five approved files and only host/path metadata.
It made no scientific-content, governing-physics, or scientific-configuration change.

## Rules

- Package-local historical paths → `<PACKAGE_ROOT>/…`
- OpenFOAM project paths → `<OPENFOAM_PROJECT_DIR>/…`
- OpenFOAM user application paths → `<FOAM_USER_APPBIN>/…`
- Other home paths → `<USER_HOME>/…`
- Machine hostname → `<HOSTNAME>`

## Changed files

| Path | Archival SHA-256 | Public SHA-256 | Replacements |
|---|---|---|---:|
| `baseline_evidence/v0_1_2/ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_2.json` | `fa7292cb3ece058ed2d6f640f61480663fe7c82b748862a7d16aec54234791d8` | `449bbbd25eb9e3ec6ccd61aba1d7a9b38bea6007e65649bfb58f69f38f1de87f` | 26 |
| `baseline_evidence/v0_1_3/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_3.json` | `56b22c062595613e297b944843aaaef053c7e68328973502344a1087778e8987` | `e928fb6c6553c06c58fb1efb591c2903632074b6e1b7c17cca916b084abd0fc3` | 212 |
| `baseline_evidence/v0_1_3/ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_3.json` | `e820fd55c23d8a5325a9ced8993c5577f6dcb3482fd219dc7b75e2e1db41e37d` | `17be485a9cff074e364a76bec4742a95415072657c5031639859941dcdbc987b` | 42 |
| `docs/BASELINE_V0_1_2_RESULT.md` | `b1799b9f0e3895657bc0ad04eff932fffbed2dfcd14a6a435d5dc137823ce4f2` | `b5ef65308ff98a61401a386fcce5de14d2074fef5322711d2687caab32ba2af4` | 1 |
| `docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md` | `f26d75b57a9a9422e41cd8bb184d50acf03678007ed32fe4395d269b0e53dfc3` | `587cafc008a6c4317dc798dfe54228b89515dc3c7ee5ee9cc5280e80b289ba59` | 1 |

The JSON comparison proves unchanged keys, structure, list lengths, and numeric/boolean/null values.
Every changed JSON value was a string containing an approved private token.
Markdown changes are limited to the documented substitutions.

This automated provenance audit is not legal advice.

## Root-import whitespace exceptions

The sanitized derivative retains 17 historical Markdown trailing-whitespace findings:

- `README.md`: lines 3–5
- `docs/QA_STATUS.md`: lines 3–4
- `docs/source_strategy/espresso_puck_modeling_and_simulation_strategy_v1_2.md`: lines 3–14

This narrow exception applies only to the root import. It is not a global waiver; subsequent changes must pass the normal whitespace check.
