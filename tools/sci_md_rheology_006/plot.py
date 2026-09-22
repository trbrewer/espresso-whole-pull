"""Illustrations from complete native traces; figures never supply scores."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import LAWS
from .observer import read
from tools.sci_md_004_stage_c.compare import scalar_internal_values,internal_numeric_values

LABEL='Synthetic fixed-k radial puck; TR dilute continuation / SW water anchoring and 90 C extrapolation'

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    events=[json.loads(l) for l in (a.artifacts/'science/INVOCATIONS.jsonl').read_text().splitlines()];ends={v['slot']:v['id'] for v in events if v['status']=='COMPLETE'}
    fig,axs=plt.subplots(2,2,figsize=(10,6),sharex=True,sharey=True)
    fig2,bxs=plt.subplots(2,2,figsize=(10,6),sharex=True)
    for i,law in enumerate(LAWS):
        for j,pressure in enumerate((3,9)):
            case=a.artifacts/'science'/ends[f'{law}_{pressure}bar_base']/'case';d=read(case);ax=axs[i,j]
            ax.step(d['end_s'],100*d['Q_inner_m3_s']/d['Q_total_m3_s'],where='pre',label='Local coupled native')
            ax.axhline(400/7,color='black',ls='--',label='Every uniform scalar: 4/7')
            ax.set_title(f'{law} / {pressure} bar',fontsize=10);ax.set_ylabel('Inner outlet share (%)');ax.set_xlabel('Time (s)');ax.grid(alpha=.2)
            bx=bxs[i,j];bx.step(d['end_s'],d['water_kg']*1000,where='pre',label='Water (g)');bx.step(d['end_s'],d['solute_kg']*1000,where='pre',label='Solute (g)');bx.step(d['end_s'],(d['water_kg']+d['solute_kg'])*1000,where='pre',label='Beverage (g)')
            bx.set_title(f'{law} / {pressure} bar',fontsize=10);bx.set_xlabel('Time (s)');bx.set_ylabel('Modeled delivery (g)');bx.grid(alpha=.2)
    for fig,axes,name in [(fig,axs,'flow_share.svg'),(fig2,bxs,'delivery.svg')]:
        axes[0,0].legend(fontsize=8);fig.suptitle(LABEL,fontsize=9);fig.tight_layout();fig.savefig(a.output/name);plt.close(fig)
    # Only predeclared 5 and 15 s snapshots of four base cases.
    fig,axs=plt.subplots(4,4,figsize=(12,10))
    for row,(law,pressure) in enumerate((l,p) for l in LAWS for p in (3,9)):
        case=a.artifacts/'science'/ends[f'{law}_{pressure}bar_base']/'case'
        n=512*64;c=np.array(internal_numeric_values(case/'0/C',cell_count=n)).reshape(n,3)
        for col,(time,field) in enumerate((t,f) for t in ('5','15') for f in ('aggregateMu','p')):
            values=np.array(scalar_internal_values(case/time/field,cell_count=n));scale=1000 if field=='aggregateMu' else 1e-5
            ax=axs[row,col];sc=ax.scatter(np.hypot(c[:,1],c[:,2])*1000,c[:,0]*1000,c=values*scale,s=2,rasterized=True)
            ax.axvline(14.5,color='white',ls='--',lw=.5);ax.set_title(f'{law[:2]} {pressure} bar, {time}s: '+('mu (mPa s)' if field=='aggregateMu' else 'p (bar)'),fontsize=8);ax.set_xlabel('Radius (mm)');ax.set_ylabel('Depth (mm)');fig.colorbar(sc,ax=ax)
    fig.suptitle(LABEL+'\nmu fields are beginning-of-step coefficients; pressure is solved interval pressure',fontsize=9);fig.tight_layout();fig.savefig(a.output/'fields.png',dpi=140);plt.close(fig)
if __name__=='__main__':main()
