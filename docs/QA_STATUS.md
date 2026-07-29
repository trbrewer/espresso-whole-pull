# Package QA status — 0.2.0

**Active role:** WP-0.2F no-physics release finalization

**Release qualification:** PASS

**Release disposition:** SOFTWARE_AND_SOURCE_LINKED_RECONSTRUCTION_RELEASE_PASS

**Release gates:** 119/119 Python tests, 34/34 active static gates, 131/131
source-manifest entries, and a passing OpenFOAM Foundation 12 build.

**Historical baseline:** v0.1.4-public.1 remains immutable and independently
checked by the baseline-integrity verifier.

**Historical package role:** WP-0.1F no-physics-change freeze finalization

**Target runtime:** OpenFOAM Foundation 12

**Packaging runtime:** no Foundation-12 installation available; target `./Allrun` and standard `./Allverify` remain controlling

## Construction and archive QA

The delivered source package is required to pass:

- shell syntax checks for `Allrun`, `Allverify`, `Allclean`, `Allwmake`, and shell helpers;
- Python bytecode compilation for every script and test;
- 36 standard-library unit/integration tests;
- 32 static package gates;
- 28/28 no-physics-change comparisons against the target-qualified v0.1.3 source contract;
- deterministic case-generation tests;
- analytical first-drip, Darcy-flow, wedge-volume, and retained-water tests;
- reduced B0 conservation and parity mathematics tests;
- heterogeneous layered-pressure discrete-reference tests;
- Foundation-12 build-path and mocked `Allwmake` tests;
- future-timestamp normalization tests;
- exact build-provenance verification tests;
- absolute-path binding of the `./Allrun` executable through the fixture, reference, and complete qualification matrix;
- terminal cross-check of qualification executable path, byte count, and SHA-256 against the reference build record;
- diagnostics tests for `FOAM_SIGFPE`, benign numeric relative-error metrics, real floating-point exceptions, compiler errors, and shell failures;
- synthetic end-to-end acceptance finalization and terminal-manifest self-verification;
- qualification CSV schema-projection tests;
- source-manifest exact-file, mode, and aggregate verification;
- clean-state restoration;
- ZIP integrity, path, fixed-timestamp, and executable-permission checks.


## Mocked full-lifecycle QA

A deterministic mock Foundation-12 environment exercised the complete package orchestration from a fresh source tree:

```text
./Allrun                                      PASS
./Allverify (standard, ten runs)             PASS
aggregate qualification gates                9 / 9 PASS
freeze finalization                          PASS
terminal manifest read-only verification     PASS
PROFILE=smoke replay                         PASS
terminal manifest unchanged by smoke         PASS
portable archived executable binding         PASS
```

A separate controlled `fixture_checkMesh` failure exited with code 17 and produced one `FAIL` run-status JSON identifying the exact failed stage and primary log. The mock lifecycle verifies shell orchestration, report generation, hash binding, failure capture, and profile isolation; it is not represented as an OpenFOAM numerical result.

## Runtime evidence inherited from v0.1.3

The bundled predecessor evidence records a successful target-system Foundation-12 reference run and a successful ten-run standard qualification campaign with 9/9 aggregate gates. Version 0.1.4 uses that source contract only to prove no governing-physics change; it does not relabel predecessor outputs as a v0.1.4 run.

## Controlling v0.1.4 runtime checks

The target system must still establish:

```text
./Allrun     PASS
./Allverify  PASS
terminal freeze manifest verification PASS
```

A package-construction PASS is not represented as an OpenFOAM execution result.

## Release disposition

Before target execution:

```text
construction/archive QA: PASS
v0.1.4 reference execution: PENDING
v0.1.4 numerical qualification: PENDING
v0.1.4 immutable freeze: PENDING
physical validation: NOT_ESTABLISHED
```

After both controlling commands and terminal verification pass:

```text
implementation: PASS
code verification: PASS
numerical qualification: PASS
release provenance: PASS
reference freeze: FROZEN / QUALIFIED
physical validation: NOT_ESTABLISHED
```
## WP-0.3B development qualification

The current branch adds only non-protected mathematical references and
measurement kernels. Its dedicated fixed-path verifier rejects solver, case,
configuration, trace, WP02-result, closure-contract, and dependency-lock
changes. Canonical reference execution is distinct from OpenFOAM scientific
execution and cannot establish physical validation.
