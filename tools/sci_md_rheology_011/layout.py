"""Presentation-only layout redraw; frozen native/scoring workflow is unchanged."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch
from .common import DOC, interface


def plot():
    plt.rcParams['svg.hashsalt']='SCI-MD-RHEOLOGY-011-layout'
    fig, axes=plt.subplots(1,2,figsize=(8,4.5))
    high,low='#e59442','#5ba4ce'
    for ax,label,r,inner,outer in [(axes[0],'A: fast core',14.5,high,low),
            (axes[1],'B: fast outer annulus',1000*float(interface()['binary64_repr']),low,high)]:
        ax.add_patch(Circle((0,0),29,color=outer))
        ax.add_patch(Circle((0,0),r,color=inner))
        ax.set(xlim=(-31,31),ylim=(-31,31),aspect='equal',title=label,xlabel='radial coordinate (mm)')
    fig.legend(handles=[Patch(color=high,label='High k: 25% area'),Patch(color=low,label='Low k: 75% area')],
               loc='lower center',ncol=2,frameon=False)
    fig.tight_layout(rect=(0,.09,1,1))
    fig.savefig(DOC/'layouts.svg',metadata={'Date':None})
    plt.close(fig)
    # Matplotlib emits trailing spaces in SVG path data; remove whitespace only.
    for path in DOC.glob("*.svg"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")

if __name__=='__main__':
    plot()
