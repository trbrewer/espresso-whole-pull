"""Actual polyMesh geometry and oriented native face exchange, read-only."""
import re
import numpy as np
from tools.sci_md_rheology_006.exchange import labels
from tools.sci_md_004_stage_c.compare import scalar_internal_values
from tools.sci_md_rheology_007.short import final_directory

def annular_volumes(n, radius=.029, depth=.009011660896432553):
    edges=np.linspace(0,radius,n+1)
    return np.pi*np.diff(edges**2)*depth

def mesh(case,nz,nr,angle=5.):
    pm=case/'constant/polyMesh'
    text=(pm/'points').read_text()
    body=re.search(r'\n(\d+)\s*\(\s*(.*?)\n\)',text,re.S)
    points=np.array([list(map(float,s.split())) for s in re.findall(r'\(([^()]+)\)',body[2])])
    if len(points)!=int(body[1]):raise ValueError('points count')
    text=(pm/'faces').read_text()
    faces=[list(map(int,s.split())) for _,s in re.findall(r'(\d+)\(([^()]+)\)',text)]
    owner=labels(pm/'owner');neighbour=labels(pm/'neighbour')
    if len(faces)!=len(owner):raise ValueError('face count')
    n=nz*nr;vol=np.zeros(n);cells=[set() for _ in range(n)];area=[]
    for i,face in enumerate(faces):
        vs=points[face];sf=np.zeros(3);vv=0.
        for j in range(1,len(vs)-1):
            cross=np.cross(vs[j]-vs[0],vs[j+1]-vs[0])/2
            sf+=cross;vv+=np.dot(cross,(vs[0]+vs[j]+vs[j+1])/3)/3
        area.append(sf);vol[owner[i]]+=vv;cells[owner[i]].update(face)
        if i<len(neighbour):vol[neighbour[i]]-=vv;cells[neighbour[i]].update(face)
    scale=2*np.pi/np.sin(np.deg2rad(angle));vol*=scale
    if np.any(vol<=0):raise ValueError('nonpositive mesh volume')
    radii=np.hypot(points[:,1],points[:,2]);shell=[];zone=[]
    edges=np.linspace(0,.029,nr+1)
    for v in cells:
        rr=radii[list(v)];lo,hi=min(rr),max(rr)
        j=int(np.argmin(abs(edges[:-1]-lo)))
        if max(abs(lo-edges[j]),abs(hi-edges[j+1]))>1e-12:
            raise ValueError('nonuniform or misaligned radial edges')
        shell.append(j);zone.append(j<nr//2)
    shell=np.array(shell);zone=np.array(zone);area=np.array(area)*scale
    expected=annular_volumes(nr)[shell]/nz
    if np.max(abs(vol/expected-1))>1e-8:raise ValueError('annular cell volume')
    inner=zone[owner[:len(neighbour)]];outer=zone[neighbour]
    interface=inner!=outer
    iface_indices=np.flatnonzero(interface)
    if len(iface_indices)!=nz:raise ValueError('disconnected radial interface')
    for i in iface_indices:
        if np.max(abs(radii[faces[i]]-.0145))>1e-12:
            raise ValueError('interface face radius')
    boundary=np.arange(len(faces))>=len(neighbour)
    outlet=boundary & (np.array([np.mean(points[f,0]) for f in faces])>.009011660896432553-1e-12)
    inner_area=float(sum(abs(area[outlet & zone[owner],0])))
    outer_area=float(sum(abs(area[outlet & ~zone[owner],0])))
    for value,expected_value in [(inner_area,np.pi*.029**2*.25),(outer_area,np.pi*.029**2*.75),
                                  (sum(vol[zone]),sum(annular_volumes(nr)[:nr//2])),
                                  (sum(vol[~zone]),sum(annular_volumes(nr)[nr//2:]))]:
        if abs(value/expected_value-1)>1e-8:raise ValueError('zone geometry')
    summary=dict(cells=n,interface_faces=len(iface_indices),radial_face_alignment_max_m=float(max(abs(radii[faces[i]]-.0145).max() for i in iface_indices)),
                 positive_volumes=True,inner_area_m2=inner_area,outer_area_m2=outer_area,inner_volume_m3=float(sum(vol[zone])),outer_volume_m3=float(sum(vol[~zone])),radial_shell_volumes_m3=[float(sum(vol[shell==j])) for j in range(nr)])
    return summary,vol,zone,owner[:len(neighbour)],neighbour,interface

def fields(case,nz,nr,end,exchange=False):
    result,vol,zone,owner,neighbour,interface=mesh(case,nz,nr)
    final=final_directory(case,end);n=nz*nr
    values={k:np.array(scalar_internal_values(final/k,cell_count=n)) for k in ('dissolvedConcentration','remainingExtractable','p','permeabilityZoneId')}
    if any(len(v)!=n or not np.isfinite(v).all() for v in values.values()):raise ValueError('invalid final fields')
    if not np.array_equal(values['permeabilityZoneId'],np.where(zone,0.,1.)):
        raise ValueError('native zone labels disagree with mesh')
    result['final_time_s']=float(final.name)
    result['final_remaining_kg']=float(sum(values['remainingExtractable']*vol))
    result['final_stored_solute_kg']=float(sum(values['dissolvedConcentration']*.4*vol))
    result['inner_remaining_kg']=float(sum(values['remainingExtractable'][zone]*vol[zone]))
    if exchange:
        q=np.array(scalar_internal_values(final/'darcyFlux',cell_count=len(neighbour)))
        c=values['dissolvedConcentration'];scale=2*np.pi/np.sin(np.deg2rad(5))
        # Positive oriented flux is core -> annulus even if owner lies outside.
        sign=np.where(zone[owner],1.,-1.)
        oriented=q*sign*scale
        solute=oriented*np.where(q>=0,c[owner],c[neighbour])
        water=float(sum(abs(oriented[interface])));mass=float(sum(abs(solute[interface])))
        if water<=1e-18 or mass<=0:raise ValueError('dynamic interface exchange not exercised')
        result['exchange']=dict(absolute_water_m3_s=water,signed_core_to_annulus_water_m3_s=float(sum(oriented[interface])),absolute_upwind_solute_kg_s=mass,signed_core_to_annulus_upwind_solute_kg_s=float(sum(solute[interface])),meaning='Advective-only native face flux and upwind donor; no total diffusion or unique mechanism attribution')
    return result
