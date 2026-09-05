"""Production evidence tests plus independent mathematical and contract tests."""
import copy, hashlib, json, math, subprocess, unittest
from pathlib import Path
from unittest.mock import patch
from scripts.xsv_pressure_001_reference import Schedule
from scripts.prepare_case import pressure_history_contract, render_properties
from scripts import validate_xsv_pressure_001 as validator
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'validation/xsv_pressure_001'
def load(name):return json.loads((OUT/name).read_text())
def scenario():
    s=json.loads((ROOT/'config/reference_R0.json').read_text());h=s['hydraulics']
    h.pop('target_inlet_pressure_gauge_Pa');h.pop('pressure_ramp_time_s')
    h['pressure_boundary_model']='prescribedPressureHistory'
    h['prescribed_pressure_boundary']={'schedule_type':'piecewiseLinear','times_s':[0,5,30],'pressures_gauge_Pa':[0,900000,0]}
    return s
class PressureHistory(unittest.TestCase):
    def test_exact_modes(self):
        for mode in ('prescribedPressure','prescribedPressureHistory','prescribedFlow','lumpedMachineCompliance'):
            self.assertIn('"'+mode+'"',(ROOT/'solver/espressoWholePullFoam/espressoWholePullFoam.C').read_text())
        s=scenario();s['hydraulics']['pressure_boundary_model']='cubicPressure'
        with self.assertRaises(SystemExit):pressure_history_contract(s)
    def test_renderer_contract(self):
        rendered=render_properties(scenario());self.assertIn('timesS (0 5 30)',rendered);self.assertIn('pressuresPa (0 900000 0)',rendered)
        self.assertNotIn('targetInletPressure',rendered);self.assertNotIn('pressureRampTime',rendered)
    def test_legacy_renderer(self):
        s=json.loads((ROOT/'config/reference_R0.json').read_text());r=render_properties(s)
        self.assertIn('targetInletPressure',r);self.assertIn('pressureRampTime',r);self.assertNotIn('prescribedPressureBoundary',r)
    def test_conflicts(self):
        for key in ('target_inlet_pressure_gauge_Pa','pressure_ramp_time_s'):
            s=scenario();s['hydraulics'][key]=0
            with self.assertRaisesRegex(SystemExit,'XSV_PRESSURE_001_CONTRACT_CONFLICT'):render_properties(s)
        s=scenario();s['hydraulics']['pressure_boundary_model']='prescribedPressure'
        with self.assertRaisesRegex(SystemExit,'XSV_PRESSURE_001_CONTRACT_CONFLICT'):render_properties(s)
    def test_missing_schedule(self):
        s=scenario();s['hydraulics'].pop('prescribed_pressure_boundary')
        with self.assertRaisesRegex(SystemExit,'XSV_PRESSURE_001_INVALID_SCHEDULE'):render_properties(s)
    def test_wrong_units_contract(self):
        s=scenario();s['hydraulics']['prescribed_pressure_boundary']['pressures_bar']=[0,9,0]
        with self.assertRaises(SystemExit):render_properties(s)
    def test_array_validation(self):
        for t,p in [([0],[0]),([0,1],[0]),([0,0],[0,1]),([1,0],[0,1]),([0,math.nan],[0,1]),([0,30],[0,math.inf]),([0,30],[0,-1]),([1,30],[0,1]),([0,29],[0,1])]:
            s=scenario();s['hydraulics']['prescribed_pressure_boundary'].update(times_s=t,pressures_gauge_Pa=p)
            with self.assertRaises(SystemExit):render_properties(s)
    def test_unreachable(self):
        with self.assertRaisesRegex(ValueError,'XSV_PRESSURE_001_CROSSING_UNREACHABLE'):Schedule([0,1],[0,0]).crossing(0,1,1,0)
    def test_interior_peak(self):self.assertEqual(Schedule([0,1,2],[0,900000,0]).maximum(),900000)
    def test_all_integration_points(self):
        s=(ROOT/'solver/espressoWholePullFoam/espressoWholePullFoam.C').read_text()
        for term in ('prescribedPressureParameters.target(timeValue)','prescribedPressureParameters.positiveDrivingIntegral','prescribedPressureParameters.crossingTime','prescribedPressureParameters.maximumPressure()'):self.assertIn(term,s)
        self.assertIn('maximumCompactionPressureDrop = maximumBoundaryPressure-outletPressure',s)
        self.assertIn('targetInletPressure = prescribedPressureHistory ? 0.0 :',s)
        self.assertIn('pressureRampTime = prescribedPressureHistory ? 0.0 :',s)
    def test_original_flow_helper_unchanged(self):
        p='solver/espressoWholePullFoam/prescribedFlowBoundaryModel.H'
        self.assertEqual((ROOT/p).read_bytes(),subprocess.check_output(['git','show',validator.load(OUT/'MATHEMATICAL_AND_COMPATIBILITY_CONTRACT.json')['base_commit']+':'+p],cwd=ROOT))
    def test_production_receipts(self):
        e=load('EXECUTION_RECEIPT.json');self.assertGreaterEqual(len(e['production_runs']),26)
        for r in e['production_runs']:
            self.assertEqual(r['completion_status'],'PASS');self.assertTrue(r['conservation_pass']);self.assertTrue(r['bounded_state_pass']);self.assertTrue(validator.digest_ok(r['log_sha256']))
    def test_complete_invalid_matrix(self):
        d=load('INVALID_CONTRACT_RESULTS.json');self.assertEqual({v['id'] for v in d['cases']},validator.INVALID)
        self.assertTrue(all(v['exit_code']!=0 and v['pass'] for v in d['cases']))
    def test_complete_regression_matrix(self):
        d=load('EXISTING_MODE_REGRESSIONS.json');self.assertEqual(set(d['comparisons']),validator.REGRESSIONS);self.assertTrue(d['pass'])
    def test_no_private_production_content(self):
        for p in (ROOT/'solver/espressoWholePullFoam').glob('*'):
            if p.is_file():
                text=p.read_text().lower()
                for forbidden in ('visualizer','cohort 066','play-003','/home/'):
                    self.assertNotIn(forbidden,text)
    def test_validator(self):
        d=validator.inspect(ROOT);self.assertTrue(d['pass'],d)
    def test_success_requires_every_gate(self):
        gates=load('RESULT.json')['gates'];self.assertEqual(validator.classify(gates),validator.SUCCESS)
        for key in gates:
            bad=dict(gates,**{key:False});self.assertNotEqual(validator.classify(bad),validator.SUCCESS)
    def test_validator_rejects_fabricated_completion(self):
        original=validator.load
        def altered(p):
            d=original(p)
            if p.name=='EXECUTION_RECEIPT.json':d['production_runs']=[]
            return d
        with patch.object(validator,'load',side_effect=altered):self.assertFalse(validator.inspect(ROOT)['pass'])
    def test_validator_rejects_false_gate(self):
        original=validator.load
        def altered(p):
            d=original(p)
            if p.name=='LEGACY_RAMP_EQUIVALENCE.json':d['pass']=False
            return d
        with patch.object(validator,'load',side_effect=altered):self.assertFalse(validator.inspect(ROOT)['pass'])
    def test_manifest_binding(self):
        d=load('ARTIFACT_MANIFEST.json')['sha256']
        for name,h in d.items():self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),h)

def vector_test(vector):
    def test(self):
        s=Schedule(vector['times'],vector['pressures']);actual=next(x for x in load('FUNCTION_LEVEL_VERIFICATION.json')['vectors'] if x['id']==vector['id'])
        self.assertTrue(actual['pass']);self.assertEqual(actual['output_sha256'],actual['repeat_sha256'])
        for row in actual['actual']:
            k=row['kind'];i=int(row['index']);value=float(row['value'])
            expected={'target':lambda:s.target(vector['targets'][i]),'integral':lambda:s.integral(*vector['integrals'][i]),'crossing':lambda:s.crossing(*vector['crossings'][i]),'maximum':s.maximum}[k]()
            limit=1e-10 if k=='crossing' else max(1e-6,abs(expected)*1e-12) if k=='integral' else 1e-6
            self.assertLessEqual(abs(value-expected),limit)
            if k=='integral':self.assertGreaterEqual(value,0)
            if k=='crossing':self.assertTrue(vector['crossings'][i][0]<=value<=vector['crossings'][i][1])
    return test
for v in load('REFERENCE_VECTORS.json'):setattr(PressureHistory,'test_vector_'+v['id'],vector_test(v))
for file in validator.FILES.values():
    def gate(self,file=file):self.assertTrue(load(file)['pass'],file)
    setattr(PressureHistory,'test_gate_'+file.split('.')[0].lower(),gate)
if __name__=='__main__':unittest.main()
