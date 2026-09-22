"""Compact flow and five-fraction comparisons; figures never supply metric samples."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tools.sci_md_rheology_002.run import rows,CASES
from .evidence import LAWS,completed

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();m=json.loads((a.output/'METRICS.json').read_text());_,_,ends=completed(a.artifacts)
    fig,axes=plt.subplots(2,2,figsize=(10,6),constrained_layout=True)
    for ax,(law,case) in zip(axes.flat,[(l,c) for l in LAWS for c in CASES]):
        for arm,color in [('C','#24548a'),('G','#cc6c22')]:
            slot=f'{law}_base_{case}_{arm}'
            if slot not in ends:continue
            d=rows(a.artifacts/ends[slot]['attempt']/'case')
            ax.stairs(1e6*d['Q_m3_s'],list(d['start_s'])+[d['end_s'][-1]],label=arm,color=color,lw=1.4)
        ax.set(title=law+' / '+case,xlabel='Time (s)',ylabel='Flow (mL/s)',xlim=(0,30));ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Independent bulk G versus local C — source-conditioned model outputs')
    fig.savefig(a.output/'flow.svg');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,6),constrained_layout=True)
    for ax,(law,case) in zip(axes.flat,[(l,c) for l in LAWS for c in CASES]):
        v=m['comparisons'][law+'/'+case]['sets'].get('base')
        if not v:continue
        for arm,offset,color in [('C',-.18,'#24548a'),('G',.18,'#cc6c22')]:
            ax.bar([i+offset for i in range(1,6)],v['delivery'][arm]['TDS_percent'],width=.35,label=arm,color=color)
        ax.set(title=law+' / '+case,xlabel='Equal beverage-mass fraction (zero to B*)',ylabel='Fraction TDS (%)',xticks=range(1,6));ax.legend()
    fig.suptitle('Conservative five-fraction observation — not physical validation')
    fig.savefig(a.output/'fraction_tds.svg');plt.close(fig)
if __name__=='__main__':main()
