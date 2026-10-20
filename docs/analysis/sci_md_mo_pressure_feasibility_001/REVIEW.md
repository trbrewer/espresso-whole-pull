# SCI-MD-MO-PRESSURE-FEASIBILITY-001 independent review

**Scientific review: PASS for the explicitly declared reduction and claim
boundaries. No material finding requires correction or a scientific recheck.**
This was one substantive review by a separate agent who did not author the
candidate. It is not a repository-CI receipt, physical validation, or approval
of a governing-law implementation.

## Candidate and evidence independently inspected

Reviewed EWP candidate commit
`f84f45610403dbf3514be9961d62415b1ee48ce1`, tree
`b193fa37c49cd29f7cfa321862374feb98306054`, against base
`7c025527da7e07982428d4c78a3e79bfa29a76ac`, tree
`5864a867a8b8b41d39f35f09a637092929f33831`.
Research reference: read-only Puckworks
`58075bbbce548e63d94106c96b918c1464221514`, tree
`a722e85bf919d038931f97af8c8437c06e922638`.
The production dependency lock is byte-identical to the EWP base and still
names `fc61c4670ec7bf801e40bb391aab16048b8da26b`.

Inspected the candidate `PLAN.md`, `RESULT.md`, `RESULT.json`, `check.py`,
`CHECKS.json`, changed-path inventory, and relevant repository instructions
and data-first/claim policies. Independently rehashed every EWP and Puckworks
evidence file listed in `RESULT.json`; all match. Independently checked the
base and research trees.

Inspected the accepted Mo manuscript's II B equations (5)–(12), II D,
II E/Table I/equations (16)–(17), incomplete-wetting rationale and geometry
interpretation. Viewed rendered manuscript pages 4, 5 and 8 to check the
signs and axes in Figures 1–3 and 7 rather than relying on extracted text or
the repository card. The inspected PDF hashes to
`55ee1e3746312f85dcc8888e337775cdea0a99e93fec4a35376cb7663b67b99c`,
matching the declared accepted-manuscript authority. The manuscript and
renderings remain outside Git.

Also inspected the Mo card, streamtube opening/clogging equations, R-04/T08,
data guide, Waszkiewicz processing provenance and the historical
SCI-MD-010/011 interface/diagnostics, SCI-MD-012, SCI-MD-002C, SCI-LC-001A,
dynamic-hydraulics and Mo chemistry-transfer results used for attribution.
Historical campaigns were not rerun.

## Findings and disposition

| Review question | Independent assessment | Materiality / disposition |
|---|---|---|
| Source signs, units and pressure reference | Figure 1's outward normal and Figures 2–3's negative inward force agree with suppression by compression. Figure 7 instead increases the threshold with its positive normal-load coordinate. Naming `sigma_c=-F_n/a_s` on the compressive branch is an explicit reconciliation, not an unnoticed sign substitution. The 2D stress dimensions, mass/time erosion rate, spacing factor in equation (12), density/volume opening conversion and bar-to-Pa/kg-to-g conductance factors are consistent. SDPD background pressure is not promoted to measured preload or a Darcy traction closure. | PASS; no material transcription or dimensional defect. |
| Fixed-state reduction | With pressure-independent coefficients, `C_E[s_E P-D]_+` is zero for `s_E<=0`, and nondecreasing for `s_E>0`, throughout `C_E,D,P>=0`. Finite positive cohesion/offset does not invalidate the statement. Affine traction and its reference are correctly classified as additional assumptions. | PASS for the local-rate lemma only. |
| Scalar evolution | Bounded Lipschitz coefficients and the positive part give local uniqueness; nonnegative evolution with `N(1)=0` preserves `[0,1]`, giving all finite-time existence for bounded admitted histories. The positive-part difference/Gronwall proof uses a state Lipschitz bound, not `F_x>=0`. Nondecreasing conductance then orders instantaneous endpoint discharge. Common parameters, initial state and physical time are explicit. | PASS; negative discharge branch excluded only within this scalar scope. |
| Adapter throughout evolution | Independently differentiating `L=P+h(KP)` gives the stated three sensitivities and denominator `1+h'(q)K>=1`. The nonnegative branch is unique exactly for `L>=h_0`. Composition `H(x,L,t)=F(x,P(x,L),t)` is Lipschitz in state and nondecreasing in line pressure on bounded admitted domains. This comparison remains valid even when the two evolving bed drops are not ordered. The separate static formula is not substituted for history-dependent evolution. | PASS; startup below the intercept and transient hydraulic validity remain explicitly outside the unconditional physical claim. |
| Actual histories, clock and initial state | The recorded high-pressure histories support ordering on their aligned grid and declared linear continuation. They do not establish pre-alignment forcing or common physical state/time since wetting. A coupled common initial/material draw is correctly required for the ensemble statement. Source flux-dependent normalization is not identified with seconds or held constant across changing physical references. No hard five-second cutoff is asserted. | PASS; these gaps justify unresolved actual-brew applicability. |
| Beverage and processed observation | The common positive hydraulic mass conversion preserves order conditionally. Separate outlet solids/retention/delay need their own mapping. Ordered cumulative mass alone does not prove ordered differentiated/smoothed endpoints. The negative-weight edge-fit example is explicitly conditional and is not claimed to reconstruct the accepted operator or explain the observed decline. | PASS; `endpoint_applicability=UNRESOLVED` is warranted. |
| Full source and historical limits | Figure 7's nonaffine threshold and capped sequential bond model need not obey the examined effective law. No spatial comparison or turnover witness is asserted. SCI-MD-002C is restricted to its fixed-active-bed 96 stems; SCI-LC-001A remains ineligible, not a physical rejection; dynamic-hydraulics results remain bounded to tested forms. SCI-MD-012 rescaling and the distinct Mo chemistry task are attributed correctly. | PASS; no general rejection of erosion or Mo2021 physics. |

The principal attempted counterarguments do not overturn the scoped theorem:
pressure suppression alone cannot create an active declining affine bracket
when its offset is nonnegative; negative state feedback does not break scalar
comparison; and a larger machine loss on the more-open trajectory does not
break comparison at fixed state. Conversely, the source's nonaffine envelope,
multiple evolving geometry variables and incomplete observation mapping are
real boundaries of the proof, not details that may be assumed away.

## Bounded verification and accepted scope

Re-executed `check.py` against the pinned research reference into an external
temporary receipt. It exited successfully and reproduced committed
`CHECKS.json` byte-for-byte. Reviewed the calculation itself: it reads only
line pressure for the new history audit, selects conditions using retained
measured means, deduplicates canonical physical brews, and performs no fit,
flow score or numerical trajectory. The adapter residual/sensitivity checks
and exact edge-fit weights support their stated algebraic roles. They are
not used as an impossibility proof. The retained diagnostic slopes and exact
adapter coefficients agree with their committed authorities.

Accepted dispositions are:

- Fixed geometry: **INFEASIBLE for decreasing local erosion rate** under the
  affine, nonnegative-offset effective-law assumptions; no endpoint theorem
  from that lemma alone.
- Declared scalar opening/conductance reduction: **INFEASIBLE for decreasing
  instantaneous endpoint discharge** for common initial/material state and
  every finite common physical time with pointwise ordered admitted bed- or
  line-pressure histories. Constant pressures are included. Actual processed
  `endpoint_100s` applicability is **UNRESOLVED**.
- Full spatial/stochastic source behavior: **UNRESOLVED**, structurally and
  for the target. No universal mechanism rejection follows.

Retiring exactly the declared scalar reduction for producing the missing
negative hydraulic branch is justified without a coffee-specific clock or
another parameter campaign. It is not a target-level falsification or a
reason to implement a different erosion law automatically.
`PHYSICAL_VALIDATION=NOT_ESTABLISHED`.

Repository checks, final PR identity and hosted CI are separate delivery
evidence to be appended by the implementing agent; this scientific review
does not assert their outcome.

## Implementer delivery and QA record

The independent review found no material defect; no scientific correction or
recheck was needed. The subsequent commit adds this review and package-manifest
bookkeeping only. `PLAN.md`, `RESULT.md`, `RESULT.json`, `check.py` and
`CHECKS.json` retain their reviewed bytes.

Local completed checks before draft publication:

- Source-manifest verification: PASS (1,423 files after adding this review).
- `scripts/static_validate.py --root .`: PASS, all 39 gates.
- Historical v0.1.4 baseline, active governing-change boundary, rheology
  005/006 validators, historical XSV-PRESSURE change contract, release boundary
  and integrity, WP-0.3A/B/C boundaries, and existing-data programme: PASS.
- Externally pinned VAL-001 administrative closure: PASS at the reviewed
  candidate head/tree, 105 records and no cycles/orphans; final-head binding
  is checked again at delivery.
- Shell syntax: 20 files PASS. JSON parsing: 1,201 files PASS.
- Tracked generated-product, private-path and secret-form scans: PASS.
- Retained EWP evidence hashes: PASS; production solver and dependency-lock
  diff against the base: empty. Puckworks research worktree: clean/read-only.

The full Python suite was launched with the current CI's pinned Python
3.12.3 / NumPy 1.26.4 / SciPy 1.11.4 / jsonschema 4.23.0 in an isolated task
QA environment (`pip check`: PASS), and with its separate historical
Puckworks test authority `a3428a4d4ad571ef3168a70e8a04620fca5d3520`
containing the required `2058d0e947ee9eb92c52d64f6165b810f1fb4732` object.
This is CI support, not either the Mo research reference or the production
lock. Its terminal count/outcome and hosted receipts are recorded in the
final draft-PR description; this document does not predeclare their success.
Full logs and temporary QA products remain outside Git.

The live EWP main ruleset requires **source-and-boundary** and
**inexpensive-checks**. Both current EWP workflows are run for the actual final
patch; no Puckworks check names or historical receipts substitute for them.
Final head/tree, actual base, exact check URLs and lifecycle state are
recorded in the associated draft PR linked from issue #206. This avoids a
self-referential commit/CI receipt in the source manifest. Required final
state is draft/open/unmerged with auto-merge disabled.
