from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from tools.validation.val001.deep_schema import build_family_schema,governed_json_paths,semantic_validate
from tools.validation.val001.framework import ContractError,load_json,validate_record

ROOT=Path(__file__).resolve().parents[1]

def first_object(value):
 if isinstance(value,dict): return value
 if isinstance(value,list):
  for item in value:
   found=first_object(item)
   if found is not None:return found
 return None

def first_scalar_slot(value):
 if isinstance(value,dict):
  for key,item in value.items():
   if not isinstance(item,(dict,list)):return value,key,item
   found=first_scalar_slot(item)
   if found:return found
 if isinstance(value,list):
  for item in value:
   found=first_scalar_slot(item)
   if found:return found
 return None

class DeepSchemaCoverageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.schema,cls.mapping=build_family_schema(ROOT)
  cls.by_family={}
  for path in governed_json_paths(ROOT):cls.by_family.setdefault(cls.mapping[path.relative_to(ROOT).as_posix()],path)

 def test_every_family_rejects_missing_wrong_type_and_unknown_nested(self):
  for family,path in self.by_family.items():
   value=load_json(path)
   with self.subTest(family=family,mutation='required'):
    changed=copy.deepcopy(value);obj=first_object(changed);obj.pop(next(iter(obj)))
    with self.assertRaises(ContractError):validate_record(changed,self.schema)
   with self.subTest(family=family,mutation='wrong_type'):
    changed=copy.deepcopy(value);obj,key,old=first_scalar_slot(changed);obj[key]=0 if isinstance(old,str) else "WRONG_TYPE"
    with self.assertRaises(ContractError):validate_record(changed,self.schema)
   with self.subTest(family=family,mutation='unknown'):
    changed=copy.deepcopy(value);first_object(changed)['UNREGISTERED_NESTED_FIELD']=True
    with self.assertRaises(ContractError):validate_record(changed,self.schema)

 def test_claim_and_authority_escalations_fail_semantically(self):
  cases=[
   ('validation/val001/results/historical/WP01R_R1_WASZKIEWICZ_9BAR.json','NEW_SCORE_BEARING_COMPARISON',True),
   ('validation/val001/contracts/VAL_001_POSTRESULT_EXECUTION_LOCK.json','authority_status','AVAILABLE'),
  ]
  for rel,key,bad in cases:
   value=load_json(ROOT/rel);value[key]=bad
   with self.assertRaises(ContractError):semantic_validate(rel,value)

 def test_no_governed_source_is_opened(self):
  self.assertNotIn('WP03_001_SOURCE_PRESSURE_SWEEP.csv',json.dumps(sorted(self.mapping)))
