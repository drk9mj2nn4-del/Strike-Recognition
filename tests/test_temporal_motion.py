import unittest

import numpy as np

from temporal_motion import vector_velocity


class TemporalMotionTests(unittest.TestCase):
    def test_nonuniform_intervals_units_and_direction(self):
        velocity = vector_velocity([10, 11, 12], [400, 450, 550],
                                   [[0, 0], [3, 4], [1, 5]])
        self.assertTrue(np.isnan(velocity[0]).all())
        np.testing.assert_allclose(velocity[1:], [[60, 80], [-20, 10]])
        self.assertAlmostEqual(np.linalg.norm(velocity[1]), 100)

    def test_missing_points_and_missing_frames_are_not_bridged(self):
        velocity = vector_velocity([0, 1, 2, 4, 5], [0, 40, 80, 160, 200],
                                   [[0, 0], [np.nan, np.nan], [2, 2], [4, 4], [5, 5]])
        self.assertTrue(np.isnan(velocity[:4]).all())
        np.testing.assert_allclose(velocity[4], [25, 25])

    def test_bad_times_are_rejected(self):
        for times in [[0, 0], [40, 0], [0, np.nan]]:
            with self.assertRaises(ValueError):
                vector_velocity([0, 1], times, [[0, 0], [1, 1]])


if __name__ == "__main__":
    unittest.main()
