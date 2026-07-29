# WP-0.3A — Puckworks alignment and holdout qualification

**Classification:** evidence review and experiment design only  
**Governing-physics change:** no  
**Holdout execution:** no  
**Physical validation:** `NOT_ESTABLISHED`

## Moving-upstream review

Puckworks `main` was resolved on 29 July 2026 at commit
`bafafef3bc3c77599af8551d4e582aedb9b23f08`, tree
`64ccf86aff4c90d1c513f1614b39e0823f64d6d7`. The review used Git metadata
and blobs only; it did not import or execute new Puckworks code.

The reviewed snapshot is 18 commits and 85 changed paths beyond the adopted
lock. The delta contains 57 documentation paths, 12 card paths, 15 Puckworks
code paths, and nine test paths, but no dataset or model-implementation path.
The locked Waszkiewicz model blob and the four source-data hashes used by
v0.2.0 are unchanged.

The newer material improves evidence semantics—especially the Pannusch
velocity convention, the Schmieder pressure-basis warning, and claim-binding
audits—but it supplies no new independent hydraulic campaign. The adoption
runtime dependency lock disposition is therefore `RETAIN_EXISTING_LOCK`;
the solver-support evidence disposition is
`ADOPT_SELECTED_EVIDENCE_WITH_FOLLOWUP`.

## Holdout decision

No reviewed candidate qualifies for an independent quantitative test of WP02
hydraulic transfer. Gagné 2021 is the closest: it has independent DE1 pressure,
flow, mass, and temperature traces from a different campaign. It still lacks
an exact hydraulic basket area, a pressure/flow uncertainty basis suitable for
thresholds, and explicit redistribution rights; its showerhead-flow estimate
also has documented late-shot drift.

Schmieder 2023, Angeloni 2023, and Perticarini 2024 can support independent
nonhydraulic extraction or chemistry questions. They cannot validate the
effective-permeability closure because they do not supply paired time-resolved
basket pressure and outlet flow. Foster 2025 primarily tests wetting and
machine/headspace behavior, while its flow curve is model-derived. The
Waszkiewicz campaign is ineligible because it selected and parameterized WP02.

The planning disposition is
`NO_QUALIFYING_INDEPENDENT_HYDRAULIC_HOLDOUT_AVAILABLE`. No comparison is
authorized.

## Required experiment

A qualifying campaign must be independent, preregistered, and blinded. It
must record calibrated basket-node gauge pressure, calibrated outlet mass,
time, and temperature for at least two pressure groups with at least five
independent shots per group. Basket hydraulic area, bed depth, dose, coffee,
grinder, preparation, water, machine, and timing landmarks must be retained.
Instrument calibration, resolution, and shot repeatability must support
thresholds before model outputs are opened.

R0 where meaningful, constant-R1, and the fixed v0.2.0 WP02 branch are the
only permitted branches. Unknown geometry, timing, or instrument quantities
may not be fitted to holdout scores.

## Mechanism discrimination

Residual signatures may motivate a later decision, never an automatic
implementation:

- imposed-pressure agreement with delivered-pressure failure suggests
  machine/headspace coupling;
- bed-height dependence or hysteresis suggests compaction or swelling;
- repeatable radial/depth structure suggests bounded heterogeneity;
- early or first-drip error suggests wetting refinement;
- acceptable hydraulics with poor species evolution suggests extraction and
  transport refinement;
- irregular nonrepeatable error calls first for preparation/channeling
  evidence.

The complete evidence matrix and machine-readable contract retain the
candidate-level rights, metadata, limitations, frozen branch identities,
access procedure, evaluation template, and claim ceiling.
