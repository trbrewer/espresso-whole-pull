// SPDX-License-Identifier: GPL-3.0-or-later
// PW D0 form A: inlet-pressure compaction, outlet mass or extracted-solid recovery.
#ifndef formAWholeBedClosure_H
#define formAWholeBedClosure_H
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace espresso
{
struct FormAParameters
{
    double a, pstar, n, pd, mc, xc;

    void validate(bool localExtraction = false) const
    {
        for (double x : {a, pstar, pd, mc})
            if (!std::isfinite(x) || x <= 0)
                throw std::invalid_argument("Form A requires positive finite parameters");
        if (!std::isfinite(n) || n < 1)
            throw std::invalid_argument("Form A requires n >= 1");
        if (localExtraction && (!std::isfinite(xc) || xc <= 0 || xc > 1))
            throw std::invalid_argument("Form A A2 requires measured 0 < Xc <= 1");
    }

    double pressureMultiplier(double inletGaugePa) const
    {
        if (!std::isfinite(inletGaugePa))
            throw std::invalid_argument("Form A invalid inlet gauge pressure");
        const double p = std::max(inletGaugePa/1e5, 0.0);
        if (p == 0) return n == 1 ? 1.0 : 0.0;
        const double x = p/pd;
        const double z = std::pow(x, n);
        // Avoid cancellation and a removable 0/0 at small pressure.
        const double openingOverPressure = z < 1e-5
            ? std::pow(x, n-1)*(z == 0 ? 1.0 : -std::expm1(-z)/z)
            : -std::expm1(-z)/x;
        return openingOverPressure*std::exp(-p/pstar);
    }

    double recovery(double massG) const
    {
        if (!std::isfinite(massG) || massG < 0)
            throw std::invalid_argument("Form A invalid outlet liquid mass");
        return std::exp(-std::exp(-massG/mc));
    }

    double localRecovery(double fraction) const
    {
        if (!std::isfinite(fraction) || fraction < 0 || fraction > 1
            || !std::isfinite(xc) || xc <= 0 || xc > 1)
            throw std::invalid_argument("Form A invalid extracted fraction or Xc");
        return std::exp(-std::exp(-fraction/xc));
    }

    static double extractedFraction(double remaining, double initial)
    {
        if (!std::isfinite(initial) || initial <= 0
            || !std::isfinite(remaining) || remaining < 0 || remaining > initial)
            throw std::invalid_argument("Form A invalid extractable inventory");
        return 1.0-remaining/initial;
    }

    double multiplier(double inletGaugePa, double massG) const
    {
        return pressureMultiplier(inletGaugePa)*recovery(massG);
    }

    double basePermeability(double mu, double depth, double rho, double area) const
    {
        return a*1e-3*mu*depth/(rho*area*1e5);
    }
};
}
#endif
