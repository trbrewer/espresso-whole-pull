#!/usr/bin/env python3
"""Bounded synthetic production qualification; raw products stay in qualification_runs."""
from __future__ import annotations
import argparse, copy, csv, hashlib, io, json, math, os, re, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.xsv_pressure_001_reference import Schedule
from tools.sci_md_004_stage_c.runner import Matrix, latest_time_name
from tools.sci_md_004_stage_c.compare import internal_numeric_values
OUT=ROOT/'validation/xsv_pressure_001'
BASE='d4a93971cd7a80c8670b83017e4283e9d34dabf0'
SYN_T=[0,3,8,18,25,30,33]; SYN_P=[0,300000,900000,900000,600000,0,0]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,data): (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
def hashes(root): return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def source_hashes(): return {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'solver/espressoWholePullFoam').glob('*')) if p.is_file()}
def rows(case):
    with (case/'postProcessing/wholePull/0/traces.csv').open() as f: return list(csv.DictReader(f))
def history(s,t,p):
    s=copy.deepcopy(s); h=s['hydraulics']
    h.pop('target_inlet_pressure_gauge_Pa',None); h.pop('pressure_ramp_time_s',None)
    h['pressure_boundary_model']='prescribedPressureHistory'
    h['prescribed_pressure_boundary']={'schedule_type':'piecewiseLinear','times_s':t,'pressures_gauge_Pa':p}
    return s

def vectors():
    definitions=[('constant',[0,10],[900000,900000],0),('zero',[0,10],[0,0],0),
    ('rising',[0,10],[0,900000],0),('falling',[0,10],[900000,0],0),
    ('rising_threshold',[0,10],[0,900000],300000),('falling_threshold',[0,10],[900000,0],300000),
    ('hold_above',[0,10],[400000,400000],300000),('hold_below',[0,10],[200000,200000],300000),
    ('multiple_knots',SYN_T,SYN_P,200000),('knot_crossing',[0,2,4],[100000,300000,100000],0),
    ('rising_crossing',[0,10],[0,900000],100000),('falling_crossing',[0,10],[900000,0],100000),
    ('constant_crossing',[0,10],[900000,900000],100000),('no_positive',[0,5,10],[0,100000,0],200000),
    ('zero_required',[0,10],[0,900000],0),('interior_maximum',[0,2,10],[0,900000,0],0),
    ('decline_to_zero',[0,2,6,10],[0,900000,400000,0],100000)]
    result=[]
    for name,t,p,pf in definitions:
        s=Schedule(t,p); targets=sorted(set(t+[(a+b)/2 for a,b in zip(t,t[1:])]))
        intervals=[[t[0],t[-1],pf],[(t[0]+t[1])/2,(t[-2]+t[-1])/2,pf]]
        total=s.integral(t[0],t[-1],pf)
        req=s.integral(t[0],t[1],pf) if name=='knot_crossing' else total*.37
        if name=='zero_required': req=0
        crossings=[[t[0],t[-1],req,pf],[t[0],t[-1],0,pf]]
        if name=='falling_threshold':crossings.append([0,10,2000000,300000])
        result.append(dict(id=name,times=t,pressures=p,targets=targets,integrals=intervals,crossings=crossings,
            expected={'maximum':[s.maximum()],'target':[s.target(x) for x in targets],
            'integral':[s.integral(*x) for x in intervals],'crossing':[s.crossing(*x) for x in crossings]}))
    return result

def dictionary(v):
    def lst(x): return '('+' '.join(lst(y) if isinstance(y,list) else format(y,'.17g') for y in x)+')'
    return ('runStart '+str(v['times'][0])+'; runEnd '+str(v['times'][-1])+';\n'
      'prescribedPressureBoundary { scheduleType piecewiseLinear; timesS '+lst(v['times'])+'; pressuresPa '+lst(v['pressures'])+'; }\n'
      +'targets '+lst(v['targets'])+'; integrals '+lst(v['integrals'])+'; crossings '+lst(v['crossings'])+';\n')

class Qualification:
    def __init__(self,work):
        self.work=work.resolve(); self.receipts=[]; self.commands=[]
        self.contract_sha256=json.loads((OUT/'CONTRACT_RECEIPT.json').read_text())['sha256']
        self.exe=self.work/'solver'; self.probe=self.work/'probe'
    def command(self,cmd,log):
        start=time.time()
        with log.open('w') as f: result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        self.commands.append({'argv':[str(x).replace(str(ROOT),'<repository>').replace(str(self.work),'<work>') for x in cmd],
                              'exit_code':result.returncode,'runtime_s':time.time()-start,'log_sha256':sha(log)})
        return result.returncode
    def build(self):
        import shutil
        build_bin=self.work/'build-bin';build_bin.mkdir()
        original_appbin=os.environ['FOAM_USER_APPBIN']
        os.environ['FOAM_USER_APPBIN']=str(build_bin)
        try:
            for directory,name in [('solver/espressoWholePullFoam','espressoWholePullFoam'),('verification/xsv_pressure_001/pressureHistoryProbe','xsvPressureHistoryProbe')]:
                code=self.command(['wclean',directory],self.work/(name+'-clean.log'))
                if code: raise RuntimeError('build clean failed: '+name)
                code=self.command(['wmake',directory],self.work/(name+'-build.log'))
                if code: raise RuntimeError('build failed: '+name)
                shutil.copy2(build_bin/name,self.exe if name=='espressoWholePullFoam' else self.probe)
        finally:
            os.environ['FOAM_USER_APPBIN']=original_appbin
    def functions(self):
        vv=vectors(); write('REFERENCE_VECTORS.json',vv); results=[]
        errors={k:0. for k in ('target','integral','integral_relative','crossing','maximum')}
        for v in vv:
            d=self.work/(v['id']+'.dict');d.write_text(dictionary(v)); files=[];code=0
            for repeat in range(2):
                log=self.work/(v['id']+f'-{repeat}.csv');code|=self.command([str(self.probe),str(d)],log);files.append(log)
            actual=list(csv.DictReader(io.StringIO(files[0].read_text()))) if code==0 else []
            passed=code==0 and files[0].read_bytes()==files[1].read_bytes() and len(actual)==sum(map(len,v['expected'].values()))
            for row in actual:
                kind=row['kind']; expected=v['expected'][kind][int(row['index'])]; value=float(row['value']);e=abs(value-expected)
                errors[kind]=max(errors[kind],e)
                if kind=='integral': errors['integral_relative']=max(errors['integral_relative'],e/max(abs(expected),1e-30))
                tolerance=1e-10 if kind=='crossing' else max(1e-6,abs(expected)*1e-12) if kind=='integral' else 1e-6
                passed &= math.isfinite(value) and e<=tolerance and (kind!='integral' or value>=0)
            results.append({'id':v['id'],'pass':passed,'dictionary_sha256':sha(d),'output_sha256':sha(files[0]),'repeat_sha256':sha(files[1]),'actual':actual})
        data={'pass':all(x['pass'] for x in results),'count':len(results),'maximum_errors':errors,'vectors':results,'probe_sha256':sha(self.probe),'source_hashes':source_hashes()}
        write('FUNCTION_LEVEL_VERIFICATION.json',data);return data
    def run(self,name,s,ranks=1,exe=None):
        exe=exe or self.exe;m=Matrix(exe,self.work);start=time.time();error=None
        import tools.sci_md_004_stage_c.runner as matrix_module
        saved_root=matrix_module.ROOT
        if exe != self.exe:
            matrix_module.ROOT=ROOT/'qualification_runs/xsv-pressure-001/baseline/pristine'
        try: case=m.run(name,s,ranks)
        except BaseException as e: error=str(e);case=self.work/name
        finally: matrix_module.ROOT=saved_root
        rr=rows(case) if (case/'postProcessing/wholePull/0/traces.csv').exists() else []
        last=rr[-1] if rr else {};f=lambda k:float(last[k]) if k in last else None
        mode=s['hydraulics'].get('pressure_boundary_model',s.get('pressureBoundaryModel','prescribedPressure'))
        schedule=s['hydraulics'].get('prescribed_pressure_boundary',{k:s['hydraulics'][k] for k in ('target_inlet_pressure_gauge_Pa','pressure_ramp_time_s') if k in s['hydraulics']})
        if mode=='prescribedFlow':schedule=s['prescribedFlowBoundary']
        if mode=='lumpedMachineCompliance':schedule=s['machineBoundary']
        bounded=bool(rr) and all(math.isfinite(float(row[k])) for row in rr for k in ('wet_front_m','cup_beverage_mass_kg','min_saturation','max_saturation','min_concentration_kg_m3','max_concentration_kg_m3','outlet_flow_m3_s'))
        bounded &= all(float(r['min_saturation'])>=-1e-12 and float(r['max_saturation'])<=1+1e-12 and float(r['min_concentration_kg_m3'])>=-1e-8 and float(r['max_concentration_kg_m3'])<=s['extraction']['saturation_concentration_kg_m3']+1e-8 and float(r['outlet_flow_m3_s'])>=0 for r in rr)
        bounded &= all(float(b['cup_beverage_mass_kg'])>=float(a['cup_beverage_mass_kg'])-1e-12 for a,b in zip(rr,rr[1:]))
        water=max((abs(float(r['liquid_balance_residual_kg'])) for r in rr),default=0)
        solute=max((abs(float(r['solute_balance_residual_kg'])) for r in rr),default=0)
        complete=error is None and bool(rr) and abs(f('time_s')-s['time']['end_s'])<1e-9 and '\nEnd\n' in (case/'solver.log').read_text()
        record=dict(case_id=name,mode=mode,schedule=schedule,schedule_sha256=hashlib.sha256(json.dumps(schedule,sort_keys=True).encode()).hexdigest(),
            executable_sha256=sha(exe),execution='serial' if ranks==1 else 'MPI',rank_count=ranks,start_time_s=s['time']['start_s'],end_time_s=f('time_s'),
            completion_status='PASS' if complete else 'FAIL',first_drip_s=f('first_drip_s'),final_wet_front_m=f('wet_front_m'),endpoint_cup_mass_kg=f('cup_beverage_mass_kg'),
            maximum_water_residual_kg=water,maximum_solute_residual_kg=solute,conservation_pass=bool(rr) and water<=1e-10 and solute<=1e-10,
            bounded_state_pass=bounded,runtime_s=time.time()-start,error=error,log_sha256=sha(case/'solver.log') if (case/'solver.log').exists() else None,
            input_hashes={str(p.relative_to(case)):sha(p) for d in ('0.orig','system','constant') for p in sorted((case/d).rglob('*')) if p.is_file()},
            commands={'case_preparation':'python3 scripts/prepare_case.py --root <repository> --config <work>/'+name+'.json --nprocs '+str(ranks)+' --case-dir <work>/'+name,'mesh':'blockMesh -case <work>/'+name,'geometry':['postProcess -case <work>/'+name+' -func '+f+' -time 0' for f in ('writeCellCentres','writeCellVolumes')],'solver':('mpirun --oversubscribe -np '+str(ranks)+' ' if ranks>1 else '')+'<bound-executable>'+(' -parallel' if ranks>1 else '')+' -case <work>/'+name,'parallel_workflow':['decomposePar -case <work>/'+name+' -force','reconstructPar -case <work>/'+name+' -latestTime'] if ranks>1 else []},
            configuration_sha256=sha(self.work/(name+'.json')),trace_sha256=sha(case/'postProcessing/wholePull/0/traces.csv') if rr else None)
        (case/'XSV_PRESSURE_001_RUN_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n')
        record['pass']=complete and bounded and record['conservation_pass'];self.receipts.append(record)
        write('EXECUTION_RECEIPT.json',{'production_runs':self.receipts,'contract_sha256':self.contract_sha256,'commands':self.commands,'source_hashes':source_hashes(),'executable_sha256':sha(self.exe),'openfoam_version':os.environ.get('WM_PROJECT_VERSION'),'base_commit':BASE,'base_tree':'95607f7b0b2e897ead16b2847934f8d047d05a13','work_directory_class':'ignored qualification_runs','status':'IN_PROGRESS'})
        return case,record

def compare(a,b,ra,rb,kind='legacy'):
    aa,bb=rows(a),rows(b); paired=[]
    for x in aa:
        matches=[y for y in bb if abs(float(x['time_s'])-float(y['time_s']))<1e-9]
        if len(matches)==1: paired.append((x,matches[0]))
    cols=['inlet_pressure_Pa','wet_front_m','first_drip_s','outlet_flow_m3_s','inlet_flow_m3_s','cumulative_inlet_water_mass_kg','stored_water_mass_kg','cup_beverage_mass_kg','remaining_extractable_mass_kg','cup_solute_mass_kg']
    differences={};passed=bool(paired) and len(paired)==len(aa) and ra['pass'] and rb['pass']
    for k in cols:
        absdiff=max(abs(float(x[k])-float(y[k])) for x,y in paired)
        scale=max(max(abs(float(x[k])),abs(float(y[k]))) for x,y in paired)
        tolerance={'inlet_pressure_Pa':1e-6,'wet_front_m':1e-10,'first_drip_s':1e-8}.get(k,max(1e-14,1e-8*scale))
        differences[k]={'maximum_absolute':absdiff,'relative_to_peak':absdiff/max(scale,1e-30),'limit':tolerance}
        if kind!='timestep':passed &= absdiff<=tolerance
    fields={}
    for p in sorted((a/latest_time_name(a)).iterdir()):
        q=b/latest_time_name(b)/p.name
        if not p.is_file() or p.name=='uniform' or not q.is_file():continue
        try:x=internal_numeric_values(p,cell_count=512);y=internal_numeric_values(q,cell_count=512)
        except (ValueError,KeyError):continue
        if len(x)!=len(y) or not x: continue
        error=max(abs(i-j) for i,j in zip(x,y))/max(1.0,max(map(abs,x)),max(map(abs,y)))
        fields[p.name]=error
        if kind!='timestep':passed &= error<=1e-8
    passed &= bool(fields)
    if kind=='timestep':
        cup=abs(ra['endpoint_cup_mass_kg']-rb['endpoint_cup_mass_kg'])/max(abs(rb['endpoint_cup_mass_kg']),1e-30)
        nrmse=math.sqrt(sum((float(x['cup_beverage_mass_kg'])-float(y['cup_beverage_mass_kg']))**2 for x,y in paired)/len(paired))/max(abs(rb['endpoint_cup_mass_kg']),1e-30)
        passed &= differences['inlet_pressure_Pa']['maximum_absolute']<=1e-6 and abs(ra['first_drip_s']-rb['first_drip_s'])<=.1 and cup<=.01 and nrmse<=.02
    else:cup=nrmse=None
    return {'pass':passed,'cases':[ra['case_id'],rb['case_id']],'common_time_count':len(paired),'differences':differences,'normalized_final_field_linf':fields,'cup_relative_difference':cup,'mass_curve_nrmse':nrmse,'conservation_pass':ra['conservation_pass'] and rb['conservation_pass']}

def invalid_contracts(q,legacy_case):
    v=vectors()[0];base=dictionary(v)
    schedule="prescribedPressureBoundary { scheduleType piecewiseLinear; timesS (0 10); pressuresPa (900000 900000); }"
    mutations=[
    ('missing_dictionary',base.replace(schedule,''),'INVALID_SCHEDULE'),
    ('missing_type',base.replace('scheduleType piecewiseLinear;',''),'INVALID_SCHEDULE'),
    ('unsupported_type',base.replace('piecewiseLinear','cubic'),'INVALID_SCHEDULE'),
    ('missing_times',base.replace('timesS (0 10);',''),'INVALID_SCHEDULE'),
    ('missing_pressures',base.replace('pressuresPa (900000 900000);',''),'INVALID_SCHEDULE'),
    ('short',base.replace('(0 10)','(0)').replace('(900000 900000)','(900000)'),'INVALID_SCHEDULE'),
    ('unequal',base.replace('(900000 900000)','(900000)'),'INVALID_SCHEDULE'),
    ('duplicate',base.replace('timesS (0 10)','timesS (0 0)'),'INVALID_SCHEDULE'),
    ('decreasing',base.replace('timesS (0 10)','timesS (10 0)'),'INVALID_SCHEDULE'),
    ('nonfinite_time',base.replace('timesS (0 10)','timesS (0 nan)'),'INVALID_SCHEDULE'),
    ('nonfinite_pressure',base.replace('pressuresPa (900000 900000)','pressuresPa (900000 nan)'),'INVALID_TARGET_PRESSURE'),
    ('negative_pressure',base.replace('pressuresPa (900000 900000)','pressuresPa (-1 900000)'),'INVALID_TARGET_PRESSURE'),
    ('start_coverage',base.replace('timesS (0 10)','timesS (1 10)'),'INVALID_SCHEDULE'),
    ('end_coverage',base.replace('timesS (0 10)','timesS (0 9)'),'INVALID_SCHEDULE'),
    ('scalar_target',base+'targetInletPressure 900000;','CONTRACT_CONFLICT'),
    ('scalar_ramp',base+'pressureRampTime 0;','CONTRACT_CONFLICT'),
    ('before_support',base.replace('targets (0 5 10)','targets (-1)'),'TIME_OUTSIDE_SUPPORT'),
    ('after_support',base.replace('targets (0 5 10)','targets (11)'),'TIME_OUTSIDE_SUPPORT'),
    ('unreachable',base.replace('crossings (','crossings ((0 10 1e20 0) ',1),'CROSSING_UNREACHABLE')]
    results=[]
    for name,text,token in mutations:
        d=q.work/('invalid-'+name+'.dict');d.write_text(text);log=q.work/('invalid-'+name+'.log')
        rc=q.command([str(q.probe),str(d)],log); expected='XSV_PRESSURE_001_'+token
        results.append({'id':name,'exit_code':rc,'expected_token':expected,'pass':rc!=0 and expected in log.read_text(),'input_sha256':sha(d),'log_sha256':sha(log),'executable_sha256':sha(q.probe)})
    import shutil
    case=q.work/'invalid-legacy-history'
    case.mkdir()
    for name in ('0','constant','system'):shutil.copytree(legacy_case/name,case/name)
    prop=case/'constant/espressoModelProperties';prop.write_text(prop.read_text()+ '\n'+schedule+'\n')
    log=case/'solver.log';rc=q.command([str(q.exe),'-case',str(case)],log)
    results.append({'id':'history_in_legacy','exit_code':rc,'expected_token':'XSV_PRESSURE_001_CONTRACT_CONFLICT','pass':rc!=0 and 'XSV_PRESSURE_001_CONTRACT_CONFLICT' in log.read_text(),'input_sha256':sha(prop),'log_sha256':sha(log),'executable_sha256':sha(q.exe),'completion_status':'REJECTED' if rc else 'UNEXPECTED_COMPLETION'})
    data={'pass':len(results)==20 and all(r['pass'] for r in results),'count':len(results),'cases':results}
    write('INVALID_CONTRACT_RESULTS.json',data)

def compaction(q,seed):
    s=seed.compact(end=.2,dt=.02,axial=32,radial=16);s['scenario_id']='xsv_pressure_001_compaction'
    s['bedMechanicsModel']='waszkiewiczQuasiStaticCompaction'
    s['poroelasticCompaction']={'model':'waszkiewicz2025FinitePhi','stressFreePorosity':.4,'criticalCompactionPressurePa':1239155,
      'stressFreePermeabilityM2':4.74023506749502e-15,'nonlinearRelativeTolerance':1e-10,'nonlinearAbsoluteTolerance':1e-10,
      'nonlinearMaximumIterations':100,'nonlinearUnderRelaxation':.7,'machineFluxRelativeTolerance':1e-6}
    s=history(s,[0,.1,.2],[0,100000,0]);a,ra=q.run('compaction_valid',s)
    import shutil
    b=q.work/'compaction_invalid';b.mkdir()
    for name in ('0','constant','system'):shutil.copytree(a/name,b/name)
    prop=b/'constant/espressoModelProperties';prop.write_text(prop.read_text().replace('pressuresPa (0 100000 0)','pressuresPa (0 1239155 0)'))
    log=b/'solver.log';rc=q.command([str(q.exe),'-case',str(b)],log)
    invalid={'case_id':'compaction_invalid','mode':'prescribedPressureHistory','rank_count':1,'exit_code':rc,'completion_status':'REJECTED' if rc else 'UNEXPECTED_COMPLETION','executable_sha256':sha(q.exe),'input_sha256':sha(prop),'schedule':[0,1239155,0],'log_sha256':sha(log),'pass':rc!=0 and 'Maximum pressure drop must remain below critical compaction pressure' in log.read_text()}
    write('COMPACTION_MAXIMUM_PRESSURE_CHECK.json',{'pass':ra['pass'] and invalid['pass'],'maximum_is_interior':True,'final_pressure_Pa':0,'valid':ra,'invalid':invalid})

def regressions(q,seed,baseline):
    from tools.xsv_flow_001.runner import flow_scenario
    base=seed.compact(end=8,dt=.02,axial=32,radial=16);base['scenario_id']='xsv_pressure_001_regression'
    scenarios={'prescribedPressure':base}
    for kind in ['constant','piecewiseLinear']:
        flow=flow_scenario(seed,case_id='pressure_regression_flow_'+kind,axial=32,dt=.02)
        if kind=='piecewiseLinear':flow['prescribedFlowBoundary']={'scheduleType':'piecewiseLinear','timesS':[0,1,3,5,6],'volumetricFlowRatesM3PerS':[0,1e-6,1.5e-6,5e-7,0],'absoluteFlowToleranceM3PerS':1e-12,'relativeFlowTolerance':1e-8}
        if kind=='constant':flow['prescribedFlowBoundary']={'scheduleType':'constant','volumetricFlowRateM3PerS':1e-6,'absoluteFlowToleranceM3PerS':1e-14,'relativeFlowTolerance':1e-8}
        scenarios['prescribedFlow_'+kind]=flow
    machine=copy.deepcopy(base);machine['pressureBoundaryModel']='lumpedMachineCompliance';machine['machineBoundary']={'initialUpstreamPressure':0.,'upstreamCompliance':1e-12,'upstreamResistance':1e10,'freeFlowRate':2e-6,'shutoffPressure':1e6,'supplyRampTime':0.,'couplingRelativeTolerance':1e-8,'couplingAbsoluteTolerance':1e-12,'couplingMaximumIterations':80}
    scenarios['lumpedMachineCompliance']=machine
    forchheimer=copy.deepcopy(base)
    spec=json.loads((ROOT/'validation/wp02/WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.json').read_text())
    item=next(x for x in spec['case_matrix'].values() if x['flowResistanceModel']=='darcyForchheimer' and x.get('inertialPermeabilityModel')=='constant')
    forchheimer['flowResistanceModel']='darcyForchheimer'
    forchheimer['inertialPermeabilityModel']='constant'
    forchheimer['constantInertialPermeabilityM']=item['constantInertialPermeabilityM']
    forchheimer['nonlinearControls']=spec['nonlinear_controls'];scenarios['DarcyForchheimer']=forchheimer
    evolving=copy.deepcopy(base)
    evolving['effective_permeability_evolution']=json.loads((ROOT/'config/reconstruction_WP02A_waszkiewicz_9bar.json').read_text())['effective_permeability_evolution']
    evolving['time']['end_s']=15;evolving['time']['field_write_interval_s']=15;scenarios['effective_permeability']=evolving
    fraction=copy.deepcopy(base);fraction['fractionCollection']={'enabled':True,'boundaryBasis':'cumulativeBeverageMass','cumulativeBoundariesKg':[.001,.003,.005],'emitTerminalPartial':True};scenarios['fraction_collection']=fraction
    comp=copy.deepcopy(base);comp['wetting']['initial_wet_front_m']=comp['coffee_bed']['bed_depth_m'];comp['time']['end_s']=.2;comp['time']['field_write_interval_s']=.2
    comp['bedMechanicsModel']='waszkiewiczQuasiStaticCompaction'
    comp['poroelasticCompaction']={'model':'waszkiewicz2025FinitePhi','stressFreePorosity':.4,'criticalCompactionPressurePa':1239155,'stressFreePermeabilityM2':4.74023506749502e-15,'nonlinearRelativeTolerance':1e-10,'nonlinearAbsoluteTolerance':1e-10,'nonlinearMaximumIterations':100,'nonlinearUnderRelaxation':.7,'machineFluxRelativeTolerance':1e-6}
    scenarios['compaction']=comp
    reference=copy.deepcopy(base);reference['time']['end_s']=30;reference['time']['field_write_interval_s']=30;scenarios['reference_completion']=reference
    results={}
    for name,s in scenarios.items():
        a,ra=q.run('regression_'+name+'_base',s,exe=baseline)
        b,rb=q.run('regression_'+name+'_candidate',s)
        results[name]=compare(a,b,ra,rb)
        if name=='fraction_collection':
            observer={}
            for filename in ('fractions.csv','fraction_species.csv'):
                left=a/'postProcessing/wholePullFractions/0'/filename;right=b/'postProcessing/wholePullFractions/0'/filename
                observer[filename]={'byte_equal':left.read_bytes()==right.read_bytes(),'baseline_sha256':sha(left),'candidate_sha256':sha(right)}
            results[name]['fraction_output_comparison']=observer
            results[name]['pass'] &= all(x['byte_equal'] for x in observer.values())
    write('EXISTING_MODE_REGRESSIONS.json',{'pass':all(v['pass'] for v in results.values()),'comparisons':results,'remaining_required':[]})


def finalize():
    from scripts.validate_xsv_pressure_001 import inspect, classify
    report=inspect(ROOT,verify_result=False,verify_manifest=False)
    write('RESULT.json',{'task_id':'XSV-PRESSURE-001','disposition':report['disposition'],'gates':report['gates'],'validation_errors':report['errors'],'governing_equation_change':False,'governing_physics_change':False,'production_boundary_behavior_change':True,'independent_exact_head_review':'PENDING','owner_merge':'NOT_PERFORMED','PLAY_003':'PAUSED'})
    (OUT/'RESULT.md').write_text('# XSV-PRESSURE-001 qualification\n\n'+report['disposition']+'\n\n'+ '\n'.join('- '+k+': '+str(v) for k,v in report['gates'].items())+'\n\nNumerical qualification only. Independent exact-head G2 review and protected owner merge remain required. PLAY-003 remains paused. No fitting, scoring, governing-equation change or external-data pressure fixture was used.\n')
    write('ARTIFACT_MANIFEST.json',{'sha256':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json'}})
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path);parser.add_argument('--finalize-only',action='store_true');args=parser.parse_args()
    if args.finalize_only:
        report=finalize();print(json.dumps(report,indent=2))
        if not report['pass']:raise SystemExit(1)
        return
    if args.work is None:parser.error('--work is required for execution')
    work=args.work.resolve();work.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((OUT/'CONTRACT_RECEIPT.json').read_text())
    assert all(sha(OUT/k)==v for k,v in receipt['sha256'].items())
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    q=Qualification(work);q.build();function=q.functions()
    if not function['pass']:raise SystemExit('XSV_PRESSURE_001_BLOCKED_PRESSURE_HISTORY_MATHEMATICS')
    seed=Matrix(q.exe,work);s=seed.compact(end=30,dt=.02,axial=32,radial=16);s['scenario_id']='xsv_pressure_001_synthetic'
    for label,ramp in [('CONSTANT',0),('RAMP',5)]:
        legacy=copy.deepcopy(s);legacy['hydraulics']['pressure_ramp_time_s']=ramp
        if ramp:legacy['hydraulics']['front_pressure_gauge_Pa']=100000
        t,p=([0,30],[900000,900000]) if not ramp else ([0,5,30],[0,900000,900000])
        a,ra=q.run(label+'_legacy',legacy);b,rb=q.run(label+'_history',history(legacy,t,p))
        write('LEGACY_'+label+'_EQUIVALENCE.json',compare(a,b,ra,rb))
    s['time']['end_s']=33;s['time']['field_write_interval_s']=33
    syn=history(s,SYN_T,SYN_P);a,ra=q.run('synthetic',syn)
    rr=rows(a);oracle=Schedule(SYN_T,SYN_P);pressure=max(abs(float(r['inlet_pressure_Pa'])-oracle.target(min(33,max(0,float(r['time_s']))))) for r in rr)
    integrals=max(abs(float(r['wetting_pressure_integral_Pa_s'])-oracle.integral(max(0,float(r['time_s'])-.02),min(33,float(r['time_s'])),0)) for r in rr)
    required=s['coffee_bed']['bed_depth_m']**2*s['coffee_bed']['initial_porosity']*s['liquid']['dynamic_viscosity_Pa_s']/(2*s['hydraulics']['wetting_permeability_m2'])
    crossing=abs(ra['first_drip_s']-oracle.crossing(0,33,required,0))
    write('SYNTHETIC_PROFILE_QUALIFICATION.json',{'pass':ra['pass'] and pressure<=1e-6 and integrals<=1e-6 and crossing<=1e-8,'schedule':list(zip(SYN_T,SYN_P)),'pressure_max_error_Pa':pressure,'integral_max_error_Pa_s':integrals,'first_drip_error_s':crossing,'run':ra})
    refined=copy.deepcopy(syn);refined['time']['delta_t_s']=.01
    b,rb=q.run('synthetic_refined',refined);write('TIMESTEP_REFINEMENT.json',compare(a,b,ra,rb,'timestep'))
    b,rb=q.run('synthetic_mpi',syn,4);write('SERIAL_MPI_EQUIVALENCE.json',compare(a,b,ra,rb))
    invalid_contracts(q,work/'CONSTANT_legacy')
    compaction(q,seed)
    regressions(q,seed,ROOT/'qualification_runs/xsv-pressure-001/baseline/espressoWholePullFoam')
    write('EXECUTION_RECEIPT.json',{'production_runs':q.receipts,'contract_sha256':q.contract_sha256,'commands':q.commands,'source_hashes':source_hashes(),'executable_sha256':sha(q.exe),'probe_sha256':sha(q.probe),'openfoam_version':os.environ.get('WM_PROJECT_VERSION'),'base_commit':BASE,'status':'COMPLETE','base_tree':'95607f7b0b2e897ead16b2847934f8d047d05a13','candidate_commit_at_generation':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'candidate_worktree_modified':True,'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'build_environment':{k:os.environ.get(k) for k in ('WM_OPTIONS','WM_COMPILER','WM_PRECISION_OPTION','WM_LABEL_SIZE')},'case_preparation_sha256':sha(ROOT/'scripts/prepare_case.py'),'probe_source_sha256':sha(ROOT/'verification/xsv_pressure_001/pressureHistoryProbe/pressureHistoryProbe.C'),'work_directory_class':'ignored qualification_runs'})
    report=finalize()
    if not report['pass']:raise SystemExit(1)
if __name__=='__main__':main()
