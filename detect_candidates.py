"""Baseline offline: excursões rápidas dos punhos, sem classificar golpes.

Lê apenas pose/metadata. A mediana de cada vetor é uma referência geométrica
por vídeo, não uma guarda identificada. Não usa anotações manuais.
"""

import argparse
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from prepare_arm_features import prepare_features
from temporal_motion import vector_velocity


@dataclass(frozen=True)
class CandidateConfig:
    min_excursion_px: float = 100
    min_prominence_px: float = 60
    min_speed_px_s: float = 1200
    context_s: float = .25
    min_separation_s: float = .16

    def __post_init__(self):
        if any(not np.isfinite(x) or x <= 0 for x in asdict(self).values()):
            raise ValueError("Os parâmetros devem ser finitos e positivos.")


def arm_candidates(frames, times_ms, vectors, side, config):
    """Picos de excursão com subida rápida e descida parcial numa janela local.

    Janelas nunca atravessam NaN/saltos de frames. No fim de um segmento, um
    candidato sem descida observável pode ser exportado como não confirmado.
    """
    times_s = np.asarray(times_ms) / 1000
    vectors = np.asarray(vectors)
    valid = np.isfinite(vectors).all(axis=1)
    reference = np.median(vectors[valid], axis=0) if valid.any() else np.full(2, np.nan)
    excursion = np.linalg.norm(vectors - reference, axis=1)
    velocity = vector_velocity(frames, times_ms, vectors)
    speed = np.linalg.norm(velocity, axis=1)
    # Cada segmento é observável e contínuo; não extrapolamos por lacunas.
    segments = []
    start = None
    for i in range(len(frames)):
        if start is not None and (not valid[i] or frames[i] != frames[i - 1] + 1):
            segments.append((start, i))
            start = None
        if valid[i] and start is None:
            start = i
    if start is not None:
        segments.append((start, len(frames)))

    events = []
    for lo, hi in segments:
        for i in range(lo + 1, hi):
            # Em patamares, usa a primeira amostra do topo.
            if excursion[i] <= excursion[i - 1]:
                continue
            if i + 1 < hi and excursion[i] < excursion[i + 1]:
                continue
            before = np.arange(lo, i)
            before = before[times_s[i] - times_s[before] <= config.context_s]
            if not len(before):
                continue
            onset = int(before[np.argmin(excursion[before])])
            rise = float(excursion[i] - excursion[onset])
            max_speed = float(np.max(speed[onset + 1:i + 1]))
            if (excursion[i] < config.min_excursion_px
                    or rise < config.min_prominence_px
                    or max_speed < config.min_speed_px_s):
                continue
            after = np.arange(i + 1, hi)
            after = after[times_s[after] - times_s[i] <= config.context_s]
            recovery = int(after[np.argmin(excursion[after])]) if len(after) else None
            drop = float(excursion[i] - excursion[recovery]) if recovery is not None else 0
            if drop >= config.min_prominence_px:
                status = "returned_partly"
                prominence = min(rise, drop)
            elif times_s[hi - 1] - times_s[i] < config.context_s:
                # Fim do vídeo ou perda de observação: não afirmar recolha.
                status = "unconfirmed_end"
                prominence = rise
            else:
                continue
            events.append(dict(
                frame_index=int(frames[i]), timestamp_ms=float(times_ms[i]),
                model_arm=side, label="movement_candidate", status=status,
                onset_frame=int(frames[onset]),
                recovery_frame=int(frames[recovery]) if status == "returned_partly" else None,
                excursion_px=float(excursion[i]), prominence_px=float(prominence),
                max_rising_speed_px_s=max_speed,
            ))
    return events, reference, excursion, velocity


def suppress_nearby(events, min_separation_s):
    """Um candidato por vizinhança temporal, incluindo deteções nos dois braços.

    Prioriza maior proeminência; pode fundir dois golpes muito próximos. O braço
    guardado é o que sustentou a regra, não uma mão anatómica validada.
    """
    selected = []
    for event in sorted(events, key=lambda e: (-e["prominence_px"], e["timestamp_ms"], e["model_arm"])):
        if all(abs(event["timestamp_ms"] - other["timestamp_ms"]) / 1000
               >= min_separation_s for other in selected):
            selected.append(event.copy())
    selected.sort(key=lambda e: e["timestamp_ms"])
    for index, event in enumerate(selected, 1):
        event["candidate_id"] = f"candidate-{index:03d}"
    return selected


def detect(frames, times_ms, features, config):
    events, signals, references = [], {}, {}
    for side in ("left", "right"):
        vectors = np.column_stack([features[f"{side}_delta_x_px"],
                                   features[f"{side}_delta_y_px"]])
        candidates, reference, excursion, velocity = arm_candidates(
            frames, times_ms, vectors, side, config,
        )
        events.extend(candidates)
        references[side] = [float(v) if np.isfinite(v) else None for v in reference]
        signals[f"{side}_vx_px_s"] = velocity[:, 0]
        signals[f"{side}_vy_px_s"] = velocity[:, 1]
        signals[f"{side}_speed_px_s"] = np.linalg.norm(velocity, axis=1)
        signals[f"{side}_excursion_px"] = excursion
    return suppress_nearby(events, config.min_separation_s), signals, references


def main(results_dir, output_dir, config):
    import matplotlib.pyplot as plt

    frames, times_ms, features, threshold = prepare_features(results_dir)
    events, signals, references = detect(frames, times_ms, features, config)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((Path(results_dir) / "metadata.json").read_text())
    document = dict(
        method="median_wrist_excursion_v1", pose_dir=str(Path(results_dir).resolve()),
        input_file=metadata["input_file"], frames_processed=len(frames),
        config=asdict(config), min_visibility=threshold,
        reference_vectors_px=references, annotations_used=False,
        classification_performed=False, candidates=events,
    )
    (output_dir / "candidates.json").write_text(
        json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    fields = ["candidate_id", "frame_index", "timestamp_ms", "model_arm", "label",
              "status", "onset_frame", "recovery_frame", "excursion_px",
              "prominence_px", "max_rising_speed_px_s"]
    with (output_dir / "candidates.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(events)
    with (output_dir / "motion_signals.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["frame_index", "timestamp_ms", *signals])
        writer.writerows(zip(frames, times_ms, *signals.values()))

    fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    for side, color in [("left", "#1769aa"), ("right", "#d95f02")]:
        axes[0].plot(times_ms / 1000, signals[f"{side}_excursion_px"], color=color,
                     label=f"Braço {side} do modelo")
        axes[1].plot(times_ms / 1000, signals[f"{side}_speed_px_s"], color=color)
    axes[0].axhline(config.min_excursion_px, color="gray", ls=":", lw=1)
    axes[1].axhline(config.min_speed_px_s, color="gray", ls=":", lw=1)
    for event in events:
        t = event["timestamp_ms"] / 1000
        for axis in axes:
            axis.axvline(t, color="#555555", alpha=.4, lw=.8)
        axes[0].plot(t, event["excursion_px"], "o", color="black", ms=4)
    axes[0].set_ylabel("Afastamento da referência (px)")
    axes[1].set_ylabel("Rapidez aparente (px/s)")
    axes[1].set_xlabel("Tempo original do vídeo (s)")
    axes[0].legend(loc="upper right")
    for axis in axes:
        axis.grid(alpha=.2)
        axis.set_ylim(bottom=0)
    fig.suptitle(f"{len(events)} candidatos de movimento — sem classificação de golpes")
    fig.tight_layout()
    fig.savefig(output_dir / "candidates.png", dpi=150)
    plt.close(fig)
    print(f"{len(events)} candidatos; {sum(e['status'] == 'unconfirmed_end' for e in events)} "
          f"sem recolha confirmada por fim de observação. Saída: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    defaults = CandidateConfig()
    for name, value in asdict(defaults).items():
        parser.add_argument("--" + name.replace("_", "-"), type=float, default=value)
    args = parser.parse_args()
    config = CandidateConfig(**{key: getattr(args, key) for key in asdict(defaults)})
    main(args.results_dir, args.output_dir, config)
