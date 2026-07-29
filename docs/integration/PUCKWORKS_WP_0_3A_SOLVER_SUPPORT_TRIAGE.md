# WP-0.3A — Puckworks moving-upstream alignment and solver-support triage

**Classification:** external dependency review; evidence and verification
support only  
**Governing-physics change:** no  
**Protected analysis:** none  
**Scientific-result change:** none  
**Physical validation:** `NOT_ESTABLISHED`

## Identity and method

The solver-reviewed Puckworks baseline remains commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. The review target was resolved
before triage as `refs/heads/main` commit
`bafafef3bc3c77599af8551d4e582aedb9b23f08`, tree
`64ccf86aff4c90d1c513f1614b39e0823f64d6d7`.

Review used Git metadata and source blobs only. No new Puckworks module,
notebook, test, protected source, OpenFOAM scenario, or analyzer was executed.

## Adopted corrections

Schmieder's prose 9.3/7.4/3.8-bar triple is retired as a Darcy pressure-flow
datum. It has an ambiguous maximum/averaging basis and is not reproducible as
a Table 2 condition mean. The reproducible Table 2 condition-mean range is
2.58–8.4333 bar. At approximately 1, 2, and 2.8 mL/s, the rounded means for
grind levels 1.4/1.7/2.0 are respectively 2.85/2.70/2.75,
3.90/3.40/3.30, and 8.00/5.30/3.55 bar. These are achieved maximum-pressure
telemetry from one DE1 Pro, one coffee, one grinder, and the source DoE—not a
permeability law.

Liang's audit requires TDS to carry method, VST instrument, distilled-water
zero, instant-coffee gravimetric calibrant, measurement temperature and
calibration metadata. Schmieder adds the DR6000-T, 589 nm, 20 °C, DIN 10775
dried-sample calibration, dilution, centrifugation and freeze/thaw details.
Refractometric TDS, gravimetric dry-down solids, retained-liquid-corrected
oven drying, and model pseudo-components cannot be silently merged. EY must
carry its TDS method, mass/volume and density basis, dry-dose convention,
filtration, retained-liquid correction, and uncertainty.

The Foster direct normalized flow-curve result is negative. It supports only
an exploratory statement that machine/wetting dynamics can generate a dip and
recovery; it does not quantitatively reconstruct the published curve.

Paper B2's 85–95 s constant is estimated inside the scored 15–95 s interval.
It is a one-parameter direct-target, in-sample subset fit, not an external or
held-out late level.

## Solver-support selection

Moroney 2017 and Matias 2023 are adopted as non-protected verification
targets. The former supplies a three-ODE zero-flow reference, conservation
check, fine/coarse cases and asymptotic composites. The latter supplies
low-/high-Pe analytic limits and a parameter-free Sh/Pe front-gating trend.
Neither is connected to WP02.

Liang is adopted for analytic identifiability planning and observables
kernels. Its transient figure must be governed and digitized before fitting;
visual estimates are prohibited.

Vaca Guerra is adopted only as an inactive offline initial-state prior. Its
corrected beta signs, dry porosity, source domain, post-fit permeability and
viscosity convention must remain explicit. Published and viscosity-normalized
variants stay separate. It cannot replace WP02 permeability or represent wet
dynamic porosity.

Maille is deferred pending rights. Ellero's flow-reversal discriminator is
deferred pending the primary Petracco data and dimensional time basis.
Perticarini contributes metadata only. Kusumaatmaja is not adopted: its
density-matched binary-fluid LB method would add an unauthorized and
coffee-unvalidated wetting mechanism.

## Mechanism discrimination

Flow-reversal recovery is a future discriminator for filter-associated
fines. Irreversible bed-height or hysteresis evidence bears on compaction or
swelling. Early/first-drip error bears on wetting. Acceptable hydraulics with
poor species traces bears on extraction and chemistry. Delivered-pressure
error with acceptable imposed-pressure response bears on machine/headspace
coupling.

These are hypotheses requiring separate contracts, not implementation
authority.

## Rights, acquisition and lock recommendation

CC-BY Moroney and Schmieder material supports attributed independent
re-expression and metadata use. Liang digitization needs an explicit license
check. Vaca Guerra digitized/transcribed data require a redistribution review.
Maille remains blocked by redaction and rights. Perticarini is metadata-only.
Ellero/Petracco is blocked by missing primary data and rights. Kusumaatmaja
remains citation-only.

The final disposition is `ADOPT_SELECTED_EVIDENCE_WITH_FOLLOWUP`. The
recommended lock action is `RETAIN_EXISTING_LOCK_PENDING_ACQUISITION`: the
selected corrections and specifications do not require a runtime dependency
change, while data and rights gaps remain.

The v0.2.0 solver, WP02 result, historical executable, traces, configurations,
closure contract, and claim ceiling are unchanged.
