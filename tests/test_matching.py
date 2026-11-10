import unittest

from compare_candidates import match_times


class MatchingTests(unittest.TestCase):
    def test_duplicates_are_not_extra_true_positives(self):
        self.assertEqual(match_times([90, 101], [100], 20), [(1, 0)])

    def test_maximizes_cardinality_before_minimizing_error(self):
        # Escolher o par exato 100→100 primeiro perderia o segundo par possível.
        self.assertEqual(match_times([0, 100], [100, 200], 100), [(0, 0), (1, 1)])

    def test_original_indices_empty_sets_and_boundary(self):
        self.assertEqual(match_times([300, 100], [110, 310], 10), [(1, 0), (0, 1)])
        self.assertEqual(match_times([], [100], 10), [])
        self.assertEqual(match_times([100], [], 10), [])
        self.assertEqual(match_times([0], [11], 10), [])


if __name__ == "__main__":
    unittest.main()
