import csv
import json
from pathlib import Path
import tempfile
import unittest

from evaluate_classification import evaluate
from consolidate_evaluation import aggregate


class ClassificationEvaluationTests(unittest.TestCase):
    def test_abstentions_misses_hooks_and_classified_extras_stay_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pose = root / "pose"
            pose.mkdir()
            (pose / "pose.jsonl").write_text("\n".join(
                json.dumps(dict(frame_index=i, timestamp_ms=i * 1000)) for i in range(10)))
            candidates = [dict(candidate_id=f"c-{i}", frame_index=frame,
                               timestamp_ms=frame * 1000, status="returned_partly",
                               classification=label, classification_reason="test")
                          for i, (frame, label) in enumerate([
                              (1, "straight"), (3, "indeterminate"),
                              (5, "straight"), (9, "uppercut")])]
            candidate_file = root / "classifications.json"
            candidate_file.write_text(json.dumps(dict(
                pose_dir=str(pose), classification_performed=True, candidates=candidates)))
            with (root / "videos.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows([["video_id", "pose_dir"], ["example", str(pose)]])
            with (root / "events.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["event_id", "video_id", "peak_frame", "label"])
                for i, (frame, label) in enumerate([(1, "straight"), (3, "uppercut"),
                                                    (5, "hook"), (7, "uppercut")]):
                    writer.writerow([f"r-{i}", "example", frame, label])
            result = evaluate(candidate_file, "example", root / "events.csv")
        self.assertEqual(result["correct_temporal_family_pairs"], 1)
        self.assertEqual(result["wrong_temporal_family_pairs"], 1)
        self.assertEqual(result["matched_indeterminate_count"], 1)
        self.assertEqual(result["no_candidate_count"], 1)
        self.assertEqual(result["classified_unmatched_count"], 1)
        self.assertEqual(result["confusion"]["hook"]["straight"], 1)
        self.assertEqual(result["confusion"]["uppercut"]["indeterminate"], 1)
        self.assertEqual(result["confusion"]["uppercut"]["not_detected"], 1)
        self.assertEqual(sum(sum(row.values()) for row in result["confusion"].values()), 4)
        # Duas gravações: os hooks e extras contam contra a precisão;
        # abstenções e golpes sem candidato permanecem no denominador do recall.
        summary = aggregate([result, result])
        self.assertEqual(summary["num_references"], 8)
        self.assertEqual(summary["target_reference_count"], 6)
        self.assertEqual(summary["classified_count"], 6)
        self.assertEqual(summary["family_precision"], 2 / 6)
        self.assertEqual(summary["family_recall"], 2 / 6)
        self.assertEqual(summary["target_abstentions"], 2)
        self.assertEqual(summary["target_no_candidate"], 2)
        self.assertEqual(summary["classified_unmatched_count"], 2)

    def test_empty_aggregate_has_no_defined_rates(self):
        summary = aggregate([])
        self.assertEqual(summary["num_references"], 0)
        self.assertIsNone(summary["family_precision"])
        self.assertIsNone(summary["family_recall"])
        self.assertIsNone(summary["family_f1"])


if __name__ == "__main__":
    unittest.main()
