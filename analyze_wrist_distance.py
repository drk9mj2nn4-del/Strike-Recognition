"""Passo 2: vetor e distância 2D punho–ombro esquerdo na imagem."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from analyze_pose import load_pose


LEFT_SHOULDER = 11
LEFT_WRIST = 15


def wrist_shoulder_vector(xy, visibility, width, height, min_visibility=0.5,
                          *, shoulder_index=LEFT_SHOULDER, wrist_index=LEFT_WRIST):
    """Vetor ombro → punho em píxeis (T, 2), com NaN onde falha o filtro.

    xy tem forma (T, 33, 2) e visibility tem forma (T, 33).
    Os índices permitem reutilizar o cálculo no braço direito; por omissão, esquerdo.
    Passar o filtro é um critério de desenho/análise, não uma garantia de acerto.
    """
    points = xy[:, [shoulder_index, wrist_index], :]
    scores = visibility[:, [shoulder_index, wrist_index]]
    passes_filter = (
        np.isfinite(points).all(axis=(1, 2))
        & ((points >= 0) & (points < 1)).all(axis=(1, 2))
        & np.isfinite(scores).all(axis=1)
        & (scores >= min_visibility).all(axis=1)
    )
    # x e y têm escalas diferentes no JSONL: converter ANTES de calcular a norma.
    displacement_px = (xy[:, wrist_index] - xy[:, shoulder_index]) * [width, height]
    # Mantém todos os instantes; não liga nem interpola através de pontos omitidos.
    displacement_px[~passes_filter] = np.nan
    return displacement_px


def wrist_shoulder_distance(xy, visibility, width, height, min_visibility=0.5):
    """Comprimento do vetor filtrado (T,): descarta a direção, mantém os NaN."""
    vector_px = wrist_shoulder_vector(xy, visibility, width, height, min_visibility)
    return np.linalg.norm(vector_px, axis=1)


def main(results_dir):
    import matplotlib.pyplot as plt

    results_dir = Path(results_dir)
    metadata = json.loads((results_dir / "metadata.json").read_text())
    frames, times_ms, xy = load_pose(results_dir / "pose.jsonl")
    if metadata["status"] != "complete" or len(frames) != metadata["frames_processed"]:
        raise ValueError("Extração incompleta ou contagem de frames inconsistente.")

    # Reutilizamos a leitura x/y do Passo 1 e lemos também os scores guardados.
    records = [json.loads(line) for line in (results_dir / "pose.jsonl").open()]
    visibility = np.full((len(records), 33), np.nan)
    for index, record in enumerate(records):
        if record["pose_detected"]:
            visibility[index] = [p["visibility"] if p["visibility"] is not None else np.nan
                                 for p in record["landmarks"]]
    threshold = metadata["draw_visibility_threshold"]
    vector_px = wrist_shoulder_vector(
        xy, visibility, metadata["width"], metadata["height"], threshold,
    )
    distance_px = np.linalg.norm(vector_px, axis=1)

    with (results_dir / "left_wrist_shoulder_distance.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frame_index", "timestamp_ms", "shoulder_visibility",
                         "wrist_visibility", "passes_filter", "distance_px",
                         "delta_x_px", "delta_y_px"])
        for index, frame in enumerate(frames):
            writer.writerow([frame, times_ms[index], visibility[index, LEFT_SHOULDER],
                             visibility[index, LEFT_WRIST],
                             bool(np.isfinite(distance_px[index])), distance_px[index],
                             vector_px[index, 0], vector_px[index, 1]])

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(times_ms / 1000, distance_px, color="#087f8c")
    ax.set(xlabel="Tempo do vídeo (s)", ylabel="Distância na imagem (px)",
           title="Punho esquerdo → ombro esquerdo — distância 2D",
           xlim=(times_ms[0] / 1000, times_ms[-1] / 1000), ylim=(0, None))
    ax.grid(alpha=.3)
    fig.text(.5, .025, f"Ambos os pontos dentro da imagem e visibility ≥ {threshold}; "
             "valores omitidos ficam como lacunas. Sem suavização.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .055, 1, 1))
    graph = results_dir / "left_wrist_shoulder_distance.png"
    fig.savefig(graph, dpi=150)
    plt.close(fig)

    # As componentes preservam o sinal: direita/baixo positivos nos eixos da imagem.
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    labels = ["Δx — positivo: punho à direita do ombro",
              "Δy — positivo: punho abaixo do ombro"]
    for axis, component, label, color in zip(
            axes, (0, 1), labels, ("#1769aa", "#d95f02")):
        axis.plot(times_ms / 1000, vector_px[:, component], color=color)
        axis.axhline(0, color="gray", lw=1, ls="--")
        axis.set(ylabel="Separação (px)", title=label,
                 xlim=(times_ms[0] / 1000, times_ms[-1] / 1000))
        axis.grid(alpha=.3)
    axes[-1].set_xlabel("Tempo do vídeo (s)")
    fig.suptitle("Vetor ombro → punho esquerdo — componentes na imagem")
    fig.text(.5, .015, "Mesmo filtro e mesmos frames da distância. Eixos da imagem; "
             "não são direções 3D relativas ao tronco.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .96))
    components_graph = results_dir / "left_wrist_shoulder_components.png"
    fig.savefig(components_graph, dpi=150)
    plt.close(fig)
    print(f"{len(frames)} frames; {np.isfinite(distance_px).sum()} passam o filtro; "
          f"{np.isnan(distance_px).sum()} lacunas. Isto não mede precisão.")
    print(f"Gráfico: {graph}")
    print(f"Componentes: {components_graph}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", type=Path)
    main(parser.parse_args().results_dir)
