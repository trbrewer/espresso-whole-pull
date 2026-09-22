# Reproduction and output contract

Use Foundation OpenFOAM 12 and an external artifact root ART. PW is a clean
read-only checkout at 2058d0e947ee9eb92c52d64f6165b810f1fb4732. ACCEPTED is the
owner-retained SCI-MD-RHEOLOGY-005 artifact directory. No restricted table or raw
run is distributed here. Missing evidence must be supplied from the accepted
external register, not replaced with a reduced model.

Copy solver/espressoWholePullFoam into ART/build and set FOAM_USER_APPBIN to
ART/bin before wmake. Compare resulting source/executable identities against
FREEZE.json; a new binary is not silently the recorded binary. Build logs and
all native artifacts stay external.

```sh
python3 -m unittest tests.test_sci_md_rheology_006 -v
python3 -m tools.sci_md_rheology_006.short --output "$ART/short" \
  --executable "$ART/bin/espressoWholePullFoam" \
  --baseline "$ACCEPTED/bin/espressoWholePullFoam"
python3 -m tools.sci_md_rheology_006.reject --output "$ART/rejections" \
  --fixture "$ART/short/transverse/case" --executable "$ART/bin/espressoWholePullFoam"
# Historical preparation; refuses an existing freeze:
python3 -m tools.sci_md_rheology_006.prepare --artifacts "$ART" \
  --accepted "$ACCEPTED" --puckworks "$PW"
# Once per exact full_matrix slot, controls first:
python3 -m tools.sci_md_rheology_006.run --artifacts "$ART" \
  --accepted "$ACCEPTED" --identity "$IDENTITY"
```

The recorded freeze is immutable. Completed runs cannot be replayed into their
original identities. --recovery-reason applies only to a failed slot, preserves
failed artifacts and cannot exceed the four-attempt reserve. Separate new
reproduction runs need their own authorized budget/identities; these commands
are not an automatic successor campaign.

Read-only analysis and plotting of completed evidence:

```sh
python3 -m tools.sci_md_rheology_006.analyze --artifacts "$ART" --output "$OUT"
# For the four base cases only, obtain cell coordinates from the native mesh:
postProcess -case "$BASE_CASE" -func writeCellCentres -time 0
python3 -m tools.sci_md_rheology_006.plot --artifacts "$ART" --output "$OUT"
python3 scripts/validate_sci_md_rheology_006.py --root .
```

RADIAL_SCHEMA.json describes the ordered CSV columns and units. Local coupled
mu is evaluated at state_s=start_s; pressure and face flux apply to the interval;
next-state concentration and inventories apply at end_s. Native pressure-matrix
flux, not reconstructed U, supplies signed zone flow. Legacy cup diagnostics
retain positive-outflow semantics; the observer checks their correspondence to
signed flux under the reverse-flow gate. Invalid Q fails support without a share
fallback. The native radial trace can preserve invalid support for diagnosis.

Radial observe mu extrema are counterfactual local-law diagnostics; hydraulics
retain constant liquid viscosity. Uniform/axial aggregate_intervals.csv remains
unchanged. Radial aggregate modes omit it and its series-resistance quantities.
Shared radial-coupled analytical-flow/error fields are NaN, explicitly unavailable;
they must not be treated as scalar-comparator predictions. The independent scalar
comparator is 4/7 under the frozen geometry/boundaries, not a chemistry comparator.

Plots identify synthetic geometry and source assumptions. Field plots use only
5 and 15 s; viscosity is the applied beginning-step coefficient, while pressure
is the interval solution. Scoring uses every native interval over 0–30 s.
EXCHANGE.json independently reconstructs the fixture's native upwind advective
solute flux using saved darcyFlux and donor concentrations, and confirms that
MPI partitions straddle the material interface. No new native run is involved.

The original execution freeze is retained after the bounded analysis-only repair
in POST_EXECUTION_CORRECTION.json. The current reducer implements the protocol's
case-level OR rule and creates its output directory. All actual scores and
outcomes are identical to the original reducer; the active validator checks both
the original and amended identities. Native execution inputs were unchanged.
