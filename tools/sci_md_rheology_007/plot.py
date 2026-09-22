"""Unsmoothed interval and conservative mass plots, with budgets and support."""
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg');matplotlib.rcParams['svg.hashsalt']='SCI-MD-RHEOLOGY-007'
import matplotlib.pyplot as plt
from .common import *
from .analyze import load
from .observer import compose,history
from tools.sci_md_rheology_004.observer import at

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--accepted',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    report=json.loads((a.output/'METRICS.json').read_text());c,parts,_,missing,_=load(a.artifacts,a.accepted)
    if missing:raise ValueError('figures require complete valid evidence')
    pairs=[(l,p) for l in LAWS for p in (3,9)]
    for kind in ('flow','share','solute','fractions'):
        fig,axs=plt.subplots(4,2,figsize=(11,12))
        for row,(law,pressure) in enumerate(pairs):
            key=f'{law}_{pressure}bar';ck=key+'_base';cc=c[ck];pp=compose(parts[ck+'_inner'],parts[ck+'_outer']);ax,bx=axs[row];sup=report['support'][str(pressure)];end=sup['B_star_kg']
            if kind in ('flow','share'):
                for d,label in ((cc,'Native radial C'),(pp,'Autonomous P')):
                    x=np.r_[d['start_s'],d['end_s'][-1]];y=d['Q']*1e6 if kind=='flow' else d['share']*100
                    ax.step(x,np.r_[y,y[-1]],where='post',label=label)
                residual=100*(pp['Q']-cc['Q'])/cc['Q'] if kind=='flow' else 100*(pp['share']-cc['share'])
                bx.step(np.r_[cc['start_s'],cc['end_s'][-1]],np.r_[residual,residual[-1]],where='post');budget=2
                ax.set_ylabel('Flow (mL/s)' if kind=='flow' else 'Inner share (%)');bx.set_ylabel('Relative flow residual (%)' if kind=='flow' else 'Share residual (pp)')
                for xx in (ax,bx):xx.set_xlabel('Time (s)')
            elif kind=='solute':
                hp,hc=history(pp),history(cc);points=np.unique(np.r_[0,hp['B'][hp['B']<end],hc['B'][hc['B']<end],end]);pv,cv=at(hp,'B',points),at(hc,'B',points)
                ax.plot(points*1000,cv['S']*1000,label='Native radial C');ax.plot(points*1000,pv['S']*1000,label='Autonomous P');bx.plot(points*1000,100*(pv['S']-cv['S'])/cv['S'][-1]);budget=1
                ax.set_ylabel('Cumulative solute (g)');bx.set_ylabel('Residual / C endpoint solute (%)')
                for xx in (ax,bx):xx.set_xlabel('Modeled beverage mass (g)')
            else:
                d=report['cases'][key]['sets']['base']['delivery'];x=np.arange(1,6)
                ax.bar(x-.18,d['C']['TDS_percent'],.36,label='Native radial C');ax.bar(x+.18,d['P']['TDS_percent'],.36,label='Autonomous P');bx.bar(x,np.array(d['P']['TDS_percent'])-d['C']['TDS_percent']);budget=.10
                ax.set_ylabel('Fraction TDS (%)');bx.set_ylabel('Fraction TDS residual (pp)')
                for xx in (ax,bx):xx.set_xlabel('Equal beverage-mass fraction');xx.set_xticks(x)
            bx.axhline(budget,ls='--',color='red',label='Peak engineering budget');bx.axhline(-budget,ls='--',color='red');bx.axhline(0,color='grey',lw=.5)
            ax.set_title(f'{law} / {pressure} bar',fontsize=9);bx.set_title(f'P − C; B*={end*1000:.5f} g; common coverage={100*sup["coverage"]:.3f}%',fontsize=8)
            ax.grid(alpha=.2);bx.grid(alpha=.2)
        axs[0,0].legend(fontsize=8);axs[0,1].legend(fontsize=8);fig.suptitle('Source-conditioned synthetic comparison; physical validation not established\nTR dilute continuation; SW water anchoring / 90 C extrapolation',fontsize=10);fig.tight_layout();fig.savefig(a.output/(kind+'.svg'),metadata={'Date':None});plt.close(fig)
if __name__=='__main__':main()
