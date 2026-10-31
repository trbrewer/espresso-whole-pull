"""Demonstration protocol arithmetic; no native runs or fitted models in CI."""
import json
import math
from pathlib import Path
import sys
import struct
import tempfile
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

    def test_trace_masks_are_separate_and_cannot_change_endpoint_grades(self):
        rows=[];traces=[];pressure=[]
        for p in D.V.NOMINAL:
            for _ in range(2):
                rows.append(dict(nominal_pressure_bar=p,observed_endpoint_g_s=1.,b1_endpoint_g_s=1.2,
                    trace_times_s=[0.,5.,10.,20.,50.,100.],trace_mask=[False,False,False,True,True,True],
                    observed_trace_g_s=[0.,0.,0.,1.,1.,1.],b1_trace_g_s=[10.,10.,10.,1.2,1.2,1.2]))
                traces.append([0.,0.,0.,1.1,1.1,1.1]);pressure.append(p)
        first=D.score_predictions(rows,[1.1]*len(rows),traces,pressure)
        self.assertAlmostEqual(first["trace_rmse_g_s"],.1,places=12)
        self.assertAlmostEqual(first["b1_trace_rmse_g_s"],.2,places=12)
        self.assertAlmostEqual(first["startup_inclusive_trace_rmse_g_s"],math.sqrt(.03/5),places=12)
        self.assertAlmostEqual(first["b1_startup_inclusive_trace_rmse_g_s"],math.sqrt(200.12/5),places=12)
        for row in rows:row["trace_mask"]=[False,True,True,True,True,True]
        second=D.score_predictions(rows,[1.1]*len(rows),traces,pressure)
        self.assertAlmostEqual(first["endpoint_rmse_g_s"],second["endpoint_rmse_g_s"],places=12)
        self.assertEqual(first["accuracy_grade"],second["accuracy_grade"])
        self.assertEqual(first["peak_grade"],second["peak_grade"])
        self.assertEqual(first["slope_grade"],second["slope_grade"])

    def test_first_drip_clocks_do_not_subtract_stable_offset_twice(self):
        row=D.onset_clocks("sample",6.,8.,12.,15.)
        self.assertEqual(row["solver_first_drip_source_elapsed_s"],20.)
        self.assertEqual(row["observed_onset_source_elapsed_s"],23.)
        self.assertEqual(row["solver_first_drip_stable_s"],12.)
        self.assertEqual(row["solver_minus_observed_s"],-3.)
        rows=[row,D.onset_clocks("other",6.,2.,10.,11.),D.onset_clocks("third",6.,4.,30.,22.)]
        summary=D.summarize_first_drip(rows)[0]
        self.assertEqual((summary["solver_median_s"],summary["solver_min_s"],summary["solver_max_s"]),(12.,10.,30.))
        self.assertEqual((summary["difference_median_s"],summary["difference_min_s"],summary["difference_max_s"]),(-1.,-3.,8.))

    def test_sanity_uses_only_numerical_limits(self):
        cfg=D.case_config(self.params,self.early,6.)
        c=dict(outlet_flow_m3_s=D.np.array([0.,10/965000,10/965000]),
            cup_water_mass_kg=D.np.array([0.,.001,.002]),inlet_pressure_Pa=D.np.full(3,6e5),
            min_saturation=D.np.ones(3),cumulative_inlet_water_mass_kg=D.np.full(3,.01),
            liquid_balance_residual_kg=D.np.zeros(3),solute_balance_residual_kg=D.np.zeros(3),
            first_drip_s=D.np.array([-1.,35.,35.]))
        keys=("finite_values","nonnegative_outlet_flow","positive_e1_multiplier","liquid_balance","solute_balance")
        self.assertTrue(all(D.numerical_values(c,cfg)[k] for k in keys))
        for column,value,key in (("outlet_flow_m3_s",-1e-9,"nonnegative_outlet_flow"),
                                 ("cup_water_mass_kg",float("nan"),"finite_values"),
                                 ("inlet_pressure_Pa",1e20,"positive_e1_multiplier"),
                                 ("liquid_balance_residual_kg",2e-9,"liquid_balance"),
                                 ("solute_balance_residual_kg",2e-10,"solute_balance")):
            bad={k:v.copy() for k,v in c.items()};bad[column][-1]=value
            self.assertFalse(D.numerical_values(bad,cfg)[key])

    def test_binary_field_checks_decode_values_before_searching_for_nan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);folder=root/"processor0/100";folder.mkdir(parents=True)
            field=folder/"permeability"
            finite_bytes=b"nan\x00\x00\x00\xf0?"
            self.assertTrue(math.isfinite(struct.unpack("<d",finite_bytes)[0]))
            field.write_bytes(b"internalField nonuniform List<scalar>\n1\n("+finite_bytes+b");")
            (folder/"e1WholeBedMultiplier").write_text("internalField uniform 0.2;")
            self.assertTrue(D.final_field_sanity(root)["finite_values"])
            field.write_bytes(b"internalField nonuniform List<scalar>\n1\n("+struct.pack("<d",float("nan"))+b");")
            self.assertFalse(D.final_field_sanity(root)["finite_values"])


if __name__ == "__main__":
    unittest.main()
