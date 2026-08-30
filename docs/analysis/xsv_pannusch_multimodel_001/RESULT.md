# XSV-PANNUSCH-MULTIMODEL-001 result

## Disposition

`XSV_PANNUSCH_MULTIMODEL_001_MECHANISTIC_STRUCTURE_HAS_GROUPED_PREDICTIVE_ADVANTAGE`

On the frozen C01/C02/C05/C06 March common subset, fixed published Pannusch
fraction-share RMSE was 0.0113722 versus 0.0242212 for the analyte-pooled
baseline: 53.05% lower. The paired condition-bootstrap 95% interval for
model-minus-baseline error was [-0.0228653, -0.00538683], no primary condition
was worse, fixed-source calibration-condition error was 0.00885328, and the
result did not reverse at 0.01x, 0.1x, or 1.0x fitted-c_s0 sensitivity scales.

The implementation reproduced the accepted valid-only/source-grind Puckworks
parity metric exactly (6.37229818164% pooled MAPE). MATLAB and the Puckworks
port are one model, not separate competitors. Published parameters were not
refit or adopted into EWP production.

## Other models

Compositional ridge and partial pooling each improved March RMSE by only 0.67%;
their paired intervals crossed zero and two of four conditions were worse.
One-timescale extraction was robustly disfavored (0.0552074; all four
conditions worse). Two-timescale extraction was also worse on average
(0.0282356) and indistinguishable within its wide interval. Nearest-condition
prediction was worse in every condition. A universal species shape was worse
than analyte-pooled shape.

`MODEL-EWP-FIXED` was specifically blocked: the source grind setting has no
qualified, non-target-derived mapping to the current EWP permeability/geometry
inputs. Inventing that bridge would violate equal privilege. C03/C04 remain
blocked by current time-dependent-temperature physics. This did not block the
core comparison.

## Secondary findings

- `SPECIES_SIGNAL_NOT_SUPPORTED`: partial pooling gained only 0.67%, with an
  interval crossing zero; no species successor is justified.
- `INVENTORY_ROBUST_RANKING`: Pannusch RMSE was 0.0113730, 0.0113723, and
  0.0113722 across the declared scales.
- `FLOW_HISTORY_SIGNAL_UNRESOLVED`: C07/C08 showed opposite early-share
  residual directions, but no frozen history-aware advantage was established.
- `TEMPERATURE_HISTORY_SIGNAL_UNRESOLVED`: C03/C04 residual direction differed,
  but two conditions and programmed machine temperature do not establish a
  repeatable thermal closure.
- `GRIND_RESIDUAL_SIGNAL_NOT_SUPPORTED`: fixed-Pannusch fit error was
  non-monotonic across 1.4/1.7/2.0, and grind-held-out models did not establish
  a stable >=10% improvement from additional complexity.
- `TELEMETRY_ADAPTER_VALUE_SUPPORTED`: the winning model systematically
  overpredicted fraction 2 (+0.01669 share) and underpredicted fractions 5/6
  (-0.00946/-0.01001). The existing 24-shot beverage-mass/fraction-boundary
  joins can test an observer explanation without changing extraction physics.

## Next task and ceiling

Strongest successor: `OBS-PANNUSCH-TELEMETRY-001`, limited to whether corrected
beverage-mass/fraction timing removes the early/tail residual structure. First
fallback: `SCI-MD-PANNUSCH-GRIND-001`. Second fallback:
`SCI-MD-PANNUSCH-FLOW-HISTORY-001`.

Maximum claim: source-internal, target-exposed grouped evidence for Pannusch
fraction-mass-share prediction under the frozen privileges. This is not
target-blind or independent validation, mass closure, hydraulic/thermal
validation, or production parameter authority.
