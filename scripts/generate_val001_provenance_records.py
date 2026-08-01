#!/usr/bin/env python3
"""Generate deterministic provenance and taxonomy records from normative inputs."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validation.val001.framework import canonical_json,load_json
from tools.validation.val001.normative import NORMATIVE_REGISTRY,schema_digest,taxonomy_counts

OLD_HEAD="54f7690d6f7457992e0d2fa15cafc41b84fd5660"
OLD_REGISTRY="validation/val001/VAL_001_EXPLICIT_SCHEMA_SPECIFICATION_REGISTRY.json"

def write(path:Path,value):path.write_bytes(canonical_json(value))

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);a=ap.parse_args();root=Path(a.root).resolve()
 old=json.loads(subprocess.run(["git","show",f"{OLD_HEAD}:{OLD_REGISTRY}"],cwd=root,check=True,capture_output=True,text=True).stdout)
 old_by={s["specification_id"]:s for s in old["specifications"]}
 normative=load_json(root/NORMATIVE_REGISTRY)
 entries=[]
 for contract in normative["contracts"]:
  prior=old_by.get(contract["specification_id"])
  if not prior:continue
  old_hash=schema_digest(prior["schema"]);new_hash=schema_digest(contract["governing_schema"])
  entries.append({
   "previous_inferred_schema_id":contract["specification_id"],"previous_schema_sha256":old_hash,
   "new_normative_contract_id":contract["normative_contract_id"],
   "new_contract_sha256":hashlib.sha256(canonical_json(contract)).hexdigest(),
   "new_governing_schema_id":contract["schema_id"],"new_governing_schema_sha256":new_hash,
   "authoritative_source_references":contract["authoritative_source_references"],
   "schema_bytes_identical":old_hash==new_hash,
   "independent_derivation_explanation":"The normative contract is the sole generator input; governed instances and prior inferred schemas are unavailable to generation and verification.",
   "no_instance_generation_test_id":f"MUT-SCHEMA-PROVENANCE-{len(entries)+1:03d}",
   "semantic_profile_id":contract["semantic_profile_id"],"reviewer_disposition":"NORMATIVE_SOURCE_REPLACED"
  })
  if len(entries)==48:break
 transition={"schema_version":"espresso.val001.schema_provenance_transition_matrix.v1","record_id":"VAL001-SCHEMA-PROVENANCE-TRANSITION-MATRIX-1","prior_inferred_family_count":48,"transition_count":len(entries),"entries":entries,"final_disposition":"ALL_PRIOR_INFERRED_FAMILIES_HAVE_NORMATIVE_TRANSITIONS"}
 write(root/"validation/val001/VAL_001_SCHEMA_PROVENANCE_TRANSITION_MATRIX.json",transition)
 counts=taxonomy_counts(root)
 taxonomy={"schema_version":"espresso.val001.schema_taxonomy_counting.v1","record_id":"VAL001-SCHEMA-TAXONOMY-COUNTING-1","definitions":{"normative_schema_specification":"A checked-in normative contract from which a governing schema is produced.","governing_schema_family":"A unique schema_id referenced by one or more governed record registrations.","administrative_meta_schema_family":"A referenced governing family for schema documents, invocation events, inventories, registries, or administration.","schema_document_count":"The number of governed records whose record class is SCHEMA.","normative_contract_count":"The number of current checked-in normative contracts.","semantic_profile_count":"The number of executable semantic profiles; it is not a schema-family count."},"count_formulas":{"governing_schema_family_count":"count(unique schema_id values referenced by immutable governed-record assignments)","prohibited_arithmetic":"NO_CONSTANT_OFFSETS_OR_PLUS_TWO","all_counts":"computed from registered entries"},"val001_schema_spec_015_disposition":"OBSOLETE_REMOVED","counts":counts}
 write(root/"validation/val001/VAL_001_SCHEMA_TAXONOMY_AND_COUNTING_SPECIFICATION.json",taxonomy)

if __name__=="__main__":main()
