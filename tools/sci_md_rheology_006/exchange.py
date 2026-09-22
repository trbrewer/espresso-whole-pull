"""Read-only verification of native upwind solute exchange in the short fixture."""
import argparse,re
from pathlib import Path
import numpy as np
from tools.sci_md_004_stage_c.compare import scalar_internal_values,internal_numeric_values
from .common import sha,write

def labels(path):
    match=re.search(r'\n(\d+)\s*\(\s*([\d\s]+)\)',path.read_text())
    if not match:raise ValueError('label list missing')
    values=np.array(list(map(int,match[2].split())))
    if len(values)!=int(match[1]):raise ValueError('label count')
    return values

def main():
    p=argparse.ArgumentParser();p.add_argument('--short',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    case=a.short/'transverse/case';n=256
    centres=np.array(internal_numeric_values(case/'0/C',cell_count=n)).reshape(n,3)
    owner=labels(case/'constant/polyMesh/owner');neighbour=labels(case/'constant/polyMesh/neighbour');owner=owner[:len(neighbour)]
    q=np.array(scalar_internal_values(case/'0.2/darcyFlux',cell_count=len(neighbour)))
    c=np.array(scalar_internal_values(case/'0.2/dissolvedConcentration',cell_count=n))
    transverse=abs(centres[owner,0]-centres[neighbour,0])<1e-12
    scale=2*np.pi/np.sin(np.deg2rad(5))
    advective=q*np.where(q>=0,c[owner],c[neighbour])
    amount=float(np.sum(abs(advective[transverse]))*scale)
    water=float(np.sum(abs(q[transverse]))*scale)
    if not amount>0 or not water>0:raise ValueError('transverse exchange not exercised')
    ranks=[]
    for rank in (0,1):
        values=scalar_internal_values(a.short/f'transverse_mpi/case/processor{rank}/0.2/permeabilityZoneId',cell_count=128)
        ranks.append(sorted(set(values)))
    if sorted(ranks)!=[[0.],[1.]]:raise ValueError('radial decomposition does not separate zones')
    paths=[case/'0/C',case/'0.2/darcyFlux',case/'0.2/dissolvedConcentration',case/'constant/polyMesh/owner',case/'constant/polyMesh/neighbour',case/'system/fvSchemes']
    write(a.output/'EXCHANGE.json',dict(status='PASS',interval_end_s=.2,transverse_absolute_native_water_flux_m3_s=water,transverse_absolute_upwind_solute_flux_kg_s=amount,operator='Gauss upwind: pressure-matrix face flux times accepted implicit donor concentration; diffusion also retained, not included in this advective-only demonstration',processor_zone_sets=ranks,processor_interface='32 radial-normal processor faces, material interface between ranks',files={str(p.relative_to(case)):sha(p) for p in paths}))
if __name__=='__main__':main()
