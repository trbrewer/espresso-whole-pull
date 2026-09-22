"""Independent 50-digit Decimal reduction from native binary64 input values.

Recomputes weighting, cumulative increments, shares, breakpoint interpolation and
fraction splitting; does not call the float comparison implementation.
"""
from bisect import bisect_right
from decimal import Decimal, localcontext

def audit(inner,outer,c,endpoint):
    with localcontext() as ctx:
        ctx.prec=50
        D=lambda x:Decimal.from_float(float(x))
        zero=Decimal(0);one=Decimal(1);hundred=Decimal(100)
        def seq(d,k):return [D(v) for v in d[k]]
        def cumulative(d,k):
            prev=zero;inc=[]
            for v in seq(d,k):inc.append(v-prev);prev=v
            return inc
        weights=[Decimal('0.25'),Decimal('0.75')]
        def weighted(k,inc=False):
            a,b=[cumulative(d,k) if inc else seq(d,k) for d in (inner,outer)]
            return [weights[0]*x+weights[1]*y for x,y in zip(a,b)]
        qi=seq(inner,'Q');qp=weighted('Q');qc=seq(c,'Q');dt=seq(c,'dt_s');sp=[weights[0]*x/y for x,y in zip(qi,qp)];sc=seq(c,'share')
        # Native C share must be recomputed before entry by caller for full arithmetic audit.
        if 'Q_inner_native' in c:sc=[x/y for x,y in zip(seq(c,'Q_inner_native'),qc)]
        den=sum(q*t for q,t in zip(qc,dt))
        result=dict(E_Qint=sum(abs(p-r)*t for p,r,t in zip(qp,qc,dt))/den,E_Qpeak=max(abs(p-r)/r for p,r in zip(qp,qc)),D_share_mean_pp=hundred*sum(q*abs(p-r)*t for q,p,r,t in zip(qc,sp,sc,dt))/den,D_share_peak_pp=hundred*max(abs(p-r) for p,r in zip(sp,sc)))
        def hist(wi,si):
            w=[zero];s=[zero]
            for dw,ds in zip(wi,si):w.append(w[-1]+dw);s.append(s[-1]+ds)
            return [x+y for x,y in zip(w,s)],s
        bp,ss=hist(weighted('water_kg',True),weighted('solute_kg',True));bc,cs=hist(cumulative(c,'water_kg'),cumulative(c,'solute_kg'))
        end=D(endpoint)
        def at(b,s,x):
            i=min(bisect_right(b,x)-1,len(b)-2)
            if x<0 or x-b[-1]>Decimal('1e-14'):raise ValueError('Decimal support')
            # Snap only inherited mass-roundoff floor at the shared endpoint.
            x=min(x,b[-1])
            return s[i]+(x-b[i])*(s[i+1]-s[i])/(b[i+1]-b[i])
        points=sorted(set([zero,end]+[x for x in bp+bc if x<end]));sd=at(bc,cs,end)
        result['E_Spath']=max(abs(at(bp,ss,x)-at(bc,cs,x)) for x in points)/sd
        boundaries=[end*Decimal(j)/Decimal(5) for j in range(6)]
        diff=[at(bp,ss,x)-at(bc,cs,x) for x in boundaries]
        result['D_TDS_pp']=hundred*max(abs(diff[j+1]-diff[j])/(boundaries[j+1]-boundaries[j]) for j in range(5))
        return {k:float(v) for k,v in result.items()}
