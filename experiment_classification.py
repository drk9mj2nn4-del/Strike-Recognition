"""Compara seis variantes determinísticas no desenvolvimento, sem mudar o matching."""

import argparse
import csv
from dataclasses import replace
import json
from pathlib import Path

from classify_candidates import ClassificationConfig, classify
from classify_motion_phases import classify_phases
from evaluate_classification import evaluate


def variants():
    baseline = ClassificationConfig()
    angles = replace(baseline, straight_min_angle_deg=60, straight_min_opening_deg=20,
                     upper_max_angle_deg=100, upper_max_opening_deg=30,
                     upper_min_preparation_angle_deg=35)
    relaxed = replace(angles, min_motion_scale=.1, straight_min_radial_gain_scale=.08,
                      straight_min_linearity=.5, straight_max_elbow_motion_ratio=1.8,
                      upper_min_rise_scale=.18, upper_min_upward_fraction=.7,
                      upper_max_over_shoulder_offset_scale=.25)
    return {
        "baseline_v1": lambda d: classify(d, baseline),
        "relax_angles": lambda d: classify(d, angles),
        "relax_all": lambda d: classify(d, relaxed),
        "phases_only": lambda d: classify_phases(d, preserve_strict=False, deduplicate=False),
        "phases_keep_strict": lambda d: classify_phases(d, deduplicate=False),
        "phases_keep_strict_dedup_v2": lambda d: classify_phases(d),
    }


def main(output_dir):
    output_dir = Path(output_dir)
    inputs = {name: json.loads(Path(f"outputs/step4/{name}-candidates/candidates.json").read_text())
              for name in ("front-view", "upper-body")}
    summaries, per_video = [], []
    for variant, run in variants().items():
        totals = dict(variant=variant, correct=0, wrong_family=0, classified_extra=0,
                      indeterminate_candidates=0, no_candidate=0, references=0,
                      target_references=0, candidates=0)
        for name, source in inputs.items():
            folder = output_dir / variant / name
            folder.mkdir(parents=True, exist_ok=True)
            document = run(source)
            document["experiment_variant"] = variant
            path = folder / "classifications.json"
            path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
            result = evaluate(path, "shbx-" + name, Path("annotations/events.csv"))
            (folder / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
            row = dict(variant=variant, video=name,
                       correct=result["correct_temporal_family_pairs"],
                       wrong_family=result["wrong_temporal_family_pairs"],
                       classified_extra=result["classified_unmatched_count"],
                       indeterminate_candidates=result["prediction_counts"].get("indeterminate", 0),
                       no_candidate=result["no_candidate_count"], references=result["num_references"],
                       target_references=result["target_reference_count"], candidates=result["num_candidates"])
            per_video.append(row)
            for key in totals:
                if key != "variant":
                    totals[key] += row[key]
        summaries.append(totals)
        print(totals)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(dict(
        scope="development_only", tolerance_ms=125, candidate_timestamps_preserved=True,
        parameter_search="six_explicit_variants; manual exploratory selection on both videos",
        totals=summaries, per_video=per_video), indent=2) + "\n")
    for name, rows in [("summary", summaries), ("per-video", per_video)]:
        with (output_dir / f"{name}.csv").open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    lines = ["# Experiências de classificação — desenvolvimento", "",
             "Mesmos 41 candidatos, timestamps, 33 referências, matching 1:1 e tolerância ±125 ms.",
             "29 referências são direto/uppercut; os quatro hooks permanecem fora do âmbito.",
             "Os dois vídeos foram explorados para escolher os perfis e parâmetros; não há teste independente.", "",
             "| Variante | Tempo/família concordantes | Família discordante | Sem referência, mas classificado | Candidatos indeterminados | Sem candidato |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in summaries:
        lines.append(f"| {r['variant']} | {r['correct']} | {r['wrong_family']} | "
                     f"{r['classified_extra']} | {r['indeterminate_candidates']} | {r['no_candidate']} |")
    lines += ["", "A v2 conserva decisões estritas da v1 e procura fases nos dois braços para os restantes.",
              "A proteção contra reutilizar a mesma fase reduz duplicações e classificações do golpe vizinho.",
              "Não foram alterados rótulos, reservadas amostras de teste ou retocados timestamps para pontuar melhor."]
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/step4/classification-experiments"))
    main(parser.parse_args().output_dir)
