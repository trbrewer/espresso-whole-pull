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
#include "machineBoundaryModel.H"
#include "forchheimerResistance.H"
#include "poroelasticCompaction.H"

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

scalar wp02Qhat(const scalar x)
{
    return x*(4.0 - 6.0*x + 4.0*sqr(x) - x*sqr(x));
}

scalar wp02PhiFactor(const scalar phi)
{
    if (phi == 0.0)
    {
        return 0.0;
    }
    if (phi < 0.0 || phi >= 1.0 || !std::isfinite(phi))
    {
        FatalErrorInFunction << "WP02 phi outside (0,1): " << phi
            << exit(FatalError);
    }
    scalar result = 0.0;
    if (phi <= 0.125)
    {
        scalar accumulator = 0.0;
        for (label n = 24; n >= 4; --n)
        {
            const scalar coefficient =
                scalar((n - 3)*(n - 2)*(2*n + 1))
               /(6.0*scalar(n)*scalar(n - 1));
            accumulator = coefficient + phi*accumulator;
        }
        result = sqr(phi)*sqr(phi)*accumulator;
    }
    else
    {
        const scalar oneMinusPhi = 1.0 - phi;
        result =
        (
            phi*(phi*(11.0*phi - 15.0) + 6.0)
          + 6.0*pow3(oneMinusPhi)*std::log1p(-phi)
        )/(6.0*sqr(oneMinusPhi));
    }
    if (!std::isfinite(result) || result < 0.0)
    {
        FatalErrorInFunction << "Invalid WP02 phi factor " << result
            << exit(FatalError);
    }
    return result;
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

    Info<< "\nStarting espressoWholePullFoam v0.2.0\n" << endl;

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
    const word pressureBoundaryModel =
        modelProperties.lookupOrDefault<word>
        (
            "pressureBoundaryModel",
            "prescribedPressure"
        );
    const word flowResistanceModel =
        modelProperties.lookupOrDefault<word>("flowResistanceModel", "darcy");
    const bool darcyForchheimer =
        flowResistanceModel == "darcyForchheimer";
    if (!darcyForchheimer && flowResistanceModel != "darcy")
    {
        FatalErrorInFunction << "Unsupported flowResistanceModel="
            << flowResistanceModel << exit(FatalError);
    }
    const word bedMechanicsModel =
        modelProperties.lookupOrDefault<word>("bedMechanicsModel", "none");
    const bool poroelasticCompaction =
        bedMechanicsModel == "waszkiewiczQuasiStaticCompaction";
    word poroelasticCompactionModel("none");
    scalar stressFreePorosity = initialPorosity;
    scalar criticalCompactionPressure = GREAT;
    scalar stressFreePermeability = saturatedPermeability;
    scalar poroelasticRelativeTolerance = 1.0e-10;
    scalar poroelasticAbsoluteTolerance = 1.0e-10;
    label poroelasticMaximumIterations = 1;
    scalar poroelasticUnderRelaxation = 1.0;
    scalar poroelasticMachineFluxTolerance = 1.0e-6;
    if (poroelasticCompaction)
    {
        if (!modelProperties.found("poroelasticCompaction"))
        {
            FatalErrorInFunction << "Missing poroelasticCompaction dictionary"
                << exit(FatalError);
        }
        const dictionary& compaction =
            modelProperties.subDict("poroelasticCompaction");
        compaction.lookup("model") >> poroelasticCompactionModel;
        stressFreePorosity =
            readScalar(compaction.lookup("stressFreePorosity"));
        criticalCompactionPressure =
            readScalar(compaction.lookup("criticalCompactionPressurePa"));
        stressFreePermeability =
            readScalar(compaction.lookup("stressFreePermeabilityM2"));
        poroelasticRelativeTolerance =
            readScalar(compaction.lookup("nonlinearRelativeTolerance"));
        poroelasticAbsoluteTolerance =
            readScalar(compaction.lookup("nonlinearAbsoluteTolerance"));
        poroelasticMaximumIterations =
            readLabel(compaction.lookup("nonlinearMaximumIterations"));
        poroelasticUnderRelaxation =
            readScalar(compaction.lookup("nonlinearUnderRelaxation"));
        poroelasticMachineFluxTolerance =
            readScalar(compaction.lookup("machineFluxRelativeTolerance"));
        if
        (
            poroelasticCompactionModel != "waszkiewicz2025FinitePhi"
         || stressFreePorosity <= 0.0 || stressFreePorosity >= 1.0
         || criticalCompactionPressure <= 0.0
         || stressFreePermeability <= 0.0
         || poroelasticRelativeTolerance <= 0.0
         || poroelasticAbsoluteTolerance <= 0.0
         || poroelasticMaximumIterations < 1
         || poroelasticUnderRelaxation <= 0.0
         || poroelasticUnderRelaxation > 1.0
         || poroelasticMachineFluxTolerance <= 0.0
         || !std::isfinite(stressFreePorosity)
         || !std::isfinite(criticalCompactionPressure)
         || !std::isfinite(stressFreePermeability)
        )
        {
            FatalErrorInFunction << "Invalid poroelastic compaction input"
                << exit(FatalError);
        }
    }
    else if (bedMechanicsModel != "none")
    {
        FatalErrorInFunction << "Unsupported bedMechanicsModel="
            << bedMechanicsModel << exit(FatalError);
    }
    word inertialPermeabilityModel("none");
    scalar constantInertialPermeability = GREAT;
    scalar layerInertialPermeabilityUpstream = GREAT;
    scalar layerInertialPermeabilityDownstream = GREAT;
    scalar innerInertialPermeability = GREAT;
    scalar outerInertialPermeability = GREAT;
    scalar nonlinearRelativeTolerance = 1.0e-10;
    scalar nonlinearAbsoluteTolerance = 1.0e-12;
    label nonlinearMaximumIterations = 1;
    scalar nonlinearUnderRelaxation = 1.0;
    scalar machineFluxRelativeTolerance = 1.0e-6;
    if (darcyForchheimer)
    {
        modelProperties.lookup("inertialPermeabilityModel")
            >> inertialPermeabilityModel;
        constantInertialPermeability = readScalar
        (
            modelProperties.lookup("constantInertialPermeabilityM")
        );
        layerInertialPermeabilityUpstream = readScalar
        (
            modelProperties.lookup("layerInertialPermeabilityUpstream")
        );
        layerInertialPermeabilityDownstream = readScalar
        (
            modelProperties.lookup("layerInertialPermeabilityDownstream")
        );
        innerInertialPermeability = readScalar
        (
            modelProperties.lookup("innerInertialPermeabilityM")
        );
        outerInertialPermeability = readScalar
        (
            modelProperties.lookup("outerInertialPermeabilityM")
        );
        nonlinearRelativeTolerance = readScalar
        (
            modelProperties.lookup("nonlinearRelativeTolerance")
        );
        nonlinearAbsoluteTolerance = readScalar
        (
            modelProperties.lookup("nonlinearAbsoluteTolerance")
        );
        nonlinearMaximumIterations = readLabel
        (
            modelProperties.lookup("nonlinearMaximumIterations")
        );
        nonlinearUnderRelaxation = readScalar
        (
            modelProperties.lookup("nonlinearUnderRelaxation")
        );
        machineFluxRelativeTolerance = readScalar
        (
            modelProperties.lookup("machineFluxRelativeTolerance")
        );
        if
        (
            (
                inertialPermeabilityModel != "constant"
             && inertialPermeabilityModel != "wadsworth2026CeramicsFit"
            )
         || constantInertialPermeability <= 0.0
         || layerInertialPermeabilityUpstream <= 0.0
         || layerInertialPermeabilityDownstream <= 0.0
         || innerInertialPermeability <= 0.0
         || outerInertialPermeability <= 0.0
         || nonlinearRelativeTolerance <= 0.0
         || nonlinearAbsoluteTolerance <= 0.0
         || nonlinearMaximumIterations < 1
         || nonlinearUnderRelaxation <= 0.0
         || nonlinearUnderRelaxation > 1.0
         || machineFluxRelativeTolerance <= 0.0
         || !std::isfinite(constantInertialPermeability)
        )
        {
            FatalErrorInFunction << "Invalid Darcy-Forchheimer input"
                << exit(FatalError);
        }
    }
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
    const scalar interfaceRadius =
        readScalar(modelProperties.lookup("interfaceRadiusM"));
    const scalar innerPermeability =
        readScalar(modelProperties.lookup("innerPermeabilityM2"));
    const scalar outerPermeability =
        readScalar(modelProperties.lookup("outerPermeabilityM2"));
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
     || interfaceRadius <= 0 || interfaceRadius >= basketRadius
     || innerPermeability <= 0 || outerPermeability <= 0
     || !std::isfinite(interfaceRadius)
     || !std::isfinite(innerPermeability)
     || !std::isfinite(outerPermeability)
     || pressureProbe1HalfWidth <= 0 || pressureProbe2HalfWidth <= 0
    )
    {
        FatalErrorInFunction
            << "Invalid non-positive or out-of-range model input in "
            << modelProperties.objectPath() << exit(FatalError);
    }

    const bool lumpedMachine =
        pressureBoundaryModel == "lumpedMachineCompliance";
    if (!lumpedMachine && pressureBoundaryModel != "prescribedPressure")
    {
        FatalErrorInFunction << "Unsupported pressureBoundaryModel="
            << pressureBoundaryModel << exit(FatalError);
    }
    MachineBoundaryParameters machineParameters =
    {
        1.0, 0.0, 1.0, outletPressure + 1.0, 0.0, 1.0, 1.0, 1
    };
    scalar initialUpstreamPressure = outletPressure;
    if (lumpedMachine)
    {
        if (!modelProperties.found("machineBoundary"))
        {
            FatalErrorInFunction << "Missing machineBoundary dictionary"
                << exit(FatalError);
        }
        const dictionary& machine = modelProperties.subDict("machineBoundary");
        initialUpstreamPressure =
            readScalar(machine.lookup("initialUpstreamPressure"));
        machineParameters.compliance =
            readScalar(machine.lookup("upstreamCompliance"));
        machineParameters.upstreamResistance =
            readScalar(machine.lookup("upstreamResistance"));
        machineParameters.freeFlowRate =
            readScalar(machine.lookup("freeFlowRate"));
        machineParameters.shutoffPressure =
            readScalar(machine.lookup("shutoffPressure"));
        machineParameters.supplyRampTime =
            readScalar(machine.lookup("supplyRampTime"));
        machineParameters.relativeTolerance =
            readScalar(machine.lookup("couplingRelativeTolerance"));
        machineParameters.absoluteTolerance =
            readScalar(machine.lookup("couplingAbsoluteTolerance"));
        machineParameters.maximumIterations =
            readLabel(machine.lookup("couplingMaximumIterations"));
        if
        (
            initialUpstreamPressure < outletPressure
         || initialUpstreamPressure > machineParameters.shutoffPressure
         || machineParameters.compliance <= 0.0
         || machineParameters.upstreamResistance < 0.0
         || machineParameters.freeFlowRate <= 0.0
         || machineParameters.shutoffPressure <= outletPressure
         || machineParameters.supplyRampTime < 0.0
         || machineParameters.relativeTolerance <= 0.0
         || machineParameters.absoluteTolerance <= 0.0
         || machineParameters.maximumIterations < 1
        )
        {
            FatalErrorInFunction << "Invalid machineBoundary input"
                << exit(FatalError);
        }
    }

    const bool effectivePermeabilityEnabled =
        modelProperties.found("effectivePermeabilityEvolution");
    scalar sourceReferencePressureBar = 0.0;
    scalar sourcePcBar = 0.0;
    scalar sourceQcGPerS = 0.0;
    scalar sourceKSolidsG = 0.0;
    scalar sourceLSolidsS = 0.0;
    scalar sourceMSolidsS = 0.0;
    scalar sourceDoseG = 0.0;
    scalar sourceToSolverOffsetS = 0.0;
    scalar sourceValidityStartS = 0.0;
    scalar minimumMultiplier = 1.0;
    scalar maximumMultiplier = 1.0;
    if (effectivePermeabilityEnabled)
    {
        const dictionary& closure =
            modelProperties.subDict("effectivePermeabilityEvolution");
        const Switch enabled(closure.lookup("enabled"));
        word closureModel;
        closure.lookup("model") >> closureModel;
        if (!enabled || closureModel != "waszkiewiczSaturatedDissolutionIndexed")
        {
            FatalErrorInFunction << "Invalid enabled WP02 closure"
                << exit(FatalError);
        }
        if (permeabilityProfile != "uniform")
        {
            FatalErrorInFunction << "WP02 closure requires uniform permeability"
                << exit(FatalError);
        }
        sourceReferencePressureBar = readScalar(closure.lookup("sourceReferencePressureBar"));
        sourcePcBar = readScalar(closure.lookup("sourcePcBar"));
        sourceQcGPerS = readScalar(closure.lookup("sourceQcGPerS"));
        sourceKSolidsG = readScalar(closure.lookup("sourceKSolidsG"));
        sourceLSolidsS = readScalar(closure.lookup("sourceLSolidsS"));
        sourceMSolidsS = readScalar(closure.lookup("sourceMSolidsS"));
        sourceDoseG = readScalar(closure.lookup("sourceDoseG"));
        sourceToSolverOffsetS = readScalar(closure.lookup("sourceToSolverOffsetS"));
        sourceValidityStartS = readScalar(closure.lookup("sourceValidityStartS"));
        minimumMultiplier = readScalar(closure.lookup("minimumMultiplier"));
        maximumMultiplier = readScalar(closure.lookup("maximumMultiplier"));
        const scalar phiM = sourceKSolidsG/sourceDoseG;
        if
        (
            sourceReferencePressureBar <= 0.0 || sourcePcBar <= 0.0
         || sourceQcGPerS <= 0.0 || sourceKSolidsG <= 0.0
         || sourceMSolidsS <= 0.0 || sourceDoseG <= 0.0
         || sourceValidityStartS < 0.0 || sourceValidityStartS > runTime.endTime().value()
         || minimumMultiplier <= 0.0 || maximumMultiplier != 1.0
         || phiM <= 0.0 || phiM >= 1.0 || saturatedPermeability <= 0.0
        )
        {
            FatalErrorInFunction << "Invalid WP02 closure input"
                << exit(FatalError);
        }
    }

    if
    (
        poroelasticCompaction
     && (
            permeabilityProfile != "uniform"
         || flowResistanceModel != "darcy"
         || effectivePermeabilityEnabled
        )
    )
    {
        FatalErrorInFunction
            << "Compaction requires uniform Darcy flow with WP02 evolution disabled"
            << exit(FatalError);
    }
    const scalar maximumCompactionPressureDrop =
        (lumpedMachine ? machineParameters.shutoffPressure : targetInletPressure)
      - outletPressure;
    if
    (
        poroelasticCompaction
     && (
            maximumCompactionPressureDrop < 0.0
         || maximumCompactionPressureDrop >= criticalCompactionPressure
        )
    )
    {
        FatalErrorInFunction
            << "Maximum pressure drop must remain below critical compaction pressure"
            << exit(FatalError);
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
     && permeabilityProfile != "radial_two_zone"
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

    volScalarField permeabilityZoneId
    (
        IOobject
        (
            "permeabilityZoneId", runTime.name(), mesh,
            IOobject::NO_READ,
            IOobject::AUTO_WRITE
        ),
        mesh,
        dimensionedScalar("inner", dimless, 0.0)
    );

    volScalarField effectiveMatrixStress
    (
        IOobject
        (
            "effectiveMatrixStress", runTime.name(), mesh,
            IOobject::NO_READ,
            poroelasticCompaction ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", p.dimensions(), 0.0)
    );

    volScalarField normalizedEffectiveStress
    (
        IOobject
        (
            "normalizedEffectiveStress", runTime.name(), mesh,
            IOobject::NO_READ,
            poroelasticCompaction ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", dimless, 0.0)
    );

    volScalarField compactionStrain
    (
        IOobject
        (
            "compactionStrain", runTime.name(), mesh,
            IOobject::NO_READ,
            poroelasticCompaction ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", dimless, 0.0)
    );

    volScalarField mechanicalPorosity
    (
        IOobject
        (
            "mechanicalPorosity", runTime.name(), mesh,
            IOobject::NO_READ,
            poroelasticCompaction ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("stressFree", dimless, stressFreePorosity)
    );

    volScalarField compactionPermeabilityRatio
    (
        IOobject
        (
            "compactionPermeabilityRatio", runTime.name(), mesh,
            IOobject::NO_READ,
            poroelasticCompaction ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("one", dimless, 1.0)
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
    const PoroelasticPuckParameters poroelasticPuckParameters
    {
        fullCrossSectionArea, bedDepth, dynamicViscosity,
        stressFreePorosity, criticalCompactionPressure,
        stressFreePermeability
    };
    const bool radialTwoZone = permeabilityProfile == "radial_two_zone";
    const scalar exactInnerArea =
        constant::mathematical::pi*sqr(interfaceRadius);
    const scalar exactOuterArea = fullCrossSectionArea - exactInnerArea;
    const scalar innerAreaFraction = exactInnerArea/fullCrossSectionArea;
    const scalar outerAreaFraction = exactOuterArea/fullCrossSectionArea;
    scalar localInnerOutletArea = 0.0;
    scalar localOuterOutletArea = 0.0;
    const vectorField& outletCentres =
        mesh.Cf().boundaryField()[outletPatchId];
    const scalarField& outletAreas =
        mesh.magSf().boundaryField()[outletPatchId];
    forAll(outletCentres, facei)
    {
        const scalar radius = Foam::sqrt
        (
            sqr(outletCentres[facei].y()) + sqr(outletCentres[facei].z())
        );
        if (radius < interfaceRadius)
        {
            localInnerOutletArea += outletAreas[facei];
        }
        else
        {
            localOuterOutletArea += outletAreas[facei];
        }
    }
    const scalar meshInnerArea =
        sectorScale*globalSumValue(localInnerOutletArea);
    const scalar meshOuterArea =
        sectorScale*globalSumValue(localOuterOutletArea);
    const scalar meshZoneAreaRelativeError = Foam::max
    (
        Foam::mag(meshInnerArea - exactInnerArea)
       /Foam::max(exactInnerArea, VSMALL),
        Foam::mag(meshOuterArea - exactOuterArea)
       /Foam::max(exactOuterArea, VSMALL)
    );
    if (radialTwoZone && meshZoneAreaRelativeError > 1.0e-8)
    {
        FatalErrorInFunction << "Radial interface does not align with mesh: "
            << meshZoneAreaRelativeError << exit(FatalError);
    }
    const scalar radialInnerDarcyResistance =
        dynamicViscosity*bedDepth/(exactInnerArea*innerPermeability);
    const scalar radialOuterDarcyResistance =
        dynamicViscosity*bedDepth/(exactOuterArea*outerPermeability);
    const scalar innerKI = darcyForchheimer
      ? (
            inertialPermeabilityModel == "wadsworth2026CeramicsFit"
          ? wadsworth2026CeramicsInertialPermeability(innerPermeability)
          : innerInertialPermeability
        )
      : GREAT;
    const scalar outerKI = darcyForchheimer
      ? (
            inertialPermeabilityModel == "wadsworth2026CeramicsFit"
          ? wadsworth2026CeramicsInertialPermeability(outerPermeability)
          : outerInertialPermeability
        )
      : GREAT;
    const scalar radialInnerInertialResistance = darcyForchheimer
      ? liquidDensity*bedDepth/(sqr(exactInnerArea)*innerKI) : 0.0;
    const scalar radialOuterInertialResistance = darcyForchheimer
      ? liquidDensity*bedDepth/(sqr(exactOuterArea)*outerKI) : 0.0;
    const RadialPuckParameters radialPuckParameters
    {
        radialInnerDarcyResistance, radialOuterDarcyResistance,
        radialInnerInertialResistance, radialOuterInertialResistance
    };
    scalar continuumResistance = bedDepth/saturatedPermeability;
    if (permeabilityProfile == "axial_two_layer")
    {
        continuumResistance =
            layerInterfacePosition/layerPermeabilityUpstream
          + (bedDepth - layerInterfacePosition)
           /layerPermeabilityDownstream;
    }
    scalar continuumInertialIntegral = 0.0;
    if (darcyForchheimer)
    {
        if (inertialPermeabilityModel == "wadsworth2026CeramicsFit")
        {
            if (permeabilityProfile == "axial_two_layer")
            {
                continuumInertialIntegral =
                    layerInterfacePosition
                   /wadsworth2026CeramicsInertialPermeability
                    (layerPermeabilityUpstream)
                  + (bedDepth - layerInterfacePosition)
                   /wadsworth2026CeramicsInertialPermeability
                    (layerPermeabilityDownstream);
            }
            else
            {
                continuumInertialIntegral =
                    bedDepth
                   /wadsworth2026CeramicsInertialPermeability
                    (saturatedPermeability);
            }
        }
        else if (permeabilityProfile == "axial_two_layer")
        {
            continuumInertialIntegral =
                layerInterfacePosition/layerInertialPermeabilityUpstream
              + (bedDepth - layerInterfacePosition)
               /layerInertialPermeabilityDownstream;
        }
        else
        {
            continuumInertialIntegral =
                bedDepth/constantInertialPermeability;
        }
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
        const scalar radius = Foam::sqrt
        (
            sqr(mesh.C()[celli].y()) + sqr(mesh.C()[celli].z())
        );
        const bool innerDiagnosticZone = radius < interfaceRadius;
        permeabilityZoneId[celli] = innerDiagnosticZone ? 0.0 : 1.0;
        if (permeabilityProfile == "axial_two_layer")
        {
            permeability[celli] =
                mesh.C()[celli].x() < layerInterfacePosition
              ? layerPermeabilityUpstream
              : layerPermeabilityDownstream;
        }
        else if (radialTwoZone)
        {
            permeability[celli] =
                innerDiagnosticZone ? innerPermeability : outerPermeability;
        }
        else
        {
            permeability[celli] =
                poroelasticCompaction
              ? stressFreePermeability
              : saturatedPermeability;
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
    permeabilityZoneId.correctBoundaryConditions();
    effectiveMatrixStress.correctBoundaryConditions();
    normalizedEffectiveStress.correctBoundaryConditions();
    compactionStrain.correctBoundaryConditions();
    mechanicalPorosity.correctBoundaryConditions();
    compactionPermeabilityRatio.correctBoundaryConditions();
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

    surfaceScalarField poroelasticFaceMobility
    (
        IOobject
        (
            "poroelasticFaceMobility",
            runTime.name(),
            mesh,
            IOobject::NO_READ,
            IOobject::NO_WRITE
        ),
        fvc::interpolate(hydraulicMobility)
    );

    volScalarField inertialPermeability
    (
        IOobject
        (
            "inertialPermeability", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("kI", dimLength, constantInertialPermeability)
    );
    forAll(inertialPermeability, celli)
    {
        if (inertialPermeabilityModel == "wadsworth2026CeramicsFit")
        {
            inertialPermeability[celli] =
                wadsworth2026CeramicsInertialPermeability(permeability[celli]);
        }
        else if (permeabilityProfile == "axial_two_layer")
        {
            inertialPermeability[celli] =
                mesh.C()[celli].x() < layerInterfacePosition
              ? layerInertialPermeabilityUpstream
              : layerInertialPermeabilityDownstream;
        }
        else if (radialTwoZone)
        {
            const scalar radius = Foam::sqrt
            (
                sqr(mesh.C()[celli].y()) + sqr(mesh.C()[celli].z())
            );
            inertialPermeability[celli] =
                radius < interfaceRadius
              ? innerInertialPermeability
              : outerInertialPermeability;
        }
    }
    inertialPermeability.correctBoundaryConditions();

    volScalarField nonlinearMobility
    (
        IOobject
        (
            "nonlinearMobility", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        hydraulicMobility
    );
    volScalarField forchheimerNumber
    (
        IOobject
        (
            "forchheimerNumber", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", dimless, 0.0)
    );
    volScalarField inertialPressureFraction
    (
        IOobject
        (
            "inertialPressureFraction", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", dimless, 0.0)
    );
    volScalarField darcyDragMagnitude
    (
        IOobject
        (
            "darcyDragMagnitude", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar
        (
            "zero", dimensionSet(1, -2, -2, 0, 0, 0, 0), 0.0
        )
    );
    volScalarField inertialDragMagnitude
    (
        IOobject
        (
            "inertialDragMagnitude", runTime.name(), mesh,
            IOobject::NO_READ,
            darcyForchheimer ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        darcyDragMagnitude
    );

    volScalarField effectivePermeabilityMultiplier
    (
        IOobject
        (
            "effectivePermeabilityMultiplier",
            runTime.name(),
            mesh,
            IOobject::NO_READ,
            effectivePermeabilityEnabled ? IOobject::AUTO_WRITE : IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar("one", dimless, 1.0)
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
              << "pressure_probe_2_Pa,"
              << "upstreamPressurePa,basketPressurePa,outletPressurePa,"
              << "supplyFlowM3s,puckFlowM3s,compliantStorageM3,"
              << "cumulativeSupplyM3,cumulativePuckIntakeM3,"
              << "cumulativePuckOutletM3,machineWaterBalanceResidualM3,"
              << "couplingResidualM3s,couplingIterations,"
              << "couplingConverged,couplingBracketed,couplingFallbackUsed,"
              << "saturationTransitionStep,pressureBoundaryModel,"
              << "flowResistanceModel,inertialPermeabilityModel,"
              << "inertialPermeabilityMinM,inertialPermeabilityMaxM,"
              << "fluxWeightedForchheimerNumber,maximumForchheimerNumber,"
              << "integratedDarcyPressureDropPa,"
              << "integratedInertialPressureDropPa,"
              << "integratedInertialPressureFraction,"
              << "nonlinearIterations,nonlinearResidual,nonlinearConverged,"
              << "machinePuckFlowM3s,openFoamOutletFlowM3s,"
              << "machineFluxRelativeDifference,"
              << "permeabilityProfile,interfaceRadiusM,innerAreaM2,"
              << "outerAreaM2,innerAreaFraction,outerAreaFraction,"
              << "innerCellVolumeM3,outerCellVolumeM3,"
              << "innerPermeabilityM2,outerPermeabilityM2,"
              << "innerInertialPermeabilityM,outerInertialPermeabilityM,"
              << "innerOutletFlowM3s,outerOutletFlowM3s,innerFlowFraction,"
              << "outerFlowFraction,innerFocusingFactor,outerFocusingFactor,"
              << "hydraulicMaldistributionIndex,"
              << "effectiveHydraulicAreaFraction,innerCumulativeLiquidM3,"
              << "outerCumulativeLiquidM3,innerSoluteFluxKgS,"
              << "outerSoluteFluxKgS,totalSoluteFluxKgS,"
              << "innerCumulativeSoluteKg,"
              << "outerCumulativeSoluteKg,innerInitialExtractableKg,"
              << "outerInitialExtractableKg,innerRemainingExtractableKg,"
              << "outerRemainingExtractableKg,innerExtractedSolidsKg,"
              << "outerExtractedSolidsKg,innerRetainedLiquidKg,"
              << "outerRetainedLiquidKg,innerMeanConcentrationKgM3,"
              << "outerMeanConcentrationKgM3,innerExtractionFraction,"
              << "outerExtractionFraction,extractionMaldistributionIndex,"
              << "maximumRadialVelocityMS,radialToAxialVelocityRatio,"
              << "machineTotalPuckFlowM3s,openFoamTotalOutletFlowM3s,"
              << "machineInnerFlowM3s,openFoamInnerOutletFlowM3s,"
              << "machineOuterFlowM3s,openFoamOuterOutletFlowM3s,"
              << "totalFluxRelativeDifference,innerFluxRelativeDifference,"
              << "outerFluxRelativeDifference,radialHeterogeneityActive,"
              << "basketOperatingPointIterations,basketOperatingResidualPa,"
              << "basketOperatingBracketed,basketOperatingConverged,"
              << "bedMechanicsModel,poroelasticCompactionModel,"
              << "stressFreePorosity,criticalCompactionPressurePa,"
              << "effectiveYoungModulusPa,stressFreePermeabilityM2,"
              << "compactionActive,mechanicalPorosityCoupledToStorage,"
              << "maximumEffectiveStressPa,"
              << "maximumNormalizedEffectiveStress,"
              << "minimumMechanicalPorosity,outletMechanicalPorosity,"
              << "volumeWeightedMechanicalPorosity,"
              << "maximumCompactionStrain,predictedBedHeightRatio,"
              << "predictedBedHeightM,mechanicalPoreVolumeChangeM3,"
              << "minimumCompactionPermeabilityM2,"
              << "outletCompactionPermeabilityM2,"
              << "volumeWeightedPermeabilityM2,"
              << "minimumPermeabilityRatio,"
              << "poroelasticExactScalarFlowM3s,"
              << "poroelasticFlowClosureError,"
              << "poroelasticNonlinearIterations,"
              << "poroelasticNonlinearResidual,"
              << "poroelasticNonlinearConverged";
        if (effectivePermeabilityEnabled)
        {
            trace << ",effective_permeability_branch_active,source_time_s,"
                  << "source_state_time_s,source_support_status,"
                  << "source_dissolved_mass_g,source_phi_t,"
                  << "source_static_flow_g_per_s,source_dynamic_flow_g_per_s,"
                  << "effective_permeability_multiplier_raw,"
                  << "effective_permeability_multiplier,"
                  << "effective_permeability_m2";
        }
        trace << '\n';
    }

    scalar localInitialStoredWaterMass = 0.0;
    forAll(saturation, celli)
    {
        localInitialStoredWaterMass +=
            liquidDensity*porosity[celli]*saturation[celli]*mesh.V()[celli];
    }
    const scalar initialStoredWaterMass =
        sectorScale*globalSumValue(localInitialStoredWaterMass);
    scalar localInnerVolume = 0.0;
    scalar localOuterVolume = 0.0;
    forAll(mesh.V(), celli)
    {
        if (permeabilityZoneId[celli] < 0.5)
        {
            localInnerVolume += mesh.V()[celli];
        }
        else
        {
            localOuterVolume += mesh.V()[celli];
        }
    }
    const scalar innerCellVolume = sectorScale*globalSumValue(localInnerVolume);
    const scalar outerCellVolume = sectorScale*globalSumValue(localOuterVolume);
    const scalar innerInitialExtractableMass =
        initialExtractableDensity*innerCellVolume;
    const scalar outerInitialExtractableMass =
        initialExtractableDensity*outerCellVolume;

    scalar firstDripTime = wetFront >= bedDepth - SMALL ? 0.0 : -1.0;
    scalar timeToTargetMass = -1.0;
    scalar cumulativeInletWaterMass = 0.0;
    scalar cupWaterMass = 0.0;
    scalar cupSoluteMass = 0.0;
    scalar soluteBackDiffusionMass = 0.0;
    scalar previousStoredWaterMass = initialStoredWaterMass;
    scalar previousCupBeverageMass = 0.0;
    scalar upstreamPressure = initialUpstreamPressure;
    scalar cumulativeSupplyVolume = 0.0;
    scalar cumulativePuckIntakeVolume = 0.0;
    scalar cumulativePuckOutletVolume = 0.0;
    scalar innerCumulativeLiquid = 0.0;
    scalar outerCumulativeLiquid = 0.0;
    scalar innerCumulativeSolute = 0.0;
    scalar outerCumulativeSolute = 0.0;

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
        scalar inletPressure = rampedPressure
        (
            timeValue,
            targetInletPressure,
            pressureRampTime
        );
        scalar supplyFlow = 0.0;
        scalar puckFlow = 0.0;
        scalar couplingResidual = 0.0;
        label couplingIterations = 0;
        bool couplingConverged = true;
        scalar machineInnerFlow = 0.0;
        scalar machineOuterFlow = 0.0;
        scalar basketOperatingResidual = 0.0;
        label basketOperatingIterations = 0;
        bool basketOperatingBracketed = true;
        bool basketOperatingConverged = true;
        const bool saturatedAtStepStart =
            wetFront >= bedDepth - SMALL;
        scalar currentDarcyIntegral = continuumResistance;
        scalar currentInertialIntegral = continuumInertialIntegral;
        if (lumpedMachine)
        {
            scalar multiplierForConductance = 1.0;
            if (effectivePermeabilityEnabled && saturatedAtStepStart)
            {
                const scalar stateTime = Foam::max
                (
                    timeValue - sourceToSolverOffsetS,
                    sourceValidityStartS
                );
                const scalar dm = 0.5*sourceKSolidsG
                    *(1.0 + Foam::tanh((stateTime-sourceLSolidsS)/sourceMSolidsS));
                const scalar phi = dm/sourceDoseG;
                const scalar phiM = sourceKSolidsG/sourceDoseG;
                const scalar qMaster = sourceQcGPerS/wp02PhiFactor(phiM);
                const scalar pMaster = sourcePcBar/phiM;
                const scalar qStatic = sourceQcGPerS
                    *wp02Qhat(sourceReferencePressureBar/sourcePcBar);
                const scalar qDynamic = Foam::max
                (
                    0.0,
                    wp02Qhat(sourceReferencePressureBar/(pMaster*phi))
                   *qMaster*wp02PhiFactor(phi)
                );
                multiplierForConductance = Foam::min
                (
                    maximumMultiplier,
                    Foam::max(minimumMultiplier, qDynamic/qStatic)
                );
            }
            const scalar couplingResistance =
                effectivePermeabilityEnabled && saturatedAtStepStart
              ? continuumResistance/multiplierForConductance
              : continuumResistance;
            currentDarcyIntegral = couplingResistance;
            if
            (
                darcyForchheimer
             && inertialPermeabilityModel == "wadsworth2026CeramicsFit"
             && effectivePermeabilityEnabled && saturatedAtStepStart
            )
            {
                currentInertialIntegral =
                    bedDepth/wadsworth2026CeramicsInertialPermeability
                    (
                        saturatedPermeability*multiplierForConductance
                    );
            }
            const scalar conductance =
                fullCrossSectionArea/(dynamicViscosity*couplingResistance);
            const scalar inertialResistance =
                darcyForchheimer
              ? liquidDensity*currentInertialIntegral
               /sqr(fullCrossSectionArea)
              : 0.0;
            const MachineBoundaryState machineState = solveMachineBoundary
            (
                timeValue, deltaT, upstreamPressure, outletPressure,
                machineParameters, saturatedAtStepStart, conductance,
                inertialResistance,
                frontPressure, wetFront, bedDepth, fullCrossSectionArea,
                initialPorosity, wettingPermeability, dynamicViscosity,
                radialTwoZone && saturatedAtStepStart
              ? &radialPuckParameters : nullptr,
                poroelasticCompaction && saturatedAtStepStart
              ? &poroelasticPuckParameters : nullptr
            );
            if (!machineState.bracketed)
            {
                FatalErrorInFunction << "Machine coupling bracket failure at t="
                    << timeValue << exit(FatalError);
            }
            if (!machineState.converged)
            {
                FatalErrorInFunction << "Machine coupling failed at t="
                    << timeValue << " residual=" << machineState.residual
                    << exit(FatalError);
            }
            upstreamPressure = machineState.upstreamPressure;
            inletPressure = machineState.basketPressure;
            supplyFlow = machineState.supplyFlow;
            puckFlow = machineState.puckFlow;
            couplingResidual = machineState.residual;
            couplingIterations = machineState.iterations;
            machineInnerFlow = machineState.innerPuckFlow;
            machineOuterFlow = machineState.outerPuckFlow;
            basketOperatingResidual = machineState.basketResidual;
            basketOperatingIterations = machineState.basketIterations;
            basketOperatingBracketed = machineState.basketBracketed;
            basketOperatingConverged = machineState.basketConverged;
            if
            (
                (radialTwoZone || poroelasticCompaction) && saturatedAtStepStart
             && (
                    !basketOperatingBracketed
                 || !basketOperatingConverged
                )
            )
            {
                FatalErrorInFunction << "Radial basket operating point failed"
                    << exit(FatalError);
            }
            cumulativeSupplyVolume += supplyFlow*deltaT;
            cumulativePuckIntakeVolume += puckFlow*deltaT;
        }
        else
        {
            upstreamPressure = inletPressure;
        }
        scalar wettingPressureIntegral =
            positiveDrivingPressureIntegral
            (
                stepStartTime,
                timeValue,
                targetInletPressure,
                pressureRampTime,
                frontPressure
            );
        if (lumpedMachine)
        {
            wettingPressureIntegral =
                Foam::max(inletPressure - frontPressure, 0.0)*deltaT;
        }
        const scalar wettingStepAverageDrivingPressure =
            wettingPressureIntegral/Foam::max(deltaT, SMALL);

        scalarField previousSaturation(saturation.size(), 0.0);
        forAll(saturation, celli)
        {
            previousSaturation[celli] = saturation[celli];
        }

        const scalar previousWetFront = wetFront;
        bool saturationTransitionStep = false;
        scalar sourceTimeS = timeValue - sourceToSolverOffsetS;
        scalar sourceStateTimeS = sourceTimeS;
        scalar sourceDissolvedMassG = 0.0;
        scalar sourcePhiT = 0.0;
        scalar sourceStaticFlowGPerS = 0.0;
        scalar sourceDynamicFlowGPerS = 0.0;
        scalar effectiveMultiplierRaw = 1.0;
        scalar effectiveMultiplier = 1.0;
        word sourceSupportStatus("UNSATURATED_BRANCH_INACTIVE");
        if (effectivePermeabilityEnabled && saturatedAtStepStart)
        {
            sourceStateTimeS = Foam::max(sourceTimeS, sourceValidityStartS);
            sourceSupportStatus =
                sourceTimeS < sourceValidityStartS
              ? "PRE_SOURCE_SUPPORT_SATURATED_HOLD"
              : "SOURCE_SUPPORTED_SATURATED_STAGE";
            sourceDissolvedMassG =
                0.5*sourceKSolidsG
               *(1.0 + Foam::tanh
                (
                    (sourceStateTimeS - sourceLSolidsS)/sourceMSolidsS
                ));
            sourcePhiT = sourceDissolvedMassG/sourceDoseG;
            const scalar phiM = sourceKSolidsG/sourceDoseG;
            const scalar qMaster = sourceQcGPerS/wp02PhiFactor(phiM);
            const scalar pMaster = sourcePcBar/phiM;
            sourceStaticFlowGPerS =
                sourceQcGPerS*wp02Qhat(sourceReferencePressureBar/sourcePcBar);
            sourceDynamicFlowGPerS = Foam::max
            (
                0.0,
                wp02Qhat(sourceReferencePressureBar/(pMaster*sourcePhiT))
               *qMaster*wp02PhiFactor(sourcePhiT)
            );
            effectiveMultiplierRaw =
                sourceDynamicFlowGPerS/sourceStaticFlowGPerS;
            if
            (
                !std::isfinite(effectiveMultiplierRaw)
             || effectiveMultiplierRaw < 0.0
             || effectiveMultiplierRaw > maximumMultiplier + 1.0e-10
            )
            {
                FatalErrorInFunction << "Invalid WP02 multiplier "
                    << effectiveMultiplierRaw << exit(FatalError);
            }
            effectiveMultiplier = Foam::min
            (
                maximumMultiplier,
                Foam::max(minimumMultiplier, effectiveMultiplierRaw)
            );
            permeability =
                dimensionedScalar
                (
                    "effectivePermeability",
                    permeability.dimensions(),
                    saturatedPermeability*effectiveMultiplier
                );
            permeability.correctBoundaryConditions();
            hydraulicMobility = permeability/dynamicViscosityCoefficient;
            hydraulicMobility.correctBoundaryConditions();
            currentDarcyIntegral =
                bedDepth/(saturatedPermeability*effectiveMultiplier);
            if
            (
                darcyForchheimer
             && inertialPermeabilityModel == "wadsworth2026CeramicsFit"
            )
            {
                inertialPermeability =
                    dimensionedScalar
                    (
                        "effectiveInertialPermeability",
                        inertialPermeability.dimensions(),
                        wadsworth2026CeramicsInertialPermeability
                        (
                            saturatedPermeability*effectiveMultiplier
                        )
                    );
                inertialPermeability.correctBoundaryConditions();
                currentInertialIntegral =
                    bedDepth/inertialPermeability[0];
            }
            effectivePermeabilityMultiplier =
                dimensionedScalar("multiplier", dimless, effectiveMultiplier);
            effectivePermeabilityMultiplier.correctBoundaryConditions();
        }

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
                saturationTransitionStep = true;
                const scalar requiredIntegral =
                    (sqr(bedDepth) - sqr(previousWetFront))
                   *initialPorosity*dynamicViscosity
                   /(2.0*wettingPermeability);
                if (lumpedMachine)
                {
                    const scalar coupledDrivingPressure =
                        Foam::max(inletPressure - frontPressure, 0.0);
                    if (coupledDrivingPressure <= VSMALL)
                    {
                        FatalErrorInFunction
                            << "Zero coupled pressure at saturation crossing"
                            << exit(FatalError);
                    }
                    firstDripTime = stepStartTime
                      + requiredIntegral/coupledDrivingPressure;
                }
                else
                {
                    firstDripTime = pressureIntegralCrossingTime
                    (
                        stepStartTime,
                        timeValue,
                        requiredIntegral,
                        targetInletPressure,
                        pressureRampTime,
                        frontPressure
                    );
                }
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
        label nonlinearIterations = 0;
        scalar nonlinearResidual = 0.0;
        bool nonlinearConverged = !darcyForchheimer;
        scalar integratedDarcyPressureDrop = 0.0;
        scalar integratedInertialPressureDrop = 0.0;
        scalar fluxWeightedFo = 0.0;
        scalar maximumFo = 0.0;
        scalar inertialPermeabilityMin = 0.0;
        scalar inertialPermeabilityMax = 0.0;
        scalar integratedInertialFraction = 0.0;
        scalar machineFluxRelativeDifference = 0.0;
        label poroelasticIterations = 0;
        scalar poroelasticResidual = 0.0;
        scalar poroelasticFlowClosureError = 0.0;
        bool poroelasticConverged =
            !poroelasticCompaction || !saturatedAtStepStart;
        const scalar poroelasticExactFlow =
            poroelasticCompaction && saturatedAtStepStart
          ? poroelasticPuckFlow
            (
                inletPressure - outletPressure,
                poroelasticPuckParameters
            )
          : 0.0;

        if (saturatedAtStepStart)
        {
            if (poroelasticCompaction)
            {
                label localInvalidInitialPressure = 0;
                forAll(p, celli)
                {
                    const scalar sigma = inletPressure - p[celli];
                    if
                    (
                        !std::isfinite(sigma)
                     || sigma < 0.0
                     || sigma >= criticalCompactionPressure
                    )
                    {
                        localInvalidInitialPressure = 1;
                    }
                }
                if (globalMaxValue(localInvalidInitialPressure))
                {
                    forAll(p, celli)
                    {
                        const scalar axialFraction = Foam::min
                        (
                            Foam::max(mesh.C()[celli].x()/bedDepth, 0.0),
                            1.0
                        );
                        p[celli] =
                            inletPressure
                          - axialFraction*(inletPressure - outletPressure);
                    }
                    p.boundaryFieldRef()[inletPatchId] == inletPressure;
                    p.boundaryFieldRef()[outletPatchId] == outletPressure;
                    p.correctBoundaryConditions();
                }
                scalar previousFlow = -1.0;
                for
                (
                    label iteration = 1;
                    iteration <= poroelasticMaximumIterations;
                    ++iteration
                )
                {
                    scalarField previousPressure(p.primitiveField());
                    const labelUList& owner = mesh.owner();
                    const labelUList& neighbour = mesh.neighbour();
                    forAll(neighbour, facei)
                    {
                        poroelasticFaceMobility[facei] =
                            poroelasticSecantMobility
                            (
                                inletPressure - p[owner[facei]],
                                inletPressure - p[neighbour[facei]],
                                stressFreePorosity,
                                criticalCompactionPressure,
                                stressFreePermeability,
                                dynamicViscosity
                            );
                    }
                    forAll(p.boundaryField(), patchi)
                    {
                        const fvPatchScalarField& pressurePatch =
                            p.boundaryField()[patchi];
                        const scalarField internalPressure
                        (
                            pressurePatch.patchInternalField()
                        );
                        scalarField otherPressure(pressurePatch);
                        if (pressurePatch.coupled())
                        {
                            otherPressure =
                                pressurePatch.patchNeighbourField();
                        }
                        fvsPatchScalarField& mobilityPatch =
                            poroelasticFaceMobility.boundaryFieldRef()[patchi];
                        forAll(mobilityPatch, facei)
                        {
                            mobilityPatch[facei] =
                                poroelasticSecantMobility
                                (
                                    inletPressure - internalPressure[facei],
                                    inletPressure - otherPressure[facei],
                                    stressFreePorosity,
                                    criticalCompactionPressure,
                                    stressFreePermeability,
                                    dynamicViscosity
                            );
                        }
                    }
                    forAll(poroelasticFaceMobility, facei)
                    {
                        if
                        (
                            !std::isfinite(poroelasticFaceMobility[facei])
                         || poroelasticFaceMobility[facei] <= 0.0
                        )
                        {
                            FatalErrorInFunction
                                << "Invalid internal poroelastic face mobility "
                                << poroelasticFaceMobility[facei]
                                << " on face " << facei
                                << exit(FatalError);
                        }
                    }
                    forAll(poroelasticFaceMobility.boundaryField(), patchi)
                    {
                        const fvsPatchScalarField& mobilityPatch =
                            poroelasticFaceMobility.boundaryField()[patchi];
                        forAll(mobilityPatch, facei)
                        {
                            if
                            (
                                !std::isfinite(mobilityPatch[facei])
                             || mobilityPatch[facei] <= 0.0
                            )
                            {
                                FatalErrorInFunction
                                    << "Invalid boundary poroelastic face mobility "
                                    << mobilityPatch[facei] << " on patch "
                                    << patchi << " face " << facei
                                    << exit(FatalError);
                            }
                        }
                    }
                    fvScalarMatrix pressureEquation
                    (
                        fvm::laplacian(poroelasticFaceMobility, p)
                    );
                    const SolverPerformance<scalar> performance
                    (
                        pressureEquation.solve()
                    );
                    if (iteration == 1)
                    {
                        pressureInitialResidual = performance.initialResidual();
                    }
                    pressureFinalResidual = performance.finalResidual();
                    pressureIterations += performance.nIterations();
                    darcyFlux = -pressureEquation.flux();

                    scalar localPressureChange = 0.0;
                    forAll(p, celli)
                    {
                        p[celli] =
                            previousPressure[celli]
                          + poroelasticUnderRelaxation
                           *(p[celli] - previousPressure[celli]);
                        localPressureChange = Foam::max
                        (
                            localPressureChange,
                            Foam::mag(p[celli] - previousPressure[celli])
                           /Foam::max
                            (
                                Foam::mag(inletPressure - outletPressure),
                                1.0
                            )
                        );
                    }
                    p.boundaryFieldRef()[inletPatchId] == inletPressure;
                    p.boundaryFieldRef()[outletPatchId] == outletPressure;
                    p.correctBoundaryConditions();

                    const scalar stressTolerance =
                        1.0e-10*criticalCompactionPressure;
                    forAll(permeability, celli)
                    {
                        scalar sigma = inletPressure - p[celli];
                        if
                        (
                            sigma < -stressTolerance
                         || sigma >= criticalCompactionPressure
                         || !std::isfinite(sigma)
                        )
                        {
                            FatalErrorInFunction
                                << "Poroelastic stress outside domain at t="
                                << timeValue << ": " << sigma
                                << exit(FatalError);
                        }
                        if (sigma < 0.0)
                        {
                            sigma = 0.0;
                        }
                        const scalar ratio = poroelasticPermeabilityRatio
                        (
                            sigma, stressFreePorosity,
                            criticalCompactionPressure
                        );
                        effectiveMatrixStress[celli] = sigma;
                        normalizedEffectiveStress[celli] =
                            sigma/criticalCompactionPressure;
                        compactionStrain[celli] = poroelasticStrain
                        (
                            sigma, stressFreePorosity,
                            criticalCompactionPressure
                        );
                        mechanicalPorosity[celli] =
                            poroelasticMechanicalPorosity
                            (
                                sigma, stressFreePorosity,
                                criticalCompactionPressure
                            );
                        compactionPermeabilityRatio[celli] = ratio;
                        permeability[celli] = stressFreePermeability*ratio;
                    }
                    effectiveMatrixStress.correctBoundaryConditions();
                    normalizedEffectiveStress.correctBoundaryConditions();
                    compactionStrain.correctBoundaryConditions();
                    mechanicalPorosity.correctBoundaryConditions();
                    compactionPermeabilityRatio.correctBoundaryConditions();
                    permeability.correctBoundaryConditions();
                    hydraulicMobility =
                        permeability/dynamicViscosityCoefficient;
                    hydraulicMobility.correctBoundaryConditions();

                    U = -hydraulicMobility*fvc::grad(p);
                    U.correctBoundaryConditions();
                    scalar localOutlet = 0.0;
                    const fvsPatchScalarField& iterationOutlet =
                        darcyFlux.boundaryField()[outletPatchId];
                    forAll(iterationOutlet, facei)
                    {
                        localOutlet += Foam::max(iterationOutlet[facei], 0.0);
                    }
                    const scalar iterationFlow =
                        sectorScale*globalSumValue(localOutlet);
                    const scalar flowChange =
                        previousFlow < 0.0
                      ? GREAT
                      : Foam::mag(iterationFlow - previousFlow)
                       /Foam::max(Foam::mag(iterationFlow), VSMALL);
                    const scalar pressureChange =
                        globalMaxValue(localPressureChange);
                    poroelasticFlowClosureError =
                        Foam::mag(iterationFlow - poroelasticExactFlow)
                       /Foam::max(Foam::mag(poroelasticExactFlow), VSMALL);
                    // The exact scalar-flow comparison is a continuous
                    // verification diagnostic.  It is not a residual of the
                    // discretized Picard equation and therefore must not gate
                    // nonlinear convergence at the iteration tolerance.
                    poroelasticResidual = Foam::max
                    (
                        Foam::max(flowChange, pressureChange),
                        pressureFinalResidual
                    );
                    poroelasticIterations = iteration;
                    if
                    (
                        flowChange <= poroelasticRelativeTolerance
                     && pressureChange <= poroelasticAbsoluteTolerance
                     && pressureFinalResidual <= poroelasticAbsoluteTolerance
                    )
                    {
                        poroelasticConverged = true;
                        break;
                    }
                    previousFlow = iterationFlow;
                }
                if (!poroelasticConverged)
                {
                    FatalErrorInFunction
                        << "Poroelastic nonlinear solve failed at t="
                        << timeValue << " residual=" << poroelasticResidual
                        << " closure=" << poroelasticFlowClosureError
                        << exit(FatalError);
                }
            }
            else if (!darcyForchheimer)
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
                scalar previousFlow = -1.0;
                nonlinearMobility = hydraulicMobility;
                for
                (
                    label iteration = 1;
                    iteration <= nonlinearMaximumIterations;
                    ++iteration
                )
                {
                    scalarField previousPressure(p.primitiveField());
                    fvScalarMatrix pressureEquation
                    (
                        fvm::laplacian(nonlinearMobility, p)
                    );
                    const SolverPerformance<scalar> performance
                    (
                        pressureEquation.solve()
                    );
                    if (iteration == 1)
                    {
                        pressureInitialResidual = performance.initialResidual();
                    }
                    pressureFinalResidual = performance.finalResidual();
                    pressureIterations += performance.nIterations();
                    darcyFlux = -pressureEquation.flux();

                    scalar localOutlet = 0.0;
                    const fvsPatchScalarField& iterationOutlet =
                        darcyFlux.boundaryField()[outletPatchId];
                    forAll(iterationOutlet, facei)
                    {
                        localOutlet += Foam::max(iterationOutlet[facei], 0.0);
                    }
                    const scalar iterationFlow =
                        sectorScale*globalSumValue(localOutlet);

                    scalar localPressureChange = 0.0;
                    const volVectorField pressureGradient(fvc::grad(p));
                    const scalar seriesSpeed =
                        iterationFlow/fullCrossSectionArea;
                    forAll(nonlinearMobility, celli)
                    {
                        const scalar g = mag(pressureGradient[celli]);
                        const scalar localSpeed = radialTwoZone
                          ? stableForchheimerSpeed
                            (
                                g, permeability[celli],
                                inertialPermeability[celli],
                                dynamicViscosity, liquidDensity
                            )
                          : seriesSpeed;
                        const scalar targetMobility =
                            !radialTwoZone
                          ? 1.0/
                            (
                                dynamicViscosity/permeability[celli]
                              + liquidDensity*seriesSpeed
                               /inertialPermeability[celli]
                            )
                          : g <= VSMALL
                          ? permeability[celli]/dynamicViscosity
                          : localSpeed/g;
                        nonlinearMobility[celli] =
                            (1.0 - nonlinearUnderRelaxation)
                           *nonlinearMobility[celli]
                          + nonlinearUnderRelaxation*targetMobility;
                        localPressureChange = Foam::max
                        (
                            localPressureChange,
                            Foam::mag(p[celli] - previousPressure[celli])
                           /Foam::max(Foam::mag(p[celli]), 1.0)
                        );
                    }
                    forAll(nonlinearMobility.boundaryField(), patchi)
                    {
                        if
                        (
                            !nonlinearMobility.boundaryField()[patchi].coupled()
                        )
                        {
                            nonlinearMobility.boundaryFieldRef()[patchi] ==
                                nonlinearMobility.boundaryField()[patchi]
                               .patchInternalField();
                        }
                    }
                    nonlinearMobility.correctBoundaryConditions();
                    const scalar pressureChange =
                        globalMaxValue(localPressureChange);
                    const scalar flowChange =
                        previousFlow < 0.0
                      ? GREAT
                      : Foam::mag(iterationFlow - previousFlow)
                       /Foam::max(Foam::mag(iterationFlow), VSMALL);
                    const scalar expectedFlow = radialTwoZone
                      ? stableSeriesFlow
                        (
                            inletPressure - outletPressure,
                            radialInnerDarcyResistance,
                            radialInnerInertialResistance
                        )
                       + stableSeriesFlow
                        (
                            inletPressure - outletPressure,
                            radialOuterDarcyResistance,
                            radialOuterInertialResistance
                        )
                      : stableSeriesFlow
                        (
                            inletPressure - outletPressure,
                            dynamicViscosity*currentDarcyIntegral
                           /fullCrossSectionArea,
                            liquidDensity*currentInertialIntegral
                           /sqr(fullCrossSectionArea)
                        );
                    const scalar closure =
                        Foam::mag(iterationFlow - expectedFlow)
                       /Foam::max(Foam::mag(expectedFlow), VSMALL);
                    nonlinearResidual =
                        Foam::max(Foam::max(flowChange, pressureChange), closure);
                    nonlinearIterations = iteration;
                    if
                    (
                        flowChange <= nonlinearRelativeTolerance
                     && pressureChange <= nonlinearAbsoluteTolerance
                     && closure <= nonlinearAbsoluteTolerance
                    )
                    {
                        nonlinearConverged = true;
                        break;
                    }
                    previousFlow = iterationFlow;
                }
                if (!nonlinearConverged)
                {
                    FatalErrorInFunction
                        << "Forchheimer nonlinear solve failed at t="
                        << timeValue << " residual=" << nonlinearResidual
                        << exit(FatalError);
                }
                U = -nonlinearMobility*fvc::grad(p);
                U.correctBoundaryConditions();
                darcyFlux = fvc::flux(U);
            }
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

        const scalar effectiveContinuumResistance =
            effectivePermeabilityEnabled && saturatedAtStepStart
          ? bedDepth/(saturatedPermeability*effectiveMultiplier)
          : continuumResistance;
        const scalar continuumAnalyticalOutletFlow =
            saturatedAtStepStart
          ? (
                poroelasticCompaction
              ? poroelasticExactFlow
              : radialTwoZone
              ? stableSeriesFlow
                (
                    inletPressure - outletPressure,
                    radialInnerDarcyResistance,
                    radialInnerInertialResistance
                )
               + stableSeriesFlow
                (
                    inletPressure - outletPressure,
                    radialOuterDarcyResistance,
                    radialOuterInertialResistance
                )
              : darcyForchheimer
              ? stableSeriesFlow
                (
                    inletPressure - outletPressure,
                    dynamicViscosity*effectiveContinuumResistance
                   /fullCrossSectionArea,
                    liquidDensity*currentInertialIntegral
                   /sqr(fullCrossSectionArea)
                )
              : fullCrossSectionArea
               *Foam::max(inletPressure - outletPressure, 0.0)
               /(dynamicViscosity*effectiveContinuumResistance)
            )
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
        scalar innerOutletFlow = 0.0;
        scalar outerOutletFlow = 0.0;
        scalar innerSoluteRate = 0.0;
        scalar outerSoluteRate = 0.0;

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
                const scalar radius = Foam::sqrt
                (
                    sqr(outletCentres[facei].y())
                  + sqr(outletCentres[facei].z())
                );
                if (radius < interfaceRadius)
                {
                    innerOutletFlow += positiveFlux;
                    innerSoluteRate +=
                        positiveFlux*outletConcentration[facei];
                }
                else
                {
                    outerOutletFlow += positiveFlux;
                    outerSoluteRate +=
                        positiveFlux*outletConcentration[facei];
                }
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
            innerOutletFlow =
                sectorScale*globalSumValue(innerOutletFlow);
            outerOutletFlow =
                sectorScale*globalSumValue(outerOutletFlow);
            innerSoluteRate =
                sectorScale*globalSumValue(innerSoluteRate);
            outerSoluteRate =
                sectorScale*globalSumValue(outerSoluteRate);
            inletBackDiffusionRate =
                sectorScale*globalSumValue(localInletBackDiffusionRate);

            if (darcyForchheimer)
            {
                scalar localMinKI = GREAT;
                scalar localMaxKI = 0.0;
                scalar localMaxFo = 0.0;
                scalar localWeightedFo = 0.0;
                scalar localVelocityWeight = 0.0;
                forAll(permeability, celli)
                {
                    const scalar speed = mag(U[celli]);
                    const scalar fo =
                        liquidDensity*permeability[celli]*speed
                       /(dynamicViscosity*inertialPermeability[celli]);
                    if
                    (
                        !std::isfinite(fo)
                     || !(permeability[celli] > 0.0)
                     || !(inertialPermeability[celli] > 0.0)
                    )
                    {
                        FatalErrorInFunction
                            << "Invalid Forchheimer field state at t="
                            << timeValue << exit(FatalError);
                    }
                    forchheimerNumber[celli] = fo;
                    inertialPressureFraction[celli] = fo/(1.0 + fo);
                    darcyDragMagnitude[celli] =
                        dynamicViscosity*speed/permeability[celli];
                    inertialDragMagnitude[celli] =
                        liquidDensity*sqr(speed)/inertialPermeability[celli];
                    localMinKI = Foam::min
                    (
                        localMinKI, inertialPermeability[celli]
                    );
                    localMaxKI = Foam::max
                    (
                        localMaxKI, inertialPermeability[celli]
                    );
                    localMaxFo = Foam::max(localMaxFo, fo);
                    localWeightedFo += fo*speed*mesh.V()[celli];
                    localVelocityWeight += speed*mesh.V()[celli];
                }
                forchheimerNumber.correctBoundaryConditions();
                inertialPressureFraction.correctBoundaryConditions();
                darcyDragMagnitude.correctBoundaryConditions();
                inertialDragMagnitude.correctBoundaryConditions();
                inertialPermeabilityMin = globalMinValue(localMinKI);
                inertialPermeabilityMax = globalMaxValue(localMaxKI);
                maximumFo = globalMaxValue(localMaxFo);
                const scalar velocityWeight =
                    globalSumValue(localVelocityWeight);
                fluxWeightedFo =
                    globalSumValue(localWeightedFo)
                   /Foam::max(velocityWeight, VSMALL);
                integratedDarcyPressureDrop =
                    dynamicViscosity*currentDarcyIntegral
                   /fullCrossSectionArea*outletVolumeFlow;
                integratedInertialPressureDrop =
                    liquidDensity*currentInertialIntegral
                   /sqr(fullCrossSectionArea)*sqr(outletVolumeFlow);
                integratedInertialFraction =
                    integratedInertialPressureDrop
                   /Foam::max
                    (
                        integratedDarcyPressureDrop
                      + integratedInertialPressureDrop,
                        VSMALL
                    );
            }
            if (lumpedMachine)
            {
                machineFluxRelativeDifference =
                    Foam::mag(puckFlow - outletVolumeFlow)
                   /Foam::max(Foam::mag(puckFlow), VSMALL);
                if
                (
                    saturatedAtStepStart
                 && machineFluxRelativeDifference
                    > (
                        poroelasticCompaction
                      ? poroelasticMachineFluxTolerance
                      : machineFluxRelativeTolerance
                    )
                )
                {
                    FatalErrorInFunction
                        << "Machine/OpenFOAM flux mismatch at t=" << timeValue
                        << ": " << machineFluxRelativeDifference
                        << exit(FatalError);
                }
            }

            cumulativeInletWaterMass +=
                liquidDensity*inletVolumeFlow*deltaT;
            cupWaterMass += liquidDensity*outletVolumeFlow*deltaT;
            cumulativePuckOutletVolume += outletVolumeFlow*deltaT;
            innerCumulativeLiquid += innerOutletFlow*deltaT;
            outerCumulativeLiquid += outerOutletFlow*deltaT;
            innerCumulativeSolute += Foam::max(innerSoluteRate, 0.0)*deltaT;
            outerCumulativeSolute += Foam::max(outerSoluteRate, 0.0)*deltaT;
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
        scalar localMaxRadialVelocity = 0.0;
        scalar localMaxAxialVelocity = 0.0;
        scalar localInnerRemainingMass = 0.0;
        scalar localOuterRemainingMass = 0.0;
        scalar localInnerRetainedLiquid = 0.0;
        scalar localOuterRetainedLiquid = 0.0;
        scalar localInnerConcentrationVolume = 0.0;
        scalar localOuterConcentrationVolume = 0.0;

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
            localMaxAxialVelocity =
                Foam::max(localMaxAxialVelocity, Foam::mag(U[celli].x()));
            localMaxRadialVelocity = Foam::max
            (
                localMaxRadialVelocity,
                Foam::sqrt(sqr(U[celli].y()) + sqr(U[celli].z()))
            );
            if (permeabilityZoneId[celli] < 0.5)
            {
                localInnerRemainingMass +=
                    remainingExtractable[celli]*mesh.V()[celli];
                localInnerRetainedLiquid +=
                    liquidDensity*porosity[celli]*saturation[celli]*mesh.V()[celli];
                localInnerConcentrationVolume +=
                    dissolvedConcentration[celli]*mesh.V()[celli];
            }
            else
            {
                localOuterRemainingMass +=
                    remainingExtractable[celli]*mesh.V()[celli];
                localOuterRetainedLiquid +=
                    liquidDensity*porosity[celli]*saturation[celli]*mesh.V()[celli];
                localOuterConcentrationVolume +=
                    dissolvedConcentration[celli]*mesh.V()[celli];
            }
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
        const scalar maxRadialVelocity =
            globalMaxValue(localMaxRadialVelocity);
        const scalar maxAxialVelocity = globalMaxValue(localMaxAxialVelocity);
        const scalar radialToAxialVelocityRatio =
            maxRadialVelocity/Foam::max(maxAxialVelocity, VSMALL);
        const scalar innerRemainingMass =
            sectorScale*globalSumValue(localInnerRemainingMass);
        const scalar outerRemainingMass =
            sectorScale*globalSumValue(localOuterRemainingMass);
        const scalar innerRetainedLiquid =
            sectorScale*globalSumValue(localInnerRetainedLiquid);
        const scalar outerRetainedLiquid =
            sectorScale*globalSumValue(localOuterRetainedLiquid);
        const scalar innerMeanConcentration =
            sectorScale*globalSumValue(localInnerConcentrationVolume)
           /Foam::max(innerCellVolume, VSMALL);
        const scalar outerMeanConcentration =
            sectorScale*globalSumValue(localOuterConcentrationVolume)
           /Foam::max(outerCellVolume, VSMALL);
        const scalar innerExtractedMass =
            Foam::max(innerInitialExtractableMass - innerRemainingMass, 0.0);
        const scalar outerExtractedMass =
            Foam::max(outerInitialExtractableMass - outerRemainingMass, 0.0);
        const scalar innerExtractionFraction =
            innerExtractedMass/Foam::max(innerInitialExtractableMass, VSMALL);
        const scalar outerExtractionFraction =
            outerExtractedMass/Foam::max(outerInitialExtractableMass, VSMALL);
        const scalar totalExtractedMass =
            innerExtractedMass + outerExtractedMass;
        const scalar extractionMaldistribution =
            totalExtractedMass > VSMALL
          ? 0.5*
            (
                Foam::mag
                (
                    innerExtractedMass/totalExtractedMass - innerAreaFraction
                )
              + Foam::mag
                (
                    outerExtractedMass/totalExtractedMass - outerAreaFraction
                )
            )
          : 0.0;
        const scalar innerFlowFraction =
            outletVolumeFlow > VSMALL
          ? innerOutletFlow/outletVolumeFlow : innerAreaFraction;
        const scalar outerFlowFraction =
            outletVolumeFlow > VSMALL
          ? outerOutletFlow/outletVolumeFlow : outerAreaFraction;
        const scalar innerFocusing =
            innerFlowFraction/innerAreaFraction;
        const scalar outerFocusing =
            outerFlowFraction/outerAreaFraction;
        const scalar hydraulicMaldistribution = 0.5*
        (
            Foam::mag(innerFlowFraction-innerAreaFraction)
          + Foam::mag(outerFlowFraction-outerAreaFraction)
        );
        const scalar effectiveHydraulicArea = 1.0/
        (
            sqr(innerFlowFraction)/innerAreaFraction
          + sqr(outerFlowFraction)/outerAreaFraction
        );
        const scalar totalFluxRelativeDifference = lumpedMachine
          ? Foam::mag(puckFlow-outletVolumeFlow)
           /Foam::max(Foam::mag(puckFlow), VSMALL) : 0.0;
        const scalar innerFluxRelativeDifference =
            lumpedMachine && radialTwoZone && saturatedAtStepStart
          ? Foam::mag(machineInnerFlow-innerOutletFlow)
           /Foam::max(Foam::mag(machineInnerFlow), VSMALL) : 0.0;
        const scalar outerFluxRelativeDifference =
            lumpedMachine && radialTwoZone && saturatedAtStepStart
          ? Foam::mag(machineOuterFlow-outerOutletFlow)
           /Foam::max(Foam::mag(machineOuterFlow), VSMALL) : 0.0;
        if
        (
            lumpedMachine && radialTwoZone && saturatedAtStepStart
         && Foam::max(innerFluxRelativeDifference, outerFluxRelativeDifference)
            > machineFluxRelativeTolerance
        )
        {
            FatalErrorInFunction << "Radial machine/field zone flux mismatch"
                << exit(FatalError);
        }

        scalar localMaximumEffectiveStress = 0.0;
        scalar localMaximumNormalizedStress = 0.0;
        scalar localMinimumMechanicalPorosity = GREAT;
        scalar localWeightedMechanicalPorosity = 0.0;
        scalar localMaximumCompactionStrain = 0.0;
        scalar localWeightedStretch = 0.0;
        scalar localMechanicalPoreVolumeChange = 0.0;
        scalar localMinimumCompactionPermeability = GREAT;
        scalar localWeightedPermeability = 0.0;
        scalar localMinimumPermeabilityRatio = GREAT;
        scalar localReferenceVolume = 0.0;
        forAll(mesh.V(), celli)
        {
            const scalar volume = mesh.V()[celli];
            localMaximumEffectiveStress = Foam::max
            (
                localMaximumEffectiveStress, effectiveMatrixStress[celli]
            );
            localMaximumNormalizedStress = Foam::max
            (
                localMaximumNormalizedStress,
                normalizedEffectiveStress[celli]
            );
            localMinimumMechanicalPorosity = Foam::min
            (
                localMinimumMechanicalPorosity, mechanicalPorosity[celli]
            );
            localWeightedMechanicalPorosity +=
                mechanicalPorosity[celli]*volume;
            localMaximumCompactionStrain = Foam::max
            (
                localMaximumCompactionStrain, compactionStrain[celli]
            );
            localWeightedStretch += (1.0-compactionStrain[celli])*volume;
            localMechanicalPoreVolumeChange +=
                (mechanicalPorosity[celli]-stressFreePorosity)*volume;
            localMinimumCompactionPermeability = Foam::min
            (
                localMinimumCompactionPermeability, permeability[celli]
            );
            localWeightedPermeability += permeability[celli]*volume;
            localMinimumPermeabilityRatio = Foam::min
            (
                localMinimumPermeabilityRatio,
                compactionPermeabilityRatio[celli]
            );
            localReferenceVolume += volume;
            if
            (
                poroelasticCompaction && saturatedAtStepStart
             && (
                    effectiveMatrixStress[celli] < 0.0
                 || normalizedEffectiveStress[celli] < 0.0
                 || normalizedEffectiveStress[celli] >= 1.0
                 || compactionStrain[celli] < 0.0
                 || compactionStrain[celli] >= stressFreePorosity
                 || mechanicalPorosity[celli] <= 0.0
                 || mechanicalPorosity[celli] > stressFreePorosity
                 || permeability[celli] <= 0.0
                 || permeability[celli] > stressFreePermeability
                )
            )
            {
                FatalErrorInFunction << "Invalid bounded compaction field state"
                    << exit(FatalError);
            }
        }
        const scalar referenceVolume =
            globalSumValue(localReferenceVolume);
        const scalar outletEffectiveStress =
            poroelasticCompaction && saturatedAtStepStart
          ? inletPressure - outletPressure : 0.0;
        const scalar outletMechanicalPorosityValue =
            poroelasticCompaction && saturatedAtStepStart
          ? poroelasticMechanicalPorosity
            (
                outletEffectiveStress, stressFreePorosity,
                criticalCompactionPressure
            )
          : stressFreePorosity;
        const scalar outletPermeabilityRatio =
            poroelasticCompaction && saturatedAtStepStart
          ? poroelasticPermeabilityRatio
            (
                outletEffectiveStress, stressFreePorosity,
                criticalCompactionPressure
            )
          : 1.0;
        const scalar outletPermeabilityValue =
            stressFreePermeability*outletPermeabilityRatio;
        const scalar maximumEffectiveStress = Foam::max
        (
            globalMaxValue(localMaximumEffectiveStress),
            outletEffectiveStress
        );
        const scalar maximumNormalizedEffectiveStress =
            maximumEffectiveStress/criticalCompactionPressure;
        const scalar minimumMechanicalPorosity = Foam::min
        (
            globalMinValue(localMinimumMechanicalPorosity),
            outletMechanicalPorosityValue
        );
        const scalar volumeWeightedMechanicalPorosity =
            globalSumValue(localWeightedMechanicalPorosity)
           /Foam::max(referenceVolume, VSMALL);
        const scalar maximumCompactionStrain =
            globalMaxValue(localMaximumCompactionStrain);
        const scalar predictedBedHeightRatio =
            globalSumValue(localWeightedStretch)
           /Foam::max(referenceVolume, VSMALL);
        const scalar predictedBedHeight =
            bedDepth*predictedBedHeightRatio;
        const scalar mechanicalPoreVolumeChange =
            sectorScale*globalSumValue(localMechanicalPoreVolumeChange);
        const scalar minimumCompactionPermeability = Foam::min
        (
            globalMinValue(localMinimumCompactionPermeability),
            outletPermeabilityValue
        );
        const scalar volumeWeightedPermeability =
            globalSumValue(localWeightedPermeability)
           /Foam::max(referenceVolume, VSMALL);
        const scalar minimumPermeabilityRatio = Foam::min
        (
            globalMinValue(localMinimumPermeabilityRatio),
            outletPermeabilityRatio
        );
        const scalar outletMechanicalPorosity =
            outletMechanicalPorosityValue;
        const scalar outletCompactionPermeability =
            outletPermeabilityValue;

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
            const scalar compliantStorage =
                lumpedMachine
              ? machineParameters.compliance
               *(upstreamPressure - initialUpstreamPressure)
              : 0.0;
            const scalar machineWaterBalanceResidual =
                lumpedMachine
              ? cumulativeSupplyVolume - compliantStorage
               - cumulativePuckIntakeVolume
              : 0.0;
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
                  << pressureProbe2 << ','
                  << upstreamPressure << ',' << inletPressure << ','
                  << outletPressure << ',' << supplyFlow << ',' << puckFlow
                  << ',' << compliantStorage << ',' << cumulativeSupplyVolume
                  << ',' << cumulativePuckIntakeVolume << ','
                  << cumulativePuckOutletVolume << ','
                  << machineWaterBalanceResidual << ',' << couplingResidual
                  << ',' << couplingIterations << ','
                  << (couplingConverged ? 1 : 0) << ','
                  << 1 << ',' << 0 << ','
                  << (saturationTransitionStep ? 1 : 0) << ','
                  << pressureBoundaryModel << ','
                  << flowResistanceModel << ','
                  << inertialPermeabilityModel << ','
                  << inertialPermeabilityMin << ','
                  << inertialPermeabilityMax << ','
                  << fluxWeightedFo << ','
                  << maximumFo << ','
                  << integratedDarcyPressureDrop << ','
                  << integratedInertialPressureDrop << ','
                  << integratedInertialFraction << ','
                  << nonlinearIterations << ','
                  << nonlinearResidual << ','
                  << (nonlinearConverged ? 1 : 0) << ','
                  << puckFlow << ','
                  << outletVolumeFlow << ','
                  << machineFluxRelativeDifference;
            trace << ',' << permeabilityProfile
                  << ',' << interfaceRadius
                  << ',' << meshInnerArea << ',' << meshOuterArea
                  << ',' << innerAreaFraction << ',' << outerAreaFraction
                  << ',' << innerCellVolume << ',' << outerCellVolume
                  << ',' << innerPermeability << ',' << outerPermeability
                  << ',' << (darcyForchheimer ? innerKI : 0.0)
                  << ',' << (darcyForchheimer ? outerKI : 0.0)
                  << ',' << innerOutletFlow << ',' << outerOutletFlow
                  << ',' << innerFlowFraction << ',' << outerFlowFraction
                  << ',' << innerFocusing << ',' << outerFocusing
                  << ',' << hydraulicMaldistribution
                  << ',' << effectiveHydraulicArea
                  << ',' << innerCumulativeLiquid
                  << ',' << outerCumulativeLiquid
                  << ',' << innerSoluteRate << ',' << outerSoluteRate
                  << ',' << outletSoluteRate
                  << ',' << innerCumulativeSolute
                  << ',' << outerCumulativeSolute
                  << ',' << innerInitialExtractableMass
                  << ',' << outerInitialExtractableMass
                  << ',' << innerRemainingMass << ',' << outerRemainingMass
                  << ',' << innerExtractedMass << ',' << outerExtractedMass
                  << ',' << innerRetainedLiquid << ',' << outerRetainedLiquid
                  << ',' << innerMeanConcentration
                  << ',' << outerMeanConcentration
                  << ',' << innerExtractionFraction
                  << ',' << outerExtractionFraction
                  << ',' << extractionMaldistribution
                  << ',' << maxRadialVelocity
                  << ',' << radialToAxialVelocityRatio
                  << ',' << puckFlow << ',' << outletVolumeFlow
                  << ',' << machineInnerFlow << ',' << innerOutletFlow
                  << ',' << machineOuterFlow << ',' << outerOutletFlow
                  << ',' << totalFluxRelativeDifference
                  << ',' << innerFluxRelativeDifference
                  << ',' << outerFluxRelativeDifference
                  << ',' << (radialTwoZone && saturatedAtStepStart ? 1 : 0)
                  << ',' << basketOperatingIterations
                  << ',' << basketOperatingResidual
                  << ',' << (basketOperatingBracketed ? 1 : 0)
                  << ',' << (basketOperatingConverged ? 1 : 0)
                  << ',' << bedMechanicsModel
                  << ',' << poroelasticCompactionModel
                  << ',' << stressFreePorosity
                  << ',' << (poroelasticCompaction
                                ? criticalCompactionPressure : 0.0)
                  << ',' << (poroelasticCompaction
                                ? criticalCompactionPressure/stressFreePorosity
                                : 0.0)
                  << ',' << (poroelasticCompaction
                                ? stressFreePermeability
                                : saturatedPermeability)
                  << ',' << (poroelasticCompaction && saturatedAtStepStart
                                ? 1 : 0)
                  << ',' << 0
                  << ',' << maximumEffectiveStress
                  << ',' << maximumNormalizedEffectiveStress
                  << ',' << minimumMechanicalPorosity
                  << ',' << outletMechanicalPorosity
                  << ',' << volumeWeightedMechanicalPorosity
                  << ',' << maximumCompactionStrain
                  << ',' << predictedBedHeightRatio
                  << ',' << predictedBedHeight
                  << ',' << mechanicalPoreVolumeChange
                  << ',' << minimumCompactionPermeability
                  << ',' << outletCompactionPermeability
                  << ',' << volumeWeightedPermeability
                  << ',' << minimumPermeabilityRatio
                  << ',' << poroelasticExactFlow
                  << ',' << poroelasticFlowClosureError
                  << ',' << poroelasticIterations
                  << ',' << poroelasticResidual
                  << ',' << (poroelasticConverged ? 1 : 0);
            if (effectivePermeabilityEnabled)
            {
                trace << ',' << (saturatedAtStepStart ? 1 : 0)
                      << ',' << sourceTimeS
                      << ',' << sourceStateTimeS
                      << ',' << sourceSupportStatus
                      << ',' << sourceDissolvedMassG
                      << ',' << sourcePhiT
                      << ',' << sourceStaticFlowGPerS
                      << ',' << sourceDynamicFlowGPerS
                      << ',' << effectiveMultiplierRaw
                      << ',' << effectiveMultiplier
                      << ',' << saturatedPermeability*effectiveMultiplier;
            }
            trace << '\n';
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
