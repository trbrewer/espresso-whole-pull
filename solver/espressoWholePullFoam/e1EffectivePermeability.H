// SPDX-License-Identifier: GPL-3.0-or-later
// PRESSURE-PEAK B0c E1: lumped whole-bed closure, not local effective stress.
#ifndef e1EffectivePermeability_H
#define e1EffectivePermeability_H
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace espresso
{
struct E1Parameters
{
    double a, pstar, tau, mc, onsetC, onsetN, earlyPressureBar;

    void validate() const
    {
        for (double x : {a, pstar, tau, mc, onsetC, earlyPressureBar})
            if (!std::isfinite(x) || x <= 0)
                throw std::invalid_argument("E1 positive finite parameter required");
        if (!std::isfinite(onsetN))
            throw std::invalid_argument("E1 finite onset exponent required");
    }
    double delay() const
    {
        const double d = onsetC*std::pow(earlyPressureBar, -onsetN);
        if (!std::isfinite(d) || d <= 0)
            throw std::invalid_argument("E1 invalid predictive onset");
        return d;
    }
    double swelling() const { return std::exp(-delay()/tau); }
    double resistance(double massG) const
    {
        if (!std::isfinite(massG) || massG < 0)
            throw std::invalid_argument("E1 invalid cumulative outlet liquid mass");
        return std::exp(std::exp(-massG/mc));
    }
    double multiplier(double inletGaugePa, double massG) const
    {
        if (!std::isfinite(inletGaugePa))
            throw std::invalid_argument("E1 invalid inlet gauge pressure");
        const double p = std::max(inletGaugePa/1e5, 0.0);
        const double value = swelling()*std::exp(-p/pstar)/resistance(massG);
        if (!std::isfinite(value) || value <= 0)
            throw std::invalid_argument("E1 nonpositive permeability multiplier");
        return value;
    }
    double basePermeability(double mu, double depth, double rho, double area) const
    {
        return a*1e-3*mu*depth/(rho*area*1e5);
    }
};
}
#endif
