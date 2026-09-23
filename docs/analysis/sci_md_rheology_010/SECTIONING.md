# Separate virtual-sectioning diagnostic — Ribes / McKeon

This owner-requested addition is descriptive, not a retrospective acceptance
contract. It changes no 010 scenario, metric, allowance, threshold or run count.
It uses stored 30 s base-case final fields for both laws/histories, old core-fast
and new annulus-fast C/E2. Old E2 is explicitly historical diagnostic evidence,
not a new integration or new primary transfer evidence. No missing fields are
interpolated and no case is rerun for this addition. `SECTIONS.json` reports any
missing case/output explicitly. No fitting or beverage-EY rescaling is performed.

## Field meanings and conservation

The accepted solver initializes `remainingExtractable` uniformly to
M0/fullMeshVolume, with M0=0.0056 kg, then removes the extraction source from
that field. It has units kg/m3 of **bulk bed**, representing the remaining
modeled solid-phase extractable inventory. It is not all remaining dry coffee.
`dissolvedConcentration`, also dimensioned kg/m3, is per **pore liquid**;
its stored mass is concentration × porosity × saturation × bulk volume.
The concentration equation uses `ddt(porosity,c)` and the same extraction source
removed from the solid. This task is fully saturated with porosity .4.
The observer reads actual porosity/saturation fields and checks dimensions,
bounds and whole-domain native mass correspondence.

There is no native `initialDryCoffeeMass` cell field. The known .020 kg initial
dry dose is reconstructed as a uniform dry-mass density over actual volumes,
consistent with the declared homogeneous inventory fraction .28 and native
uniform M0 initialization. This is a stated scenario assumption, not measured
sample mass or a new evolving solid-density solution. Regional initial inventory
is M0 V_region/V_total. Regional **solid depletion** is initial minus remaining
solid inventory; its percentage denominator is initial dry coffee in that region.
Retained dissolved solute is reported separately in kg and as percent of the same
denominator. It is not subtracted from solid depletion to claim regional delivery.

Whole-domain closure is M0 = remaining solid + dissolved pore solute + outlet
solute + inlet solute loss, within inherited 1e-8 kg; field integrals agree with
native values within 1e-10 kg. Every section partition sums to the whole domain
within 1e-12 kg. Native correction mass is separately governed by the unchanged
qualification. Source semantics: `espressoWholePullFoam.C`, initialization near
`initialExtractableDensity`, source/transport near `localExtractionRate`, and
mass integrals near `localRemainingMass` (hash bound in REUSE.json).

## Actual geometry and partial cells

The observer reads native polyMesh points, faces, owner and neighbour, computes
oriented polyhedral cell volumes, and applies the accepted full-basket wedge
factor 2*pi/sin(5 degrees). Actual vertex radii and axial extents independently
check these against annular volumes at the inherited 1e-8 relative tolerance.
For a cell spanning [r_lo,r_hi] and a section [a,b], its contribution is
V_cell * max(0, min(r_hi,b)^2 - max(r_lo,a)^2)/(r_hi^2-r_lo^2), with disjoint
intervals given zero. This is the native axisymmetric annular interpretation of
the wedge mesh, not an arbitrary-polyhedron cylinder-clipping method.
Cell-average fields are piecewise constant. Cuts are exactly 0,18,25,29 mm.
No cut is moved to a cell centre; no slope or hidden subcell profile is invented.
Partition-of-unity, uniform-field invariance and known regional-inventory tests
check the operator. Partial-cell counts and field/mesh hashes are retained.

E2 has radial cells 0–14.5 and 14.5–29 mm at each axial station. Its experimental
centre section combines the core cell with part of the annulus cell. Both
18–25 and 25–29 mm lie entirely in the **same annulus cell** at every station.
Their extensive masses differ by area, but normalized E2 inventory/depletion
values must coincide. This equality is an imposed resolution limit, not evidence
that the true middle and edge are uniform. C resolves a finer radial pattern,
but its finite-volume averages and partial-cut reconstruction are still model
outputs, not an experimental recovery assay. No unique lateral mechanism follows.

Regional outlet water share remains the native core/annulus exit-flow partition.
The scalar aggregate has no tracer of initial-region origin, and snapshots alone
do not yield time-integrated outlet solute for the Ribes cuts. These regional
outlet deliveries are labeled NOT_INFERRED_FROM_SECTION_INVENTORY. Native
core/annulus partition also differs geometrically from the Ribes cuts.

## Source lineage and assay mapping still required

The [newer Decent summary](https://www.decent.la/docs/radial_uniformity_of_espresso_extractions)
explicitly summarizes [Ribes's March 2020 deck](https://decentespresso.com/doc/radial_extraction_uniformity/radial_extraction_uniformity.pdf).
They are **one underlying experiment**, not replication. The deck uses 12 g in a
15 g basket and 1:2.5 ratio, with filter/tamper interventions and 18/25/29 mm cuts.
It shows region and beverage TDS-derived EY, but does not supply a complete
sample-mass/recovery/retained-liquid calculation or shot-EY anchoring equation.
The summary does not fill these metrology gaps. Three to five refractometer
readings are not three to five independent shots. The retained Puckworks
`ribes2020/radial_ey` entry remains slide-grade context.

[Ribes 2021](https://decentespresso.com/doc/wdt_radial_uniformity/wdt_radial_uniformity.pdf)
is a separate contact-screen experiment: 19 g, 20 g VST/Pullman baskets, 1:2
ratio and the same cuts. Puckworks `ribes2021/radial_ey` records missing replicate
counts, undocumented recovery/retained-liquid corrections and anchoring, and a
Pullman/no-screen inconsistency between area-weighted and stated shot EY.
The photo sequence supports sectioning and water recovery, but cannot establish
recovery efficiency, exact sample water/dry masses or a closed mass balance.
Do not assign the Pocket Science method to either Ribes dataset as fact.

[Pocket Science's own workflow](https://pocketsciencecoffee.com/2024/01/07/espresso-water-flow-part-0-workflow/)
describes prompt two-zone sectioning, oven drying at 250 F for eight hours,
weighing dried sections at 0.1 g resolution, approximately 20:1 hot-water recovery
in Clever drippers for ten minutes, and TDS measurement. Handling/volatile losses
and retained brew are acknowledged. Its accepted `edge_ey_condition_means` record
uses section EY anchored to shot EY and outer-to-total sample mass fractions;
it does not measure this model's 18/25 mm sections. Drying a wet section can leave
pore-liquid solute in the dried residue: interpreting recovered solubles therefore
requires both model compartments, actual sample masses, recovery efficiency,
liquid handling and the source's mass-balance/anchoring rule. This diagnostic
supplies the compartments; it does not establish that assay mapping.

[McKeon's critique (2023)](https://rmckeon.medium.com/a-critique-of-radial-uniformity-experiments-in-espresso-a232f9087ed5)
questions whether coarse outer-ring cuts conceal a narrow wall feature and
axial variation, and notes the ambiguity created by lateral solute movement.
He describes a shot-EY baseline interpretation of Ribes and proposes finer cuts,
vertical inspection and different brew ratios. That is a secondary interpretation,
not missing source-authorized assay documentation. His photographs and different
grounds-TDS procedure do not quantitatively establish depletion, and the proposed
radial profile is not a measured target. We use the critique to identify resolution
and observable limitations, not to select permeabilities or demand another run.

No source-to-model regional EY agreement is scored. A valid mapping would still
need source-specific wet/dry sample masses, post-shot drainage/retention history,
retained-liquid solute, recovery conditions/efficiency, losses, TDS mass basis,
replicate uncertainty and any shot-EY anchoring, as well as compatible geometry,
coffee/inventory and pressure history. Useful radial evidence is acknowledged;
PHYSICAL_VALIDATION = NOT_ESTABLISHED. No laboratory action or successor.

Observer correction before publication: Foundation 12 writes dimensionless
porosity/saturation as `dimensions [];` (`dimensionSetIO.C`,
`dimensionSet::writeNoBeginOrEnd`). The first parser expected seven explicit
zero exponents and rejected all 16 cases. Its output is retained externally.
The parser now accepts the native empty bracket representation as dimensionless,
with a focused regression test. This reuses the same fields and changes no
acceptance contract, conservation tolerance, run count or native evidence.
