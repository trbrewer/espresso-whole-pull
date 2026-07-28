# Patch notes — v0.1.3 numerical hardening

## Baseline

The v0.1.2 package successfully compiled and completed the R0 model on OpenFOAM Foundation 12 using 64 MPI ranks. It passed mesh, solver, reconstruction, field, and conservation gates. Version 0.1.3 deliberately changes numerical handling, so the predecessor’s outputs are retained as regression evidence rather than copied forward as new results.

## Corrected

- straight-sided wedge scale changed from `360/theta_deg` to `2*pi/sin(theta)`;
- mesh-to-cylinder volume equivalence made a fatal runtime gate;
- pressure ramp integrated exactly over each wetting step;
- breakthrough located by sub-step root finding;
- binary field compression disabled;
- future-dated build inputs normalized automatically;
- `FOAM_SIGFPE` enablement removed from issue counts.

## Added

- axial two-layer permeability support for verification;
- quarter- and three-quarter-depth pressure probes;
- mandatory layered-pressure fixture with a discrete reference;
- independent B0 one-dimensional reduced twin;
- reference analytical and B0 parity gates;
- live stage logs and stage timing JSON;
- build/source/executable provenance;
- `./Allverify` time-step, mesh, rank, and layered serial/parallel matrix;
- versioned v0.1.3 acceptance, trace, field-index, timing, and status artifacts;
- qualification CSV schema projection that excludes non-tabular diagnostics;
- single-report error trapping for both `Allrun` and `Allverify`;
- reuse of the case-generated B0 artifact during postprocessing;
- 26 unit tests and 25 static gates in the delivered package.

## Unchanged

- 58 mm/20 g R0 geometry and recipe class;
- 9 bar bed-top pressure boundary and 30 s duration;
- calibrated uniform permeability value;
- one-solute extraction closure and its engineering-assumption status;
- exclusion of machine coupling, evolving structure, fines, channeling, thermal physics, gas, and multispecies chemistry;
- physical claim ceiling.

## Runtime status at delivery

The packaging environment has no Foundation-12 runtime. The changed v0.1.3 C++ source has therefore not been compiled or executed here. `./Allrun` on the target system is the controlling implementation test; standard `./Allverify` is the controlling numerical-freeze test.
