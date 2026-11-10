"""Consolida o piloto de desenvolvimento sem executar ou ajustar o classificador."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from compare_candidates import compare
from evaluate_classification import evaluate, PREDICTIONS, REFERENCES


VIDEOS = {"shbx-front-view": "front-view", "shbx-upper-body": "upper-body"}
TOLERANCES = (50, 100, 125, 167, 200)
NOMINAL_MS = 125
TARGETS = ("straight", "uppercut")


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def aggregate(results):
    """Contagens micro: inclui abstenções, referências perdidas e extras."""
    matrix = {r: {p: 0 for p in PREDICTIONS + ["not_detected"]} for r in REFERENCES}
    predictions = Counter()
    for result in results:
        predictions.update(result["prediction_counts"])
        for label, row in result["confusion"].items():
            for prediction, count in row.items():
                matrix[label][prediction] += count
    correct = sum(matrix[label][label] for label in TARGETS)
    target_count = sum(sum(matrix[label].values()) for label in TARGETS)
    assigned = sum(predictions[label] for label in TARGETS)
    refs = sum(sum(row.values()) for row in matrix.values())
    missing = sum(row["not_detected"] for row in matrix.values())
    matched = refs - missing
    count = sum(predictions.values())
    precision, recall = ratio(correct, assigned), ratio(correct, target_count)
    return dict(
        num_candidates=count, num_references=refs, target_reference_count=target_count,
        prediction_counts=dict(predictions), confusion=matrix,
        temporal_pairs=matched, unmatched_candidate_count=count - matched,
        no_candidate_count=missing,
        correct_temporal_family_pairs=correct,
        wrong_temporal_family_pairs=sum(r["wrong_temporal_family_pairs"] for r in results),
        matched_indeterminate_count=sum(row["indeterminate"] for row in matrix.values()),
        target_abstentions=sum(matrix[label]["indeterminate"] for label in TARGETS),
        target_no_candidate=sum(matrix[label]["not_detected"] for label in TARGETS),
        classified_unmatched_count=sum(r["classified_unmatched_count"] for r in results),
        classified_count=assigned, temporal_precision=ratio(matched, count),
        temporal_recall=ratio(matched, refs),
        family_precision=precision, family_recall=recall,
        family_f1=ratio(2 * correct, assigned + target_count),
    )


def consolidate(output_dir):
    annotations = Path("annotations/events.csv")
    paths = {vid: Path(f"outputs/step4/{stem}-classification-v2/classifications.json")
             for vid, stem in VIDEOS.items()}
    # Identifica exatamente código e dados usados, incluindo os timestamps originais.
    inputs = {annotations, Path("annotations/videos.csv"), Path(__file__),
              Path("evaluate_classification.py"), Path("compare_candidates.py"),
              Path("classify_candidates.py"), Path("classify_motion_phases.py"),
              Path("detect_candidates.py"), Path("temporal_motion.py"),
              Path("prepare_arm_features.py"), Path("analyze_pose.py")}
    documents = {vid: json.loads(path.read_text()) for vid, path in paths.items()}
    for vid, document in documents.items():
        inputs.update((paths[vid], Path(document["pose_dir"]) / "pose.jsonl",
                       Path(document["pose_dir"]) / "metadata.json"))
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)}
    runs = []
    for tolerance in TOLERANCES:
        results = [evaluate(path, vid, annotations, tolerance) for vid, path in paths.items()]
        runs.append(dict(tolerance_ms=tolerance, summary=aggregate(results), videos=results))
    nominal = next(run for run in runs if run["tolerance_ms"] == NOMINAL_MS)
    # O consolidado deve reproduzir integralmente os relatórios v2 preservados.
    for result in nominal["videos"]:
        saved = json.loads((paths[result["video_id"]].parent / "classification-evaluation.json").read_text())
        if result != saved:
            raise ValueError(f"Avaliação nominal diverge do relatório preservado: {result['video_id']}")
    negatives = {vid: compare(path, vid, annotations)["negative_peak_candidates"]
                 for vid, path in paths.items()}
    v1 = aggregate([evaluate(f"outputs/step4/{stem}-classification/classifications.json",
                            vid, annotations, NOMINAL_MS) for vid, stem in VIDEOS.items()])
    for stem in VIDEOS.values():
        path = Path(f"outputs/step4/{stem}-classification/classifications.json")
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = dict(scope="development_only", independent_test=False, hand_scored=False,
                  nominal_tolerance_ms=NOMINAL_MS,
                  matching="one_to_one_maximum_count_then_minimum_absolute_error_without_labels",
                  tolerances=runs, v1_nominal=v1, explicit_negative_intervals=negatives,
                  input_sha256=hashes,
                  caveat="Retrospective development diagnostic; temporal pairs do not validate physical phase or arm.")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    with (output_dir / "references.csv").open("w", newline="") as file:
        rows = [dict(video_id=r["video_id"], **row)
                for r in nominal["videos"] for row in r["reference_rows"]]
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output_dir / "sensitivity.csv").open("w", newline="") as file:
        rows = [dict(tolerance_ms=run["tolerance_ms"], **{
            k: v for k, v in run["summary"].items() if not isinstance(v, dict)}) for run in runs]
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    s = nominal["summary"]
    lines = ["# Avaliação piloto v2 — desenvolvimento", "",
             "Gerado por `consolidate_evaluation.py`; regras e previsões preservadas.",
             "Matching temporal 1:1 sem usar família/mão. ±125 ms é a referência histórica,",
             "não uma tolerância escolhida num teste independente. Não valida braço/fase física.", "",
             f"- Candidatos/referências: {s['num_candidates']}/{s['num_references']}.",
             f"- Pares temporais: {s['temporal_pairs']}; extras: {s['unmatched_candidate_count']}; "
             f"referências sem candidato: {s['no_candidate_count']}.",
             f"- Famílias atribuídas: {s['classified_count']}; pares concordantes: {s['correct_temporal_family_pairs']}.",
             f"- Precisão diagnóstica tempo/família: {s['family_precision']:.1%}; "
             f"recall nas famílias-alvo: {s['family_recall']:.1%}; F1: {s['family_f1']:.1%}.",
             "- Denominadores: precisão = concordantes / todas as atribuições de família;",
             "  recall = concordantes / todos os diretos e uppercuts anotados.", "",
             "| Família manual | Direto | Uppercut | Indeterminado | Sem candidato |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for label, row in s["confusion"].items():
        lines.append(f"| {label} | " + " | ".join(str(v) for v in row.values()) + " |")
    lines += ["", "## Sensibilidade à tolerância, sem alterar previsões", "",
              "| ±ms | Pares temporais /33 | Concordantes /29 | Família errada | Referências indeterminadas | Sem candidato | Classificados sem par |",
              "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for run in runs:
        r = run["summary"]
        lines.append(f"| {run['tolerance_ms']} | " + " | ".join(str(r[k]) for k in (
            "temporal_pairs", "correct_temporal_family_pairs", "wrong_temporal_family_pairs",
            "matched_indeterminate_count", "no_candidate_count", "classified_unmatched_count")) + " |")
    lines += ["", "Hooks preservados: fora do classificador, incluídos nos erros e na matriz.",
              "Indeterminado é abstenção; não significa ausência de golpe.",
              "Candidatos sem recolha no fim do vídeo não foram excluídos.",
              "Não inclui upper body 3 (original/2×), sem anotações e mesma gravação.",
              "Inspeção e interpretação: ../../docs/EVALUATION_PILOT.md."]
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n")
    # Confere que esta execução de avaliação não modificou nenhuma entrada.
    for path, expected in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Entrada alterada durante a consolidação: {path}")
    print(f"Piloto consolidado em {output_dir}: {s['correct_temporal_family_pairs']}/{s['target_reference_count']} "
          f"concordantes; {s['classified_count']} atribuições; {len(runs)} tolerâncias.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/step5"))
    consolidate(parser.parse_args().output_dir)
