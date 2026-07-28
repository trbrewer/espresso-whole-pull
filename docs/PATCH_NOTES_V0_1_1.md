# Patch notes — v0.1.1

## Trigger

The first target-machine execution of package v0.1.0 reached `wmake` and failed
at the first solver include:

```text
fatal error: fvCFD.H: No such file or directory
```

The compiler command showed a valid OpenFOAM Foundation 12 installation and the
expected `finiteVolume/lnInclude` path. The defect was in the delivered solver:
it retained the historical `fvCFD.H` umbrella include despite targeting
Foundation 12.

## Source correction

`espressoWholePullFoam.C` now includes the required Foundation-12 interfaces
explicitly, including the field, finite-volume matrix, `fvc`, and `fvm` headers.
A static gate rejects any future reintroduction of `#include "fvCFD.H"`.

`Allwmake` also checks the active Foundation-12 `lnInclude` directories for the
required headers before invoking `wmake`. This distinguishes a package/API issue
from an incomplete local source installation.

## Diagnostic correction

Package v0.1.0 created its controlling acceptance JSON only after a completed
simulation. A compilation failure therefore left no single portable diagnostic
artifact. Version 0.1.1 creates:

```text
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_1.json
```

for environment, configuration, static-validation, test, build, mesh,
decomposition, MPI/solver, reconstruction, and postprocessing failures, as well
as successful completion. The report embeds bounded log tails and detected
issue lines rather than requiring a separate directory of logs.

## Scientific scope

No WP-0.1 physical assumption, scenario input, mesh resolution, closure,
calibration declaration, governing equation, or numerical acceptance threshold
was changed by this compatibility hotfix. The solver/package version is now
`0.1.1`; the scientific acceptance schema remains `V0_1`.

## Remaining runtime status

The corrected source could not be compiled in the packaging environment because
OpenFOAM Foundation 12 is not installed there. Compilation and execution on the
target machine remain the controlling runtime test. Any subsequent failure
should now be communicated using the run-status JSON above.
