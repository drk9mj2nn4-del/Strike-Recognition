"""Diagnóstico conjunto de tempo e família, incluindo abstenções e golpes perdidos."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from compare_candidates import compare


PREDICTIONS = ["straight", "uppercut", "indeterminate"]
REFERENCES = ["straight", "uppercut", "hook"]


def evaluate(classification_file, video_id, annotations_file, tolerance_ms=125):
    document = json.loads(Path(classification_file).read_text())
    if not document.get("classification_performed"):
        raise ValueError("O ficheiro não contém classificações.")
    temporal = compare(classification_file, video_id, annotations_file, tolerance_ms)
    candidates = document["candidates"]
    by_id = {e["candidate_id"]: e for e in candidates}
    by_reference = {m["reference_id"]: m for m in temporal["matches"]}
    with Path(annotations_file).open(newline="", encoding="utf-8") as file:
        refs = [r for r in csv.DictReader(file) if r["video_id"] == video_id and r["peak_frame"]]
    matrix = {label: {p: 0 for p in PREDICTIONS + ["not_detected"]} for label in REFERENCES}
    rows = []
    correct, wrong, abstained, unsupported = [], [], [], []
    for ref in refs:
        match = by_reference.get(ref["event_id"])
        candidate = by_id[match["candidate_id"]] if match else None
        prediction = candidate["classification"] if candidate else "not_detected"
        matrix[ref["label"]][prediction] += 1
        row = dict(reference_id=ref["event_id"], reference_frame=int(ref["peak_frame"]),
                   reference_label=ref["label"], prediction=prediction,
                   candidate_id=candidate["candidate_id"] if candidate else None,
                   candidate_frame=candidate["frame_index"] if candidate else None,
                   error_ms=match["error_ms"] if match else None,
                   reason=candidate["classification_reason"] if candidate else "no_temporal_candidate")
        rows.append(row)
        if candidate and prediction == "indeterminate":
            abstained.append(row)
        elif candidate and prediction == ref["label"]:
            correct.append(row)
        elif candidate:
            wrong.append(row)
        if ref["label"] == "hook":
            unsupported.append(row)
    extras = [by_id[e["candidate_id"]] for e in temporal["unmatched_candidates"]]
    classified_extras = [e for e in extras if e["classification"] != "indeterminate"]
    num_target_refs = sum(r["label"] in ("straight", "uppercut") for r in refs)
    return dict(video_id=video_id, scope="development_only", tolerance_ms=tolerance_ms,
                num_candidates=len(candidates), num_references=len(refs),
                prediction_counts=dict(Counter(e["classification"] for e in candidates)),
                target_reference_count=num_target_refs,
                correct_temporal_family_pairs=len(correct), wrong_temporal_family_pairs=len(wrong),
                matched_indeterminate_count=len(abstained),
                no_candidate_count=len(temporal["missed_references"]),
                unmatched_candidate_count=len(extras), classified_unmatched_count=len(classified_extras),
                confusion=matrix, reference_rows=rows, unmatched_candidates=extras,
                unsupported_hook_reference_count=len(unsupported),
                hand_scored=False, independent_test=False,
                caveat="Temporal matching does not validate physical phase or model arm; hooks remain out of scope.")


def main(classification_file, video_id, annotations_file, tolerance_ms):
    import matplotlib.pyplot as plt
    import numpy as np

    result = evaluate(classification_file, video_id, annotations_file, tolerance_ms)
    output_dir = Path(classification_file).parent
    (output_dir / "classification-evaluation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8",
    )
    rows = result["reference_rows"]
    with (output_dir / "classification-evaluation.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]) if rows else ["reference_id"])
        writer.writeheader()
        writer.writerows(rows)
    counts = result["prediction_counts"]
    lines = [f"# Classificação geométrica — {video_id}", "",
             "Diagnóstico de desenvolvimento; os dois vídeos foram explorados para definir as regras.",
             f"Pares temporais um-para-um a ±{tolerance_ms:g} ms, sem pontuar mão anatómica.",
             "Indeterminado é abstenção sobre a família; não significa que não ocorreu golpe.",
             "Hooks são mantidos no quadro como família fora do âmbito; não foram relabelados.", "",
             f"- Candidatos: {result['num_candidates']}",
             f"- Previsões: {counts.get('straight',0)} diretos; {counts.get('uppercut',0)} uppercuts; "
             f"{counts.get('indeterminate',0)} indeterminados.",
             f"- Pares com tempo e família concordantes: {result['correct_temporal_family_pairs']}",
             f"- Pares com família discordante: {result['wrong_temporal_family_pairs']}",
             f"- Referências com candidato indeterminado: {result['matched_indeterminate_count']}",
             f"- Referências sem candidato: {result['no_candidate_count']}",
             f"- Candidatos sem par: {result['unmatched_candidate_count']} "
             f"({result['classified_unmatched_count']} com família atribuída).", "",
             "## Todos os golpes manuais, incluindo os não classificados", "",
             "| Família manual | Direto previsto | Uppercut previsto | Indeterminado | Sem candidato |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for label in REFERENCES:
        values = result["confusion"][label]
        lines.append(f"| {label} | " + " | ".join(str(values[p]) for p in PREDICTIONS + ["not_detected"]) + " |")
    lines += ["", "## Cada referência", "",
              "| Referência (frame) | Manual | Previsto | Candidato (frame) | Erro ms |",
              "| --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['reference_id']} ({row['reference_frame']}) | {row['reference_label']} | "
                     f"{row['prediction']} | {row['candidate_id'] or '—'} "
                     f"({row['candidate_frame'] if row['candidate_frame'] is not None else '—'}) | "
                     f"{row['error_ms'] if row['error_ms'] is not None else '—'} |")
    lines += ["", "## Candidatos sem par", ""]
    lines += [f"- Frame {e['frame_index']}: {e['classification']} ({e['classification_reason']})."
              for e in result["unmatched_candidates"]] or ["Nenhum."]
    lines += ["", "Uma concordância neste quadro não demonstra reconhecimento físico robusto.",
              "As abstenções e as regras escolhidas nestes dados impedem alegar generalização."]
    (output_dir / "classification-evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    matrix = np.array([[result["confusion"][r][p] for p in PREDICTIONS + ["not_detected"]]
                       for r in REFERENCES])
    fig, axis = plt.subplots(figsize=(8, 4.5))
    axis.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, matrix.max()))
    axis.set(xticks=range(4), xticklabels=["Direto", "Uppercut", "Indeterminado", "Sem candidato"],
             yticks=range(3), yticklabels=["Direto", "Uppercut", "Hook (fora do âmbito)"],
             xlabel="Saída do protótipo", ylabel="Anotação manual",
             title=f"{video_id}: todos os golpes — desenvolvimento")
    for (row, column), value in np.ndenumerate(matrix):
        axis.text(column, row, str(value), ha="center", va="center",
                  color="white" if value > matrix.max() / 2 else "black", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "classification-confusion.png", dpi=150)
    plt.close(fig)
    print(f"{video_id}: {counts}; {result['correct_temporal_family_pairs']} pares concordantes; "
          f"{result['wrong_temporal_family_pairs']} discordantes; "
          f"{result['matched_indeterminate_count']} referências com abstenção; "
          f"{result['no_candidate_count']} sem candidato.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("classification_file", type=Path)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--annotations", type=Path, default=Path("annotations/events.csv"))
    parser.add_argument("--tolerance-ms", type=float, default=125)
    args = parser.parse_args()
    main(args.classification_file, args.video_id, args.annotations, args.tolerance_ms)
