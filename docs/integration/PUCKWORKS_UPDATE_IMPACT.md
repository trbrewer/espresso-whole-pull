# Puckworks Update Impact — WP01R-001

## Purpose

This report records the bounded, static review of the Puckworks dependency
update used by Espresso Whole-Pull. Change declaration:
`NO_GOVERNING_PHYSICS_CHANGE`.

The review detects upstream scientific, semantic, validation-contract, data,
interface, and rights effects. It does not change the solver repository's
governing physics or scientific configuration.

## Reviewed identities

| Role | Commit | Tree |
| --- | --- | --- |
| Historical and previous lock | `352dacd51015d95a3b5a5b3e1a8fb331419d78b0` | `66d898118c40300393eb8abc543f7c02f6bd8129` |
| Selected reviewed snapshot | `fc61c4670ec7bf801e40bb391aab16048b8da26b` | `1d553e44ee2f7480a5df521560801b478618cc84` |

The reviewed ref was `refs/heads/main`. Initial resolution occurred at
`2026-07-28T16:05:27Z`; the recorded review cutoff was
`2026-07-28T16:12:00Z`. The old commit is the selected commit's direct parent,
so the complete review covered one intervening commit without divergence.

The lock means `REVIEWED_MAIN_AT_RECORDED_UTC_CUTOFF`; it does not claim that
the selected commit will always be the latest upstream tip.

## Change and inventory summary

The dependency delta contains 80 classified paths: 19 added and 61 modified,
with no deletions, renames, copies, or mode changes. It contains no Git LFS
pointers, gitlinks, symlinks, executable-mode changes, or changed objects over
1 MiB. Six changed PNG blobs were treated as opaque committed review inputs
and were not regenerated.

The R1-controlling inventory contains 32 semantic artifacts, split evenly
between 16 changed and 16 unchanged records, plus six separate quantity
records. Unchanged items remain controlling where they define a source role,
unit, basis, pressure node, computational role, uncertainty, rights status, or
claim limit. The exhaustive path classification and inventory are in the
[JSON companion](../../validation/integration/PUCKWORKS_UPDATE_IMPACT.json).

## Material upstream findings

- The 57 deposited Waszkiewicz trace records correspond to 56 distinct brews.
  `12-8-6.txt` is an exact prefix of `12-8-6_alt.txt`; the complete files are
  not described as byte-identical.
- At 13 bar there are seven deposited records representing six distinct
  brews.
- Source-aggregate reproduction retains the alias, while analyses using the
  shot as the experimental unit exclude it.
- Adjacent pressure-axis winner transitions were corrected from two to three.
- Pressure-level mean-curve RMSE is not random-shot prediction error.
- Basket/puck-inlet gauge pressure is distinct from line/pump-side pressure.
- Source-curve reproduction, within-campaign holdout, and independent
  validation are distinct evidence classes.
- Perticarini bed-height/time, EY/TDS, and granulometry records were added.
- The Puckworks data manifest increased from 107 to 110 entries.
- Foster wording was corrected to include machine and wetting effects while
  excluding extraction-driven structural change.

These findings are dependency evidence. They do not select calibration inputs,
freeze protected comparisons, resolve the downstream TDS basis, implement R1,
or alter the current solver configuration.

## Rights and redistribution

Puckworks repository code is MIT-licensed, but that is not blanket clearance
for every paper, dataset, figure, or third-party artifact:

- Waszkiewicz deposited data is CC-BY-4.0 and requires attribution.
- The Waszkiewicz article is citation-only.
- Perticarini thesis tables have no explicit source license and remain
  citation-and-metadata-only unless separately cleared.
- Ellero, Matias, and other paper text and figures remain citation-only unless
  separately cleared.
- Some upstream outward-use rights remain `NOT_REVIEWED`.

No rights-restricted Puckworks material is vendored in this repository.
Per-artifact rights review remains required.

## Residuals and downstream work

WP01R-001 records but does not resolve:

- missing shot-matched TDS;
- incomplete identity of source-side excluded brews;
- exact downstream TDS basis;
- calibration-input authorization;
- protected-comparison selection;
- final per-artifact redistribution clearance.

Issue #4 owns the Waszkiewicz source/quantity/evidence dossier, source units
and bases, source pressure and time nodes, provenance, rights, digitization or
processing history, and the missing-data register. Issue #5 owns the frozen R1
roles and contract: prescribed inputs, calibration inputs,
protected-comparison selection, exclusions, downstream units, bases, nodes and
time origins, uncertainty treatment, tolerances, parameter bounds, and
validation/acceptance gates. Issue #6 owns the provenance-preserving Puckworks
bridge and deterministic R1 case generator. Issue #7 owns execution against
the frozen contract, conservation and comparison outputs, the
protected-comparison scorecard, and residual classification.

## Disposition and drift

Analysis status: `COMPLETE`.

Adoption recommendation: `ADOPT_WITH_FOLLOWUP`.

At implementation start (`2026-07-28T16:26:49Z`), live Puckworks `main` still
resolved to `fc61c4670ec7bf801e40bb391aab16048b8da26b`;
`drift_detected=false`. The pre-pull-request observation at
`2026-07-28T16:31:59Z` resolved to the same commit, so
`drift_detected=false` remained unchanged.

## Verification

The final verification record is maintained in the JSON companion. Source
verification passed 106/106 at aggregate
`5e10b5d2ed6148111a0d53a8d5db9082eb81d6bf24bc47b65eb29c9db757e750`;
scientific inputs passed 19/19 at their unchanged aggregate; static validation
passed 32/32; Python tests passed 43/43; and the no-physics contract passed
28/28. Shell syntax, structured parsing, Markdown links, private/secret
boundaries, generated-product scanning, large-file scanning, the checkout
tool, and the exact changed-path allowlist also passed. `gitleaks` was not
available, so an explicit regex scan was used and that limitation is retained.
No OpenFOAM or Puckworks code was executed.

## Claim ceiling

R0 remains `NUMERICALLY_QUALIFIED_CALIBRATION_BASELINE`; physical validation
remains `NOT_ESTABLISHED`. WP01R-001 authorizes neither R1 implementation nor
calibration/protected-comparison selection.
