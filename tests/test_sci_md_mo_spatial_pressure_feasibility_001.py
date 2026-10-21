"""Focused mathematical, hydraulic and domain controls; no empirical data."""
import unittest

import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad

from tools.sci_md_mo_spatial_pressure_feasibility_001.analyze import (
    aperture_rate, erosion, hydraulics, integrate, positive_linear_mean,
)


class SpatialPressureControls(unittest.TestCase):
    def test_slit_bridge_symmetry_and_passivity(self):
        h = hydraulics(np.ones(5), 3)
        assert_allclose(h["p"], [3, 1.5, 1.5, 0])
        self.assertEqual(h["K"], 1)
        self.assertEqual(h["q"][4], 0)
        for x in [np.array([.2, .7, .5, .1, .4]), np.ones(5)]:
            h = hydraulics(x, 2)
            h2 = hydraulics(x, 2, independent=True)
            assert_allclose(h["p"], h2["p"], atol=1e-14)
            q = h["q"]
            assert_allclose([q[0]-q[1]-q[4], q[2]-q[3]+q[4]], 0, atol=1e-14)
            assert_allclose(h["Qin"], h["Qout"], atol=1e-14)
            assert_allclose(2*h["Qin"], np.dot(h["g"], h["dp"]**2), atol=1e-14)
            for j in range(5):
                opened = x.copy()
                opened[j] += .1
                self.assertGreaterEqual(hydraulics(opened, 2)["K"] + 1e-14, h["K"])

    def test_threshold_integration_not_threshold_of_mean(self):
        for left, right in [(-3, 1), (1, -3), (2, 4), (-1, -2), (0, 0)]:
            actual = positive_linear_mean(np.array([left]), np.array([right]))[0]
            root = left/(left-right) if left != right else -1
            expected = quad(lambda s: max(left+(right-left)*s, 0), 0, 1,
                            points=[root] if 0 < root < 1 else None)[0]
            self.assertAlmostEqual(actual, expected, places=14)
        self.assertEqual(positive_linear_mean(np.array([-3.]), np.array([1.]))[0], .125)

    def test_fixed_full_state_pressure_monotonicity(self):
        rng = np.random.default_rng(9)
        for _ in range(40):
            x0 = rng.uniform(.1, 1, 5)
            x = rng.uniform(x0, 2)
            gamma, beta = rng.uniform(.01, .5), rng.uniform(0, 4)
            rates = [aperture_rate(x, x0, p, gamma, beta) for p in [.1, 1, 2, 3]]
            self.assertGreaterEqual(np.min(np.diff(rates, axis=0)), -1e-14)
            assert_allclose(erosion(x, 2, gamma, beta),
                            erosion(x, 2, gamma, beta, True), atol=2e-14)

    def test_active_and_inactive_domains(self):
        x = np.full(5, .5)
        self.assertGreater(erosion(x, 1, .1, 4)[1], 0)
        self.assertAlmostEqual(erosion(x, 1, .1, 4)[1], .005625, places=14)
        assert_allclose(erosion(x, 3, 6, 0), 0)
        c = {"x0": x, "gamma": 6., "beta": 1.}
        sol = integrate(c, 3, times=np.linspace(0, 2, 9))
        assert_allclose(sol["x"], np.tile(x, (9, 1)), atol=0)

    def test_homogeneous_common_orbit_and_inventory(self):
        c = {"x0": [.2, .6, .7, .3, .4], "gamma": 0., "beta": .3}
        low = integrate(c, 1, times=np.linspace(0, 4, 65), rtol=1e-11, atol=1e-13)
        high = integrate(c, 2, times=np.linspace(0, 2, 65), rtol=1e-11, atol=1e-13)
        assert_allclose(low["x"], high["x"], atol=2e-9, rtol=2e-9)
        assert_allclose(high["Q"], 2*low["Q"], atol=2e-9, rtol=2e-9)
        self.assertLess(low["solid_balance_error"], 1e-14)
        self.assertGreaterEqual(low["min_dQ"], -1e-12)

    def test_finite_threshold_not_cooperative_or_common_orbit(self):
        x = np.array([1., 1., 1., .5, 1.])
        f1 = erosion(x, 1, .1, 0)
        f2 = erosion(x, 2, .1, 0)
        self.assertGreater(abs(f1[0]*f2[1]-f1[1]*f2[0]), 1e-4)
        opened = x.copy()
        opened[3] += 1e-5
        self.assertLess(erosion(opened, 1, .1, 0)[1], f1[1])

    def test_symmetric_scalar_order(self):
        c = {"x0": [.5]*5, "gamma": .1, "beta": 0.}
        low = integrate(c, 1, times=np.linspace(0, 2, 33))
        high = integrate(c, 2, times=np.linspace(0, 2, 33))
        assert_allclose(low["x"][:, 0], low["x"][:, 1], atol=1e-12)
        assert_allclose(low["x"][:, 0], low["x"][:, 2], atol=1e-12)
        assert_allclose(low["x"][:, 4], .5, atol=1e-12)
        self.assertTrue(np.all(high["Q"] >= low["Q"]))


if __name__ == "__main__":
    unittest.main()
