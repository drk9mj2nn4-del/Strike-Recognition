"""V2: regras de trajetória em fases locais dos dois braços, com abstenção.

Mantém os candidatos/timestamps do detetor. Não lê eventos ou classes manuais.
A mediana e as fases são calculadas offline, a partir da pose do vídeo inteiro.
"""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from analyze_pose import load_pose
from classify_candidates import ClassificationConfig, classify, summarize_window, write_classifications
from prepare_arm_features import ARMS, prepare_features


@dataclass(frozen=True)
class PhaseConfig:
    lookback_ms: float = 320
    endpoint_before_ms: float = 120
    endpoint_after_ms: float = 80
    min_samples: int = 3
    min_motion_scale: float = .15
    max_endpoint_height_scale: float = .15
    straight_max_preparation_depth_scale: float = .35
    straight_min_rise_scale: float = .1
    straight_min_linearity: float = .6
    straight_min_radial_gain_scale: float = .05
    straight_min_opening_deg: float = 15
    straight_projected_ascent_min_upward_fraction: float = .8
    straight_projected_ascent_min_motion_scale: float = .35
    straight_max_axis_crossing_scale: float = .05
    min_reference_horizontal_scale: float = .05
    upper_min_preparation_depth_scale: float = .4
    upper_min_rise_scale: float = .4
    upper_min_upward_fraction: float = .65
    upper_max_angle_deg: float = 110
    upper_max_opening_deg: float = 45
    ambiguity_score_ratio: float = .8
    endpoint_penalty_ms: float = 80
    duplicate_endpoint_distance_ms: float = 200
    duplicate_min_overlap_fraction: float = .6


def decide_phase(summary, reference_x, config):
    """Profundidade e sentidos são relativos ao ombro NA IMAGEM, não 3D.

    O perfil uppercut requer preparação baixa nestes exemplos; não é exigência
    universal de uppercut. A regra de direto inclui um perfil ascendente na
    imagem sem exigir grande ângulo 2D; não determina a causa desse ângulo.
    """
    if summary is None or summary["samples"] < config.min_samples:
        return "indeterminate", "missing_or_short_phase"
    s = summary
    if s["net_motion_scale"] < config.min_motion_scale:
        return "indeterminate", "insufficient_phase_motion"
    top = s["peak_vertical_offset_scale"] <= config.max_endpoint_height_scale
    radial_or_angle = (s["radial_gain_scale"] >= config.straight_min_radial_gain_scale
                       or s["elbow_opening_deg"] >= config.straight_min_opening_deg)
    projected_ascent = (
        s["upward_fraction"] >= config.straight_projected_ascent_min_upward_fraction
        and s["net_motion_scale"] >= config.straight_projected_ascent_min_motion_scale
    )
    orientation_known = abs(reference_x) / s["arm_scale_px"] >= config.min_reference_horizontal_scale
    sign = 1 if reference_x >= 0 else -1
    axis_consistent = (orientation_known and sign * s["end_x_px"] / s["arm_scale_px"]
                       >= -config.straight_max_axis_crossing_scale)
    straight = (
        s["preparation_depth_scale"] <= config.straight_max_preparation_depth_scale
        and s["vertical_rise_scale"] >= config.straight_min_rise_scale
        and s["linearity"] >= config.straight_min_linearity
        and top and axis_consistent and (radial_or_angle or projected_ascent)
    )
    upper = (
        s["preparation_depth_scale"] >= config.upper_min_preparation_depth_scale
        and s["vertical_rise_scale"] >= config.upper_min_rise_scale
        and s["upward_fraction"] >= config.upper_min_upward_fraction
        and s["peak_elbow_deg"] <= config.upper_max_angle_deg
        and s["elbow_opening_deg"] <= config.upper_max_opening_deg and top
    )
    if upper and not straight:
        return "uppercut", "low_preparation_then_ascent"
    if straight and not upper:
        return "straight", "shallow_preparation_and_extension_or_projected_ascent"
    return "indeterminate", "ambiguous_phase" if upper and straight else "no_phase_pattern"


def phase_hypothesis(frames, times, vectors, angles, elbows, scale, timestamp_ms, side, config):
    """Seleciona topo vertical local e ponto baixo anterior, sem atravessar lacunas."""
    if not np.isfinite(scale) or scale <= 0:
        return None
    valid = np.isfinite(vectors).all(axis=1) & np.isfinite(angles) & np.isfinite(elbows).all(axis=1)
    near = np.flatnonzero((times >= timestamp_ms - config.endpoint_before_ms)
                         & (times <= timestamp_ms + config.endpoint_after_ms))
    # Rejeitar a vizinhança se houver lacuna, em vez de saltar pontos inválidos.
    if (not len(near) or not valid[near].all()
            or np.any(np.diff(frames[near]) != 1)):
        return None
    end = int(near[np.argmin(vectors[near, 1])])
    before = np.flatnonzero((times >= times[end] - config.lookback_ms) & (times < times[end]))
    # Só usa o sufixo contínuo e válido imediatamente anterior ao topo.
    start_limit = end
    while start_limit > 0 and times[end] - times[start_limit - 1] <= config.lookback_ms:
        previous = start_limit - 1
        if not valid[previous] or frames[start_limit] != frames[previous] + 1:
            break
        start_limit = previous
    before = before[before >= start_limit]
    if not len(before):
        return None
    start = int(before[np.argmax(vectors[before, 1])])
    window = slice(start, end + 1)
    summary = summarize_window(frames[window], times[window], vectors[window],
                               angles[window], elbows[window], scale)
    if summary is None:
        return None
    summary.update(preparation_depth_scale=float(vectors[start, 1] / scale),
                   end_x_px=float(vectors[end, 0]))
    reference_x = float(np.median(vectors[valid, 0]))
    label, reason = decide_phase(summary, reference_x, config)
    # Score de ordenação geométrica, não probabilidade/confiança calibrada.
    score = (summary["net_motion_scale"] * summary["linearity"]
             / (1 + abs(float(times[end]) - timestamp_ms) / config.endpoint_penalty_ms))
    return dict(classification=label, reason=reason, model_arm=side,
                start_frame=int(frames[start]), end_frame=int(frames[end]),
                endpoint_ms=float(times[end]), score=float(score), features=summary)


def select_hypothesis(hypotheses, config):
    supported = sorted((h for h in hypotheses if h and h["classification"] != "indeterminate"),
                       key=lambda h: (-h["score"], h["model_arm"]))
    if not supported:
        return None, "no_supported_phase"
    first = supported[0]
    if any(h["classification"] != first["classification"]
           and h["score"] >= config.ambiguity_score_ratio * first["score"] for h in supported[1:]):
        return None, "conflicting_arm_phases"
    return first, first["reason"]


def duplicates_phase(phase, accepted, config):
    for previous in accepted:
        if (phase["model_arm"] != previous["model_arm"]
                or abs(phase["endpoint_ms"] - previous["endpoint_ms"])
                > config.duplicate_endpoint_distance_ms):
            continue
        overlap = max(0, min(phase["end_frame"], previous["end_frame"])
                      - max(phase["start_frame"], previous["start_frame"]) + 1)
        shorter = min(phase["end_frame"] - phase["start_frame"] + 1,
                      previous["end_frame"] - previous["start_frame"] + 1)
        if overlap / shorter >= config.duplicate_min_overlap_fraction:
            return True
    return False


def classify_phases(document, config=PhaseConfig(), preserve_strict=True, deduplicate=True):
    baseline = classify(document, ClassificationConfig())
    frames, times, features, _ = prepare_features(document["pose_dir"])
    _, _, xy = load_pose(Path(document["pose_dir"]) / "pose.jsonl")
    metadata = json.loads((Path(document["pose_dir"]) / "metadata.json").read_text())
    points = xy * [metadata["width"], metadata["height"]]
    geometry = {}
    for side, (shoulder, elbow, wrist) in ARMS.items():
        lengths = (np.linalg.norm(points[:, elbow] - points[:, shoulder], axis=1)
                   + np.linalg.norm(points[:,wrist] - points[:,elbow], axis=1))
        angles = features[f"{side}_elbow_angle_deg"]
        valid = np.isfinite(angles) & (lengths > 0)
        geometry[side] = (
            np.column_stack([features[f"{side}_delta_x_px"], features[f"{side}_delta_y_px"]]),
            angles, points[:,elbow] - points[:,shoulder],
            float(np.median(lengths[valid])) if valid.any() else np.nan,
        )
    output, accepted = [], []
    for event in baseline["candidates"]:
        new = dict(event)
        hypotheses = []
        selected = None
        if preserve_strict and event["classification"] != "indeterminate":
            selected = dict(classification=event["classification"], reason=event["classification_reason"],
                            model_arm=event["model_arm"], start_frame=event["onset_frame"],
                            end_frame=event["frame_index"], endpoint_ms=event["timestamp_ms"],
                            features=event["classification_features"], score=None)
            new["classification_source"] = "strict_v1"
        elif event["status"] == "returned_partly":
            for side, args in geometry.items():
                hypothesis = phase_hypothesis(frames, times, *args, event["timestamp_ms"], side, config)
                if hypothesis:
                    hypotheses.append(hypothesis)
            selected, reason = select_hypothesis(hypotheses, config)
            new.update(classification="indeterminate", classification_reason=reason,
                       classification_source="phase_v2", classification_features=None)
        else:
            new["classification_source"] = "abstained"
        new["classification_hypotheses"] = hypotheses
        if selected is not None:
            new["classification_features"] = selected["features"]
            if deduplicate and duplicates_phase(selected, accepted, config):
                new.update(classification="indeterminate", classification_reason="phase_already_used",
                           classification_source="duplicate_phase")
            else:
                new.update(classification=selected["classification"], classification_reason=selected["reason"])
                accepted.append(selected)
            new.update(classification_model_arm=selected["model_arm"],
                       classification_start_frame=selected["start_frame"],
                       classification_end_frame=selected["end_frame"])
        output.append(new)
    result = dict(baseline)
    result.update(classification_method="geometry_phases_v2", candidates=output,
                  classification_config=dict(phases=asdict(config), preserve_strict_v1=preserve_strict,
                                             deduplicate_phases=deduplicate,
                                             strict_v1=asdict(ClassificationConfig())),
                  classification_annotations_used=False, candidate_timestamps_preserved=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_classifications(classify_phases(json.loads(args.candidate_file.read_text())), args.output_dir)
