#ifndef prescribedPressureBoundaryModel_H
#define prescribedPressureBoundaryModel_H

#include "dictionary.H"
#include "scalarList.H"
#include "word.H"
#include "DynamicList.H"
#include "token.H"
#include <cmath>

namespace Foam
{

struct PrescribedPressureBoundaryParameters
{
    word scheduleType;
    scalarList times;
    scalarList pressures;

    scalar supportedTime(const scalar time) const
    {
        const scalar tolerance = 1e-12*Foam::max
        (1.0, Foam::max(Foam::mag(times[0]), Foam::mag(times.last())));
        if (!std::isfinite(time) || time < times[0]-tolerance
         || time > times.last()+tolerance)
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_TIME_OUTSIDE_SUPPORT time="
                << time << " support=[" << times[0] << ',' << times.last()
                << ']' << exit(FatalError);
        }
        if (time < times[0]) return times[0];
        if (time > times.last()) return times.last();
        return time;
    }

    scalar target(const scalar time) const
    {
        const scalar t = supportedTime(time);
        if (t == times[0]) return pressures[0];
        for (label i=1; i<times.size(); ++i)
        {
            if (t == times[i]) return pressures[i];
            if (t < times[i])
            {
                const scalar f = (t-times[i-1])/(times[i]-times[i-1]);
                return (1.0-f)*pressures[i-1]+f*pressures[i];
            }
        }
        return pressures.last();
    }

    // Exact positive area of a linear segment, including threshold crossings.
    static scalar area(const scalar a, const scalar b, const scalar duration)
    {
        if (a <= 0 && b <= 0) return 0;
        if (a >= 0 && b >= 0) return (0.5*a+0.5*b)*duration;
        if (a < 0) return 0.5*b*duration*(b/(b-a));
        return 0.5*a*duration*(a/(a-b));
    }

    scalar positiveDrivingIntegral
    (const scalar startTime, const scalar endTime, const scalar frontPressure) const
    {
        const scalar start = supportedTime(startTime);
        const scalar end = supportedTime(endTime);
        if (end < start || !std::isfinite(frontPressure))
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE integral interval/threshold"
                << exit(FatalError);
        }
        scalar total=0;
        for (label i=1; i<times.size(); ++i)
        {
            const scalar a=Foam::max(start,times[i-1]);
            const scalar b=Foam::min(end,times[i]);
            if (b>a) total += area(target(a)-frontPressure,target(b)-frontPressure,b-a);
        }
        if (!std::isfinite(total) || total < 0)
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE nonfinite integral"
                << exit(FatalError);
        }
        return total;
    }

    scalar crossingTime
    (const scalar startTime, const scalar endTime,
     const scalar requiredIntegral, const scalar frontPressure) const
    {
        const scalar start=supportedTime(startTime), end=supportedTime(endTime);
        const scalar available=positiveDrivingIntegral(start,end,frontPressure);
        if (!std::isfinite(requiredIntegral) || requiredIntegral < 0
         || requiredIntegral > available)
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_CROSSING_UNREACHABLE required="
                << requiredIntegral << " available=" << available << exit(FatalError);
        }
        if (requiredIntegral == 0) return start;
        scalar cumulative=0;
        for (label i=1; i<times.size(); ++i)
        {
            const scalar a=Foam::max(start,times[i-1]);
            const scalar b=Foam::min(end,times[i]);
            if (b<=a) continue;
            const scalar segment=area(target(a)-frontPressure,target(b)-frontPressure,b-a);
            if (segment>0 && cumulative+segment>=requiredIntegral)
            {
                const scalar remaining=requiredIntegral-cumulative;
                const scalar excessA=target(a)-frontPressure;
                const scalar excessB=target(b)-frontPressure;
                const scalar positiveEnd = excessB < 0
                    ? a+(b-a)*(excessA/(excessA-excessB)) : b;
                // At the full positive area, return the earliest plateau edge.
                // Bisection of a flat integral can mistake roundoff for equality.
                if (requiredIntegral == cumulative+segment) return positiveEnd;
                scalar lo=a, hi=positiveEnd;
                for (label iteration=0; iteration<96; ++iteration)
                {
                    const scalar mid=lo+0.5*(hi-lo);
                    const scalar partial=area(target(a)-frontPressure,target(mid)-frontPressure,mid-a);
                    if (partial < remaining) lo=mid;
                    else hi=mid;
                }
                return lo+0.5*(hi-lo);
            }
            cumulative += segment;
        }
        FatalErrorInFunction << "XSV_PRESSURE_001_CROSSING_UNREACHABLE segment lookup"
            << exit(FatalError);
        return start;
    }

    scalar maximumPressure() const
    {
        scalar result=pressures[0];
        forAll(pressures,i) result=Foam::max(result,pressures[i]);
        return result;
    }
};

// Read numeric lists explicitly so malformed/nonfinite tokens carry stable diagnostics.
inline scalarList readPressureHistoryList(const dictionary& dict, const word& key)
{
    ITstream& stream=dict.lookup(key);
    token item(stream);
    label declared=-1;
    if (item.isLabel())
    {
        declared=item.labelToken();
        if (declared<0)
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE negative list length"
                << exit(FatalError);
        }
        stream >> item;
    }
    if (!item.isPunctuation() || item.pToken()!=token::BEGIN_LIST)
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE expected list " << key
            << exit(FatalError);
    }
    DynamicList<scalar> values;
    while (stream.good())
    {
        stream >> item;
        if (item.isPunctuation() && item.pToken()==token::END_LIST) break;
        if (!item.isNumber() || !std::isfinite(item.number()))
        {
            FatalErrorInFunction << (key=="pressuresPa"
                ? "XSV_PRESSURE_001_INVALID_TARGET_PRESSURE"
                : "XSV_PRESSURE_001_INVALID_SCHEDULE") << " nonnumeric/nonfinite " << key
                << exit(FatalError);
        }
        values.append(item.number());
    }
    if (!item.isPunctuation() || item.pToken()!=token::END_LIST
     || (declared>=0 && declared!=values.size()) || stream.nRemainingTokens()!=0)
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE malformed list " << key
            << exit(FatalError);
    }
    return scalarList(values);
}

inline PrescribedPressureBoundaryParameters readPrescribedPressureBoundary
(const dictionary& modelProperties, const scalar runStart, const scalar runEnd)
{
    if (modelProperties.found("targetInletPressure") || modelProperties.found("pressureRampTime"))
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_CONTRACT_CONFLICT history prohibits scalar ramp"
            << exit(FatalError);
    }
    if (!modelProperties.isDict("prescribedPressureBoundary"))
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE missing history dictionary"
            << exit(FatalError);
    }
    const dictionary& dict=modelProperties.subDict("prescribedPressureBoundary");
    if (!dict.found("scheduleType") || !dict.found("timesS") || !dict.found("pressuresPa")
     || dict.isDict("scheduleType") || dict.isDict("timesS") || dict.isDict("pressuresPa"))
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE missing schedule field"
            << exit(FatalError);
    }
    PrescribedPressureBoundaryParameters result;
    ITstream& typeStream=dict.lookup("scheduleType");
    token typeToken(typeStream);
    if (!typeToken.isWord() || typeToken.wordToken() != "piecewiseLinear"
     || typeStream.nRemainingTokens()!=0)
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE unsupported scheduleType"
            << exit(FatalError);
    }
    result.scheduleType="piecewiseLinear";
    result.times=readPressureHistoryList(dict,"timesS");
    result.pressures=readPressureHistoryList(dict,"pressuresPa");
    if (result.times.size()<2 || result.times.size()!=result.pressures.size())
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE unequal/short lists"
            << exit(FatalError);
    }
    forAll(result.times,i)
    {
        if (!std::isfinite(result.times[i])
         || (i>0 && (!(result.times[i]>result.times[i-1])
                  || !std::isfinite(result.times[i]-result.times[i-1]))))
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE invalid time at " << i
                << exit(FatalError);
        }
        if (!std::isfinite(result.pressures[i]) || result.pressures[i]<0)
        {
            FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_TARGET_PRESSURE index=" << i
                << exit(FatalError);
        }
    }
    if (!std::isfinite(runStart) || !std::isfinite(runEnd) || runEnd<runStart
     || result.times[0]>runStart || result.times.last()<runEnd)
    {
        FatalErrorInFunction << "XSV_PRESSURE_001_INVALID_SCHEDULE incomplete run coverage"
            << exit(FatalError);
    }
    return result;
}
}
#endif
