"""Display all base native mass breakpoints; plotting never supplies metrics."""
import numpy as np
from .observer import at


def figures(curves,report,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt']='SCI-MD-RHEOLOGY-004'
    for name in ('coordinates','discrepancy','fraction_tds','timing'):
        fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
        for ax,(key,h) in zip(axes.flat,curves.items()):
            law,scenario=key.split('/');end=report['support'][scenario]['B']
            ax.set_title(f'{law}\n{scenario}; beverage support 0–{end*1000:.6f} g',fontsize=10)
            if 'N' not in h:
                ax.text(.1,.5,'Native N unavailable');continue
            if name=='coordinates':
                for arm,color in (('C','tab:blue'),('N','tab:orange')):
                    x=np.r_[h[arm]['B'][h[arm]['B']<end],end]
                    ax.plot(x*1000,at(h[arm],'B',x)['S']*1000,label=arm+' vs beverage',color=color)
                inset=ax.inset_axes([.50,.12,.46,.40])
                for arm in ('C','N'):inset.plot(h[arm]['t'],h[arm]['S']*1000,label=arm)
                inset.set(xlabel='Time (s), 0–30',ylabel='Solute (g)');inset.tick_params(labelsize=7)
                ax.set(xlabel='Modeled beverage (g)',ylabel='Outlet aggregate solute (g)')
            elif name=='discrepancy':
                x=np.unique(np.r_[0,h['C']['B'][h['C']['B']<end],h['N']['B'][h['N']['B']<end],end])
                a,b=at(h['C'],'B',x),at(h['N'],'B',x)
                ax.plot(x*1000,100*(a['S']-b['S'])/b['S'][-1],label='Signed C−N / terminal N')
                ax.axhline(5,color='grey',ls='--');ax.axhline(-5,color='grey',ls='--')
                ax.set(xlabel='Modeled beverage (g)',ylabel='Solute discrepancy (% of terminal N)')
            elif name=='fraction_tds':
                m=report['comparisons'][key]['sets']['base']['B']['C_N'];x=np.arange(1,6)
                for a,offset,label in (('C',-.18,'C'),('R',.18,'N')):ax.bar(x+offset,m[a]['TDS_percent'],width=.36,label=label)
                ax.set(xlabel='Equal beverage-mass fraction (first through fifth)',ylabel='Fraction TDS (%)',xticks=x)
            else:
                for arm in ('C','N'):
                    x=np.r_[h[arm]['B'][h[arm]['B']<end],end]
                    ax.plot(x*1000,at(h[arm],'B',x)['t'],label=arm)
                ax.set(xlabel='Modeled beverage (g)',ylabel='Time to output (s)')
            ax.legend(fontsize=8);ax.grid(alpha=.2)
        fig.savefig(output/(name+'.svg'),metadata={'Date':None});plt.close(fig)
