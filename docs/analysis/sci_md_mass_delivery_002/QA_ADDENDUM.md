# Bounded final-acceptance QA correction

Owner-authorized completion of SCI-MD-MASS-DELIVERY-002. G0 bookkeeping
correction within the existing G1 task; NO_GOVERNING_PHYSICS_CHANGE.
This addendum preserves SOFTWARE_QA.json and all original scientific receipts.

## Demonstrated defect

[Static validation run 36264548360, job 108466605248](https://github.com/trbrewer/espresso-whole-pull/actions/runs/36264548360/job/108466605248)
checked out EWP head `6b36257e6da29b69936bed0494f847e29333e4e4`
(tree `de026df23b279785c11e429166a2eea568935989`) directly, not a synthetic
merge. Python 3.12.3, NumPy 1.26.4, SciPy 1.11.4 and jsonschema 4.23.0
matched the pinned workflow. Its Python step ran 1,604 tests: one failure,
ten skips. The failure was
`test_existing_data_leverage_programme.ExistingDataLeverageProgrammeTest.test_existing_data_leverage_programme`:
`scripts/validate_existing_data_leverage_programme.py:46` asserted that every
ledger opportunity ID existed in the machine-readable programme.

The only unmatched ID was `SCI-MD-MASS-DELIVERY-002`. The task had appended
its ledger entry without the companion programme entry. This is a
task-induced current-state bookkeeping defect, not a numerical, model or
CSV-newline defect. The unchanged test reproduces the same assertion in a
fresh isolated environment with those exact four pinned versions.
The original authenticated job log is retained outside Git with SHA256
`b2faaa38c4a32a9b8b067f871c16e07c862adaa0fcf729c98fe2a99170e28884`.

## Correction and verification scope

Add the missing completed-negative entry to
`provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json`, consistent with the
existing ledger and frozen result. Do not change existing opportunities,
current priority, laboratory authority, ledger, validator or tests.
The other changed paths are this addendum, SOURCE_PACKAGE_MANIFEST.json and
the corresponding current manifest count/hash in PACKAGE_QA_STATUS.json.
All six existing programme tests pass after the correction in the same
isolated pinned environment. The existing regression assertion is retained
without weakening or replacing its expectation.

The programme is administrative metadata and is not an input to the frozen
producer or research consumer. No runtime, model, kernel, source mapping,
support, parameter, prediction, metric, threshold or result path changes.
All original task artifacts and production dependency files are checked
against their pre-correction SHA256 values in the external acceptance record.
No fitting, prediction-matrix generation or target scoring is repeated.

Frozen producer remains `cec97741e72b126f04f05b73691d9223bbdb148f`, tree
`1b30d6d6152baedc28fab42419a2c33d61b8694b`. The producer result record remains
`029b57c00a17d298f45728216f0168a6bcfc082f`, tree
`3b98650a1284eb4bf2c13ad4cc80313e670c9de5`. HANDOFF.json distinguishes these
identities and is unchanged. The pre-score reviewed consumer remains the
historical `db02beaf12976497d9f9714d36d38142f7a37ad1`; its scientific runtime
bytes are unchanged in the QA descendant.

| Immutable evidence | SHA256 |
|---|---|
| Approved freeze | e8333b85943bc3ab54db88adb8b631cd863911a9e626a9ba20c006b5c7dbc7c6 |
| Actual independent pre-score receipt | 2483b4547734d3bd847ec903ce7d2a93f9a6844b3f5d954bf058df5356339907 |
| Frozen predictions (private) | 1f8641ccc7e91d4fa3ea913f15073097b13736743100b0fb2a04723222ba0012 |
| Completed results | 189d014437391b0f7b3d33c9b5a98d16223edc5e0189c8772bd88c0a804966a9 |

## Authority and disposition

Live bases observed for this correction: Puckworks
`69f9ef3453294709ef575d63b156d9d78c49d2db`, tree
`24ebe16623b350f8e4f3fd04b7ecbf241c9a03a8`; EWP
`386cba18c421d4f0944450f412fd055ca2127a19`, tree
`b255367805d527bfd04c36426ae1435aae9656c8`. Final descendant identity, local
gates, hosted checks and independent exact-pair/base acceptance are recorded
externally after commit. This document does not approve its own containing
commit or relabel the old audit as approval of new bytes. Hosted success and
independent final acceptance remain separate requirements.

SCIENTIFIC_DISPOSITION = TESTED_CONDITIONING_FAMILY_INADEQUATE. MTF remains
primary; A/B/C/D remain FAIL. Source and numerical qualification are unchanged.
SOURCE_INTERNAL; TARGET_EXPOSED; RETROSPECTIVE_MODEL_DEVELOPMENT_COMPARISON.
PHYSICAL_VALIDATION = NOT_ESTABLISHED; NATIVE_EWP_RUNS = 0;
PRODUCTION_DEFAULTS_CHANGED = false; PRODUCTION_DEPENDENCY_LOCK_CHANGED = false;
NO_SUCCESSOR_AUTHORIZED. Both PRs remain OPEN/UNMERGED for a separate owner
merge decision. Pannusch-derived evidence retains CC-BY-NC-3.0 treatment.
