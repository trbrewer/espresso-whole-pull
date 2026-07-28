/*---------------------------------------------------------------------------*\
  espressoWholePullFoam

  OpenFOAM Foundation 12 reference solver for the first Puckworks whole-pull
  milestone.  The implementation is intentionally bounded:

    * dry-bed filling by a Darcy sharp-front storage closure;
    * saturated incompressible Darcy pressure solve;
    * one conservative dissolved-solute transport equation;
    * explicit remaining-solid inventory and cup accumulation.

  SPDX-License-Identifier: GPL-3.0-or-later
\*---------------------------------------------------------------------------*/

// OpenFOAM Foundation 12 does not provide the historical fvCFD.H umbrella
// header. Include only the Foundation 12 interfaces used by this solver.
#include "argList.H"
#include "Time.H"
#include "fvMesh.H"
#include "volFields.H"
#include "surfaceFields.H"
#include "IOdictionary.H"
#include "fixedValueFvPatchFields.H"
#include "zeroGradientFvPatchFields.H"
#include "fvMatrices.H"
#include "fvcFlux.H"
#include "fvcGrad.H"
#include "fvmDdt.H"
#include "fvmDiv.H"
#include "fvmLaplacian.H"
#include "PstreamReduceOps.H"
#include "mathematicalConstants.H"
#include "OSspecific.H"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>

using namespace Foam;

namespace
{

scalar globalSumValue(scalar value)
{
    reduce(value, sumOp<scalar>());
    return value;
}

scalar globalMinValue(scalar value)
{
    reduce(value, minOp<scalar>());
    return value;
}

scalar globalMaxValue(scalar value)
{
    reduce(value, maxOp<scalar>());
    return value;
}

scalar clamp01(const scalar value)
{
    return Foam::max(0.0, Foam::min(1.0, value));
}

scalar rampedPressure
(
    const scalar time,
    const scalar targetPressure,
    const scalar rampTime
)
{
    if (rampTime <= SMALL)
    {
        return targetPressure;
    }

    return targetPressure*clamp01(time/rampTime);
}


scalar positiveDrivingPressureIntegral
(
    const scalar startTime,
    const scalar endTime,
    const scalar targetPressure,
    const scalar rampTime,
    const scalar frontPressure
)
{
    if (endTime <= startTime)
    {
        return 0.0;
    }

    const scalar boundedStart = Foam::max(startTime, 0.0);
    const scalar boundedEnd = Foam::max(endTime, boundedStart);

    if (rampTime <= SMALL)
    {
        return Foam::max(targetPressure - frontPressure, 0.0)
              *(boundedEnd - boundedStart);
    }

    if (targetPressure <= SMALL)
    {
        return Foam::max(-frontPressure, 0.0)
              *(boundedEnd - boundedStart);
    }

    const scalar slope = targetPressure/rampTime;
    const scalar thresholdTime = rampTime*frontPressure/targetPressure;
    scalar result = 0.0;

    const scalar rampStart = Foam::max
    (
        boundedStart,
        Foam::max(0.0, thresholdTime)
    );
    const scalar rampEnd = Foam::min(boundedEnd, rampTime);
    if (rampEnd > rampStart)
    {
        result +=
            0.5*slope*(sqr(rampEnd) - sqr(rampStart))
          - frontPressure*(rampEnd - rampStart);
    }

    const scalar plateauStart = Foam::max(boundedStart, rampTime);
    if (boundedEnd > plateauStart)
    {
        result += Foam::max(targetPressure - frontPressure, 0.0)
                 *(boundedEnd - plateauStart);
    }

    return Foam::max(result, 0.0);
}


scalar pressureIntegralCrossingTime
(
    const scalar startTime,
    const scalar endTime,
    const scalar requiredIntegral,
    const scalar targetPressure,
    const scalar rampTime,
    const scalar frontPressure
)
{
    scalar low = startTime;
    scalar high = endTime;

    for (label iteration = 0; iteration < 80; ++iteration)
    {
        const scalar midpoint = 0.5*(low + high);
        const scalar integral = positiveDrivingPressureIntegral
        (
            startTime,
            midpoint,
            targetPressure,
            rampTime,
            frontPressure
        );
        if (integral >= requiredIntegral)
        {
            high = midpoint;
        }
        else
        {
            low = midpoint;
        }
    }

    return 0.5*(low + high);
}

} // End anonymous namespace


int main(int argc, char *argv[])
{
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"

    Info<< "\nStarting espressoWholePullFoam v0.1.3\n" << endl;

    if (runTime.value() > SMALL)
    {
        FatalErrorInFunction
            << "WP-0.1 does not support restart from a non-zero time. "
            << "Run the supplied ./Allrun workflow from a clean case."
            << exit(FatalError);
    }

    IOdictionary modelProperties
    (
        IOobject
        (
            "espressoModelProperties",
            runTime.constant(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        )
    );

    word scenarioId;
    word mode;
    word inletPatchName;
    word outletPatchName;
    word pressureIntegrationMethod;
    word permeabilityProfile;
    modelProperties.lookup("scenarioId") >> scenarioId;
    modelProperties.lookup("mode") >> mode;
    modelProperties.lookup("inletPatch") >> inletPatchName;
    modelProperties.lookup("outletPatch") >> outletPatchName;
    modelProperties.lookup("pressureIntegrationMethod")
        >> pressureIntegrationMethod;
    modelProperties.lookup("permeabilityProfile") >> permeabilityProfile;

    const scalar basketRadius = readScalar(modelProperties.lookup("basketRadius"));
    const scalar bedDepth = readScalar(modelProperties.lookup("bedDepth"));
    const scalar wedgeAngleDegrees =
        readScalar(modelProperties.lookup("wedgeAngleDegrees"));
    const scalar dryDose = readScalar(modelProperties.lookup("dryDose"));
    const scalar extractableFraction =
        readScalar(modelProperties.lookup("extractableFraction"));
    const scalar initialPorosity =
        readScalar(modelProperties.lookup("initialPorosity"));
    const scalar liquidDensity =
        readScalar(modelProperties.lookup("liquidDensity"));
    const scalar dynamicViscosity =
        readScalar(modelProperties.lookup("dynamicViscosity"));
    const scalar saturatedPermeability =
        readScalar(modelProperties.lookup("saturatedPermeability"));
    const scalar wettingPermeability =
        readScalar(modelProperties.lookup("wettingPermeability"));
    const scalar targetInletPressure =
        readScalar(modelProperties.lookup("targetInletPressure"));
    const scalar outletPressure =
        readScalar(modelProperties.lookup("outletPressure"));
    const scalar frontPressure =
        readScalar(modelProperties.lookup("frontPressure"));
    const scalar pressureRampTime =
        readScalar(modelProperties.lookup("pressureRampTime"));
    const scalar frontSmoothingLength =
        readScalar(modelProperties.lookup("frontSmoothingLength"));
    const scalar extractionRateConstant =
        readScalar(modelProperties.lookup("extractionRateConstant"));
    const scalar saturationConcentration =
        readScalar(modelProperties.lookup("saturationConcentration"));
    const scalar effectiveSoluteDiffusivity =
        readScalar(modelProperties.lookup("effectiveSoluteDiffusivity"));
    const scalar targetBeverageMass =
        readScalar(modelProperties.lookup("targetBeverageMass"));
    const scalar initialWetFront =
        readScalar(modelProperties.lookup("initialWetFront"));
    const scalar layerInterfacePosition =
        readScalar(modelProperties.lookup("layerInterfacePosition"));
    const scalar layerPermeabilityUpstream =
        readScalar(modelProperties.lookup("layerPermeabilityUpstream"));
    const scalar layerPermeabilityDownstream =
        readScalar(modelProperties.lookup("layerPermeabilityDownstream"));
    const scalar pressureProbe1Position =
        readScalar(modelProperties.lookup("pressureProbe1Position"));
    const scalar pressureProbe1HalfWidth =
        readScalar(modelProperties.lookup("pressureProbe1HalfWidth"));
    const scalar pressureProbe2Position =
        readScalar(modelProperties.lookup("pressureProbe2Position"));
    const scalar pressureProbe2HalfWidth =
        readScalar(modelProperties.lookup("pressureProbe2HalfWidth"));

    if
    (
        basketRadius <= 0 || bedDepth <= 0 || wedgeAngleDegrees <= 0
     || wedgeAngleDegrees >= 180.0
     || dryDose <= 0 || initialPorosity <= 0 || initialPorosity >= 1
     || liquidDensity <= 0 || dynamicViscosity <= 0
     || saturatedPermeability <= 0 || wettingPermeability <= 0
     || saturationConcentration <= 0 || extractionRateConstant < 0
     || effectiveSoluteDiffusivity < 0
     || initialWetFront < 0 || initialWetFront > bedDepth
     || layerInterfacePosition <= 0 || layerInterfacePosition >= bedDepth
     || layerPermeabilityUpstream <= 0
     || layerPermeabilityDownstream <= 0
     || pressureProbe1HalfWidth <= 0 || pressureProbe2HalfWidth <= 0
    )
    {
        FatalErrorInFunction
            << "Invalid non-positive or out-of-range model input in "
            << modelProperties.objectPath() << exit(FatalError);
    }


    if (pressureIntegrationMethod != "exactPiecewiseLinearIntegral")
    {
        FatalErrorInFunction
            << "Unsupported pressureIntegrationMethod="
            << pressureIntegrationMethod << exit(FatalError);
    }

    if
    (
        permeabilityProfile != "uniform"
     && permeabilityProfile != "axial_two_layer"
    )
    {
        FatalErrorInFunction
            << "Unsupported permeabilityProfile=" << permeabilityProfile
            << exit(FatalError);
    }

    const label inletPatchId = mesh.boundaryMesh().findIndex(inletPatchName);
    const label outletPatchId = mesh.boundaryMesh().findIndex(outletPatchName);

    if (inletPatchId < 0 || outletPatchId < 0)
    {
        FatalErrorInFunction
            << "Required patches not found. inlet=" << inletPatchName
            << ", outlet=" << outletPatchName << nl
            << "Available patches: " << mesh.boundaryMesh().names()
            << exit(FatalError);
    }

    volScalarField p
    (
        IOobject("p", runTime.name(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
        mesh
    );

    volVectorField U
    (
        IOobject("U", runTime.name(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
        mesh
    );

    volScalarField saturation
    (
        IOobject
        (
            "saturation",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField wetMask
    (
        IOobject
        (
            "wetMask",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField porosity
    (
        IOobject
        (
            "porosity",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField permeability
    (
        IOobject
        (
            "permeability",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField dissolvedConcentration
    (
        IOobject
        (
            "dissolvedConcentration",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField remainingExtractable
    (
        IOobject
        (
            "remainingExtractable",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    volScalarField localExtractionRate
    (
        IOobject
        (
            "localExtractionRate",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    );

    surfaceScalarField darcyFlux
    (
        IOobject
        (
            "darcyFlux",
            runTime.name(),
            mesh,
            IOobject::NO_READ,
            IOobject::AUTO_WRITE
        ),
        fvc::flux(U)
    );

    const dimensionedScalar dynamicViscosityCoefficient
    (
        "dynamicViscosity",
        dimensionSet(1, -1, -1, 0, 0, 0, 0),
        dynamicViscosity
    );

    const dimensionedScalar soluteDiffusivity
    (
        "soluteDiffusivity",
        dimensionSet(0, 2, -1, 0, 0, 0, 0),
        effectiveSoluteDiffusivity
    );

    const scalar wedgeAngleRadians =
        wedgeAngleDegrees*constant::mathematical::pi/180.0;
    const scalar sectorScale =
        2.0*constant::mathematical::pi/std::sin(wedgeAngleRadians);

    scalar localMeshVolume = 0.0;
    forAll(mesh.V(), celli)
    {
        localMeshVolume += mesh.V()[celli];
    }
    const scalar rawWedgeMeshVolume = globalSumValue(localMeshVolume);
    const scalar fullMeshVolume = sectorScale*rawWedgeMeshVolume;
    const scalar nominalCylinderVolume =
        constant::mathematical::pi*sqr(basketRadius)*bedDepth;
    const scalar meshVolumeRelativeError =
        Foam::mag(fullMeshVolume - nominalCylinderVolume)
       /Foam::max(nominalCylinderVolume, VSMALL);

    if (meshVolumeRelativeError > 1.0e-8)
    {
        FatalErrorInFunction
            << "Straight-sided wedge volume equivalence failed: scaled="
            << fullMeshVolume << " m3, nominal=" << nominalCylinderVolume
            << " m3, relative error=" << meshVolumeRelativeError
            << exit(FatalError);
    }

    const scalar fullCrossSectionArea =
        constant::mathematical::pi*sqr(basketRadius);
    scalar continuumResistance = bedDepth/saturatedPermeability;
    if (permeabilityProfile == "axial_two_layer")
    {
        continuumResistance =
            layerInterfacePosition/layerPermeabilityUpstream
          + (bedDepth - layerInterfacePosition)
           /layerPermeabilityDownstream;
    }

    const scalar initialExtractableMass = dryDose*extractableFraction;
    const scalar initialExtractableDensity =
        initialExtractableMass/fullMeshVolume;

    p = dimensionedScalar("zero", p.dimensions(), 0.0);
    U = dimensionedVector("zero", U.dimensions(), vector::zero);
    porosity = dimensionedScalar
    (
        "porosity", porosity.dimensions(), initialPorosity
    );
    permeability = dimensionedScalar
    (
        "permeability", permeability.dimensions(), saturatedPermeability
    );
    forAll(permeability, celli)
    {
        if (permeabilityProfile == "axial_two_layer")
        {
            permeability[celli] =
                mesh.C()[celli].x() < layerInterfacePosition
              ? layerPermeabilityUpstream
              : layerPermeabilityDownstream;
        }
        else
        {
            permeability[celli] = saturatedPermeability;
        }
    }

    scalar wetFront = initialWetFront;
    forAll(saturation, celli)
    {
        const scalar axialPosition = mesh.C()[celli].x();
        scalar localSaturation = 0.0;
        if (wetFront >= bedDepth - SMALL)
        {
            localSaturation = 1.0;
        }
        else if (wetFront > SMALL)
        {
            localSaturation = 0.5
              * (1.0 + Foam::tanh
                (
                    (wetFront - axialPosition)
                   /Foam::max(frontSmoothingLength, SMALL)
                ));
        }
        saturation[celli] = clamp01(localSaturation);
        wetMask[celli] = saturation[celli];
    }

    dissolvedConcentration = dimensionedScalar
    (
        "zero", dissolvedConcentration.dimensions(), 0.0
    );
    remainingExtractable = dimensionedScalar
    (
        "initialExtractableDensity",
        remainingExtractable.dimensions(),
        initialExtractableDensity
    );
    localExtractionRate = dimensionedScalar
    (
        "zero", localExtractionRate.dimensions(), 0.0
    );

    p.boundaryFieldRef()[inletPatchId] == 0.0;
    p.boundaryFieldRef()[outletPatchId] == outletPressure;
    saturation.boundaryFieldRef()[inletPatchId] == 1.0;
    wetMask.boundaryFieldRef()[inletPatchId] == 1.0;

    p.correctBoundaryConditions();
    U.correctBoundaryConditions();
    saturation.correctBoundaryConditions();
    wetMask.correctBoundaryConditions();
    porosity.correctBoundaryConditions();
    permeability.correctBoundaryConditions();
    dissolvedConcentration.correctBoundaryConditions();
    remainingExtractable.correctBoundaryConditions();
    localExtractionRate.correctBoundaryConditions();
    darcyFlux = fvc::flux(U);

    // Field-valued mobility keeps the reference case uniform while making the
    // pressure equation ready for later radial/depth-dependent closures.
    volScalarField hydraulicMobility
    (
        IOobject
        (
            "hydraulicMobility",
            runTime.name(),
            mesh,
            IOobject::NO_READ,
            IOobject::AUTO_WRITE
        ),
        permeability/dynamicViscosityCoefficient
    );

    fileName caseRoot(runTime.path());
    const char* caseRootEnv = std::getenv("ESPRESSO_CASE_ROOT");
    if (caseRootEnv && caseRootEnv[0] != '\0')
    {
        caseRoot = fileName(caseRootEnv);
    }

    const fileName traceDirectory
    (
        caseRoot/"postProcessing"/"wholePull"/"0"
    );
    const fileName tracePath(traceDirectory/"traces.csv");

    std::ofstream trace;
    if (Pstream::master())
    {
        // Create each level explicitly.  This avoids relying on whether the
        // host filesystem/API treats mkDir as recursive.
        mkDir(caseRoot/"postProcessing");
        mkDir(caseRoot/"postProcessing"/"wholePull");
        mkDir(traceDirectory);
        trace.open(tracePath.c_str(), std::ios::out | std::ios::trunc);
        if (!trace.good())
        {
            FatalErrorInFunction
                << "Unable to open trace output: " << tracePath
                << exit(FatalError);
        }
        trace << std::setprecision(15)
              << "time_s,inlet_pressure_Pa,wet_front_m,first_drip_s,"
              << "time_to_40g_s,outlet_flow_m3_s,inlet_flow_m3_s,"
              << "cumulative_inlet_water_mass_kg,cup_water_mass_kg,"
              << "cup_solute_mass_kg,cup_beverage_mass_kg,"
              << "instantaneous_tds_mass_fraction,cumulative_tds_mass_fraction,"
              << "extraction_yield_mass_fraction,stored_water_mass_kg,"
              << "remaining_extractable_mass_kg,dissolved_in_puck_mass_kg,"
              << "solute_backdiffusion_mass_kg,liquid_balance_residual_kg,"
              << "solute_balance_residual_kg,min_saturation,max_saturation,"
              << "min_concentration_kg_m3,max_concentration_kg_m3,"
              << "max_velocity_m_s,pressure_initial_residual,"
              << "pressure_final_residual,pressure_iterations,"
              << "concentration_initial_residual,"
              << "concentration_final_residual,concentration_iterations,"
              << "wetting_pressure_integral_Pa_s,"
              << "wetting_step_average_driving_pressure_Pa,"
              << "straight_sided_wedge_scale,raw_wedge_mesh_volume_m3,"
              << "scaled_mesh_volume_m3,nominal_cylinder_volume_m3,"
              << "mesh_volume_relative_error,"
              << "continuum_analytical_outlet_flow_m3_s,"
              << "relative_outlet_flow_error,pressure_probe_1_Pa,"
              << "pressure_probe_2_Pa\n";
    }

    scalar localInitialStoredWaterMass = 0.0;
    forAll(saturation, celli)
    {
        localInitialStoredWaterMass +=
            liquidDensity*porosity[celli]*saturation[celli]*mesh.V()[celli];
    }
    const scalar initialStoredWaterMass =
        sectorScale*globalSumValue(localInitialStoredWaterMass);

    scalar firstDripTime = wetFront >= bedDepth - SMALL ? 0.0 : -1.0;
    scalar timeToTargetMass = -1.0;
    scalar cumulativeInletWaterMass = 0.0;
    scalar cupWaterMass = 0.0;
    scalar cupSoluteMass = 0.0;
    scalar soluteBackDiffusionMass = 0.0;
    scalar previousStoredWaterMass = initialStoredWaterMass;
    scalar previousCupBeverageMass = 0.0;

    Info<< "Scenario: " << scenarioId << nl
        << "Mode: " << mode << nl
        << "Pressure integration: " << pressureIntegrationMethod << nl
        << "Permeability profile: " << permeabilityProfile << nl
        << "Raw wedge mesh volume: " << rawWedgeMeshVolume << " m3" << nl
        << "Full wedge-scaled mesh volume: " << fullMeshVolume << " m3" << nl
        << "Nominal cylindrical volume: " << nominalCylinderVolume << " m3" << nl
        << "Mesh-volume relative error: " << meshVolumeRelativeError << nl
        << "Initial stored water mass: " << initialStoredWaterMass << " kg" << nl
        << "Initial extractable mass: " << initialExtractableMass << " kg" << nl
        << "Straight-sided sector scale: " << sectorScale << nl
        << "Cells per rank (local rank shown): " << mesh.nCells() << nl << endl;

    while (runTime.loop())
    {
        const scalar timeValue = runTime.value();
        const scalar deltaT = runTime.deltaTValue();
        const scalar stepStartTime = timeValue - deltaT;
        const scalar inletPressure = rampedPressure
        (
            timeValue,
            targetInletPressure,
            pressureRampTime
        );
        const scalar wettingPressureIntegral =
            positiveDrivingPressureIntegral
            (
                stepStartTime,
                timeValue,
                targetInletPressure,
                pressureRampTime,
                frontPressure
            );
        const scalar wettingStepAverageDrivingPressure =
            wettingPressureIntegral/Foam::max(deltaT, SMALL);

        scalarField previousSaturation(saturation.size(), 0.0);
        forAll(saturation, celli)
        {
            previousSaturation[celli] = saturation[celli];
        }

        const scalar previousWetFront = wetFront;
        const bool saturatedAtStepStart =
            previousWetFront >= bedDepth - SMALL;

        if (!saturatedAtStepStart)
        {
            const scalar frontSquared =
                sqr(previousWetFront)
              + 2.0*wettingPermeability*wettingPressureIntegral
               /(initialPorosity*dynamicViscosity);
            wetFront = Foam::min
            (
                bedDepth,
                Foam::sqrt(Foam::max(frontSquared, 0.0))
            );

            if (wetFront >= bedDepth - SMALL && firstDripTime < 0.0)
            {
                const scalar requiredIntegral =
                    (sqr(bedDepth) - sqr(previousWetFront))
                   *initialPorosity*dynamicViscosity
                   /(2.0*wettingPermeability);
                firstDripTime = pressureIntegralCrossingTime
                (
                    stepStartTime,
                    timeValue,
                    requiredIntegral,
                    targetInletPressure,
                    pressureRampTime,
                    frontPressure
                );
                wetFront = bedDepth;
            }
        }

        forAll(saturation, celli)
        {
            const scalar axialPosition = mesh.C()[celli].x();
            scalar localSaturation = 0.0;

            if (wetFront >= bedDepth - SMALL)
            {
                localSaturation = 1.0;
            }
            else if (wetFront > SMALL)
            {
                localSaturation = 0.5
                  * (1.0 + Foam::tanh
                    (
                        (wetFront - axialPosition)
                       /Foam::max(frontSmoothingLength, SMALL)
                    ));
            }

            saturation[celli] = clamp01(localSaturation);
            wetMask[celli] = saturation[celli];
        }
        saturation.boundaryFieldRef()[inletPatchId] == 1.0;
        wetMask.boundaryFieldRef()[inletPatchId] == 1.0;
        saturation.correctBoundaryConditions();
        wetMask.correctBoundaryConditions();

        scalar localStoredWaterMass = 0.0;
        forAll(saturation, celli)
        {
            localStoredWaterMass +=
                liquidDensity*porosity[celli]*saturation[celli]*mesh.V()[celli];
        }
        const scalar storedWaterMass =
            sectorScale*globalSumValue(localStoredWaterMass);

        if (!saturatedAtStepStart)
        {
            cumulativeInletWaterMass +=
                Foam::max(storedWaterMass - previousStoredWaterMass, 0.0);
        }
        previousStoredWaterMass = storedWaterMass;

        p.boundaryFieldRef()[inletPatchId] == inletPressure;
        p.boundaryFieldRef()[outletPatchId] == outletPressure;

        scalar outletVolumeFlow = 0.0;
        scalar inletVolumeFlow = 0.0;
        scalar pressureInitialResidual = 0.0;
        scalar pressureFinalResidual = 0.0;
        label pressureIterations = 0;
        scalar concentrationInitialResidual = 0.0;
        scalar concentrationFinalResidual = 0.0;
        label concentrationIterations = 0;

        if (saturatedAtStepStart)
        {
            fvScalarMatrix pressureEquation
            (
                fvm::laplacian(hydraulicMobility, p)
            );
            const SolverPerformance<scalar> pressurePerformance
            (
                pressureEquation.solve()
            );
            pressureInitialResidual = pressurePerformance.initialResidual();
            pressureFinalResidual = pressurePerformance.finalResidual();
            pressureIterations = pressurePerformance.nIterations();

            darcyFlux = -pressureEquation.flux();
            U = -hydraulicMobility*fvc::grad(p);
            U.correctBoundaryConditions();
        }
        else
        {
            const scalar frontVelocity =
                (wetFront - previousWetFront)/Foam::max(deltaT, SMALL);
            const scalar superficialFillingVelocity =
                initialPorosity*Foam::max(frontVelocity, 0.0);

            forAll(p, celli)
            {
                const scalar axialPosition = mesh.C()[celli].x();
                if (wetFront > SMALL && axialPosition < wetFront)
                {
                    p[celli] = outletPressure
                      + (inletPressure - outletPressure)
                       *Foam::max(1.0 - axialPosition/wetFront, 0.0);
                }
                else
                {
                    p[celli] = outletPressure;
                }

                U[celli] = vector
                (
                    superficialFillingVelocity*wetMask[celli],
                    0.0,
                    0.0
                );
            }
            p.correctBoundaryConditions();
            U.correctBoundaryConditions();
            darcyFlux = fvc::flux(U);
        }

        scalar localProbe1WeightedPressure = 0.0;
        scalar localProbe1Volume = 0.0;
        scalar localProbe2WeightedPressure = 0.0;
        scalar localProbe2Volume = 0.0;
        forAll(p, celli)
        {
            const scalar axialPosition = mesh.C()[celli].x();
            if
            (
                Foam::mag(axialPosition - pressureProbe1Position)
             <= pressureProbe1HalfWidth
            )
            {
                localProbe1WeightedPressure += p[celli]*mesh.V()[celli];
                localProbe1Volume += mesh.V()[celli];
            }
            if
            (
                Foam::mag(axialPosition - pressureProbe2Position)
             <= pressureProbe2HalfWidth
            )
            {
                localProbe2WeightedPressure += p[celli]*mesh.V()[celli];
                localProbe2Volume += mesh.V()[celli];
            }
        }
        const scalar probe1WeightedPressure =
            globalSumValue(localProbe1WeightedPressure);
        const scalar probe1Volume = globalSumValue(localProbe1Volume);
        const scalar probe2WeightedPressure =
            globalSumValue(localProbe2WeightedPressure);
        const scalar probe2Volume = globalSumValue(localProbe2Volume);
        const scalar pressureProbe1 =
            probe1Volume > VSMALL ? probe1WeightedPressure/probe1Volume : 0.0;
        const scalar pressureProbe2 =
            probe2Volume > VSMALL ? probe2WeightedPressure/probe2Volume : 0.0;

        const scalar continuumAnalyticalOutletFlow =
            saturatedAtStepStart
          ? fullCrossSectionArea
           *Foam::max(inletPressure - outletPressure, 0.0)
           /(dynamicViscosity*continuumResistance)
          : 0.0;

        // Explicit source evaluated from the beginning-of-step inventories.
        forAll(localExtractionRate, celli)
        {
            const scalar capacityFactor = Foam::max
            (
                1.0 - dissolvedConcentration[celli]/saturationConcentration,
                0.0
            );
            scalar rate =
                extractionRateConstant
               *remainingExtractable[celli]
               *wetMask[celli]
               *capacityFactor;
            rate = Foam::min
            (
                Foam::max(rate, 0.0),
                remainingExtractable[celli]/Foam::max(deltaT, SMALL)
            );
            localExtractionRate[celli] = rate;
        }
        localExtractionRate.correctBoundaryConditions();

        if (saturatedAtStepStart)
        {
            fvScalarMatrix concentrationEquation
            (
                fvm::ddt(porosity, dissolvedConcentration)
              + fvm::div(darcyFlux, dissolvedConcentration)
              - fvm::laplacian
                (
                    porosity*soluteDiffusivity,
                    dissolvedConcentration
                )
             == localExtractionRate
            );
            const SolverPerformance<scalar> concentrationPerformance
            (
                concentrationEquation.solve()
            );
            concentrationInitialResidual =
                concentrationPerformance.initialResidual();
            concentrationFinalResidual =
                concentrationPerformance.finalResidual();
            concentrationIterations = concentrationPerformance.nIterations();

            forAll(remainingExtractable, celli)
            {
                remainingExtractable[celli] = Foam::max
                (
                    remainingExtractable[celli]
                  - deltaT*localExtractionRate[celli],
                    0.0
                );
                dissolvedConcentration[celli] = Foam::max
                (
                    dissolvedConcentration[celli],
                    0.0
                );
            }
        }
        else
        {
            // During filling there is no cup outlet.  Conserve local dissolved
            // bulk mass while the wet storage volume increases.
            forAll(dissolvedConcentration, celli)
            {
                const scalar oldBulkDissolved =
                    porosity[celli]
                   *previousSaturation[celli]
                   *dissolvedConcentration[celli];
                const scalar newBulkDissolved =
                    oldBulkDissolved + deltaT*localExtractionRate[celli];
                const scalar newLiquidFraction =
                    porosity[celli]*saturation[celli];

                if (newLiquidFraction > VSMALL)
                {
                    dissolvedConcentration[celli] = Foam::max
                    (
                        newBulkDissolved/newLiquidFraction,
                        0.0
                    );
                }
                else
                {
                    dissolvedConcentration[celli] = 0.0;
                }

                remainingExtractable[celli] = Foam::max
                (
                    remainingExtractable[celli]
                  - deltaT*localExtractionRate[celli],
                    0.0
                );
            }
        }

        dissolvedConcentration.correctBoundaryConditions();
        remainingExtractable.correctBoundaryConditions();

        scalar outletSoluteRate = 0.0;
        scalar inletBackDiffusionRate = 0.0;

        if (saturatedAtStepStart)
        {
            scalar localOutletVolumeFlow = 0.0;
            scalar localInletVolumeFlow = 0.0;
            scalar localOutletAdvectiveSoluteRate = 0.0;

            const fvsPatchScalarField& outletFlux =
                darcyFlux.boundaryField()[outletPatchId];
            const fvPatchScalarField& outletConcentration =
                dissolvedConcentration.boundaryField()[outletPatchId];

            forAll(outletFlux, facei)
            {
                const scalar positiveFlux = Foam::max(outletFlux[facei], 0.0);
                localOutletVolumeFlow += positiveFlux;
                localOutletAdvectiveSoluteRate +=
                    positiveFlux*outletConcentration[facei];
            }

            const fvsPatchScalarField& inletFlux =
                darcyFlux.boundaryField()[inletPatchId];
            forAll(inletFlux, facei)
            {
                localInletVolumeFlow += Foam::max(-inletFlux[facei], 0.0);
            }

            tmp<scalarField> tInletGradient =
                dissolvedConcentration.boundaryField()[inletPatchId].snGrad();
            const scalarField& inletGradient = tInletGradient();
            const scalarField& inletArea =
                mesh.magSf().boundaryField()[inletPatchId];
            scalar localInletBackDiffusionRate = 0.0;
            forAll(inletGradient, facei)
            {
                const scalar diffusiveOutwardRate =
                    -initialPorosity*effectiveSoluteDiffusivity
                    *inletGradient[facei]*inletArea[facei];
                localInletBackDiffusionRate +=
                    Foam::max(diffusiveOutwardRate, 0.0);
            }

            outletVolumeFlow =
                sectorScale*globalSumValue(localOutletVolumeFlow);
            inletVolumeFlow =
                sectorScale*globalSumValue(localInletVolumeFlow);
            outletSoluteRate =
                sectorScale*globalSumValue(localOutletAdvectiveSoluteRate);
            inletBackDiffusionRate =
                sectorScale*globalSumValue(localInletBackDiffusionRate);

            cumulativeInletWaterMass +=
                liquidDensity*inletVolumeFlow*deltaT;
            cupWaterMass += liquidDensity*outletVolumeFlow*deltaT;
            cupSoluteMass += Foam::max(outletSoluteRate, 0.0)*deltaT;
            soluteBackDiffusionMass +=
                Foam::max(inletBackDiffusionRate, 0.0)*deltaT;
        }

        scalar localRemainingMass = 0.0;
        scalar localDissolvedMass = 0.0;
        scalar localMinSaturation = GREAT;
        scalar localMaxSaturation = -GREAT;
        scalar localMinConcentration = GREAT;
        scalar localMaxConcentration = -GREAT;
        scalar localMaxVelocity = 0.0;

        forAll(mesh.V(), celli)
        {
            localRemainingMass +=
                remainingExtractable[celli]*mesh.V()[celli];
            localDissolvedMass +=
                porosity[celli]*saturation[celli]
               *dissolvedConcentration[celli]*mesh.V()[celli];
            localMinSaturation = Foam::min
            (
                localMinSaturation,
                saturation[celli]
            );
            localMaxSaturation = Foam::max
            (
                localMaxSaturation,
                saturation[celli]
            );
            localMinConcentration = Foam::min
            (
                localMinConcentration,
                dissolvedConcentration[celli]
            );
            localMaxConcentration = Foam::max
            (
                localMaxConcentration,
                dissolvedConcentration[celli]
            );
            localMaxVelocity = Foam::max
            (
                localMaxVelocity,
                mag(U[celli])
            );
        }

        const scalar remainingMass =
            sectorScale*globalSumValue(localRemainingMass);
        const scalar dissolvedMass =
            sectorScale*globalSumValue(localDissolvedMass);
        const scalar minSaturation = globalMinValue(localMinSaturation);
        const scalar maxSaturation = globalMaxValue(localMaxSaturation);
        const scalar minConcentration = globalMinValue(localMinConcentration);
        const scalar maxConcentration = globalMaxValue(localMaxConcentration);
        const scalar maxVelocity = globalMaxValue(localMaxVelocity);

        const scalar cupBeverageMass = cupWaterMass + cupSoluteMass;
        const scalar instantaneousTds =
            outletVolumeFlow > VSMALL
          ? outletSoluteRate
           /(liquidDensity*outletVolumeFlow + outletSoluteRate + VSMALL)
          : 0.0;
        const scalar cumulativeTds =
            cupBeverageMass > VSMALL
          ? cupSoluteMass/cupBeverageMass
          : 0.0;
        const scalar extractionYield = cupSoluteMass/dryDose;
        const scalar liquidBalanceResidual =
            initialStoredWaterMass + cumulativeInletWaterMass
          - storedWaterMass - cupWaterMass;
        const scalar relativeOutletFlowError =
            saturatedAtStepStart && continuumAnalyticalOutletFlow > VSMALL
          ? Foam::mag(outletVolumeFlow - continuumAnalyticalOutletFlow)
           /continuumAnalyticalOutletFlow
          : 0.0;
        const scalar soluteBalanceResidual =
            initialExtractableMass
          - remainingMass
          - dissolvedMass
          - cupSoluteMass
          - soluteBackDiffusionMass;

        if
        (
            timeToTargetMass < 0.0
         && cupBeverageMass >= targetBeverageMass
         && cupBeverageMass > previousCupBeverageMass
        )
        {
            const scalar fraction = clamp01
            (
                (targetBeverageMass - previousCupBeverageMass)
               /(cupBeverageMass - previousCupBeverageMass)
            );
            timeToTargetMass = stepStartTime + fraction*deltaT;
        }
        previousCupBeverageMass = cupBeverageMass;

        const bool finiteState =
            std::isfinite(cupBeverageMass)
         && std::isfinite(liquidBalanceResidual)
         && std::isfinite(soluteBalanceResidual)
         && std::isfinite(maxConcentration)
         && std::isfinite(maxVelocity)
         && std::isfinite(pressureProbe1)
         && std::isfinite(pressureProbe2)
         && std::isfinite(relativeOutletFlowError);
        if (!finiteState)
        {
            FatalErrorInFunction
                << "Non-finite state detected at t=" << timeValue
                << exit(FatalError);
        }

        if (Pstream::master())
        {
            trace << timeValue << ','
                  << inletPressure << ','
                  << wetFront << ','
                  << firstDripTime << ','
                  << timeToTargetMass << ','
                  << outletVolumeFlow << ','
                  << inletVolumeFlow << ','
                  << cumulativeInletWaterMass << ','
                  << cupWaterMass << ','
                  << cupSoluteMass << ','
                  << cupBeverageMass << ','
                  << instantaneousTds << ','
                  << cumulativeTds << ','
                  << extractionYield << ','
                  << storedWaterMass << ','
                  << remainingMass << ','
                  << dissolvedMass << ','
                  << soluteBackDiffusionMass << ','
                  << liquidBalanceResidual << ','
                  << soluteBalanceResidual << ','
                  << minSaturation << ','
                  << maxSaturation << ','
                  << minConcentration << ','
                  << maxConcentration << ','
                  << maxVelocity << ','
                  << pressureInitialResidual << ','
                  << pressureFinalResidual << ','
                  << pressureIterations << ','
                  << concentrationInitialResidual << ','
                  << concentrationFinalResidual << ','
                  << concentrationIterations << ','
                  << wettingPressureIntegral << ','
                  << wettingStepAverageDrivingPressure << ','
                  << sectorScale << ','
                  << rawWedgeMeshVolume << ','
                  << fullMeshVolume << ','
                  << nominalCylinderVolume << ','
                  << meshVolumeRelativeError << ','
                  << continuumAnalyticalOutletFlow << ','
                  << relativeOutletFlowError << ','
                  << pressureProbe1 << ','
                  << pressureProbe2 << '\n';
        }

        if (runTime.writeTime())
        {
            Info<< "t=" << timeValue << " s"
                << ", front=" << wetFront << " m"
                << ", Qout=" << 1e6*outletVolumeFlow << " mL/s"
                << ", cup=" << 1e3*cupBeverageMass << " g"
                << ", TDS=" << 100.0*cumulativeTds << " %"
                << ", EY=" << 100.0*extractionYield << " %"
                << ", liquid residual=" << liquidBalanceResidual << " kg"
                << ", solute residual=" << soluteBalanceResidual << " kg"
                << endl;
        }

        runTime.write();
    }

    if (Pstream::master())
    {
        trace.flush();
        trace.close();
    }

    Info<< "\nEnd\n" << endl;
    return 0;
}

// ************************************************************************* //
