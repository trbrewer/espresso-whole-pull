# Paired Inventory and Species-Fraction Feasibility Pilot

```text
STATUS:
  SCIENTIFIC_DIRECTION_OWNER_APPROVED
  LAB_READY_PREPARATION_ARTIFACT
  NOT_A_FROZEN_ADJUDICATIVE_EXPERIMENT
  NOT_INDEPENDENT_VALIDATION
  NO_DATA_COLLECTED_BY_THIS_TASK
```

This brief prepares a laboratory conversation and feasibility exercise. Puckworks EXP-006 and EXP-010 remain the experimental-data authorities. This document neither duplicates nor replaces the Puckworks campaign catalog or the SCI-ED-002 contract. Exact laboratory commissioning, capability confirmation, protocol freeze, expenditure, shipment, and collection require separate human operational action.

## Purpose and boundaries

The pilot asks:

1. Can absolute caffeine and trigonelline mass be measured reproducibly in consecutive, mass-defined espresso fractions?
2. Can initial and spent-puck operational reference extractability be measured with enough repeatability to support a later experiment?
3. Does measured mass balance close sufficiently to interpret cup, retained, and residual species quantities?
4. Is there evidence of a repeatable empirical relationship between `I_ref` and the effective production inventory required by the model?
5. What analytical, shot-to-shot, preparation, recovery, censoring, and reference-tail uncertainties must enter a later G1 data contract?

The pilot does not validate the production model, estimate a universal `Q`, prove `I_ref = M0`, select an optimized minimum sample size, provide an independent holdout, authorize an inventory predictor, or establish `c_s0`.

## Practical starting envelope

This is a feasibility starting envelope, not an optimized or frozen minimum. It may change only through a later laboratory-capability discussion and G1 measurement-contract decision.

### Coffee

- one well-homogenized roasted-coffee lot and one recorded roast state;
- enough retained material for repeat preparations and method checks; and
- a measured and documented dry-mass or moisture basis.

### Operating conditions

- two materially separated shot conditions;
- preferably one controlled principal contrast, such as flow or grind;
- no simultaneous changes to several factors unless apparatus constraints require them; and
- exact settings selected prospectively with the operator and laboratory.

### Replication and fractions

- three to five valid shots per condition, approximately six to ten total;
- failed or excluded shots retained with reasons;
- approximately six consecutive mass-defined fractions per shot;
- boundaries recorded prospectively in beverage-mass units;
- the whole-shot endpoint retained; and
- no silent rebucketing after chemistry results are seen.

The replication range supports feasibility and variance estimation only; it is not a final power result.

### Species and reference material

- caffeine and trigonelline;
- repeated initial `I_ref` preparations from randomized aliquots of the homogenized lot;
- spent-puck `I_ref` for every shot where feasible;
- if capacity prevents every-shot spent-puck analysis, a prospectively selected subset with the limitation recorded; and
- `T_total` as useful context where practical, kept distinct from `I_ref` and production `M0`.

## Requested measurements, subject to laboratory feasibility

### A. Absolute chemistry

Request caffeine and trigonelline concentration or mass together with sample mass or volume sufficient to derive absolute mass. Retain calibration standards and curves, blanks, recovery or spike checks where supported, dilution factors, detection and quantification limits, instrument-native output, analytical batch identity, and every rerun or exclusion record.

### B. Initial reference extractability

Record method-conditioned `I_ref`, exact sample mass, dry-basis conversion, extraction solvent and volume, time, temperature, agitation, particle preparation, filtration, and analytical method. Collect sequential-cycle or retained-tail data sufficient to observe rather than assume the unresolved tail behavior.

### C. Spent-puck reference extractability

Record the complete puck-recovery method, retained-liquid handling, drying or moisture method, subsampling and homogenization, extraction and assay under a method explicitly related to the initial `I_ref` procedure, and all losses or unrecovered material.

### D. Shot telemetry and preparation

Record dose, grinder and setting, particle-size information where available, distribution and tamp procedure, basket and puck geometry, water temperature, measured pressure at available nodes, measured flow or delivered-mass history, beverage mass, fraction boundaries and collection times, reliably observed first drip, shot order, apparatus, operator, deviations, and exclusions.

### E. Data integrity

Retain raw instrument-native files and unmodified telemetry. Require monotonic elapsed time; explicit units; checksums; calibration and chain-of-custody records; and sample identifiers linking coffee aliquot, shot, fraction, initial reference, spent puck, preparation, and analytical batch. Do not smooth or replace raw values.

## Design practices

- randomize or balance shot order;
- randomize or block analytical order and record analytical batches;
- preserve every replicate;
- define exclusion reasons prospectively;
- never remove an outlier solely because it disagrees with a model;
- retain sufficient reserve material for repeats;
- preserve paired identity from initial coffee through fractions and spent puck; and
- distinguish prescribed quantities from measured quantities.

This brief does not freeze a reference-extraction stopping rule. Sequential-tail behavior must be measured empirically. The existing proposed stopping rule remains unvalidated.

## Pilot outputs and decisions

The pilot should estimate or document:

1. analytical repeatability by species and sample type;
2. between-preparation variation for initial `I_ref`;
3. between-shot variation;
4. spent-puck preparation variation;
5. reference-extraction tail behavior;
6. censoring and detection-limit incidence;
7. initial-reference/cup/spent-puck mass-balance closure;
8. exploratory condition dependence;
9. an exploratory `I_ref`-to-production-inventory bridge assessment, explicitly non-universal and non-validating; and
10. enough variance and operational evidence to design—or decline—a later adjudicative campaign.

Possible pilot-level dispositions are:

```text
PILOT_METHOD_AND_PAIRING_FEASIBLE
PILOT_ANALYTICAL_METHOD_DEVELOPMENT_REQUIRED
PILOT_REFERENCE_EXTRACTION_TAIL_NOT_CONTROLLED
PILOT_MASS_BALANCE_INSUFFICIENT
PILOT_BRIDGE_NOT_STABLE_OVER_TESTED_CONDITIONS
PILOT_VARIANCE_TOO_LARGE_FOR_CURRENT_MODEL_DECISION
PILOT_DATA_SUFFICIENT_TO_FREEZE_FOLLOW_ON_NO_RETUNING_CAMPAIGN
```

These are feasibility and design dispositions, not physical-validation results.

## Follow-on no-retuning campaign

Pilot data are method-development and design evidence; they are not automatically an untouched holdout. Before a later adjudicative campaign:

1. freeze the estimands and relationship among `T_total`, `I_ref`, production `M0`, and any bridge parameter;
2. freeze model version and executable;
3. freeze all scientific parameters;
4. freeze hydraulic boundary inputs;
5. freeze fraction boundaries and observation operators;
6. freeze processing and exclusions;
7. freeze numerical settings and tolerances;
8. freeze uncertainty treatment and acceptance criteria;
9. designate and seal comparison observations;
10. generate and hash immutable predictions before protected target access; and
11. score once without post-result retuning.

The later evidence must be labelled according to its actual design: within-campaign holdout, independent holdout, or cross-condition transfer. It is not independent merely because collection occurred after model development.

## Later upstream hydraulic priority

After the chemistry/inventory feasibility question, the next major empirical direction is grinder-specific particle-size distribution, packing, porosity, puck geometry, permeability, synchronized pressure, synchronized flow and delivered mass, and puck deformation where feasible. This direction links to Puckworks EXP-003 and existing synchronized-measurement planning. New hydraulic or evolving-bed physics should be selected from these measurements rather than implementation convenience.

