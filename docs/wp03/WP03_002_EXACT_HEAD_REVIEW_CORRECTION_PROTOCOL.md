# WP03-002 exact-head-review correction protocol addendum

**Status:** prospectively frozen before additional diagnostic access or execution  
**Issue:** #51  
**Pull request:** #52  
**Reviewed head:** `cb7decead725d215c590994ff4504762cec59b4a`  
**Reviewed tree:** `e951506f1076554507a9403e9a28240c5259ed08`  
**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`

This append-only addendum supplements, and does not revise, the original
WP03-002 prospective diagnostic protocol. It freezes the bounded response to
the exact-head review findings
`REQUIRED_END_STATE_ADMINISTRATIVE_RECONCILIATION_INCOMPLETE` and
`FROZEN_DIAGNOSTIC_PROTOCOL_NOT_FULLY_EVIDENCED` before additional diagnostic
evidence is accessed or produced.

The execution matrix remains exactly `WASZ-5-COMPACT`, `WASZ-9-COMPACT`, and
`WASZ-11-COMPACT`, using their frozen configurations, 16-rank reproduction
mode, physical inputs, time steps, nonlinear tolerances, initialization,
evidence mappings, Puckworks locks, and source snapshots. The accepted
equation-preserving convergence-gate correction and retained continuous
analytical closure diagnostic remain unchanged unless evidence shows that the
correction changes the discrete governing solution or accepts an unconverged
state.

## Permitted diagnostic-only work

Existing retained logs and traces are inspected first. If they do not contain
the required per-iteration components, an exact-base predecessor build may add
logging only while preserving the original four-component convergence gate.
The diagnostic source diff and executable hash must be retained. Production
telemetry may be added only if required to reconstruct the accepted gate; it
must not change equations, controls, tolerances, ordering, iteration limits,
fields, initialization, or physical inputs.

For every nonlinear iteration the evidence must contain iteration number,
iteration flow, `flowChange`, `pressureChange`, `pressureFinalResidual`,
`poroelasticFlowClosureError`, relative tolerance, absolute tolerance, and the
solver convergence decision. An independent reducer recomputes:

```text
flow_ratio = flowChange / nonlinearRelativeTolerance
pressure_ratio = pressureChange / nonlinearAbsoluteTolerance
linear_ratio = pressureFinalResidual / nonlinearAbsoluteTolerance
closure_ratio = poroelasticFlowClosureError / nonlinearAbsoluteTolerance
retained_gate_ratio = max(flow_ratio, pressure_ratio, linear_ratio)
predecessor_gate_ratio = max(retained_gate_ratio, closure_ratio)
```

The reducer fails closed for a missing component or tolerance, a nonfinite
value, an unreconstructable combined residual, solver-reported convergence
with `retained_gate_ratio > 1`, or disagreement between the independently
calculated and solver-reported retained gate. Behavioral tests cover all
retained components passing, each retained component failing individually,
closure failing while retained components pass, missing and nonfinite values,
an inconsistent solver flag, and mixed relative/absolute tolerance handling.

Acceptance requires component histories to demonstrate that continuous
analytical closure has a representation/discretization floor distinct from
successive-iteration convergence, the retained three-component gate converges
under frozen controls, no corrected step is accepted above ratio one, and the
predecessor failure is caused by the equation-extrinsic closure veto rather
than tolerance relaxation or physical-input change.

## Required verification closure

A machine-readable compliance matrix must explicitly adjudicate every
original frozen requirement as `PASS`, `FAIL`, or
`NOT_APPLICABLE_WITH_EVIDENCE`: independent scalar residual agreement;
analytical/finite-difference derivative agreement; endpoint, near-limit,
zero-stress, high-admissible-stress, invalid-domain, bracket, and no-root
behavior; WP03-001 and machine-coupling regressions; serial/MPI repeatability;
timestep refinement; conservation; and full repository checks. Bracket and
no-root requirements may be not applicable only when exact production source
and tests establish that the current Picard path has no scalar bracketed-root
algorithm.

The corrected 5/9/11-bar runs and accepted VAL-CORPUS V3 reductions must remain
within declared numerical tolerances. All three cases must complete; source
ordering must remain `5 > 9 > 11`, model ordering `11 > 9 > 5`, and flow and
mass Spearman values `-1.0`. A material scientific change is a stop condition.

## Administrative and claim boundaries

Current-state records must distinguish merged base `main` from the WP03-002
candidate, close stale current-looking PR #38/#48/#50 states, preserve
time-scoped historical records and immutable VAL-CORPUS-001 campaign counts,
and explicitly define the executable identity field. The required candidate
state is `RESULT_COMPLETE_PENDING_EXACT_HEAD_REVIEW`; the next scientific task
after an approved merge is
`VAL_CORPUS_002_EXTRACTION_AND_CUP_CHEMISTRY`, which is not started here.

No physical or numerical retuning, new validation case, data planning,
experiment, protected scoring, or governing-physics work is permitted.
`PHYSICAL_VALIDATION: NOT_ESTABLISHED`,
`EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`, `VAL-CASE-002: NOT_STARTED`, and
`NEW_GOVERNING_PHYSICS: NOT_YET_JUSTIFIED` remain fixed. PR #52 and issue #51
remain open; merge is not authorized.
