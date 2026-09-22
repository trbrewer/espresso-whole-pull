"""Scientific G2 radial compatibility and interval arithmetic tests."""
import copy,tempfile,unittest
from pathlib import Path
import numpy as np
from scripts.aggregate_viscosity import contract
from tools.sci_md_rheology_006.common import radial
from tools.sci_md_rheology_006.observer import scores,validate,decision
from tools.sci_md_rheology_002.export import HEADER

class RadialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.table=Path(self.tmp.name)/'constant.table';self.table.write_text(HEADER+'0 .001\n.1 .001\n.24 .001\n')
    def spec(self,mode='coupled'):
        s=radial();s['aggregate_viscosity']=dict(mode=mode,table=str(self.table));return s
    def test_geometry_envelope(self):
        for mode in ('coupled','observe'):self.assertIn(mode,contract(self.spec(mode)))
        with self.assertRaises(ValueError):contract(self.spec('bulkCoupled'))
    def test_rejected_configurations(self):
        for field,value in [('interface_radius_m',0),('interface_radius_m',.0146),('inner_permeability_m2',0),('outer_permeability_m2',float('nan'))]:
            s=self.spec();s['hydraulics']['permeability_profile'][field]=value
            with self.assertRaises(ValueError):contract(s)
        for field,value in [('pressure_ramp_time_s',1),('pressure_boundary_model','prescribedFlow'),('target_inlet_pressure_gauge_Pa',float('inf'))]:
            s=self.spec();s['hydraulics'][field]=value
            with self.assertRaises(ValueError):contract(s)
    def test_malformed_table(self):
        for content in [HEADER+'0 .001\n.1 .001\n.24 nan\n',HEADER+'0 .001\n.1 .001\n.24\n',HEADER+'0 .001\n.1 0\n.24 .001\n']:
            self.table.write_text(content)
            with self.assertRaises(ValueError):contract(self.spec())
    def trace(self):
        # Two equal total-flow intervals with opposite ten-pp share shifts.
        from tools.sci_md_rheology_006.observer import S0
        d={k:np.zeros(2) for k in ('schema_version start_s end_s dt_s state_s Q_inner_m3_s Q_outer_m3_s Q_total_m3_s reverse_inner_m3_s reverse_outer_m3_s reverse_total_m3_s volume_m3 cup_Q_m3_s c_n_min_kg_m3 c_n_max_kg_m3 mu_n_min_Pa_s mu_n_max_Pa_s c_next_min_kg_m3 c_next_max_kg_m3 mu_next_min_Pa_s mu_next_max_Pa_s correction_kg water_kg solute_kg stored_solute_kg remaining_kg inlet_loss_kg water_balance_kg solute_balance_kg dilute_pore_volume_fraction pore_courant_outgoing_max inner_area_m2 outer_area_m2 inner_volume_m3 outer_volume_m3 inner_remaining_kg outer_remaining_kg').split()}
        d.update(schema_version=np.ones(2),start_s=np.array([0.,1.]),state_s=np.array([0.,1.]),end_s=np.array([1.,2.]),dt_s=np.ones(2),Q_total_m3_s=np.full(2,1e-8),Q_inner_m3_s=1e-8*np.array([S0+.1,S0-.1]),cup_Q_m3_s=np.full(2,1e-8),volume_m3=np.full(2,1e-8),water_kg=965e-8*np.array([1.,2.]))
        d['Q_outer_m3_s']=d['Q_total_m3_s']-d['Q_inner_m3_s']
        for k in ('mu_n_min_Pa_s','mu_n_max_Pa_s','mu_next_min_Pa_s','mu_next_max_Pa_s'):d[k][:]=.001
        for zone,f in [('inner',.25),('outer',.75)]:
            d[zone+'_area_m2'][:]=np.pi*.029**2*f;d[zone+'_volume_m3'][:]=np.pi*.029**2*f*.009011660896432553
        return d
    def test_hand_computable_and_conservative_split(self):
        d=self.trace();validate(d,2);r=scores(d)
        self.assertAlmostEqual(r['D_mean_pp'],10);self.assertAlmostEqual(r['D_peak_pp'],10);self.assertAlmostEqual(r['signed_shift_pp'],0)
        split={k:np.repeat(v,2) for k,v in d.items()}
        split['dt_s'][:]=.5;split['start_s']=np.arange(4)*.5;split['state_s']=split['start_s'].copy();split['end_s']=split['start_s']+.5
        split['volume_m3']/=2;split['water_kg']=np.cumsum(split['volume_m3'])*965
        validate(split,2)
        for k in r:self.assertAlmostEqual(scores(split)[k],r[k],places=12)
    def test_corrupt_support_rejected(self):
        mutations=[('Q_total_m3_s',0),('Q_total_m3_s',float('nan')),('state_s',.1),('start_s',.2),('dt_s',0),('reverse_total_m3_s',1e-8),('inner_area_m2',0),('water_kg',1),('schema_version',2)]
        for key,value in mutations:
            d=self.trace();d[key][0]=value
            with self.assertRaises(ValueError,msg=key):validate(d,2)
        d=self.trace();del d['Q_inner_m3_s']
        with self.assertRaises(ValueError):validate(d,2)
        d={k:v[:1] for k,v in self.trace().items()}
        with self.assertRaises(ValueError):validate(d,2)
    def test_strict_decision(self):
        self.assertEqual(decision(1.1,.1,1),'UNRESOLVED')
        self.assertEqual(decision(1.2,.1,1),'MATERIAL')
        self.assertEqual(decision(.8,.1,1),'BELOW_BUDGET')
        self.assertEqual(decision(4,.21,1),'UNRESOLVED')
