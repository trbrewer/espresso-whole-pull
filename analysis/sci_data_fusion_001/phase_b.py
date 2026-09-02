import csv,json,hashlib
from pathlib import Path
from .compatibility import reduce_component
from .constraints import narrowing
from .decision import reduce_overall
from .extraction import extract_supports
from .lineage import pair_independence
from .closeout import apply as apply_closeout
def dump(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
def csv_dump(path,rows,fields):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader()
        for row in rows:writer.writerow({key:json.dumps(row.get(key),sort_keys=True) if isinstance(row.get(key),(list,dict)) else row.get(key) for key in fields})
def execute(root:Path,output:Path,fixture=None):
    config=fixture or json.loads((root/"analysis/sci_data_fusion_001/execution_plan.json").read_text());inventory=config.get("inventory") or json.loads((root/"docs/analysis/sci_data_fusion_001/SOURCE_SUPPORT_INVENTORY.json").read_text())["records"];rules=config.get("extraction_rules") or json.loads((root/"docs/analysis/sci_data_fusion_001/SUPPORT_EXTRACTION_RULES.json").read_text())["rules"]
    supports=inventory if fixture else extract_supports(root,rules,inventory);contracts=config["pairwise_gate_contracts"];baselines=config["baselines"];quantities=sorted({item["canonical_quantity_id"] for item in supports if item.get("canonical_quantity_id")});components=[];compat_rows=[];lineage_rows=[]
    for quantity in quantities:
        component=reduce_component(quantity,supports,contracts,baselines[quantity]);component["narrowing"]=narrowing(component.get("common_support"),baselines[quantity]);component["narrowing_status"]=component["narrowing"]["narrowing_status"];components.append(component);compat_rows.extend(component.get("compatibility_findings",[]));eligible=[item for item in supports if item.get("canonical_quantity_id")==quantity and item.get("frozen_role")=="COMMON_CONSTRAINT_CANDIDATE"]
        for i,left in enumerate(eligible):
            for right in eligible[i+1:]:lineage_rows.append(pair_independence(left,right))
    uncertainties=[{"support_id":item["support_id"],"statistic":item.get("uncertainty_statistic"),"replicate_unit":item.get("replicate_unit"),"numeric_combination":"PROHIBITED"} for item in supports if item.get("uncertainty_statistic")];decision=reduce_overall(components);output.mkdir(parents=True,exist_ok=True)
    csv_dump(output/"LINEAGE_INDEPENDENCE_MATRIX.csv",lineage_rows,["left_support_id","right_support_id","gates","independent_for_common_constraint","context_roles_preserved"]);csv_dump(output/"COMPATIBILITY_MATRIX.csv",compat_rows,["left_support_id","right_support_id","gates","failed_gates","unknown_gates","terminal_compatibility"]);dump(output/"COMPONENT_CONSTRAINTS.json",{"components":components});dump(output/"UNCERTAINTY_SUPPORTS.json",{"records":uncertainties,"numeric_combination_rule":"NONE_AUTHORIZED"});dump(output/"EWP_BASELINE_REGISTER.json",baselines);csv_dump(output/"EWP_CONSTRAINT_EFFECTS.csv",[],["quantity_id","observable","effect","propagation_status"]);dump(output/"DECISION.json",decision);dump(output/"summary.json",decision)
    (output/"RESULT.md").write_text(f"# SCI-DATA-FUSION-001 result\n\n`{decision['disposition']}`\n\nCross-corpus component evidence only. No production adoption or physical validation.\n");(output/"REPRODUCTION.md").write_text("# Reproduction\n\nRun the audited execute operation with exact frozen authorities.\n");artifacts=[]
    for path in sorted(output.iterdir()):
        if path.name!="RESULT_ARTIFACT_MANIFEST.json" and path.is_file():artifacts.append({"path":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    dump(output/"RESULT_ARTIFACT_MANIFEST.json",{"artifacts":artifacts})
    if fixture is None:apply_closeout(root,decision,hashlib.sha256((output/"RESULT_ARTIFACT_MANIFEST.json").read_bytes()).hexdigest())
    return decision
