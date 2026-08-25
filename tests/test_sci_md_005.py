import csv,json,math,tempfile,unittest
from pathlib import Path
from tools.inventory_scaled_composition import compose
from tools.sci_md_005.reduced import simulate

ROOT=Path(__file__).resolve().parents[1]
class CompositionTests(unittest.TestCase):
 def test_arbitrary_species_and_closure(self):
  value=compose(aggregate_history=[{'beverage_mass_kg':0,'cup_solute_mass_kg':0},{'beverage_mass_kg':.04,'cup_solute_mass_kg':.004}],inventories={'x':.01,'y':.02},dry_dose_kg=.02,fractions=[{'fraction_id':'f','lower_beverage_mass_kg':0,'upper_beverage_mass_kg':.04}],aggregate_inventory_fraction=.28,uncertainty={'inventory':'measured'})
  self.assertEqual(['x','y'],[r['species_id'] for r in value['species']]);self.assertEqual({'inventory':'measured'},value['uncertainty_components'])
 def test_frozen_h0_exact_reproduction(self):
  path=ROOT/'validation/sci_md_004_stage_e1_hydraulic_reconciliation/prediction_freeze/PREDICTIONS.csv'
  with path.open(newline='') as f: rows=list(csv.DictReader(f))
  idx={(r['sample_id'],r['hypothesis'],r['observable']):r for r in rows}
  mismatches=[]
  for sample in sorted({r['sample_id'] for r in rows}):
   total=idx[(sample,'H0','total_solids')]
   scenario=json.loads((ROOT/f'validation/sci_md_004_stage_e1_hydraulic_reconciliation/scenarios/{sample}-H0-reference.json').read_text())
   inv={x['id']:x['dry_coffee_inventory_mass_fraction'] for x in scenario['extraction']['species'] if x['id'] in {'caffeine','trigonelline'}}
   result=compose(aggregate_history=[{'beverage_mass_kg':0,'cup_solute_mass_kg':0},{'beverage_mass_kg':float(total['cup_water_mass_kg']),'cup_solute_mass_kg':float(total['cup_mass_kg'])}],inventories=inv,dry_dose_kg=scenario['coffee_bed']['dry_dose_kg'],fractions=[{'fraction_id':'all','lower_beverage_mass_kg':0,'upper_beverage_mass_kg':float(total['cup_water_mass_kg'])}],aggregate_inventory_fraction=.28)
   got={r['species_id']:r['species_cup_mass_kg'] for r in result['species']}
   for species in inv:mismatches.append(abs(got[species]-float(idx[(sample,'H0',species)]['cup_mass_kg'])))
   self.assertAlmostEqual(result['species'][0]['aggregate_total_solids_cup_mass_kg'],float(total['cup_mass_kg']),places=14)
  # This frozen incompatibility is the SCI-MD-005 data-contract blocker: a
  # single aggregate fraction cannot exactly reproduce the historical species.
  self.assertGreater(max(mismatches),1e-8)
class ReducedTests(unittest.TestCase):
 def test_conservation_nonnegative_and_inventory(self):
  r=simulate(flow_m3_s=1e-6,end_s=20,dose_kg=.02,inventory_fraction=.01,k_1_s=.08,csat_kg_m3=10,diffusivity_m2_s=1e-10,cells=32,dt_s=.05)
  self.assertLess(abs(r['conservation_residual_kg']),1e-8);self.assertGreaterEqual(r['remaining_inventory_kg'],0);self.assertGreaterEqual(r['cup_mass_kg'],0);self.assertLessEqual(r['remaining_inventory_kg'],r['initial_inventory_kg'])
 def test_replay(self):
  kw=dict(flow_m3_s=1e-6,end_s=2,dose_kg=.02,inventory_fraction=.01,k_1_s=.08,csat_kg_m3=10,diffusivity_m2_s=1e-10,cells=16,dt_s=.1)
  self.assertEqual(simulate(**kw),simulate(**kw))
if __name__=='__main__':unittest.main()
