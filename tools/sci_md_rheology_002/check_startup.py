"""Native startup rejection fixtures deliberately bypass maintained Python checks."""
import argparse
from pathlib import Path
import shutil
import subprocess
from tools.sci_md_rheology_001.analysis import write


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--executable',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);records=[]
    mutations={
        'restart':('control','startFrom       startTime;','startFrom latestTime;'),
        'temperature':('model','liquidTemperature 363.15;','liquidTemperature 360;'),
        'density':('model','liquidDensity              965;','liquidDensity 1000;'),
        'wetting':('model',None,None),
        'ramp':('model','pressureRampTime          0;','pressureRampTime 1;'),
        'bad_mode':('model','aggregateViscosityMode coupled;','aggregateViscosityMode implicit;'),
        'bad_purpose':('model','aggregateViscosityPurpose synthetic;','aggregateViscosityPurpose unknown;'),
    }
    for name,(kind,old,new) in mutations.items():
        case=a.output/name
        for path in ('0','constant','system'):shutil.copytree(a.fixture/path,case/path)
        path=case/('system/controlDict' if kind=='control' else 'constant/espressoModelProperties')
        text=path.read_text()
        import re
        if name=='wetting':text,n=re.subn(r'initialWetFront\s+[^;]+;', 'initialWetFront 0;',text)
        elif name=='restart':text,n=re.subn(r'startFrom\s+[^;]+;', 'startFrom latestTime;',text)
        elif name=='ramp':text,n=re.subn(r'pressureRampTime\s+[^;]+;', 'pressureRampTime 1;',text)
        else:n=int(old in text);text=text.replace(old,new)
        if n!=1:raise ValueError('mutation not applied: '+name)
        path.write_text(text)
        result=subprocess.run([str(a.executable),'-case',str(case)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (case/'startup.log').write_text(result.stdout)
        if result.returncode==0 or 'RHEOLOGY_' not in result.stdout:raise ValueError('native rejection failed '+name)
        records.append(dict(fixture=name,status='REJECTED',exit_code=result.returncode))
    write(a.output/'STARTUP.json',records)

if __name__=='__main__':main()
