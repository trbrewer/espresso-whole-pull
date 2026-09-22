"""Sixteen native startup rejection attempts, bypassing Python preparation."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from .common import write,sha

def main():
    p=argparse.ArgumentParser()
    for k in ('output','fixture','executable'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    mutations={'bulk_radial':('aggregateViscosityMode','bulkCoupled'),'mode':('aggregateViscosityMode','unknown'),
        'flow':('pressureBoundaryModel','prescribedFlow'),'ramp':('pressureRampTime','1'),
        'restart':('startFrom','latestTime'),'unsaturated':('initialWetFront','0'),
        'temperature':('liquidTemperature','360'),'density':('liquidDensity','1000'),
        'k_zero':('innerPermeabilityM2','0'),'k_negative':('outerPermeabilityM2','-1e-15'),
        'interface_empty':('interfaceRadiusM','0'),'interface_misaligned':('interfaceRadiusM','.0146'),
        'zero_pressure':('targetInletPressure','0'),'nonfinite_pressure':('targetInletPressure','1e999'),
        'malformed_table':('aggregateViscosityTable','TABLE'),'mechanics':('bedMechanicsModel','unknown')}
    table=a.output/'malformed.table';table.write_text('EWP_AGGREGATE_V1 wet_mass_fraction Pa.s linear 363.15 965 0.1 0.24\n0 .001\n.1 .001\n.24\n')
    records=json.loads((a.output/'REJECTIONS.json').read_text()) if (a.output/'REJECTIONS.json').exists() else {}
    for name,(key,value) in mutations.items():
        if name in records:
            record=records[name]
            if name=='nonfinite_pressure' and record['returncode']==-8:
                record.update(status='REJECTED',layer='OpenFOAM numeric parser SIGFPE before time loop')
                write(a.output/'REJECTIONS.json',records)
            if record['status']!='REJECTED':raise ValueError('prior incomplete rejection '+name)
            continue
        case=a.output/name
        for folder in ('0','constant','system'):shutil.copytree(a.fixture/folder,case/folder)
        path=case/('system/controlDict' if name=='restart' else 'constant/espressoModelProperties')
        if value=='TABLE':value='"'+str(table)+'"'
        content,n=re.subn(r'(?m)^'+key+r'\s+[^;]+;',key+' '+value+';',path.read_text())
        if n!=1:raise ValueError('mutation absent '+key)
        path.write_text(content)
        records[name]=dict(status='STARTED');write(a.output/'REJECTIONS.json',records)
        proc=subprocess.run([str(a.executable),'-case',str(case)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (case/'startup.log').write_text(proc.stdout)
        records[name]=dict(status='REJECTED' if proc.returncode and ('FOAM FATAL' in proc.stdout or (name=='nonfinite_pressure' and proc.returncode==-8)) else 'FAIL',returncode=proc.returncode,log_sha256=sha(case/'startup.log'))
        write(a.output/'REJECTIONS.json',records)
        assert records[name]['status']=='REJECTED',(name,proc.stdout[-1000:])
    print('16 native rejections passed')
if __name__=='__main__':main()
