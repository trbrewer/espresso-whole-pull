# EWP closure equivalence

The unchanged production authority is `solver/espressoWholePullFoam/poroelasticCompaction.H` (SHA-256 `4a673a52e9d690ac22b3ecc21b8cf2c9b7e32168bd62863465c7e53b9515b0b6`). It defines `poroelasticIntegral`, `poroelasticUniversalIntegral`, `poroelasticUniversalQhat`, `poroelasticPermeabilityRatio`, and both overloads of `poroelasticPuckFlow`. The separate `poroelasticSaturatedPuckState` is in `machineBoundaryModel.H` (SHA-256 `20d8e48ee6c4f9ffe6c61b40604760be65fc3ff4225f33f2cac5a61437baf719`). `waszkiewicz2025FinitePhi`, `stressFreePorosity`, `criticalCompactionPressure`, and `stressFreePermeability` are configured/consumed in `espressoWholePullFoam.C` (SHA-256 `99c8fe756a57410eff65e302784247346d2d2b0d61d6f9db401033b73996b6e6`).

The mapping is production normalized stress `X = sigma/criticalPressure` ↔ `p_basket/Pc`; `stressFreePorosity` ↔ fixed `Phi`; `criticalCompactionPressure` ↔ `Pc`; and the production mobility/geometry normalization ↔ fitted observable `Qc`.

Production evaluates

`J(x,Phi)=integral_0^x (1-s)^3/(1-Phi*s) ds`.

At `Phi -> 0`, `4 J(x,0) = x(4-6x+4x^2-x^3)` and `J(1,0)=1/4`, proving the registered universal normalized curve. Both normalized shapes equal zero at `x=0`, equal one at `x=1`, and have derivative proportional to `(1-x)^3/(1-Phi*x)`: they are nondecreasing on `0<=x<=1`, with zero derivative at the critical boundary. They can flatten/saturate but cannot represent genuine within-fit high-pressure turnover.

The production flow is volumetric: `Qv_c=A*k0*Pc_Pa*J(1,Phi)/(mu*h)`. With `Pc_Pa=1e5*Pc_bar`, observable mass flow is `Qc_g_s=1000*rho_kg_m3*A*k0*(1e5*Pc_bar)*J(1,Phi)/(mu*h)`. This agrees with EWP SI pressure, area, depth, permeability, viscosity, and volumetric-flow conventions. SCI-MD-011 fits only effective `Qc` and `Pc`; it does not separately identify `k0`, `rho`, `A`, `h`, `mu`, `Y`, `Phi`, or physical wet permeability. No fitted value becomes a production input.

The closure equation is production-equivalent. The quadratic line-to-basket adapter is solely the accepted SCI-MD-010 evaluation authority. The live EWP poroelastic machine helper instead uses a separate linear upstream resistance. Full production machine-boundary equivalence is not claimed.

The task-local oracle is `tests/fixtures/sci_md_011_closure_oracle/sci_md_011_closure_oracle.C`, following the existing WP03-001 OpenFOAM fixture pattern and compiled through `scripts/run_sci_md_011_closure_oracle.sh` against the unchanged production header. SCI-MD-011 freezes absolute and relative parity tolerances of `1e-12` and checks `x=0`, interior points, near one, normalization at one, exact source Phi, and two additional valid Phi values. `x=1` is otherwise normalization/oracle-only; prediction requires `0<=x<1`.

For the machine-coupled equation, `H(pb)=pb+D(Qc*f(pb/Pc))-p_line` is strictly increasing because both the closure and quadratic adapter are nondecreasing (the adapter is strictly increasing for nonnegative flow). Hence at most one admissible root exists. The bracket, failure retention, and tolerances are frozen in `EVALUATION_CONTRACT.json`; observed flow never enters the adapter.
