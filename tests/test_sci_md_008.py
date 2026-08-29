import csv, importlib, inspect, json, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock

from tools.sci_md_008 import study

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'validation/sci_md_008'

class SciMd008Tests(unittest.TestCase):
    def copy_package(self):
        temporary=tempfile.TemporaryDirectory(); path=Path(temporary.name)/'result'
        shutil.copytree(PACKAGE,path); return temporary,path

    def test_parameter_artifact_is_frozen(self):
        self.assertEqual(study.sha(ROOT/study.PARAM_REL),study.PARAM_SHA)

    def test_cli_calls_only_real_inventory_gate(self):
        argv=['--puckworks','/p','--executable','/e','--run-root','/r','--output','/o']
        with mock.patch.object(study,'run_inventory_gate',return_value={'disposition':study.STOP}) as gate:
            self.assertEqual(study.main(argv),3)
        gate.assert_called_once_with(Path('/p'),Path('/e'),Path('/r'),Path('/o'))

    def test_only_scientific_runner_is_inventory_gate(self):
        runners=[name for name,value in vars(study).items() if inspect.isfunction(value) and name.startswith('run_')]
        self.assertEqual(runners,['run_inventory_gate'])

    def test_target_scoring_functions_are_absent(self):
        for name in ('run_matrix','score','prediction_row','inventory_gate','adjudicate','plots'):
            self.assertFalse(hasattr(study,name),name)

    def test_source_has_no_synthetic_inventory_pass(self):
        source=inspect.getsource(study)
        self.assertNotIn('INVENTORY_SCALE_INVARIANCE_PASS',source)
        self.assertNotIn('fraction_shape_max_difference":0.0',source.replace(' ',''))

    def test_source_has_no_performance_disposition(self):
        source=inspect.getsource(study)
        for token in ('SCI_MD_008_PRODUCTION_PDE_CONDITIONAL_SOURCE_RECONSTRUCTION_SUPPORTED',
                      'SCI_MD_008_PRODUCTION_PDE_NO_MATERIAL_INCREMENTAL_VALUE',
                      'SCI_MD_008_PRODUCTION_TRANSPORT_PARAMETERIZATION_OR_FORMULATION_REJECTED'):
            self.assertNotIn(token,source)

    def test_blocked_target_artifacts(self):
        for name in study.BLOCKED_TABLES:
            self.assertEqual(study.read_csv(PACKAGE/name),[{'state':'BLOCKED','reason':study.STOP}])

    def test_result_closes_against_real_inventory_csv(self):
        self.assertEqual(study.verify_result_package(PACKAGE)['status'],'PASS')

    def test_maximum_is_recomputed_from_rows(self):
        rows=study.read_csv(PACKAGE/'INVENTORY_SCALE_INVARIANCE.csv')
        maximum=max(float(r['fraction_shape_max_absolute_difference']) for r in rows)
        result=json.loads((PACKAGE/'RESULT.json').read_text())
        self.assertEqual(maximum,result['maximum_fraction_shape_difference'])

    def test_mutated_gate_row_fails(self):
        temporary,path=self.copy_package()
        try:
            rows=study.read_csv(path/'INVENTORY_SCALE_INVARIANCE.csv'); rows[0]['condition']='E99'
            with (path/'INVENTORY_SCALE_INVARIANCE.csv').open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
            with self.assertRaises(ValueError): study.verify_result_package(path)
        finally: temporary.cleanup()

    def test_mutated_result_summary_fails(self):
        temporary,path=self.copy_package()
        try:
            result=json.loads((path/'RESULT.json').read_text()); result['maximum_fraction_shape_difference']=0
            (path/'RESULT.json').write_text(json.dumps(result))
            with self.assertRaises(ValueError): study.verify_result_package(path)
        finally: temporary.cleanup()

    def test_positive_disposition_mutation_fails(self):
        temporary,path=self.copy_package()
        try:
            result=json.loads((path/'RESULT.json').read_text()); result['disposition']='SCI_MD_008_PRODUCTION_PDE_NO_MATERIAL_INCREMENTAL_VALUE_OVER_FROZEN_REDUCED_MODEL'
            (path/'RESULT.json').write_text(json.dumps(result))
            with self.assertRaises(ValueError): study.verify_result_package(path)
        finally: temporary.cleanup()

    def test_unblocked_target_artifact_fails(self):
        temporary,path=self.copy_package()
        try:
            (path/'MODEL_COMPARISON.csv').write_text('state,reason\nPASS,scored\n')
            with self.assertRaises(ValueError): study.verify_result_package(path)
        finally: temporary.cleanup()

    def test_incomplete_run_manifest_fails(self):
        temporary,path=self.copy_package()
        try:
            lines=(path/'RUN_MANIFEST.csv').read_text().splitlines(); (path/'RUN_MANIFEST.csv').write_text('\n'.join(lines[:-1])+'\n')
            with self.assertRaises(ValueError): study.verify_result_package(path)
        finally: temporary.cleanup()

    def test_import_has_no_execution_side_effect(self):
        with mock.patch.object(study.Matrix,'run',side_effect=AssertionError('scientific run')):
            importlib.reload(study)

    def test_package_verification_is_deterministic(self):
        self.assertEqual(study.verify_result_package(PACKAGE),study.verify_result_package(PACKAGE))

    def test_exact_stop_is_preserved(self):
        result=json.loads((PACKAGE/'RESULT.json').read_text())
        self.assertEqual(result['disposition'],study.STOP)

    def test_exact_gate_coverage(self):
        result=study.verify_result_package(PACKAGE)
        self.assertEqual((result['production_runs'],result['inventory_rows']),(18,36))

    def test_zero_target_predictions(self):
        result=json.loads((PACKAGE/'RESULT.json').read_text())
        self.assertEqual(result['canonical_prediction_count'],0)
        self.assertEqual(result['canonical_matrix_state'],'BLOCKED_NOT_EXECUTED_BY_PREDECLARED_GATE')

    def test_mutated_parameter_fails_authority(self):
        def fake_git(*args,**kwargs): return 'commit' if args[:2]==('cat-file','-t') else study.PW_TREE
        with mock.patch.object(study,'git',side_effect=fake_git), mock.patch.object(study,'sha',return_value='bad'):
            with self.assertRaises(SystemExit): study.authority(ROOT)

if __name__=='__main__': unittest.main()
