# Data-First Scientific Development Plan

- **Status date:** 29 August 2026
- **Status:** Current scientific execution plan and task-selection guidance
- **Applies to:** espresso-whole-pull model, simulation, validation, and independent-data work, with Puckworks as the evidence/data authority
- **Governance class:** `G0`
- **Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
- **Claim ceiling:** `PHYSICAL_VALIDATION_NOT_ESTABLISHED`
- **Current scientific gate:** `DIRECT_PAIRED_MEASUREMENT_FEASIBILITY`
- **Current solver task:** `NONE`
- **Current surrogate task:** `NONE`
- **SCI-MD-009-C2:** `PAUSED_NOT_CURRENT_PRIORITY`
- **Pilot scientific direction:** `OWNER_APPROVED_FOR_LAB_READY_PREPARATION`
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

### Priority 0 — close current lane

SCI-MD-009-C1-R1 is merged as a terminal response-model stop. The current surrogate/identifiability lane is closed, and SCI-MD-009-C2 must not execute now.

### Priority 1 — local method and mass-closure qualification contract

Prepare, but do not execute without separate authorization, the minimum contract
for repeated operational references, paired caffeine/trigonelline fractions,
spent residual, retained liquid, moisture basis, blanks, recovery, LOD/LOQ and
durable joins. Pannusch already supplies source-apparatus feasibility and planning
evidence; the remaining decision is local qualification and closure.

### Historical Priority 1 — paired inventory/fraction feasibility pilot

Prepare and execute, through human laboratory operations, a small combined EXP-006 / EXP-010 feasibility pilot. It asks whether measurement, uncertainty, mass closure, and the empirical relationship—if any—between operational reference extractability and production-shot inventory can support a later experiment. It is not an independent model-validation campaign. The laboratory-facing preparation brief is `docs/validation/PAIRED_INVENTORY_FRACTION_FEASIBILITY_PILOT_BRIEF.md`.

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
  OWNER_APPROVED
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
