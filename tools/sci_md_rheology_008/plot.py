"""Unsmoothed native interval curves and exact mass-fraction outputs."""
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import *
from .analyze import load
from .observer import history
from tools.sci_md_rheology_004.observer import at
from tools.sci_md_rheology_007.analyze import load as load_p
from tools.sci_md_rheology_007.observer import compose

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    c,e,_,_=load(a.artifacts);loc=json.loads((a.artifacts/'LOCATIONS.json').read_text())
    _,paths,_,missing,_=load_p(Path(loc['accepted_p']),Path(loc['accepted']))
    if missing:raise ValueError('P plot evidence missing')
    support=json.loads((DOC/'SUPPORT.json').read_text())['inherited']['support']
    plt.rcParams.update({'svg.hashsalt':'SCI-MD-RHEOLOGY-008','font.size':9})
    colors=dict(C='black',P='#777777',E2='#d95f02',E4='#1b9e77',E8='#7570b3')
    for kind in ('flow','share','solute','fractions'):
        fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
        for ax,(law,pressure) in zip(axes.flat,[(law,p) for law in LAWS for p in (3,9)]):
            key=f'{law}_{pressure}bar_base';end=support[str(pressure)]['B_star_kg']
            data=dict(C=c[key],P=compose(paths[key+'_inner'],paths[key+'_outer']))
            data.update({f'E{n}':e[f'E{n}_{key}'] for n in (2,4,8) if f'E{n}_{key}' in e})
            for j,(name,d) in enumerate(data.items()):
                h=history(d);kwargs=dict(label=name,color=colors[name],linewidth=1.2,linestyle='--' if name=='P' else '-')
                if kind in ('flow','share'):
                    y=d['Q']*1e6 if kind=='flow' else d['share']*100
                    ax.stairs(y,np.r_[d['start_s'][0],d['end_s']],**kwargs)
                    ax.set(xlabel='Time (s)',ylabel='Outlet Q (mL/s)' if kind=='flow' else 'Core outlet share (%)')
                elif kind=='solute':
                    b=np.unique(np.r_[h['B'][h['B']<end],min(end,h['B'][-1])])
                    ax.plot(b*1000,at(h,'B',b)['S']*1000,**kwargs);ax.set(xlabel='Beverage mass (g)',ylabel='Delivered solute (g)')
                elif h['B'][-1]>=end:
                    s=at(h,'B',np.linspace(0,end,6))['S'];ax.plot(np.arange(1,6),100*np.diff(s)/(end/5),marker='o',**kwargs);ax.set(xlabel='Equal beverage-mass fraction',ylabel='Fraction TDS (%)',xticks=range(1,6))
            ax.set_title(law+f' / {pressure} bar');ax.grid(alpha=.2);ax.legend()
        fig.savefig(a.output/(kind+'.svg'),metadata={'Date':None});plt.close(fig)
if __name__=='__main__':main()
