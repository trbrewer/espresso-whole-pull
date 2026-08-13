#!/usr/bin/env python3
"""XSV-XCT-001 processed-source reproduction and real-geometry utilities."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

try:
    import numpy as np
except ModuleNotFoundError:  # Optional scientific dependency, absent in base CI.
    np = None

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "verification/cases/xsv_xct_001"
ENS = ROOT / "verification/cases/xsv_ens_001"
SOURCE_SHA256 = "3b0139fe02108d3dfcd1441d9e4062e86d9b7e1a8505141a7beefd9366ebf20f"
TARGETS = (0.373506, 0.389226, 0.395294)


def require_numpy():
    if np is None:
        raise RuntimeError("XSV-XCT-001 numerical commands require NumPy")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def finite(value):
    return value not in (None, "") and math.isfinite(float(value))


def import_processed(source: Path):
    if sha256(source) != SOURCE_SHA256:
        raise ValueError("Wadsworth processed source hash mismatch")
    rows = read_csv(source)
    if len(rows) != 22:
        raise ValueError("expected exactly 22 Wadsworth Table-1 rows")
    identities = [(row["coffee"], int(row["G"])) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate source sample identity")
    output = []
    for row in rows:
        coffee = row["coffee"]
        voxel_m = 2.99e-6 if coffee == "Guayacan" else 2.69e-6
        converted = dict(row)
        converted.update({
            "source_id": "WADSWORTH_2026_RS0S_252031",
            "sample_id": f"{coffee.upper()}-G{int(row['G']):02d}",
            "coffee_normalized": coffee,
            "grind_setting_normalized": int(row["G"]),
            "voxel_size_m": voxel_m,
            "sample_class": "REAL_PACKED_GROUND_COFFEE_XCT",
            "preparation_class": "LOOSE_STRAW_PACK_NOT_CONTROLLED_TAMPED_PUCK",
            "permeability_evidence_role": "PUBLISHED_NUMERICAL_PERMEABILITY_REFERENCE",
        })
        output.append(converted)
    fields = list(rows[0]) + [key for key in output[0] if key not in rows[0]]
    write_csv(CASE / "XSV_XCT_001_PROCESSED_SOURCE_DATA.csv", output, fields)
    matrix=[]
    for row in output:
        scoreable=all(finite(row[key]) for key in ("phi_p_connected","s_p_connected_per_m","k_m2"))
        matrix.append({"sample_id":row["sample_id"],"source_id":row["source_id"],
          "coffee":row["coffee"],"grind_setting":row["G"],"route":"PROCESSED_DATA",
          "primary_transfer_included":str(scoreable).lower(),
          "exclusion_reason":"" if scoreable else "MISSING_SOURCE_HYDRAULIC_FIELDS",
          "related_group":row["coffee"],"raw_volume_available":"false","gpu_execution":"NOT_APPLICABLE"})
    write_csv(CASE/"XSV_XCT_001_SCORED_MATRIX.csv",matrix)
    (CASE/"XSV_XCT_001_SCORED_MATRIX.json").write_text(json.dumps({
      "schema_version":"espresso.whole_pull.xsv_xct_001.scored_matrix.v1",
      "selection_rule":"ALL_22_PRIMARY_SOURCE_ROWS_RETAINED",
      "rows":matrix},indent=2)+"\n")
    return output


def kozeny_carman(phi, surface, W=5.0):
    return phi**3 / (W * surface**2)


def percolation(phi, surface, exponent=4.4):
    return 2.0 * (1.0 - phi) * phi**exponent / surface**2


def angular_surface(radius_m, phi, alpha_per_m=4808.0):
    return 3.0 * (1.0 - phi) * math.exp(alpha_per_m * radius_m) / radius_m


def directional_mean(values):
    values = np.asarray(values, dtype=float)
    if values.shape != (3,):
        raise ValueError("directional averaging requires exactly x, y, z")
    return float(values.mean())


def source_reproduction(rows):
    out = []
    for row in rows:
        if not all(finite(row[key]) for key in
                   ("phi_p_connected", "s_p_connected_per_m", "k_m2", "R_mean_m")):
            out.append({"sample_id":row["sample_id"], "coffee":row["coffee"],
                        "G":row["G"], "status":"MISSING_SOURCE_HYDRAULIC_FIELDS"})
            continue
        phi, surface, observed, radius = (float(row[key]) for key in
            ("phi_p_connected", "s_p_connected_per_m", "k_m2", "R_mean_m"))
        kc = kozeny_carman(phi, surface)
        perc = percolation(phi, surface)
        model_surface = angular_surface(radius, phi)
        perc_angular = percolation(phi, model_surface)
        out.append({
            "sample_id":row["sample_id"], "coffee":row["coffee"], "G":row["G"],
            "status":"PASS", "published_k_m2":observed,
            "published_k_uncertainty_m2":float(row["k_err_m2"]),
            "kozeny_carman_k_m2":kc, "percolation_measured_surface_k_m2":perc,
            "angular_surface_recalculated_per_m":model_surface,
            "published_connected_surface_per_m":surface,
            "percolation_angular_surface_k_m2":perc_angular,
            "kc_log_error":math.log(kc/observed),
            "percolation_log_error":math.log(perc/observed),
            "percolation_angular_log_error":math.log(perc_angular/observed),
        })
    fields = ["sample_id","coffee","G","status","published_k_m2",
              "published_k_uncertainty_m2","kozeny_carman_k_m2",
              "percolation_measured_surface_k_m2","angular_surface_recalculated_per_m",
              "published_connected_surface_per_m","percolation_angular_surface_k_m2",
              "kc_log_error","percolation_log_error","percolation_angular_log_error"]
    write_csv(CASE / "XSV_XCT_001_SOURCE_REPRODUCTION.csv", out, fields)
    return out


def ridge_fit_predict(train_x, train_y, test_x, alpha=1.0):
    require_numpy()
    mean = train_x.mean(axis=0); scale = train_x.std(axis=0)
    scale[scale == 0] = 1.0
    x = (train_x - mean) / scale
    xt = (test_x - mean) / scale
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(design.shape[1]); penalty[0, 0] = 0.0
    beta = np.linalg.solve(design.T @ design + alpha * penalty, design.T @ train_y)
    return np.column_stack([np.ones(len(xt)), xt]) @ beta, beta, mean, scale


def grouped_predictions(x, y, groups, alpha=1.0):
    pred = np.empty(len(y))
    unique = sorted(set(groups))
    for fold in range(5):
        held = {g for i, g in enumerate(unique) if i % 5 == fold}
        test = np.array([g in held for g in groups])
        pred[test], *_ = ridge_fit_predict(x[~test], y[~test], x[test], alpha)
    return pred


def assess_transfer_arm(name, label, feature_names, sx, rx, sy, ry, groups, real):
    oof = grouped_predictions(sx, sy, groups)
    residual_sd = float(np.std(sy-oof, ddof=1))
    pred, beta, mean, scale = ridge_fit_predict(sx, sy, rx)
    lower, upper = pred - 1.96*residual_sd, pred + 1.96*residual_sd
    inside_by_feature = (rx >= sx.min(axis=0)) & (rx <= sx.max(axis=0))
    inside = np.all(inside_by_feature, axis=1)
    nearest = np.min(np.sqrt(np.sum(((rx[:,None,:]-mean)/scale-
                                     (sx[None,:,:]-mean)/scale)**2, axis=2)), axis=1)
    errors=pred-ry
    baseline=float(ry.mean())
    baseline_sse=float(np.sum((ry-baseline)**2))
    r2=float(1.0-np.sum(errors**2)/baseline_sse)
    by_coffee={}
    for coffee in sorted({r["coffee"] for r in real}):
        idx=np.array([r["coffee"]==coffee for r in real])
        by_coffee[coffee]={"n":int(idx.sum()),"rmse_logK":float(np.sqrt(np.mean(errors[idx]**2))),
          "median_multiplicative_error":float(np.median(np.exp(np.abs(errors[idx])))),
          "mean_signed_log_bias":float(np.mean(errors[idx]))}
    grind_rank=[]
    for grind in sorted({int(r["G"]) for r in real}):
        indices=[i for i,r in enumerate(real) if int(r["G"])==grind]
        grind_rank.append({"grind_rank":grind,"n":len(indices),
          "aggregate_metrics":"NOT_ESTIMABLE_N_LT_3" if len(indices)<3 else "ESTIMABLE",
          "rows":[{"sample_id":real[i]["sample_id"],"log_residual":float(errors[i]),
                   "multiplicative_error":float(math.exp(abs(errors[i])))} for i in indices]})
    ranges={"synthetic":{},"real":{}}
    for i,feature in enumerate(feature_names):
        ranges["synthetic"][feature]=[float(sx[:,i].min()),float(sx[:,i].max())]
        ranges["real"][feature]=[float(rx[:,i].min()),float(rx[:,i].max())]
    return {"arm":name,"label":label,"mode":"SYNTHETIC_TRAIN_REAL_TEST",
      "features":feature_names,"rmse_logK":float(np.sqrt(np.mean(errors**2))),
      "median_multiplicative_error":float(np.median(np.exp(np.abs(errors)))),
      "mean_signed_log_bias":float(np.mean(errors)),
      "empirical_95_interval_coverage":float(np.mean((ry>=lower)&(ry<=upper))),
      "r2_logK":r2,"r2_baseline":"MEAN_OBSERVED_LOG_K_FULL_REAL_EVALUATION_POPULATION",
      "r2_baseline_logK":baseline,"real_inside_synthetic_feature_box":int(inside.sum()),
      "real_outside_synthetic_feature_box":int((~inside).sum()),
      "per_feature_inside_counts":{feature:int(inside_by_feature[:,i].sum()) for i,feature in enumerate(feature_names)},
      "standardized_nearest_synthetic_distance":{"minimum":float(nearest.min()),
        "median":float(np.median(nearest)),"maximum":float(nearest.max())},
      "feature_ranges":ranges,"by_coffee":by_coffee,"grind_rank_reporting":grind_rank,
      "grind_rank_aggregate_limitation":"MOST_RANKS_HAVE_ONE_OR_TWO_OBSERVATIONS; AGGREGATE_RANK_METRICS_NOT_ESTIMABLE",
      "synthetic_grouped_oof_residual_sd_logK":residual_sd,
      "ridge_coefficients_standardized_with_intercept":[float(v) for v in beta],
      "prediction":pred,"lower":lower,"upper":upper,"inside":inside,"nearest":nearest,
      "errors":errors}


def transfer(rows):
    synthetic = [r for r in read_csv(ENS / "XSV_ENS_001_PLOT_SOURCE.csv")
                 if r["direction"] == "X" and r["status"] == "PASS"]
    by_hash = {}
    for row in synthetic: by_hash.setdefault(row["geometry_sha256"], row)
    synthetic = list(by_hash.values())
    real = [r for r in rows if all(finite(r[key]) for key in
            ("phi_p_connected","s_p_connected_per_m","R_mean_m","k_m2"))]
    voxel = np.array([float(r["voxel_um"]) * 1e-6 for r in synthetic])
    sx2 = np.column_stack([
        [float(r["phi_connected_x"]) for r in synthetic],
        [float(r["specific_interfacial_area_lu"]) / v for r, v in zip(synthetic, voxel)],
    ])
    rx2 = np.column_stack([[float(r["phi_p_connected"]) for r in real],
                          [float(r["s_p_connected_per_m"]) for r in real]])
    sx3=np.column_stack([sx2,[float(r["pore_distance_q50"])*v for r,v in zip(synthetic,voxel)]])
    rx3=np.column_stack([rx2,[float(r["R_mean_m"]) for r in real]])
    sy = np.log(np.array([float(r["K_gross_lu2"]) * v*v
                          for r, v in zip(synthetic, voxel)]))
    ry = np.log(np.array([float(r["k_m2"]) for r in real]))
    groups = np.array([r["physical_lineage_id"] for r in synthetic])
    arm2=assess_transfer_arm("TWO_FEATURE_SHARED_PROXY","SPECIFIC_SURFACE_PROXY_MAPPING_NON_IDENTICAL_DEFINITIONS",
      ["connected_porosity","specific_surface_proxy_per_m"],sx2,rx2,sy,ry,groups,real)
    arm3=assess_transfer_arm("THREE_FEATURE_SCALE_PROXY_SENSITIVITY","SCALE_PROXY_MISMATCH",
      ["connected_porosity","specific_surface_proxy_per_m","non_equivalent_scale_proxy_m"],sx3,rx3,sy,ry,groups,real)
    prediction_rows=[]
    for i,(row,obs) in enumerate(zip(real,ry)):
        prediction_rows.append({"sample_id":row["sample_id"],"coffee":row["coffee"],
          "G":row["G"],"published_k_m2":math.exp(obs),
          "two_feature_prediction_k_m2":math.exp(arm2["prediction"][i]),
          "two_feature_log_residual":arm2["errors"][i],
          "two_feature_multiplicative_error":math.exp(abs(arm2["errors"][i])),
          "two_feature_covered_95":arm2["lower"][i]<=obs<=arm2["upper"][i],
          "two_feature_inside_box":bool(arm2["inside"][i]),
          "two_feature_nearest_distance":arm2["nearest"][i],
          "three_feature_prediction_k_m2":math.exp(arm3["prediction"][i]),
          "three_feature_log_residual":arm3["errors"][i],
          "three_feature_multiplicative_error":math.exp(abs(arm3["errors"][i])),
          "three_feature_covered_95":arm3["lower"][i]<=obs<=arm3["upper"][i],
          "three_feature_inside_box":bool(arm3["inside"][i]),
          "three_feature_nearest_distance":arm3["nearest"][i],
          "scale_proxy_label":"SCALE_PROXY_MISMATCH"})
    write_csv(CASE / "XSV_XCT_001_PLOT_SOURCE.csv", prediction_rows)
    for arm in (arm2,arm3):
        for key in ("prediction","lower","upper","inside","nearest","errors"): arm.pop(key)
    real_models=real_only_reference_models(real)
    result={"schema_version":"espresso.whole_pull.xsv_xct_001.transfer.v2",
      "mode":"SYNTHETIC_TRAIN_REAL_TEST","real_data_refitting":False,
      "synthetic_unique_masks":len(synthetic),"synthetic_physical_lineages":len(set(groups)),
      "real_scored_samples":len(real),"real_missing_samples":len(rows)-len(real),
      "descriptor_semantics":{"mapping":"SPECIFIC_SURFACE_PROXY_MAPPING_WITH_NON_IDENTICAL_DEFINITIONS",
        "real":"WADSWORTH_CONNECTED_PERCOLATING_PHASE_SURFACE_DERIVED_USING_MARCHING_CUBES",
        "synthetic":"TOTAL_PERIODIC_VOXEL_FACE_INTERFACIAL_AREA_PROXY_NOT_RESTRICTED_TO_CONNECTED_PORE_PHASE",
        "interpretation":"SURFACE_SCALE_DOMAIN_SEPARATION_NOT_UNIQUE_PHYSICAL_MECHANISM_IDENTIFICATION",
        "real_total_surface_robustness_range_per_m":[min(float(r["s_total_per_m"]) for r in real),max(float(r["s_total_per_m"]) for r in real)]},
      "two_feature_assessment":arm2,"three_feature_scale_proxy_sensitivity":arm3,
      "scale_proxy_semantics":"pore_distance_q50_times_voxel_m_and_R_mean_m_are_non_equivalent_scale_descriptors",
      "box_monotonicity":"OUTSIDE_TWO_FEATURE_BOX_IMPLIES_OUTSIDE_CORRESPONDING_THREE_FEATURE_BOX",
      "real_only_leave_one_coffee_out":real_models,
      "disposition":"SYNTHETIC_CLOSURE_REAL_DATA_OUT_OF_DOMAIN",
      "full_topology_transfer":"FULL_TRANSFER_NOT_TESTABLE_WITH_PROCESSED_DATA_ONLY"}
    (CASE/"XSV_XCT_001_TRANSFER_ASSESSMENT.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def real_only_reference_models(real):
    y=np.log(np.array([float(r["k_m2"]) for r in real]))
    coffee=np.array([r["coffee"] for r in real])
    candidates={
      "connected_porosity_only":np.array([[float(r["phi_p_connected"])] for r in real]),
      "connected_porosity_plus_specific_surface":np.array([[float(r["phi_p_connected"]),
        float(r["s_p_connected_per_m"])] for r in real])}
    out={}
    for name,x in candidates.items():
        pred=np.empty(len(y))
        for held in sorted(set(coffee)):
            test=coffee==held
            pred[test], *_=ridge_fit_predict(x[~test],y[~test],x[test],1.0)
        e=pred-y
        out[name]={"grouping":"LEAVE_ONE_COFFEE_OUT","n":len(y),
          "rmse_logK":float(np.sqrt(np.mean(e*e))),
          "median_multiplicative_error":float(np.median(np.exp(np.abs(e)))),
          "mean_signed_log_bias":float(e.mean())}
    return out


def volume_from_npy(path: Path, *, solid_value=1):
    require_numpy()
    array=np.load(path,allow_pickle=False)
    if array.ndim != 3: raise ValueError("volume must be three-dimensional")
    if not np.isin(array,[0,1]).all(): raise ValueError("binary labels 0/1 required")
    return np.asarray(array == solid_value,dtype=bool)


def volume_descriptors(solid):
    from scipy import ndimage
    fluid=~solid; total=float(fluid.mean())
    labels,n=ndimage.label(fluid,structure=ndimage.generate_binary_structure(3,1))
    directional=[]; spanning=set()
    for axis in range(3):
        low=set(np.unique(np.take(labels,0,axis=axis)))-{0}
        high=set(np.unique(np.take(labels,-1,axis=axis)))-{0}
        ids=low&high; spanning |= ids
        directional.append(float(np.isin(labels,list(ids)).mean()))
    connected=float(np.isin(labels,list(spanning)).mean())
    faces=sum(np.count_nonzero(np.diff(solid.astype(np.int8),axis=a)) for a in range(3))
    distances=ndimage.distance_transform_edt(fluid)
    pore=distances[fluid]
    return {"phi_total":total,"phi_connected_union":connected,
      "phi_connected_x":directional[0],"phi_connected_y":directional[1],
      "phi_connected_z":directional[2],"isolated_void_fraction":total-connected,
      "specific_interfacial_area_lu":float(faces/solid.size),
      "pore_distance_q10":float(np.quantile(pore,.1)),"pore_distance_q50":float(np.quantile(pore,.5)),
      "pore_distance_q90":float(np.quantile(pore,.9)),"fluid_component_count":int(n)}


def hydraulic_contract(phi_gross, q_box_lu, nu_lu, force_lu, voxel_m):
    if not 0 < phi_gross <= 1: raise ValueError("gross porosity must be in (0,1]")
    if force_lu <= 0 or nu_lu <= 0 or voxel_m <= 0: raise ValueError("positive force, viscosity, and voxel size required")
    u_void=q_box_lu/phi_gross
    kg=nu_lu*q_box_lu/force_lu
    kv=nu_lu*u_void/force_lu
    return {"u_void_lu":u_void,"K_gross_lu2":kg,"K_void_lu2":kv,
            "K_gross_m2":kg*voxel_m**2}


def parity_disposition(*, exact_mask, equivalent_boundary, value_mapping=True):
    if not exact_mask: return "SOURCE_DOMAIN_NOT_IDENTICAL"
    if not equivalent_boundary: return "BOUNDARY_SEMANTICS_NOT_EQUIVALENT"
    if not value_mapping: return "PUBLISHED_VALUE_MAPPING_UNRESOLVED"
    return "CROSS_CODE_PARITY_NUMERIC_ADJUDICATION_REQUIRED"


def figures(rows, repro, transfer_result):
    require_numpy()
    import matplotlib.pyplot as plt
    figure_dir=ROOT/"docs/verification/figures/xsv_xct_001"
    figure_dir.mkdir(parents=True,exist_ok=True)
    passed=[r for r in repro if r["status"]=="PASS"]
    obs=np.array([float(r["published_k_m2"]) for r in passed])
    kc=np.array([float(r["kozeny_carman_k_m2"]) for r in passed])
    pc=np.array([float(r["percolation_measured_surface_k_m2"]) for r in passed])
    fig,ax=plt.subplots(figsize=(5.5,4.5)); lo=min(obs.min(),kc.min(),pc.min()); hi=max(obs.max(),kc.max(),pc.max())
    ax.loglog(obs,kc,"o",label="Kozeny–Carman"); ax.loglog(obs,pc,"s",label="Percolation")
    ax.plot([lo,hi],[lo,hi],"k--",lw=1); ax.set(xlabel="Published numerical K (m²)",ylabel="Recalculated K (m²)")
    ax.legend(); fig.tight_layout(); fig.savefig(figure_dir/"source_model_reproduction.png",dpi=180); plt.close(fig)
    plot=read_csv(CASE/"XSV_XCT_001_PLOT_SOURCE.csv")
    fig,axs=plt.subplots(1,2,figsize=(9,4.2))
    for ax,prefix,title in ((axs[0],"two_feature","Two-feature proxy mapping"),(axs[1],"three_feature","Scale proxy mismatch")):
        for coffee,marker in (("Guayacan","o"),("Tumba","s")):
            p=[r for r in plot if r["coffee"]==coffee]
            ax.loglog([float(r["published_k_m2"]) for r in p],[float(r[f"{prefix}_prediction_k_m2"]) for r in p],marker,label=coffee,ls="none")
        values=[float(r[f"{prefix}_prediction_k_m2"]) for r in plot]+[float(r["published_k_m2"]) for r in plot]
        lo,hi=min(values),max(values); ax.plot([lo,hi],[lo,hi],"k--",lw=1); ax.set_title(title)
        ax.set(xlabel="Published numerical K (m²)",ylabel="Synthetic-trained prediction (m²)"); ax.legend()
    fig.tight_layout(); fig.savefig(figure_dir/"synthetic_to_real_transfer.png",dpi=180); plt.close(fig)
    ranges=transfer_result["two_feature_assessment"]["feature_ranges"]
    fig,axs=plt.subplots(1,2,figsize=(8,3.5))
    for ax,key,label in zip(axs,("connected_porosity","specific_surface_proxy_per_m"),("Connected porosity","Non-identical surface proxy (m⁻¹)")):
        s=ranges["synthetic"][key]; r=ranges["real"][key]
        ax.plot(s,[0,0],lw=8,label="Synthetic"); ax.plot(r,[1,1],lw=8,label="Real processed")
        ax.set_yticks([0,1],["Synthetic","Real"]); ax.set_xlabel(label)
    fig.tight_layout(); fig.savefig(figure_dir/"shared_feature_domain.png",dpi=180); plt.close(fig)


def summarize(repro, transfer_result):
    passed=[r for r in repro if r["status"]=="PASS"]
    def metrics(key):
        e=np.array([float(r[key]) for r in passed])
        return {"geometric_mean_prediction_over_observation":float(np.exp(e.mean())),
                "rmse_logK":float(np.sqrt(np.mean(e*e))),
                "median_multiplicative_error":float(np.median(np.exp(np.abs(e))))}
    values=np.array([float(r["published_k_m2"]) for r in passed])
    target={str(t):{"minimum_over_maximum_ratio":float(values.min()/values.max()),
                    "cross_sample_range_spans_target":bool(values.min()/values.max()<=t)} for t in TARGETS}
    result={"schema_version":"espresso.whole_pull.xsv_xct_001.result.v1",
      "route":"PROCESSED_REAL_COFFEE_DATA_ROUTE_COMPLETE","source_rows":22,
      "source_scored_rows":len(passed),"raw_or_segmented_volumes":0,"gpu_runs":0,
      "source_reproduction":{"kozeny_carman":metrics("kc_log_error"),
        "percolation_measured_surface":metrics("percolation_log_error"),
        "percolation_angular_surface":metrics("percolation_angular_log_error")},
      "transfer":transfer_result,"cross_code":"CROSS_CODE_PARITY_NOT_ADJUDICATED",
      "generator":"REAL_VOLUME_EVIDENCE_INSUFFICIENT_FOR_GENERATOR_ASSESSMENT",
      "real_coffee_rev":"REAL_COFFEE_REV_NOT_ADJUDICATED",
      "target":{"evidence_role":"STATIC_CROSS_SAMPLE_CAPABILITY_CONFOUNDED_BY_COFFEE_GRIND_POROSITY_AND_PREPARATION",
                "adjudication":target,"dynamic_mechanism":"NOT_IDENTIFIED"},
      "next_programme":"DEDICATED_REAL_XCT_DATA_ACCESS_OR_ACQUISITION",
      "production_disposition":"NO_NEW_PRODUCTION_PHYSICS_YET",
      "claim_boundary":{"physical_validation":"NOT_ESTABLISHED","real_coffee_geometry":"PROCESSED_DATA_ONLY",
        "real_tamped_puck_representative_volume":"NOT_ESTABLISHED","dynamic_pressure_mechanism":"NOT_IDENTIFIED",
        "production_openfoam_physics":"UNCHANGED"}}
    (CASE/"XSV_XCT_001_TARGET_ASSESSMENT.json").write_text(json.dumps({
      "schema_version":"espresso.whole_pull.xsv_xct_001.target_assessment.v1",
      "targets":target,"observed_minimum_over_maximum_ratio":float(values.min()/values.max()),
      "comparison_class":"STATIC_STATE_CAPABILITY_COMPARISON",
      "selection_class":"POST_OBSERVATION_TARGET_COMPARISON",
      "confounding":["coffee","grind","porosity","preparation"],
      "physical_cause":"NOT_IDENTIFIED","paired_transformation":"NOT_EXECUTED_NO_REAL_VOLUME"},indent=2)+"\n")
    (CASE/"XSV_XCT_001_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def write_artifact_manifest():
    paths=[
      CASE/"XSV_XCT_001_PROCESSED_SOURCE_DATA.csv",CASE/"XSV_XCT_001_SOURCE_REPRODUCTION.csv",
      CASE/"XSV_XCT_001_SCORED_MATRIX.csv",CASE/"XSV_XCT_001_SCORED_MATRIX.json",
      CASE/"XSV_XCT_001_PLOT_SOURCE.csv",CASE/"XSV_XCT_001_TRANSFER_ASSESSMENT.json",
      CASE/"XSV_XCT_001_TARGET_ASSESSMENT.json",CASE/"XSV_XCT_001_RESULT.json",
      ROOT/"docs/verification/XSV_XCT_001_REAL_COFFEE_XCT_IMPORT_AND_COMPARISON_RESULT.md",
      ROOT/"docs/verification/figures/xsv_xct_001/shared_feature_domain.png",
      ROOT/"docs/verification/figures/xsv_xct_001/source_model_reproduction.png",
      ROOT/"docs/verification/figures/xsv_xct_001/synthetic_to_real_transfer.png"]
    records=[{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":sha256(p)} for p in paths]
    aggregate=hashlib.sha256("".join(f"{r['path']}\0{r['sha256']}\n" for r in records).encode()).hexdigest()
    (CASE/"XSV_XCT_001_ARTIFACT_MANIFEST.json").write_text(json.dumps({
      "schema_version":"espresso.whole_pull.xsv_xct_001.artifact_manifest.v1",
      "file_count":len(records),"aggregate_sha256":aggregate,"files":records},indent=2)+"\n")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["import-processed","reproduce-source","transfer","all","inspect-volume"])
    parser.add_argument("--source",type=Path); parser.add_argument("--volume",type=Path)
    args=parser.parse_args()
    if args.command=="inspect-volume":
        print(json.dumps(volume_descriptors(volume_from_npy(args.volume)),indent=2)); return
    source=args.source
    if source is None: raise SystemExit("--source is required")
    rows=import_processed(source)
    if args.command=="import-processed": return
    repro=source_reproduction(rows)
    if args.command=="reproduce-source": return
    trans=transfer(rows)
    if args.command in ("transfer","all"):
        result=summarize(repro,trans)
        if args.command=="all": figures(rows,repro,trans)
        write_artifact_manifest()
        print(json.dumps(result,indent=2))


if __name__ == "__main__": main()
