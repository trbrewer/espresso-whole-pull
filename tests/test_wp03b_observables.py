import math
import unittest
from dataclasses import replace
from tools.reference.wp03b.observables import *


class TestObservables(unittest.TestCase):
    def tds(self, method="REFRACTOMETRIC", basis="MASS"):
        return TDSMeasurement(method, "A", "B", basis, .001, "synthetic",
            589, 293.15, "RECORDED", "water", "sucrose", "ICUMSA",
            "UNDILUTED", "FILTERED", "FRESH")

    def observation(self):
        return RetainedLiquidDryingObservation(
            .018, .3, .25, .06, .016, .0002, .02,
            .0001, .0002, .0003, .0004, .0005, .0006, .0007)

    def test_jacobian_uncertainties(self):
        o = self.observation(); result = drying_kernel(o)
        retained = o.wet_spent_grounds_kg-o.dry_spent_grounds_kg
        expected = math.sqrt(
            o.dry_dose_uncertainty_kg**2+
            o.volatile_loss_uncertainty_kg**2+
            o.retained_liquid_tds_mass_fraction**2*o.wet_spent_uncertainty_kg**2+
            (1+o.retained_liquid_tds_mass_fraction)**2*o.dry_spent_uncertainty_kg**2+
            retained**2*o.retained_liquid_tds_uncertainty**2)
        self.assertAlmostEqual(result["corrected_extracted_uncertainty_kg"],
                               expected)
        self.assertAlmostEqual(result["retained_liquid_uncertainty_kg"],
            math.hypot(o.wet_spent_uncertainty_kg,
                       o.dry_spent_uncertainty_kg))
        self.assertGreater(result["water_balance_uncertainty_kg"], 0)

    def test_method_merge_rejected_by_sensitive_fields(self):
        with self.assertRaises(ValueError):
            assert_compatible(self.tds(), replace(self.tds(), calibrant="other"))
        with self.assertRaises(ValueError):
            assert_compatible(self.tds(), self.tds("GRAVIMETRIC_DRY_DOWN"))

    def test_metadata_and_density(self):
        with self.assertRaises(ValueError): self.tds("UNKNOWN")
        with self.assertRaises(ValueError):
            EYConvention("BEVERAGE_TDS_TIMES_BEVERAGE_MASS_OVER_DRY_DOSE",
                "REFRACTOMETRIC", "VOLUME", None, "dry", False, False,
                "none", "rss")
        with self.assertRaises(ValueError):
            EYConvention("X", "REFRACTOMETRIC", "MASS", None, "dry",
                         False, False, "none", "rss")

    def test_refractometric_metadata_required(self):
        with self.assertRaises(ValueError):
            TDSMeasurement("REFRACTOMETRIC", "A", "B", "MASS", .1, "scope")
        for field in ("optical_wavelength_nm", "freeze_thaw_status",
                      "sample_temperature_K", "calibrant"):
            with self.assertRaises(ValueError):
                TDSMeasurement(**dict(self.tds().__dict__, **{field: None}))

    def test_output_specific_negative_inventory(self):
        with self.assertRaises(ValueError):
            drying_kernel(replace(self.observation(),
                                  dry_spent_grounds_kg=.2))
        with self.assertRaises(ValueError):
            RetainedLiquidDryingObservation(-1,1,1,1,1,0,0,0)


if __name__ == "__main__":
    unittest.main()
