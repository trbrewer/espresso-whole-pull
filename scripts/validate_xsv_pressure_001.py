#!/usr/bin/env python3
"""Fail-closed validation of compact, source-bound production qualification evidence."""
from __future__ import annotations
import argparse, copy, difflib, hashlib, json, math, subprocess
from pathlib import Path
TASK='XSV-PRESSURE-001'
FROZEN_CONTRACT_SHA256={'MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.json': 'e1c3719da9e3a18ec32dec2c18f7d4167a3d03884b23250e08b4cfe4394cc070', 'MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.md': '6330a7369928008063ab76c166e6f50d31f77109b60565cf05701cb385a6ff2a'}
AUTHORIZED_EXISTING_PRODUCTION_DELTAS={'solver/espressoWholePullFoam/espressoWholePullFoam.C': 'f0cfcf39bafe9a1c88f87f0a14678b7c427a10d4a38a3b8f6ff7eb7d1c518768', 'scripts/prepare_case.py': '9a10f3e32c9a433725ebab7ea7d58e470c7916e034189a7f367eab8d812074df'}
SUCCESS='XSV_PRESSURE_001_NATIVE_PIECEWISE_LINEAR_PRESCRIBED_PRESSURE_HISTORY_QUALIFIED_READY_FOR_EXACT_HEAD_REVIEW'
FILES={'helper_reference_vectors_pass':'FUNCTION_LEVEL_VERIFICATION.json','legacy_constant_equivalence_pass':'LEGACY_CONSTANT_EQUIVALENCE.json',
'legacy_ramp_equivalence_pass':'LEGACY_RAMP_EQUIVALENCE.json','synthetic_profile_pass':'SYNTHETIC_PROFILE_QUALIFICATION.json',
'timestep_refinement_pass':'TIMESTEP_REFINEMENT.json','serial_mpi_equivalence_pass':'SERIAL_MPI_EQUIVALENCE.json',
'compaction_maximum_pressure_pass':'COMPACTION_MAXIMUM_PRESSURE_CHECK.json','invalid_contract_matrix_pass':'INVALID_CONTRACT_RESULTS.json'}
INVALID={'missing_dictionary','missing_type','unsupported_type','missing_times','missing_pressures','short','unequal','duplicate','decreasing','nonfinite_time','nonfinite_pressure','negative_pressure','start_coverage','end_coverage','scalar_target','scalar_ramp','history_in_legacy','before_support','after_support','unreachable'}
REGRESSIONS={'prescribedPressure','prescribedFlow_constant','prescribedFlow_piecewiseLinear','lumpedMachineCompliance','DarcyForchheimer','compaction','effective_permeability','fraction_collection','reference_completion'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def digest_ok(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)
def classify(g):
    groups=[(['contract_frozen','helper_reference_vectors_pass','schedule_validation_pass','invalid_contract_matrix_pass'],'MATHEMATICS'),
    (['legacy_constant_equivalence_pass','legacy_ramp_equivalence_pass'],'COMPATIBILITY'),
    (['synthetic_profile_pass','compaction_maximum_pressure_pass','bounded_state_pass','conservation_pass','production_case_completion_pass'],'PRODUCTION'),
    (['timestep_refinement_pass','serial_mpi_equivalence_pass'],'NUMERICAL'),
    (['legacy_prescribed_pressure_regression_pass','prescribed_flow_regression_pass','lumped_machine_regression_pass'],'REGRESSION')]
    names={'MATHEMATICS':'PRESSURE_HISTORY_MATHEMATICS','COMPATIBILITY':'LEGACY_PRESSURE_COMPATIBILITY','PRODUCTION':'PRODUCTION_HISTORY_QUALIFICATION','NUMERICAL':'NUMERICAL_APPLICATION','REGRESSION':'EXISTING_BOUNDARY_REGRESSION'}
    for keys,reason in groups:
        if any(g.get(k) is not True for k in keys):return 'XSV_PRESSURE_001_BLOCKED_'+names[reason]
    return SUCCESS if g and all(v is True for v in g.values()) else 'XSV_PRESSURE_001_STOP_AUTHORITY_MISMATCH'
def inspect(root,verify_result=True,verify_manifest=True):
    out=root/'validation/xsv_pressure_001';errors=[];g={}
    try:
        contract=load(out/'MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.json');receipt=load(out/'CONTRACT_RECEIPT.json')
        g['contract_frozen']=receipt['sha256']==FROZEN_CONTRACT_SHA256 and set(receipt['sha256'])=={'MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.md','MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.json'} and all(sha(out/k)==v for k,v in receipt['sha256'].items())
        g['contract_frozen'] &= contract['change_class']=='G2' and contract['production_behavior_change'] is True and contract['governing_equation_change'] is False and contract['governing_physics_change'] is False
        inventory=load(out/'SOURCE_USAGE_INVENTORY.json');g['source_usage_inventory_complete']=bool(inventory['tracked_occurrences']) and len(inventory['search_terms'])==9 and all(all(k in r for k in ('file','context','purpose','current_mode_applicability','must_remain_legacy_only','must_use_new_schedule_abstraction','planned_correction','verification_gate')) for r in inventory['tracked_occurrences'])
        for gate,file in FILES.items():g[gate]=load(out/file).get('pass') is True
        function=load(out/'FUNCTION_LEVEL_VERIFICATION.json');vectors=load(out/'REFERENCE_VECTORS.json')
        g['helper_reference_vectors_pass'] &= function['count']==len(vectors)>=17 and len(function['vectors'])==len(vectors) and all(v['pass'] is True and digest_ok(v['dictionary_sha256']) and v['output_sha256']==v['repeat_sha256'] for v in function['vectors'])
        for key,value in function['source_hashes'].items():
            if sha(root/key)!=value:errors.append('probe source mismatch '+key)
        for key,limit in [('target',1e-6),('crossing',1e-10),('maximum',1e-6)]:
            g['helper_reference_vectors_pass'] &= math.isfinite(function['maximum_errors'][key]) and function['maximum_errors'][key]<=limit
        g['helper_reference_vectors_pass'] &= function['maximum_errors']['integral']<=1e-6 or function['maximum_errors']['integral_relative']<=1e-12
        invalid=load(out/'INVALID_CONTRACT_RESULTS.json');g['invalid_contract_matrix_pass'] &= invalid['count']==20 and {v['id'] for v in invalid['cases']}==INVALID and all(v['exit_code']!=0 and v['pass'] is True and v['expected_token'].startswith('XSV_PRESSURE_001_') and digest_ok(v['log_sha256']) and digest_ok(v['input_sha256']) and digest_ok(v['executable_sha256']) for v in invalid['cases'])
        g['schedule_validation_pass']=g['invalid_contract_matrix_pass']
        execution=load(out/'EXECUTION_RECEIPT.json')
        if execution.get('contract_sha256')!=receipt['sha256']:errors.append('production run contract freeze mismatch')
        if execution.get('status')!='COMPLETE':errors.append('production execution not complete')
        runs=execution['production_runs'];runmap={r['case_id']:r for r in runs}
        if len(runmap)!=len(runs) or not runs:errors.append('missing/duplicate production runs')
        if not digest_ok(execution['executable_sha256']) or execution['openfoam_version']!='12':errors.append('binary/OpenFOAM identity absent')
        for key,value in execution['source_hashes'].items():
            if sha(root/key)!=value:errors.append('production source mismatch '+key)
        required={'solver/espressoWholePullFoam/espressoWholePullFoam.C','solver/espressoWholePullFoam/prescribedPressureBoundaryModel.H'}
        if not required<=execution['source_hashes'].keys():errors.append('missing production source binding')
        for r in runs:
            if not all(digest_ok(r.get(k)) for k in ('executable_sha256','schedule_sha256','log_sha256','trace_sha256','configuration_sha256')):errors.append('missing run identities '+r['case_id'])
            if not r['input_hashes'] or 'constant/espressoModelProperties' not in r['input_hashes'] or 'system/controlDict' not in r['input_hashes']:errors.append('missing generated inputs '+r['case_id'])
            if r['executable_sha256']!=execution['executable_sha256'] and not r['case_id'].endswith('_base'):errors.append('candidate binary mismatch '+r['case_id'])
        required_cases={'CONSTANT_legacy','CONSTANT_history','RAMP_legacy','RAMP_history','synthetic','synthetic_refined','synthetic_mpi','compaction_valid'}
        if not required_cases<=runmap.keys():errors.append('required actual production runs absent')
        g['production_case_completion_pass']=bool(runs) and all(r['completion_status']=='PASS' and r['end_time_s']>r['start_time_s'] and r['error'] is None for r in runs)
        g['bounded_state_pass']=bool(runs) and all(r['bounded_state_pass'] is True for r in runs)
        g['conservation_pass']=bool(runs) and all(r['conservation_pass'] is True and math.isfinite(r['maximum_water_residual_kg']) and r['maximum_water_residual_kg']<=1e-10 and math.isfinite(r['maximum_solute_residual_kg']) and r['maximum_solute_residual_kg']<=1e-10 for r in runs)
        for name in ['LEGACY_CONSTANT_EQUIVALENCE.json','LEGACY_RAMP_EQUIVALENCE.json','SERIAL_MPI_EQUIVALENCE.json']:
            data=load(out/name)
            if not data['normalized_final_field_linf'] or any(not math.isfinite(x) or x>1e-8 for x in data['normalized_final_field_linf'].values()):errors.append(name+' final field gate')
            if any(v['maximum_absolute']>v['limit'] for v in data['differences'].values()):errors.append(name+' scalar difference')
            if any(k not in runmap for k in data['cases']):errors.append(name+' no production receipt')
        time=load(out/'TIMESTEP_REFINEMENT.json')
        g['timestep_refinement_pass'] &= bool(time['normalized_final_field_linf']) and time['cup_relative_difference']<=.01 and time['mass_curve_nrmse']<=.02 and time['differences']['first_drip_s']['maximum_absolute']<=.1
        mpi=runmap.get('synthetic_mpi',{});g['serial_mpi_equivalence_pass'] &= mpi.get('rank_count')==4
        compact=load(out/'COMPACTION_MAXIMUM_PRESSURE_CHECK.json');g['compaction_maximum_pressure_pass'] &= compact['maximum_is_interior'] is True and compact['final_pressure_Pa']==0 and compact['invalid']['exit_code']!=0 and compact['invalid']['schedule'][1]>max(compact['invalid']['schedule'][0],compact['invalid']['schedule'][-1])
        reg=load(out/'EXISTING_MODE_REGRESSIONS.json');r=reg['comparisons']
        if set(r)!=REGRESSIONS or reg.get('remaining_required'):errors.append('incomplete existing-mode regression')
        g['legacy_prescribed_pressure_regression_pass']=r['prescribedPressure']['pass'] is True and r['reference_completion']['pass'] is True
        g['prescribed_flow_regression_pass']=all(r[k]['pass'] is True for k in ('prescribedFlow_constant','prescribedFlow_piecewiseLinear'))
        g['lumped_machine_regression_pass']=r['lumpedMachineCompliance']['pass'] is True
        if any(x['pass'] is not True for x in r.values()):errors.append('existing regression failure')
        # Scope is bound to the reviewed exact production delta and unchanged other production files.
        legacy_inputs=load(out/'LEGACY_INPUT_CONTRACT_EQUIVALENCE.json')
        if legacy_inputs['pass'] is not True or not legacy_inputs['cases'] or any(r['baseline_normalized_sha256']!=r['candidate_normalized_sha256'] for r in legacy_inputs['cases']):
            errors.append('legacy input contract changed')
        for path,expected in AUTHORIZED_EXISTING_PRODUCTION_DELTAS.items():
            original=subprocess.check_output(['git','show',contract['base_commit']+':'+path],cwd=root,text=True)
            delta='\n'.join(difflib.unified_diff(original.splitlines(),(root/path).read_text().splitlines(),n=0))
            if hashlib.sha256(delta.encode()).hexdigest()!=expected:errors.append('change outside frozen pressure boundary delta '+path)
        scope=load(out/'PRODUCTION_SCOPE.json')
        base=contract['base_commit']
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'solver'],cwd=root,text=True).splitlines()
        for path in paths:
            if path not in contract['permitted_production_paths']:
                original=subprocess.check_output(['git','show',base+':'+path],cwd=root)
                if (root/path).read_bytes()!=original:errors.append('prohibited production path changed '+path)
        original_source=subprocess.check_output(['git','show',base+':solver/espressoWholePullFoam/espressoWholePullFoam.C'],cwd=root,text=True)
        current_source=(root/'solver/espressoWholePullFoam/espressoWholePullFoam.C').read_text()
        if original_source[:original_source.index('int main(')] != current_source[:current_source.index('int main(')].replace('#include "prescribedPressureBoundaryModel.H"\n',''):
            errors.append('legacy mathematical helper equations changed')
        for k,h in scope['unchanged_production_sha256'].items():
            if sha(root/k)!=h:errors.append('prohibited production change '+k)
        for k,h in scope['authorized_candidate_sha256'].items():
            if sha(root/k)!=h:errors.append('unreviewed production delta '+k)
        g['no_governing_equation_change']=not errors and scope['governing_equation_change'] is False
        g['no_puckworks_change']=all(sha(root/k)==h for k,h in scope['dependency_sha256'].items())
        production='\n'.join((root/k).read_text() for k in scope['authorized_candidate_sha256'])
        g['no_visualizer_specific_production_code']=all(x not in production.lower() for x in ('visualizer','cohort 066','play-003','puckworks/','/home/'))
        if verify_result:
            result=load(out/'RESULT.json')
            if result['gates']!=g:errors.append('result gates differ from independently recomputed gates')
            if result['disposition']!=classify(g):errors.append('invalid success/failure classification')
        if verify_manifest:
            manifest=load(out/'ARTIFACT_MANIFEST.json')['sha256'];actual={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json'}
            if actual!=manifest:errors.append('artifact manifest drift/incomplete coverage')
    except (KeyError,ValueError,TypeError,OSError) as e:errors.append(str(e))
    if not g or any(v is not True for v in g.values()):errors.append('material required gate false/missing')
    return {'pass':not errors,'gates':g,'errors':errors,'disposition':classify(g)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path);p.add_argument('--declaration',type=Path);a=p.parse_args()
    report=inspect(a.root.resolve());text=json.dumps(report,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text,end='');return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
