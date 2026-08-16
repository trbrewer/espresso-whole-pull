import hashlib, importlib.util, json, math, pathlib, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import poroelastic_compaction_reference as independent
SPEC=importlib.util.spec_from_file_location("md2",ROOT/"scripts/sci_md_002a.py"); md2=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(md2)
class FreezeTests(unittest.TestCase):
    def test_unique_bounded_matrix(self):
        rows=md2.matrix_rows(); self.assertEqual(len(rows),580); self.assertEqual(len({r['case_id'] for r in rows}),580); self.assertLessEqual(len(rows),10000)
    def test_protocol_hash_and_boundaries(self):
        p=json.loads((ROOT/"validation/cases/sci_md_002a/SCI_MD_002A_PROTOCOL.json").read_text()); b=(ROOT/"validation/cases/sci_md_002a/SCI_MD_002A_CASE_MATRIX.json").read_bytes()
        self.assertEqual(p["matrix_sha256"],hashlib.sha256(b).hexdigest()); self.assertEqual(p["change_declaration"],"NO_GOVERNING_PHYSICS_CHANGE"); self.assertEqual(p["claim_boundary"]["physical_validation"],"NOT_ESTABLISHED")
    def test_no_primary_namespace_owned(self):
        d=json.loads((ROOT/"docs/analysis/sci_md_002a/PARALLEL_LANE_DECLARATION.json").read_text()); self.assertFalse(any("sci_lc" in p for p in d["owned_paths"]))
    def test_equilibrium_mapping_matches_independent_reference(self):
        for pc in md2.PCS:
            for pressure in (450000,900000):
                if pressure>=pc: continue
                x=pressure/pc
                self.assertAlmostEqual(md2.j_integral(x),float(independent.integrate_j(x,md2.PHI)),places=12)
                self.assertAlmostEqual(md2.bed_ratio(x),float(independent.bed_height_ratio(pressure,md2.PHI,pc)),places=10)
    def test_constant_load_backward_euler_response(self):
        dt,tau,target=.05,10.,9e5; sigma=0.
        for _ in range(200): sigma=(sigma+dt*target/tau)/(1+dt/tau)
        exact=target*(1-math.exp(-10/tau))
        self.assertLess(abs(sigma-exact)/target,1e-3)
    def test_zero_and_frozen_controls(self):
        self.assertEqual(md2.j_integral(0),0); self.assertEqual(md2.bed_ratio(0),1); self.assertEqual(md2.porosity(0),md2.PHI); self.assertGreater(md2.conductance(0,1239155,1e-15),0)
        for x in (1e-12,1e-9,1e-6,1e-4):
            self.assertTrue(0<md2.j_integral(x)<x)
            self.assertTrue(0<md2.bed_ratio(x)<=1)
    def test_compaction_resistance_direction_is_separate_from_flow_order(self):
        pc,k0=1239155,2e-15
        pressures=(5e5,9e5,11e5)
        conductances=[md2.conductance(p,pc,k0) for p in pressures]
        flows=[g*p for g,p in zip(conductances,pressures)]
        self.assertTrue(conductances[0]>conductances[1]>conductances[2])
        self.assertFalse(flows[0]>flows[1]>flows[2])
    def test_machine_balance_uses_adjacent_state(self):
        row=next(r for r in md2.matrix_rows() if r['arm']=='S2_MACHINE_TRANSFER')
        result=md2.simulate(row,md2.source_rows())
        self.assertEqual(result['status'],'PASS')
        self.assertLess(result['machine_balance_max_m3_s'],1e-18)
if __name__ == '__main__': unittest.main()
