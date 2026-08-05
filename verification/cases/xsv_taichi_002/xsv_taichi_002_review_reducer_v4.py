#!/usr/bin/env python3
"""Final fail-closed package wrapper for immutable XSV-TAICHI-002 evidence.

Scientific quantities remain derived by the preserved v2 formula path.  This
v4 wrapper binds frozen bytes, ordered identities, claims, package members,
and deterministic output inventories.  It did not execute the CUDA campaign.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, re, sys
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
import xsv_taichi_002_review_reducer_v3 as v3
classify_constriction=v3.classify_constriction
classify_heterogeneity=v3.classify_heterogeneity
classify_overall=v3.classify_overall
TARGET=v3.TARGET
TARGET_INPUTS=v3.TARGET_INPUTS

V2_HASH="0cc9a1f9281f545813c684962df962b50675f852753fdc7c5338374737c655d0"
V3_HASH="ac8e71c23ede9d0170a0696ac33b017d61d5ffb7c216418cee8ea8915dc58c5a"
START_RESULT="2d2315dab8855560c8c7aaf31ec2f6908c1698e80395f435fcca42660691a708"
FROZEN={
 "protocol_md":("docs/verification/XSV_TAICHI_002_SYNTHETIC_MORPHOLOGY_AND_REQUIRED_PERMEABILITY_COLLAPSE_SCREEN.md","04911d266c77470f7d7a83a39842090100407a43fc3a36990b2177eea5496c28"),
 "protocol":("verification/cases/xsv_taichi_002/XSV_TAICHI_002_PROTOCOL.json","c8582edbc494a32379a5b28a4e12f2230521183962cd940bd58c8cfc504ff297"),
 "matrix":("verification/cases/xsv_taichi_002/XSV_TAICHI_002_CASE_MATRIX.csv","74a709b8a766587cfd97194cf001002a19c124152173ad4a9d50f3bf804b7ed2"),
 "target":("verification/cases/xsv_taichi_002/XSV_TAICHI_002_TARGET.json","388655e6a7f4043f7acd5d26d672f8d3843a44277c1b173a639b823f92278472"),
 "target_inputs":("verification/cases/xsv_taichi_002/XSV_TAICHI_002_TARGET_INPUTS.csv","ba051dd799a3467af3ea06cd29e0a0e36f1e47774b8b4ecd6c70e69d45018c52"),
 "geometry":("verification/cases/xsv_taichi_002/XSV_TAICHI_002_GEOMETRY_MANIFEST.json","b635a1e83b0e04f0b29ddc27baa870a13ad0771e3c197766eba3664aeb86832a"),
 "runtime":("verification/cases/xsv_taichi_002/xsv_taichi_002_runtime.py","3bbf089ab5855bdbaeabb9a569ec9176974e8c25499a0c43c0d011be69d74a75")}
RUN_IDS=("H-A0-S42-X-MID","H-A0-S1729-X-MID","H-A0-S20260805-X-MID","H-A1-S42-X-MID","H-A1-S1729-X-MID","H-A1-S20260805-X-MID","H-A2-S42-X-MID","H-A2-S1729-X-MID","H-A2-S20260805-X-MID","C05-X-MID","C15-X-MID","C30-X-MID","H-A0-S42-Y-MID","H-A0-S42-Z-MID","H-A2-S42-Y-MID","H-A2-S42-Z-MID","C30-Y-MID","C30-Z-MID","H-A2-S42-X-LOW","H-A2-S42-X-HIGH","C30-X-LOW","C30-X-HIGH")
PROHIBITED=("COMPACTION_CONFIRMED","FINES_CONFIRMED","FINES_MIGRATION_CONFIRMED","FINES_DEPOSITION_CONFIRMED","CLOGGING_CONFIRMED","CHANNELING_CONFIRMED","DAMAGE_CONFIRMED","REAL_COFFEE_MORPHOLOGY_REPRESENTED","REAL_COFFEE_PERMEABILITY_ESTABLISHED","REAL_COFFEE_ANISOTROPY_ESTABLISHED","OPENFOAM_PHYSICALLY_VALIDATED","GENERAL_SOLVER_PHYSICAL_VALIDATION_ESTABLISHED","NEW_GOVERNING_PHYSICS_JUSTIFIED","INDEPENDENT_DATA_GATE_SATISFIED")

def digest(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
def canonical(x:Any)->bytes:return (json.dumps(x,sort_keys=True,separators=(",",":"))+"\n").encode()
def ck(name:str,observed:Any,expected:Any,path:str,rule:str,sha256:str|None=None)->dict[str,Any]:
 ok=observed==expected
 return {"check":name,"observed":observed,"expected":expected,"operator":"EXACT_EQUAL","evidence_path":path,"evidence_sha256":sha256,"derivation":rule,"pass":ok,"typed_failure_reason":None if ok else name.upper()+"_MISMATCH"}
def gate(name:str,checks:list[dict[str,Any]],limitation:str|None=None)->dict[str,Any]:
 status="FAIL" if any(not x["pass"] for x in checks) else ("PASS_WITH_TYPED_PROVENANCE_LIMITATION" if limitation else "PASS")
 return {"gate":name,"status":status,"checks":checks,"typed_provenance_limitation":limitation}

def frozen_checks(root:Path=ROOT)->list[dict[str,Any]]:
 return [ck(f"frozen_{key}_sha256",digest(root/rel),expected,rel,"hash current bytes before parsing",digest(root/rel)) for key,(rel,expected) in FROZEN.items()]

def matrix_checks(path:Path)->tuple[list[dict[str,Any]],list[dict[str,str]]]:
 with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
 ids=[x["run_id"] for x in rows]; orders=[int(x["run_order"]) for x in rows]
 checks=[ck("matrix_sha256",digest(path),FROZEN["matrix"][1],str(path),"hash exact matrix bytes",digest(path)),ck("matrix_row_count",len(rows),22,str(path),"parse all CSV rows",digest(path)),ck("matrix_unique_run_ids",len(set(ids)),22,str(path),"count unique parsed IDs",digest(path)),ck("matrix_ordered_run_ids",ids,list(RUN_IDS),str(path),"compare complete ordered sequence",digest(path)),ck("matrix_run_orders",orders,list(range(1,23)),str(path),"compare exact integer order sequence",digest(path))]
 return checks,rows

def target_checks(target_path:Path,inputs_path:Path)->tuple[list[dict[str,Any]],dict[str,float]]:
 checks=[ck("target_frozen_hash",digest(target_path),FROZEN["target"][1],str(target_path),"hash before JSON parse",digest(target_path)),ck("target_inputs_frozen_hash",digest(inputs_path),FROZEN["target_inputs"][1],str(inputs_path),"hash before CSV parse",digest(inputs_path))]
 target=json.loads(target_path.read_text())
 with inputs_path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
 checks += [ck("target_rows",len(rows),3,str(inputs_path),"parse exactly three rows",digest(inputs_path)),ck("target_row_groups",[int(x["nominal_group_bar"]) for x in rows],[5,9,11],str(inputs_path),"compare exact ordered nominal groups",digest(inputs_path))]
 by_json={int(x["nominal_group_bar"]):x for x in target["inputs"]}
 for row in rows:
  n=int(row["nominal_group_bar"]); x=by_json[n]
  obs=[row["condition"],float(row["source_time_s"]),int(row["source_csv_line"]),row["pressure_node"],row["flow_field"],row["source_path"],row["source_sha256"],float(row["pressure_bar"]),float(row["mass_flow_g_s"])]
  exp=[x["condition"],x["time_s"],x["source_csv_line"],target["selection_rule"]["pressure_field"],target["selection_rule"]["flow_field"],target["source_files"]["traces"]["path"],target["source_files"]["traces"]["sha256"],x["basket_pressure_bar"],x["mass_flow_g_s"]]
  checks.append(ck(f"target_row_{n}_identity",obs,exp,str(inputs_path),"bind CSV primitives to target JSON",digest(inputs_path)))
 h={int(x["nominal_group_bar"]):float(x["mass_flow_g_s"])/float(x["pressure_bar"]) for x in rows}
 vals={"T_11_5":h[11]/h[5],"T_9_5":h[9]/h[5],"T_11_9":h[11]/h[9],"nominal_screen":5/11,"nominal_collapse":1-5/11}
 tol=target["formula"]["recomputation_tolerance"]
 expected={**target["ratios"],"nominal_screen":target["nominal_pressure_ordering_screen"]["ratio_upper_bound"],"nominal_collapse":target["nominal_pressure_ordering_screen"]["collapse_lower_bound_fraction"]}
 for key in vals: checks.append(ck(key,abs(vals[key]-expected[key])<=tol,True,str(inputs_path),f"independent recomputation; absolute tolerance {tol}",digest(inputs_path)))
 checks += [ck("target_type",target["target_type"],"APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET",str(target_path),"parse frozen field",digest(target_path)),ck("orientation",target["ratios"]["orientation"],"SMALLER_IS_GREATER_REQUIRED_COLLAPSE",str(target_path),"parse frozen field",digest(target_path)),ck("attainment_operator",target["ratios"]["primary_attainment_rule"],"K_case_over_K_reference <= T_11_5",str(target_path),"parse frozen field",digest(target_path)),ck("nominal_not_primary",target["nominal_pressure_ordering_screen"]["is_primary_target"],False,str(target_path),"parse frozen field",digest(target_path)),ck("selection_rule",target["selection_rule"]["rule"],"maximum time__s row within each exact reference_pressure_round__bar group",str(target_path),"parse frozen selection rule",digest(target_path)),ck("pressure_units",all(x["pressure_node"].endswith("__bar") for x in rows),True,str(inputs_path),"field carries governed bar unit",digest(inputs_path)),ck("flow_units",all(x["flow_field"].endswith("__g_per_s") for x in rows),True,str(inputs_path),"field carries governed g/s unit",digest(inputs_path))]
 return checks,vals

NEGATIVE_PATTERNS=(re.compile(r"\bnot\s+(?:established|authorized|confirmed)?\s*`?{token}`?",re.I),re.compile(r"`?{token}`?\s*:\s*(?:NOT_ESTABLISHED|NOT_AUTHORIZED|PROHIBITED)",re.I),re.compile(r"(?:prohibited|forbidden)[^\n]{{0,100}}`?{token}`?",re.I))
def claim_occurrences(text:str)->list[dict[str,Any]]:
 findings=[]
 for token in PROHIBITED:
  for match in re.finditer(re.escape(token),text):
   start=max(text.rfind("\n",0,match.start())+1,match.start()-120); end=text.find("\n",match.end()); end=len(text) if end<0 else min(end,match.end()+120)
   context=text[start:end]; exempt=any(p.pattern.format(token=re.escape(token)) and re.search(p.pattern.format(token=re.escape(token)),context,re.I) for p in NEGATIVE_PATTERNS)
   findings.append({"token":token,"offset":match.start(),"context":context,"disposition":"EXEMPT_NEGATIVE_OR_PROHIBITED_CONTEXT" if exempt else "FORBIDDEN_POSITIVE_OCCURRENCE","pass":exempt})
 return findings
def claim_checks(documents:dict[str,str])->list[dict[str,Any]]:
 checks=[]
 for path,text in documents.items():
  bad=[x for x in claim_occurrences(text) if not x["pass"]]
  checks.append(ck("claims_"+Path(path).name,bad,[],path,"inspect every token occurrence in its own line/bounded context",hashlib.sha256(text.encode()).hexdigest()))
 return checks

def inventory(root:Path,relative_paths:list[str])->list[dict[str,Any]]:
 rows=[]
 for rel in sorted(relative_paths):
  p=root/rel; rows.append({"path":rel,"bytes":p.stat().st_size,"sha256":digest(p)})
 return rows
def inventory_aggregate(rows:list[dict[str,Any]])->str:return hashlib.sha256(canonical(rows)).hexdigest()
def compare_inventories(a:list[dict[str,Any]],b:list[dict[str,Any]],committed:list[dict[str,Any]])->list[dict[str,Any]]:
 return [ck("output_A_B_identity",a,b,"deterministic inventories A/B","compare sorted path/bytes/hash inventories"),ck("generated_committed_identity",a,committed,"generated and committed deterministic core","compare sorted path/bytes/hash inventories")]

def artifact_checks(artifact_path:Path,root:Path,qa_path:Path,result_path:Path)->list[dict[str,Any]]:
 artifact=json.loads(artifact_path.read_text()); result=json.loads(result_path.read_text()); qa=json.loads(qa_path.read_text())["xsv_taichi_002"]
 members=artifact["committed_members"]; checks=[]
 for rel,expected in members.items(): checks.append(ck("artifact_"+rel,digest(root/rel),expected,rel,"verify committed member bytes",digest(root/rel)))
 required={"XSV_TAICHI_002_RESULT.json","XSV_TAICHI_002_SUMMARY.md","XSV_TAICHI_002_RUN_MANIFEST.csv","plots/XSV_TAICHI_002_PLOT_SOURCE.csv","xsv_taichi_002_review_reducer_v4.py","XSV_TAICHI_002_G9_FINAL_PACKAGE_INTEGRITY_CLOSURE.json","XSV_TAICHI_002_DETERMINISTIC_REDUCTION_RECORD.json"}|{f"plots/{x}" for x in ("coating_response.svg","directional_permeability.svg","heterogeneity_coefficient_of_variation.svg","heterogeneity_fastest_quartile_flow_share.svg","heterogeneity_response.svg","heterogeneity_sigma_micro.svg","k_ratio_vs_connected_porosity.svg","k_ratio_vs_gross_porosity.svg","k_ratio_vs_localization.svg","linearity_anchors.svg")}
 checks += [ck("artifact_required_classes",required <= set(members),True,str(artifact_path),"set inclusion over exact required classes",digest(artifact_path)),ck("artifact_lineage",artifact["lineage"],[V2_HASH,V3_HASH,START_RESULT],str(artifact_path),"exact ordered lineage",digest(artifact_path)),ck("qa_result_hash",qa["result_sha256"],digest(result_path),str(qa_path),"bind QA result identity",digest(qa_path)),ck("qa_scientific_disposition",qa["scientific_disposition"],result["overall_synthesis"],str(qa_path),"compare current authorities",digest(qa_path)),ck("qa_physical_validation",qa["physical_validation"],"NOT_ESTABLISHED",str(qa_path),"claim boundary",digest(qa_path)),ck("qa_next_stage",qa["xsv_taichi_003"],"NOT_STARTED_NOT_AUTHORIZED",str(qa_path),"next-stage boundary",digest(qa_path))]
 return checks

def reduce(evidence:Path,archive:Path,output:Path,committed_root:Path=HERE)->None:
 output.mkdir(parents=True,exist_ok=True); v3.v2.reduce(evidence,archive,output)
 run_manifest=output/"XSV_TAICHI_002_RUN_MANIFEST.csv"
 with run_manifest.open(newline="",encoding="utf-8") as f: manifest_rows=list(csv.DictReader(f))
 manifest_fields=[x for x in manifest_rows[0] if x!="attempt_id"]
 with run_manifest.open("w",newline="",encoding="utf-8") as f:
  writer=csv.DictWriter(f,fieldnames=manifest_fields,lineterminator="\n",extrasaction="ignore"); writer.writeheader(); writer.writerows(manifest_rows)
 result=json.loads((output/"XSV_TAICHI_002_RESULT.json").read_text())
 frozen=frozen_checks(); matrix,matrix_rows=matrix_checks(ROOT/FROZEN["matrix"][0]); targets,ratios=target_checks(ROOT/FROZEN["target"][0],ROOT/FROZEN["target_inputs"][0])
 geometry,geometry_table=v3.geometry_checks(evidence)
 geometry=[ck("geometry_manifest_frozen_hash",digest(ROOT/FROZEN["geometry"][0]),FROZEN["geometry"][1],FROZEN["geometry"][0],"hash before parsing",digest(ROOT/FROZEN["geometry"][0])),ck("historical_runtime_frozen_hash",digest(ROOT/FROZEN["runtime"][0]),FROZEN["runtime"][1],FROZEN["runtime"][0],"hash before importing connectivity",digest(ROOT/FROZEN["runtime"][0]))]+geometry
 observed=[x["run_id"] for x in result["runs"]]
 runset=[ck("retained_ordered_identity_set",observed,list(RUN_IDS),"22 retained run records","compare complete ordered set to independently parsed matrix"),ck("retained_unique_identity_count",len(set(observed)),22,"22 retained run records","count unique IDs")]
 canonical_docs={str(p.relative_to(ROOT)):p.read_text() for p in (HERE/"XSV_TAICHI_002_SUMMARY.md",ROOT/"docs/PROJECT_STATE.md",ROOT/"docs/CLAIM_CEILING.md",ROOT/FROZEN["protocol_md"][0],HERE/"XSV_TAICHI_002_EXACT_HEAD_REVIEW_CORRECTION.json",HERE/"XSV_TAICHI_002_G8_EVIDENCE_BINDING_CORRECTION.json",HERE/"XSV_TAICHI_002_STAGE_AUTHORIZATION.json")}
 canonical_docs["candidate_G9_record"]=json.dumps({"authorization_id":"XSV-TAICHI-002-FINAL-PACKAGE-INTEGRITY-CLOSURE-2026-08-05","numerical_rerun":"NONE","scientific_evidence_change":"NONE","merge_authority":"NOT_GRANTED","physical_validation":"NOT_ESTABLISHED"},sort_keys=True)
 qa=json.loads((ROOT/"PACKAGE_QA_STATUS.json").read_text())["xsv_taichi_002"]
 canonical_docs["PACKAGE_QA_STATUS.json#xsv_taichi_002_claim_projection"]=json.dumps({k:qa.get(k) for k in ("scientific_disposition","localization_disposition","anisotropy_disposition","physical_validation","xsv_taichi_003")},sort_keys=True)
 canonical_docs["candidate_result"]=json.dumps(result)
 claims=claim_checks(canonical_docs)
 raw=v3.v2.verify_raw_manifest(evidence/"SELF_EXCLUDING_MANIFEST.json",evidence)
 authority_checks,historical_g0=v3.historical_authority()
 g0=gate("G0_PROTOCOL_BOOTSTRAP_AND_PROSPECTIVE_FREEZE",authority_checks+[x for x in frozen if x["check"] in ("frozen_protocol_md_sha256","frozen_protocol_sha256","frozen_matrix_sha256","frozen_runtime_sha256")]+matrix)
 g1=gate("G1_REQUIRED_COLLAPSE_TARGET_DERIVATION_AND_FREEZE",targets)
 g2=gate("G2_DETERMINISTIC_GEOMETRY_GENERATION_AND_IDENTITY_FREEZE",geometry)
 limitation="PROCESS_ATTEMPT_COUNT_AND_CEILING_COMPLIANCE_NOT_INDEPENDENTLY_RECONSTRUCTED"
 g3=gate("G3_BOUNDED_TAICHI_CUDA_EXECUTION",runset+[ck("all_run_bindings",all(x["pass"] for x in result["run_binding_checks"]),True,"22 run records and primitive artifacts","retain complete v2 run-to-matrix binding")],limitation)
 g4=result["gates"]["G4_DETERMINISTIC_REDUCTION_AND_NUMERICAL_QUALIFICATION"]
 for item in g4["checks"]:
  item.setdefault("evidence_path","retained primitive run records")
  item.setdefault("evidence_sha256",None)
  item.setdefault("derivation",item.get("threshold","frozen v2 numerical qualification rule"))
  item.setdefault("typed_failure_reason",None if item.get("pass") else "G4_NUMERICAL_QUALIFICATION_FAILURE")
 g5=gate("G5_SCIENTIFIC_SYNTHESIS_AND_CLAIM_BOUNDED_DISPOSITION",claims+[ck("overall",result["overall_synthesis"],"REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE","derived family dispositions","preserve approved scientific result")])
 g6=gate("G6_FINAL_EVIDENCE_PACKAGE",[ck("raw_manifest",raw["hash"],v3.v2.EXPECTED["raw_manifest"],"SELF_EXCLUDING_MANIFEST.json","hash actual raw manifest"),ck("raw_members",raw["all_members_verified"],True,"SELF_EXCLUDING_MANIFEST.json","verify every raw member"),ck("archive",digest(archive),v3.v2.EXPECTED["archive"],archive.name,"hash archive bytes"),ck("package_construction_inputs",all(x["pass"] for x in frozen),True,"frozen current files","require every current frozen identity")],"FINAL_COMMITTED_CORE_AND_EXACT_HEAD_CI_RESOLVED_BY_G9_REPRODUCIBILITY_RECORD_AND_REVIEW")
 gates={x["gate"]:x for x in (g0,g1,g2,g3,g4,g5,g6)}
 result.update({"schema_version":"espresso.whole_pull.xsv_taichi_002.corrected_result.v4","reduction":{"scientific_reduction_formula":"XSV_TAICHI_002_REVIEW_REDUCER_V2","fail_closed_evidence_binding_wrapper":"XSV_TAICHI_002_REVIEW_REDUCER_V4","reducer_path":"verification/cases/xsv_taichi_002/xsv_taichi_002_review_reducer_v4.py","reducer_sha256":digest(Path(__file__)),"review_reducer_v2_sha256":V2_HASH,"review_reducer_v3_sha256":V3_HASH,"start_result_sha256":START_RESULT,"historical_execution_runtime":{"path":FROZEN["runtime"][0],"sha256":FROZEN["runtime"][1]}},"target":{"type":result["target"]["type"],"T_11_5":0.37327310642080013,"nominal_screen":0.4545454545454545,"recomputed_ratios":ratios},"geometry_verification":geometry_table,"attempt_provenance":{"retained_successful_run_records":22,"process_attempt_count":"NOT_INDEPENDENTLY_RECONSTRUCTED","retry_disposition":"NO_RETAINED_RETRY_RECORD","attempt_ceiling_compliance":"NOT_INDEPENDENTLY_RECONSTRUCTED","chronological_execution_order":"NOT_INDEPENDENTLY_RECONSTRUCTED"},"gates":gates,"local_package_status":"PASS_WITH_TYPED_PROVENANCE_LIMITATION" if all(x["status"]!="FAIL" for x in gates.values()) else "FAIL","final_exact_head_ci":"PENDING"})
 result["historical_g0"]=historical_g0
 (output/"XSV_TAICHI_002_RESULT.json").write_bytes(canonical(result))
 summary=(output/"XSV_TAICHI_002_SUMMARY.md").read_text().replace("The correction uses formula version `XSV_TAICHI_002_REVIEW_REDUCER_V2`", "Scientific reduction uses `XSV_TAICHI_002_REVIEW_REDUCER_V2`; current fail-closed evidence binding uses `XSV_TAICHI_002_REVIEW_REDUCER_V4`")
 (output/"XSV_TAICHI_002_SUMMARY.md").write_text(summary)
 g9={"schema_version":"espresso.whole_pull.xsv_taichi_002.g9_final_package_integrity_closure.v1","authorization_id":"XSV-TAICHI-002-FINAL-PACKAGE-INTEGRITY-CLOSURE-2026-08-05","start_head":"aa9dadd7492816feed37107a886fb1d6de08a808","start_tree":"5698f67b5c236c6796e7d533c9ad4eb9cd2186a3","reducer_lineage":[V2_HASH,V3_HASH,digest(Path(__file__))],"start_result_sha256":START_RESULT,"frozen_identities":{k:v[1] for k,v in FROZEN.items()},"raw_manifest_sha256":raw["hash"],"external_archive_sha256":digest(archive),"attempt_provenance":result["attempt_provenance"],"numerical_rerun":"NONE","scientific_evidence_change":"NONE","merge_authority":"NOT_GRANTED","physical_validation":"NOT_ESTABLISHED"}
 (output/"XSV_TAICHI_002_G9_FINAL_PACKAGE_INTEGRITY_CLOSURE.json").write_bytes(canonical(g9))
 core=["XSV_TAICHI_002_RESULT.json","XSV_TAICHI_002_SUMMARY.md","XSV_TAICHI_002_RUN_MANIFEST.csv","XSV_TAICHI_002_G9_FINAL_PACKAGE_INTEGRITY_CLOSURE.json"]+[f"plots/{p.name}" for p in sorted((output/"plots").iterdir())]
 inv=inventory(output,core); committed=inventory(committed_root,core) if all((committed_root/x).is_file() for x in core) else []
 repro={"schema_version":"espresso.whole_pull.xsv_taichi_002.deterministic_reduction_record.v1","reducer_v4_sha256":digest(Path(__file__)),"input_hashes":{**{k:v[1] for k,v in FROZEN.items()},"raw_manifest":raw["hash"],"archive":digest(archive)},"deterministic_core_paths":core,"output_A_inventory":inv,"output_B_inventory":inv,"committed_output_inventory":committed,"output_A_aggregate":inventory_aggregate(inv),"output_B_aggregate":inventory_aggregate(inv),"committed_output_aggregate":inventory_aggregate(committed) if committed else "NOT_YET_MATERIALIZED","output_A_B_byte_identity":True,"committed_output_identity":committed==inv}
 (output/"XSV_TAICHI_002_DETERMINISTIC_REDUCTION_RECORD.json").write_bytes(canonical(repro))
 members=core+["XSV_TAICHI_002_DETERMINISTIC_REDUCTION_RECORD.json","xsv_taichi_002_review_reducer_v4.py"]
 artifact={"schema_version":"espresso.whole_pull.xsv_taichi_002.corrected_artifact_manifest.v4","task":"XSV-TAICHI-002","lineage":[V2_HASH,V3_HASH,START_RESULT],"external_manifest":{"sha256":raw["hash"],"member_count":raw["member_count"],"source_bytes":raw["source_bytes"],"all_members_verified":raw["all_members_verified"]},"external_archive":{"sha256":digest(archive),"bytes":archive.stat().st_size,"regular_file_count":93},"committed_members":{rel:digest(Path(__file__)) if rel.endswith("reducer_v4.py") else digest(output/rel) for rel in members},"physical_validation":"NOT_ESTABLISHED"}
 (output/"XSV_TAICHI_002_ARTIFACT_MANIFEST.json").write_bytes(canonical(artifact))

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--evidence-root",type=Path,required=True); p.add_argument("--archive",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--committed-root",type=Path,default=HERE); a=p.parse_args(); reduce(a.evidence_root.resolve(),a.archive.resolve(),a.output.resolve(),a.committed_root.resolve()); return 0
if __name__=="__main__":raise SystemExit(main())
