#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=a.root/'validation/sci_md_004_stage_e1_hydraulic_reconciliation'
 with (base/'prediction_freeze/PREDICTIONS.csv').open(newline='') as f: rows=list(csv.DictReader(f))
 idx={(r['sample_id'],r['hypothesis'],r['observable']):r for r in rows}; detail=[]
 for sample in sorted({r['sample_id'] for r in rows}):
  scenario=json.loads((base/f'scenarios/{sample}-H0-reference.json').read_text());dose=scenario['coffee_bed']['dry_dose_kg']
  total=idx[(sample,'H0','total_solids')]; aggregate_fraction=float(total['cup_mass_kg'])/(dose*.28)
  for item in scenario['extraction']['species']:
   if item['id'] not in ('caffeine','trigonelline'):continue
   frozen=float(idx[(sample,'H0',item['id'])]['cup_mass_kg']); inventory=dose*item['dry_coffee_inventory_mass_fraction']; actual=frozen/inventory
   common=inventory*aggregate_fraction
   detail.append({'sample_id':sample,'species_id':item['id'],'frozen_species_extracted_fraction':actual,'aggregate_legacy_extracted_fraction':aggregate_fraction,
    'fraction_difference':actual-aggregate_fraction,'frozen_cup_mass_kg':frozen,'common_closure_cup_mass_kg':common,'cup_mass_difference_kg':frozen-common})
 exact=all(x['cup_mass_difference_kg']==0 for x in detail)
 result={'schema_version':'ewp.sci-md-005-h0-contract-audit/v1','frozen_case_count':len({x['sample_id'] for x in detail}),'comparison_count':len(detail),
  'exact_reproduction':exact,'maximum_absolute_cup_mass_difference_kg':max(abs(x['cup_mass_difference_kg']) for x in detail),
  'maximum_extracted_fraction_difference':max(abs(x['fraction_difference']) for x in detail),'detail':detail,
  'disposition':'PASS' if exact else 'SCI_MD_005_TRAINING_DATA_CONTRACT_BLOCKED',
  'reason':'FROZEN_SCI_MD_004_H0_USED_A_COMMON_ABSOLUTE_CSAT_AND_DOES_NOT_HAVE_A_COMMON_INVENTORY_SCALED_EXTRACTION_FRACTION'}
 a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
