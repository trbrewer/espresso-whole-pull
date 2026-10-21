# Independent scientific review — SCI-MD-WASZ-TERMINAL-MASS-ROBUSTNESS-001

Disposition: **PASS_WITH_DECLARED_HISTORICAL_OPERATOR_LINEAGE_LIMITATION**.
No material scientific correction is required. This is an independent AI-agent
scientific review, not a human GitHub approval, merge approval, or physical
validation.

Reviewed scientific commit: `2b5feb4d756981b13d980f51835126dbbeccb1e6`.
EWP base: `f93095abd58b31476ec331f3aa8d68feb98df9b0`.
Read-only Puckworks: `58075bbbce548e63d94106c96b918c1464221514`.
Original source: `fbc33d3380a9c8cff2467bae70fec7137a6ed46f`, tag `v1.0.1`.
Review date: 2026-10-20. The reviewer did not author or modify the submitted
implementation, protocol, results, or tests. Administrative navigation and QA
closeout continued during review; the scientific files reviewed here remained
unchanged. Final PR-head CI/lifecycle verification is a separate maintainer step.

## Scope and independent method

Read the complete analysis implementation, fixed protocol, human result,
retained machine results/support/reconstruction/influence files, focused tests,
accepted SCI-MD-010 estimator and membership, SCI-MD-011 observation interface,
Puckworks provenance/loaders/alias tests, and original formatter/calibration.
Checked the task against the existing claim ceilings and the prior #207
endpoint-applicability argument. No prior calibration or model comparison was
repeated, and no fourth terminal mass window was introduced.

A separate reviewer program read the original JSON bytes directly and did not
import the task module. It used **50-digit Decimal arithmetic** for raw mass
interpolation, condition means and slopes. The slope was computed through the
algebraically equivalent pairwise identity
`sum_{i<j}((p_j-p_i)(q_j-q_i))/sum_{i<j}((p_j-p_i)^2)`, providing a distinct
arithmetic route from the submitted centered covariance implementation.
For source reconstruction it independently implemented the gradient as positive
weighted adjacent interval rates, interior SG as a sliding arithmetic mean, and
SG boundary values as explicit degree-one regression. It did not call NumPy
`gradient`, SciPy `savgol_filter`, or the upstream GPL script.

The reproducible reviewer evidence directory contains `independent_verify.py`
(SHA-256 `0b0805437b910cca219e80ed8a46f930724272dba70a203f44360f2859c0ce75`)
and `independent_numeric_receipt.json`
(SHA-256 `35cb257b77de29d57b9e0f48bdfe65eedccf4e4932fe80aa994b420b45c29c0e`).
These are review working evidence outside Git; the independently established
results and checks are retained in this receipt.

## Provenance, membership and support findings

- Authenticated **75 consumed source/authority files** against their actual
  pinned Git objects and manifest SHA-256 hashes. Verified upstream tag identity.
  Puckworks was read only. CC-BY-4.0 data attribution and distinct GPLv3 code
  convention are preserved; inspection does not imply code ingestion.
- Independently recovered **56 distinct physical brews / 11 conditions** from
  accepted fold membership. The 1,447-line `12-8-6` record exactly matches the
  first 1,447 lines of its 1,489-line alias. Its 42 additional tail records do not
  create another physical brew. No excluded-source record enters the cohort.
- Checked median-p2 pressure mapping, half-bar rounding, corrections affecting
  `1-2`, `2-3`, `2-5`, strict tolerance bounds, reversed index-500-through-0
  semantics, START_IDX, and aligned origin against every reconstruction record.
  Condition assignments use accepted identities, not filename pressures.
- Independently checked all **224 endpoint brackets**. Three are exact;
  nonexact support is at most 0.095 s wide. All complete raw timestamps are
  strictly increasing; maximum complete-record gap is 0.095 s. Every q10/q5/q20
  has support for every physical brew; no holding or extrapolation enters these
  observers. Raw mass decreases are retained.
- Verified the incomplete `7-1` final record: its p2 participates in the median,
  while absent t/m are neither fabricated nor used as measurements. It lies
  beyond all required support. Inspected the listed large scale drops: the
  earliest is `9-1` at 119.609–119.702 s, outside terminal windows and inferred
  accepted-operator support. No terminal reset or suspicious gap was identified.
  This establishes recorded support, not an instrument-error calibration.

## Numerical and statistical findings

Independent raw-byte slopes, rounded here to 12 decimals, are:

| Observer | LOW g/s/bar | HIGH g/s/bar |
|---|---:|---:|
| historical endpoint | 0.504206839400 | -0.065506412628 |
| q10 primary | 0.500459536271 | -0.070789817239 |
| q5 sensitivity | 0.501605586079 | -0.069375819216 |
| q20 sensitivity | 0.496239627735 | -0.069756131065 |

The maximum discrepancy from retained per-brew mass results is
`9.542896362388469e-15` g/s; maximum baseline slope discrepancy is
`3.661961127421691e-16` g/s/bar. The Decimal route independently verifies all
**448 deletion records** (56 physical brews × four observers × two subsets),
with maximum slope discrepancy `6.192222690226599e-16` g/s/bar. The original
condition pressures remain fixed. There are 27 relevant LOW and 15 relevant
HIGH deletions per observer; outside-subset deletions correctly contribute no
additional robustness evidence. No sign reverses. In particular q10's relevant
ranges are LOW `[0.496214041220, 0.505572699048]` and HIGH
`[-0.079892092088, -0.062068995243]` g/s/bar. q5/q20 and historical ranges also
match the retained vector.

Equal-brew averaging, unweighted condition slopes, sample SD convention,
condition membership, peak group, explicit complete/common support and deletion
sign bookkeeping are appropriate for the prespecified descriptive question.
The result does not convert these ranges to confidence intervals. Arithmetic
near-zero bounds are explicitly distinguished from physical uncertainty; the
conclusion does not depend on a retroactive physical-significance threshold.

## Historical endpoint and operator assessment

The independent finite-difference/regression route reproduces all **57 × 1000**
source trace rows for each of pressure, mass, mass flow and derived basket
pressure. Maximum field discrepancy is `5.00000000069889e-6`, consistent with
5-decimal retained serialization. All published duplicate-weighted condition
means and SEMs match, with maximum discrepancy `5.00000000069889e-7`, consistent
with 6-decimal serialization. The debugging CSV's four-decimal values are
correctly not reloaded. The 57-record published aggregation and 56-brew primary
aggregation are distinguished; duplicate weighting is confined to its known
condition and cannot explain the accepted flow-target discrepancies elsewhere.

**Important retained limitation, not an uncorrected defect:** the accepted
`endpoint_100s` equilibrium table differs from the source truncated trace's
last point. Independently averaging full-record filtered derivatives over
actual [99.9,100.1] s acquisitions matches all accepted flow/basket values and
sample counts: maximal differences are `4.569781772989501e-6` g/s and
`4.85450486475969e-6` bar. The missing original producer means this is a strong
numerical lineage inference, not uniquely established original-code provenance.
The result correctly refuses a qualified contrast that identifies the accepted
observer with the truncated source operator. It keeps the accepted values
immutable and presents terminal mass-window results independently.

The operator discussion is scientifically sound. Explicit regression at the
truncated edge produces negative interval-rate weights; all actual reconstructed
source grids have such weights. A separate reviewer synthetic calculation gives
endpoint A=1 and B=0.9445564516129032 after adding nonnegative discharge on
[70,71] s, confirming the counterexample without importing submitted functions.
All three declared mass averages preserve order in that illustration. The
accepted-table numerical rule instead samples interior SG positions, where
positive adjacent-rate weighting applies. Its kernels/support times differ
between brews. The report appropriately separates these facts, does not claim
negative edge weights caused the empirical downturn, and does not apply a
common-kernel theorem to separately sampled instrument records without further
assumptions. Cumulative mass ordering alone is correctly rejected as sufficient.

## Executed checks and disposition

- Focused unittest suite: **16/16 PASS**.
- Full analysis rerun using the documented Python environment: **PASS**.
- Byte comparison of all seven generated CSV/JSON artifacts against the retained
  bundle: **7/7 IDENTICAL**, including SOURCE_MANIFEST and RESULT.
- Independent raw-byte numerical and provenance program: **PASS**.
- Inspected documentary findings against numerical evidence: **consistent**.

No blocking or material findings were identified; no scientific correction
round is needed. The pending repository-wide source-manifest/QA and hosted CI
closeout is administrative and remains the implementer's responsibility at the
actual final PR head. This review does not assert those checks already passed.

The supported conclusion is that HIGH terminal beverage-mass slopes remain
negative, and LOW slopes positive, across all three fixed windows and all
relevant one-brew deletions on the full recorded cohort. Retain those as
conditional, source-internal descriptive features. Instrument response and
interpolation error, beverage outflow versus puck flux, aligned versus common
physical-origin time, material/initial-state variation, and original accepted
operator provenance remain limits. Neither independent validation, mechanism
identification, full Mo2021 applicability, nor a reversal of #207's theorem is
established. No automatic follow-on is warranted or authorized by this review.

PHYSICAL_VALIDATION=NOT_ESTABLISHED
