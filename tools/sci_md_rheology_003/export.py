"""Export and qualify external native tables for the fixed three new laws."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import numpy as np
from tools.sci_md_rheology_001.analysis import source, sha, write, DOC as PREDECESSOR
from tools.sci_md_rheology_002.export import HEADER
from .laws import NEW, TK, RHO, eq5, evaluate, knots

SW_FILES = ('docs/cards/sobolik2002.md', 'puckworks/data/sobolik2002/README.md',
            'puckworks/data/sobolik2002/eq5_viscosity_dilute_computed.csv',
            'puckworks/data/sobolik2002/fig3_viscosity_dilute_weisser_digitized.csv')


def reproduce_csv(path):
    with Path(path).open() as f:
        rows = list(csv.DictReader(f))
    errors = [abs(float(eq5(float(r['omega']),float(r['T_degC'])))-float(r['mu_Pa_s'])) for r in rows]
    # Source CSV is rounded to 8 decimal places in Pa.s (trailing zeros omitted).
    tolerance = 5e-9 + 1e-15
    if not rows or max(errors) > tolerance:
        raise ValueError('Eq5 source CSV reproduction failed')
    return dict(rows=len(rows),max_absolute_error_Pa_s=max(errors),tolerance_Pa_s=tolerance,
                tolerance_reason='half of 1e-8 Pa.s decimal rounding plus floating arithmetic margin',
                domain_w=[0,.5],domain_temperature_C=[0,80],evidence='equation-generated, not independent measurements')


def export(puckworks, output, evaluator):
    data, water = source(puckworks)
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    muw=float(water.water_viscosity(TK))
    breaks=sorted({round(1-float(r['Xw_pct'])/100,14) for r in data.telisromero_table1_eta()})
    receipt=dict(source_commit='2058d0e947ee9eb92c52d64f6165b810f1fb4732',
                 source_tree='a6ffb312473b15be43c1571a893b19873ea47c5a',
                 source_hashes=json.loads((PREDECESSOR/'AUTHORITY.json').read_text())['puckworks_source_hashes'],
                 water_viscosity_Pa_s=muw, temperature_K=TK, rho_water_kg_m3=RHO,
                 basis='w=c/(965+c); c is kg dissolved aggregate per m3 pore water',
                 source_csv=reproduce_csv(Path(puckworks)/SW_FILES[2]),
                 raw_eq5_water_90C_Pa_s=float(eq5(0,90,extrapolate_90=True)),
                 normalization_factor=float(muw/eq5(0,90,extrapolate_90=True)),
                 exporter_sha256=sha(__file__),laws_sha256=sha(Path(__file__).with_name('laws.py')),
                 evaluator_sha256=sha(evaluator),tables={})
    receipt['source_hashes'].update({p:sha(Path(puckworks)/p) for p in SW_FILES})
    for law in NEW:
        for refined in (False,True):
            tag=law+('_refined' if refined else '_base')
            ws=knots(breaks,refined); mus=evaluate(law,ws,muw,data.telisromero_eta_measured)
            path=output/(tag+'.table')
            path.write_text(HEADER+''.join(f'{w:.17g} {mu:.17g}\n' for w,mu in zip(ws,mus)))
            points=np.unique(np.concatenate([np.linspace(0,.24,240001),ws,
                [v+d for v in ws for d in (-1e-12,1e-12) if 0<=v+d<=.24]]))
            cs=RHO*points/(1-points); native_w=cs/(RHO+cs)
            continuous=evaluate(law,native_w,muw,data.telisromero_eta_measured)
            table=np.interp(native_w,ws,mus)
            result=subprocess.run([str(evaluator),str(path)],input='\n'.join(format(c,'.17g') for c in cs),
                                  text=True,capture_output=True,check=True)
            native=np.array(list(map(float,result.stdout.split())))
            native_error=float(np.max(abs(native/table-1)))
            approx=float(np.max(abs(table/continuous-1)))
            if native_error>1e-12 or approx>1e-4 or np.any(continuous<=0) or np.any(np.diff(continuous)<-1e-14*np.max(continuous)):
                raise ValueError('table qualification failed: '+tag)
            if law.startswith('TR_'):
                measured=points[points>=.1]
                if not np.array_equal(evaluate(law,measured,muw,data.telisromero_eta_measured),
                                      evaluate('TR_LINEAR',measured,muw,data.telisromero_eta_measured)):
                    raise ValueError('measured segment changed')
            receipt['tables'][tag]=dict(sha256=sha(path),knots=len(ws),dense_points=len(points),
                max_relative_table_approximation=approx,max_relative_native_python=native_error,
                endpoints_Pa_s=[float(mus[0]),float(mus[-1])],extrema_Pa_s=[float(min(continuous)),float(max(continuous))],
                positive=True,monotone=True,monotonicity_roundoff_relative_tolerance=1e-14,domain=[0,.24],spacing=.0005 if refined else .001)
    write(output/'EXPORT.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('puckworks','output','evaluator'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.puckworks,a.output,a.evaluator),indent=2))

if __name__=='__main__':main()
