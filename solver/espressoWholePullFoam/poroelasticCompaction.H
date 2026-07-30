#ifndef poroelasticCompaction_H
#define poroelasticCompaction_H

#include "scalar.H"
#include <cmath>

namespace Foam
{

inline scalar poroelasticIntegral
(
    const scalar X,
    const scalar Phi
)
{
    if
    (
        !std::isfinite(X) || !std::isfinite(Phi)
     || X < 0.0 || X > 1.0 || Phi <= 0.0 || Phi >= 1.0
    )
    {
        return -GREAT;
    }
    if (X == 0.0)
    {
        return 0.0;
    }

    // Positive geometric expansion of 1/(1-Phi*s).  Each coefficient is
    // integrated analytically, so the sum has no cancellation.  This is also
    // the documented small-Phi series and reduces exactly to the universal
    // Phi=0 integral in its first term.
    scalar sum = 0.0;
    scalar phiPower = 1.0;
    scalar xPower = X;
    for (label n = 0; n < 4096; ++n)
    {
        const scalar nn = scalar(n);
        const scalar term = phiPower
        *(
            xPower/(nn + 1.0)
          - 3.0*xPower*X/(nn + 2.0)
          + 3.0*xPower*sqr(X)/(nn + 3.0)
          - xPower*pow3(X)/(nn + 4.0)
        );
        sum += term;
        if (n > 8 && Foam::mag(term) <= 2.0e-16*Foam::max(sum, VSMALL))
        {
            break;
        }
        phiPower *= Phi;
        xPower *= X;
    }
    return sum;
}

inline scalar poroelasticUniversalIntegral(const scalar X)
{
    return X*(1.0 - X*(1.5 - X*(1.0 - 0.25*X)));
}

inline scalar poroelasticUniversalQhat(const scalar X)
{
    return 4.0*poroelasticUniversalIntegral(X);
}

inline scalar poroelasticStrain
(
    const scalar sigma,
    const scalar Phi,
    const scalar criticalPressure
)
{
    return Phi*sigma/criticalPressure;
}

inline scalar poroelasticMechanicalPorosity
(
    const scalar sigma,
    const scalar Phi,
    const scalar criticalPressure
)
{
    const scalar strain = poroelasticStrain(sigma, Phi, criticalPressure);
    return (Phi - strain)/(1.0 - strain);
}

inline scalar poroelasticPermeabilityRatio
(
    const scalar sigma,
    const scalar Phi,
    const scalar criticalPressure
)
{
    const scalar X = sigma/criticalPressure;
    return pow3(1.0 - X)/(1.0 - Phi*X);
}

inline scalar poroelasticSecantMobility
(
    const scalar sigmaA,
    const scalar sigmaB,
    const scalar Phi,
    const scalar criticalPressure,
    const scalar stressFreePermeability,
    const scalar viscosity
)
{
    const scalar difference = sigmaB - sigmaA;
    if
    (
        Foam::mag(difference)
      <= 1.0e-12*Foam::max(criticalPressure, scalar(1))
    )
    {
        return stressFreePermeability
            *poroelasticPermeabilityRatio
            (
                0.5*(sigmaA + sigmaB), Phi, criticalPressure
            )/viscosity;
    }
    return stressFreePermeability*criticalPressure
        *(
            poroelasticIntegral(sigmaB/criticalPressure, Phi)
          - poroelasticIntegral(sigmaA/criticalPressure, Phi)
        )/(viscosity*difference);
}

inline scalar poroelasticPuckFlow
(
    const scalar pressureDrop,
    const scalar area,
    const scalar depth,
    const scalar viscosity,
    const scalar Phi,
    const scalar criticalPressure,
    const scalar stressFreePermeability
)
{
    if (pressureDrop <= 0.0)
    {
        return 0.0;
    }
    const scalar J = poroelasticIntegral
    (
        pressureDrop/criticalPressure,
        Phi
    );
    return area*stressFreePermeability*criticalPressure
        *J/(viscosity*depth);
}

inline scalar poroelasticMatchedPermeability
(
    const scalar effectivePermeability,
    const scalar referencePressure,
    const scalar Phi,
    const scalar criticalPressure
)
{
    return effectivePermeability*referencePressure
        /(criticalPressure*poroelasticIntegral
          (referencePressure/criticalPressure, Phi));
}

struct PoroelasticPuckParameters
{
    scalar area;
    scalar depth;
    scalar viscosity;
    scalar stressFreePorosity;
    scalar criticalPressure;
    scalar stressFreePermeability;
};

inline scalar poroelasticPuckFlow
(
    const scalar pressureDrop,
    const PoroelasticPuckParameters& p
)
{
    return poroelasticPuckFlow
    (
        pressureDrop, p.area, p.depth, p.viscosity,
        p.stressFreePorosity, p.criticalPressure,
        p.stressFreePermeability
    );
}

} // End namespace Foam

#endif
