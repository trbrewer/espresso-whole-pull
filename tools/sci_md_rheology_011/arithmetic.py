"""Independent 50-digit arithmetic on two native radial histories directly."""
from bisect import bisect_right
from decimal import Decimal, localcontext

def audit(e, c, endpoint):
    with localcontext() as ctx:
        ctx.prec = 50
        D = lambda x: Decimal.from_float(float(x))
        zero, hundred = Decimal(0), Decimal(100)
        def seq(d, k):
            return [D(x) for x in d[k]]
        for k in ('start_s', 'end_s', 'state_s', 'dt_s'):
            if seq(e,k) != seq(c,k):
                raise ValueError('independent native clock mismatch')
        qe, qc, dt = seq(e,'Q'), seq(c,'Q'), seq(c,'dt_s')
        se = [i/q for i,q in zip(seq(e,'Q_inner_native'),qe)]
        sc = [i/q for i,q in zip(seq(c,'Q_inner_native'),qc)]
        if any(q<=0 for q in qe+qc) or any(t<=0 for t in dt):raise ValueError('nonpositive denominator')
        den = sum(q*t for q,t in zip(qc,dt))
        result = dict(E_Qint=sum(abs(a-b)*t for a,b,t in zip(qe,qc,dt))/den,
                      E_Qpeak=max(abs(a-b)/b for a,b in zip(qe,qc)),
                      D_share_mean_pp=hundred*sum(q*abs(a-b)*t for q,a,b,t in zip(qc,se,sc,dt))/den,
                      D_share_peak_pp=hundred*max(abs(a-b) for a,b in zip(se,sc)))
        def hist(d):
            w,s = [zero],[zero]
            wp,sp = zero,zero
            for wn,sn in zip(seq(d,'water_kg'), seq(d,'solute_kg')):
                dw,ds = wn-wp,sn-sp
                if dw<=0 or ds<0:
                    raise ValueError('independent invalid increments')
                w.append(w[-1]+dw);s.append(s[-1]+ds);wp,sp=wn,sn
            return [a+b for a,b in zip(w,s)],s
        be,es = hist(e);bc,cs = hist(c);end=D(endpoint)
        if end>min(be[-1],bc[-1]):
            return {k:float(v) for k,v in result.items()}
        def at(b,s,x):
            if x<zero or x>b[-1]:
                raise ValueError('independent support')
            x=min(x,b[-1]);i=min(bisect_right(b,x)-1,len(b)-2)
            return s[i]+(x-b[i])*(s[i+1]-s[i])/(b[i+1]-b[i])
        points=sorted(set([zero,end]+[x for x in be+bc if x<end]))
        if at(bc,cs,end)<=0:raise ValueError('zero solute denominator')
        result['E_Spath']=max(abs(at(be,es,x)-at(bc,cs,x)) for x in points)/at(bc,cs,end)
        bounds=[end*Decimal(j)/Decimal(5) for j in range(6)]
        splits=[]
        for a,b in zip(bounds[:-1],bounds[1:]):
            de=at(be,es,b)-at(be,es,a);dc=at(bc,cs,b)-at(bc,cs,a)
            splits.append(hundred*abs(de/(b-a)-dc/(b-a)))
        result['D_TDS_pp']=max(splits)
        return {k:float(v) for k,v in result.items()}
