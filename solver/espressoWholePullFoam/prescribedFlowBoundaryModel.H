#ifndef prescribedFlowBoundaryModel_H
#define prescribedFlowBoundaryModel_H

#include "dictionary.H"
#include "scalarList.H"
#include "word.H"
#include <cmath>

namespace Foam
{

struct PrescribedFlowBoundaryParameters
{
    word scheduleType;
    scalarList times;
    scalarList flows;
    scalar absoluteTolerance;
    scalar relativeTolerance;

    scalar target(const scalar time) const
    {
        if (scheduleType == "constant")
        {
            return flows[0];
        }
        const scalar endpointTolerance = 1.0e-12*Foam::max
        (
            1.0, Foam::max(Foam::mag(times[0]), Foam::mag(times[times.size()-1]))
        );
        if (time < times[0] - endpointTolerance
         || time > times[times.size() - 1] + endpointTolerance)
        {
            FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE time="
                << time << " outside [" << times[0] << ','
                << times[times.size() - 1] << ']' << exit(FatalError);
        }
        if (Foam::mag(time-times[0]) <= endpointTolerance) return flows[0];
        if (Foam::mag(time-times[times.size()-1]) <= endpointTolerance)
            return flows[flows.size()-1];
        for (label i = 0; i < times.size(); ++i)
        {
            if (time == times[i]) return flows[i];
            if (time < times[i])
            {
                const scalar fraction =
                    (time - times[i - 1])/(times[i] - times[i - 1]);
                return flows[i - 1] + fraction*(flows[i] - flows[i - 1]);
            }
        }
        return flows[flows.size() - 1];
    }
};

inline PrescribedFlowBoundaryParameters readPrescribedFlowBoundary
(
    const dictionary& modelProperties,
    const scalar runStart,
    const scalar runEnd
)
{
    if (!modelProperties.found("prescribedFlowBoundary"))
    {
        FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE missing dictionary"
            << exit(FatalError);
    }
    const dictionary& dict = modelProperties.subDict("prescribedFlowBoundary");
    PrescribedFlowBoundaryParameters result;
    dict.lookup("scheduleType") >> result.scheduleType;
    result.absoluteTolerance =
        readScalar(dict.lookup("absoluteFlowToleranceM3PerS"));
    result.relativeTolerance =
        readScalar(dict.lookup("relativeFlowTolerance"));
    if (!std::isfinite(result.absoluteTolerance)
     || !std::isfinite(result.relativeTolerance)
     || result.absoluteTolerance <= 0.0 || result.relativeTolerance <= 0.0)
    {
        FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE invalid tolerances"
            << exit(FatalError);
    }
    if (result.scheduleType == "constant")
    {
        if (!dict.found("volumetricFlowRateM3PerS")
         || dict.found("timesS") || dict.found("volumetricFlowRatesM3PerS"))
        {
            FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE constant contract"
                << exit(FatalError);
        }
        result.flows.setSize(1);
        result.flows[0] = readScalar(dict.lookup("volumetricFlowRateM3PerS"));
    }
    else if (result.scheduleType == "piecewiseLinear")
    {
        if (!dict.found("timesS") || !dict.found("volumetricFlowRatesM3PerS")
         || dict.found("volumetricFlowRateM3PerS"))
        {
            FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE piecewise contract"
                << exit(FatalError);
        }
        result.times = scalarList(dict.lookup("timesS"));
        result.flows = scalarList(dict.lookup("volumetricFlowRatesM3PerS"));
        if (result.times.size() < 2 || result.times.size() != result.flows.size()
         || result.times[0] > runStart
         || result.times[result.times.size() - 1] < runEnd)
        {
            FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE size or coverage"
                << exit(FatalError);
        }
        forAll(result.times, i)
        {
            if (!std::isfinite(result.times[i])
             || (i && result.times[i] <= result.times[i - 1]))
            {
                FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE times"
                    << exit(FatalError);
            }
        }
    }
    else
    {
        FatalErrorInFunction << "XSV_FLOW_001_INVALID_SCHEDULE scheduleType="
            << result.scheduleType << exit(FatalError);
    }
    forAll(result.flows, i)
    {
        if (!std::isfinite(result.flows[i]) || result.flows[i] < 0.0)
        {
            FatalErrorInFunction << "XSV_FLOW_001_INVALID_TARGET_FLOW index=" << i
                << exit(FatalError);
        }
    }
    return result;
}

}
#endif
