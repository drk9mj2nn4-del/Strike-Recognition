import unittest

import numpy as np

from classify_motion_phases import PhaseConfig, duplicates_phase, phase_hypothesis, select_hypothesis


class MotionPhaseTests(unittest.TestCase):
    def geometry(self):
        frames = np.arange(10)
        times = frames * 40
        vectors = np.column_stack([np.linspace(20, 30, 10), [0, 20, 50, 80, 100, 80, 40, 0, -20, -10]])
        return frames, times, vectors, np.full(10, 60.), np.zeros((10, 2))

    def test_finds_preparation_and_ascent_instead_of_detector_onset(self):
        phase = phase_hypothesis(*self.geometry(), 100, 320, "left", PhaseConfig())
        self.assertEqual(phase["start_frame"], 4)
        self.assertEqual(phase["end_frame"], 8)
        self.assertEqual(phase["classification"], "uppercut")
        self.assertAlmostEqual(phase["features"]["vertical_rise_scale"], 1.2)

    def test_missing_endpoint_neighborhood_is_not_interpolated(self):
        frames, times, vectors, angles, elbows = self.geometry()
        vectors[7] = np.nan
        self.assertIsNone(phase_hypothesis(frames, times, vectors, angles, elbows,
                                          100, 320, "left", PhaseConfig()))

    def test_gap_in_lookback_does_not_supply_old_preparation(self):
        frames, times, vectors, angles, elbows = self.geometry()
        angles[5] = np.nan
        phase = phase_hypothesis(frames, times, vectors, angles, elbows,
                                100, 360, "left", PhaseConfig())
        # O frame 4 era o mais baixo, mas está separado por uma lacuna no 5.
        self.assertEqual(phase["start_frame"], 6)

    def test_two_comparable_conflicting_arms_abstain(self):
        a = dict(classification="straight", score=1., model_arm="left", reason="a")
        b = dict(classification="uppercut", score=.9, model_arm="right", reason="b")
        chosen, reason = select_hypothesis([a, b], PhaseConfig())
        self.assertIsNone(chosen)
        self.assertEqual(reason, "conflicting_arm_phases")
        b["score"] = .4
        self.assertEqual(select_hypothesis([b, a], PhaseConfig())[0], a)

    def test_overlapping_same_arm_episode_not_reused(self):
        previous = dict(model_arm="left", start_frame=106, end_frame=113, endpoint_ms=4520)
        phase = dict(model_arm="left", start_frame=109, end_frame=117, endpoint_ms=4680)
        self.assertTrue(duplicates_phase(phase, [previous], PhaseConfig()))
        self.assertFalse(duplicates_phase(dict(phase, model_arm="right"), [previous], PhaseConfig()))
        self.assertFalse(duplicates_phase(dict(phase, start_frame=114, end_frame=120),
                                         [previous], PhaseConfig()))


if __name__ == "__main__":
    unittest.main()
