#!/usr/bin/env python3
"""Independent closed-form pressure schedule reference (verification only)."""
from bisect import bisect_right
import math
from fractions import Fraction
from decimal import Decimal, localcontext

class Schedule:
    def __init__(self, times, pressures, start=None, end=None):
        if not isinstance(times,list) or not isinstance(pressures,list) or len(times)<2 or len(times)!=len(pressures):
            raise ValueError('XSV_PRESSURE_001_INVALID_SCHEDULE')
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in times):
            raise ValueError('XSV_PRESSURE_001_INVALID_SCHEDULE')
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in pressures):
            raise ValueError('XSV_PRESSURE_001_INVALID_TARGET_PRESSURE')
        if any(b<=a or not math.isfinite(b-a) for a,b in zip(times,times[1:])):
            raise ValueError('XSV_PRESSURE_001_INVALID_SCHEDULE')
        if (start is not None and times[0]>start) or (end is not None and times[-1]<end):
            raise ValueError('XSV_PRESSURE_001_INVALID_SCHEDULE')
        self.t,self.p=times[:],pressures[:]
        self.qt=[Fraction(str(x)) for x in times]
        self.qp=[Fraction(str(x)) for x in pressures]

    def _target(self,t):
        i=min(bisect_right(self.qt,t)-1,len(self.qt)-2)
        return self.qp[i]+(self.qp[i+1]-self.qp[i])*(t-self.qt[i])/(self.qt[i+1]-self.qt[i])

    def target(self,t):
        if not math.isfinite(t) or not self.t[0]<=t<=self.t[-1]:
            raise ValueError('XSV_PRESSURE_001_TIME_OUTSIDE_SUPPORT')
        return float(self._target(Fraction(str(t))))

    def positive_pieces(self,a,b,pf):
        self.target(a); self.target(b)
        if b<a or not math.isfinite(pf): raise ValueError('XSV_PRESSURE_001_INVALID_SCHEDULE')
        a,b,pf=(Fraction(str(x)) for x in (a,b,pf))
        cuts=[a]+[t for t in self.qt if a<t<b]+[b]
        for lo,hi in zip(cuts,cuts[1:]):
            if hi==lo: continue
            x,y=self._target(lo)-pf,self._target(hi)-pf
            slope=(y-x)/(hi-lo)
            if max(x,y)<=0: continue
            if x<0: lo=lo-x/slope; x=Fraction(0)
            if y<0: hi=hi-y/slope; y=Fraction(0)
            yield lo,hi,x,y,slope

    def integral(self,a,b,pf):
        # Rational segment geometry avoids threshold-time rounding in the oracle.
        return float(sum(((hi-lo)*(x+y)/2 for lo,hi,x,y,m in self.positive_pieces(a,b,pf)),Fraction(0)))

    def crossing(self,a,b,required,pf):
        if not math.isfinite(required) or required<0:
            raise ValueError('XSV_PRESSURE_001_CROSSING_UNREACHABLE')
        pieces=list(self.positive_pieces(a,b,pf))
        required=Fraction(str(required))
        total=sum(((hi-lo)*(x+y)/2 for lo,hi,x,y,m in pieces),Fraction(0))
        if required>total:raise ValueError('XSV_PRESSURE_001_CROSSING_UNREACHABLE')
        if required==0:return a
        for lo,hi,x,y,m in pieces:
            area=(hi-lo)*(x+y)/2
            if required<=area:
                if required==area:return float(hi)
                with localcontext() as context:
                    context.prec=80
                    dec=lambda q:Decimal(q.numerator)/Decimal(q.denominator)
                    r,initial,slope=map(dec,(required,x,m))
                    duration=2*r/(initial+(initial*initial+2*slope*r).sqrt()) if slope else r/initial
                    return float(dec(lo)+duration)
            required-=area
        raise ValueError('XSV_PRESSURE_001_CROSSING_UNREACHABLE')

    def maximum(self): return max(self.p)
