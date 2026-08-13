# XSV-XCT-001 data availability and rights

Status: prospective source audit, 2026-08-12.  
Change declaration: `NUMERICAL_METHOD_CHANGE`; scope:
`DIAGNOSTIC_PORE_SCALE_ONLY`; production OpenFOAM integration: false;
Puckworks runtime-lock change: false; physical validation: false.

## Admitted sources

Wadsworth et al. (2026), DOI `10.1098/rsos.252031`, is the primary source. The
article is CC BY 4.0 and states that all processed permeability,
pore-network, and grain-size data are supplied in a linked ZIP. It reports 22
real packed-ground-coffee samples: Tumba/Rwanda and Guayacan/Colombia at
Mahlkonig settings 1--11, reconstructed at 2.69 and 2.99 micrometres per
voxel. Samples were loaded loosely into 5 mm straws without controlled
tamping. Published permeability is an LBflow numerical result, not a direct
permeameter measurement.

The processed source data are admitted for `SOURCE_REPRODUCTION` and
`INDEPENDENT_EWP_REANALYSIS`. Repository inclusion is limited to compact
rights-compatible tables with attribution. The paper does not state that raw
reconstructions or binary segmentations are public. No rendered figure is a
volume substitute.

Mo et al. (2023), DOI `10.1038/s41598-023-42380-y`, is secondary comparison
evidence. Its data-availability statement makes datasets available from the
authors on reasonable request; no request is sent by this task. Its primary
threshold was partly conditioned on an assumed literature porosity, so any
future geometry is `SOURCE_MODEL_CONDITIONED_SEGMENTATION` and cannot
independently confirm porosity.

## Route disposition at freeze

- Route A: `ADMITTED_AND_REQUIRED`; execute on every usable Wadsworth row.
- Route B: `CONDITIONAL_NOT_YET_ADMITTED`; no rights-cleared raw or segmented
  coffee volume was found in local staging or the public source record.
- Route C: create the owner-facing request specification if Route B remains
  unavailable after the bounded public audit.

The locked Puckworks runtime is commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. It is read-only and unchanged.
The read-only evidence reference observed at commencement is commit
`bafafef3bc3c77599af8551d4e582aedb9b23f08`, tree
`64ccf86aff4c90d1c513f1614b39e0823f64d6d7`. It is context, not runtime
authority. Puckworks data are not copied as a substitute for the publisher's
source package.

## Scientific classifications

```text
PRIMARY_SAMPLE_CLASS: REAL_PACKED_GROUND_COFFEE_XCT
PRIMARY_PREPARATION_EXCLUSION: NOT_CONTROLLED_TAMPED_ESPRESSO_PUCK
PRIMARY_PERMEABILITY_ROLE: PUBLISHED_NUMERICAL_PERMEABILITY_REFERENCE
DIRECT_PERMEAMETER_VALIDATION: FALSE
PHYSICAL_VALIDATION: NOT_ESTABLISHED
```
