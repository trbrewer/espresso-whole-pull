"""Standalone figures; no native execution and no additional decisions."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from .common import DOC, LAWS, TRACE, interface
from .analyze import reference_data
from .run import complete
from .observer import native, read, high_share
from tools.sci_md_rheology_007.observer import history

def plot(art):
    plt.rcParams['svg.hashsalt']='SCI-MD-RHEOLOGY-011'
    def save(fig,name):
        fig.tight_layout();fig.savefig(DOC/(name+'.svg'),metadata={'Date':None});plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(8,4))
    for ax,label,r,inner,outer in [(axs[0],'A: fast core',.0145,'#e59442','#5ba4ce'),(axs[1],'B: fast outer annulus',float(interface()['binary64_repr']),'#5ba4ce','#e59442')]:
        ax.add_patch(Circle((0,0),29,color=outer));ax.add_patch(Circle((0,0),r*1000,color=inner));ax.set(xlim=(-31,31),ylim=(-31,31),aspect='equal',title=label,xlabel='radius (mm)');ax.text(0,-35,'High k: 25% area; low k: 75%',ha='center')
    save(fig,'layouts')
    scores=json.loads((DOC/'METRICS.json').read_text());support=json.loads((DOC/'SUPPORT.json').read_text())
    data,_,_,_=reference_data(art);spec=json.loads((art/'SCENARIOS.json').read_text());loc=json.loads((art/'LOCATIONS.json').read_text());oldspec=json.loads((Path(loc['accepted'])/'SCENARIOS.json').read_text())
    if scores['conditional']:
        for k in spec:
            if k.startswith('E2_'):
                e=complete(art,[k])[k];data['new_'+k]=native(read(art/'runs'/e['id']/'case'/TRACE),spec[k])
    configs=[('old_C_','A / C',oldspec,'-'),('new_C_','B / C',spec,'--')]+([('new_E2_','B / E2',spec,':')] if scores['conditional'] else [])
    fig,axs=plt.subplots(4,4,figsize=(16,12));fd,ad=plt.subplots(2,2,figsize=(10,7));ff,af=plt.subplots(2,2,figsize=(10,7))
    for row,(law,h) in enumerate((l,h) for l in LAWS for h in ('UP','DOWN')):
        key=law+'_'+h;endpoint=float(support['B_star_kg'][h]);di=ad.flat[row];fi=af.flat[row]
        for prefix,label,scenarios,style in configs:
            k=prefix+key+'_base';d=data[k];s=scenarios[('E2_' if 'E2' in prefix else 'C_')+key+'_base'];sch=s['hydraulics']['prescribed_pressure_boundary']
            axs[row,0].plot(d['end_s'],np.interp(d['end_s'],sch['times_s'],sch['pressures_gauge_Pa'])/1e5,style,label=label)
            axs[row,1].plot(d['end_s'],d['Q']*1e6,style,label=label)
            axs[row,2].plot(d['end_s'],100*d['share'],style,label=label)
            axs[row,3].plot(d['end_s'],100*high_share(d,s),style,label=label)
            hist=history(d);mask=hist['B']<endpoint
            from tools.sci_md_rheology_004.observer import at
            v=at(hist,'B',[endpoint]);di.plot(np.r_[hist['B'][mask],endpoint]*1000,np.r_[hist['S'][mask],v['S'][0]]*1000,style,label=label)
            bounds=at(hist,'B',np.linspace(0,endpoint,6));fi.plot(range(1,6),100*np.diff(bounds['S'])/np.diff(bounds['B']),style+'o',label=label)
        for j,name in enumerate(('Pressure (bar)','Flow (mL/s)','INNER share (%)','High-k share (%)')):axs[row,j].set(title=key+'\n'+name,xlabel='time (s)');axs[row,j].legend(fontsize=7)
        di.set(title=key,xlabel='beverage mass (g)',ylabel='cumulative solute (g)');di.legend()
        fi.set(title=key,xlabel='equal beverage-mass fraction',ylabel='TDS (%)');fi.legend()
    save(fig,'hydraulics');save(fd,'delivery');save(ff,'fractions')
    for group in ('primary','conditional'):
        if not scores[group]:continue
        rows=[(case,metric,q) for case,c in scores[group].items() for metric,q in c['decisions'].items()]
        fig,ax=plt.subplots(figsize=(12,max(4,len(rows)*.3)))
        for i,(case,metric,q) in enumerate(rows):
            if q['value'] is not None and q['u_total'] is not None:ax.errorbar(q['value']/q['budget'],i,xerr=q['u_total']/q['budget'],fmt='o',color={'PASS':'green','BELOW_BUDGET':'green','MATERIAL':'darkorange','FAIL':'red','UNRESOLVED':'gray'}[q['decision']])
        ax.axvline(1,color='black',linestyle='--');ax.set(yticks=range(len(rows)),yticklabels=[c+' / '+m for c,m,_ in rows],xlabel='metric / budget (bars: empirical numerical allowance)');save(fig,group+'_budgets')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);plot(p.parse_args().artifacts)
