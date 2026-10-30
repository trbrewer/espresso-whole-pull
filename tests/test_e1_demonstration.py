"""Demonstration protocol arithmetic; no native runs or fitted models in CI."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import e1_demonstration as D
from prepare_case import pressure_history_contract, render_properties


class DemonstrationTests(unittest.TestCase):
    def setUp(self):
        self.params=dict(aGPerSBar=3.,pstarBar=7.,tauS=10.,mcG=29.,onsetCS=16.,onsetN=.05)
        self.early={p:p for p in D.V.NOMINAL}

    def test_sweep_and_single_extension_do_not_duplicate_nominal_runs(self):
        p=D.initial_pressures()
        self.assertEqual(len(p),20)
        self.assertTrue(set(D.V.NOMINAL).issubset(p))
        self.assertEqual(D.extension_pressures({x:-(x-6.25)**2 for x in p}),[])
        self.assertEqual(D.extension_pressures({x:x for x in p}),[8.25,8.5,8.75])
        self.assertEqual(D.extension_pressures({x:-x for x in p}),[4.25,4.5,4.75])

    def test_r0_geometry_and_physics_unchanged(self):
        original=json.loads((ROOT/"config/reference_R0.json").read_text())
        cfg=D.case_config(self.params,self.early,6.)
        for field in ("geometry","coffee_bed","liquid","wetting","extraction","verification"):
            self.assertEqual(cfg[field],original[field])
        self.assertEqual(cfg["hydraulics"]["pressure_ramp_time_s"],0.)
        self.assertEqual(cfg["time"]["delta_t_s"],.0025)
        self.assertEqual(cfg["time"]["end_s"],100.)
        for key,value in self.params.items():
            self.assertEqual(cfg["e1_whole_bed_closure"][key],value)
        render_properties(cfg)

    def test_history_keeps_pressure_clock_and_has_no_observed_onset(self):
        cfg=D.case_config(self.params,self.early,6.,([0.,10.,100.],[4.,6.,5.]),5.8)
        history=pressure_history_contract(cfg)
        self.assertEqual(history["times_s"],[0.,10.,100.])
        self.assertEqual(history["pressures_gauge_Pa"],[400000.,600000.,500000.])
        self.assertEqual(cfg["e1_whole_bed_closure"]["earlyPressureBar"],5.8)
        self.assertEqual(set(cfg["e1_whole_bed_closure"]),set(self.params)|{"enabled","earlyPressureBar"})
        render_properties(cfg)

    def test_delay_holds_mass_until_start_without_shifting_pressure_history(self):
        absolute,forcing=D.delayed_grid([0.,25.,50.,75.,100.],[1.,2.,3.,4.,5.],30.)
        self.assertEqual(absolute.tolist(),[30.,50.,75.,100.])
        self.assertAlmostEqual(forcing[0],2.2,places=12)
        calls=[]
        def evaluator(model,free,pressure,t,delay,mc):
            calls.append((model,free,pressure,t,delay,mc))
            return D.np.array([1.+t/100.]),None
        q=D.python_e1(self.params,[0.,25.,50.,75.,100.],[1.,2.,3.,4.,5.],6.,30.,evaluator)
        self.assertEqual(q[:2].tolist(),[0.,0.])
        self.assertAlmostEqual(q[-1],1.7,places=12)
        self.assertAlmostEqual(calls[0][2][0,0],2.2,places=12)
        self.assertEqual(calls[0][3].tolist(),[0.,20.,45.,70.])
        self.assertEqual(calls[0][1],[3.,7.,10.])
        self.assertEqual(calls[0][-1],29.)

    def test_continuous_peak_is_bracketed_quadratic_only(self):
        p=D.np.arange(5.,8.01,.25)
        self.assertAlmostEqual(D.quadratic_peak(p,4.-(p-6.13)**2),6.13,places=11)
        self.assertIsNone(D.quadratic_peak(p,p))

    def test_capability_bands_and_negative_slope_guard(self):
        self.assertEqual(D.grades(.2,.3,[-.1,.1],[8.,8.],[-.1,-.06]),("TIE","MEETS","NEAR","MEETS"))
        self.assertEqual(D.grades(.2,.3,[-.3,.1],[5.,6.],[-.03,-.025]),("UNRESOLVED","NEAR","MEETS","NEAR"))
        self.assertEqual(D.grades(.4,.3,[.01,.2],[9.,11.],[-.08,.001]),("WORSE","MISSES","MISSES","MISSES"))
        self.assertEqual(D.comparison([-.2,-.01]),"BETTER")
        self.assertEqual(D.comparison([-.25,.25]),"TIE")

    def test_paired_whole_brew_draws_keep_identical_models_identical(self):
        squared=D.np.array([[1.,4.,9.,16.],[1.,4.,9.,16.]])
        draws=D.paired_rmse_draws(squared,[[0],[1,2,3]])
        self.assertEqual(draws.shape,(1000,2))
        self.assertTrue(D.np.array_equal(draws[:,0],draws[:,1]))
        self.assertTrue(D.np.array_equal(draws,D.paired_rmse_draws(squared,[[0],[1,2,3]])))

    def test_constant_forcing_has_zero_width_response_intervals(self):
        p=D.np.repeat(D.np.array(D.V.NOMINAL),3)
        q=2.-.1*(p-6.)**2
        result=D.response_draws(q,p,p)
        self.assertEqual(result["peak_interval"],[6.,6.])
        self.assertAlmostEqual(result["slope_interval"][0],result["slope_interval"][1],places=14)
        for low,high in result["intervals"]:
            self.assertAlmostEqual(low,high,places=14)


if __name__ == "__main__":
    unittest.main()
