#ifndef forchheimerResistance_H
#define forchheimerResistance_H

#include "scalar.H"
#include <cmath>

namespace Foam
{

static constexpr scalar wadsworthGamma2 = -1.71588;
static constexpr scalar wadsworthTau = -0.08093;

inline scalar wadsworth2026CeramicsInertialPermeability(const scalar kSI)
{
    if (!(kSI > 0.0) || !std::isfinite(kSI))
    {
        FatalErrorInFunction << "k [m2] must be positive and finite"
            << exit(FatalError);
    }
    // The source expression has an implicit unit convention: kSI is the
    // numerical value of permeability expressed in m2 and the result is in m.
    const scalar kI = std::exp(wadsworthGamma2*std::pow(kSI, wadsworthTau));
    if (!(kI > 0.0) || !std::isfinite(kI))
    {
        FatalErrorInFunction << "Invalid Wadsworth inertial permeability"
            << exit(FatalError);
    }
    return kI;
}

inline scalar stableForchheimerSpeed
(
    const scalar gradientMagnitude,
    const scalar permeability,
    const scalar inertialPermeability,
    const scalar viscosity,
    const scalar density
)
{
    if (gradientMagnitude <= VSMALL)
    {
        return 0.0;
    }
    const scalar a = viscosity/permeability;
    const scalar b = density/inertialPermeability;
    return 2.0*gradientMagnitude
        /(a + std::sqrt(sqr(a) + 4.0*b*gradientMagnitude));
}

inline scalar stableSeriesFlow
(
    const scalar pressureDrop,
    const scalar darcyResistance,
    const scalar inertialResistance
)
{
    const scalar dp = Foam::max(pressureDrop, 0.0);
    if (inertialResistance <= 0.0)
    {
        return dp/darcyResistance;
    }
    return 2.0*dp
        /(darcyResistance
        + std::sqrt(sqr(darcyResistance) + 4.0*inertialResistance*dp));
}

}

#endif
