import hashlib, importlib.util, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("md2",ROOT/"scripts/sci_md_002a.py"); md2=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(md2)
class FreezeTests(unittest.TestCase):
    def test_unique_bounded_matrix(self):
        rows=md2.rows(); self.assertEqual(len(rows),580); self.assertEqual(len({r['case_id'] for r in rows}),580); self.assertLessEqual(len(rows),10000)
    def test_protocol_hash_and_boundaries(self):
        p=json.loads((ROOT/"validation/cases/sci_md_002a/SCI_MD_002A_PROTOCOL.json").read_text()); b=(ROOT/"validation/cases/sci_md_002a/SCI_MD_002A_CASE_MATRIX.json").read_bytes()
        self.assertEqual(p["matrix_sha256"],hashlib.sha256(b).hexdigest()); self.assertEqual(p["change_declaration"],"NO_GOVERNING_PHYSICS_CHANGE"); self.assertEqual(p["claim_boundary"]["physical_validation"],"NOT_ESTABLISHED")
    def test_no_primary_namespace_owned(self):
        d=json.loads((ROOT/"docs/analysis/sci_md_002a/PARALLEL_LANE_DECLARATION.json").read_text()); self.assertFalse(any("sci_lc" in p for p in d["owned_paths"]))
if __name__ == '__main__': unittest.main()
