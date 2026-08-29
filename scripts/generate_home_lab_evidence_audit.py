#!/usr/bin/env python3
"""Regenerate the bounded HOME-LAB-EVIDENCE-001 planning package.

This generator contains only aggregate planning conclusions. It never reads raw
Visualizer records and deliberately fails closed when no auditable store is supplied.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "timeframe", "achieved_pressure", "pressure_goal", "scale_mass_flow",
    "machine_native_flow", "flow_goal", "beverage_weight_series", "water_dispensed",
    "basket_temperature", "mix_temperature", "temperature_goal", "state_changes",
    "dose", "final_drink_weight", "duration", "grinder_model", "grinder_setting",
    "machine", "roast_level_or_presence", "profile_presence", "tag_presence",
    "coffee_context", "TDS", "extraction_yield", "sensory_fields",
]


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)

    integrity = {
        "schema_version": 1,
        "audit_id": "HOME-LAB-EVIDENCE-001",
        "corpus_status": "ABSENT",
        "searched_scope": [
            "authoritative Puckworks puckworks/data/visualizer",
            "documented predecessor crawl_v6_20260715 location",
            "workspace stores matching Visualizer shard/index/run conventions",
        ],
        "tracked_aggregate_is_not_local_store": True,
        "stable_production_salt_present": False,
        "reconciliation": {"executed": False, "reason": "NO_LOCAL_STORE"},
        "rebuild_index": {"executed": False, "reason": "NO_SHARDS"},
        "total_records": None,
        "unique_latest_version_shots": None,
        "historical_versions": None,
        "quarantined_records": None,
        "first_source_timestamp": None,
        "last_source_timestamp": None,
        "first_update_timestamp": None,
        "last_update_timestamp": None,
        "interrupted_run_manifests": None,
        "duplicate_records": None,
        "unreadable_shards": None,
        "unit_flags": None,
        "channel_length_mismatches": None,
        "missing_machine_records": None,
        "latest_version_logic": "Puckworks max(updated_at), tie by append sequence; not executable without index/store",
        "privacy_small_cell_rule": "Suppress machine/contributor cells <5; combine into Other/Redacted; never emit identifiers.",
    }
    (out / "VISUALIZER_LOCAL_CORPUS_INTEGRITY.json").write_text(
        json.dumps(integrity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    completeness_rows = []
    for field in FIELDS:
        tier = "USER_OUTCOME" if field in {"TDS", "extraction_yield", "sensory_fields"} else ("HYDRAULIC_OR_THERMAL" if field in FIELDS[:12] else "SCALAR_CONTEXT")
        completeness_rows.append(["ALL", tier, field, "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "none", "local corpus absent"])
    write_csv(out / "VISUALIZER_FIELD_COMPLETENESS.csv",
              ["machine_cohort", "evidence_tier", "field", "count", "completeness_pct", "valid_unit_pct", "plausible_range_pct", "usable_series_pct", "median_sampling_interval_s", "series_length_distribution", "missingness_association", "suitability", "caveat"], completeness_rows)

    cohort_rules = [
        ("complete_hydraulic", "valid time+achieved pressure+beverage weight+scale flow or derivable weight+machine+duration"),
        ("complete_thermal_hydraulic", "complete hydraulic plus valid temperature"),
        ("repeated_contributor_ge_3", "salted contributor with >=3 usable shots"),
        ("repeated_contributor_ge_10", "salted contributor with >=10 usable shots"),
        ("repeated_contributor_ge_30", "salted contributor with >=30 usable shots"),
        ("profile_contrast", "achieved-channel classification: low/conventional/declining/flow-controlled/long-or-short-preinfusion/other"),
        ("manual_or_lever_relevant", "conservative machine/integration metadata only; NO_RELIABLE_MANUAL_LEVER_COHORT_IDENTIFIER when unsupported"),
        ("outcome_annotated", "TDS/EY retained separately from hydraulics"),
    ]
    write_csv(out / "VISUALIZER_COHORT_ATLAS.csv",
              ["cohort", "inclusion_rule", "count", "time_span", "machine_mix", "channel_completeness", "principal_caveat", "permitted_scientific_use"],
              [[n, r, "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "NOT_COMPUTABLE", "local corpus absent", "definition/design only; no empirical claim"] for n, r in cohort_rules])

    marginal = {
        "classification": "LOCAL_CORPUS_ABSENT_HARVEST_REQUIRED",
        "subsampling_executed": False,
        "reason": "No auditable local records; stabilization cannot be estimated from aggregate_stats.csv.",
        "metrics": {k: "NOT_COMPUTABLE" for k in ["shot_duration", "peak_pressure", "peak_scale_flow", "beverage_yield", "achieved_pressure_profile_classes", "pressure_flow_trajectory_clusters"]},
        "incremental_harvest_executed": False,
        "harvest_blocker": "Existing stable production salt is absent; creating a replacement would break contributor continuity.",
        "worthwhile_collection": "Restore/reconcile the documented recent-window store, or run one bounded current-window crawl only with the existing production salt; prioritize new machine/integration coverage.",
        "likely_redundant": "Repeated ordinary current-window crawls after duration/pressure/flow/profile distributions demonstrate deterministic stability.",
    }
    (out / "VISUALIZER_MARGINAL_VALUE.json").write_text(json.dumps(marginal, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    (out / "VISUALIZER_HISTORICAL_ACCESS_BRIEF.md").write_text("""# Visualizer historical-access brief

Status: `REQUEST_NOT_SENT`. The local recent-window corpus is absent, so corpus stabilization and rare machine coverage cannot be assessed.

Request a maintainer-generated, privacy-stripped aggregate or appropriately scoped token for shot ID/version timestamps, machine/integration class, sampled achieved pressure, scale weight/flow, temperature, goals/state changes, duration/dose/yield, coarse profile tags, and outcome-presence flags. Desired span: earliest retained public record through the export cutoff. Filters: machine/integration categories with a coarse manual/lever/Pressensor/Smart Espresso Profiler indicator; no free text, user name, raw contributor ID, location, or private URL. Retain only the existing salted one-way contributor key if the maintainer can apply the production salt; otherwise contributor analyses should be omitted.

Redistribution posture: raw records remain local and uncommitted; publish only aggregates with cells below five suppressed or pooled. A historical export would materially help determine temporal coverage, repeated-shot structure, rare manual/lever relevance, and whether recent-window distributions are stable. It would not create controlled Flair tie-points, analytical groundtruth, PSD, geometry, or paired cup/spent inventory.
""", encoding="utf-8")

    evidence = [
        ["visualizer/hydraulic_timeseries", "visualizer_coffee", "1;14", "community machine telemetry", "heterogeneous", "unknown", "unknown", "pressure/flow/mass/time/temperature context", "time series", "local raw absent", "unlicensed user corpus; aggregates only", "not model-fit", "ecological", "software/design/ecological context", "uncontrolled; no Flair tie-point"],
        ["visualizer/user_outcomes", "visualizer_coffee", "3", "user entry", "heterogeneous", "unknown", "unknown", "TDS/EY/sensory", "shot scalar", "unknown", "unlicensed user corpus; aggregates only", "not model-fit", "hypothesis-level", "ecological context only", "not analytical groundtruth"],
        ["waszkiewicz2025/traces_time_dependent", "waszkiewicz2025", "1;2;12", "instrumented espresso rig", "source rig", "source grinder", "pressure ladder", "basket/line pressure, flow, mass, dissolved mass", "time series", "retained", "CC-BY-4.0", "consumed by RC-3/SCI-MD stages", "within-rig", "design/reconstruction", "pressure nodes and TDS-derived dissolved flow must stay distinct"],
        ["waszkiewicz2025/tds_fractions", "waszkiewicz2025", "3;4", "5-s fraction collection", "source rig", "source grinder", "pressure conditions", "fraction TDS/time", "5-s fractions", "replicates; first sparse", "CC-BY-4.0", "consumed", "within-rig", "fraction design", "not Flair and not fresh validation"],
        ["waszkiewicz2025/mastersizer_psd", "waszkiewicz2025", "10", "Mastersizer", "n/a", "source grinder", "3 replicates", "volume PSD", "binned", "3 replicates", "CC-BY-4.0", "consumed", "independent measurement", "instrument/PSD planning", "not grinder-setting transfer"],
        ["wadsworth2026/table1_full", "wadsworth2026", "10;11;12", "PSD/packed-bed rig", "source apparatus", "source grinder", "multiple grinds", "moments, porosity, permeability", "condition scalar", "k error retained", "CC-BY-4.0", "consumed", "independent measurement", "range/design/reconstruction", "source-specific"],
        ["schmieder2023/raw_fractions", "schmieder2023", "4;5", "espresso fractions+assay", "source machine", "source grinder", "15 experiments x3", "fraction mass, caffeine/trigonelline/TDS", "fractions 1,2,3,5,7,10", "replicates", "CC-BY", "consumed SCI-MD-004/007/008/009", "independent measurement within source", "fraction design/method planning", "not eligible fresh holdout"],
        ["schmieder2023/cup_masses", "schmieder2023", "3;5", "espresso+assay", "source machine", "source grinder", "15 experiments", "whole-cup species/TDS mass", "whole shot", "RSD reported", "CC-BY", "consumed", "same apparatus", "signal sizing", "not Flair"],
        ["pannusch2024/experimental_kinetics", "pannusch2024", "4;5", "espresso fractions+assay", "source machine", "source grinder", "15 x 6 fractions", "species/TDS kinetics", "6 fractions", "run-averaged", "CC-BY-NC-3.0", "consumed", "same lineage as Schmieder", "fraction design", "not independent of Schmieder"],
        ["dias2015/table2", "dias2015", "6", "roasted coffee assay", "n/a", "n/a", "coffee/roast rows", "total caffeine/trigonelline", "bulk", "retained", "CC-BY-4.0", "consumed SCI-MD-007", "within-source", "initial-content prior", "total content != I_ref or M0"],
        ["viencz2023/tables1_2", "viencz2023", "6", "roasted coffee assay", "n/a", "n/a", "canephora rows", "total species", "bulk", "retained", "public normalized facts", "consumed", "shared lab lineage", "initial-content prior", "not extractability"],
        ["acre2024/tables1_2", "acre2024", "6", "roasted coffee assay", "n/a", "n/a", "canephora rows", "total species/moisture context", "bulk", "retained", "open access", "consumed", "shared lineage with Viencz", "prior only", "not independent holdout"],
        ["liang2021/fig3_tds", "liang2021", "3;7", "1-L reference extraction", "batch extraction", "varied grind", "~42 digitized points", "TDS/extraction vs brew ratio", "bulk", "digitized", "open access", "consumed", "post-fit", "reference-extractability proxy", "method-conditioned proxy; not production M0"],
        ["liang2021/fig4_E", "liang2021", "7;9", "equilibrium/oven", "batch extraction", "varied", "source curve", "equilibrium extraction/dry basis", "bulk", "digitized", "open access", "consumed", "within-source", "method and dry-basis planning", "not paired to home shots"],
        ["romancorrochano2017/tamped_kappa", "romancorrochano2017", "10;11;12", "tamped-bed Darcy rig", "source rig", "source grinds", "4 grinds x3 densities", "permeability/density", "condition", "SD", "open thesis; noncommercial research", "consumed", "independent measurement", "range/fixture design", "no Flair pairing"],
        ["foster2025_2/fig12_14_curves", "foster2025_2", "2;13;14", "CT espresso rig", "source rig", "fine grind", "source curves", "front/headspace/deformation", "time series", "data error", "paper", "consumed", "post-fit same campaign", "camera/thermal timing design", "not transferable quantitative deformation"],
        ["egidi2024/table2", "egidi2024", "3;14", "espresso apparatus", "source machine", "source grinder", "12 conditions", "TDS/EY, pressure,temp,time", "bulk shot", "TDS sigma", "paper", "context-consumed", "independent bracket", "signal range", "not response test and not Flair"],
    ]
    write_csv(out / "PUCKWORKS_HOME_LAB_EVIDENCE_MATRIX.csv", ["dataset_id", "source", "lanes", "apparatus", "machine", "grinder", "condition_replicate_scope", "variables", "temporal_fraction_resolution", "uncertainty", "rights", "prior_model_consumption", "independence", "current_permitted_use", "principal_caveat"], evidence)

    eligibility = [[r[0], r[11], "DESIGN_RECONSTRUCTION_OR_CALIBRATION", "NO" if "not model-fit" not in r[11] else "POTENTIALLY_YES_IF_PROSPECTIVELY_RESERVED", r[-1]] for r in evidence]
    write_csv(out / "SOURCE_CONSUMPTION_AND_ELIGIBILITY.csv", ["dataset_id", "consumption_status", "current_role", "eligible_as_fresh_independent_comparison", "reason"], eligibility)

    priors = [
        ["shot duration", "15-60 s ecological/planning envelope", "visualizer/hydraulic_timeseries; egidi2024/table2", "mixed; Visualizer local values unavailable", "unknown/source-reported", "yes", "yes"],
        ["preinfusion duration", "short vs long; establish locally before numeric bounds", "visualizer/hydraulic_timeseries; foster2025_2/fig12_14_curves", "inferred design class", "not quantified", "yes", "yes"],
        ["first-drip time", "order 8 s source offset; qualify locally", "waszkiewicz2025/tds_solids_calibration; foster2025_2/fig12_14_curves", "measured/model-aligned source", "source-specific", "yes", "yes"],
        ["achieved pressure", "0-12 bar sizing; distinguish basket from line", "waszkiewicz2025/traces_time_dependent", "measured", "retained by source", "yes", "yes"],
        ["scale outlet flow", "0-8 g/s conservative logger range; normal espresso mostly lower", "waszkiewicz2025/traces_time_dependent; visualizer/hydraulic_timeseries", "measured/source plus ecological intended", "source retained", "yes", "yes"],
        ["beverage mass", "0-60 g conservative", "waszkiewicz2025/traces_time_dependent; schmieder2023/cup_masses", "measured", "source retained", "yes", "yes"],
        ["fraction mass", "about 3-8 g for six fractions of a 20-48 g beverage", "schmieder2023/raw_fractions; pannusch2024/experimental_kinetics", "inferred planning range", "propagate balance/collector uncertainty", "yes", "yes"],
        ["bulk TDS", "source curves imply percent-scale signal; qualify refractometer across early-to-late dilution", "waszkiewicz2025/tds_fractions; egidi2024/table2", "measured source", "source sigma where available", "yes", "yes"],
        ["caffeine/trigonelline", "mg/g and absolute mg fraction signals; set LOQ from late fractions, not a universal numeric range", "schmieder2023/raw_fractions; cup_masses", "measured source", "replicate/RSD", "yes for service specification", "yes"],
        ["initial total content", "coffee/species-specific mg/g dry basis distributions", "dias2015/table2; viencz2023/tables1_2; acre2024/tables1_2", "measured", "retained", "context only", "yes"],
        ["reference extractability proxy", "~0.20 dry-mass fraction equilibrium context", "liang2021/fig4_E", "digitized measured proxy", "source uncertainty limited", "method planning only", "yes"],
        ["spent-puck inventory", "NO_ACCEPTED_PAIRED_RANGE", "none", "missing", "unknown", "no", "new measurement required"],
        ["coffee moisture", "measure each lot; do not import a universal correction", "liang2021/fig4_E; accepted composition sources", "method context", "source-specific", "yes", "yes"],
        ["PSD descriptors", "volume distribution/moments; no setting conversion", "waszkiewicz2025/mastersizer_psd; wadsworth2026/table1_full", "measured", "replicate/error retained", "yes", "yes"],
        ["porosity", "source packed-bed values only; measure grinder/dose/prep-specific value later", "wadsworth2026/table1_full", "measured", "source error", "fixture sizing", "yes"],
        ["permeability", "roughly 1e-17 to 1e-12 m2 conservative multi-source apparatus envelope", "wadsworth2026/table1_full; romancorrochano2017/tamped_kappa", "measured heterogeneous methods", "source error/SD", "fixture sizing", "yes"],
    ]
    write_csv(out / "SIGNAL_AND_RANGE_PRIORS.csv", ["observable", "planning_range", "source_ids", "measured_or_inferred", "uncertainty", "equipment_sizing", "flair_extrapolation_required"], priors)

    fractions = [
        ["six_equal_beverage_mass", "~3-8 g", "variable; record switches", "resolves early decline with uniform mass support", "six-point species mass curve", "late low concentration", "high", "moderate; source six-point structure retained", "moderate", "whole-shot endpoint plus summed fractions", "RECOMMENDED: PROVISIONAL_PRE-PILOT_DESIGN; NOT_OPTIMIZED_MINIMUM; SUBJECT_TO_HOME_COLLECTION_AND_ANALYTICAL_FEASIBILITY"],
        ["six_equal_time", "highly unequal", "equal", "early fractions can be tiny before/near first drip", "risk of censored early/late mass", "high", "low", "moderate", "moderate", "requires exact mass per cup", "FALLBACK only if switching by mass fails"],
        ["early_dense_mass", "smaller early, larger late", "variable", "best early TDS detail", "best early species detail", "late pooled improves LOQ", "high", "high", "high", "explicit boundaries and whole-shot endpoint", "FALLBACK: PROVISIONAL_PRE-PILOT_DESIGN; NOT_OPTIMIZED_MINIMUM; SUBJECT_TO_HOME_COLLECTION_AND_ANALYTICAL_FEASIBILITY"],
        ["eight_mass", "~2.5-6 g", "variable", "more detail", "more detail if LOQ permits", "higher", "high", "high", "high", "more balance terms", "defer until six-fraction feasibility"],
        ["ten_source_like", "source-defined/irregular", "source-like", "closest to Schmieder sampling", "highest source-curve fidelity", "highest censoring risk", "very high", "highest", "very high", "most balance terms", "not justified for first home pilot"],
    ]
    write_csv(out / "FRACTION_DESIGN_COMPARISON.csv", ["scheme", "fraction_sample_mass", "fraction_duration", "expected_tds_progression", "expected_species_mass_progression", "late_fraction_difficulty", "information_retained", "source_curve_fidelity", "flair_switching_burden", "mass_closure", "disposition"], fractions)

    cross = [
        ["Flair pressure/flow/mass characterization", "synchronized pressure, scale mass/time", "source rig + ecological telemetry", "yes", "mostly consumed/context", "no", "Flair synchronized trace", "existing scale+video first; pressure only if failed", "existing gear then transducer", "yes"],
        ["first drip", "time-stamped visible first beverage", "source timing", "yes", "consumed", "no", "Flair first drip", "phone video synchronized to scale", "none initially", "yes"],
        ["fraction bulk extraction", "fraction mass+TDS", "source fractions", "yes", "consumed", "no", "Flair paired fractions", "six mass fractions", "manual collector+qualified refractometer", "yes"],
        ["dry-basis extraction yield", "dose moisture+cup dissolved mass", "bulk source EY", "yes", "consumed", "no", "home dry basis", "moisture plus TDS", "qualified drying workflow", "yes"],
        ["initial moisture", "lot moisture", "method context only", "yes", "n/a", "no", "same lot", "replicate drying", "oven/desiccator or external service", "yes"],
        ["initial I_ref", "sequential reference extractability", "proxy only", "yes", "consumed", "no", "method-conditioned paired initial value", "external method development", "external service first", "yes"],
        ["spent-puck I_ref", "recovered spent-puck sequential extractability", "none", "n/a", "no", "no", "paired spent value and tail", "external paired assay", "external service first", "yes"],
        ["fraction caffeine/trigonelline mass", "concentration x sample mass", "source species fractions", "yes", "consumed", "no", "home Flair fractions", "external chromatography batch", "HPLC service", "yes"],
        ["cup-spent mass balance", "initial I_ref, all fractions, spent I_ref, losses", "no complete paired source", "yes", "no", "no", "complete paired chain", "one external reference batch", "service+prep equipment", "yes"],
        ["grinder-specific PSD", "PSD moments/distribution", "other grinders", "yes", "consumed", "no", "home grinder/prep PSD", "external imaging first", "imaging service/equipment later", "yes"],
        ["grinder-specific permeability", "pressure-flow across known geometry", "other rigs", "yes", "consumed", "no", "home prepared-bed tie point", "later fixture test", "permeability fixture", "yes"],
        ["puck deformation", "time-resolved puck/headspace geometry", "CT source", "yes", "consumed", "no", "Flair-visible or displacement tie point", "camera feasibility", "camera then sensor only if needed", "yes"],
    ]
    write_csv(out / "MINIMUM_NEW_MEASUREMENT_CROSSWALK.csv", ["decision", "required_observable", "existing_source_coverage", "apparatus_specific", "already_consumed", "suitably_paired", "remaining_missing", "least_expensive_new_measurement", "equipment_or_service", "reusable"], cross)

    gates = [
        ["compact logging scale", "USE_EXISTING_EQUIPMENT_FIRST", "synchronized beverage mass/time", "source telemetry sets range only", "no", "existing scale fails rate/export/synchronization qualification", ">=0.1 g resolution; monotonic timestamps; adequate rate for flow derivation", "static mass, timing, drift, video sync", "high"],
        ["camera and mount", "USE_EXISTING_EQUIPMENT_FIRST", "first drip/switch/deformation timing", "source video/CT guides targets", "partial", "phone view or synchronization inadequate", "stable view; readable clock/scale; no dropped critical events", "timing and repeatability", "high"],
        ["temperature logger/probes", "BUY_ONLY_IF_EXISTING_EQUIPMENT_FAILS_QUALIFICATION", "basket/water temperature history", "source thermal ranges", "limited", "thermometer cannot resolve chosen thermal decision", "documented response, accuracy and safe placement", "ice/boiling/reference comparison and response", "high"],
        ["pressure transducer", "LIKELY_FIRST_PURCHASE", "Flair pressure-node trace", "other-rig traces not transferable", "no", "existing Flair gauge/video cannot yield synchronized quantitative trace", "correct node; 0-12 bar range; calibration; adequate sample rate", "zero/span/leak/sync/repeatability", "high"],
        ["inline flowmeter", "NOT_CURRENTLY_JUSTIFIED", "inlet volumetric flow", "scale mass flow usually sufficient", "partial", "mass-derived outlet flow cannot answer a frozen decision", "fluid/temperature compatible; calibrated dynamic range", "gravimetric calibration and pressure-drop test", "medium"],
        ["manual fraction collector", "REQUIRED_FOR_PAIRED_FEASIBILITY_PILOT", "mass-defined fractions", "source fractions define design", "no", "B1 begins", "repeatable low-loss switching for ~3-8 g fractions", "recovery, contamination, switch timing, summed mass", "high"],
        ["refractometer", "LIKELY_FIRST_PURCHASE", "fraction/bulk TDS", "existing TDS evidence sizes signal", "method-transfer required", "borrowed/existing device fails precision/range qualification and B1 is current", "espresso-compatible range; repeatability sufficient for late fractions", "water zero, standards, replicate, temp, mass closure", "high"],
        ["0.1 mg analytical balance", "METHOD_DEPENDENT_DEFER", "small-mass preparation/standards", "source methods guide loads", "no", "selected preparation uncertainty budget requires it", "0.1 mg readability with qualified repeatability/linearity", "weights, drift, eccentricity", "high"],
        ["drying oven", "METHOD_DEPENDENT_DEFER", "moisture/dry basis", "methods exist but lot-specific value missing", "no", "B2 method chosen and external option rejected", "stable method temperature and safe capacity", "uniformity, repeat drying to mass criterion", "high"],
        ["desiccator", "METHOD_DEPENDENT_DEFER", "controlled cool/weigh", "method evidence", "transferable", "gravimetric drying selected", "sealed low-humidity capacity", "blank and repeat mass stability", "high"],
        ["quantitative pipettes", "METHOD_DEPENDENT_DEFER", "dilution/extract volumes", "source methods", "partial", "analytical method and volumes fixed", "volume range/accuracy matched to uncertainty", "gravimetric qualification", "high"],
        ["volumetric glassware", "METHOD_DEPENDENT_DEFER", "extract/dilution volumes", "source methods", "partial", "workflow volumes fixed", "class/accuracy matched to budget", "gravimetric verification", "high"],
        ["heated ultrasonic bath", "METHOD_DEPENDENT_DEFER", "controlled extraction agitation", "reference extraction remains unresolved", "no", "selected I_ref method requires sonication", "temperature/time uniformity", "mapping and recovery", "medium"],
        ["centrifuge", "METHOD_DEPENDENT_DEFER", "clarification", "source prep methods only", "partial", "demonstrated workflow requires centrifugal clarification", "RCF/tube compatibility", "recovery/clarity/carryover", "medium"],
        ["filtration equipment", "METHOD_DEPENDENT_DEFER", "clarified aliquot", "methods guide choices", "partial", "filter study selects material/pore size", "low adsorption and adequate recovery", "blank/spike/recovery", "high"],
        ["cold storage", "METHOD_DEPENDENT_DEFER", "sample stability", "no transferable stability proof", "no", "holding-time study/service logistics require it", "temperature monitoring/capacity", "stability blanks and excursions", "high"],
        ["particle-imaging equipment", "LATER_GRINDER_HYDRAULIC_STAGE", "grinder-specific PSD", "other-grinder PSD only", "no", "Priority 3 campaign frozen; service inadequate", "resolved size range and validated segmentation", "reference particles/repeatability", "high"],
        ["sieves", "LATER_GRINDER_HYDRAULIC_STAGE", "coarse mass-size distribution", "PSD sources reduce exploratory need", "partial", "sieve descriptor is decision-relevant", "appropriate stack and recoverable mass", "mass recovery/repeatability", "medium"],
        ["permeability fixture", "LATER_GRINDER_HYDRAULIC_STAGE", "prepared-bed k-pressure-flow", "source rigs not transferable", "no", "grinder-specific hydraulic stage begins", "known geometry; low leak/compliance; pressure-flow range", "blank resistance/leak/calibration/repeats", "high"],
        ["UV-Vis", "NOT_CURRENTLY_JUSTIFIED", "method-dependent absorbance", "species selectivity unresolved", "no", "external reference establishes a validated useful method", "method-specific", "linearity/specificity/recovery", "medium"],
        ["HPLC", "EXTERNAL_SERVICE_FIRST", "reference caffeine/trigonelline", "accepted source chemistry sizes method", "not transferable operationally", "sustained validated throughput exceeds service rationale", "species separation, LOQ for late fractions, traceable calibration", "linearity/precision/recovery/LOQ/carryover", "high"],
    ]
    write_csv(out / "EQUIPMENT_PURCHASE_GATES.csv", ["item", "status", "unique_new_observable", "existing_evidence_reducing_need", "evidence_transferable", "purchase_trigger", "minimum_performance", "qualification_tests", "later_reuse"], gates)

    result = {
        "audit_id": "HOME-LAB-EVIDENCE-001", "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE", "claim_ceiling": "PHYSICAL_VALIDATION_NOT_ESTABLISHED",
        "overall_disposition": "EXISTING_DATA_SUFFICIENT_FOR_DESIGN_NOT_VALIDATION",
        "visualizer": {"corpus_status": "ABSENT", "marginal_value": "LOCAL_CORPUS_ABSENT_HARVEST_REQUIRED", "historical_access_materially_helpful": True},
        "measurement_lane_classification": {
            "operating_and_instrument_ranges": "EXISTING_DATA_SUFFICIENT_FOR_CURRENT_DECISION",
            "fraction_scheme_and_signal_planning": "EXISTING_DATA_SUFFICIENT_FOR_DESIGN_NOT_VALIDATION",
            "visualizer_population_context": "EXISTING_DATA_PARTIAL_TARGETED_EXPANSION_WORTHWHILE",
            "flair_hydraulics_and_first_drip": "NEW_FLAIR_SPECIFIC_TIE_POINT_REQUIRED",
            "initial_and_spent_reference_extractability_mass_balance": "NEW_PAIRED_HOME_MEASUREMENT_REQUIRED",
            "fraction_caffeine_trigonelline": "EXTERNAL_ANALYTICAL_SERVICE_REQUIRED",
            "uv_vis_hplc_inline_flow_and_advanced_prep": "EQUIPMENT_PURCHASE_NOT_YET_JUSTIFIED"
        },
        "minimum_first_purchase": "NONE before zero/low-cost Flair qualification; if gauge/video fails, pressure transducer is likely first; for B1, a qualified refractometer and manual collector are required.",
        "provisional_fraction_scheme": "six equal beverage-mass fractions",
        "fallback_fraction_scheme": "early-dense mass fractions",
        "validation_result_issued": False,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
