"""Acrescenta anéis roxos aos punhos omitidos num overlay já exportado.

Não executa o modelo nem corrige/interpola posições. Usa pose.jsonl e metadata.json
da MESMA pasta que overlay.mp4. Requer FFmpeg disponível no PATH.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import tempfile

import cv2


def render(results_dir):
    results_dir = Path(results_dir)
    metadata = json.loads((results_dir / "metadata.json").read_text())
    records = [json.loads(line) for line in (results_dir / "pose.jsonl").open()]
    if metadata["status"] != "complete" or len(records) != metadata["frames_processed"]:
        raise ValueError("Extração incompleta ou contagem de registos inconsistente.")
    output = results_dir / "overlay-purple-wrists-h264.mp4"
    csv_path = results_dir / "purple-wrists-inspection.csv"
    report_path = results_dir / "purple-wrists-inspection.json"
    for path in (output, csv_path, report_path):
        if path.exists():
            raise FileExistsError(path)

    width, height, fps = metadata["width"], metadata["height"], metadata["fps"]
    threshold = metadata["draw_visibility_threshold"]
    capture = cv2.VideoCapture(str(results_dir / "overlay.mp4"))
    if not capture.isOpened():
        raise ValueError("Não foi possível abrir overlay.mp4.")
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo",
        "-pixel_format", "bgr24", "-video_size", f"{width}x{height}",
        "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output),
    ]
    rows = []
    # Reduzimos apenas a letra da legenda quando necessário; a imagem não muda de escala.
    font_scale = min(0.67, (width - 36) / 1450)
    panel_height = max(54, round(font_scale * 105))
    with tempfile.TemporaryFile() as errors:
        encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        try:
            for index, record in enumerate(records):
                ok, frame = capture.read()
                if not ok or frame.shape[:2] != (height, width):
                    raise ValueError(f"Frame {index} ausente ou com resolução incorreta.")
                if record["frame_index"] != index:
                    raise ValueError("Índices de frames descontínuos.")
                if record["timestamp_ms"] != round(index / fps * 1000):
                    raise ValueError("Timestamp diferente do esperado para este overlay CFR.")
                scores = []
                if record["pose_detected"]:
                    for point_id, label in ((15, "E"), (16, "D")):
                        point = record["landmarks"][point_id]
                        if point["id"] != point_id:
                            raise ValueError("Ordem de landmarks inesperada.")
                        x, y, visibility = point["x"], point["y"], point["visibility"]
                        inside = (math.isfinite(x) and math.isfinite(y)
                                  and 0 <= x < 1 and 0 <= y < 1)
                        drawn = inside and visibility is not None and visibility >= threshold
                        purple = inside and not drawn
                        if purple:
                            # Mesma conversão usada no overlay original: sem corrigir a previsão.
                            position = (int(x * width), int(y * height))
                            cv2.circle(frame, position, 10, (220, 60, 220), 2, cv2.LINE_AA)
                            cv2.putText(frame, label, (position[0] + 13, position[1] - 8),
                                        cv2.FONT_HERSHEY_SIMPLEX, .55, (220, 60, 220),
                                        2, cv2.LINE_AA)
                        score = f"{visibility:.3f}" if visibility is not None else "ausente"
                        scores.append(f"{label} ({point_id}): visibility = {score}"
                                      + (" | fora da imagem" if not inside else ""))
                        rows.append(dict(frame_index=index, timestamp_ms=record["timestamp_ms"],
                                         point_id=point_id, x=x, y=y, visibility=visibility,
                                         inside_image=inside, originally_drawn=drawn,
                                         purple_ring=purple))
                else:
                    scores = ["Sem pose: nao ha coordenadas para assinalar"]
                # Rodapé de inspeção; mantém o timestamp original no topo.
                panel = frame[-panel_height:]
                panel[:] = cv2.convertScaleAbs(panel, alpha=.25)
                texts = ["Roxo: estimativa omitida | Amarelo: overlay original | Sem correcao manual",
                         " | ".join(scores)]
                for text, offset in zip(texts, (round(panel_height * .62), 13)):
                    cv2.putText(frame, text, (18, height - offset), cv2.FONT_HERSHEY_SIMPLEX,
                                font_scale, (255, 255, 255), 1, cv2.LINE_AA)
                encoder.stdin.write(frame.tobytes())
            if capture.read()[0]:
                raise ValueError("Overlay tem mais frames do que o JSONL.")
        finally:
            capture.release()
            encoder.stdin.close()
            return_code = encoder.wait()
        if return_code:
            errors.seek(0)
            raise RuntimeError(errors.read().decode())

    if rows:
        with csv_path.open("x", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    counts = {}
    for point_id in (15, 16):
        selected = [row for row in rows if row["point_id"] == point_id]
        counts[str(point_id)] = dict(
            yellow_frames=sum(row["originally_drawn"] for row in selected),
            purple_frames=sum(row["purple_ring"] for row in selected),
            outside_image_frames=sum(not row["inside_image"] for row in selected),
        )
    report = dict(output=str(output), frames=len(records), width=width, height=height,
                  fps=fps, draw_visibility_threshold=threshold,
                  frames_without_pose=sum(not r["pose_detected"] for r in records),
                  rule="Purple rings only at saved in-image wrist estimates omitted by visibility filter; no interpolation or manual correction.",
                  counts=counts)
    with report_path.open("x") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", type=Path, help="Pasta com overlay.mp4, pose.jsonl e metadata.json")
    render(parser.parse_args().results_dir)
