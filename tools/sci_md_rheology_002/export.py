"""Export the accepted fixed-temperature adapter without redistributing its table."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from tools.sci_md_rheology_001.analysis import source, viscosity, sha, write, DOC as PREDECESSOR

HEADER = 'EWP_AGGREGATE_V1 wet_mass_fraction Pa.s linear 363.15 965 0.1 0.24\n'


def export(puckworks, output, evaluator):
    data, water = source(puckworks)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    muw = float(water.water_viscosity(363.15))
    # All loader breakpoints; rounding removes only binary percent conversion noise.
    ws = sorted({0., .1, *[round(1-float(r['Xw_pct'])/100, 14) for r in data.telisromero_table1_eta()]})
    mus, _ = viscosity(np.array(ws), 90., muw, data.telisromero_eta_measured)
    table = output/'aggregate.table'
    table.write_text(HEADER+''.join(f'{w:.17g} {mu:.17g}\n' for w, mu in zip(ws,mus)))
    points = np.unique(np.concatenate([np.linspace(0,.24,24001), ws,
        [w+d for w in ws for d in (-1e-12,1e-12) if 0<=w+d<=.24]]))
    cs = 965*points/(1-points)
    # Compare the actual native concentration mapping, including floating roundoff.
    expected,_ = viscosity(cs/(965+cs),90,muw,data.telisromero_eta_measured)
    result = subprocess.run([str(evaluator),str(table)], input='\n'.join(format(c,'.17g') for c in cs),
                            text=True,capture_output=True,check=True)
    actual = np.array(list(map(float,result.stdout.split())))
    mismatch = float(np.max(abs(actual/expected-1)))
    if mismatch>1e-4: raise ValueError('native adapter equivalence failed')
    authority=json.loads((PREDECESSOR/'AUTHORITY.json').read_text())
    receipt=dict(basis='dimensionless wet-basis aggregate mass fraction c/(rho_water+c)',
        viscosity_units='Pa.s',density_kg_m3=965,temperature_K=363.15,
        domain=[0,.24],measured_domain=[.1,.24],dilute_boundary=.1,
        interpolation='piecewise linear preserving every measured-loader concentration breakpoint',
        dilute_extension='linear water anchor to measured 0.10 boundary; assumption',
        water_viscosity_Pa_s=muw,source_commit=authority['puckworks_analysis_commit'],
        source_tree=authority['puckworks_analysis_tree'],source_hashes=authority['puckworks_source_hashes'],
        exporter_sha256=sha(__file__),runtime_table_sha256=sha(table),
        evaluator_sha256=sha(evaluator),points=len(points),max_relative_mismatch=mismatch,
        equivalence_tolerance=1e-4,breakpoint_count=len(ws),source_tables_redistributed=False)
    write(output/'EXPORT.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--puckworks',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--evaluator',type=Path,required=True)
    a=p.parse_args(); print(json.dumps(export(a.puckworks,a.output,a.evaluator),indent=2))

if __name__=='__main__': main()
