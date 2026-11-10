"""Inspeção de candidatos ou classificações previstas, sem rótulos manuais."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import cv2


def render(candidate_file, display_s=.22):
    document = json.loads(Path(candidate_file).read_text())
    pose_dir = Path(document["pose_dir"])
    metadata = json.loads((pose_dir / "metadata.json").read_text())
    with (pose_dir / "pose.jsonl").open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file]
    events = document["candidates"]
    classified = document.get("classification_performed", False)
    destination = Path(candidate_file).parent / ("classification-demo.mp4" if classified else "candidate-demo.mp4")
    if destination.exists():
        raise FileExistsError(f"O vídeo de demonstração já existe: {destination}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("É necessário FFmpeg para exportar H.264.")
    fps, width, height = metadata["fps"], metadata["width"], metadata["height"]
    if len(records) != metadata["frames_processed"]:
        raise ValueError("Contagem de pose inconsistente.")
    by_frame = {e["frame_index"]: e for e in events}
    count, last = 0, None
    preview = None
    with tempfile.TemporaryDirectory(prefix="strike-candidates-") as folder:
        temporary = Path(folder) / "demo.avi"
        capture = cv2.VideoCapture(str(pose_dir / "overlay.mp4"))
        writer = cv2.VideoWriter(str(temporary), cv2.VideoWriter_fourcc(*"MJPG"),
                                 fps, (width, height))
        try:
            if not capture.isOpened() or not writer.isOpened():
                raise RuntimeError("Não foi possível abrir vídeo de entrada/saída.")
            for index, record in enumerate(records):
                ok, frame = capture.read()
                if not ok or frame.shape[:2] != (height, width):
                    raise ValueError(f"Overlay incompleto ou dimensões erradas no frame {index}.")
                if record["frame_index"] != index:
                    raise ValueError("O renderer requer os frames originais contínuos desde 0.")
                event = by_frame.get(index)
                if event:
                    count += 1
                    last = event
                active = (last is not None and
                          0 <= record["timestamp_ms"] - last["timestamp_ms"] <= display_s * 1000)
                # Painel só com previsões; anotações humanas ficam no relatório separado.
                panel_height = 125
                shade = frame.copy()
                cv2.rectangle(shade, (0, 0), (width, panel_height), (20, 20, 20), -1)
                cv2.addWeighted(shade, .85, frame, .15, 0, frame)
                color = (0, 220, 255) if active else (230, 230, 230)
                if active and classified:
                    label = {"straight": "DIRETO (hipotese)", "uppercut": "UPPERCUT (hipotese)",
                             "indeterminate": "INDETERMINADO"}[last["classification"]]
                    heading = f"{label} #{count:02d}"
                else:
                    heading = f"CANDIDATO A GOLPE #{count:02d}" if active else "Analise de movimento"
                cv2.putText(frame, heading, (20, 37), cv2.FONT_HERSHEY_SIMPLEX, .95,
                            color, 2, cv2.LINE_AA)
                subtitle = ("Classificacao experimental: direto / uppercut / indeterminado"
                            if classified else "Sem classificacao de familias")
                cv2.putText(frame, f"Candidatos acumulados: {count} | {subtitle}",
                            (20, 76), cv2.FONT_HERSHEY_SIMPLEX, .7, (230, 230, 230), 2, cv2.LINE_AA)
                detail = f"frame {index} | {record['timestamp_ms']/1000:.3f} s"
                if active:
                    arm = last.get("classification_model_arm", last["model_arm"])
                    detail += f" | pico candidato: {last['frame_index']} | braco modelo: {arm}"
                    if "classification_start_frame" in last:
                        detail += f" | fase: {last['classification_start_frame']}-{last['classification_end_frame']}"
                    if last["status"] == "unconfirmed_end":
                        detail += " | recolha nao observada"
                cv2.putText(frame, detail, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, .58,
                            (230, 230, 230), 1, cv2.LINE_AA)
                writer.write(frame)
                if event and preview is None:
                    preview = frame.copy()
            if capture.read()[0]:
                raise ValueError("Overlay tem mais frames do que o JSONL.")
        finally:
            capture.release()
            writer.release()
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-i", str(temporary),
                        "-an", "-vf", "scale=in_range=full:out_range=tv",
                        "-color_range", "tv", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(destination)], check=True)
    if preview is not None:
        scale = min(1, 1280 / width)
        preview = cv2.resize(preview, (round(width * scale), round(height * scale)))
        if not cv2.imwrite(str(destination.with_name(destination.stem + "-preview.png")), preview):
            raise OSError("Falha ao guardar pré-visualização.")
    print(f"{len(records)} frames; {count} candidatos assinalados. Vídeo: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    args = parser.parse_args()
    render(args.candidate_file)
