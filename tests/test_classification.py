import unittest

import numpy as np

from classify_candidates import ClassificationConfig, decide, summarize_window


class ClassificationTests(unittest.TestCase):
    def summary(self, vectors, angles, elbows=None, scale=100):
        vectors = np.array(vectors, dtype=float)
        if elbows is None:
            elbows = np.zeros(vectors.shape)
        return summarize_window(np.arange(len(vectors)), np.arange(len(vectors)) * 40,
                                vectors, np.array(angles), np.array(elbows), scale)

    def test_extension_with_opening_is_straight(self):
        summary = self.summary([[20, 0], [40, -5], [80, -10]], [30, 60, 120])
        label, _ = decide(summary, "returned_partly", ClassificationConfig())
        self.assertEqual(label, "straight")

    def test_rise_with_bent_elbow_is_uppercut(self):
        summary = self.summary([[10, 50], [20, 20], [30, -20]], [70, 65, 60])
        label, _ = decide(summary, "returned_partly", ClassificationConfig())
        self.assertEqual(label, "uppercut")

    def test_descending_preparation_and_unobserved_return_abstain(self):
        summary = self.summary([[20, 0], [50, 30], [80, 80]], [30, 60, 120])
        self.assertEqual(decide(summary, "returned_partly", ClassificationConfig())[0], "indeterminate")
        rising = self.summary([[10, 50], [20, 20], [30, -20]], [70, 65, 60])
        self.assertEqual(decide(rising, "unconfirmed_end", ClassificationConfig())[0], "indeterminate")

    def test_pixel_scaling_does_not_change_normalized_evidence(self):
        vectors = np.array([[20, 0], [40, -5], [80, -10]], dtype=float)
        a = self.summary(vectors, [30, 60, 120])
        b = self.summary(vectors * 3, [30, 60, 120], scale=300)
        for key in ["net_motion_scale", "radial_gain_scale", "linearity", "upward_fraction"]:
            self.assertAlmostEqual(a[key], b[key])
        self.assertEqual(decide(a, "returned_partly", ClassificationConfig()),
                         decide(b, "returned_partly", ClassificationConfig()))

    def test_missing_pose_or_discontinuous_window_abstains(self):
        vectors = np.array([[20, 0], [40, -5], [80, -10]], dtype=float)
        for frames, angles in [(np.array([0, 1, 3]), np.array([30, 60, 120])),
                               (np.array([0, 1, 2]), np.array([30, np.nan, 120]))]:
            summary = summarize_window(frames, np.array([0, 40, 120]), vectors,
                                       angles, np.zeros((3, 2)), 100)
            self.assertIsNone(summary)
            self.assertEqual(decide(summary, "returned_partly", ClassificationConfig())[0], "indeterminate")


if __name__ == "__main__":
    unittest.main()
