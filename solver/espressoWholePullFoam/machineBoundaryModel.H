#ifndef machineBoundaryModel_H
#define machineBoundaryModel_H

#include "scalar.H"
#include "word.H"
#include <cmath>

namespace Foam
{

struct MachineBoundaryParameters
{
    scalar compliance;
    scalar upstreamResistance;
    scalar freeFlowRate;
    scalar shutoffPressure;
    scalar supplyRampTime;
    scalar relativeTolerance;
    scalar absoluteTolerance;
    label maximumIterations;
};

struct MachineBoundaryState
{
    scalar upstreamPressure;
    scalar basketPressure;
    scalar supplyFlow;
    scalar puckFlow;
    scalar residual;
    label iterations;
    bool converged;
};

inline scalar machineRamp(const scalar t, const scalar rampTime)
{
    return rampTime <= SMALL ? 1.0 : Foam::max(0.0, Foam::min(1.0, t/rampTime));
}

inline scalar machineSupply
(
    const scalar time,
    const scalar upstreamPressure,
    const scalar outletPressure,
    const MachineBoundaryParameters& p
)
{
    const scalar span = p.shutoffPressure - outletPressure;
    return p.freeFlowRate*machineRamp(time, p.supplyRampTime)
        *Foam::max(0.0, 1.0 - (upstreamPressure - outletPressure)/span);
}

inline scalar saturatedPuckFlow
(
    const scalar upstreamPressure,
    const scalar outletPressure,
    const scalar conductance,
    const scalar upstreamResistance
)
{
    return conductance*Foam::max(upstreamPressure - outletPressure, 0.0)
        /(1.0 + conductance*upstreamResistance);
}

inline scalar wettingPuckFlow
(
    const scalar upstreamPressure,
    const scalar outletPressure,
    const scalar frontPressure,
    const scalar oldFront,
    const scalar bedDepth,
    const scalar area,
    const scalar porosity,
    const scalar permeability,
    const scalar viscosity,
    const scalar dt,
    const scalar upstreamResistance
)
{
    scalar lo = 0.0;
    scalar hi = area*porosity*Foam::max(bedDepth - oldFront, 0.0)/dt;
    for (label i = 0; i < 80; ++i)
    {
        const scalar q = 0.5*(lo + hi);
        const scalar pb = Foam::max
        (
            outletPressure,
            upstreamPressure - upstreamResistance*q
        );
        const scalar z = Foam::min
        (
            bedDepth,
            Foam::sqrt
            (
                Foam::max
                (
                    sqr(oldFront)
                  + 2.0*permeability*Foam::max(pb - frontPressure, 0.0)*dt
                   /(porosity*viscosity),
                    0.0
                )
            )
        );
        const scalar demand = area*porosity*(z - oldFront)/dt;
        if (q > demand) hi = q; else lo = q;
    }
    return 0.5*(lo + hi);
}

inline MachineBoundaryState solveMachineBoundary
(
    const scalar time,
    const scalar dt,
    const scalar previousUpstreamPressure,
    const scalar outletPressure,
    const MachineBoundaryParameters& p,
    const bool saturated,
    const scalar saturatedConductance,
    const scalar frontPressure,
    const scalar oldFront,
    const scalar bedDepth,
    const scalar area,
    const scalar porosity,
    const scalar wettingPermeability,
    const scalar viscosity
)
{
    scalar lo = outletPressure;
    scalar hi = p.shutoffPressure;
    MachineBoundaryState state;
    state.converged = false;
    state.iterations = 0;

    for (label i = 1; i <= p.maximumIterations; ++i)
    {
        const scalar pu = 0.5*(lo + hi);
        const scalar qp = saturated
          ? saturatedPuckFlow(pu, outletPressure, saturatedConductance, p.upstreamResistance)
          : wettingPuckFlow
            (
                pu, outletPressure, frontPressure, oldFront, bedDepth, area,
                porosity, wettingPermeability, viscosity, dt,
                p.upstreamResistance
            );
        const scalar qs = machineSupply(time, pu, outletPressure, p);
        const scalar residual =
            p.compliance*(pu - previousUpstreamPressure)/dt - (qs - qp);
        state = MachineBoundaryState
        {
            pu,
            Foam::max(outletPressure, pu - p.upstreamResistance*qp),
            qs,
            qp,
            residual,
            i,
            false
        };
        const scalar scale = Foam::max(Foam::max(qs, qp), VSMALL);
        if
        (
            Foam::mag(residual)
         <= p.absoluteTolerance + p.relativeTolerance*scale
        )
        {
            state.converged = true;
            break;
        }
        if (residual > 0.0) hi = pu; else lo = pu;
    }
    return state;
}

}

#endif
