"""Geometria e alinhamento temporal; exemplos sintéticos não avaliam boxe."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from prepare_arm_features import arm_features, elbow_angle, prepare_features


class ArmFeaturesTests(unittest.TestCase):
    def test_angles_in_pixel_space_and_zero_segment(self):
        xy = np.full((4, 33, 2), .5)
        xy[:, 13] = [.5, .5]
        xy[:, 11] = [.75, .5]
        xy[:, 15] = [[.75, .5], [.5, .75], [.25, .5], [.5, .5]]
        angles = elbow_angle(xy, np.ones((4, 33)), 200, 100, (11, 13, 15))
        np.testing.assert_allclose(angles[:3], [0, 90, 180])
        self.assertTrue(np.isnan(angles[3]))
        # Numa imagem retangular, estes vetores fazem 90° em píxeis,
        # mas não quando calculados diretamente com x/y normalizados.
        xy[0, 11] = [.6, .7]  # (20, 20) px a partir do cotovelo.
        xy[0, 15] = [.4, .7]  # (-20, 20) px.
        self.assertAlmostEqual(elbow_angle(
            xy[:1], np.ones((1, 33)), 200, 100, (11, 13, 15),
        )[0], 90)

    def test_both_arms_and_separate_filters(self):
        xy = np.full((7, 33, 2), .5)
        xy[:, 15] = [.6, .7]
        xy[:, 13] = [.5, .6]
        xy[:, 16] = [.4, .3]
        xy[:, 14] = [.5, .4]
        visibility = np.ones((7, 33))
        visibility[0] = .5
        visibility[1, 13] = .49  # Só o ângulo esquerdo fica em falta.
        visibility[2, 16] = .49  # Vetor e ângulo direitos ficam em falta.
        xy[3] = np.nan
        xy[4, 12, 0] = 1  # Ombro direito fora da imagem.
        visibility[5, 11] = np.nan
        features = arm_features(xy, visibility, 200, 100)
        np.testing.assert_allclose(features["left_delta_x_px"][[0, 1, 2, 4, 6]], 20)
        np.testing.assert_allclose(features["right_delta_x_px"][[0, 1, 5, 6]], -20)
        np.testing.assert_allclose(features["right_delta_y_px"][[0, 1, 5, 6]], -20)
        self.assertTrue(np.isnan(features["left_elbow_angle_deg"][1]))
        self.assertTrue(np.isnan(features["left_distance_px"][5]))
        self.assertTrue(np.isnan(features["right_distance_px"][[2, 3, 4]]).all())
        self.assertTrue(np.isfinite(features["left_elbow_angle_deg"][[0, 6]]).all())
        for values in features.values():
            self.assertEqual(values.shape, (7,))
            self.assertTrue(np.isnan(values[3]))

    def test_original_frames_times_and_missing_pose(self):
        points = [{"x": .5, "y": .5, "visibility": 1} for _ in range(33)]
        points[13]["y"] = .6
        points[15]["x"] = .7
        records = [
            {"frame_index": 10, "timestamp_ms": 400,
             "pose_detected": True, "landmarks": points},
            {"frame_index": 11, "timestamp_ms": 437,
             "pose_detected": False, "landmarks": []},
            {"frame_index": 12, "timestamp_ms": 490,
             "pose_detected": True, "landmarks": points},
        ]
        metadata = {"status": "complete", "frames_processed": 3,
                    "width": 200, "height": 100, "draw_visibility_threshold": .5}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "metadata.json").write_text(json.dumps(metadata))
            (path / "pose.jsonl").write_text("\n".join(json.dumps(r) for r in records))
            frames, times, features, threshold = prepare_features(path)
            # Recusar tempos duplicados evita interpretar uma sequência inválida.
            records[2]["timestamp_ms"] = 437
            (path / "pose.jsonl").write_text("\n".join(json.dumps(r) for r in records))
            with self.assertRaises(ValueError):
                prepare_features(path)
        np.testing.assert_array_equal(frames, [10, 11, 12])
        np.testing.assert_array_equal(times, [400, 437, 490])
        self.assertEqual(threshold, .5)
        np.testing.assert_allclose(features["left_delta_x_px"][[0, 2]], 40)
        self.assertTrue(all(np.isnan(v[1]) for v in features.values()))


if __name__ == "__main__":
    unittest.main()
