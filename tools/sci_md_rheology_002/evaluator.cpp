#include "../../solver/espressoWholePullFoam/aggregateViscosity.H"
#include <iostream>
#include <iomanip>
int main(int argc,char** argv) {
    try {
        if(argc!=2) return 2;
        espresso::AggregateViscosity table(argv[1]);
        double c;
        std::cout << std::setprecision(17);
        while(std::cin >> c) std::cout << table.value(table.fraction(c)) << '\n';
        return std::cin.eof()?0:2;
    } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
