# XSV-XCT-001 real-coffee XCT import and comparison protocol

Status: prospective freeze before scored transfer or new GPU execution.  
Issue: #66. Branch: `verification/xsv-xct-001-real-coffee-xct-comparison`.

## Questions and evidence order

The primary test is strict `SYNTHETIC_TRAIN_REAL_TEST`: does an
overlapping-sphere closure transfer without refitting to Wadsworth real-coffee
processed data? The secondary post-observation test uses exact SCI-MD-001
conductance ratios 0.373506, 0.389226, and 0.395294. Cross-sample or digitally
transformed comparisons are static capability evidence and cannot identify a
dynamic pressure mechanism.

Source reproduction precedes independent EWP reanalysis. Processed data do
not imply volume access. Published numerical permeability does not imply
laboratory validation. Loose straw packs do not represent controlled tamped
espresso pucks.

## Frozen processed-data population and features

All Wadsworth source rows with published permeability, connected porosity,
connected specific surface, mean particle radius, and uncertainty are scored;
missing rows are retained and excluded only per-metric. Coffee and integer
grind setting are labels, never substitute measurements.

The shared synthetic/real feature set is frozen to:

```text
phi_connected_x -> real phi_p_connected
specific_interfacial_area_lu / voxel_m -> real s_p_connected_per_m
pore_distance_q50 * voxel_m -> real R_mean_m (scale proxy; primary sensitivity)
```

Because pore-distance median and particle mean radius are not identical
quantities, the primary strict transfer reports both the full three-feature
mapping as `SCALE_PROXY_MISMATCH` and a two-feature
`connected_porosity_specific_surface` assessment. No real-data fit may alter
the synthetic-trained coefficients. The frozen XSV-ENS
`B_porosity_topology` full closure is not testable from processed data alone.

Primary metrics are RMSE(log K), median multiplicative error, signed log bias,
and empirical 95% interval coverage. R-squared is reported only with an
explicit baseline. Results are stratified by coffee and grind rank. Synthetic
training rows are grouped by `physical_lineage_id`; real rows are never mixed
into training. Real-only fitted references use leave-one-coffee-out grouping
and are secondary because only two coffees exist.

Out-of-domain status is assigned per feature outside the closed synthetic
minimum/maximum and by standardized nearest-neighbour distance. No row is
excluded for being out of domain or for disagreeing with the model.

## Source reproduction

Original names and units are retained beside normalized SI fields. Reproduce
the published percolation form, connected specific-surface treatment,
Kozeny--Carman comparison, directional averaging, and uncertainty convention
from published equations. Supplied values, recalculated values, and prose- or
figure-derived values remain distinct. No plot digitization is primary.

## Conditional volume route

Only a source-supplied or rights-cleared grayscale/binary volume with spacing,
axis, phase, crop, and permitted-use metadata may be admitted. Internally,
`solid=true`, `fluid=false`. Exact bytes remain external. Import checks cover
slice order/completeness, dimensions, spacing, axis mapping, phase inversion,
crop and normalized-volume hashes, central slices, and directional
connectivity.

Source binary segmentation is primary. A grayscale-only primary threshold is
frozen from the source method or image statistics before flow, with one lower
and one higher solid-threshold sensitivity. Thresholds cannot be selected from
permeability. Native, moderate, and coarse phase-aware resolutions are frozen
only where the pore phase remains resolved. Image resolution, LBM grid,
segmentation, and finite-subvolume effects are reported separately or as
confounded.

Flow uses the established gross-area contract:

```text
q_box_lu = superficial gross-box flux
u_void_lu = q_box_lu / phi_gross
K_gross_lu2 = nu_lu * q_box_lu / g_lu
K_void_lu2 = nu_lu * u_void_lu / g_lu
K_gross_lu2 = phi_gross * K_void_lu2
K_gross_m2 = K_gross_lu2 * voxel_m**2
```

Boundary semantics must match the source. Periodic wrapping that changes
face connectivity prohibits exact-parity adjudication. A diagnostic buffered
through-flow extension, if required, needs channel/Poiseuille verification,
mass conservation, force linearity, and periodic-control comparison and is a
`NUMERICAL_METHOD_CHANGE` limited to diagnostic pore scale.

The pilot uses retained XSV anchors, paired f64/f32 real anchors, multiple
low forces, Mach <= 0.05, stable K and q/g, convergence, conservation, and at
least 20% measured GPU-memory headroom. Tolerances are 1% for permeability,
3% directional ratio, and 5% localization. Broad flow uses f32 only after the
pilot passes. Failures and nonconvergence are retained without replacement.

If volumes exist, descriptor calculations use all feasible volumes. Flow uses
all feasible volumes or a frozen both-coffee fine/middle/coarse grind-rank
subset selected without permeability. Directions, thresholds, resolutions,
subvolumes, force levels, and transformations from one parent remain one
physical lineage. Subvolume bootstraps resample parent scans, never rows.

Static restriction levels are frozen at removed-void fractions 0.10, 0.20,
0.30, and 0.40 after baseline qualification. They are not fines, swelling,
compaction, or a pressure trajectory. A robust target claim requires at least
eight valid paired parents, at least 75% crossing, and an upper 95% bootstrap
bound at or below the exact target; otherwise attainment is sample- or
uncertainty-limited.

## Final dispositions

Processed Route A completes even when volumes are unavailable. Without exact
binary domains and matched boundaries, cross-code parity is
`CROSS_CODE_PARITY_NOT_ADJUDICATED`. Without independent parent volumes,
`REAL_COFFEE_REV_NOT_ADJUDICATED`. Generator and transfer conclusions use the
vocabulary frozen in `XSV_XCT_001_PROTOCOL.json`. The programme ends with one
evidence-selected next-task recommendation and does not commence it.
