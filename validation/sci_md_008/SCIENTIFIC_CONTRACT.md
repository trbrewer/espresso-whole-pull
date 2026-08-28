# SCI-MD-008 scientific contract

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`. Evidence class:
`SOURCE_DEPENDENT_RECONSTRUCTION`. The accepted Schmieder/Pannusch fractions
were consumed by SCI-MD-004 and are not independent validation.

The frozen comparators are B0 (canonical SCI-MD-004 exponential), B1
(production indexed PDE, uniform geometry, prescribed flow), and B2
(production indexed PDE, existing half-depth 0.5/2.0 axial contrast,
prescribed flow). No scientific parameter is fitted or retuned. The accepted
1000 kg/m3 beverage observation density is used. Reported constant flow and
every reported lower/upper mass boundary are used without smoothing,
extrapolation, gap imputation, or target-selected choices.

Before target scoring, normalized fraction shape must be invariant under
0.01x, 0.1x, and 1x inventory scaling within `1e-6`. This tolerance is larger
than observed deterministic/interface rounding and materially below the reused
SCI-MD-004 meaningful relative-improvement threshold of 0.15. Failure requires
`SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT`; B0/B1/B2
performance is then not adjudicated. If reached, positive incremental value
would require at least 15% aggregate improvement, more than half of blocks
improved, neither species worsened, and all direction/numerical gates passed.

