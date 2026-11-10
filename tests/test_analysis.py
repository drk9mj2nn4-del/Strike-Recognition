"""Regressão: uma ausência não pode deslocar os pontos ou apagar tempo."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from analyze_pose import load_pose


class AnalysisTests(unittest.TestCase):
    def test_missing_pose_preserves_time_and_later_coordinates(self):
        # Tempos não uniformes para detetar uma reconstrução indevida por FPS.
        points = [{"x": 1.1, "y": -0.1, "visibility": 0.1} for _ in range(33)]
        records = [
            {"frame_index": 10, "timestamp_ms": 400,
             "pose_detected": True, "landmarks": points},
            {"frame_index": 11, "timestamp_ms": 437,
             "pose_detected": False, "landmarks": []},
            {"frame_index": 12, "timestamp_ms": 490,
             "pose_detected": True, "landmarks": points},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pose.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
            frames, timestamps, xy = load_pose(path)

        np.testing.assert_array_equal(frames, [10, 11, 12])
        np.testing.assert_array_equal(timestamps, [400, 437, 490])
        self.assertEqual(xy.shape, (3, 33, 2))
        self.assertTrue(np.isnan(xy[1]).all())
        # Nem recorte para [0, 1] nem eliminação de pontos pouco visíveis.
        np.testing.assert_array_equal(xy[0, 15], [1.1, -0.1])
        np.testing.assert_array_equal(xy[2, 15], [1.1, -0.1])


if __name__ == "__main__":
    unittest.main()
