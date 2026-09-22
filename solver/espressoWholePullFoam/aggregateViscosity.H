// SPDX-License-Identifier: GPL-3.0-or-later
// Shared by the native solver and standalone equivalence verifier. No Python.
#ifndef aggregateViscosity_H
#define aggregateViscosity_H
#include <algorithm>
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace espresso {
struct AggregateStorage {
    double poreVolume=0, dissolvedMass=0;
    void add(double phi, double c, double volume) {
        if (!std::isfinite(phi) || phi<=0 || phi>1
            || !std::isfinite(volume) || volume<=0
            || !std::isfinite(c) || c<0)
            throw std::runtime_error("RHEOLOGY_INVALID_STORAGE_CELL");
        poreVolume += phi*volume;
        dissolvedMass += phi*c*volume;
    }
};
struct AggregateViscosity {
    std::vector<double> w, mu;
    double rho=965, temperature=363.15;
    explicit AggregateViscosity(const std::string& path) {
        std::ifstream f(path);
        std::string magic, basis, units, interpolation;
        double dilute, upper;
        if (!(f >> magic >> basis >> units >> interpolation >> temperature >> rho >> dilute >> upper)
            || magic!="EWP_AGGREGATE_V1" || basis!="wet_mass_fraction"
            || units!="Pa.s" || interpolation!="linear" || temperature!=363.15
            || rho!=965 || dilute!=0.10 || upper!=0.24)
            throw std::runtime_error("RHEOLOGY_TABLE_CONTRACT");
        double x,y;
        while (true) {
            f >> std::ws;
            if (f.eof()) break; // EOF is allowed only before an entry starts.
            if (!(f >> x >> y) || !std::isfinite(x) || !std::isfinite(y) || y<=0
                || x<0 || x>upper || (!w.empty() && x<=w.back()))
                throw std::runtime_error("RHEOLOGY_TABLE_ENTRIES");
            w.push_back(x); mu.push_back(y);
        }
        if (!f.eof() || w.size()<3 || w.front()!=0 || w.back()!=upper
            || std::find(w.begin(),w.end(),dilute)==w.end())
            throw std::runtime_error("RHEOLOGY_TABLE_COVERAGE");
    }
    double fraction(double c) const {
        if (!std::isfinite(c) || c<0) throw std::runtime_error("RHEOLOGY_NEGATIVE_OR_NONFINITE_STATE");
        return c/(rho+c);
    }
    // Inputs are globally reduced exactly once by the caller. Extensive units:
    // dissolved mass [kg], pore-water volume [m3]. No resistance weighting.
    double bulkFraction(double dissolvedMass, double poreVolume) const {
        if (!std::isfinite(dissolvedMass) || dissolvedMass<0
            || !std::isfinite(poreVolume) || poreVolume<=0)
            throw std::runtime_error("RHEOLOGY_INVALID_BULK_STORAGE");
        return fraction(dissolvedMass/poreVolume);
    }
    double value(double x) const {
        if (!std::isfinite(x) || x<0 || x>w.back())
            throw std::runtime_error("RHEOLOGY_SOURCE_DOMAIN");
        auto it=std::lower_bound(w.begin(),w.end(),x);
        auto i=it-w.begin();
        if (i==0) return mu[0];
        double a=(x-w[i-1])/(w[i]-w[i-1]);
        return mu[i-1]+a*(mu[i]-mu[i-1]);
    }
};
}
#endif
