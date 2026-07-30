#include "argList.H"
#include "forchheimerResistance.H"
#include "machineBoundaryModel.H"

#include <cmath>
#include <fstream>
#include <iomanip>
#include <vector>

using namespace Foam;

namespace
{

scalar relativeError(const scalar value, const scalar reference)
{
    return Foam::mag(value - reference)/Foam::max(Foam::mag(reference), VSMALL);
}

}

int main(int argc, char* argv[])
{
    argList::noParallel();
    argList args(argc, argv, false, true);
    if (argc != 2)
    {
        FatalErrorInFunction << "usage: wp02003ZeroInertiaFixture OUTPUT.json"
            << exit(FatalError);
    }

    struct Case
    {
        scalar pressureDrop;
        scalar darcyResistance;
        scalar upstreamResistance;
    };
    const std::vector<Case> cases
    {
        {1.0, 2.0, 0.0},
        {1.0e5, 8.0e10, 2.0e10},
        {9.0e5, 6.0690821502994e11, 2.0e11},
        {1.2e6, 3.0e12, 7.0e11}
    };

    scalar maximumSeriesError = 0.0;
    scalar maximumPuckError = 0.0;
    bool finite = true;
    bool nonnegative = true;
    for (const Case& item : cases)
    {
        const scalar series = stableSeriesFlow
        (
            item.pressureDrop, item.darcyResistance, 0.0
        );
        const scalar seriesReference =
            item.pressureDrop/item.darcyResistance;
        maximumSeriesError = Foam::max
        (
            maximumSeriesError, relativeError(series, seriesReference)
        );

        const scalar productionPuck = saturatedPuckFlow
        (
            item.pressureDrop, 0.0, item.darcyResistance, 0.0,
            item.upstreamResistance
        );
        const scalar conductance = 1.0/item.darcyResistance;
        const scalar acceptedLinear =
            conductance*item.pressureDrop
           /(1.0 + conductance*item.upstreamResistance);
        maximumPuckError = Foam::max
        (
            maximumPuckError, relativeError(productionPuck, acceptedLinear)
        );
        finite = finite && std::isfinite(series)
            && std::isfinite(productionPuck);
        nonnegative = nonnegative && series >= 0.0 && productionPuck >= 0.0;
    }

    const MachineBoundaryParameters parameters
    {
        2.0e-11, 2.0e11, 6.0e-6, 1.2e6, 1.0,
        1.0e-12, 1.0e-18, 80
    };
    const scalar representativeRD = cases[2].darcyResistance;
    const MachineBoundaryState state = solveMachineBoundary
    (
        0.02, 0.02, 0.0, 0.0, parameters, true,
        1.0/representativeRD, 0.0, 0.0, 0.009, 0.009,
        0.0026, 0.4, 1.77e-15, 3.15e-4
    );
    const scalar acceptedMachineFlow = saturatedPuckFlow
    (
        state.upstreamPressure, 0.0, 1.0/representativeRD,
        parameters.upstreamResistance
    );
    const scalar machineFlowError =
        relativeError(state.puckFlow, acceptedMachineFlow);
    finite = finite
        && std::isfinite(state.upstreamPressure)
        && std::isfinite(state.basketPressure)
        && std::isfinite(state.puckFlow)
        && std::isfinite(state.residual);
    nonnegative = nonnegative && state.puckFlow >= 0.0;

    const scalar maximumRelativeError = Foam::max
    (
        Foam::max(maximumSeriesError, maximumPuckError), machineFlowError
    );
    const bool pass =
        maximumRelativeError <= 1.0e-12
     && finite && nonnegative && state.bracketed && state.converged
     && !state.fallbackUsed;

    std::ofstream output(argv[1], std::ios::out | std::ios::trunc);
    output << std::setprecision(17)
        << "{\n"
        << "  \"schema_version\": \"espresso.public.wp02_003.zero_inertia_fixture.v1\",\n"
        << "  \"production_headers\": [\"forchheimerResistance.H\", \"machineBoundaryModel.H\"],\n"
        << "  \"case_count\": " << cases.size() << ",\n"
        << "  \"maximum_series_relative_error\": " << maximumSeriesError << ",\n"
        << "  \"maximum_saturated_puck_relative_error\": " << maximumPuckError << ",\n"
        << "  \"machine_flow_relative_error\": " << machineFlowError << ",\n"
        << "  \"maximum_relative_error\": " << maximumRelativeError << ",\n"
        << "  \"all_values_finite\": " << (finite ? "true" : "false") << ",\n"
        << "  \"all_flows_nonnegative\": " << (nonnegative ? "true" : "false") << ",\n"
        << "  \"machine_bracketed\": " << (state.bracketed ? "true" : "false") << ",\n"
        << "  \"machine_converged\": " << (state.converged ? "true" : "false") << ",\n"
        << "  \"machine_fallback_used\": " << (state.fallbackUsed ? "true" : "false") << ",\n"
        << "  \"status\": \"" << (pass ? "PASS" : "FAIL") << "\"\n"
        << "}\n";
    output.close();
    return pass ? 0 : 1;
}
