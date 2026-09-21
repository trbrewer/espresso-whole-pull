"""Compact SVG plots from native per-step evidence (no source table)."""
import html
import numpy as np


def figures(data,output):
    for kind in ('flow','feedback','solute'):
        parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" viewBox="0 0 1000 430">',
               '<rect width="1000" height="430" fill="white"/>',
               '<g font-family="sans-serif" font-size="13" fill="#19232b">']
        for panel,(name,tt) in enumerate(data.items()):
            x0=65+panel*495;y0=340;width=405;height=270
            if kind=='flow': curves=[(t,tt[t]['Q_m3_s']*1e6) for t in ('W','C','N')];unit='Flow (mL/s)'
            elif kind=='feedback':curves=[('C native',tt['C']['Q_m3_s']*1e6),('C continuum',tt['C']['Q_cont_m3_s']*1e6),('W frozen continuum',tt['W']['Q_cont_m3_s']*1e6)];unit='Flow (mL/s)'
            else:curves=[(t,tt[t]['solute_kg']*1e3) for t in ('W','C','N')];unit='Cumulative outlet solute (g)'
            ymax=max(float(max(y)) for _,y in curves)*1.06
            parts += [f'<text x="{x0}" y="25">{html.escape(name)} — {unit}</text>',f'<path d="M{x0},{y0-height} V{y0} H{x0+width}" fill="none" stroke="#333"/>']
            for j,(label,yy) in enumerate(curves):
                color=('#536d89','#b43e34','#26805c')[j]
                xx=tt['C']['end_s'];ix=np.unique(np.r_[0,np.arange(0,len(xx),5),len(xx)-1]).astype(int)
                pts=' '.join(f'{x0+xx[i]/30*width:.2f},{y0-yy[i]/ymax*height:.2f}' for i in ix)
                parts += [f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>',f'<text x="{x0}" y="{375+j*17}" fill="{color}">{label}</text>']
            for t in (0,10,20,30):parts.append(f'<text x="{x0+t/30*width-4}" y="358">{t}</text>')
            for y in np.linspace(0,ymax,5):parts.append(f'<text x="{x0-45}" y="{y0-y/ymax*height+4:.1f}">{y:.2f}</text>')
        parts+=['</g></svg>'];(output/(kind+'.svg')).write_text('\n'.join(parts)+'\n')
