"""Render three bounded diagnostic figures; never invokes native tools."""
import json
from .observe import DOC


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=json.loads((DOC/'RESULT.json').read_text());cases=r['cases']
    keys=sorted(cases)
    labels=[k.replace('SW_WATER_ANCHORED_90C','SW').replace('TR_LINEAR','TR').replace('_base','') for k in keys]
    for name,quantity,title in (
        ('compartments','solid_depletion_edge_minus_center_pp','Solid-depletion contrast: edge minus center'),
        ('composite','composite_R_plus_L_edge_minus_center_pp','Recoverable composite (R + L) / initial dry mass'),
    ):
        fig,ax=plt.subplots(figsize=(10,6))
        for idx,q in enumerate((.31,.34)):
            values=[cases[k]['partitions'][idx][quantity] for k in keys]
            ax.plot(values,range(len(keys)),'o' if idx==0 else 'x',label=f'q={q}')
        ax.axvline(0,color='gray',lw=.7);ax.set_yticks(range(len(keys)),labels);ax.set_xlabel('Edge minus center (percentage points)')
        ax.set_title(title+'\nSynthetic stored-field diagnostic; no source comparison')
        ax.legend();fig.tight_layout();fig.savefig(DOC/(name+'.svg'));plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6))
    for survival,style in (('retain','o'),('remove','x')):
        vals=[100*cases[k]['partitions'][0]['forward_models']['Sworks High Flow_'+survival+'_pore_solute']['assay']['edge_minus_center_fraction'] for k in keys]
        ax.plot(vals,range(len(keys)),style,label=survival+' pore solute')
    ax.axvline(0,color='gray',lw=.7);ax.set_yticks(range(len(keys)),labels)
    ax.set_xlabel('Apparent Sworks-formula edge minus center (percentage points)')
    ax.set_title('Conditional drainage sensitivity, q=0.31\nComplete recovery; no handling loss; model cup anchor')
    ax.legend();fig.tight_layout();fig.savefig(DOC/'conditional.svg');plt.close(fig)
    lines=['# SCI-MD-RADIAL-OBS-001 retained-field diagnostic','',
           'The assay identifies sheet-specific recoverable-solute composites. Solid depletion requires additional assumptions about retained pore solute, recovery, initial regional inventory and sample handling. The forward operator is CONDITIONAL; PHYSICAL_VALIDATION=NOT_ESTABLISHED.','',
           f"Observed {len(cases)} retained base snapshots and {sum(len(c['partitions']) for c in cases.values())} case/partition evaluations. Old E2 remains historical evidence. No new E2 accuracy or spatial-transfer qualification follows from these snapshots. No source-EWP fit, ranking or treatment-effect claim is made.",'',
           'The source-inspired q=.31 and .34 values are explicit synthetic initial-mass cuts in the uniform cylinder. They are not measured cutter radii. Native oriented mesh volumes and annular overlap conserve inventories; cell averages remain constant through partial cells. E2 has unresolved structure within its annulus.','',
           'Table values are edge minus center, in percentage points of regional initial dry coffee. Composite is remaining solid plus retained dissolved solute. Apparent EY uses Sworks algebra under complete no-loss recovery, pore solute retained and synthetic LRR=0. No measured source anchor is used.','',
           '| Case | q | Solid depletion | Retained pore solute | Composite | Conditional apparent EY |',
           '|---|---:|---:|---:|---:|---:|']
    for k in keys:
        for x in cases[k]['partitions']:
            ey=100*x['forward_models']['Sworks High Flow_retain_pore_solute']['assay']['edge_minus_center_fraction']
            lines.append(f"| {k} | {x['q']} | {x['solid_depletion_edge_minus_center_pp']:.6f} | {x['retained_dissolved_edge_minus_center_pp']:.6f} | {x['composite_R_plus_L_edge_minus_center_pp']:.6f} | {ey:.6f} |")
    lines += ['', 'Each region\'s masses, dry residue, recovery water/beverage, both workbook conventions, both pore-solute survival examples and matched C/E2 differences are in [RESULT.json](RESULT.json). Undefined source inputs are explicit. These extreme handling assumptions are sensitivity examples, not confidence intervals.', '',
              '![Solid depletion](compartments.svg)','![Composite](composite.svg)','![Conditional handling sensitivity](conditional.svg)','',
              'SOURCE_RECONSTRUCTION is reported by the linked Puckworks artifact. FORWARD_ASSAY_MAP=CONDITIONAL; IDENTIFIED_OBSERVABLE=sheet-specific corrected recoverable-solute contrast (see Puckworks measurement map); EWP_FIELD_DIAGNOSTIC='+r['EWP_FIELD_DIAGNOSTIC']+'.', '',
              'NEW_NATIVE_INTEGRATIONS=0; NEW_NATIVE_BUILDS=0; PRODUCTION_DEFAULTS_AND_LOCK=UNCHANGED. No source coffee/geometry/endpoint/pressure match; no new physical validation, production adoption or successor.']
    if r['missing']:
        lines += ['', 'Named missing/partial cases:'] + [f'- {k}: {v}' for k,v in r['missing'].items()]
    (DOC/'RESULT.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
