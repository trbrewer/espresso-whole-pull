import json
from pathlib import Path
def json_path(value:object,path:list[object])->object:
    current=value
    for part in path:current=current[part] # type: ignore[index]
    return current
def extract_supports(root:Path,rules:list[dict],inventory:list[dict])->list[dict]:
    by_id={row["support_id"]:dict(row) for row in inventory}
    for rule in rules:
        record=by_id[rule["support_id"]]; document=json.loads((root/rule["artifact_path"]).read_text()); lo=json_path(document,rule["minimum_json_path"]); hi=json_path(document,rule["maximum_json_path"])
        if not isinstance(lo,(int,float)) or not isinstance(hi,(int,float)) or lo>hi:raise ValueError(f"invalid extracted interval for {rule['support_id']}")
        record["interval"]=[float(lo)*rule["unit_scale"],float(hi)*rule["unit_scale"]]; record["interval_semantics"]=rule["interval_semantics"]; record["source_ids"]=[record["support_id"]]
    return [by_id[key] for key in sorted(by_id)]
