#include "argList.H"
#include "OSspecific.H"
#include "mathematicalConstants.H"
#include "machineBoundaryModel.H"
#include "poroelasticCompaction.H"
#include <fstream>
#include <iomanip>

using namespace Foam;

int main(int argc, char* argv[])
{
    argList args(argc, argv, false, true, false);
    if (argc != 2)
    {
        FatalErrorInFunction << "usage: fixture output.json" << exit(FatalError);
    }
    const scalar area = constant::mathematical::pi*sqr(0.029);
    const scalar depth = 0.009011660896432553;
    const scalar mu = 3.0e-4;
    const scalar phi = 0.4;
    const scalar pc = 1.239155e6;
    const scalar k0 = 3.0e-15;
    const PoroelasticPuckParameters puck
    {
        area, depth, mu, phi, pc, k0
    };
    scalar maxLocalBoundsViolation = 0.0;
    for (const scalar x : {0.0, 0.1, 0.5, 0.8, 0.95})
    {
        const scalar sigma = x*pc;
        const scalar e = poroelasticStrain(sigma, phi, pc);
        const scalar mechanicalPhi =
            poroelasticMechanicalPorosity(sigma, phi, pc);
        const scalar ratio = poroelasticPermeabilityRatio(sigma, phi, pc);
        if
        (
            e < 0.0 || e >= phi || mechanicalPhi <= 0.0
         || mechanicalPhi > phi || ratio <= 0.0 || ratio > 1.0
        )
        {
            maxLocalBoundsViolation = 1.0;
        }
    }
    scalar universalErrors[3];
    label ui = 0;
    for (const scalar smallPhi : {1.0e-2, 1.0e-4, 1.0e-8})
    {
        scalar error = 0.0;
        const scalar denominator = poroelasticIntegral(1.0, smallPhi);
        for (const scalar x : {0.1, 0.5, 0.8, 0.95})
        {
            error = Foam::max
            (
                error,
                Foam::mag
                (
                    poroelasticIntegral(x, smallPhi)/denominator
                  - poroelasticUniversalQhat(x)
                )
            );
        }
        universalErrors[ui++] = error;
    }
    const scalar referencePressure = 9.0e5;
    const scalar effectiveK = 1.77e-15;
    const scalar matchedK = poroelasticMatchedPermeability
    (
        effectiveK, referencePressure, phi, pc
    );
    const PoroelasticPuckParameters matched
    {
        area, depth, mu, phi, pc, matchedK
    };
    const scalar matchedFlow =
        poroelasticPuckFlow(referencePressure, matched);
    const scalar darcyFlow =
        area*effectiveK*referencePressure/(mu*depth);
    const MachineBoundaryParameters machine
    {
        2.0e-11, 2.0e11, 7.0e-6, 1.2e6, 3.0,
        1.0e-14, 1.0e-18, 200
    };
    const MachineBoundaryState state = solveMachineBoundary
    (
        10.0, 0.02, 7.0e5, 0.0, machine, true,
        1.0, 0.0, 0.0, depth, depth, area, 0.4, effectiveK, mu,
        nullptr, &matched
    );
    std::ofstream out(args[1]);
    out << std::setprecision(17)
        << "{\n"
        << "  \"schema_version\": \"espresso.public.wp03_001.production_fixture.v1\",\n"
        << "  \"local_bounds_violation\": " << maxLocalBoundsViolation << ",\n"
        << "  \"local_constitutive_values\": [\n";
    bool firstLocalValue = true;
    for (const scalar testPhi : {0.1, 0.4, 0.8})
    {
        for (const scalar x : {0.0, 0.1, 0.5, 0.8, 0.95})
        {
            const scalar sigma = x*pc;
            const scalar e = poroelasticStrain(sigma, testPhi, pc);
            const scalar mechanicalPhi =
                poroelasticMechanicalPorosity(sigma, testPhi, pc);
            const scalar ratio =
                poroelasticPermeabilityRatio(sigma, testPhi, pc);
            const bool boundsPass =
                e >= 0.0 && e < testPhi
             && mechanicalPhi > 0.0 && mechanicalPhi <= testPhi
             && ratio > 0.0 && ratio <= 1.0;
            if (!firstLocalValue)
            {
                out << ",\n";
            }
            firstLocalValue = false;
            out << "    {\"stressFreePorosity\": " << testPhi
                << ", \"normalizedEffectiveStress\": " << x
                << ", \"productionCompactionStrain\": " << e
                << ", \"productionMechanicalPorosity\": " << mechanicalPhi
                << ", \"productionPermeabilityRatio\": " << ratio
                << ", \"stateBoundsPass\": "
                << (boundsPass ? "true" : "false") << "}";
        }
    }
    out << "\n  ],\n"
        << "  \"scalar_flow_m3_s\": "
        << poroelasticPuckFlow(5.0e5, puck) << ",\n"
        << "  \"scalar_integral\": "
        << poroelasticIntegral(5.0e5/pc, phi) << ",\n"
        << "  \"universal_errors\": [" << universalErrors[0] << ", "
        << universalErrors[1] << ", " << universalErrors[2] << "],\n"
        << "  \"matched_permeability_m2\": " << matchedK << ",\n"
        << "  \"matched_identity_relative_error\": "
        << Foam::mag(matchedFlow-darcyFlow)/darcyFlow << ",\n"
        << "  \"machine_upstream_pressure_pa\": " << state.upstreamPressure << ",\n"
        << "  \"machine_basket_pressure_pa\": " << state.basketPressure << ",\n"
        << "  \"machine_supply_flow_m3_s\": " << state.supplyFlow << ",\n"
        << "  \"machine_puck_flow_m3_s\": " << state.puckFlow << ",\n"
        << "  \"machine_storage_m3\": "
        << machine.compliance*(state.upstreamPressure-7.0e5) << ",\n"
        << "  \"machine_iterations\": " << state.iterations << ",\n"
        << "  \"basket_iterations\": " << state.basketIterations << ",\n"
        << "  \"machine_bracketed\": " << (state.bracketed ? "true" : "false") << ",\n"
        << "  \"basket_bracketed\": " << (state.basketBracketed ? "true" : "false") << ",\n"
        << "  \"machine_converged\": " << (state.converged ? "true" : "false") << ",\n"
        << "  \"basket_converged\": " << (state.basketConverged ? "true" : "false") << ",\n"
        << "  \"fallback_count\": " << (state.fallbackUsed ? 1 : 0) << "\n"
        << "}\n";
    return 0;
}
