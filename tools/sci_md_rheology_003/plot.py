"""Compact model-output figures; all metrics use unthinned native intervals."""
import html
import numpy as np
from .laws import LAWS
from .analyze import calibrate
from tools.sci_md_rheology_002.run import CASES


def figures(data,output):
    for kind in ('flow','residual','solute'):
        parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="500" viewBox="0 0 1200 500">',
               '<rect width="1200" height="500" fill="white"/>','<g font-family="sans-serif" font-size="13" fill="#19232b">']
        for panel,name in enumerate(CASES):
            x0=70+panel*595;y0=350;width=500;height=280;curves=[]
            for law in LAWS:
                dd=data[law]['base'];c,w=dd[name]['C'],dd[name]['W'];xx=c['start_s']
                alpha=calibrate(dd[CASES[0]]['C'],dd[CASES[0]]['W'])
                if kind=='flow':yy=c['Q_m3_s']*1e6;unit='C outlet flow (mL/s)'
                elif kind=='residual':yy=100*(c['Q_m3_s']/(alpha*w['Q_m3_s'])-1);unit='Signed C/N residual (%)'
                else:yy=c['solute_kg']*1e3;unit='C cumulative outlet solute (g)';xx=c['end_s']
                curves.append((law,yy))
            ymax=max(float(max(y)) for _,y in curves)*1.06
            ymin=min(0.,min(float(min(y)) for _,y in curves)*1.06)
            scale=ymax-ymin
            parts += [f'<text x="{x0}" y="25">{html.escape(name)}: {unit}</text>',
                      f'<path d="M{x0},{y0-height} V{y0} H{x0+width}" fill="none" stroke="#333"/>']
            for j,(label,yy) in enumerate(curves):
                color=('#536d89','#b43e34','#26805c','#9851a6')[j]
                # Plot every native sample, with the zero-time first physical interval.
                pts=' '.join(f'{x0+t/30*width:.2f},{y0-(v-ymin)/scale*height:.2f}' for t,v in zip(xx,yy))
                parts += [f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>',
                          f'<text x="{x0}" y="{390+j*20}" fill="{color}">{label}</text>']
            for t in (0,10,20,30):parts.append(f'<text x="{x0+t/30*width-4}" y="370">{t} s</text>')
            for y in np.linspace(ymin,ymax,5):parts.append(f'<text x="{x0-55}" y="{y0-(y-ymin)/scale*height+4:.1f}">{y:.2f}</text>')
        parts+=['</g></svg>'];(output/(kind+'.svg')).write_text('\n'.join(parts)+'\n')
