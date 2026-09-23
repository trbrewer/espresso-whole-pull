"""Focused static export figures from qualified bounded evidence."""
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import *
from tools.sci_md_rheology_002.verify import traces
from tools.sci_md_rheology_007.observer import history as delivery_history

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();art=a.artifacts
    verify(art,'FREEZE.json',True)
    result=json.loads((DOC/'METRICS.json').read_text());sealed=json.loads((DOC/'SUPPORT.json').read_text())
    figs={name:plt.subplots(2,2,figsize=(10,7),constrained_layout=True) for name in ('pressure','flow','share','solute','fractions','budgets')}
    for i,law in enumerate(LAWS):
        for j,h in enumerate(HISTORIES):
            title=('TR' if i==0 else 'SW')+' / '+h
            for name,(fig,axes) in figs.items():axes[i,j].set_title(title);axes[i,j].grid(alpha=.2)
            axes=figs['pressure'][1];axes[i,j].plot(TIMES,np.array(HISTORIES[h])/1e5,'k--',label='imposed')
            for model in ('C','E2'):
                case=art/'full'/f'{model}_{law}_{h}_base'/'case';d=native(read(case/TRACE));t=d['end_s'];hist=delivery_history(d)
                axes[i,j].plot(t,traces(case)['inlet_pressure_Pa']/1e5,label=model+' applied')
                figs['flow'][1][i,j].plot(t,d['Q']*1e6,label=model)
                figs['share'][1][i,j].plot(t,d['share']*100,label=model)
                figs['solute'][1][i,j].plot(hist['B']*1000,hist['S']*1000,label=model)
            figs['solute'][1][i,j].axvline(float(sealed['B_star_kg'][h])*1000,color='k',linestyle=':',label='support')
            record=result['cases'][law+'_'+h];base=record['variants']['base'];delivery=base.get('delivery')
            if delivery:
                # Derive exact five mass increments using the already qualified native observer.
                from tools.sci_md_rheology_004.observer import at
                for model,offset in [('C',-.18),('E2',.18)]:
                    d=native(read(art/'full'/f'{model}_{law}_{h}_base'/'case'/TRACE));hist=delivery_history(d);end=float(sealed['B_star_kg'][h]);edges=np.linspace(0,end,6)
                    ss=np.interp(edges,hist['B'],hist['S']);tds=100*np.diff(ss)/np.diff(edges)
                    figs['fractions'][1][i,j].bar(np.arange(1,6)+offset,tds,width=.36,label=model)
            dec=record['decisions'];ax=figs['budgets'][1][i,j];ks=list(BUDGETS)
            ax.bar(np.arange(6),[dec[k]['value']/dec[k]['budget'] if dec[k]['value'] is not None else np.nan for k in ks],yerr=[dec[k]['u_total']/dec[k]['budget'] if dec[k]['u_total'] is not None else 0. for k in ks],capsize=3)
            for index,k in enumerate(ks):
                if dec[k]['value'] is None or dec[k]['u_total'] is None:ax.text(index,0.,'UNRESOLVED',rotation=90,fontsize=7)
            ax.axhline(1,color='r',linestyle='--');ax.set_xticks(np.arange(6),['Qint','Qpeak','smean','speak','Spath','TDS'],rotation=30)
    labels={'pressure':('time (s)','bed-inlet gauge pressure (bar)'),'flow':('time (s)','outlet flow (mL/s)'),'share':('time (s)','core outlet share (%)'),'solute':('beverage (g)','delivered solute (g)'),'fractions':('equal beverage fraction','fraction TDS (%)'),'budgets':('metric','metric ± empirical allowance / budget')}
    for name,(fig,axes) in figs.items():
        for ax in axes.flat:
            ax.set_xlabel(labels[name][0]);ax.set_ylabel(labels[name][1])
            if name!='budgets':ax.legend(fontsize=8)
        fig.savefig(DOC/(name+'.svg'));plt.close(fig)
if __name__=='__main__':main()
