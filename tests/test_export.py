"""Verificações do formato e do tempo; não testam a qualidade do modelo."""

import json
import unittest
from types import SimpleNamespace

from extract_pose import frame_record, timestamp_ms


class ExportTests(unittest.TestCase):
    def test_missing_pose_keeps_frame_and_time(self):
        result = SimpleNamespace(pose_landmarks=[], pose_world_landmarks=[])
        record = frame_record(result, frame_index=60, fps=30)
        self.assertEqual(record["frame_index"], 60)
        self.assertEqual(record["timestamp_ms"], 2000)
        self.assertFalse(record["pose_detected"])
        self.assertEqual(record["landmarks"], [])
        self.assertEqual(record["world_landmarks"], [])
        json.dumps(record, allow_nan=False)

    def test_raw_low_visibility_points_are_not_replaced_or_clipped(self):
        point = SimpleNamespace(x=1.1, y=-0.1, z=-0.4, visibility=0.1, presence=0.8)
        result = SimpleNamespace(pose_landmarks=[[point] * 33], pose_world_landmarks=[])
        record = frame_record(result, frame_index=0, fps=30)
        wrist = record["landmarks"][15]
        self.assertTrue(record["pose_detected"])
        self.assertEqual(wrist["name"], "left_wrist")
        self.assertEqual(wrist["x"], 1.1)
        self.assertEqual(wrist["y"], -0.1)
        self.assertEqual(wrist["visibility"], 0.1)

    def test_world_coordinates_are_separate_from_image_coordinates(self):
        image = SimpleNamespace(x=0.5, y=0.4, z=-0.1, visibility=0.9, presence=0.9)
        world = SimpleNamespace(x=0.2, y=-0.3, z=0.8, visibility=0.9, presence=0.9)
        result = SimpleNamespace(pose_landmarks=[[image] * 33], pose_world_landmarks=[[world] * 33])
        record = frame_record(result, frame_index=1, fps=30)
        self.assertEqual(record["landmarks"][15]["x"], 0.5)
        self.assertEqual(record["world_landmarks"][15]["x"], 0.2)

    def test_fractional_fps_does_not_accumulate_rounding_drift(self):
        self.assertEqual(timestamp_ms(30000, 30000 / 1001), 1001000)
        times = [timestamp_ms(i, 30000 / 1001) for i in range(100)]
        self.assertTrue(all(a < b for a, b in zip(times, times[1:])))

    def test_invalid_fps_is_rejected(self):
        for fps in (0, -1, float("nan"), float("inf"), 1001):
            with self.subTest(fps=fps), self.assertRaises(ValueError):
                timestamp_ms(0, fps)


if __name__ == "__main__":
    unittest.main()

