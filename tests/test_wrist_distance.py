"""Verifica a geometria numa imagem retangular e preservação de lacunas."""

import unittest

import numpy as np

from analyze_wrist_distance import wrist_shoulder_distance, wrist_shoulder_vector


class WristDistanceTests(unittest.TestCase):
    def test_pixel_geometry_and_common_translation(self):
        xy = np.zeros((2, 33, 2))
        xy[0, 11] = [.1, .1]
        xy[0, 15] = [.13, .18]
        xy[1] = xy[0] + [.2, .3]
        # Imagem 100×50: separação (3, 4) píxeis => distância 5, em ambos os frames.
        distances = wrist_shoulder_distance(xy, np.ones((2, 33)), 100, 50)
        np.testing.assert_allclose(distances, [5, 5])
        vectors = wrist_shoulder_vector(xy, np.ones((2, 33)), 100, 50)
        np.testing.assert_allclose(vectors, [[3, 4], [3, 4]])

    def test_equal_lengths_keep_distinct_directions(self):
        xy = np.zeros((3, 33, 2))
        xy[:, 11] = [.5, .5]
        xy[:, 15] = [[.7, .5], [.5, .7], [.3, .5]]
        visibility = np.ones((3, 33))
        vectors = wrist_shoulder_vector(xy, visibility, 1000, 1000)
        np.testing.assert_allclose(vectors, [[200, 0], [0, 200], [-200, 0]])
        np.testing.assert_allclose(wrist_shoulder_distance(xy, visibility, 1000, 1000),
                                   [200, 200, 200])

    def test_filter_checks_both_endpoints_and_keeps_gaps(self):
        xy = np.zeros((7, 33, 2))
        xy[:, 11] = [.1, .1]
        xy[:, 15] = [.13, .18]
        visibility = np.ones((7, 33))
        visibility[0, [11, 15]] = .5  # O limiar é inclusivo.
        visibility[1, 11] = .49
        visibility[2, 15] = .49
        xy[3] = np.nan  # Frame sem pose.
        xy[4, 15, 0] = 1  # Fora da imagem; não recortar.
        visibility[5, 15] = np.nan
        distances = wrist_shoulder_distance(xy, visibility, 100, 50)
        self.assertEqual(distances.shape, (7,))
        np.testing.assert_allclose(distances[[0, 6]], [5, 5])
        self.assertTrue(np.isnan(distances[1:6]).all())
        vectors = wrist_shoulder_vector(xy, visibility, 100, 50)
        self.assertTrue(np.isnan(vectors[1:6]).all())
        np.testing.assert_allclose(vectors[[0, 6]], [[3, 4], [3, 4]])


if __name__ == "__main__":
    unittest.main()
