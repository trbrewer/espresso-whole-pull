# SCI-MD-010 Phase B result

## Disposition and authority

`NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`.

This is the single authorized execution of reviewed R4 freeze commit
`9b1c7ed2505ac5a95768cdd188682e7a6ee6ee77`, tree
`1ef01bd26ee2a45ec509ee8c6afa99eaa009c4a5`, from EWP base
`f8bd4cc5c4c05869ceda75e273784781b8429c28`, tree
`9d9a8ae2434b35c405e47e2d164084677aa13b48`. The freeze-manifest file
SHA-256 is `cdac6800b8976290621b1f0e75b484c7b062833d4ebe03fefee51a8789dbf030`;
its aggregate frozen-content SHA-256 is
`cc04d349140a42072d9260321569cb363eb796ce782db0ad3903c284f5e8edf0`.
The read-only analysis Puckworks authority is commit
`2058d0e947ee9eb92c52d64f6165b810f1fb4732`, tree
`a6ffb312473b15be43c1571a893b19873ea47c5a`. The accepted review is
[PR comment 5519736636](https://github.com/trbrewer/espresso-whole-pull/pull/140#issuecomment-5519736636);
the review-receipt SHA-256 is
`cd56ea04316f122a70f4227af85b158732c32f969f45f09d346c5cc87c2acf60`.

## Frozen comparison

The evaluation retains 56 canonical physical brews in 11
leave-one-pressure-condition-out folds. Pressure is directly measured line
pressure and the response is `endpoint_100s` equilibrium mass flow.

- B0 (`HYD_B0_TRAINING_MEAN`): condition-balanced training mean.
- B1 (`HYD_B1_PRESSURE_QUADRATIC`): fixed quadratic empirical form in line
  pressure, fit only on each outer training fold.
- E1 (`HYD_E1_LUMPED_DARCY`): machine-coupled reduced steady Darcy form with
  one nonnegative effective conductance fit only on each outer training fold.

All 33 model/fold fits and predictions passed, with zero failed roots. The 168
brew prediction rows retain every evaluation brew for all three models.

## Losses and uncertainty

| Model | Aggregate normalized loss | Mean physical RMSE (g/s) | Fold RMSE range (g/s) | Normalized fold-loss range |
|---|---:|---:|---:|---:|
| B0 | 0.31786798610901296 | 0.5916020492750618 | 0.14271942301589208–1.5036816216390032 | 0.07395068467143684–0.90246030817923 |
| B1 | 0.1532500174983135 | 0.29362695566852126 | 0.11558352138601755–0.7271585992029245 | 0.05989010018825456–0.37678036485469374 |
| E1 | 0.29894242558587686 | 0.5756564539493186 | 0.061746973096364274–1.491651890624376 | 0.03199446046216478–0.7729058615296726 |

The full-domain normalized B1-minus-E1 point delta is
`-0.14569240808756337`, with paired 95% interval
`[-0.2487589900770766, -0.036163174040446486]`. The low-pressure point
delta is `-0.11232543181874685`, with interval
`[-0.2669334833198054, 0.029735204181095785]`. Negative values favor B1.
The frozen materiality label is `PREDICTIVE_RANKING_ONLY`. The paired
condition/brew bootstrap used 2,000 replicates, seed 20260902, and no refit.

Condition-level B1-minus-E1 deltas are: 1.0 bar +0.04502816985693528; 2.0 bar
+0.0916460308168119; 3.5 bar -0.09464035642483527; 4.0 bar
-0.2824855359901189; 5.0 bar -0.32117546735252733; 6.0 bar
-0.3316041110881307; 7.0 bar -0.20480816405017596; 8.0 bar
+0.052625494441993784; 9.0 bar +0.08315765270469977; 11.0 bar
-0.24423470520287058; and 13.0 bar -0.3961254966749788. Thus B1 wins seven
conditions and E1 wins four.

## Pressure-response diagnostics

Observed low- and high-pressure slopes are respectively
`0.5042068394004887` and `-0.06550641262782862` g/s/bar.

| Model | Predicted low slope | Low gate | Predicted high slope | High gate | Predicted peak | Spearman | Ordering concordance |
|---|---:|---|---:|---|---|---:|---:|
| B0 | -0.05042068394004887 | fail | 0.006550641262782813 | fail | 1.0 bar | -1.0 | 0.0 |
| B1 | 0.3491836916872465 | pass | -0.3400461981768364 | pass | 8.0 bar | 0.7363636363636363 | 0.7818181818181819 |
| E1 | 0.20374327855116542 | pass | 0.32853439107949434 | fail | 13.0 bar | 0.44545454545454544 | 0.6363636363636364 |

The observed peak is 6.0 bar. Every diagnostic uses directly measured line
pressure; no basket-pressure field enters the result.

## Architecture and experiment consequence

The exact reduced-E1 architecture decision is
`NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`. E1 conductance is interior in
all folds and ranges from 0.20726176030430005 to 0.25349768592319233 g/s/bar,
but one effective conductance does not identify full EWP quantities. Reduced
Darcy did not establish stable advantage over quadratic B1; B1 is better on
the frozen full-domain predictive ranking, while E1's low-pressure utility is
not established because that paired interval crosses zero. Simplification or
reparameterization should precede hydraulic-specific new data.

The exact experiment recommendation is
`SIMPLIFY_BEFORE_HYDRAULIC_SPECIFIC_EXPERIMENT_M01_NOT_ADJUDICATED`.
M01 absolute chemistry is not adjudicated by L-HYD. SCI-ED-003 remains
complete; Stage F and Stage D remain unauthorized. No automatic successor is
selected.

## Claim boundary and programme interpretation

The strongest claim is
`RETROSPECTIVE_SOURCE_CONDITIONED_CONDITIONAL_HYDRAULIC_COMPONENT_UTILITY_ONLY`.
The broad evidence register remains the Phase A evidence-utility assessment;
only L-HYD received a new adjudicative model-utility score. L-FRAC remains
prior-result context, Wadsworth and Vaca remain constraint/operator evidence,
and aggregate-source exclusions are unchanged. No source data are declared
useless.

This result directly adjudicates only reduced equilibrium hydraulics. Current
full EWP E2 is `NOT_ADJUDICATED`; grinder-to-cup Level-4 prediction and
end-to-end validation remain unestablished. The unresolved grinder-to-cup path
still lacks qualified grinder-PSD-to-wet-permeability and absolute
inventory/chemistry observation bridges. It does not establish universal
conductance, wet-permeability identification, machine transfer, transient
hydraulics, chemistry utility, absolute-inventory closure, independent
validation, or physical validation. `PHYSICAL_VALIDATION` remains
`NOT_ESTABLISHED`.
