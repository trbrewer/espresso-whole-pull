import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xsv_xct_001", ROOT / "verification/tools/xsv_xct_001.py")
XCT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = XCT
SPEC.loader.exec_module(XCT)
np = XCT.np


class XsvXct001Tests(unittest.TestCase):
    def test_protocol_uses_exact_targets_and_processed_route(self):
        protocol=json.loads((ROOT/"verification/cases/xsv_xct_001/XSV_XCT_001_PROTOCOL.json").read_text())
        self.assertEqual(protocol["exact_targets"]["primary"], 0.373506)
        self.assertEqual(protocol["exact_targets"]["supporting"], [0.389226, 0.395294])
        self.assertIn("PROCESSED", json.dumps(protocol))

    def test_processed_table_preserves_original_and_normalized_fields(self):
        rows=XCT.read_csv(ROOT/"verification/cases/xsv_xct_001/XSV_XCT_001_PROCESSED_SOURCE_DATA.csv")
        self.assertEqual(len(rows),22)
        self.assertEqual(len({r["sample_id"] for r in rows}),22)
        for row in rows:
            self.assertIn("coffee",row); self.assertIn("coffee_normalized",row)
            self.assertIn("k_m2",row); self.assertIn("permeability_evidence_role",row)

    def test_rights_status_is_present(self):
        rows=XCT.read_csv(ROOT/"verification/cases/xsv_xct_001/XSV_XCT_001_SOURCE_MANIFEST.csv")
        self.assertTrue(all(r["license_or_basis"] and r["repository_inclusion_permitted"] for r in rows))

    def test_binary_volume_labels_and_hash_are_deterministic(self):
        a=np.zeros((3,4,5),dtype=np.uint8); a[1,2,3]=1
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fixture.npy"; np.save(p,a)
            solid=XCT.volume_from_npy(p,solid_value=1)
            self.assertTrue(solid[1,2,3]); self.assertEqual(int(solid.sum()),1)
            self.assertEqual(XCT.sha256(p),XCT.sha256(p))
            inverse=XCT.volume_from_npy(p,solid_value=0)
            self.assertTrue(np.array_equal(inverse,~solid))

    def test_volume_rejects_nonbinary_and_nondimensional_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.npy"; np.save(p,np.array([[0,2]]))
            with self.assertRaises(ValueError): XCT.volume_from_npy(p)

    def test_morphology_known_fixture(self):
        solid=np.ones((5,5,5),dtype=bool); solid[:,2,2]=False; solid[2,0,0]=False
        m=XCT.volume_descriptors(solid)
        self.assertAlmostEqual(m["phi_total"],6/125)
        self.assertAlmostEqual(m["phi_connected_x"],5/125)
        self.assertAlmostEqual(m["isolated_void_fraction"],1/125)
        self.assertGreater(m["specific_interfacial_area_lu"],0)
        self.assertLessEqual(m["pore_distance_q10"],m["pore_distance_q90"])

    def test_hydraulic_gross_void_and_si_contract(self):
        h=XCT.hydraulic_contract(.25,2e-6,.1,1e-6,3e-6)
        self.assertAlmostEqual(h["K_gross_lu2"],.2)
        self.assertAlmostEqual(h["K_void_lu2"],.8)
        self.assertAlmostEqual(h["K_gross_lu2"],.25*h["K_void_lu2"])
        self.assertAlmostEqual(h["K_gross_m2"],.2*9e-12)
        with self.assertRaises(ValueError): XCT.hydraulic_contract(.25,1,.1,-1,1)

    def test_directional_average_and_parity_fail_closed(self):
        self.assertEqual(XCT.directional_mean([1,2,3]),2)
        with self.assertRaises(ValueError): XCT.directional_mean([1,2])
        self.assertEqual(XCT.parity_disposition(exact_mask=False,equivalent_boundary=True),"SOURCE_DOMAIN_NOT_IDENTICAL")
        self.assertEqual(XCT.parity_disposition(exact_mask=True,equivalent_boundary=False),"BOUNDARY_SEMANTICS_NOT_EQUIVALENT")

    def test_transfer_is_strict_and_grouped(self):
        result=json.loads((ROOT/"verification/cases/xsv_xct_001/XSV_XCT_001_TRANSFER_ASSESSMENT.json").read_text())
        self.assertEqual(result["mode"],"SYNTHETIC_TRAIN_REAL_TEST")
        self.assertGreater(result["synthetic_physical_lineages"],1)
        self.assertEqual(result["real_inside_synthetic_shared_feature_box"],0)
        self.assertEqual(result["full_topology_transfer"],"FULL_TRANSFER_NOT_TESTABLE_WITH_PROCESSED_DATA_ONLY")

    def test_claims_remain_bounded(self):
        result=json.loads((ROOT/"verification/cases/xsv_xct_001/XSV_XCT_001_RESULT.json").read_text())
        claims=result["claim_boundary"]
        self.assertEqual(claims["physical_validation"],"NOT_ESTABLISHED")
        self.assertEqual(claims["real_coffee_geometry"],"PROCESSED_DATA_ONLY")
        self.assertEqual(claims["real_tamped_puck_representative_volume"],"NOT_ESTABLISHED")
        self.assertEqual(claims["dynamic_pressure_mechanism"],"NOT_IDENTIFIED")
        self.assertEqual(result["cross_code"],"CROSS_CODE_PARITY_NOT_ADJUDICATED")

    def test_no_external_volume_is_committed(self):
        forbidden={".tif",".tiff",".nrrd",".nii",".raw",".mhd",".h5",".npy"}
        tracked=set()
        import subprocess
        for name in subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True).splitlines():
            if Path(name).suffix.lower() in forbidden and "fixture" not in name: tracked.add(name)
        self.assertEqual(tracked,set())


if __name__ == "__main__": unittest.main()
