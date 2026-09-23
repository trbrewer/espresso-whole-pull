"""Compact public-safe synthetic figures on the sealed support."""
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import *
from .analyze import reference_data, checked_support
from .run import complete
from tools.sci_md_rheology_007.observer import history
from tools.sci_md_rheology_004.observer import at


def plot(art):
    sealed=checked_support(art);d,_,_,_=reference_data(art)
    for k,v in matrix().items():
        if v['model']=='E2':
            e=complete(art,[k])[k];d['new_'+k]=native(read(art/'runs'/e['id']/'case'/TRACE))
    m=json.loads((DOC/'METRICS.json').read_text());coverage=json.loads((DOC/'COVERAGE.json').read_text())
    plt.rcParams.update({'font.size':9,'svg.hashsalt':'rheology010'})
    cases=[(law,h) for law in LAWS for h in ('UP','DOWN')]
    for name in ('hydraulics','delivery','fractions'):
        fig,axes=plt.subplots(2,2,figsize=(10,6),constrained_layout=True)
        for ax,(law,h) in zip(axes.flat,cases):
            end=float(sealed['B_star_kg'][h]);key=law+'_'+h
            ax.set_title(('TR' if law==LAWS[0] else 'SW')+' / '+h)
            if name=='hydraulics':
                twin=ax.twinx()
                for model,style in [('C','-'),('E2','--')]:
                    x=d['new_'+model+'_'+key+'_base'];ax.plot(x['end_s'],x['Q']*1e6,style,label=model+' Q',color='#146a97')
                    twin.plot(x['end_s'],100*x['share'],style,label=model+' core share',color='#b85c12')
                ax.set(xlabel='Time (s)',ylabel='Native Q (mL/s)');twin.set_ylabel('Core flow share (%)',color='#b85c12');ax.legend(fontsize=7)
            elif name=='delivery':
                for config,model,style in [('old','C',':'),('new','C','-'),('new','E2','--')]:
                    x=history(d[config+'_'+model+'_'+key+'_base']);points=np.r_[x['B'][x['B']<end],end];y=at(x,'B',points)
                    ax.plot(points*1000,y['S']*1000,style,label=('Core-fast' if config=='old' else 'Annulus-fast')+' '+model)
                ax.set(xlabel='Beverage mass (g)',ylabel='Delivered solute (g)');ax.legend(fontsize=7)
            else:
                y=m['secondary'][key]['signed_fraction_TDS_new_minus_old_pp'];ax.bar(range(1,6),y,color='#146a97')
                ax.axhline(0,color='black',lw=.7);ax.axhline(.1,color='#b85c12',ls=':');ax.axhline(-.1,color='#b85c12',ls=':')
                ax.set(xlabel='Equal-beverage fraction',ylabel='New C − old C TDS (pp)',xticks=range(1,6))
        fig.suptitle({'hydraulics':'Annulus-fast native hydraulics and CORE allocation','delivery':'Mass-conditioned delivery — scored support only','fractions':'Resolved C contrast — signed fraction differences'}[name])
        fig.savefig(DOC/(name+'.svg'),metadata={'Date':None});plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for ax,h in zip(axes,('UP','DOWN')):
        for label,color in [('old_C','#777777'),('new_C','#146a97'),('new_E2','#b85c12')]:
            values=[x['scored_fraction_of_terminal']*100 for k,x in coverage.items() if k.startswith(label+'_') and '_'+h+'_' in k]
            ax.scatter(values,[label]*len(values),s=24,color=color,label=label)
        ax.set(title=h+'; B*='+sealed['B_star_kg'][h]+' kg',xlabel='Scored support / terminal beverage (%)');ax.axvline(100,color='black',ls=':')
    fig.savefig(DOC/'coverage.svg',metadata={'Date':None});plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    for ax,(law,h) in zip(axes.flat,cases):
        key=law+'_'+h;decisions=list(m['primary'][key]['decisions'].items())+list(m['secondary'][key]['decisions'].items())
        labels=[('E2/C ' if i<6 else 'C/C ')+k for i,(k,v) in enumerate(decisions)]
        vals=[v['value']/v['budget'] for k,v in decisions];u=[v['u_total']/v['budget'] for k,v in decisions]
        ax.barh(range(8),vals,xerr=u,color=['#146a97']*6+['#b85c12']*2,capsize=2)
        ax.set(yticks=range(8),yticklabels=labels,title=('TR' if law==LAWS[0] else 'SW')+'/'+h,xlabel='Magnitude ± empirical allowance / budget');ax.axvline(1,color='black',ls=':')
    fig.savefig(DOC/'budgets.svg',metadata={'Date':None});plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);plot(p.parse_args().artifacts)
