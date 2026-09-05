#include "IFstream.H"
#include "prescribedPressureBoundaryModel.H"
#include <iostream>
#include <iomanip>
int main(int argc, char** argv)
{
    if (argc!=2) return 2;
    Foam::IFstream input(argv[1]);
    Foam::dictionary dict(input);
    const auto p=Foam::readPrescribedPressureBoundary(dict,
        Foam::readScalar(dict.lookup("runStart")),Foam::readScalar(dict.lookup("runEnd")));
    std::cout << std::setprecision(17);
    std::cout << "kind,index,value\nmaximum,0," << p.maximumPressure() << '\n';
    const Foam::scalarList targets(dict.lookup("targets"));
    forAll(targets,i) std::cout << "target," << i << ',' << p.target(targets[i]) << '\n';
    const Foam::List<Foam::scalarList> integrals(dict.lookup("integrals"));
    forAll(integrals,i) std::cout << "integral," << i << ',' << p.positiveDrivingIntegral(integrals[i][0],integrals[i][1],integrals[i][2]) << '\n';
    const Foam::List<Foam::scalarList> crossings(dict.lookup("crossings"));
    forAll(crossings,i) std::cout << "crossing," << i << ',' << p.crossingTime(crossings[i][0],crossings[i][1],crossings[i][2],crossings[i][3]) << '\n';
    return 0;
}
