# SCI-MD-MO-SPATIAL-PRESSURE-FEASIBILITY-001 independent review

**Scientific disposition: PASS for `UNRESOLVED_BOUNDED_ANALYSIS` and its
explicit boundaries. No unresolved material scientific finding remains.**
This is one substantive review by a separate agent who did not author the
candidate. It does not establish reversal capability, a general exclusion,
physical validation, repository QA success or approval for production adoption.

## Reviewed candidate and correction

Initial candidate: `a643cb234ace8a7066e08820bd1db19cf2ad1904`.
The same review includes the bounded correction at final scientific candidate
`5c31093f6c76debc0199ca8df33b0d4015c25976`, tree
`8547ac7145e44f54ad684902cafd6cfb60a49a9e`, against EWP base
`ba28b230d2c3a5da8b7d611b48af59b0ba90df35`.
Read-only Puckworks research authority is
`58075bbbce548e63d94106c96b918c1464221514`.

The implementer identified one arithmetic typo while this review was active:
for the equal-aperture active-domain illustration, the AT endpoint brackets
are -1.85 and .15, giving J=.005625. The original prose's -.85 and .01125
were incorrect. I independently derived the corrected values and verified
the new exact-value test. The implementation and retained search/refinement
outputs did not change. This was a corrected illustrative calculation, not
a changed mechanism, parameter search or terminal conclusion. No second
scientific review or search was required.

Inspected PLAN, RESULT prose/JSON, SEARCH, CANDIDATES, REFINEMENT, both research
programs, focused tests, candidate history, state/ledger/programme updates,
relevant repository governance and source/claim authorities. Reused #207's
reviewed source/sign/unit crosswalk, and inspected the accepted manuscript's
II B effective-law/mass-rate and incomplete-wetting passages and II E
approximation and normalization passages. The manuscript SHA-256 is
`55ee1e3746312f85dcc8888e337775cdea0a99e93fec4a35376cb7663b67b99c`.
Also inspected the Mo card, R-04/T08 recommendation and relevant predecessor
result/observer boundaries. No restricted source was copied into Git.

## Scientific findings

| Question | Independent assessment |
|---|---|
| Source versus reduction | PASS. The study uses the effective Eq. (11) law, not the full stochastic particle/bond system. The source's approximate failure envelope, per-particle mass rate and 2D units are distinguished from the new 3D per-effective-site coefficient. Supported coatings, uniform-aperture projection, finite remaining-site weight and the graph are expressly additional assumptions. The weak-friction domain is hypothetical, not source-measured coffee. |
| Compression, reference and support | PASS conditionally. Outward solid normal and inward fluid traction give compression-positive differential load p(s)-p_out. All interiors use the same p_out, supports remain rigid, and preload is zero. The hydraulic maximum principle makes this load nonnegative. This is a mechanically specified hypothetical closure; neither line pressure nor imposed bed drop is silently identified with grain compression. Its coffee applicability remains unestablished. |
| Slit hydraulics and passive opening | PASS. The full-gap Poiseuille conductance and wall shear have the stated factors and units. Positive conductances give unique internal pressures, signed cross-flow, conservation and positive dissipation. The Dirichlet minimum-energy argument correctly gives Rayleigh monotonicity. Consequently each individual constant-pressure discharge is nondecreasing; this result alone does not compare two evolving pressure runs. |
| Fixed-complete-state pressure monotonicity | PASS. At any fixed state and axial location the rate bracket is [pi s-gamma]+ with gamma>=0. For s<=0 it is inactive; for s>0 it is pressure-nondecreasing. Axial integration and pressure-independent nonnegative site/mass weights preserve the componentwise order. The implementation matches this statement. The local positive part is integrated before averaging; it is not the positive part of averaged compression. |
| Common state, material, mass and clock | PASS. Each pair shares x0, inventories, all material coefficients, references and support. The two-wall rate and full-gap mass formula have consistent factors. The pressure-independent stress/time scales preserve equal physical elapsed time. The z transform preserves the exact invariant domain without clipping, with finite-time exhaustion excluded analytically. Discarded solids have no additional hydraulic or beverage effect. |
| Hydraulic approximation | PASS for the declared controlled limit. With positive minimum conductance and bounded aperture rates, the omitted pore-storage/throughflow ratio tends uniformly to zero as the common kinetic coefficient tends to zero at fixed dimensionless time. Low inertia is a separate scale assumption. This does not supply a calibrated finite coffee timescale or storage error bound. |
| Analytical exclusions and gap | PASS. Frozen geometry, unique scalar states, D=0 including preload, and a common orbit with nonnegative pressure-monotone scalar speed give valid exclusions. The general finite-threshold family is neither globally collinear nor cooperative in the aperture order. The report correctly treats failure of those sufficient conditions as a gap, not a reversal or proof that all other comparisons fail. |
| Numerical assurance | PASS for a bounded null screen. Guard-rejected pairs remain ineligible; negative dense-output states are not used as physical effects. Accepted-state conservation, inventory identities, monotonicity and pressure bounds are checked. The closest-pair refinement has a different integrator, graph-Laplacian hydraulic calculation and root-split integral. Agreement is an inter-method estimate, not a rigorous error enclosure or a continuous-time ordering proof. |
| Scope and consequence | PASS. No full-family infeasibility, positive capability, line-pressure witness, observed branch reproduction or physical validation is claimed. #207/#209/#211 retain their accepted strength. The missing coffee loading/material/time/geometry/observation joins remain explicit. Retirement is limited to proved subfamilies; the asymmetric finite-cohesion bridge is neither promoted nor retired as infeasible. No automatic successor follows. |

I independently evaluated the obstruction using exact rational arithmetic:
for x=(1,1,1,1/2,1), p_A/pi=25/43 and p_B/pi=32/43.
The SA/AT pressure-vector determinant is exactly -7/430, and
partial p_A/partial g_BT=-256/1849 at pi=1. Multiplying rows by positive
inventory weights preserves noncollinearity. The negative derivative applies
at an interior active state, so inactive thresholds and zero-rate inventory
faces do not restore cooperativity on the whole domain. This remains an
admissible-state obstruction, not a reachability or reversal witness.

## Bounded execution and independently checked evidence

The committed plan predates exploration; the pre-exploration implementation
already contained the conservative 200,000-call charge for a failed pair.
I inspected the later instrumentation delta: it adds actual-start/call and
failure diagnostics without changing numerical equations, parameters,
selection or stop behavior. The retained original external CSV and corrected
CSV have identical original scientific fields for all 81 rows. The original
162 scheduled trajectories are correctly distinguished from 151 actual starts.

Independently regenerated only the Sobol parameter sequence, not trajectories:
all 81 retained candidates are exactly the declared prefix. Recomputed totals
from the retained CSV: 57 complete pairs, 24 failed pairs, 230,283 calls in
complete pairs, 306,221 actual calls overall, and 5,030,283 conservatively
charged calls. The 19 lower-z, 23 lower-aperture and one aperture-decrement
rejections are overlapping counts and reproduce from the retained diagnostics.
The 47 unvisited candidates and sampled-time restriction are reported correctly.
The budget overshoot is one failed-pair charge, not undisclosed extra search;
actual computation is below the specified RHS budget. The conservative charge
made the screen stop early, so the result must remain bounded and unresolved.

Independently rehashed 22 declared source/input/artifact identities, including
the accepted manuscript, EWP base authorities, research-reference files and
four retained plan/search/refinement artifacts: all matched. The embedded
SEARCH and REFINEMENT objects in RESULT.json exactly match their files.
The production solver and dependency-lock diff against the base is empty;
the Puckworks research worktree is clean.

Ran the seven focused tests on the initial candidate, then rechecked the
corrected candidate including its new active-domain assertion: PASS. These
cover the relevant mathematical/conservation/domain controls and are not
empirical validation. Independently replayed only the frozen closest-pair
refinement to an external directory: four trajectories, 22,672 RHS calls,
with REFINEMENT.json reproduced byte-for-byte. No new parameter search or
failed-candidate rescue was launched by this reviewer.

For candidate 48, the refined minimum Q_H-Q_L is
0.00303106590846626 Q_ref at theta=0, with pressure/discharge ratio
1.0528511677868664. The initial common geometry explains this minimum;
it is not an incipient crossing. The independent-path differences reproduce:
maximum absolute Q difference 2.7547408798511697e-15,
gap difference 7.216449660063518e-16 and aperture difference
2.0317081350640365e-14 over 4097 common sample times in [0,32].
These estimates do not certify any continuous-time ordering. There is no
reversal interval and no qualified witness to certify.

The report's aggregate accepted-state hydraulic residual and algebraic solid
inventory residual are consistent with the retained data and implemented
checks. I did not rerun all 57 completed exploratory pairs; that is not needed
to approve the explicitly bounded unresolved claim. The independently
replayed closest pair has hydraulic residual at most
6.938893903907228e-17 and inventory residual at most
2.220446049250313e-16 in the declared units.

## Accepted terminal boundary

`UNRESOLVED_BOUNDED_ANALYSIS` is scientifically supportable. The exact unresolved
question is whether the general asymmetric finite-threshold supported-slit
bridge has a discharge-ordering invariant or admits a valid common-time
reversal. This study proves exclusions only for its stated subfamilies and
finds no sampled witness in 57 completed pairs; 24 rejected pairs, 47 unvisited
candidates, unsampled times and the wider continuous parameter region remain
unresolved. The result is prescribed-bed-pressure research only, with
line-pressure applicability `NOT_ASSESSED` and
`PHYSICAL_VALIDATION=NOT_ESTABLISHED`.

Repository checks, source-manifest completion, hosted CI, final PR/head
identity and draft/open/unmerged/auto-merge-disabled lifecycle are separate
implementer delivery evidence. This review does not predeclare their success.

## Implementer QA and delivery record

The corrected scientific candidate above remains unchanged after review.
Subsequent edits add this review, package/source-manifest bookkeeping and the
new numerical test to the static validator's existing research-test dependency
allowlist. The latter uses the already pinned NumPy/SciPy environment and
changes no production rule or scientific calculation.

Scientific review and numerical assurance are separate from repository QA.
The initial full local suite ran 1,677 tests with 21 skips; three failures
were stale source/package manifest bookkeeping and one error was the static
validator's missing research-test allowlist entry. These are corrected in
this lane. All 18 affected/related tests then passed, including the seven
scientific tests, manifest portability, package QA and nonmutating validator
checks. No scientific campaign was rerun to repair those QA issues.

Static validation passed all 39 gates. Historical baseline, active governing
boundary, rheology 005/006 validators, historical pressure contract, release
boundary/integrity, WP-0.3A/B/C boundaries and existing-data programme checks
passed. Shell syntax (20 files), JSON syntax, input/artifact hashes,
generated-product and private-path/secret scans passed. Final manifest,
externally bound administrative closure and hosted full-suite receipts are
recorded on the draft PR after its final head is fixed. This avoids a
self-referential receipt. Production solver/defaults, dependency lock,
Puckworks and predecessor bundles remain unchanged.

Required terminal delivery is one draft PR, open and unmerged, with auto-merge
disabled. Final actual base, tested head/tree, hosted check URLs and outcomes
belong in that PR body. No successor is executed.
