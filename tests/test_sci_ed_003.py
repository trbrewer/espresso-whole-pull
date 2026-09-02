import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/validate_sci_ed_003.py"
FILES=["docs/analysis/sci_ed_003","docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md","docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv","docs/PROJECT_STATE.md","docs/CLAIM_CEILING.md"]

class SciEd003Test(unittest.TestCase):
    def run_validator(self,root): return subprocess.run([sys.executable,str(SCRIPT),"--root",str(root)],text=True,capture_output=True)
    def test_live_contract_passes(self): self.assertEqual(self.run_validator(ROOT).returncode,0)
    def mutate(self, edit):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for rel in FILES:
                src=ROOT/rel; dst=root/rel
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copytree(src,dst) if src.is_dir() else shutil.copy2(src,dst)
            edit(root)
            self.assertNotEqual(self.run_validator(root).returncode,0)
    def test_authorization_fail_open_rejected(self):
        def edit(root):
            p=root/"docs/analysis/sci_ed_003/MINIMUM_PROGRAMME.json"; x=json.loads(p.read_text()); x["operation_authorized"]=True; p.write_text(json.dumps(x))
        self.mutate(edit)
    def test_quantity_equivalence_rejected(self):
        def edit(root):
            p=root/"docs/analysis/sci_ed_003/DECISION_ESTIMAND_REGISTER.json"; x=json.loads(p.read_text()); x["distinctness_assertions"]["I_ref_EQUALS_PRODUCTION_M0"]="ESTABLISHED"; p.write_text(json.dumps(x))
        self.mutate(edit)
    def test_unsupported_endpoint_rejected(self):
        def edit(root):
            p=root/"docs/analysis/sci_ed_003/DECISION_ESTIMAND_REGISTER.json"; x=json.loads(p.read_text()); next(d for d in x["decisions"] if d["decision_id"]=="D02_REFERENCE_ENDPOINT")["prohibited_endpoint_adoption"]["maximum_eight_cycles"]=True; p.write_text(json.dumps(x))
        self.mutate(edit)
    def test_technical_replicate_pseudoreplication_rejected(self):
        def edit(root):
            p=root/"docs/analysis/sci_ed_003/MEASUREMENT_MODULES.json"; x=json.loads(p.read_text()); x["replication_contract"].pop("not_independent_shots"); p.write_text(json.dumps(x))
        self.mutate(edit)
if __name__=="__main__": unittest.main()
