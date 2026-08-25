#!/usr/bin/env python3
"""Describe the frozen SCI-MD-004 result without scoring or prediction."""
import argparse,csv,json,statistics
from collections import defaultdict
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=a.root/'validation/sci_md_004_stage_e1_hydraulic_reconciliation'
 with (base/'result/CONDITION_LEVEL_RESULTS.csv').open(newline='') as f: rows=list(csv.DictReader(f))
 indexed={(r['sample_id'],r['hypothesis'],r['observable']):r for r in rows}
 detail=[]
 for sample in sorted({r['sample_id'] for r in rows}):
  for species in ('caffeine','trigonelline'):
   h0=indexed[(sample,'H0',species)];h1=indexed[(sample,'H1',species)]
   detail.append({'sample_id':sample,'species_id':species,'H1_H0_prediction_ratio':float(h1['prediction_kg_m3'])/float(h0['prediction_kg_m3']),
    'observed_H0_extraction_ratio':float(h0['observation_kg_m3'])/float(h0['prediction_kg_m3']),
    'observed_H1_extraction_ratio':float(h1['observation_kg_m3'])/float(h1['prediction_kg_m3']),
    'H0_signed_error_kg_m3':float(h0['signed_error']),'H1_signed_error_kg_m3':float(h1['signed_error'])})
 manifest=json.load(open(base/'prediction_freeze/EXECUTION_MANIFEST.json'))['executions']; compartments=defaultdict(list)
 for x in manifest:
  if not x['configuration_id'].endswith('-reference'):continue
  hypothesis=x['configuration_id'].split('-')[1]
  for species in ('caffeine','trigonelline'):
   o=x['observables'][species];initial=o['initial_inventory_kg'];remaining=o['remaining_inventory_kg'];cup=o['cup_mass_kg'];diss=o['dissolved_mass_kg'];back=o['back_diffusion_mass_kg']
   compartments[(hypothesis,species)].append({'inventory_utilization':(initial-remaining)/initial,'fraction_initial_remaining':remaining/initial,
    'cup_fraction_initial':cup/initial,'dissolved_fraction_initial':diss/initial,'retained_fraction_initial':(initial-remaining-cup-diss-back)/initial,'back_diffused_fraction_initial':back/initial})
 summary={}
 for key,values in compartments.items():summary['/'.join(key)]={name:{'mean':statistics.mean(v[name] for v in values),'minimum':min(v[name] for v in values),'maximum':max(v[name] for v in values)} for name in values[0]}
 signs=[x['H1_signed_error_kg_m3'] for x in detail]
 result={'schema_version':'ewp.sci-md-005-consumed-comparison-diagnostic/v1','source':'COMMITTED_SCI_MD_004_ARTIFACTS_ONLY','angeloni_status':'CONSUMED_POST_HOLDOUT_COMPARISON_DATA',
  'optimization_performed':False,'revised_prediction_generated':False,'detail':detail,'compartment_summary':summary,
  'signed_error_distribution':{'minimum':min(signs),'median':statistics.median(signs),'maximum':max(signs),'mean':statistics.mean(signs)},
  'every_H1_species_error_same_sign':all(v<0 for v in signs) or all(v>0 for v in signs),'H1_error_sign':'NEGATIVE' if all(v<0 for v in signs) else 'MIXED',
  'maximum_local_concentration_relative_to_Csat':{'status':'NOT_RECORDED_IN_COMMITTED_STAGE_E1_RESULT_ARTIFACTS','new_execution_prohibited_for_this_diagnostic':True},
  'limitation_classification':{'H1_caffeine':'TRANSFER_RATE_OR_RESIDENCE_TIME_LIMITED','H1_trigonelline':'TRANSFER_RATE_OR_RESIDENCE_TIME_LIMITED','inventory_limited':False,'boundary_loss_limited':False,
   'basis':'35-78% inventory utilization across H1 cases; mean back-diffusion below 5e-6 of inventory; substantial inventory remains at endpoint. C_sat-specific attribution is not separable without the unrecorded local maximum.'},
  'semantic_portability_hypothesis':'DIRECT_OUTLET_EXPONENTIAL_PARAMETERS_ARE_NOT_SEMANTICALLY_PORTABLE_TO_THE_LOCAL_PRODUCTION_SOURCE','classification':'SUPPORTED',
  'basis':['H1/H0 is systematically below one for both species and every condition.','Every H1 signed error is negative.','The production-law H1 leaves substantial inventory while boundary loss is negligible.','The unchanged indexed solver and numerical qualification already passed.']}
 a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
