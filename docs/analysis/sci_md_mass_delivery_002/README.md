# Pinned research consumer

Select a family explicitly; the consumer never chooses a target-score winner.
Use an explicit Puckworks checkout at HANDOFF.json's producer revision:

```bash
git clone https://github.com/trbrewer/puckworks "$PRODUCER"
git -C "$PRODUCER" checkout --detach cec97741e72b126f04f05b73691d9223bbdb148f
python3 scripts/research_conditioned_mass_delivery.py --producer "$PRODUCER" \
  --model MTF --temperature-K 363.15 --source-flow-setting-code 1.7 --stop-kg 0.04
CONDITIONED_MASS_PRODUCER="$PRODUCER" python3 -m unittest discover -s tests \
  -p test_research_conditioned_mass_delivery.py
```

Allowed families: M0, MT, MF, MTF, SETTING_AWARE_EMPIRICAL. Synthetic requested
intervals demonstrate the fitted artifact's actual behavior, including small
slopes. The producer also provides an offline synthetic nonzero-slope example:
`python -m puckworks.analysis.conditioned_mass_delivery` from its checkout.
Source reconstruction/fitting/freezing/scoring commands belong to the producer's
task README. Read its RESULT.md before interpreting any model prediction.

The consumer verifies the explicit commit/tree and every runtime module/model
hash, then loads both wrapper and reused integration kernel in an isolated
namespace with an empty package search path. An installed Puckworks package
cannot supply dependencies. Missing or modified files fail closed.
HANDOFF.json is separate from the production dependency lock, which is unchanged.

Inputs: mass kg, constant nominal programmed temperature K, dimensionless
source_flow_setting_code. No measured/local puck temperature, hydraulic flow
conversion, flow/pressure/time/mass-attainment prediction, inventory or mechanism.
Queries must lie in the FIT mass interval and design diamond, not its rectangle.
Ramps are unsupported. Modeled gaps are not measured whole-cup totals.

G1 / NO_GOVERNING_PHYSICS_CHANGE. SOURCE_INTERNAL; TARGET_EXPOSED;
RETROSPECTIVE_MODEL_DEVELOPMENT_COMPARISON. March was already exposed; excluding
it from fitting does not make it blind. Source-derived models and aggregate
results retain Pannusch/Schmieder attribution and CC-BY-NC-3.0 treatment,
[Mendeley DOI 10.17632/y2tz67f6ry.1](https://doi.org/10.17632/y2tz67f6ry.1),
distinct from first-party software licensing. No restricted raw or row-level
measurement/prediction tables are copied here.

PHYSICAL_VALIDATION = NOT_ESTABLISHED. NATIVE_EWP_RUNS = 0.
PRODUCTION_DEFAULTS_CHANGED = false. PRODUCTION_DEPENDENCY_LOCK_CHANGED = false.
NO_SUCCESSOR_AUTHORIZED. Both task PRs remain open/unmerged for owner disposition.
