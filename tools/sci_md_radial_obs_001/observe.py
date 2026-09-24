"""Read-only annular observations of exactly the retained 010 base snapshots."""
import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_010 import sections as historical
from tools.sci_md_rheology_010.common import ROOT, LIMITS, TRACE, sha, read
from tools.sci_md_004_stage_c.compare import scalar_internal_values

DOC=ROOT/'docs/analysis/sci_md_radial_obs_001'


def annular_weights(lo,hi,cuts):
    lo,hi,cuts=[np.asarray(x,dtype=float) for x in (lo,hi,cuts)]
    if lo.ndim!=1 or lo.size==0 or lo.shape!=hi.shape or cuts.ndim!=1 or cuts.size<2:
        raise ValueError('partition shape')
    if not all(np.isfinite(x).all() for x in (lo,hi,cuts)) or np.any(lo<0) or np.any(hi<=lo) or np.any(np.diff(cuts)<=0):
        raise ValueError('partition bounds')
    if lo.min()<cuts[0]-1e-12 or hi.max()>cuts[-1]+1e-12:raise ValueError('uncovered cells')
    a=np.maximum(lo[None,:],cuts[:-1,None]);b=np.minimum(hi[None,:],cuts[1:,None])
    w=np.where(b>a,(b*b-a*a)/(hi*hi-lo*lo),0)
    if np.max(abs(w.sum(axis=0)-1))>1e-12:raise ValueError('partition closure')
    return w


def integrate(volume,weights,remaining,concentration,porosity,saturation,dose,initial,rho):
    v,w,r,c,p,s=[np.asarray(x,dtype=float) for x in (volume,weights,remaining,concentration,porosity,saturation)]
    if v.ndim!=1 or not v.size or w.ndim!=2 or w.shape[1]!=v.size or any(x.shape!=v.shape for x in (r,c,p,s)):
        raise ValueError('field shape')
    if not all(np.isfinite(x).all() for x in (v,w,r,c,p,s)) or not np.isfinite([dose,initial,rho]).all():raise ValueError('nonfinite')
    if not 0<initial<=dose or rho<=0 or np.any(v<=0) or np.any(w<0) or np.max(abs(w.sum(axis=0)-1))>1e-12:raise ValueError('inventory/partition bounds')
    if np.any(r<0) or np.any(c<0) or np.any(c>LIMITS['c_max_kg_m3']) or np.any(p<=0) or np.any(p>=1) or np.any(s<0) or np.any(s>1):raise ValueError('field bounds')
    i=initial*v/v.sum()
    if np.any(r*v-i>LIMITS['field_mass_kg']):raise ValueError('remaining exceeds initial')
    cells=dict(initial_dry_coffee_kg=dose*v/v.sum(),initial_model_soluble_kg=i,
               remaining_solid_soluble_kg=r*v,retained_dissolved_solute_kg=p*s*c*v,
               retained_solvent_kg=rho*p*s*v,solid_depletion_kg=i-r*v)
    result={k:w@x for k,x in cells.items()}
    closure={k:float(result[k].sum()-x.sum()) for k,x in cells.items()}
    if max(abs(x) for x in closure.values())>1e-12:raise ValueError('inventory closure')
    return [dict((k,float(x[j])) for k,x in result.items()) for j in range(w.shape[0])],closure


def load_assay(root):
    path=root/'puckworks/analysis/pocketscience2024_assay.py'
    freeze=json.loads((DOC/'CONTRACT.json').read_text())
    if sha(path)!=freeze['puckworks_assay_sha256']:raise ValueError('analysis code identity changed')
    spec=importlib.util.spec_from_file_location('radial_source_assay',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def scenario_masses(scenario):
    bed=scenario['coffee_bed'];dose=bed['dry_dose_kg'];initial=dose*bed['initial_extractable_fraction_dry_basis'];rho=scenario['liquid']['density_kg_m3']
    if (dose,bed['initial_extractable_fraction_dry_basis'],rho)!=(.020,.28,965.):raise ValueError('scenario mass convention changed')
    return dose,initial,rho


def observation(case,scenario,expected,assay):
    # Compare all inputs to accepted historical section receipt before integrating.
    final=case/'30'
    for name,h in expected['field_sha256'].items():
        if sha(final/name)!=h:raise ValueError('stored field identity '+name)
    for name,h in expected['mesh_sha256'].items():
        if sha(case/'constant/polyMesh'/name)!=h:raise ValueError('mesh identity '+name)
    if sha(case/TRACE)!=expected['trace_sha256'] or sha(case.parent/'scenario.json')!=expected['scenario_sha256']:raise ValueError('trace/scenario identity')
    v,lo,hi=historical.geometry(case)
    fields=[]
    for name in ('remainingExtractable','dissolvedConcentration','porosity','saturation'):
        text=(final/name).read_text();dim=[1,-3,0,0,0,0,0] if len(fields)<2 else [0]*7
        if historical.field_dimensions(text)!=dim:raise ValueError('field dimensions '+name)
        fields.append(scalar_internal_values(final/name,cell_count=len(v)))
    dose,initial,rho=scenario_masses(scenario)
    # Demonstrate three-region parity on the actual historical case first.
    hw=annular_weights(lo,hi,historical.CUTS)
    if np.max(abs(hw-historical.section_weights(lo,hi)))>1e-12:raise ValueError('historical weight parity')
    old=historical.inventories(v,hw,*fields);generic,_=integrate(v,hw,*fields,dose,initial,rho)
    aliases=dict(initial_model_soluble_kg='initial_extractable_kg',remaining_solid_soluble_kg='remaining_solid_solubles_kg')
    parity=0.
    for new,previous in zip(generic,old['sections'].values()):
        for k,x in new.items():
            if k!='retained_solvent_kg':parity=max(parity,abs(x-previous[aliases.get(k,k)]))
    if parity>1e-12:raise ValueError('historical observer parity')
    # Also compare to retained published historical values, not just helper code.
    for name,previous in old['sections'].items():
        for k,x in previous.items():
            tolerance=1e-10 if k.endswith('dry') else 1e-12
            if abs(x-expected['sections'][name][k])>tolerance:raise ValueError('retained historical section parity')
    trace=read(case/TRACE);idx=np.flatnonzero(abs(trace['end_s']-30)<=LIMITS['clock_end_s'])
    if len(idx)!=1:raise ValueError('native clock')
    j=int(idx[0]);whole=old['whole_domain']
    for k,col in [('remaining_solid_solubles_kg','remaining_kg'),('retained_dissolved_solute_kg','stored_solute_kg')]:
        if abs(whole[k]-trace[col][j])>LIMITS['field_mass_kg']:raise ValueError('native mass agreement')
    residual=initial-whole['remaining_solid_solubles_kg']-whole['retained_dissolved_solute_kg']-trace['solute_kg'][j]-trace['inlet_loss_kg'][j]
    if abs(residual)>LIMITS['solute_balance_kg']:raise ValueError('global solute closure')
    # Native solvent convention: rho*water volume; beverage adds native solute.
    cup_solute=float(trace['solute_kg'][j]);cup_water=float(trace['water_kg'][j])
    results=[]
    radius=scenario['geometry']['basket_radius_m']
    for q in (.31,.34):
        cuts=[0,radius*np.sqrt(1-q),radius];w=annular_weights(lo,hi,cuts)
        regions,closure=integrate(v,w,*fields,dose,initial,rho)
        states=tuple(assay.CompartmentState(**{k:x for k,x in r.items() if k!='solid_depletion_kg'}) for r in regions)
        models={}
        for sheet in ('Sworks High Flow','VST18'):
            for survival in (1.,0.):
                # Deliberately synthetic retention: 0, not the source's post-flush LRR.
                p=assay.RecoveryProtocol(1,1,survival,1,1,1,20,0,assay.SourceProtocol(sheet,q,0))
                f=assay.forward_assay(states,p,assay.AnchorPolicy(cup_water+cup_solute,cup_solute,'MODEL_DERIVED'))
                models[sheet+('_retain_pore_solute' if survival else '_remove_pore_solute')]=asdict(f)
        normalized=lambda key:100*(regions[1][key]/regions[1]['initial_dry_coffee_kg']-regions[0][key]/regions[0]['initial_dry_coffee_kg'])
        results.append(dict(q=q,cuts_m=cuts,role='SYNTHETIC_INITIAL_MASS_PARTITION_SOURCE_INSPIRED_ONLY',regions=regions,
            solid_depletion_edge_minus_center_pp=normalized('solid_depletion_kg'),
            retained_dissolved_edge_minus_center_pp=normalized('retained_dissolved_solute_kg'),
            composite_R_plus_L_edge_minus_center_pp=normalized('remaining_solid_soluble_kg')+normalized('retained_dissolved_solute_kg'),
            forward_models=models,source_qualified_prediction='NOT_ESTABLISHED',
            undefined_source_inputs=['actual drainage and handling','recovery efficiencies','source coffee inventory and regional initial mass','measured-shot anchor (not used)','plotting/MC algorithm'],
            closure_kg=closure,partial_cells=[int(np.sum((x>1e-12)&(x<1-1e-12))) for x in w]))
    return dict(partitions=results,historical_parity_max_kg=parity,global_solute_closure_kg=float(residual),
                field_sha256=expected['field_sha256'],mesh_sha256=expected['mesh_sha256'],trace_sha256=expected['trace_sha256'],scenario_sha256=expected['scenario_sha256'],
                radial_cells=scenario['geometry']['radial_cells'],retained_solvent_convention='965 kg/m3 times pore-water volume; solute separate',
                resolution_caveat='PIECEWISE_CONSTANT; E2 OUTER SUBCELL STRUCTURE UNRESOLVED')


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--puckworks',type=Path,required=True);a=p.parse_args()
    contract=json.loads((DOC/'CONTRACT.json').read_text());audit=json.loads((DOC/'AUDIT.json').read_text())
    if audit['status']!='PASS' or audit['contract_sha256']!=sha(DOC/'CONTRACT.json'):raise ValueError('exact independent pre-analysis audit required')
    for name,h in contract['code_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen observer changed '+name)
    for name,h in contract['retained_receipt_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen historical input changed '+name)
    assay=load_assay(a.puckworks)
    from .prepare import retained_cases
    cases,missing=retained_cases(a.artifacts)
    expected=json.loads((ROOT/'docs/analysis/sci_md_rheology_010/SECTIONS.json').read_text())['cases']
    identities={k:{x:v[x] for x in contract['field_set'][k]} for k,v in expected.items()}
    if identities!=contract['field_set']:raise ValueError('frozen field set changed')
    results={}
    for key,(case,scenario) in cases.items():
        try:results[key]=observation(case,scenario,expected[key],assay)
        except (OSError,ValueError,KeyError) as e:missing[key]=str(e).replace(str(case.parent),'<retained-case-parent>')
    comparisons=[]
    for key,c in results.items():
        if '_C_' not in key:continue
        other=results.get(key.replace('_C_','_E2_'))
        if not other:continue
        for x,y in zip(c['partitions'],other['partitions']):
            row=dict(case_pair=key,q=x['q'],sign='E2 minus C',solid_depletion_contrast_difference_pp=y['solid_depletion_edge_minus_center_pp']-x['solid_depletion_edge_minus_center_pp'],composite_contrast_difference_pp=y['composite_R_plus_L_edge_minus_center_pp']-x['composite_R_plus_L_edge_minus_center_pp'])
            row['apparent_contrast_difference_pp']={k:100*(y['forward_models'][k]['assay']['edge_minus_center_fraction']-x['forward_models'][k]['assay']['edge_minus_center_fraction']) for k in x['forward_models']}
            comparisons.append(row)
    result=dict(EWP_FIELD_DIAGNOSTIC='COMPLETE' if len(results)==16 and not missing else 'PARTIAL',
                FORWARD_ASSAY_MAP='CONDITIONAL',PHYSICAL_VALIDATION='NOT_ESTABLISHED',NEW_NATIVE_INTEGRATIONS=0,NEW_NATIVE_BUILDS=0,PRODUCTION_DEFAULTS_AND_LOCK='UNCHANGED',
                cases=results,missing=missing,paired_differences=comparisons,contract_sha256=sha(DOC/'CONTRACT.json'),historical_old_E2='RETAINED_DIAGNOSTIC_ONLY')
    (DOC/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['EWP_FIELD_DIAGNOSTIC'],len(results),'cases',2*len(results),'partitions')

if __name__=='__main__':main()
