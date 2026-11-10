"""Primeiro classificador geométrico: direto, uppercut ou indeterminado.

Recebe candidatos e pose; não lê anotações. As regras descrevem padrões 2D
conservadores, não garantias sobre a técnica física do praticante.
"""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from analyze_pose import load_pose
from prepare_arm_features import ARMS, prepare_features


@dataclass(frozen=True)
class ClassificationConfig:
    min_samples: int = 3
    min_motion_scale: float = .2
    straight_min_angle_deg: float = 80
    straight_min_opening_deg: float = 35
    straight_min_radial_gain_scale: float = .15
    straight_min_linearity: float = .7
    straight_max_elbow_motion_ratio: float = 1.25
    straight_max_downward_fraction: float = .2
    upper_min_rise_scale: float = .25
    upper_min_upward_fraction: float = .8
    upper_max_angle_deg: float = 80
    upper_max_opening_deg: float = 20
    upper_min_preparation_angle_deg: float = 45
    upper_max_over_shoulder_offset_scale: float = .15


def summarize_window(frames, times_ms, vectors, angles, elbows, scale):
    """Resume apenas observações contínuas; comprimentos relativos à escala do braço.

    Escala = mediana por vídeo da soma dos comprimentos projetados dos dois
    segmentos do braço. Não é comprimento físico calibrado.
    """
    if len(frames) < 2 or not np.isfinite(scale) or scale <= 0:
        return None
    if (np.any(np.diff(frames) != 1) or np.any(np.diff(times_ms) <= 0)
            or not np.isfinite(times_ms).all() or not np.isfinite(vectors).all()
            or not np.isfinite(angles).all() or not np.isfinite(elbows).all()):
        return None
    delta = vectors[-1] - vectors[0]
    chord = float(np.linalg.norm(delta))
    path = float(np.linalg.norm(np.diff(vectors, axis=0), axis=1).sum())
    if chord <= 0 or path <= 0:
        return None
    return dict(
        samples=len(frames), duration_s=float((times_ms[-1] - times_ms[0]) / 1000),
        arm_scale_px=float(scale), dx_px=float(delta[0]), dy_px=float(delta[1]),
        net_motion_scale=chord / scale, linearity=chord / path,
        radial_gain_scale=float((np.linalg.norm(vectors[-1]) - np.linalg.norm(vectors[0])) / scale),
        vertical_rise_scale=float(-delta[1] / scale), upward_fraction=float(-delta[1] / chord),
        start_elbow_deg=float(angles[0]), peak_elbow_deg=float(angles[-1]),
        elbow_opening_deg=float(angles[-1] - angles[0]),
        elbow_motion_ratio=float(np.linalg.norm(elbows[-1] - elbows[0]) / chord),
        peak_horizontal_offset_scale=float(abs(vectors[-1, 0]) / scale),
        peak_vertical_offset_scale=float(vectors[-1, 1] / scale),
    )


def decide(summary, status, config):
    """Devolve classe e razão; indeterminado é abstenção, não ausência de golpe."""
    if status != "returned_partly":
        return "indeterminate", "return_not_observed"
    if summary is None:
        return "indeterminate", "missing_or_discontinuous_geometry"
    s = summary
    if s["samples"] < config.min_samples or s["net_motion_scale"] < config.min_motion_scale:
        return "indeterminate", "insufficient_observed_motion"
    straight = (
        s["peak_elbow_deg"] >= config.straight_min_angle_deg
        and s["elbow_opening_deg"] >= config.straight_min_opening_deg
        and s["radial_gain_scale"] >= config.straight_min_radial_gain_scale
        and s["linearity"] >= config.straight_min_linearity
        and s["elbow_motion_ratio"] <= config.straight_max_elbow_motion_ratio
        and s["upward_fraction"] >= -config.straight_max_downward_fraction
    )
    # Aceita preparação com flexão moderada ou uma subida quase sobre o ombro
    # na imagem. Esta segunda hipótese depende fortemente do ponto de vista.
    preparation = (
        s["start_elbow_deg"] >= config.upper_min_preparation_angle_deg
        or (s["peak_horizontal_offset_scale"] <= config.upper_max_over_shoulder_offset_scale
            and s["peak_vertical_offset_scale"] < 0)
    )
    upper = (
        s["vertical_rise_scale"] >= config.upper_min_rise_scale
        and s["upward_fraction"] >= config.upper_min_upward_fraction
        and s["peak_elbow_deg"] <= config.upper_max_angle_deg
        and s["elbow_opening_deg"] <= config.upper_max_opening_deg
        and preparation
    )
    if straight and not upper:
        return "straight", "extension_and_elbow_opening"
    if upper and not straight:
        return "uppercut", "upward_motion_with_bent_elbow"
    return "indeterminate", "conflicting_rules" if straight and upper else "no_supported_pattern"


def classify(document, config):
    """Mantém número, timestamps e braço do detetor; não corrige candidatos com rótulos."""
    pose_dir = Path(document["pose_dir"])
    frames, times_ms, features, _ = prepare_features(pose_dir)
    _, _, xy = load_pose(pose_dir / "pose.jsonl")
    metadata = json.loads((pose_dir / "metadata.json").read_text())
    xy_px = xy * [metadata["width"], metadata["height"]]
    index = {int(frame): i for i, frame in enumerate(frames)}
    scales, elbows_by_side = {}, {}
    for side, (shoulder, elbow, wrist) in ARMS.items():
        lengths = (np.linalg.norm(xy_px[:, elbow] - xy_px[:, shoulder], axis=1)
                   + np.linalg.norm(xy_px[:, wrist] - xy_px[:, elbow], axis=1))
        valid = np.isfinite(features[f"{side}_elbow_angle_deg"]) & (lengths > 0)
        scales[side] = float(np.median(lengths[valid])) if valid.any() else np.nan
        elbows_by_side[side] = xy_px[:, elbow] - xy_px[:, shoulder]
    results = []
    for event in document["candidates"]:
        side = event["model_arm"]
        lo, hi = index[event["onset_frame"]], index[event["frame_index"]]
        if lo >= hi or event["timestamp_ms"] != times_ms[hi]:
            raise ValueError("Janela/timestamp do candidato inconsistente com a pose.")
        window = slice(lo, hi + 1)
        vectors = np.column_stack([features[f"{side}_delta_x_px"][window],
                                   features[f"{side}_delta_y_px"][window]])
        summary = summarize_window(
            frames[window], times_ms[window], vectors,
            features[f"{side}_elbow_angle_deg"][window],
            elbows_by_side[side][window], scales[side],
        )
        label, reason = decide(summary, event["status"], config)
        results.append(dict(event, classification=label, classification_reason=reason,
                            classification_features=summary))
    result = dict(document)
    result.update(classification_performed=True, classification_method="geometry_v1",
                  classification_config=asdict(config), classification_annotations_used=False,
                  classification_arm_scales_px={s: v if np.isfinite(v) else None for s, v in scales.items()},
                  candidates=results)
    return result


def write_classifications(result, output_dir):
    """Exportação partilhada pelas versões; preserva a configuração de cada uma."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "classifications.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    fields = ["candidate_id", "frame_index", "timestamp_ms", "model_arm", "status",
              "classification", "classification_reason"]
    phase_fields = [key for key in ["classification_model_arm", "classification_start_frame",
                                    "classification_end_frame", "classification_source"]
                    if any(key in e for e in result["candidates"])]
    feature_fields = list(dict.fromkeys(key for e in result["candidates"]
                                       for key in (e["classification_features"] or {})))
    with (output_dir / "classifications.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields + phase_fields + feature_fields)
        writer.writeheader()
        for event in result["candidates"]:
            writer.writerow({**{key: event.get(key) for key in fields + phase_fields},
                             **(event["classification_features"] or {})})
    print(dict(Counter(e["classification"] for e in result["candidates"])))
    print(f"Saída: {output_dir}")


def main(candidate_file, output_dir):
    document = json.loads(Path(candidate_file).read_text())
    write_classifications(classify(document, ClassificationConfig()), output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    main(args.candidate_file, args.output_dir)
