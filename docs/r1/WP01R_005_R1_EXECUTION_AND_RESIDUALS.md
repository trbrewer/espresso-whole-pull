# WP01R-005 R1 execution and residuals

WP01R-005 executed the frozen Waszkiewicz R1 scenario without changing the
solver, governing equations, scientific contract, scenario, calibration,
selectors, windows, or thresholds. Physical validation remains
`NOT_ESTABLISHED`.

## Protocol status

PR #16 is preserved as superseded historical pre-protocol evidence. Protected
data and its preliminary result were known before the final corrective analyzer
was frozen, so this is not a blinded first reveal. The merged WP01R-003
contract nevertheless fixed the selectors, formulas, thresholds, time mapping,
scenario, and no-retuning rule before that historical access.

Corrective attempt 1 passed R0 `Allrun` but stopped at a legacy terminal-freeze
Git-mode verifier defect. Attempt 2 passed the complete R0 `Allrun`, standard
`Allverify`, terminal freeze generation, and read-only freeze verification,
then completed one unchanged central R1 run.

The final mapped source point was 103.0 s, while the completed solver trace
ended at 102.999999999997 s. A tightly bounded floating-point endpoint
reconciliation selected the existing final trace sample. No timestamp,
source-to-solver mapping, scientific tolerance, solver result, or trace value
was changed, and no interpolation extrapolation was performed. The solver
execution preceded this endpoint-handling correction, but the correction was
frozen before corrective protected processing.

## Result

- Numerical verification, liquid and solute conservation: `PASS`.
- Calibration reproduction: `PASS`; predicted late mean
  1.8821959328388052 g/s versus 1.8821959328386835 g/s target.
- Protected shape comparison: `FAIL`.
- All five normalized-shape RMSE gates failed.
- Pearson correlation was undefined for all five shots because the normalized
  predicted protected-window trace had zero population standard deviation.
- Overall disposition: `SOURCE_LINKED_RECONSTRUCTION_FAIL`.
- Reproducibility: `PRELIMINARY_RESULT_EXACTLY_REPRODUCED`.

The primary residual is `STRUCTURAL_MODEL_INADEQUACY`: the numerically sound,
constant-permeability reconstruction reproduces the frozen hydraulic scale but
not the protected rising-flow shapes. Source processing and the experimental
total-beverage versus hydraulic-equivalent liquid-mass basis remain contributing
data/semantic limitations, not grounds for retuning.

The result is a
`GOVERNED_NONBLINDED_REPRODUCIBILITY_CONFIRMATION`. It supports selecting a
future evolving-hydraulic-structure task for separate authorization; it does
not itself authorize or implement new physics.

## Review artifacts

- [Run status](../../validation/r1/WP01R_005_RUN_STATUS.json)
- [Execution result](../../validation/r1/WP01R_005_EXECUTION_RESULT.json)
- [Reduced predicted trace](../../validation/r1/WP01R_005_REDUCED_TRACE.csv)
- [Protected flow-shape figure](../../validation/r1/WP01R_005_PROTECTED_FLOW_SHAPES.svg)
- [Protocol correction record](../../validation/r1/WP01R_005_PROTOCOL_CORRECTION.json)

The observed curves in the new figure derive from the Waszkiewicz deposited
data under CC-BY-4.0, referenced through Puckworks commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`. No complete protected source
series is committed.

## Environment and record lifecycle

The [environment and provenance record](../../validation/r1/WP01R_005_ENVIRONMENT_AND_PROVENANCE.json)
binds the exact executable and retained OpenFOAM environment identities. Exact
compiler and MPI versions, OS distribution release, CPU model, artifact-bound
logical-processor count, and physical memory were not retained; each is
explicitly `UNAVAILABLE_FROM_RETAINED_EVIDENCE`. No present-machine value was
substituted. This is a declared reproducibility-metadata limitation, not a
scientific-result change, and no rerun was performed.

The execution result preserves its nested case-local acceptance object
verbatim. That object was captured before terminal R0 freeze binding, so its
pending or `NOT_FROZEN` fields are not authoritative final status. The
top-level R0 release gate and WP01R-003 source-linked analytical calibration
records are authoritative; the nested legacy R0 permeability note is not.
