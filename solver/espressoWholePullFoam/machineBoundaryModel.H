#ifndef machineBoundaryModel_H
#define machineBoundaryModel_H

#include "scalar.H"
#include "word.H"
#include "forchheimerResistance.H"
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
    bool bracketed;
    bool fallbackUsed;
    scalar innerPuckFlow;
    scalar outerPuckFlow;
    scalar basketResidual;
    label basketIterations;
    bool basketBracketed;
    bool basketConverged;
};

struct RadialPuckParameters
{
    scalar innerDarcyResistance;
    scalar outerDarcyResistance;
    scalar innerInertialResistance;
    scalar outerInertialResistance;
};

struct RadialPuckState
{
    scalar basketPressure;
    scalar innerFlow;
    scalar outerFlow;
    scalar totalFlow;
    scalar residual;
    label iterations;
    bool bracketed;
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

inline scalar saturatedPuckFlow
(
    const scalar upstreamPressure,
    const scalar outletPressure,
    const scalar darcyResistance,
    const scalar inertialResistance,
    const scalar upstreamResistance
)
{
    return stableSeriesFlow
    (
        upstreamPressure - outletPressure,
        upstreamResistance + darcyResistance,
        inertialResistance
    );
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

inline RadialPuckState radialSaturatedPuckState
(
    const scalar upstreamPressure,
    const scalar outletPressure,
    const scalar upstreamResistance,
    const RadialPuckParameters& radial,
    const scalar relativeTolerance,
    const scalar absoluteTolerance,
    const label maximumIterations
)
{
    scalar lo = outletPressure;
    scalar hi = upstreamPressure;
    RadialPuckState state
    {
        outletPressure, 0.0, 0.0, 0.0, GREAT, 0, false, false
    };
    const auto evaluate = [&](const scalar pb, RadialPuckState& target)
    {
        target.basketPressure = pb;
        target.innerFlow = stableSeriesFlow
        (
            pb - outletPressure, radial.innerDarcyResistance,
            radial.innerInertialResistance
        );
        target.outerFlow = stableSeriesFlow
        (
            pb - outletPressure, radial.outerDarcyResistance,
            radial.outerInertialResistance
        );
        target.totalFlow = target.innerFlow + target.outerFlow;
        target.residual =
            pb - (upstreamPressure - upstreamResistance*target.totalFlow);
    };
    RadialPuckState loState(state), hiState(state);
    evaluate(lo, loState);
    evaluate(hi, hiState);
    state.bracketed =
        std::isfinite(loState.residual) && std::isfinite(hiState.residual)
     && loState.residual <= 0.0 && hiState.residual >= 0.0;
    if (!state.bracketed)
    {
        return state;
    }
    for (label i = 1; i <= maximumIterations; ++i)
    {
        evaluate(0.5*(lo + hi), state);
        state.iterations = i;
        state.bracketed = true;
        const scalar pressureScale = Foam::max
        (
            Foam::mag(upstreamPressure - outletPressure), 1.0
        );
        if
        (
            Foam::mag(state.residual)
         <= absoluteTolerance*pressureScale
          + relativeTolerance*pressureScale
        )
        {
            state.converged = true;
            break;
        }
        if (state.residual > 0.0) hi = state.basketPressure;
        else lo = state.basketPressure;
    }
    return state;
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
    const scalar saturatedInertialResistance,
    const scalar frontPressure,
    const scalar oldFront,
    const scalar bedDepth,
    const scalar area,
    const scalar porosity,
    const scalar wettingPermeability,
    const scalar viscosity,
    const RadialPuckParameters* radial = nullptr
)
{
    scalar lo = outletPressure;
    scalar hi = p.shutoffPressure;
    MachineBoundaryState state
    {
        outletPressure, outletPressure, 0.0, 0.0, GREAT, 0,
        false, false, false, 0.0, 0.0, GREAT, 0, false, false
    };
    state.converged = false;
    state.iterations = 0;
    state.bracketed = false;
    state.fallbackUsed = false;

    const auto residualAt = [&](const scalar pu)
    {
        const scalar qp = saturated && radial
          ? radialSaturatedPuckState
            (
                pu, outletPressure, p.upstreamResistance, *radial,
                p.relativeTolerance, p.absoluteTolerance, p.maximumIterations
            ).totalFlow
          : saturated
          ? (
                saturatedInertialResistance > 0.0
              ? saturatedPuckFlow
                (
                    pu, outletPressure, 1.0/saturatedConductance,
                    saturatedInertialResistance, p.upstreamResistance
                )
              : saturatedPuckFlow
                (
                    pu, outletPressure, saturatedConductance,
                    p.upstreamResistance
                )
            )
          : wettingPuckFlow
            (
                pu, outletPressure, frontPressure, oldFront, bedDepth, area,
                porosity, wettingPermeability, viscosity, dt,
                p.upstreamResistance
            );
        return p.compliance*(pu - previousUpstreamPressure)/dt
             - (machineSupply(time, pu, outletPressure, p) - qp);
    };
    const scalar residualLo = residualAt(lo);
    const scalar residualHi = residualAt(hi);
    state.bracketed =
        std::isfinite(residualLo) && std::isfinite(residualHi)
     && residualLo <= 0.0 && residualHi >= 0.0;
    if (!state.bracketed)
    {
        return state;
    }

    for (label i = 1; i <= p.maximumIterations; ++i)
    {
        const scalar pu = 0.5*(lo + hi);
        const RadialPuckState radialState = saturated && radial
          ? radialSaturatedPuckState
            (
                pu, outletPressure, p.upstreamResistance, *radial,
                p.relativeTolerance, p.absoluteTolerance, p.maximumIterations
            )
          : RadialPuckState
            {
                outletPressure, 0.0, 0.0, 0.0, 0.0, 0, true, true
            };
        const scalar qp = saturated && radial
          ? radialState.totalFlow
          : saturated
          ? (
                saturatedInertialResistance > 0.0
              ? saturatedPuckFlow
                (
                    pu, outletPressure, 1.0/saturatedConductance,
                    saturatedInertialResistance, p.upstreamResistance
                )
              : saturatedPuckFlow
                (
                    pu, outletPressure, saturatedConductance,
                    p.upstreamResistance
                )
            )
          : wettingPuckFlow
            (
                pu, outletPressure, frontPressure, oldFront, bedDepth, area,
                porosity, wettingPermeability, viscosity, dt,
                p.upstreamResistance
            );
        const scalar qs = machineSupply(time, pu, outletPressure, p);
        const scalar residual =
            p.compliance*(pu - previousUpstreamPressure)/dt - (qs - qp);
        state.upstreamPressure = pu;
        state.basketPressure = saturated && radial
          ? radialState.basketPressure
          : Foam::max(outletPressure, pu - p.upstreamResistance*qp);
        state.supplyFlow = qs;
        state.puckFlow = qp;
        state.residual = residual;
        state.iterations = i;
        state.converged = false;
        state.bracketed = true;
        state.fallbackUsed = false;
        state.innerPuckFlow = saturated && radial ? radialState.innerFlow : 0.0;
        state.outerPuckFlow = saturated && radial ? radialState.outerFlow : 0.0;
        state.basketResidual = saturated && radial ? radialState.residual : 0.0;
        state.basketIterations = saturated && radial ? radialState.iterations : 0;
        state.basketBracketed = !radial || radialState.bracketed;
        state.basketConverged = !radial || radialState.converged;
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
