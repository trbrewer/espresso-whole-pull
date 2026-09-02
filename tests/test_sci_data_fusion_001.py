import hashlib,json,os,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from analysis.sci_data_fusion_001.audit import PASS,validate_audit
from analysis.sci_data_fusion_001.authority import AuthorityError,SUPERSEDED_FREEZE,git,sha256,verify_consumed,verify_freeze_manifest,verify_puckworks
from analysis.sci_data_fusion_001.compatibility import LOAD_BEARING_GATES,build_pairwise,independently_eligible,interval_metrics,reduce_component
from analysis.sci_data_fusion_001.constraints import narrowing
from analysis.sci_data_fusion_001.decision import reduce_overall
from analysis.sci_data_fusion_001.inventory import scan_registered_families,validate_support_inventory
from analysis.sci_data_fusion_001.lineage import pair_independence
from analysis.sci_data_fusion_001.phase_b import execute
from analysis.sci_data_fusion_001.uncertainty import combine,compatible
ROOT=Path(__file__).parents[1];PUCK=Path(os.environ["EWP_SCI_DATA_FUSION_001_PUCKWORKS_ROOT"])
def support(name,lineage,group,interval=(.2,.4),**extra):
    row={"support_id":name,"lineage_id":lineage,"correlation_group_id":group,"experiment_id":lineage,"interval":list(interval),"frozen_role":"COMMON_CONSTRAINT_CANDIDATE","qualified_support":True,"target_exposed":False,"source_internal_validation":False,"consumed_comparison_conflict":False,"provenance_complete":True,"rights_permit_analysis":True,"canonical_quantity_id":"Q"};row.update(extra);return row
def gates(value=True):return {name:value for name in LOAD_BEARING_GATES}
class AuthorityTests(unittest.TestCase):
    def test_frozen_base_not_current_head(self):
        auth=json.loads((ROOT/"docs/analysis/sci_data_fusion_001/AUTHORITY.json").read_text());self.assertEqual(auth["frozen_ewp_base"]["commit"],"2bf996596bb7408c2b5e2fc1eb0f7a65e5f5bae2");self.assertNotEqual(auth["frozen_ewp_base"]["commit"],git(ROOT,"rev-parse","HEAD"))
    def test_consumed_exact(self):verify_consumed(ROOT,json.loads((ROOT/"docs/analysis/sci_data_fusion_001/CONSUMED_RESULT_ARTIFACTS.json").read_text()))
    def test_consumed_duplicate_rejects(self):
        ledger=json.loads((ROOT/"docs/analysis/sci_data_fusion_001/CONSUMED_RESULT_ARTIFACTS.json").read_text());ledger["artifacts"].append(dict(ledger["artifacts"][0]))
        with self.assertRaises(AuthorityError):verify_consumed(ROOT,ledger)
    def test_consumed_missing_or_extra_rejects(self):
        ledger=json.loads((ROOT/"docs/analysis/sci_data_fusion_001/CONSUMED_RESULT_ARTIFACTS.json").read_text());expected={x["path"] for x in ledger["artifacts"]};ledger["artifacts"].pop()
        with self.assertRaises(AuthorityError):verify_consumed(ROOT,ledger,expected)
    def test_consumed_altered_rejects(self):
        with self.assertRaises(AuthorityError):verify_consumed(ROOT,{"artifacts":[{"path":"AGENTS.md","sha256":"0"*64}]})
    def test_puckworks_exact(self):
        expected=json.loads((ROOT/"docs/analysis/sci_data_fusion_001/AUTHORITY.json").read_text())["puckworks"];self.assertEqual(verify_puckworks(PUCK,expected)["commit"],expected["commit"])
    def test_no_puckworks_fallback(self):
        with self.assertRaises(AuthorityError):verify_puckworks(ROOT,json.loads((ROOT/"docs/analysis/sci_data_fusion_001/AUTHORITY.json").read_text())["puckworks"])
    def test_freeze_path_mutation_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"x").write_text("a");manifest=root/"m.json";manifest.write_text(json.dumps({"files":[{"path":"x","sha256":sha256(root/"x")}]}));(root/"x").write_text("b")
            with self.assertRaises(AuthorityError):verify_freeze_manifest(root,manifest)
class CensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules=json.loads((ROOT/"analysis/sci_data_fusion_001/family_screen_rules.json").read_text());cls.families,cls.datasets=scan_registered_families(PUCK,cls.rules)
    def test_exact_39_once(self):self.assertEqual(len(self.families),39);self.assertEqual(len({x["family_id"] for x in self.families}),39)
    def test_all_terminal(self):self.assertTrue(all(x["screening_disposition"] and x["terminal_reason"] for x in self.families))
    def test_named_minimum_accounted(self):self.assertTrue({"wadsworth2026","vacaguerra2023a","maille2024","romancorrochano2017","hargarten2020","mo2023","mo2023_2","visualizer","g3_pump_characteristic","waszkiewicz2025","gagne2021","pocketscience2024"}<={x["family_id"] for x in self.families})
    def test_manifest_references_checked(self):self.assertTrue(self.datasets);self.assertTrue(all(x["manifest_verified"] for x in self.datasets))
    def test_screened_out_not_omitted(self):self.assertTrue(any(x["screening_disposition"].startswith("EXCLUDED") for x in self.families))
    def test_unavailable_not_absent(self):self.assertEqual(next(x for x in self.families if x["family_id"]=="pocketscience2024")["screening_disposition"],"MATCHED_BUT_DATA_UNAVAILABLE")
class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=json.loads((ROOT/"docs/analysis/sci_data_fusion_001/SOURCE_SUPPORT_INVENTORY.json").read_text())["records"]
    def test_unique_and_terminal(self):validate_support_inventory(self.rows);self.assertEqual(len(self.rows),25)
    def test_fig12_separate(self):self.assertTrue({"VACA_FIG12_MEASURED_DRY_POROSITY","VACA_FIG12_CALCULATED_DRY_POROSITY"}<={x["support_id"] for x in self.rows})
    def test_vaca_k_separate(self):self.assertTrue({"VACA_C1_DARCY_K_PUBLISHED_VISCOSITY","VACA_C1_DARCY_K_EWP_VISCOSITY_REEXPRESSION"}<={x["support_id"] for x in self.rows})
    def test_eq11_context(self):self.assertEqual(next(x for x in self.rows if x["support_id"]=="VACA_EQ11_POSTFIT_RECONSTRUCTION")["frozen_role"],"CONTEXT_ONLY")
    def test_unqualified_not_promoted(self):self.assertTrue(all(x.get("originating_task_id") or not x.get("qualified_support") for x in self.rows))
class CompatibilityTests(unittest.TestCase):
    def test_complete_pair_count(self):
        items=[support("a","a","a"),support("b","b","b"),support("c","c","c")];contracts={f"{a}|{b}":gates() for a,b in (("a","b"),("a","c"),("b","c"))};self.assertEqual(len(build_pairwise(items,contracts)),3)
    def test_omitted_pair_blocks(self):
        with self.assertRaises(ValueError):build_pairwise([support("a","a","a"),support("b","b","b")],{})
    def test_unknown_gate_fails_closed(self):
        row=gates();row["physical_quantity"]=None;self.assertEqual(build_pairwise([support("a","a","a"),support("b","b","b")],{"a|b":row})[0]["terminal_compatibility"],"BLOCKED_SEMANTIC")
    def test_explicit_mismatch(self):
        row=gates();row["observation_operator"]=False;self.assertEqual(build_pairwise([support("a","a","a"),support("b","b","b")],{"a|b":row})[0]["terminal_compatibility"],"INCOMPATIBLE")
    def test_same_group_blocks(self):self.assertFalse(pair_independence(support("a","a","g"),support("b","b","g"))["independent_for_common_constraint"])
    def test_target_exposed_ineligible(self):self.assertFalse(independently_eligible(support("a","a","a",target_exposed=True)))
    def test_ineligible_role_excluded(self):self.assertFalse(independently_eligible(support("a","a","a",frozen_role="CONTEXT_ONLY")))
    def test_disjoint_same_scope_conflict(self):self.assertEqual(reduce_component("Q",[support("a","a","a",(.1,.2)),support("b","b","b",(.3,.4))],{"a|b":gates()},{"status":"NO_AUTHORIZED_NUMERIC_BASELINE"})["component_result"],"CONFLICT_SAME_SCOPE_SUPPORTS")
    def test_source_ids_survive(self):self.assertEqual([x["support_id"] for x in reduce_component("Q",[support("a","a","a"),support("b","b","b",(.3,.5))],{"a|b":gates()},{"status":"NO_AUTHORIZED_NUMERIC_BASELINE"})["contributing_supports"]],["a","b"])
    def test_interval_not_distribution(self):self.assertNotIn("distribution",interval_metrics([.1,.4],[.3,.5]))
class BaselineReducerTests(unittest.TestCase):
    def test_all_non_numeric_statuses(self):
        for status in ("NO_AUTHORIZED_NUMERIC_BASELINE","BASELINE_SEMANTICALLY_INCOMPATIBLE","BASELINE_AUTHORITY_BLOCKED"):self.assertFalse(narrowing([.2,.3],{"status":status})["quantitative_narrowing_claim"])
    def test_outside_not_narrowing(self):self.assertFalse(narrowing([.1,.3],{"status":"AUTHORIZED_BASELINE_AVAILABLE","interval":[.2,.4]})["quantitative_narrowing_claim"])
    def test_strict_narrowing(self):self.assertTrue(narrowing([.2,.3],{"status":"AUTHORIZED_BASELINE_AVAILABLE","interval":[.1,.4]})["quantitative_narrowing_claim"])
    def test_incidental_blocker_not_control(self):self.assertNotIn("BLOCKED",reduce_overall([{"component_result":"NEGATIVE_NO_COMMON_SUPPORT","decision_material":False,"blockers":["x"]}])["disposition"])
    def test_mixed_preserved(self):self.assertTrue(reduce_overall([{"component_result":"CONFLICT_SAME_SCOPE_SUPPORTS","decision_material":False,"blockers":[]},{"component_result":"NEGATIVE_NO_COMMON_SUPPORT","decision_material":False,"blockers":[]}])["mixed_outcomes_preserved"])
    def test_uncertainty_no_pool(self):
        row={x:"same" for x in ("statistic","estimand","scale","replicate_unit","state","observation_operator")};self.assertTrue(compatible(row,dict(row)))
        with self.assertRaises(RuntimeError):combine(row,row)
class AuditTests(unittest.TestCase):
    def record(self):
        manifest=ROOT/"docs/analysis/sci_data_fusion_001/FREEZE_CONTENT_MANIFEST.json";return {"task_id":"SCI-DATA-FUSION-001","audit_type":"SINGLE_INDEPENDENT_PREEXECUTION_AUDIT","audit_disposition":PASS,"reviewed_head":git(ROOT,"rev-parse","HEAD"),"reviewed_tree":git(ROOT,"rev-parse","HEAD^{tree}"),"reviewed_freeze_content_manifest_sha256":sha256(manifest),"reviewer_identity":"independent-reviewer","reviewer_independence_statement":"I did not prepare the freeze and independently reviewed it.","reviewed_authorities":{"ewp":True,"puckworks":True},"material_findings":[],"review_record_reference":"https://example.invalid/review","review_date":"2026-09-02"}
    def validate(self,row):
        with tempfile.NamedTemporaryFile("w",suffix=".json") as stream:json.dump(row,stream);stream.flush();return validate_audit(ROOT,Path(stream.name),ROOT/"docs/analysis/sci_data_fusion_001/FREEZE_CONTENT_MANIFEST.json")
    def test_empty_reject(self):
        with self.assertRaises(AuthorityError):self.validate({})
    def test_wrong_exact_identity_rejects(self):
        for key in ("reviewed_head","reviewed_tree","reviewed_freeze_content_manifest_sha256"):
            row=self.record();row[key]="0"*(64 if "sha256" in key else 40)
            with self.assertRaises(AuthorityError):self.validate(row)
    def test_superseded_reject(self):
        row=self.record();row["reviewed_head"]=SUPERSEDED_FREEZE
        with self.assertRaises(AuthorityError):self.validate(row)
    def test_findings_or_no_independence_reject(self):
        row=self.record();row["material_findings"]=["material"]
        with self.assertRaises(AuthorityError):self.validate(row)
        row=self.record();row["reviewer_independence_statement"]=""
        with self.assertRaises(AuthorityError):self.validate(row)
    def test_exact_pass(self):
        row=self.record();row["reviewed_head"]="1"*40;row["reviewed_tree"]="2"*40
        with patch("analysis.sci_data_fusion_001.audit.git",side_effect=lambda root,*args:"1"*40 if args[-1]=="HEAD" else "2"*40):self.assertEqual(self.validate(row)["audit_disposition"],PASS)
class DeterminismTests(unittest.TestCase):
    def test_synthetic_phase_b_byte_deterministic(self):
        fixture={"inventory":[support("a","a","a"),support("b","b","b",(.3,.5))],"extraction_rules":[],"pairwise_gate_contracts":{"a|b":gates()},"baselines":{"Q":{"status":"NO_AUTHORIZED_NUMERIC_BASELINE"}}}
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a",Path(td)/"b";execute(ROOT,a,fixture);execute(ROOT,b,fixture);self.assertEqual({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in a.iterdir()},{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in b.iterdir()})
if __name__=="__main__":unittest.main()
