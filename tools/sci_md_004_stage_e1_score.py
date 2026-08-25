#!/usr/bin/env python3
"""Single-process protected scorer for the immutable SCI-MD-004 bundle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICTION_COMMIT = "8c46ca93e23ac8eb1c521509566f6d3e96cbc381"
PREDICTION_TREE = "9d9960945774e84b696d7dd5d17b62c474d4bdd4"
PREDICTION_MANIFEST_SHA = "06312aa83f200cdeab09795e8611e80d63865936794b84fc582ed2b990214062"
TARGET_SHA = "f3282db7e86a9aff1fce04e71c65beb430925ca515d5a898339e2e379844d1c5"
G1_MANIFEST_SHA = "7ec81afcb4c91d9592b6eb07ea923f35107d690245157ea5e1972ab3edb538ef"
STAGE_E0 = {
 "BLOCKED_WHOLE_EXPERIMENT_CV.csv":"8d3c5f4b725351e915a6ce56a7591bc709e8f59e2459dd14b25fc1258251f48a",
 "COMMON_H0_H1_OBSERVATION_OPERATOR.json":"4d2e5347ca876553443d9ba5629b6095679a33a9f4794bed98ea8cc3c63d76fd",
 "CONDITIONAL_CASE_FREEZE.json":"d969d00295443b2861a9f0107c2536ef5283f9e580a1f3fb56a8c2252df47626",
 "NUMERICAL_APPLICATION_QUALIFICATION.json":"e9ffc2f907e5ca3d31e47fdc3c865f8cd63c4fda509d687318979786652b0385",
 "PARAMETERIZATION_AND_IDENTIFIABILITY.json":"ec30b7e0038e092c9b8e0d8e3d5d47de35be4e1afdbc650f826ac72f17e1b051",
}


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value: object) -> bytes: return (json.dumps(value,indent=2,sort_keys=True)+"\n").encode()
def read_csv(path: Path):
    with path.open(newline="") as stream: return list(csv.DictReader(stream))
def write_csv(path: Path, rows: list[dict]):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def metric(values: list[tuple[float,float]]) -> dict:
    errors=[p-o for p,o in values]; absolute=[abs(x) for x in errors]
    observed=[o for _,o in values]; predicted=[p for p,_ in values]
    relative=sorted(abs((p-o)/o) for p,o in values); middle=len(relative)//2
    return {"n":len(values),"MAE":sum(absolute)/len(values),
      "RMSE":math.sqrt(sum(x*x for x in errors)/len(values)),
      "NRMSE":math.sqrt(sum(x*x for x in errors)/len(values))/(sum(observed)/len(observed)),
      "median_absolute_relative_error":.5*(relative[middle-1]+relative[middle]),
      "sMAPE":sum(2*abs(p-o)/(abs(p)+abs(o)) for p,o in values)/len(values),
      "signed_bias":sum(errors)/len(values),"observed_range":[min(observed),max(observed)],
      "predicted_range":[min(predicted),max(predicted)]}


def score(prediction_dir: Path, puckworks: Path, destination: Path) -> None:
    lifecycle=["BEFORE_TARGET_OPEN"]
    head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    tree=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD^{tree}"],text=True).strip()
    if (head,tree)!=(PREDICTION_COMMIT,PREDICTION_TREE): raise SystemExit("prediction Git identity mismatch")
    if sha(prediction_dir/"PREDICTION_MANIFEST.json")!=PREDICTION_MANIFEST_SHA: raise SystemExit("prediction manifest mismatch")
    prediction_manifest=json.loads((prediction_dir/"PREDICTION_MANIFEST.json").read_text())
    if prediction_manifest["semantic_protected_target_open_count"]!=0 or prediction_manifest["numerical_gate_status"]!="PASS":
        raise SystemExit("prediction bundle is not score eligible")
    if sha(ROOT/"validation/sci_md_004_stage_e1_hydraulic_reconciliation/G1_FREEZE_MANIFEST.json")!=G1_MANIFEST_SHA:
        raise SystemExit("G1 freeze hash mismatch")
    for name,expected in STAGE_E0.items():
        if sha(ROOT/"validation/sci_md_004_stage_e0"/name)!=expected: raise SystemExit("Stage E0 hash mismatch")
    if subprocess.check_output(["git","-C",str(puckworks),"rev-parse","HEAD"],text=True).strip()!="5ce003e751aac516b5de3d9ede4e6910627e2b12":
        raise SystemExit("Puckworks identity mismatch")
    # The protected adapter is imported only after every immutable authority passes.
    sys.path.insert(0,str(puckworks.parent))
    from puckworks.analysis import angeloni2023_multispecies as adapter
    target_bytes=adapter._csv(adapter.build_targets())
    if hashlib.sha256(target_bytes).hexdigest()!=TARGET_SHA: raise SystemExit("protected target hash mismatch")
    lifecycle.append("TARGET_OPENED")
    target_rows=list(csv.DictReader(target_bytes.decode().splitlines()))
    targets={}
    for row in target_rows:
        if row["observable_id"]=="bioactives" and row["species_id"] in {"caffeine","trigonelline"}:
            targets[(row["sample_id"],row["species_id"])]=float(row["canonical_value"])
        elif row["observable_id"]=="total_solids": targets[(row["sample_id"],"total_solids")]=float(row["canonical_value"])
    predictions=read_csv(prediction_dir/"PREDICTIONS.csv")
    if len(predictions)!=396 or len(targets)!=198: raise SystemExit("prediction/target completeness mismatch")
    condition_rows=[]; grouped={}
    for row in predictions:
        key=(row["hypothesis"],row["observable"]); pred=float(row["prediction_kg_m3"])
        obs=targets[(row["sample_id"],row["observable"])]
        grouped.setdefault(key,[]).append((pred,obs))
        condition_rows.append({"sample_id":row["sample_id"],"hypothesis":row["hypothesis"],"observable":row["observable"],
          "prediction_kg_m3":pred,"observation_kg_m3":obs,"signed_error":pred-obs,"absolute_error":abs(pred-obs),
          "relative_error":(pred-obs)/obs,"squared_error":(pred-obs)**2})
    metrics={obs:{h:metric(grouped[(h,obs)]) for h in ("H0","H1")} for obs in ("caffeine","trigonelline","total_solids")}
    pair_manifest=json.loads((prediction_dir/"DIRECTIONAL_PAIR_MANIFEST.json").read_text())
    pred_index={(r["sample_id"],r["hypothesis"],r["observable"]):float(r["prediction_kg_m3"]) for r in predictions}
    directional={}
    directional_rows=[]
    for species in ("caffeine","trigonelline"):
      directional[species]={}
      for hypothesis in ("H0","H1"):
        correct=0
        for pair in pair_manifest["pairs"]:
          a,b=pair["sample_a"],pair["sample_b"]
          pd=pred_index[(a,hypothesis,species)]-pred_index[(b,hypothesis,species)]
          od=targets[(a,species)]-targets[(b,species)]
          concordant=(pd==0 and od==0) or pd*od>0
          correct+=int(concordant)
          directional_rows.append({"condition_id":pair["condition_id"],"species":species,"hypothesis":hypothesis,
            "sample_a":a,"sample_b":b,"predicted_difference":pd,"observed_difference":od,"concordant":concordant})
        directional[species][hypothesis]={"concordant":correct,"pairs":33,"fraction":correct/33}
    j0=.5*(metrics["caffeine"]["H0"]["NRMSE"]+metrics["trigonelline"]["H0"]["NRMSE"])
    j1=.5*(metrics["caffeine"]["H1"]["NRMSE"]+metrics["trigonelline"]["H1"]["NRMSE"])
    accepted=(j1<=.85*j0 and all(metrics[s]["H1"]["NRMSE"]<=metrics[s]["H0"]["NRMSE"] for s in ("caffeine","trigonelline"))
      and all(directional[s]["H1"]["fraction"]>=directional[s]["H0"]["fraction"] for s in ("caffeine","trigonelline"))
      and metrics["total_solids"]["H1"]["NRMSE"]<=1.10*metrics["total_solids"]["H0"]["NRMSE"])
    incomplete=(j1<=1.10*j0 and all(metrics[s]["H1"]["NRMSE"]<=1.10*metrics[s]["H0"]["NRMSE"] for s in ("caffeine","trigonelline"))
      and metrics["total_solids"]["H1"]["NRMSE"]<=1.10*metrics["total_solids"]["H0"]["NRMSE"])
    result=("SCI_MD_004_ACCEPTED_PREDICTIVE_EXTENSION" if accepted else
            "SCI_MD_004_CAPABILITY_ADDED_PHYSICAL_VALIDATION_INCOMPLETE" if incomplete else
            "SCI_MD_004_REJECTED_PARAMETERIZATION_OR_FORMULATION")
    temp=destination.with_name(destination.name+".tmp-single-scorer")
    if temp.exists() or destination.exists(): raise SystemExit("result destination is not fresh")
    temp.mkdir(parents=True)
    write_csv(temp/"CONDITION_LEVEL_RESULTS.csv",condition_rows); write_csv(temp/"DIRECTIONAL_RESULTS.csv",directional_rows)
    (temp/"SPECIES_METRICS.json").write_bytes(canonical({s:metrics[s] for s in ("caffeine","trigonelline")}))
    (temp/"TOTAL_SOLIDS_METRICS.json").write_bytes(canonical(metrics["total_solids"]))
    (temp/"FINAL_SCIENTIFIC_RESULT.json").write_bytes(canonical({"primary_scientific_result":result,
      "joint_J":{"H0":j0,"H1":j1,"relative_improvement":1-j1/j0,"material_improvement_threshold":.15},
      "directional_results":directional,"prediction_execution_count":264,"successful_scorer_process_count":1,
      "protected_target_open_count":1,"post_holdout_retuning_count":0,"physical_validation":"NOT_ESTABLISHED",
      "claim_ceiling":["THE GENERIC INDEXED SPECIES SOLVER IS SOFTWARE AND NUMERICALLY VERIFIED.",
      "THE CAFFEINE AND TRIGONELLINE PARAMETERS ARE TRAINING-DATA ESTIMATES, NOT UNIVERSAL PHYSICAL CONSTANTS.",
      "THE HYDRAULIC ADAPTER USES CONDITION-SPECIFIC EFFECTIVE PERMEABILITY DERIVED FROM REPORTED PRESSURE, NOMINAL YIELD, DURATION, GEOMETRY, AND WATER PROPERTIES.",
      "THE INFERRED PERMEABILITIES ARE NONPORTABLE NUISANCE INPUTS AND ARE NOT A VALIDATED GRINDER-TO-PERMEABILITY MODEL.",
      "THE ANGELONI COMPARISON IS CONDITIONAL ON MEASURED INITIAL INVENTORIES AND NONCHEMICAL APPARATUS INPUTS.",
      "THE RESULT DOES NOT VALIDATE MACHINE HYDRAULICS, PERMEABILITY, INTERNAL TRANSIENT FIELDS, THERMAL CHEMISTRY, LIPID TRANSPORT, TASTE, OR UNRESTRICTED TRANSFER.",
      "GENERAL PHYSICAL VALIDATION REMAINS NOT_ESTABLISHED.",
      "ANGELONI MAY NOT AGAIN BE CALLED A NO-RETUNING HOLDOUT FOR A MODEL REVISED IN RESPONSE TO ITS RESULTS."]}))
    lifecycle.append("RESULT_COMMITTED")
    receipt={"lifecycle":lifecycle,"scorer_process_count":1,"protected_target_open_count":1,"target_sha256":TARGET_SHA,
      "prediction_commit":PREDICTION_COMMIT,"prediction_tree":PREDICTION_TREE,"prediction_manifest_sha256":PREDICTION_MANIFEST_SHA,
      "g1_freeze_manifest_sha256":G1_MANIFEST_SHA,"result":result}
    (temp/"SCORER_INVOCATION_RECEIPT.json").write_bytes(canonical(receipt))
    artifacts=[p for p in temp.iterdir()]
    (temp/"RESULT_MANIFEST.json").write_bytes(canonical({"primary_scientific_result":result,
      "artifact_hashes":{p.name:sha(p) for p in artifacts},"successful_scorer_process_count":1,"target_open_count":1}))
    os.replace(temp,destination)


def main():
    p=argparse.ArgumentParser();p.add_argument("--prediction-dir",required=True,type=Path);p.add_argument("--puckworks",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();score(a.prediction_dir.resolve(),a.puckworks.resolve(),a.output.resolve())
if __name__=="__main__": main()
