import unittest

import numpy as np

from detect_candidates import CandidateConfig, arm_candidates, suppress_nearby


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.config = CandidateConfig(min_excursion_px=50, min_prominence_px=40,
                                      min_speed_px_s=500, context_s=.25)

    def test_out_and_partial_return_without_full_guard(self):
        # A mediana é zero; o pico em 4 tem subida rápida e descida parcial.
        vectors = np.column_stack([[0, 0, 0, 50, 100, 60, 50, 0, 0, 0, 0], np.zeros(11)])
        events, reference, _, _ = arm_candidates(
            np.arange(11), np.arange(11) * 40, vectors, "left", self.config,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["frame_index"], 4)
        self.assertEqual(events[0]["status"], "returned_partly")
        np.testing.assert_allclose(reference, [0, 0])

    def test_missing_observation_does_not_supply_a_return(self):
        vectors = np.column_stack([[0, 0, 0, 0, 50, 100, np.nan, 0, 0], np.zeros(9)])
        events, _, _, velocity = arm_candidates(
            np.arange(9), np.arange(9) * 40, vectors, "left", self.config,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "unconfirmed_end")
        self.assertIsNone(events[0]["recovery_frame"])
        self.assertTrue(np.isnan(velocity[6:8]).all())

    def test_small_movement_rejected_and_unobserved_end_marked(self):
        frames = np.arange(7)
        for values, count in [([0, 0, 0, 10, 20, 0, 0], 0),
                              ([0, 0, 0, 0, 0, 50, 100], 1)]:
            vectors = np.column_stack([values, np.zeros(7)])
            events, _, _, _ = arm_candidates(frames, frames * 40, vectors, "left", self.config)
            self.assertEqual(len(events), count)
            if events:
                self.assertEqual(events[0]["frame_index"], 6)
                self.assertEqual(events[0]["status"], "unconfirmed_end")

    def test_two_arms_nearby_not_counted_twice(self):
        events = [dict(timestamp_ms=400, prominence_px=100, model_arm="left"),
                  dict(timestamp_ms=440, prominence_px=150, model_arm="right"),
                  dict(timestamp_ms=700, prominence_px=100, model_arm="left")]
        result = suppress_nearby(events, .16)
        self.assertEqual([e["timestamp_ms"] for e in result], [440, 700])
        self.assertNotIn("candidate_id", events[0])

    def test_all_missing_and_frame_jump_do_not_invent_movement(self):
        events, reference, _, _ = arm_candidates(
            np.arange(4), np.arange(4) * 40, np.full((4, 2), np.nan), "left", self.config,
        )
        self.assertEqual(events, [])
        self.assertTrue(np.isnan(reference).all())
        events, _, _, _ = arm_candidates(
            np.array([0, 1, 2, 10, 11, 12]), np.array([0, 40, 80, 400, 440, 480]),
            np.array([[0, 0], [0, 0], [0, 0], [100, 0], [100, 0], [100, 0]]),
            "left", self.config,
        )
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
