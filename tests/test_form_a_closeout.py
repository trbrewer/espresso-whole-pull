import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import form_a_closeout as C


class FormACloseoutTests(unittest.TestCase):
    def test_missing_evidence_is_unavailable_not_a_censored_subset_score(self):
        inputs=[dict(brew=str(p),nominal_pressure_bar=float(p),observed_onset_for_scoring_only_s=12.) for p in C.NOMINAL]
        chosen={r['brew']:dict(first_drip_s=10.,balances_and_bounds_qualified=True) for r in inputs}
        contexts={r['brew']:{} for r in inputs}
        def observe(work,record,context):
            raise ValueError('Corrupt retained evidence')
        with patch.object(C,'native_observations',side_effect=observe):
            score,rows,summary=C.onset_assessment(inputs,chosen,Path('.'),contexts,'A1','test')
        self.assertEqual(score['available_brews'],0)
        self.assertEqual(score['intended_brews'],11)
        self.assertEqual(score['onset_grade'],'NOT_SCORED')
        self.assertNotIn('onset_rmse_s',score)
        self.assertTrue(all(r['detector_censored'] is None for r in rows))
        self.assertTrue(all(r['detector_median_lower_bound_s'] is None for r in summary))
        self.assertTrue(all(r['front_median_s']==10. for r in summary))

    def test_identical_predictions_have_zero_paired_difference_despite_brew_variation(self):
        inputs=[];endpoints=[];traces=[]
        for p in C.NOMINAL:
            for i in range(3):
                inputs.append(dict(nominal_pressure_bar=float(p),observed_endpoint_g_s=1.,
                    observed_trace_g_s=[1.,1.,1.],trace_times_s=[0.,5.,10.],trace_mask=[False,True,True]))
                endpoints.append(1.+i*.2);traces.append([1.,1.+i*.1,1.+i*.3])
        prediction=dict(endpoints=endpoints,traces=traces)
        rows=C.R.paired_comparison(inputs,prediction,prediction,'test')
        for row in rows:
            self.assertGreater(row['A0_rmse_g_s'],0.)
            self.assertEqual(row['A1_minus_A0_g_s'],0.)
            self.assertEqual(row['paired_interval_g_s'],[0.,0.])

    def test_cell_volume_mapping_preserves_global_cells_across_decompositions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for i,(labels,volumes) in enumerate([([2,0],[30.,10.]),([3,1],[40.,20.])]):
                address=root/f'processor{i}/constant/polyMesh/cellProcAddressing';address.parent.mkdir(parents=True)
                address.write_bytes(b'FoamFile { format binary; }\n2\n('+np.asarray(labels,dtype='<i4').tobytes()+b')')
                field=root/f'processor{i}/10/Vc';field.parent.mkdir()
                field.write_bytes(b'format binary; internalField nonuniform List<scalar> 2\n('
                                  +np.asarray(volumes,dtype='<f8').tobytes()+b');')
            volumes,hashes=C.global_cell_volumes(root,2)
            np.testing.assert_array_equal(volumes,[10.,20.,30.,40.])
            self.assertEqual(len(hashes),4)
            address.write_bytes(b'FoamFile { format binary; }\n2\n('+np.asarray([2,1],dtype='<i4').tobytes()+b')')
            with self.assertRaises(ValueError):C.global_cell_volumes(root,2)


if __name__=='__main__':unittest.main()
