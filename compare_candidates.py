"""Diagnóstico temporal no desenvolvimento; não mede classificação de famílias."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def match_times(candidate_ms, reference_ms, tolerance_ms):
    """Correspondência 1:1: maximiza pares e depois minimiza erro absoluto total.

    Programação dinâmica em sequências ordenadas. Uma duplicação nunca pode
    contar duas vezes para a mesma referência. Devolve índices das listas originais.
    """
    if not np.isfinite(tolerance_ms) or tolerance_ms < 0:
        raise ValueError("Tolerância deve ser finita e não negativa.")
    if not np.isfinite(candidate_ms).all() or not np.isfinite(reference_ms).all():
        raise ValueError("Instantes devem ser finitos.")
    order_c = sorted(range(len(candidate_ms)), key=lambda i: candidate_ms[i])
    order_r = sorted(range(len(reference_ms)), key=lambda i: reference_ms[i])
    n, m = len(order_c), len(order_r)
    best = [[(0, 0.0) for _ in range(m + 1)] for _ in range(n + 1)]
    step = {}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            choices = [(best[i - 1][j], "candidate"), (best[i][j - 1], "reference")]
            error = abs(candidate_ms[order_c[i - 1]] - reference_ms[order_r[j - 1]])
            if error <= tolerance_ms:
                count, neg_error = best[i - 1][j - 1]
                choices.append(((count + 1, neg_error - error), "match"))
            best[i][j], step[i, j] = max(choices, key=lambda item: item[0])
    pairs = []
    i, j = n, m
    while i and j:
        action = step[i, j]
        if action == "match":
            pairs.append((order_c[i - 1], order_r[j - 1]))
            i, j = i - 1, j - 1
        elif action == "candidate":
            i -= 1
        else:
            j -= 1
    return list(reversed(pairs))


def compare(candidate_file, video_id, annotations_file, tolerance_ms=125):
    document = json.loads(Path(candidate_file).read_text())
    pose_dir = Path(document["pose_dir"])
    with (pose_dir / "pose.jsonl").open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file]
    frame_times = {r["frame_index"]: r["timestamp_ms"] for r in records}
    with Path(annotations_file).open(newline="", encoding="utf-8") as file:
        annotations = [r for r in csv.DictReader(file) if r["video_id"] == video_id]
    if not annotations:
        raise ValueError("Não há referências para este vídeo.")
    # Confere o ID contra o inventário, para não comparar pose do vídeo errado.
    with (Path(annotations_file).parent / "videos.csv").open(newline="", encoding="utf-8") as file:
        videos = {r["video_id"]: r for r in csv.DictReader(file)}
    if Path(videos[video_id]["pose_dir"]).resolve() != pose_dir.resolve():
        raise ValueError("Vídeo anotado e extração dos candidatos não correspondem.")
    references = [r for r in annotations if r["label"] != "non_punch"]
    reference_ms = [frame_times[int(r["peak_frame"])] for r in references]
    candidates = document["candidates"]
    candidate_ms = []
    for event in candidates:
        actual_ms = frame_times[event["frame_index"]]
        if event["timestamp_ms"] != actual_ms:
            raise ValueError("Timestamp de candidato não corresponde ao frame original.")
        candidate_ms.append(actual_ms)
    pairs = match_times(candidate_ms, reference_ms, tolerance_ms)
    matched_c, matched_r = {i for i, _ in pairs}, {j for _, j in pairs}
    details = [dict(candidate_id=candidates[i]["candidate_id"],
                    candidate_frame=candidates[i]["frame_index"],
                    reference_id=references[j]["event_id"],
                    reference_frame=int(references[j]["peak_frame"]),
                    reference_label=references[j]["label"],
                    error_ms=candidate_ms[i] - reference_ms[j]) for i, j in pairs]
    extras = [e for i, e in enumerate(candidates) if i not in matched_c]
    missed = [r for j, r in enumerate(references) if j not in matched_r]
    negative_peaks = []
    for negative in (r for r in annotations if r["label"] == "non_punch"):
        negative_peaks.append(dict(event_id=negative["event_id"],
            candidate_ids=[c["candidate_id"] for c in candidates
                if int(negative["start_frame"]) <= c["frame_index"] <= int(negative["end_frame"])]))
    return dict(video_id=video_id, scope="development_only", tolerance_ms=tolerance_ms,
                matching="one_to_one_maximum_count_then_minimum_absolute_error",
                hand_and_family_scored=False, num_candidates=len(candidates),
                num_references=len(references), num_matches=len(pairs),
                temporal_precision=len(pairs) / len(candidates) if candidates else 0,
                temporal_recall=len(pairs) / len(references) if references else 0,
                unconfirmed_end_count=sum(c["status"] == "unconfirmed_end" for c in candidates),
                matches=details, unmatched_candidates=extras, missed_references=missed,
                negative_peak_candidates=negative_peaks)


def main(candidate_file, video_id, annotations_file, tolerance_ms):
    import matplotlib.pyplot as plt

    result = compare(candidate_file, video_id, annotations_file, tolerance_ms)
    output_dir = Path(candidate_file).parent
    (output_dir / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [f"# Diagnóstico de desenvolvimento — {video_id}", "",
             f"Tolerância provisória: ±{tolerance_ms:g} ms; correspondência um-para-um.",
             "Os candidatos não têm família prevista. Este diagnóstico ignora mão e família.",
             "Ambos os vídeos foram usados no desenvolvimento; não há teste independente.", "",
             f"- Candidatos: {result['num_candidates']}",
             f"- Golpes manuais: {result['num_references']}",
             f"- Correspondências temporais: {result['num_matches']}",
             f"- Candidatos sem par: {len(result['unmatched_candidates'])}",
             f"- Referências sem par: {len(result['missed_references'])}",
             f"- Precisão temporal: {result['temporal_precision']:.1%}",
             f"- Cobertura temporal (recall): {result['temporal_recall']:.1%}",
             f"- Sem recolha confirmada no fim de observação: {result['unconfirmed_end_count']}", "",
             "As contagens incluem candidatos sem recolha confirmada; ver o campo status no CSV.",
             "Um par temporal não prova deteção da mão, da fase física ou da família correta.", "",
             "| Candidato (frame) | Referência (frame) | Família manual | Erro (ms) |",
             "| --- | --- | --- | --- |"]
    for match in result["matches"]:
        lines.append(f"| {match['candidate_id']} ({match['candidate_frame']}) | "
                     f"{match['reference_id']} ({match['reference_frame']}) | "
                     f"{match['reference_label']} | {match['error_ms']:+g} |")
    lines += ["", "## Candidatos sem par", ""]
    lines += [f"- {e['candidate_id']}: frame {e['frame_index']}, {e['status']}"
              for e in result["unmatched_candidates"]] or ["Nenhum."]
    lines += ["", "## Referências sem par", ""]
    lines += [f"- {e['event_id']}: frame {e['peak_frame']}, {e['label']}"
              for e in result["missed_references"]] or ["Nenhuma."]
    lines += ["", "## Intervalos negativos explícitos", ""]
    lines += [f"- {e['event_id']}: {len(e['candidate_ids'])} instantes de candidato no intervalo."
              for e in result["negative_peak_candidates"]] or ["Não há intervalos negativos explícitos neste vídeo."]
    (output_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    document = json.loads(Path(candidate_file).read_text())
    candidates = document["candidates"]
    with Path(annotations_file).open(newline="") as file:
        refs = [r for r in csv.DictReader(file) if r["video_id"] == video_id and r["peak_frame"]]
    fig, axis = plt.subplots(figsize=(13, 3))
    colors = {"straight": "#1769aa", "uppercut": "#d95f02", "hook": "#8c52aa"}
    for label, color in colors.items():
        frames = [int(r["peak_frame"]) for r in refs if r["label"] == label]
        axis.scatter(frames, [1] * len(frames), color=color, marker="v", s=55,
                     label=f"Manual: {label}")
    axis.scatter([e["frame_index"] for e in candidates], [0] * len(candidates),
                 color="black", s=25, label="Candidato sem classe")
    for match in result["matches"]:
        axis.plot([match["candidate_frame"], match["reference_frame"]], [0, 1],
                  color="gray", lw=.7, alpha=.5)
    axis.set(yticks=[0, 1], yticklabels=["Candidatos", "Referências"],
             xlabel="Frame original", ylim=(-.5, 1.7),
             title=f"{video_id}: {result['num_matches']}/{result['num_references']} referências com par "
                   f"a ±{tolerance_ms:g} ms — desenvolvimento")
    axis.legend(loc="upper center", ncols=4, fontsize=8)
    axis.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(output_dir / "comparison.png", dpi=150)
    plt.close(fig)
    print(f"{video_id}: {result['num_matches']}/{result['num_references']} referências com par; "
          f"{len(result['unmatched_candidates'])} candidatos sem par; "
          f"{len(result['missed_references'])} referências sem par.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--annotations", type=Path, default=Path("annotations/events.csv"))
    parser.add_argument("--tolerance-ms", type=float, default=125)
    args = parser.parse_args()
    main(args.candidate_file, args.video_id, args.annotations, args.tolerance_ms)
