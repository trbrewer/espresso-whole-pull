#include "poroelasticCompaction.H"
#include <iomanip>
#include <iostream>
int main(){
 const Foam::scalar phis[]={2.257390325360356/18.5,0.1,0.4};
 const Foam::scalar xs[]={0.0,0.1,0.25,0.5,0.9,0.999999,1.0};
 std::cout<<std::setprecision(17);
 for(const auto phi:phis)for(const auto x:xs)
  std::cout<<phi<<','<<x<<','<<Foam::poroelasticIntegral(x,phi)/Foam::poroelasticIntegral(1.0,phi)<<','<<Foam::poroelasticUniversalQhat(x)<<'\n';
}
