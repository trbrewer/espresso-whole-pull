"""Synthetic geometric/observation tests; zero native solver calls."""
import unittest
from unittest.mock import patch
import numpy as np
from tools.sci_md_radial_obs_001.observe import annular_weights,integrate,scenario_masses
from tools.sci_md_rheology_010.sections import section_weights, inventories

class RadialObservationTests(unittest.TestCase):
    def test_historical_three_region_parity(self):
        lo=np.array([0,.0145]);hi=np.array([.0145,.029]);cuts=[0,.018,.025,.029]
        w=annular_weights(lo,hi,cuts)
        np.testing.assert_array_equal(w,section_weights(lo,hi))
        v=np.pi*(hi**2-lo**2)*.009
        fields=[np.array([100.,60.]),np.array([70.,20.]),np.full(2,.4),np.ones(2)]
        new,closure=integrate(v,w,*fields,.02,.0056,965)
        old=inventories(v,w,*fields)['sections']
        for x,y in zip(new,old.values()):
            self.assertAlmostEqual(x['remaining_solid_soluble_kg'],y['remaining_solid_solubles_kg'],places=15)
            self.assertAlmostEqual(x['retained_dissolved_solute_kg'],y['retained_dissolved_solute_kg'],places=15)
        self.assertLess(max(abs(x) for x in closure.values()),1e-12)

    def test_partial_cells_conserve_unequal_mass(self):
        lo=np.array([0,.5]);hi=np.array([.5,1.]);v=(hi**2-lo**2)*1e-5
        for q in (.31,.34):
            w=annular_weights(lo,hi,[0,np.sqrt(1-q),1])
            sections,closure=integrate(v,w,[100,100],[40,40],[.4,.4],[1,1],.02,.0056,965)
            self.assertAlmostEqual(sections[1]['initial_dry_coffee_kg'],q*.02)
            self.assertAlmostEqual(sum(x['remaining_solid_soluble_kg'] for x in sections),.001)
            self.assertAlmostEqual(sum(x['retained_dissolved_solute_kg'] for x in sections),.00016)
            self.assertAlmostEqual(sum(x['retained_solvent_kg'] for x in sections),965*.4e-5)
            self.assertTrue(0<w[1,1]<1)

    def test_e2_unresolved_subcell_constant(self):
        w=annular_weights([0,.5],[.5,1],[0,.8,.9,1])
        values=w@np.array([.25*10,.75*20])/(w@np.array([.25,.75]))
        self.assertAlmostEqual(values[1],values[2],places=13)

    def test_invalid_missing(self):
        for cuts in ([0,.5,.4,1],[0,.9],[0,float('nan'),1]):
            with self.assertRaises(ValueError):annular_weights([0,.5],[.5,1],cuts)
        with self.assertRaises(ValueError):integrate([1],[[1]],[None],[0],[.4],[1],.02,.0056,965)
        with self.assertRaises(ValueError):integrate([1],[[1]],[0],[0],[.4],[1],.02,.0056,-1)

    def test_derived_binary64_initial_inventory(self):
        # The source inputs are exact declarations; their floating product need
        # not equal the literal .0056 bit-for-bit. Physical checks retain limits.
        scenario={'coffee_bed':{'dry_dose_kg':.020,'initial_extractable_fraction_dry_basis':.28},'liquid':{'density_kg_m3':965.}}
        dose,initial,rho=scenario_masses(scenario)
        self.assertEqual(initial,dose*.28)
        for group,key,bad in [('coffee_bed','dry_dose_kg',.021),('coffee_bed','initial_extractable_fraction_dry_basis',.29),('liquid','density_kg_m3',1000.)]:
            previous=scenario[group][key];scenario[group][key]=bad
            with self.assertRaises(ValueError):scenario_masses(scenario)
            scenario[group][key]=previous
        rows,_=integrate([1e-5],[[.7],[.3]],[100],[40],[.4],[1],.020,initial,965.)
        self.assertAlmostEqual(sum(r['initial_model_soluble_kg'] for r in rows),.0056,places=15)

    def test_no_native_execution(self):
        with patch('subprocess.run',side_effect=AssertionError('native execution forbidden')),patch('subprocess.Popen',side_effect=AssertionError('native execution forbidden')):
            w=annular_weights([0],[1],[0,.8,1])
            integrate([1e-5],w,[100],[40],[.4],[1],.02,.0056,965)

if __name__=='__main__':unittest.main()
