import math
import unittest
from dataclasses import replace
from tools.reference.wp03b import moroney2017 as m
from tools.reference.wp03b.moroney2017_derivation import build_derivation


class TestMoroney(unittest.TestCase):
    def test_trajectory_refinement_and_endpoint_diagnostic(self):
        for p in (m.FINE,m.COARSE):
            traces=[m.solve(p,8,h) for h in (.002,.001,.0005)]
            d=m.trajectory_refinement(traces)
            self.assertGreater(d["D_01"],d["roundoff_floor"])
            self.assertGreater(d["D_12"],d["roundoff_floor"])
            self.assertLessEqual(d["refinement_ratio"],.35)
            self.assertLessEqual(abs(d["observed_order"]-4),.5)
            endpoint=[x[-1][1] for x in traces]
            self.assertLess(max(abs(endpoint[i+1]-endpoint[i]) for i in (0,1)),
                            d["roundoff_floor"])

    def test_roundoff_floor_and_alignment_rejection(self):
        t=[[(0,0,0,0),(1,1,1,1)]]*3
        with self.assertRaises(ValueError): m.trajectory_refinement(t)

    def test_reduced_agreement_and_all_level_conservation(self):
        for p in (m.FINE,m.COARSE):
            for h in (.002,.001,.0005):
                full=m.solve(p,2,h); reduced=m.solve_reduced(p,2,h)
                self.assertLess(max(max(abs(a[j]-b[j]) for j in range(1,4))
                                    for a,b in zip(full,reduced)),2e-12)
                for trace in (full,reduced):
                    base=m.inventory(trace[0][1:],p)
                    self.assertLess(max(abs(m.inventory(x[1:],p)-base) for x in trace),2e-11)

    def test_equilibrium_all_states(self):
        for p in (m.FINE,m.COARSE):
            eq=m.equilibrium(p)
            self.assertAlmostEqual(m.inventory(eq,p),m.inventory((0,p.gamma1,1),p))
            self.assertEqual(eq[2],0)

    def test_symbolic_derivation_and_composite_initial_state(self):
        self.assertEqual(build_derivation()["status"],"PASS")
        for p in (m.FINE,m.COARSE):
            got=m.governing_ode_consistent_second_order_composite(0,p)
            self.assertLess(max(abs(a-b) for a,b in zip(got,(0,p.gamma1,1))),1e-14)

    def test_composite_epsilon_convergence(self):
        for base in (m.FINE,m.COARSE):
            errors=[]
            for divisor in (1,2,4):
                p=replace(base,epsilon=base.epsilon/divisor)
                trace=m.solve(p,2,.00025)
                errors.append(max(max(abs(x[j+1]-
                    m.governing_ode_consistent_second_order_composite(x[0],p)[j])
                    for j in range(3)) for x in trace))
            self.assertLess(max(errors[i+1]/errors[i] for i in (0,1)),.35)

    def test_literal_and_derived_are_distinct(self):
        self.assertNotEqual(m.published_truncated_composite(.1,m.FINE),
                            m.governing_ode_consistent_second_order_composite(.1,m.FINE))

    def test_bad_inputs_and_no_clipping(self):
        with self.assertRaises(ValueError):m.derivative((-1,0,1),m.FINE)
        with self.assertRaises(ValueError):m.solve(m.FINE,-1,.1)

    def test_portable_ulp(self):
        self.assertEqual(m.portable_ulp(0.0), 2.0**-1074)
        self.assertEqual(m.portable_ulp(1.0), 2.0**-52)
        self.assertEqual(m.portable_ulp(-1.0), 2.0**-52)
        with self.assertRaises(ValueError): m.portable_ulp(float("inf"))
        if hasattr(math, "ulp"):
            for value in (0.0, 1e-300, .125, 1.0, 1.092624879):
                self.assertEqual(m.portable_ulp(value), math.ulp(value))

if __name__=="__main__":unittest.main()
