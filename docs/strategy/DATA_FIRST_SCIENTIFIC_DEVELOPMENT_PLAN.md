# Data-First Scientific Development Plan

> **Current authority (2026-09-03):** SCI-MD-010 is `MERGED_COMPLETE`. L-HYD is
> `NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`; reduced E1 is
> `NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`; current full EWP E2 is
> `NOT_ADJUDICATED`. SCI-MD-011 is
> `ACTIVE_OWNER_AUTHORIZED_G1_EXISTING_DATA_TASK`. SCI-ED-003 remains complete.
> Stage F and Stage D are not authorized, and physical validation
> remains `NOT_ESTABLISHED`.
> No automatic successor is selected.
> SCI-ED-003 is complete with status
> `CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`; its owner decision is
> bounded and execution requires separate owner authorization.

> 2026-08-31 C1 correction: no tested bounded evolving-resistance form has stable
> grouped predictive advantage sufficient for adoption; fixed resistance is
> retained by parsimony. Mean ranking and the adoption decision are stable only
> within the tested processing windows, while effect magnitude varies. The
> grouped Waszkiewicz fixed-versus-evolving resistance task was
> null at condition variability. Retain fixed hydraulics and proceed to the
> separate-source `EWP-POROSITY-PERMEABILITY-PRIOR-001` task. No laboratory
> operation or production adoption is authorized.

> 2026-08-31: 39 reviewed families are registered. Immediate priority is grouped
> Waszkiewicz hydraulics. Visualizer is descriptive/boundary authority,
> Wadsworth/Vaca remain separate, and home lab remains deferred.

## Historical residual-selected result, superseded by later work (2026-09-01)

The task selection in this section is retained as history and is not current
execution authority.

Fixed Pannusch has strong advantage over the ordinal-only pooled baseline, but
no established advantage over the calibration-only boundary-aware fair
comparator; its systematic observation-window residual remains.
`OBS-PANNUSCH-FRACTION-WINDOW-001` proved that all 24 source windows already
derive from the corresponding beverage-mass fit and returned an exact null.
The selected, unimplemented fallback is `SCI-MD-PANNUSCH-FLOW-HISTORY-001`.
No additional extraction physics or laboratory operation is authorized.

## Historical additive decision, superseded by later work (2026-08-30)

The task selection in this section is retained as history and is not current
execution authority.

`ESPRESSO_DATA_LEVERAGE_001_EXISTING_DATA_SUPPORTS_IMMEDIATE_MODEL_ADVANCEMENT`.
The immediate task is `XSV-PANNUSCH-MULTIMODEL-001`, using grouped, scale-
reduced and bounded-nuisance comparisons on corrected Pannusch evidence.
SCI-ED-003 is deferred as a later absolute-closure and independence task;
home-lab operation remains deferred. See `EXISTING_DATA_LEVERAGE_PROGRAMME.md`.

- **Status date:** 29 August 2026
- **Status:** Current scientific execution plan and task-selection guidance
- **Applies to:** espresso-whole-pull model, simulation, validation, and independent-data work, with Puckworks as the evidence/data authority
- **Governance class:** `G0`
- **Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
- **Claim ceiling:** `PHYSICAL_VALIDATION_NOT_ESTABLISHED`
- **Current scientific gate:** `OWNER_DECISION_PENDING`
- **Current solver task:** `NONE`
- **Current surrogate task:** `NONE`
- **SCI-MD-009-C2:** `PAUSED_NOT_CURRENT_PRIORITY`
- **Pilot scientific direction:** `CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED`
- **Exact laboratory commissioning, expenditure, shipment and collection:** `REQUIRES_SEPARATE_HUMAN_OPERATIONAL_ACTION`

## 1. Executive decision

The numerical platform is substantially more mature than the independent empirical evidence available to constrain it. The programme has produced many positive engineering and numerical results, useful local reconstructions, and valid scientific falsifications, but few positive independent predictive results. That pattern does not show scientific dishonesty or a defective fail-closed approach. It does show that further simulation and assurance work against essentially the same evidence has reached diminishing scientific returns.

Before recovery and qualification of the full Pannusch corpus, the programme was
described as **data-starved, not model-starved**. That historical diagnosis is now
too broad. Source reconstruction, replicate-resolved fraction chemistry,
source-internal campaign-separated comparison, source-apparatus variance, and
species-trajectory diagnostics are available. Specific gaps remain for production
M0, operational-reference repeatability, initial/cup/retained/residual closure,
local method qualification, independent coffee/apparatus/laboratory transfer, and
hydraulic or structural validation. Use the pinned available-data authority,
current sufficiency artifact, and completed preflight before proposing measurement.

> Negative results are scientifically useful when they retire a hypothesis,
> constrain a claim, or change the next decision. Repeated negative or
> blocked results at the same missing-data boundary are a signal to change
> the information entering the programme, not to repeat the same style of
> analysis.

SCI-MD-009-C1-R1 is merged with the terminal disposition `SCI_MD_009_C1_STOP_NONLINEAR_RESPONSE_NOT_QUALIFIED`. Its response maximum was `0.08255430449708766` against `0.02`; profiles, recovery, observable bundles, precision, and pilot selection remain blocked. That honest stop closes the current surrogate/identifiability lane without claiming that every possible approximation is disproved.

## 2. No positive-result quota

There is no desired positive-to-negative scientific-result ratio. A programme that tests difficult hypotheses prospectively should expect rejections and null results. The raw count of `PASS`, `STOP`, and `REJECTED` labels is not a meaningful performance measure because numerical verification, source reconstruction, mechanism discrimination, and independent validation answer different questions.

The programme must not relax tolerances, reuse consumed data as holdout, or relabel reconstruction as validation merely to increase its apparent success rate. Work is valuable when it produces a trustworthy decision, including a decision to stop.

## 3. Four separate scientific scorecards

Future programme summaries must report these scorecards separately and must never collapse them into one positive/negative total.

### Numerical verification

**Question:** Does the implementation solve its stated equations consistently?

Examples include analytical and manufactured checks, conservation, mesh and timestep behavior, serial/MPI agreement, and boundary and observer correctness.

**Current interpretation:** `STRONG_POSITIVE_CAPABILITY`.

### Source reconstruction and calibration

**Question:** Can the model reproduce data used to construct or fit it?

**Current interpretation:** `MIXED; SOME USEFUL LOCAL RECONSTRUCTION, LIMITED TRANSFER`.

### Mechanism discrimination

**Question:** Does a candidate mechanism reproduce distinguishing trends, signs, ordering, or spatial behavior better than alternatives?

**Current interpretation:** `PRODUCTIVE BUT OFTEN NEGATIVE OR NON-IDENTIFYING`.

### Independent validation and transfer

**Question:** Does a frozen model predict genuinely independent observations without target-informed retuning?

**Current interpretation:** `NOT_ESTABLISHED; PRINCIPALLY LIMITED BY DATA`.

## 4. Three-test task-selection gate

Before any substantive model, simulation, surrogate, evidence, or experimental task begins, its proposer must answer three questions in writing.

1. **New information:** What genuinely new information enters the programme? Strong answers include a new direct measurement, independent dataset, new observable, untested parameter regime, materially different physical hypothesis, or direct solver calculation that cannot be inferred from existing runs. Weak answers include another presentation of the same evidence, another surrogate over the same cases without a decision need, or another assurance layer around closed artifacts.
2. **Decision consequence:** How would each plausible outcome change the next decision? A task is weak when positive, negative, and null or blocked outcomes all lead to the same next action.
3. **Grinder-to-cup relevance:** How does the task materially advance the integrated grinder-to-cup objective?

A proposed task that fails any two tests must not begin without an explicit owner exception identifying its unusual value.

Copyable task intake:

```text
NEW_INFORMATION:
DECISION_IF_POSITIVE:
DECISION_IF_NEGATIVE:
DECISION_IF_NULL_OR_BLOCKED:
GRINDER_TO_CUP_LINK:
REPEATED_BLOCKER:
LOWER_COST_ALTERNATIVE:
GOVERNANCE_CLASS:
```

## 5. Repeated-blocker circuit breaker

When two or more consecutive substantive tasks converge on the same missing measurement, the default next task must address that measurement. A new simulation may supersede that default only when it can resolve the blocker using genuinely new information already available.

SCI-MD-007, SCI-MD-008, and SCI-MD-009 collectively identify direct species inventory/reference-extractability and absolute fraction evidence as the current chemistry bottleneck. The SCI-MD-009-C1 response-model stop does not create a requirement for another response-model search. SCI-MD-009-C2 is paused and is not an automatically authorized successor.

Reconsidering SCI-MD-009-C2 requires all four conditions:

1. the proposed response approximation changes an identified decision;
2. direct-production evaluation is demonstrably impractical for that decision;
3. no feasible near-term measurement route can supply the needed information; and
4. explicit owner authorization reopens the lane.

## 6. Proportional correction-cycle rule

The default scientific-development cadence is:

```text
one implementation
-> one substantive review
-> at most one correction for a material scientific, claim, or fail-open defect
-> merge the honest result and move on
```

A second correction is allowed only where the first correction itself leaves a specific material risk uncontrolled. Correction rounds must not continue for stylistic consistency, redundant proof, optional lifecycle ceremony, non-material test completeness, or a desire to convert an honest negative result into a positive result.

Material scientific errors, false-green execution paths, misleading claims, source or rights defects, and production-safety defects must still be corrected.

> Governance protects the science; it is not a substitute for science and is
> not an independent programme objective.

Use the least burdensome governance class that protects the claim. G0 documentation does not acquire G1 or G3 controls merely because it discusses future measurements.

## 7. Current priority sequence

### Priority 0 — bounded owner decision

SCI-ED-003 has completed the minimum contract. The pending owner options are
`AUTHORIZE_STAGE_F_FEASIBILITY`, `DECLINE_EXECUTION`, or
`REQUEST_SPECIFIC_APPARATUS_OR_LABORATORY_CAPABILITY_INPUT`. None has been
exercised. If Stage F is separately authorized, execute only its defined
nonadjudicative feasibility programme. Stage D may be sized and frozen only
after qualified Stage F results and separate owner authorization. Independent
no-retuning comparison remains later; hydraulic and grinder modules remain
conditional under the SCI-ED-003 triggers.

### Historical Priority 1 — paired inventory/fraction feasibility pilot

Prepare and execute, through human laboratory operations, a small combined EXP-006 / EXP-010 feasibility pilot. It asks whether measurement, uncertainty, mass closure, and the empirical relationship—if any—between operational reference extractability and production-shot inventory can support a later experiment. It is not an independent model-validation campaign. The laboratory-facing preparation brief is `docs/validation/PAIRED_INVENTORY_FRACTION_FEASIBILITY_PILOT_BRIEF.md`.

“Prepare and execute” above is superseded historical wording. It grants no
current laboratory, preparation, commissioning, or execution authorization.

### Priority 2 — prospective no-retuning comparison

Use feasibility results to freeze a later data contract. Reserve new observations as a sealed comparison or holdout. Before target access, freeze parameters, inventory interpretation, flow inputs, observation operator, numerical settings, and acceptance criteria. Execute one no-retuning prediction and report the result honestly.

### Priority 3 — upstream hydraulic/grinder evidence

Proceed to grinder-specific particle-size, packing, porosity, and permeability characterization. Pair those measurements with synchronized pressure, flow, delivered mass, and, where feasible, puck deformation. Use the measurements to decide which hydraulic or evolving-bed mechanism is justified.

## 8. Near-term success criterion

> One genuinely new synchronized dataset is accepted with measured uncertainty,
> and one prospectively frozen no-retuning model comparison is completed against
> new observations.

Next-phase success is not obtaining more positive dispositions, increasing solver equation count, adding another mechanism, completing another synthetic sensitivity sweep, passing more governance checks, or finding a surrogate that merely permits another synthetic analysis.

## 9. Current non-priorities

Unless new evidence changes the decision, current non-priorities are:

- SCI-MD-009-C2;
- another polynomial, kernel, neural-network, or generic surrogate search;
- further synthetic inventory-identifiability work using the same cases;
- descriptor-based inventory prediction;
- assuming `I_ref` equals production `M0`;
- another broad literature atlas without a concrete eligible-data target;
- unrestricted fitting of existing source data;
- another evolving-puck mechanism without a distinguishing measurement;
- broad three-dimensional parameter sweeps or simultaneous addition of mechanisms;
- a new governance or verifier framework; and
- repeated review of unchanged scientific evidence.

## 10. Claim boundaries

```text
PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
INVENTORY_PREDICTOR:
  NOT_AUTHORIZED
c_s0_MAPPING:
  NOT_ESTABLISHED
I_ref_EQUALS_PRODUCTION_M0:
  NOT_ESTABLISHED
PROTECTED_OR_HOLDOUT_SCORING:
  NOT_AUTHORIZED_UNTIL_SEPARATE_PROSPECTIVE_FREEZE
NEW_GOVERNING_PHYSICS:
  NOT_CURRENTLY_JUSTIFIED
EXPERIMENTAL_FEASIBILITY_DIRECTION:
  CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED
EXACT_LABORATORY_PROTOCOL_AND_OPERATION:
  REQUIRES_HUMAN_LAB_CAPABILITY_INPUTS_AND_SEPARATE_OPERATIONAL_ACTION
```

Approval of the scientific direction does not authorize Codex or another agent to spend funds, contact or select laboratories, obtain quotations, ship material, collect data, or fabricate experimental results. Exact laboratory details must come from the laboratory and operator.

## 11. Restart instructions

Future substantive sessions must:

1. resolve live repository identities rather than trusting recorded SHAs;
2. read `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, `docs/governance/MINIMUM_NECESSARY_GOVERNANCE_STANDARD.md`, and this plan;
3. classify the proposed task using the four scorecards;
4. complete the three-test task-selection gate;
5. check whether it encounters a repeated blocker;
6. choose the least burdensome governance class that protects the claim;
7. prefer new direct data over another synthetic calculation when both address the same blocker; and
8. preserve negative results without automatically creating a rescue task.
