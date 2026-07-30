#include "argList.H"
#include "machineBoundaryModel.H"
#include "mathematicalConstants.H"
#include <fstream>
#include <iomanip>

using namespace Foam;

static scalar rel(const scalar a, const scalar b)
{
    return mag(a-b)/max(mag(b), VSMALL);
}

int main(int argc, char *argv[])
{
    argList::noParallel();
    argList args(argc, argv, false, true);
    if (argc != 2) return 2;
    const scalar mu = 0.000315, rho = 965.0;
    const scalar length = 0.009011660896432553;
    const scalar radius = 0.029, ri = 0.0145;
    const scalar ai = constant::mathematical::pi*sqr(ri);
    const scalar ao = constant::mathematical::pi*(sqr(radius)-sqr(ri));
    const scalar dp = 900000.0;
    const scalar ki = 4.045714285714286e-15;
    const scalar ko = 1.0114285714285715e-15;
    const scalar kii = 2.0e-11, kio = 9.0e-11;
    RadialPuckParameters darcy
    {
        mu*length/(ai*ki), mu*length/(ao*ko), 0.0, 0.0
    };
    RadialPuckParameters nonlinear
    {
        darcy.innerDarcyResistance, darcy.outerDarcyResistance,
        rho*length/(sqr(ai)*kii), rho*length/(sqr(ao)*kio)
    };
    const scalar qdi = stableSeriesFlow(dp, darcy.innerDarcyResistance, 0.0);
    const scalar qdo = stableSeriesFlow(dp, darcy.outerDarcyResistance, 0.0);
    const scalar qfi = stableSeriesFlow
        (dp, nonlinear.innerDarcyResistance, nonlinear.innerInertialResistance);
    const scalar qfo = stableSeriesFlow
        (dp, nonlinear.outerDarcyResistance, nonlinear.outerInertialResistance);
    const RadialPuckState basket = radialSaturatedPuckState
    (
        1000000.0, 0.0, 2.0e11, nonlinear, 1e-13, 1e-13, 200
    );
    MachineBoundaryParameters mp
    {
        2e-11, 2e11, 7e-6, 1.2e6, 3.0, 1e-13, 1e-16, 200
    };
    const MachineBoundaryState machine = solveMachineBoundary
    (
        10.0, 0.02, 700000.0, 0.0, mp, true, 1.0, 0.0,
        0.0, length, length, ai+ao, 0.269, 1.77e-15, mu, &nonlinear
    );
    const scalar equalK = 1.77e-15;
    RadialPuckParameters equal
    {
        mu*length/(ai*equalK), mu*length/(ao*equalK), 0.0, 0.0
    };
    const scalar equalFlow = stableSeriesFlow(dp, equal.innerDarcyResistance, 0)
                           + stableSeriesFlow(dp, equal.outerDarcyResistance, 0);
    const scalar uniformFlow = (ai+ao)*equalK*dp/(mu*length);
    const scalar maximumError = max
    (
        rel(equalFlow, uniformFlow),
        max
        (
            rel(qdi, dp/darcy.innerDarcyResistance),
            rel(qdo, dp/darcy.outerDarcyResistance)
        )
    );
    std::ofstream out(argv[1]);
    out << std::setprecision(17)
        << "{\n"
        << "  \"schema_version\": \"espresso.public.wp02_004.production_fixture.v1\",\n"
        << "  \"equal_zone_relative_error\": " << rel(equalFlow, uniformFlow) << ",\n"
        << "  \"darcy_inner_flow_m3_s\": " << qdi << ",\n"
        << "  \"darcy_outer_flow_m3_s\": " << qdo << ",\n"
        << "  \"forchheimer_inner_flow_m3_s\": " << qfi << ",\n"
        << "  \"forchheimer_outer_flow_m3_s\": " << qfo << ",\n"
        << "  \"basket_pressure_pa\": " << basket.basketPressure << ",\n"
        << "  \"basket_inner_flow_m3_s\": " << basket.innerFlow << ",\n"
        << "  \"basket_outer_flow_m3_s\": " << basket.outerFlow << ",\n"
        << "  \"basket_residual_pa\": " << basket.residual << ",\n"
        << "  \"basket_bracketed\": " << (basket.bracketed ? "true" : "false") << ",\n"
        << "  \"basket_converged\": " << (basket.converged ? "true" : "false") << ",\n"
        << "  \"machine_upstream_pressure_pa\": " << machine.upstreamPressure << ",\n"
        << "  \"machine_basket_pressure_pa\": " << machine.basketPressure << ",\n"
        << "  \"machine_inner_flow_m3_s\": " << machine.innerPuckFlow << ",\n"
        << "  \"machine_outer_flow_m3_s\": " << machine.outerPuckFlow << ",\n"
        << "  \"machine_total_flow_m3_s\": " << machine.puckFlow << ",\n"
        << "  \"machine_residual_m3_s\": " << machine.residual << ",\n"
        << "  \"machine_bracketed\": " << (machine.bracketed ? "true" : "false") << ",\n"
        << "  \"machine_converged\": " << (machine.converged ? "true" : "false") << ",\n"
        << "  \"fallback_count\": " << (machine.fallbackUsed ? 1 : 0) << ",\n"
        << "  \"maximum_identity_relative_error\": " << maximumError << "\n"
        << "}\n";
    return out.good() && machine.converged && basket.converged ? 0 : 1;
}
