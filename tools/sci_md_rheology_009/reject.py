"""Direct native malformed/unsupported startup checks; no time stepping permitted."""
import argparse
import re
import shutil
import subprocess
from .common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();art=a.artifacts
    source=art/'short/E2_up/case';out=art/'rejections';out.mkdir(exist_ok=True)
    mutations={'bulk':('aggregateViscosityMode','bulkCoupled'),'mode':('aggregateViscosityMode','unknown'),'flow':('pressureBoundaryModel','prescribedFlow'),'restart':('startFrom','latestTime'),'wetting':('initialWetFront','0'),'temperature':('liquidTemperature','360'),'density':('liquidDensity','1000'),'mechanics':('bedMechanicsModel','unknown'),'zero_knot':('pressuresPa','(300000 0 900000 900000)'),'nonfinite_knot':('pressuresPa','(300000 nan 900000 900000)'),'duplicate_knot':('timesS','(0 .065 .065 .2)'),'missing_knot':('timesS','(0 .065 .2)'),'out_of_support':('timesS','(0 .065 .135 .19)'),'scalar_conflict':('APPEND','targetInletPressure 900000;'),'ramp_conflict':('APPEND','pressureRampTime 0;'),'evolving':('APPEND','effectivePermeabilityEvolution {}')}
    records={}
    for name,(key,value) in mutations.items():
        case=out/name
        if case.exists():raise ValueError('no rejection overwrite')
        for folder in ('0','constant','system'):shutil.copytree(source/folder,case/folder)
        path=case/('system/controlDict' if name=='restart' else 'constant/espressoModelProperties');text=path.read_text()
        if key=='APPEND':text+='\n'+value+'\n'
        else:
            text,n=re.subn(r'(?m)^(\s*)'+key+r'\s+[^;]+;',lambda m:m[1]+key+' '+value+';',text)
            if n!=1:raise ValueError('mutation key '+key)
        path.write_text(text);records[name]=dict(status='STARTED');write(out/'REJECTIONS.json',records)
        proc=subprocess.run([str(art/'bin/espressoWholePullFoam'),'-case',str(case)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (case/'startup.log').write_text(proc.stdout)
        ok=proc.returncode!=0 and 'FOAM FATAL' in proc.stdout and 'Time = ' not in proc.stdout
        records[name]=dict(status='REJECTED' if ok else 'FAIL',returncode=proc.returncode,log_sha256=sha(case/'startup.log'));write(out/'REJECTIONS.json',records)
        if not ok:raise ValueError('unexpected native startup '+name)
    write(DOC/'REJECTIONS.json',records)
if __name__=='__main__':main()
