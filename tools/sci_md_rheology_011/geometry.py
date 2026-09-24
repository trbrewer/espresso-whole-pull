"""Actual polyMesh geometry and oriented native face exchange, read-only."""
import re
import numpy as np
from tools.sci_md_rheology_006.exchange import labels
from tools.sci_md_004_stage_c.compare import scalar_internal_values
from tools.sci_md_rheology_007.short import final_directory

def mesh(case,s):
    g=s['geometry'];nz,nr=g['axial_cells'],g['radial_cells']
    radius=g['basket_radius_m'];depth=s['coffee_bed']['bed_depth_m'];angle=g['wedge_angle_deg']
    interface_radius=s['hydraulics']['permeability_profile']['interface_radius_m']
    from scripts.radial_mesh import contract
    m=contract(s)
    edges=(np.r_[np.linspace(0,interface_radius,m['inner_cells']+1),
                  np.linspace(interface_radius,radius,m['outer_cells']+1)[1:]]
           if m else np.linspace(0,radius,nr+1))
    ni=m['inner_cells'] if m else round(interface_radius/radius*nr)
    annular=np.pi*np.diff(edges**2)*depth
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
    for v in cells:
        rr=radii[list(v)];lo,hi=min(rr),max(rr)
        j=int(np.argmin(abs(edges[:-1]-lo)))
        if max(abs(lo-edges[j]),abs(hi-edges[j+1]))>1e-12:
            raise ValueError('nonuniform or misaligned radial edges')
        shell.append(j);zone.append(j<ni)
    shell=np.array(shell);zone=np.array(zone);area=np.array(area)*scale
    expected=annular[shell]/nz
    if np.max(abs(vol/expected-1))>1e-8:raise ValueError('annular cell volume')
    inner=zone[owner[:len(neighbour)]];outer=zone[neighbour]
    interface=inner!=outer
    iface_indices=np.flatnonzero(interface)
    if len(iface_indices)!=nz:raise ValueError('disconnected radial interface')
    for i in iface_indices:
        if np.max(abs(radii[faces[i]]-interface_radius))>1e-12:
            raise ValueError('interface face radius')
    boundary=np.arange(len(faces))>=len(neighbour)
    outlet=boundary & (np.array([np.mean(points[f,0]) for f in faces])>depth-1e-12)
    inner_area=float(sum(abs(area[outlet & zone[owner],0])))
    outer_area=float(sum(abs(area[outlet & ~zone[owner],0])))
    for value,expected_value in [(inner_area,np.pi*interface_radius**2),(outer_area,np.pi*(radius**2-interface_radius**2)),
                                  (sum(vol[zone]),sum(annular[:ni])),
                                  (sum(vol[~zone]),sum(annular[ni:]))]:
        if abs(value/expected_value-1)>1e-8:raise ValueError('zone geometry')
    # Check named boundary membership independently from observed zone volumes.
    bt=(pm/'boundary').read_text()
    patches={name:(kind,int(count),int(start)) for name,kind,count,start in
             re.findall(r'(\w+)\s*\{\s*type\s+(\w+);.*?nFaces\s+(\d+);\s*startFace\s+(\d+);',bt,re.S)}
    expected_types=dict(inlet='patch',outlet='patch',outerWall='wall',axis='empty',wedgeMinus='wedge',wedgePlus='wedge')
    if set(patches)!=set(expected_types):raise ValueError('unexpected material/external boundary')
    covered=[]
    for name,(kind,count,start) in patches.items():
        if kind!=expected_types[name]:raise ValueError('boundary type')
        ids=list(range(start,start+count));covered.extend(ids)
        for i in ids:
            pp=points[faces[i]]
            if name in ('inlet','outlet') and np.max(abs(pp[:,0]-(0 if name=='inlet' else depth)))>1e-12:raise ValueError('axial boundary')
            if name=='outerWall' and np.max(abs(radii[faces[i]]-radius))>1e-12:raise ValueError('wall boundary')
            if name.startswith('wedge'):
                sign=-1 if name=='wedgeMinus' else 1
                if np.max(abs(pp[:,2]-sign*pp[:,1]*np.tan(np.deg2rad(angle/2))))>1e-12:raise ValueError('wedge boundary')
    if sorted(covered)!=list(range(len(neighbour),len(faces))):raise ValueError('boundary coverage')
    if not np.array_equal(np.flatnonzero(outlet),np.arange(patches['outlet'][2],sum(patches['outlet'][1:]))):raise ValueError('outlet classification')
    # Every cell belongs to one connected mesh; material faces stay INTERNAL.
    adjacency=[[] for _ in range(n)]
    for a,b in zip(owner[:len(neighbour)],neighbour):adjacency[a].append(b);adjacency[b].append(a)
    seen={0};stack=[0]
    while stack:
        for j in adjacency[stack.pop()]:
            if j not in seen:seen.add(j);stack.append(j)
    if len(seen)!=n:raise ValueError('disconnected mesh')
    summary=dict(boundaries={k:list(v) for k,v in patches.items()},connected=True,cells=n,interface_faces=len(iface_indices),radial_face_alignment_max_m=float(max(abs(radii[faces[i]]-interface_radius).max() for i in iface_indices)),
                 positive_volumes=True,inner_area_m2=inner_area,outer_area_m2=outer_area,inner_volume_m3=float(sum(vol[zone])),outer_volume_m3=float(sum(vol[~zone])),radial_shell_volumes_m3=[float(sum(vol[shell==j])) for j in range(nr)])
    return summary,vol,zone,owner[:len(neighbour)],neighbour,interface
