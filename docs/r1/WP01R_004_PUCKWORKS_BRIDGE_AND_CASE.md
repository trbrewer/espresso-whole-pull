# WP01R-004 Puckworks Bridge and Deterministic R1 Case

## Purpose and authority

WP01R-004 implements the deterministic input bridge for the Waszkiewicz R1
scenario. Authority is, in order:

1. merged [R1 contract](../validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md);
2. merged [source dossier](../evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md);
3. locked Puckworks identity;
4. `config/reference_R0.json` only for explicitly inherited numerical and
   chemistry assumptions.

The scope is `SOURCE_SCENARIO_CHANGE_ONLY`; governing physics and qualified R0
configuration are unchanged.

## Commands

Regenerate and check the canonical inputs:

```sh
python3 scripts/r1_contract_bridge.py \
  --root . \
  --output config/reconstruction_R1_waszkiewicz_9bar.json \
  --check
```

Generate a complete case without invoking OpenFOAM:

```sh
python3 scripts/prepare_case.py \
  --root . \
  --config config/reconstruction_R1_waszkiewicz_9bar.json \
  --case-dir /tmp/r1-case \
  --nprocs 32
```

The generated case contains canonical scenario JSON, `blockMeshDict`,
`controlDict`, `decomposeParDict`, `espressoModelProperties`, byte-exact
qualified `fvSchemes`, `fvSolution`, `0.orig`, initialized `0`, analytical and
reduced preflights, input provenance, and a deterministic governed manifest.
Environment, hostname, wall-clock, username, and absolute paths are omitted
from governed outputs.

## Frozen mappings

The 58 mm basket is hardware context; the hydraulic mesh uses the 56 mm bed
diameter and 0.028 m radius. Basket-top pressure ramps to `870902.419 Pa`
gauge over 3 s and then remains constant. Solver time equals source time plus
3 s; the source fixed 8 s processing offset is excluded.

Uniform saturated and wetting permeability are both
`2.8642613245723525e-15 m2`. This is one historically calibrated scenario
parameter and zero runtime, generation-time, or post-run adjustable
parameters.

The protected predictor is the hydraulic-equivalent flow
`1000 * 965 * outlet_flow_m3_s` in g/s. It excludes solute flux. The
beverage-mass derivative is an unscored diagnostic. Protected shot IDs,
windows, gates, and Pearson degeneracy rules are carried as selectors only;
no protected numerical series is embedded or compared.

## Determinism and R0 protection

Two unrelated target directories produce identical governed file sets,
individual bytes, and aggregate identities. The generated manifest uses
logical paths, sorted traversal, SHA-256 hashes, canonical JSON, and no
environment metadata.

Solver C++, reference mathematics, R0 configuration, qualified case templates,
baseline evidence, and the 19-file R0 scientific-input bundle remain
unchanged. Analytical and reduced preflights verify configuration only; they
are not OpenFOAM or physical results.

WP01R-004 performs no fitting, optimization, OpenFOAM command, Puckworks code
execution, or protected comparison. After review and merge, issue #7 may run
the central R1 case and compute the predeclared scorecard.
