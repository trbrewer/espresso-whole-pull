import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from prepare_case import render_properties, render_e1
from e1_verification import early_input, balance_bounds, observed_order, refinement_table, PRIMARY
from puckworks_historical_lock import historical_lock, OLD_COMMIT, OLD_TREE, RUNTIME_COMMIT, RUNTIME_TREE


class E1Tests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads((ROOT/"config/reference_R0.json").read_text())
        self.e=dict(enabled=True,aGPerSBar=3.,pstarBar=7.,tauS=10.,mcG=29.,
                    onsetCS=16.,onsetN=.05,earlyPressureBar=9.)

    def test_off_mode_dictionary_is_byte_identical(self):
        old=render_properties(self.cfg)
        self.cfg["e1_whole_bed_closure"]={"enabled":False}
        self.assertEqual(old,render_properties(self.cfg))
        self.assertNotIn("e1WholeBedClosure",old)

    def test_onset_is_predictive_and_fields_are_exact(self):
        self.cfg["e1_whole_bed_closure"]=self.e
        self.assertIn("earlyPressureBar 9;",render_e1(self.cfg))
        self.e["observedOnsetS"]=5.
        with self.assertRaisesRegex(ValueError,"no measured onset"):render_e1(self.cfg)

    def test_invalid_parameters_and_conflicting_closures(self):
        self.cfg["e1_whole_bed_closure"]=self.e
        for key in ("aGPerSBar","mcG","earlyPressureBar"):
            for value in (0.,-1.,math.nan,math.inf):
                cfg=copy.deepcopy(self.cfg);cfg["e1_whole_bed_closure"][key]=value
                with self.assertRaises(ValueError):render_e1(cfg)
        for key,value in (("bedMechanicsModel","waszkiewiczQuasiStaticCompaction"),
                          ("flowResistanceModel","darcyForchheimer"),
                          ("pressureBoundaryModel","prescribedFlow"),
                          ("effective_permeability_evolution",{})):
            cfg=copy.deepcopy(self.cfg);cfg[key]=value
            with self.assertRaises(ValueError):render_e1(cfg)

    def test_early_input_uses_training_pressure_only(self):
        self.assertEqual(early_input(6.,{1.:1.,2.:2.,3.5:3.5,4.:4.,5.:5.,6.:6.,7.:7.,8.:8.,9.:9.,11.:11.,13.:13.}),6.)

    def test_convergence_order_requires_same_signed_differences(self):
        self.assertAlmostEqual(observed_order(1.04,1.02,1.01),1.,places=12)
        self.assertAlmostEqual(observed_order(1.16,1.04,1.01),2.,places=12)
        self.assertEqual(observed_order(1.,1.,1.),"NOT_AVAILABLE")
        self.assertEqual(observed_order(1.,2.,1.),"NOT_AVAILABLE")

    def test_refinement_bands_unchanged_and_diagnostic_ungraded(self):
        names=("coarse","middle","fine")
        rows={n:dict.fromkeys(PRIMARY,1.)|{"first_drip_s":4.} for n in names}
        rows["coarse"]["cup_water_mass_kg"]=1.006
        rows["middle"]["cup_water_mass_kg"]=1.003
        table=refinement_table(rows,names)
        failed=[r for r in table if r["status"]=="FAIL"]
        self.assertEqual([r["tolerance"] for r in failed],[.005,.0025])
        self.assertTrue(all(r["status"]=="DESCRIPTIVE" for r in refinement_table(rows,names,False,False)))
        first=[r for r in refinement_table(rows,names,True,False) if r["metric"]=="first_drip_s"]
        self.assertEqual([r["tolerance"] for r in first],[1e-8,1e-8])

    def test_runtime_and_historical_authorities_are_distinct(self):
        lock=json.loads((ROOT/"dependencies/puckworks.lock.json").read_text())
        self.assertEqual((lock["checkout_commit"],lock["checkout_tree_sha"]),(RUNTIME_COMMIT,RUNTIME_TREE))
        old=historical_lock(lock)
        self.assertEqual((old["checkout_commit"],old["checkout_tree_sha"]),(OLD_COMMIT,OLD_TREE))
        bad=copy.deepcopy(lock);bad["historical_runtime_identity"]["checkout_commit"]="0"*40
        with self.assertRaises(ValueError):historical_lock(bad)
        self.assertEqual(lock["checkout_commit"],RUNTIME_COMMIT)

    def test_cpp_terms_and_mass_feedback(self):
        # Compile the production header, independent of OpenFOAM and its runtime.
        source='''#include "e1EffectivePermeability.H"
#include <iostream>
#include <iomanip>
int main() { espresso::E1Parameters e{3,7,10,29,16,.05,9}; e.validate();
std::cout << std::setprecision(17) << e.delay() << " " << e.swelling() << " "
<< e.multiplier(9e5,0) << " " << e.multiplier(9e5,100) << " "
<< e.multiplier(-1,0) << " " << e.basePermeability(.000315,.01,965,.0026);
try { e.multiplier(9e5,-1); return 3; } catch(const std::invalid_argument&) {}
}'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/"terms.C").write_text(source)
            subprocess.run(["g++","-std=c++14","-I",str(ROOT/"solver/espressoWholePullFoam"),
                            str(p/"terms.C"),"-o",str(p/"terms")],check=True,capture_output=True)
            actual=list(map(float,subprocess.check_output([str(p/"terms")],text=True).split()))
        delay=16*9**(-.05);swelling=math.exp(-delay/10)
        expected=[delay,swelling,swelling*math.exp(-9/7)/math.e,
                  swelling*math.exp(-9/7)/math.exp(math.exp(-100/29)),swelling/math.e,
                  3e-3*.000315*.01/(965*.0026*1e5)]
        for a,b in zip(actual,expected):self.assertTrue(math.isclose(a,b,rel_tol=1e-12))
        self.assertGreater(actual[3],actual[2])


if __name__=="__main__":unittest.main()
