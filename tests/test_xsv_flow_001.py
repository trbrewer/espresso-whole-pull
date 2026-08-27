import copy, importlib.util, json, math, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prepare_case",ROOT/"scripts/prepare_case.py")
PREPARE=importlib.util.module_from_spec(spec); spec.loader.exec_module(PREPARE)
from tools.sci_md_004_stage_c.runner import Matrix
from tools.xsv_flow_001.reference import (discrete_volume, layered_pressure_drop,
    schedule_value, uniform_pressure_drop)
from tools.xsv_flow_001.runner import CASE_IDS, canonical

class XsvFlow001Tests(unittest.TestCase):
    def setUp(self):
        self.scenario=Matrix(Path("/bin/true"),Path("/tmp/unused-xsv-flow")).compact(end=6,dt=.02,axial=32,radial=1)
        self.scenario["wetting"]["initial_wet_front_m"]=self.scenario["coffee_bed"]["bed_depth_m"]
        self.scenario["hydraulics"]["pressure_ramp_time_s"]=0
        self.scenario["pressureBoundaryModel"]="prescribedFlow"
        self.scenario["prescribedFlowBoundary"]={"scheduleType":"constant","volumetricFlowRateM3PerS":1e-6,"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}

    def test_constant_rendering_and_zero(self):
        text=PREPARE.render_properties(self.scenario)
        self.assertIn("pressureBoundaryModel      prescribedFlow;",text)
        self.assertIn("volumetricFlowRateM3PerS 1e-06;",text)
        zero=copy.deepcopy(self.scenario); zero["prescribedFlowBoundary"]["volumetricFlowRateM3PerS"]=0
        self.assertIn("volumetricFlowRateM3PerS 0;",PREPARE.render_properties(zero))

    def test_piecewise_rendering_and_oracle(self):
        b={"scheduleType":"piecewiseLinear","timesS":[0,1,3,5,6],"volumetricFlowRatesM3PerS":[0,.5,1.25,1.25,0],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}
        self.scenario["prescribedFlowBoundary"]=b; text=PREPARE.render_properties(self.scenario)
        self.assertIn("timesS (0 1 3 5 6);",text)
        self.assertEqual(schedule_value(b["timesS"],b["volumetricFlowRatesM3PerS"],0),0)
        self.assertEqual(schedule_value(b["timesS"],b["volumetricFlowRatesM3PerS"],1),.5)
        self.assertEqual(schedule_value(b["timesS"],b["volumetricFlowRatesM3PerS"],2),.875)
        self.assertEqual(schedule_value(b["timesS"],b["volumetricFlowRatesM3PerS"],6),0)

    def test_malformed_schedules(self):
        bad=[{}, {"scheduleType":"other","absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8},
          {"scheduleType":"constant","volumetricFlowRateM3PerS":-1,"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8},
          {"scheduleType":"piecewiseLinear","timesS":[0,0],"volumetricFlowRatesM3PerS":[0,1],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8},
          {"scheduleType":"piecewiseLinear","timesS":[0,1],"volumetricFlowRatesM3PerS":[0],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8},
          {"scheduleType":"piecewiseLinear","timesS":[0],"volumetricFlowRatesM3PerS":[0],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8},
          {"scheduleType":"piecewiseLinear","timesS":[0,5],"volumetricFlowRatesM3PerS":[0,1],"absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}]
        for boundary in bad:
            scenario=copy.deepcopy(self.scenario); scenario["prescribedFlowBoundary"]=boundary
            with self.subTest(boundary=boundary), self.assertRaises(SystemExit): PREPARE.render_properties(scenario)

    def test_prohibited_combinations(self):
        mutations=[lambda s:s["wetting"].update(initial_wet_front_m=0),lambda s:s.update(flowResistanceModel="darcyForchheimer"),lambda s:s.update(bedMechanicsModel="waszkiewiczQuasiStaticCompaction"),lambda s:s.update(effective_permeability_evolution={}),lambda s:s.update(machineBoundary={}),lambda s:s["hydraulics"].update(permeability_profile={"type":"radial_two_zone"}),lambda s:s["hydraulics"].update(pressure_ramp_time_s=1)]
        for mutate in mutations:
            scenario=copy.deepcopy(self.scenario); mutate(scenario)
            with self.assertRaises(SystemExit): PREPARE.render_properties(scenario)

    def test_default_rendering_unchanged_by_omission(self):
        scenario=copy.deepcopy(self.scenario); scenario.pop("pressureBoundaryModel"); scenario.pop("prescribedFlowBoundary")
        text=PREPARE.render_properties(scenario)
        self.assertIn("pressureBoundaryModel      prescribedPressure;\nflowResistanceModel darcy;",text)
        self.assertNotIn("prescribedFlowBoundary",text)

    def test_oracles_and_serialization(self):
        self.assertAlmostEqual(uniform_pressure_drop(2,3,5,7,11),30/77)
        self.assertAlmostEqual(layered_pressure_drop(2,5,7,(1,2),(10,20)),2/7)
        self.assertEqual(discrete_volume([1,2],[1,1],lambda t:t),3)
        value={"b":1,"a":2}; self.assertEqual(canonical(value),'{"a":2,"b":1}\n')
        self.assertEqual(len(CASE_IDS),11)

    def test_cpp_contract_tokens_and_matrix_flux(self):
        source=(ROOT/"solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()
        header=(ROOT/"solver/espressoWholePullFoam/prescribedFlowBoundaryModel.H").read_text()
        self.assertIn("-referenceEquation.flux()",source)
        self.assertIn("darcyFlux = -pressureEquation.flux();",source)
        for token in ("XSV_FLOW_001_FLOW_GATE_FAIL","XSV_FLOW_001_INLET_OUTLET_CLOSURE_FAIL","XSV_FLOW_001_REVERSE_FLOW_FAIL","XSV_FLOW_001_INVALID_SCHEDULE"):
            self.assertIn(token,source+header)

if __name__=="__main__": unittest.main()
