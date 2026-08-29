"""Deterministic supporting plots for SCI-MD-009 tables."""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def save(out,name,x,y,xlabel,ylabel,groups=None):
    fig,ax=plt.subplots(figsize=(6.4,4));
    if groups:
        for label,xx,yy in groups:ax.plot(xx,yy,marker='o',label=label)
        ax.legend(fontsize=7)
    else:ax.plot(x,y,marker='o')
    ax.set(xlabel=xlabel,ylabel=ylabel);ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/f'{name}.svg');plt.close(fig)
def generate(out:Path):
    out=Path(out); reg=rows(out/'DIMENSIONLESS_REGIME_MAP.csv'); traj=rows(out/'INVENTORY_CAPACITY_TRAJECTORIES.csv');loc=rows(out/'LOCAL_SENSITIVITY.csv')
    groups=[]
    for sp in ('caffeine','trigonelline'):
      x=[r for r in reg if r['species']==sp and r['condition_id']=='E7'];groups.append((sp,[float(r['Lambda_full']) for r in x],[float(r['normalized_shape'].split(';')[0]) for r in x]))
    save(out,'shape_across_lambda',[],[],'Lambda_full','first normalized fraction',groups)
    groups=[]
    for sp in ('caffeine','trigonelline'):
      x=[r for r in reg if r['species']==sp and r['condition_id']=='E7'];groups.append((sp,[float(r['Lambda_full']) for r in x],[float(r['absolute_extracted_mass_kg']) for r in x]))
    save(out,'absolute_across_lambda',[],[],'Lambda_full','extracted mass (kg)',groups)
    x=[r for r in traj if r['condition_id']=='E7' and r['species']=='caffeine' and r['inventory_scale']=='1.0'];save(out,'lambda_wet',range(1,len(x)+1),[float(r['Lambda_wet']) for r in x],'fraction','Lambda_wet')
    groups=[]
    for p in ('M0','k','Csat','D'):
      x=[r for r in loc if r['condition_id']=='E7' and r['species']=='caffeine' and r['parameter']==p and r['step']=='0.01'];groups.append((p,[int(r['fraction_index']) for r in x],[float(r['elasticity']) for r in x]))
    save(out,'elasticity',[],[],'fraction','elasticity',groups)
    ident=json.loads((out/'IDENTIFIABILITY_RESULTS.json').read_text())
    c=np.array(ident['combined']['caffeine']['correlation']);fig,ax=plt.subplots();im=ax.imshow(c,vmin=-1,vmax=1,cmap='coolwarm');fig.colorbar(im);ax.set_xticks(range(3),['M0','k','Csat']);ax.set_yticks(range(3),['M0','k','Csat']);fig.tight_layout();fig.savefig(out/'parameter_correlation.svg');plt.close(fig)
    groups=[(sp,range(1,4),ident['combined'][sp]['singular_values']) for sp in ('caffeine','trigonelline')];save(out,'singular_values',[],[],'index','singular value',groups)
    prof=rows(out/'PROFILE_RESULTS.csv');groups=[]
    for p in ('M0','k','Csat'):
      x=[r for r in prof if r['species']=='caffeine' and r['parameter']==p];groups.append((p,[float(r['log_offset']) for r in x],[float(r['profile_error']) for r in x]))
    save(out,'profiles',[],[],'log offset','profile error',groups)
    rec=rows(out/'SYNTHETIC_RECOVERY.csv');groups=[]
    for sp in ('caffeine','trigonelline'):
      x=[r for r in rec if r['species']==sp and r['noise_relative']=='0.02'];groups.append((sp,range(len(x)),[float(r['relative_error']) for r in x]))
    save(out,'synthetic_recovery',[],[],'synthetic replicate','relative M0 error',groups)
    front=rows(out/'PRECISION_FRONTIER.csv');groups=[]
    for sp in ('caffeine','trigonelline'):
      xx=sorted({float(r['inventory_relative_uncertainty']) for r in front});yy=[np.mean([float(r['pass_fraction']) for r in front if r['species']==sp and float(r['inventory_relative_uncertainty'])==u]) for u in xx];groups.append((sp,xx,yy))
    save(out,'precision_frontier',[],[],'inventory uncertainty','passing fraction',groups)
    sep=rows(out/'MODEL_SEPARATION.csv');save(out,'model_separation',range(len(sep)),[float(r['B0_B1']) for r in sep],'condition/species block','B0-B1 norm')
    pareto=rows(out/'PILOT_DESIGN_PARETO.csv');x=[r for r in pareto if r['viable']=='True'];save(out,'pilot_pareto',[int(r['shots']) for r in x],[int(r['chromatography_injections']) for r in x],'shots','injections')
    design=json.loads((out/'MINIMUM_PILOT_DESIGN.json').read_text());names=['minimum','robust'];save(out,'pilot_layout',names,[design[n]['shots'] for n in names],'design','shots')

