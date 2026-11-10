"""Passo 4, incremento 1: séries geométricas dos braços, sem deteção de golpes."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from analyze_pose import load_pose
from analyze_wrist_distance import wrist_shoulder_vector


# Nomes anatómicos do modelo, sem atribuir lead/rear ou resolver espelhamento.
ARMS = {"left": (11, 13, 15), "right": (12, 14, 16)}


def elbow_angle(xy, visibility, width, height, indices, min_visibility=0.5):
    """Ângulo interior 2D em graus (T,); três pontos filtrados, zero → NaN."""
    points = xy[:, list(indices), :]
    scores = visibility[:, list(indices)]
    passes_filter = (
        np.isfinite(points).all(axis=(1, 2))
        & ((points >= 0) & (points < 1)).all(axis=(1, 2))
        & np.isfinite(scores).all(axis=1)
        & (scores >= min_visibility).all(axis=1)
    )
    points_px = points * [width, height]
    # Os dois vetores partem do cotovelo: cotovelo→ombro e cotovelo→punho.
    upper = points_px[:, 0] - points_px[:, 1]
    forearm = points_px[:, 2] - points_px[:, 1]
    denominator = np.linalg.norm(upper, axis=1) * np.linalg.norm(forearm, axis=1)
    valid = passes_filter & (denominator > 0)
    angles = np.full(len(xy), np.nan)
    cosine = np.sum(upper[valid] * forearm[valid], axis=1) / denominator[valid]
    # O arredondamento numérico pode levar o cosseno ligeiramente fora de [-1, 1].
    angles[valid] = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
    return angles


def arm_features(xy, visibility, width, height, min_visibility=0.5):
    """Uma série (T,) por característica e braço, sem alterar a ordem temporal."""
    features = {}
    for side, indices in ARMS.items():
        shoulder, _, wrist = indices
        vector = wrist_shoulder_vector(
            xy, visibility, width, height, min_visibility,
            shoulder_index=shoulder, wrist_index=wrist,
        )
        features[f"{side}_delta_x_px"] = vector[:, 0]
        features[f"{side}_delta_y_px"] = vector[:, 1]
        features[f"{side}_distance_px"] = np.linalg.norm(vector, axis=1)
        features[f"{side}_elbow_angle_deg"] = elbow_angle(
            xy, visibility, width, height, indices, min_visibility,
        )
    return features


def prepare_features(results_dir):
    """Lê apenas pose/metadata; as anotações manuais não entram neste componente."""
    results_dir = Path(results_dir)
    metadata = json.loads((results_dir / "metadata.json").read_text())
    frames, times_ms, xy = load_pose(results_dir / "pose.jsonl")
    if metadata["status"] != "complete" or len(frames) != metadata["frames_processed"]:
        raise ValueError("Extração incompleta ou contagem de frames inconsistente.")
    if not len(frames) or np.any(np.diff(frames) <= 0):
        raise ValueError("É necessária uma sequência não vazia com índices crescentes.")
    if not np.isfinite(times_ms).all() or np.any(np.diff(times_ms) <= 0):
        raise ValueError("Os timestamps originais devem ser finitos e crescentes.")

    # Mesma leitura de visibility usada na análise do Passo 2, mantendo ausências.
    with (results_dir / "pose.jsonl").open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file]
    visibility = np.full((len(records), 33), np.nan)
    for index, record in enumerate(records):
        if record["pose_detected"]:
            visibility[index] = [
                p["visibility"] if p["visibility"] is not None else np.nan
                for p in record["landmarks"]
            ]
    threshold = metadata["draw_visibility_threshold"]
    features = arm_features(
        xy, visibility, metadata["width"], metadata["height"], threshold,
    )
    return frames, times_ms, features, threshold


def main(results_dir, output_dir):
    import matplotlib.pyplot as plt

    frames, times_ms, features, threshold = prepare_features(results_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "arm_features.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["frame_index", "timestamp_ms", *features])
        writer.writerows(zip(frames, times_ms, *features.values()))

    fig, axes = plt.subplots(4, 2, figsize=(13, 10), sharex=True, sharey="row")
    series = [
        ("delta_x_px", "Δx (px) — direita positiva"),
        ("delta_y_px", "Δy (px) — baixo positivo"),
        ("distance_px", "Distância 2D (px)"),
        ("elbow_angle_deg", "Ângulo 2D (°)"),
    ]
    for column, (side, label, color) in enumerate([
        ("left", "Esquerdo — 11/13/15", "#1769aa"),
        ("right", "Direito — 12/14/16", "#d95f02"),
    ]):
        axes[0, column].set_title(label)
        for row, (key, ylabel) in enumerate(series):
            axis = axes[row, column]
            axis.plot(times_ms / 1000, features[f"{side}_{key}"], color=color, lw=1.2)
            axis.set_ylabel(ylabel)
            axis.grid(alpha=.3)
            if row < 2:
                axis.axhline(0, color="gray", lw=.7, ls="--")
        axes[3, column].set_ylim(0, 180)
        axes[-1, column].set_xlabel("Tempo original do vídeo (s)")
    # Definir o limite depois de desenhar AMBOS os braços: sharey não deve
    # fixar a escala pelo primeiro braço e cortar os picos do segundo.
    axes[2, 0].set_ylim(bottom=0)
    fig.suptitle("Características dos braços ao longo do tempo — sem deteção de golpes")
    fig.text(.5, .015, f"Visibility ≥ {threshold}; coordenadas dentro da imagem; "
             "NaN preservados. Sem suavização/interpolação. Filtro não garante precisão.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .96))
    graph_path = output_dir / "arm_features.png"
    fig.savefig(graph_path, dpi=150)
    plt.close(fig)
    print(f"{len(frames)} frames; tempos originais {times_ms[0]}–{times_ms[-1]} ms.")
    for key, values in features.items():
        print(f"{key}: {np.isfinite(values).sum()} valores válidos pelo filtro.")
    print(f"CSV: {csv_path}\nGráfico: {graph_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    main(args.results_dir, args.output_dir)
