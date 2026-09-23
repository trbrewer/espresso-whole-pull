"""One append-only ledger counts every solver launch, including startup failure."""
import argparse
import fcntl
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from .common import *
from tools.sci_md_rheology_008.run import append
from tools.sci_md_rheology_008.geometry import mesh
from tools.sci_md_rheology_006.exchange import labels
from tools.sci_md_rheology_007.short import final_directory
from tools.sci_md_004_stage_c.compare import scalar_internal_values
from tools.sci_md_rheology_002.verify import traces


def events(art):
    p=art/'ATTEMPTS.jsonl'
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def reserve(ev,slot,scenario_hash,exe_hash,recovery=None):
    starts=[e for e in ev if e['status']=='STARTED']
    prior=[e for e in starts if e['slot']==slot]
    if len(starts)>=44:raise ValueError('44 total native attempt ceiling')
    if prior:
        if recovery is None or recovery.get('category')!='INFRASTRUCTURE_INTERRUPTION' or not recovery.get('evidence_sha256'):
            raise ValueError('demonstrable infrastructure interruption required')
        if sum(bool(e.get('recovery')) for e in starts)>=2:raise ValueError('two extra attempts total')
        for s in prior:
            ends=[e for e in ev if e.get('id')==s['id'] and e['status']=='FAILED']
            if len(ends)!=1 or ends[0].get('failure_class')!='INFRASTRUCTURE_INTERRUPTION':
                raise ValueError('unresolved/scientific/numerical failure cannot retry')
            if (s['scenario_sha256'],s['executable_sha256'])!=(scenario_hash,exe_hash):
                raise ValueError('recovery inputs changed')
    elif recovery is not None:raise ValueError('no prior attempt')
    return slot+('__recovery'+str(len(prior)) if prior else '')


def check_assignment(values,zone,s):
    k=s['hydraulics']['permeability_profile']
    if not np.array_equal(values['permeabilityZoneId'],np.where(zone,0.,1.)):
        raise ValueError('core zone label changed')
    expected=np.where(zone,k['inner_permeability_m2'],k['outer_permeability_m2'])
    if max(abs(values['permeability']/expected-1))>LIMITS['geometry_relative']:
        raise ValueError('actual mesh permeability assignment')


def field_check(case,s,mpi=False):
    nz,nr=s['geometry']['axial_cells'],s['geometry']['radial_cells'];n=nz*nr
    summary,vol,zone,*_=mesh(case,nz,nr)
    names=('dissolvedConcentration','remainingExtractable','p','permeabilityZoneId','permeability')
    values={k:np.full(n,np.nan) for k in names};covered=[];rank_zones=[]
    for directory in ([case/'processor0',case/'processor1'] if mpi else [case]):
        idx=labels(directory/'constant/polyMesh/cellProcAddressing') if mpi else np.arange(n)
        covered.extend(idx.tolist());final=final_directory(directory,s['time']['end_s'])
        for k in names:values[k][idx]=scalar_internal_values(final/k,cell_count=len(idx))
        rank_zones.append(sorted(set(values['permeabilityZoneId'][idx])))
    if sorted(covered)!=list(range(n)) or any(not np.isfinite(x).all() for x in values.values()):
        raise ValueError('invalid field coverage')
    check_assignment(values,zone,s)
    if mpi and sorted(rank_zones)!=[[0.],[1.]]:raise ValueError('MPI must split radial interface')
    summary.update(final_remaining_kg=float(sum(values['remainingExtractable']*vol)),
        final_stored_solute_kg=float(sum(values['dissolvedConcentration']*.4*vol)),
        inner_remaining_kg=float(sum(values['remainingExtractable'][zone]*vol[zone])),
        permeability_assignment='PASS',rank_zones=rank_zones)
    return summary


def qualify(case,s,mpi=False):
    raw=read(case/TRACE);d=native(raw,s['time']['end_s'])
    pressure=pressure_audit(raw,traces(case),s)
    ff=field_check(case,s,mpi)
    for k,r in [('final_remaining_kg','remaining_kg'),('final_stored_solute_kg','stored_solute_kg'),('inner_remaining_kg','inner_remaining_kg')]:
        if abs(ff[k]-raw[r][-1])>LIMITS['field_mass_kg']:raise ValueError('final field aggregation '+k)
    return dict(balance=d['balance'],pressure=pressure,fields=ff)


def complete(art,required):
    result={};ev=events(art)
    for slot in required:
        found=[e for e in ev if e['slot']==slot and e['status']=='COMPLETE']
        if len(found)!=1:raise ValueError('missing/duplicate complete slot '+slot)
        e=found[0];verify_files(art/'runs'/e['id'],e['files']);result[slot]=e
    return result


def run(art,stage,slot,recovery=None):
    short=stage=='short';verify(art,frozen=not short,audited=not short)
    specs=json.loads((art/('SHORT_SCENARIOS.json' if short else 'SCENARIOS.json')).read_text())
    if slot not in specs or (not short and matrix()[slot]['model']!=stage):raise ValueError('undeclared slot')
    if stage=='E2':
        from .analyze import checked_support
        checked_support(art)
    ledger=art/'ATTEMPTS.jsonl';s=specs[slot]
    exe=Path(json.loads((art/'LOCATIONS.json').read_text())['executable']);sh=digest(s);eh=sha(exe)
    with (art/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ev=events(art)
        if any(e['slot']==slot and e['status']=='COMPLETE' for e in ev):return complete(art,[slot])[slot]
        if any(e['slot']==slot and e['status']=='PREPARING' and not any(x.get('id')==e['id'] and x['status'] in ('COMPLETE','FAILED','PREPARATION_FAILED') for x in ev) for e in ev):
            raise ValueError('slot already reserved')
        ident=reserve(ev,slot,sh,eh,recovery)
        directory=art/'runs'/ident
        if directory.exists():
            failed_preps=[e for e in ev if e['slot']==slot and e['status']=='PREPARATION_FAILED']
            if not failed_preps:raise ValueError('preserve prior invocation')
            ident+='__preparation'+str(len(failed_preps));directory=art/'runs'/ident
            if directory.exists():raise ValueError('preserve failed preparation')
        append(ledger,dict(id=ident,slot=slot,stage=stage,status='PREPARING',utc=datetime.now(timezone.utc).isoformat()))
    directory.mkdir(parents=True);write(directory/'scenario.json',s);case=directory/'case';mpi=short and slot.endswith('_mpi')
    start=time.monotonic();launched=False
    def command(cmd,name):
        with (directory/name).open('w') as log:
            subprocess.run(cmd,cwd=ROOT,env=dict(runtime_environment(json.loads((art/'RUNTIME.json').read_text())),ESPRESSO_CASE_ROOT=str(case)),stdout=log,stderr=subprocess.STDOUT,check=True)
    try:
        command([sys.executable,str(ROOT/'scripts/prepare_case.py'),'--root',str(ROOT),'--config',str(directory/'scenario.json'),'--case-dir',str(case),'--nprocs','2' if mpi else '1'],'prepare.log')
        command(['blockMesh','-case',str(case)],'mesh.log')
        if mpi:
            (case/'system/decomposeParDict').write_text('FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }\nnumberOfSubdomains 2; method simple; simpleCoeffs { n (1 2 1); delta 0.001; }\n')
            command(['decomposePar','-case',str(case)],'decompose.log')
        with (art/'ledger.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            reserve(events(art),slot,sh,eh,recovery)
            append(ledger,dict(id=ident,slot=slot,stage=stage,status='STARTED',utc=datetime.now(timezone.utc).isoformat(),scenario_sha256=sh,executable_sha256=eh,recovery=recovery,
                               support_sha256=sha(DOC/'SUPPORT.json') if stage=='E2' else None))
        launched=True
        cmd=['mpirun','-np','2',str(exe),'-case',str(case),'-parallel'] if mpi else [str(exe),'-case',str(case)]
        command(cmd,'native.log')
        append(ledger,dict(id=ident,slot=slot,stage=stage,status='NATIVE_COMPLETED'))
        quality=qualify(case,s,mpi)
        e=dict(id=ident,slot=slot,stage=stage,status='COMPLETE',elapsed_s=time.monotonic()-start,
               cells=s['geometry']['axial_cells']*s['geometry']['radial_cells'],quality=quality,
               files={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file()})
        append(ledger,e);print(slot+' COMPLETE',flush=True);return e
    except BaseException as error:
        integrating=(case/TRACE).exists() and len((case/TRACE).read_text().splitlines())>1
        append(ledger,dict(id=ident,slot=slot,stage=stage,status='FAILED' if launched else 'PREPARATION_FAILED',
               failure_class='UNCLASSIFIED_NO_RETRY',integrating=integrating,elapsed_s=time.monotonic()-start,
               error_type=type(error).__name__,reason=str(error)))
        raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--stage',choices=('C','E2'),required=True);p.add_argument('--workers',type=int,default=1);a=p.parse_args()
    from concurrent.futures import ThreadPoolExecutor
    slots=[k for k,v in matrix().items() if v['model']==a.stage]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for f in [pool.submit(run,a.artifacts,a.stage,k) for k in slots]:f.result()
if __name__=='__main__':main()
