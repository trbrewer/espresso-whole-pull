// Synthetic code-verification fixtures; no scientific property data.
#include "../../solver/espressoWholePullFoam/aggregateViscosity.H"
#include <cassert>
#include <iostream>
void close(double a,double b) { assert(std::abs(a-b)<1e-12*std::max(1.,std::abs(b))); }
int main(int argc,char**argv) {
    espresso::AggregateViscosity law(argv[1]), constant(argv[2]);
    espresso::AggregateStorage s, scaled, subdivided, uniform;
    s.add(.2,20,3); s.add(.6,160,2);
    close(s.poreVolume,1.8); close(s.dissolvedMass,204);
    for(int i=0;i<7;++i) {subdivided.add(.2,20,3./7);subdivided.add(.6,160,2./7);}
    scaled.add(.2,20,3*19.);scaled.add(.6,160,2*19.);
    double w=law.bulkFraction(s.dissolvedMass,s.poreVolume);
    close(w,204/(965*1.8+204));
    close(w,law.bulkFraction(scaled.dissolvedMass,scaled.poreVolume));
    close(w,law.bulkFraction(subdivided.dissolvedMass,subdivided.poreVolume));
    uniform.add(.2,90,3);uniform.add(.6,90,2);
    close(law.value(law.bulkFraction(uniform.dissolvedMass,uniform.poreVolume)),law.value(law.fraction(90)));
    close(constant.value(w),constant.value(law.fraction(160)));
    // Series resistance weights V/k, distinct from phi*V. A cancels here.
    double equivalent=(3/1.*law.value(law.fraction(20))+2/4.*law.value(law.fraction(160)))/(3/1.+2/4.);
    assert(std::abs(law.value(w)-equivalent)>1e-5);
    assert(std::abs(w-(law.fraction(20)+law.fraction(160))/2)>1e-3);
    bool rejected=false;
    try { law.value(law.fraction(400)); } catch(const std::exception&) {rejected=true;}
    assert(rejected); // bulk can be valid despite an invalid local cell.
    espresso::AggregateStorage invalidMean;invalidMean.add(.4,400,.001);invalidMean.add(.4,0,1);
    assert(law.value(law.bulkFraction(invalidMean.dissolvedMass,invalidMean.poreVolume))>0);
    for(double c : {-1.,double(NAN)}) {rejected=false;try{s.add(.4,c,1);}catch(const std::exception&){rejected=true;}assert(rejected);}
    std::cout << "weighting scaling subdivision uniform constant heterogeneous domain PASS\n";
}
