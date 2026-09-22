"""History admission, clocks, support and inherited observer mutation coverage."""
import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scripts.aggregate_viscosity import contract
from tools.sci_md_rheology_002.export import HEADER
from tools.sci_md_rheology_009.common import history, radial, matrix, support, pressure_audit


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.table=Path(self.tmp.name)/'constant.table';self.table.write_text(HEADER+'0 .001\n.1 .001\n.24 .001\n')
    def spec(self):
        s=history(radial(),'UP');s['aggregate_viscosity']=dict(mode='coupled',table=str(self.table));return s
    def test_new_and_legacy_admission(self):
        for mode in ('observe','coupled'):
            s=self.spec();s['aggregate_viscosity']['mode']=mode;self.assertIn(mode,contract(s))
            old=radial();old['aggregate_viscosity']=s['aggregate_viscosity'];self.assertIn(mode,contract(old))
        s=self.spec();s['aggregate_viscosity']['mode']='off';self.assertEqual(contract(s),'')
    def test_rejections(self):
        mutations=[lambda s:s['aggregate_viscosity'].update(mode='bulkCoupled'),lambda s:s.update(bedMechanicsModel='poroelastic'),lambda s:s.update(flowResistanceModel='darcyForchheimer'),lambda s:s.update(effective_permeability_evolution={}),lambda s:s['time'].update(start_s=.1),lambda s:s['wetting'].update(initial_saturation=.5),lambda s:s['wetting'].update(initial_wet_front_m=0),lambda s:s['hydraulics']['permeability_profile'].update(type='uniform'),lambda s:s['hydraulics'].update(pressure_boundary_model='prescribedFlow'),lambda s:s['liquid'].update(density_kg_m3=1000),lambda s:s['extraction'].update(model='indexed')]
        for mutate in mutations:
            s=self.spec();mutate(s)
            with self.assertRaises((ValueError,SystemExit)):contract(s)
    def test_schedule_validation(self):
        for times,pressures in [([0,1,1,30],[3e5]*4),([0,15,30],[3e5]*4),([0,14.5,float('nan'),30],[3e5]*4),([0,14.5,15.5,29],[3e5]*4),([0,14.5,15.5,30],[3e5,0,9e5,9e5]),([0,14.5,15.5,30],[3e5,float('inf'),9e5,9e5])]:
            s=self.spec();s['hydraulics']['prescribed_pressure_boundary'].update(times_s=times,pressures_gauge_Pa=pressures)
            with self.assertRaises((ValueError,SystemExit)):contract(s)
        for key in ('target_inlet_pressure_gauge_Pa','pressure_ramp_time_s'):
            s=self.spec();s['hydraulics'][key]=0
            with self.assertRaises(SystemExit):contract(s)
    def test_reference_only_support(self):
        c={k:'0.01234567891' for k,v in matrix().items() if v['model']=='C'}
        self.assertEqual(support(c),dict(UP='0.011728394',DOWN='0.011728394'))
        for bad in [dict(c,E2='0.001'),dict(list(c.items())[1:])]:
            with self.assertRaises(ValueError):support(bad)
    def test_pressure_clock_mutations(self):
        s=history(radial(),'UP',True)
        raw=dict(start_s=np.array([0.,.02]),state_s=np.array([0.,.02]),end_s=np.array([.02,.04]))
        t=dict(time_s=raw['end_s'].copy(),inlet_pressure_Pa=np.array([3e5,3e5]))
        pressure_audit(raw,t,s)
        for key in ('time_s','inlet_pressure_Pa'):
            bad=copy.deepcopy(t);bad[key][1]=bad[key][0] if key=='time_s' else 4e5
            with self.assertRaises(ValueError):pressure_audit(raw,bad,s)
        bad=copy.deepcopy(raw);bad['state_s']=raw['end_s']
        with self.assertRaises(ValueError):pressure_audit(bad,t,s)
        raw=dict(start_s=np.array([.06]),state_s=np.array([.06]),end_s=np.array([.08]))
        t=dict(time_s=raw['end_s'],inlet_pressure_Pa=np.array([364285.7142857143]))
        with self.assertRaises(ValueError):pressure_audit(raw,t,s)
if __name__=='__main__':unittest.main()
