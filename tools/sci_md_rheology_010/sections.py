"""Non-scoring virtual sections of stored native fields; never launches a solver."""
import argparse
import re
import numpy as np
from .common import DOC, ROOT, OLD, TRACE, LAWS, sha, write, read, LIMITS, verify_files
from .run import complete
from tools.sci_md_rheology_006.exchange import labels
from tools.sci_md_004_stage_c.compare import scalar_internal_values
from tools.sci_md_rheology_007.short import final_directory

CUTS=np.array([0.,.018,.025,.029])
NAMES=('centre_0_18mm','middle_18_25mm','outer_25_29mm')


def section_weights(lo,hi,cuts=CUTS):
    """Piecewise-constant cell fields, split by overlap of annular squared radii."""
    lo,hi,cuts=map(lambda x:np.asarray(x,dtype=float),(lo,hi,cuts))
    if lo.shape!=hi.shape or np.any(~np.isfinite(lo+hi)) or np.any(hi<=lo) or np.any(lo<0):
        raise ValueError('invalid radial extents')
    if len(cuts)!=4 or not np.isfinite(cuts).all() or np.any(np.diff(cuts)<=0):raise ValueError('invalid cuts')
    if min(lo)<cuts[0]-1e-12 or max(hi)>cuts[-1]+1e-12:raise ValueError('sections do not cover mesh')
    lower=np.maximum(lo[None,:],cuts[:-1,None]);upper=np.minimum(hi[None,:],cuts[1:,None])
    weights=np.where(upper>lower,(upper**2-lower**2)/(hi**2-lo**2),0.)
    if max(abs(weights.sum(axis=0)-1))>1e-12:raise ValueError('section closure')
    return weights


def geometry(case):
    """Actual oriented polyhedral volumes with inherited full-basket wedge scale."""
    pm=case/'constant/polyMesh';body=re.search(r'\n(\d+)\s*\(\s*(.*?)\n\)',(pm/'points').read_text(),re.S)
    points=np.array([list(map(float,s.split())) for s in re.findall(r'\(([^()]+)\)',body[2])])
    faces=[list(map(int,s.split())) for _,s in re.findall(r'(\d+)\(([^()]+)\)',(pm/'faces').read_text())]
    if any(len(f) not in (3,4) for f in faces):raise ValueError('unsupported non-tri/quad native face')
    owner=labels(pm/'owner');neighbour=labels(pm/'neighbour');n=int(max(owner.max(),neighbour.max())+1)
    vertices=points[np.array([f+[f[-1]]*(4-len(f)) for f in faces])]
    vv=np.zeros(len(faces))
    for j in (1,2):
        cross=np.cross(vertices[:,j]-vertices[:,0],vertices[:,j+1]-vertices[:,0])/2
        vv+=np.einsum('ij,ij->i',cross,(vertices[:,0]+vertices[:,j]+vertices[:,j+1])/3)/3
    scale=2*np.pi/np.sin(np.deg2rad(5))
    volume=(np.bincount(owner,weights=vv,minlength=n)-np.bincount(neighbour,weights=vv[:len(neighbour)],minlength=n))*scale
    radius=np.hypot(vertices[:,:,1],vertices[:,:,2]);rlo=radius.min(axis=1);rhi=radius.max(axis=1)
    lo=np.full(n,np.inf);hi=np.zeros(n);zlo=np.full(n,np.inf);zhi=np.full(n,-np.inf)
    for ids,limit in ((owner,len(owner)),(neighbour,len(neighbour))):
        np.minimum.at(lo,ids,rlo[:limit]);np.maximum.at(hi,ids,rhi[:limit])
        np.minimum.at(zlo,ids,vertices[:limit,:,0].min(axis=1));np.maximum.at(zhi,ids,vertices[:limit,:,0].max(axis=1))
    analytic=np.pi*(hi**2-lo**2)*(zhi-zlo)
    if np.any(volume<=0) or max(abs(volume/analytic-1))>LIMITS['geometry_relative']:
        raise ValueError('actual annular geometry mismatch')
    return volume,lo,hi


def inventories(volume,weights,remaining,concentration,porosity,saturation,dose=.020,initial=.0056):
    volume,weights,remaining,concentration,porosity,saturation=map(lambda x:np.asarray(x,dtype=float),(volume,weights,remaining,concentration,porosity,saturation))
    if weights.shape!=(3,len(volume)) or any(x.shape!=volume.shape for x in (remaining,concentration,porosity,saturation)):
        raise ValueError('field shape')
    if any(not np.isfinite(x).all() for x in (volume,weights,remaining,concentration,porosity,saturation)):
        raise ValueError('nonfinite fields')
    if np.any(volume<=0) or np.any(weights<0) or max(abs(weights.sum(axis=0)-1))>1e-12:raise ValueError('nonconservative sections')
    if np.any(remaining < -1e-10) or np.any(concentration < -1e-10) or np.any(porosity<=0) or np.any(porosity>=1) or np.any(saturation<0) or np.any(saturation>1):
        raise ValueError('field bounds')
    # Initial dry coffee is a declared uniform mass density, not a native field.
    initial_cell=initial*volume/volume.sum();dry_cell=dose*volume/volume.sum()
    solid=remaining*volume;liquid=porosity*saturation*concentration*volume
    if np.any(solid-initial_cell>LIMITS['field_mass_kg']):raise ValueError('solid inventory exceeds initial')
    values=dict(initial_dry_coffee_kg=dry_cell,initial_extractable_kg=initial_cell,
                remaining_solid_solubles_kg=solid,retained_dissolved_solute_kg=liquid,
                solid_depletion_kg=initial_cell-solid)
    sections={name:{} for name in NAMES};closure={}
    for k,x in values.items():
        summed=weights@x;closure[k]=float(summed.sum()-x.sum())
        if abs(closure[k])>1e-12:raise ValueError('whole-domain section closure')
        for name,value in zip(NAMES,summed):sections[name][k]=float(value)
    for row in sections.values():
        row['solid_depletion_percent_initial_dry']=100*row['solid_depletion_kg']/row['initial_dry_coffee_kg']
        row['retained_dissolved_percent_initial_dry']=100*row['retained_dissolved_solute_kg']/row['initial_dry_coffee_kg']
    return dict(sections=sections,whole_domain={k:float(x.sum()) for k,x in values.items()},closure_residuals_kg=closure)


def field_dimensions(text):
    """Foundation 12 writes dimensionless fields as [] (dimensionSet::write)."""
    dim=re.search(r'dimensions\s*\[([^]]*)\]',text)
    if not dim:raise ValueError('missing dimensions')
    values=list(map(float,dim[1].split()))
    if not values:return [0.]*7
    if len(values)!=7:raise ValueError('unsupported dimensions')
    return values


def observe(case,s,time=30.):
    volume,lo,hi=geometry(case);weights=section_weights(lo,hi);final=final_directory(case,time)
    values={};hashes={}
    for name in ('remainingExtractable','dissolvedConcentration','porosity','saturation'):
        p=final/name
        if not p.exists():raise ValueError('missing required stored field '+name)
        expected=[1,-3,0,0,0,0,0] if name in ('remainingExtractable','dissolvedConcentration') else [0]*7
        if field_dimensions(p.read_text())!=expected:raise ValueError('field units '+name)
        values[name]=scalar_internal_values(p,cell_count=len(volume));hashes[name]=sha(p)
    result=inventories(volume,weights,values['remainingExtractable'],values['dissolvedConcentration'],values['porosity'],values['saturation'])
    raw=read(case/TRACE);idx=np.flatnonzero(abs(raw['end_s']-float(final.name))<=LIMITS['clock_end_s'])
    if len(idx)!=1:raise ValueError('stored time has no unique native interval')
    j=int(idx[0]);whole=result['whole_domain']
    for field,col in [('remaining_solid_solubles_kg','remaining_kg'),('retained_dissolved_solute_kg','stored_solute_kg')]:
        if abs(whole[field]-raw[col][j])>LIMITS['field_mass_kg']:raise ValueError('native field conservation '+field)
    residual=.0056-whole['remaining_solid_solubles_kg']-whole['retained_dissolved_solute_kg']-raw['solute_kg'][j]-raw['inlet_loss_kg'][j]
    if abs(residual)>LIMITS['solute_balance_kg']:raise ValueError('global solute conservation')
    nr=s['geometry']['radial_cells']
    result.update(stored_time_s=float(final.name),field_sha256=hashes,trace_sha256=sha(case/TRACE),scenario_sha256=sha(case.parent/'scenario.json'),
        mesh_sha256={p.name:sha(p) for p in sorted((case/'constant/polyMesh').iterdir()) if p.is_file()},
        cells=len(volume),radial_cells=nr,partial_cells_per_section=[int(sum((w>1e-12)&(w<1-1e-12))) for w in weights],
        outlet_solute_whole_domain_kg=float(raw['solute_kg'][j]),inlet_solute_loss_kg=float(raw['inlet_loss_kg'][j]),
        global_balance_residual_kg=float(residual),regional_outlet_delivery='NOT_INFERRED_FROM_SECTION_INVENTORY',
        subcell_interpretation='UNRESOLVED_MIDDLE_AND_OUTER_SHARE_ONE_NATIVE_RADIAL_CELL' if nr==2 else 'PIECEWISE_CONSTANT_RESOLVED_C_FIELD_DIAGNOSTIC')
    return result


def main():
    import json
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=__import__('pathlib').Path,required=True);a=p.parse_args();art=a.artifacts
    accepted=__import__('pathlib').Path(json.loads((art/'LOCATIONS.json').read_text())['accepted'])
    receipt=json.loads((OLD/'ARTIFACT_RECEIPT.json').read_text())
    if sha(accepted/'full/INVOCATIONS.jsonl')!=receipt['ledgers']['full']:raise ValueError('old ledger identity')
    oldevents=[json.loads(x) for x in (accepted/'full/INVOCATIONS.jsonl').read_text().splitlines()]
    output={};missing={}
    for config,root in [('old',accepted),('new',art)]:
        specs=json.loads((root/'SCENARIOS.json').read_text())
        for model in ('C','E2'):
            for law in LAWS:
                for h in ('UP','DOWN'):
                    k=f'{model}_{law}_{h}_base';key=config+'_'+k
                    try:
                        e=next(e for e in oldevents if e['slot']==k and e['status']=='COMPLETE') if config=='old' else complete(art,[k])[k]
                        directory=root/('full' if config=='old' else 'runs')/e['id'];verify_files(directory,e['files'])
                        output[key]=observe(directory/'case',specs[k])
                    except (OSError,ValueError,StopIteration) as error:missing[key]=str(error)
    write(DOC/'SECTIONS.json',dict(role='SEPARATE_NONSCORING_OBSERVER_DIAGNOSTIC',observer_sha256=sha(__import__('pathlib').Path(__file__)),source_receipt_sha256=sha(DOC/'SECTION_SOURCE_RECEIPT.json'),time_policy='stored 30-second final fields of all base C/E2 law/history cases; old E2 explicitly historical diagnostic only',cuts_m=CUTS.tolist(),cases=output,unavailable=missing,physical_validation='NOT_ESTABLISHED'))
    print('virtual sections:',len(output),'stored cases;',len(missing),'unavailable')
if __name__=='__main__':main()
