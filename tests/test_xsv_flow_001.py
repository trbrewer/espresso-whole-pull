import copy, importlib.util, json, math, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prepare_case",ROOT/"scripts/prepare_case.py")
PREPARE=importlib.util.module_from_spec(spec); spec.loader.exec_module(PREPARE)
from tools.sci_md_004_stage_c.runner import Matrix
from tools.xsv_flow_001.reference import (discrete_volume, layered_pressure_drop,
    schedule_value, uniform_pressure_drop)
from tools.xsv_flow_001.runner import (CASE_IDS, analyze, canonical,
    compare_default_pair, serial_two_rank_comparison, timestep_comparison)

def diagnostic_row(time, target=1e-6, pressure=200000.0, conductance=1e-11):
    return {"time_s":str(time),"target_outlet_flow_m3_s":str(target),
      "achieved_signed_outlet_flow_m3_s":str(target),"achieved_positive_outlet_flow_m3_s":str(target),
      "achieved_signed_inlet_flow_m3_s":str(target),"required_inlet_pressure_Pa":str(pressure),
      "outlet_pressure_Pa":"100000","discrete_conductance_m3_s_Pa":str(conductance),
      "absolute_flow_error_m3_s":"0","flow_error_limit_m3_s":"1.01e-12","flow_error_ratio":"0",
      "inlet_outlet_closure_error_m3_s":"0","closure_error_limit_m3_s":"2.1e-12",
      "outlet_reverse_flow_m3_s":"0","inlet_reverse_flow_m3_s":"0",
      "flow_gate_pass":"1","closure_gate_pass":"1","direction_gate_pass":"1"}

def constant_scenario(target=1e-6):
    return {"prescribedFlowBoundary":{"scheduleType":"constant","volumetricFlowRateM3PerS":target,
      "absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}}

def piecewise_scenario():
    return {"prescribedFlowBoundary":{"scheduleType":"piecewiseLinear","timesS":[0,1,3,5,6],
      "volumetricFlowRatesM3PerS":[0,5e-7,1.25e-6,1.25e-6,0],
      "absoluteFlowToleranceM3PerS":1e-12,"relativeFlowTolerance":1e-8}}

def schedule_rows(step):
    scenario=piecewise_scenario(); boundary=scenario["prescribedFlowBoundary"]
    result=[]
    for index in range(1,round(6/step)+1):
        time=round(index*step,12); target=schedule_value(boundary["timesS"],boundary["volumetricFlowRatesM3PerS"],time)
        result.append(diagnostic_row(time,target,100000+target/1e-11))
    return result

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

    def test_timestep_comparator_valid_nested_fixture(self):
        data={"FLOW_UPL_DT040":schedule_rows(.04),"FLOW_UPL_DT020":schedule_rows(.02),"FLOW_UPL_DT010":schedule_rows(.01)}
        scenarios={key:piecewise_scenario() for key in data}
        result=timestep_comparison(data,scenarios)
        self.assertEqual(result["status"],"PASS"); self.assertEqual([pair["matched_common_time_count"] for pair in result["pairs"]],[150,150,300])

    def test_timestep_comparator_pressure_failure(self):
        data={"FLOW_UPL_DT040":schedule_rows(.04),"FLOW_UPL_DT020":schedule_rows(.02),"FLOW_UPL_DT010":schedule_rows(.01)}
        data["FLOW_UPL_DT020"][49]["required_inlet_pressure_Pa"]="200001"
        self.assertEqual(timestep_comparison(data,{key:piecewise_scenario() for key in data})["status"],"FAIL")

    def test_timestep_comparator_missing_common_time(self):
        data={"FLOW_UPL_DT040":schedule_rows(.04),"FLOW_UPL_DT020":schedule_rows(.02),"FLOW_UPL_DT010":schedule_rows(.01)}; data["FLOW_UPL_DT020"].pop(1)
        self.assertEqual(timestep_comparison(data,{key:piecewise_scenario() for key in data})["status"],"FAIL")

    def test_timestep_comparator_shifted_and_duplicate_time(self):
        for mutation in ("shift","duplicate"):
            data={"FLOW_UPL_DT040":schedule_rows(.04),"FLOW_UPL_DT020":schedule_rows(.02),"FLOW_UPL_DT010":schedule_rows(.01)}
            data["FLOW_UPL_DT020"][1]["time_s"]="0.080000000002" if mutation=="shift" else data["FLOW_UPL_DT020"][0]["time_s"]
            with self.subTest(mutation=mutation): self.assertEqual(timestep_comparison(data,{key:piecewise_scenario() for key in data})["status"],"FAIL")

    def test_timestep_comparator_required_knot_absent(self):
        data={"FLOW_UPL_DT040":schedule_rows(.04),"FLOW_UPL_DT020":schedule_rows(.02),"FLOW_UPL_DT010":schedule_rows(.01)}
        data["FLOW_UPL_DT010"][99]["time_s"]="1.000000000002"
        self.assertEqual(timestep_comparison(data,{key:piecewise_scenario() for key in data})["status"],"FAIL")

    def test_mpi_comparator_valid_fixture(self):
        data=schedule_rows(.02); self.assertEqual(serial_two_rank_comparison(data,copy.deepcopy(data))["status"],"PASS")

    def test_mpi_comparator_time_misalignment(self):
        serial=schedule_rows(.02); mpi=copy.deepcopy(serial); mpi[10]["time_s"]="0.220000000002"
        self.assertEqual(serial_two_rank_comparison(serial,mpi)["status"],"FAIL")

    def test_mpi_comparator_pressure_failure(self):
        serial=schedule_rows(.02); mpi=copy.deepcopy(serial); mpi[10]["required_inlet_pressure_Pa"]="300000"
        self.assertEqual(serial_two_rank_comparison(serial,mpi)["status"],"FAIL")

    def test_mpi_comparator_conductance_failure(self):
        serial=schedule_rows(.02); mpi=copy.deepcopy(serial); mpi[10]["discrete_conductance_m3_s_Pa"]="2e-11"
        self.assertEqual(serial_two_rank_comparison(serial,mpi)["status"],"FAIL")

    def test_mpi_comparator_cumulative_volume_failure(self):
        serial=schedule_rows(.02); mpi=copy.deepcopy(serial)
        for row in mpi: row["achieved_signed_outlet_flow_m3_s"]=str(float(row["achieved_signed_outlet_flow_m3_s"])+1e-9)
        self.assertEqual(serial_two_rank_comparison(serial,mpi)["status"],"FAIL")

    def write_diagnostic(self, root, data):
        path=root/"postProcessing/prescribedFlow/0"; path.mkdir(parents=True)
        import csv
        with (path/"prescribed_flow.csv").open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=data[0]); writer.writeheader(); writer.writerows(data)

    def analysis_scenario(self):
        scenario=copy.deepcopy(self.scenario); scenario["geometry"]={"basket_radius_m":.03}
        return scenario

    def test_per_row_reducer_gate_and_limit_failures(self):
        for field,value in (("flow_gate_pass","0"),("absolute_flow_error_m3_s","2e-12")):
            with tempfile.TemporaryDirectory() as directory:
                data=[diagnostic_row(.02)]; data[0][field]=value; self.write_diagnostic(Path(directory),data)
                with self.subTest(field=field): self.assertEqual(analyze(Path(directory),self.analysis_scenario())["status"],"FAIL")

    def test_per_row_reducer_rejects_bad_numeric_and_time(self):
        fixtures=[]
        for value in ("nan","inf"): data=[diagnostic_row(.02)]; data[0]["absolute_flow_error_m3_s"]=value; fixtures.append(data)
        duplicate=[diagnostic_row(.02),diagnostic_row(.02)]; fixtures.append(duplicate)
        nonmonotone=[diagnostic_row(.04),diagnostic_row(.02)]; fixtures.append(nonmonotone)
        for index,data in enumerate(fixtures):
            with tempfile.TemporaryDirectory() as directory:
                self.write_diagnostic(Path(directory),data)
                with self.subTest(index=index): self.assertEqual(analyze(Path(directory),self.analysis_scenario())["status"],"FAIL")

    def test_default_comparison_detects_input_difference(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)/"base"; candidate=Path(directory)/"candidate"
            for root,value in ((base,"a"),(candidate,"b")):
                (root/"constant").mkdir(parents=True); (root/"constant/espressoModelProperties").write_text(value)
            self.assertEqual(compare_default_pair(base,candidate)["status"],"FAIL")

    def test_default_comparison_detects_output_difference_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)/"base"; candidate=Path(directory)/"candidate"
            for root in (base,candidate):
                (root/"constant").mkdir(parents=True); (root/"constant/espressoModelProperties").write_text("same")
                (root/"postProcessing/wholePull/0").mkdir(parents=True); (root/"postProcessing/wholePull/0/traces.csv").write_text("same")
            (candidate/"postProcessing/wholePull/0/traces.csv").write_text("changed")
            self.assertEqual(compare_default_pair(base,candidate)["status"],"FAIL")
            (candidate/"postProcessing/wholePull/0/traces.csv").write_text("same"); (candidate/"postProcessing/extra").mkdir(); (candidate/"postProcessing/extra/value").write_text("x")
            self.assertEqual(compare_default_pair(base,candidate)["status"],"FAIL")

if __name__=="__main__": unittest.main()
