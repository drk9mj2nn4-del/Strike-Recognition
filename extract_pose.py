"""Primeiro componente: vídeo → MediaPipe Full → coordenadas e vídeo anotado.

Ler primeiro main(), depois extract(), para acompanhar o fluxo do programa.
Esta versão assume vídeo com frequência de frames constante (CFR).
"""

import argparse
import hashlib
import json
import math
import os
from importlib.metadata import version
from pathlib import Path
from time import perf_counter


# Guia de leitura: main() escolhe ficheiros; extract() contém o percurso completo.
# Dentro de extract(), procurar os blocos 1–5 e o ciclo `while success`.
# As funções frame_record()/serialize_landmarks() preparam a saída numérica;
# draw_pose() prepara a saída visual. Ambas usam o resultado do mesmo frame.

# A ordem dos 33 pontos é definida pelo MediaPipe. Estes nomes tornam os índices
# legíveis no JSON: por exemplo, 11 = ombro esquerdo e 15 = punho esquerdo.
# Esquerda/direita referem-se ao corpo da pessoa, não aos lados da imagem.
LANDMARK_NAMES = (
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer", "left_ear", "right_ear",
    "mouth_left", "mouth_right", "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_pinky", "right_pinky", "left_index", "right_index",
    "left_thumb", "right_thumb", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
    "left_heel", "right_heel", "left_foot_index", "right_foot_index",
)
# Cada par indica dois pontos a unir no desenho: (11, 13) liga ombro a cotovelo.
# Estas linhas são escolhidas por nós; não são uma previsão adicional do modelo.
# Um subconjunto das ligações, para tornar o desenho fácil de ler.
BODY_CONNECTIONS = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
)
# Este limiar só controla o desenho, não a inferência nem os dados exportados.
DRAW_VISIBILITY = 0.5


def timestamp_ms(frame_index, fps):
    """Tempo do frame num vídeo CFR; não é o tempo gasto a executar o modelo."""
    if not math.isfinite(fps) or not 0 < fps <= 1000:
        raise ValueError("FPS inválido; é necessário um vídeo CFR com 0 < FPS <= 1000.")
    # Índices começam em zero: a 25 FPS, o frame 50 está em 2 s = 2000 ms.
    # O tempo pertence ao vídeo mesmo que a análise demore mais ou menos tempo.
    return round(1000 * frame_index / fps)


def serialize_landmarks(landmarks):
    """Preserva os pontos brutos: baixa visibilidade não significa coordenada zero."""
    if landmarks and len(landmarks) != len(LANDMARK_NAMES):
        raise ValueError("Esperavam-se 33 pontos do MediaPipe Pose Landmarker.")
    # A API devolve objetos com atributos (point.x); criamos dicionários que o
    # módulo json consegue escrever. enumerate() associa cada ponto ao seu índice.
    # visibility/presence são estimativas do modelo, não garantias de precisão.
    return [
        {"id": index, "name": LANDMARK_NAMES[index], "x": point.x,
         "y": point.y, "z": point.z, "visibility": point.visibility,
         "presence": point.presence}
        for index, point in enumerate(landmarks)
    ]


def frame_record(result, frame_index, fps):
    """Um registo por frame, incluindo quando não há pose detetada."""
    # O primeiro nível da lista corresponde às pessoas/poses encontradas.
    # Como pedimos no máximo uma pose, usamos [0] se existir; senão, lista vazia.
    landmarks = result.pose_landmarks[0] if result.pose_landmarks else []
    world = result.pose_world_landmarks[0] if result.pose_world_landmarks else []
    # landmarks: coordenadas da imagem; x/y normalizados por largura/altura.
    # world_landmarks: estimativas 3D em metros, relativas ao centro das ancas;
    # não são medições calibradas. Guardamo-las separadas; o gráfico usa só x/y.
    # Sem pose, mantemos frame_index e tempo, com pose_detected=False e listas [].
    return {
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms(frame_index, fps),
        "pose_detected": bool(landmarks),
        "landmarks": serialize_landmarks(landmarks),
        "world_landmarks": serialize_landmarks(world),
    }


def draw_pose(cv2, frame, landmarks):
    """Só desenha pontos visíveis dentro da imagem; os dados guardados ficam brutos."""
    height, width = frame.shape[:2]
    pixels = {}
    for index, point in enumerate(landmarks):
        # A omissão visual pode dever-se a baixa visibilidade ou a um ponto fora
        # da imagem. Não apagamos a respetiva coordenada do resultado/JSONL.
        if (point.visibility is not None and point.visibility >= DRAW_VISIBILITY
                and 0 <= point.x < 1 and 0 <= point.y < 1):
            # Origem no canto superior esquerdo: x cresce à direita, y para baixo.
            # Ex.: x=0.5 numa imagem de 800 px corresponde à coluna 400.
            pixels[index] = (int(point.x * width), int(point.y * height))
    for start, end in BODY_CONNECTIONS:
        # Só desenhamos uma ligação se os seus dois extremos passaram o filtro.
        if start in pixels and end in pixels:
            cv2.line(frame, pixels[start], pixels[end], (80, 220, 80), 2)
    for index, position in pixels.items():
        # Punhos amarelos para facilitar a inspeção dos movimentos rápidos.
        color = (0, 255, 255) if index in (15, 16) else (80, 220, 80)
        cv2.circle(frame, position, 5 if index in (15, 16) else 3, color, -1)
    # line()/circle() alteram a própria matriz `frame`. Não é preciso devolvê-la;
    # quem chamou esta função passa a ter a imagem com o desenho por cima.


def extract(video_path, model_path, output_dir):
    if not video_path.is_file():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}. Ver download no README.")
    if output_dir.exists():
        raise FileExistsError(f"A pasta {output_dir} já existe. Escolhe outra para preservar os resultados.")

    # Imports aqui permitem ler a ajuda e testar a exportação sem as bibliotecas CV.
    os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))
    import cv2
    import mediapipe as mp

    # 1. ENTRADA — OpenCV descodifica o vídeo para matrizes de píxeis BGR.
    # Não carregamos o vídeo todo em memória: capture.read() avança um frame.
    capture = cv2.VideoCapture(str(video_path))
    writer = None
    frame_count = 0
    detected_count = 0
    started = perf_counter()
    try:
        if not capture.isOpened():
            raise ValueError(f"Não foi possível abrir o vídeo: {video_path}")
        # FPS dá-nos a relação índice → tempo, assumindo frequência constante.
        fps = capture.get(cv2.CAP_PROP_FPS)
        timestamp_ms(0, fps)  # Validar antes de criar ficheiros de saída.
        success, frame = capture.read()
        if not success:
            raise ValueError("O vídeo não contém um primeiro frame legível.")
        # Um frame a cores tem forma (altura, largura, 3 canais).
        height, width = frame.shape[:2]
        if width % 2 or height % 2:
            raise ValueError("Esta versão requer largura e altura pares para exportar MP4.")

        # 2. MODELO — MediaPipe é a biblioteca; o .task contém o modelo
        # pré-treinado e os recursos necessários. Aqui só fazemos inferência.
        # VIDEO processa uma sequência com tempos crescentes e permite à API
        # usar seguimento entre frames; não classificamos ações ou golpes.
        # num_poses=1 limita a uma pose; não escolhe manualmente uma pessoa.
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(model_path.resolve()),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
        )
        # Criamos/carregamos uma vez e reutilizamos ao longo de todo o vídeo.
        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
            output_dir.mkdir(parents=True, exist_ok=False)
            # 3. SAÍDAS — metadata descreve esta execução; JSONL guardará os
            # números de cada frame; MP4 guardará as imagens com as anotações.
            metadata = {
                "status": "in_progress",
                "backend": "mediapipe", "device": "cpu",
                "mediapipe_version": version("mediapipe"),
                "opencv_version": cv2.__version__,
                "model_file": model_path.name,
                "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "input_file": video_path.name,
                "fps": fps, "width": width, "height": height,
                "timestamp_source": "frame_index / fps; assumes constant frame rate",
                "image_coordinates": "x/width, y/height; z relative to hip midpoint, not meters",
                "world_coordinates": "estimated meters, origin at hip midpoint; not calibrated measurements",
                "draw_visibility_threshold": DRAW_VISIBILITY,
            }
            metadata_path = output_dir / "metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            # O writer codifica os frames que lhe dermos, com resolução/FPS iguais
            # aos da entrada. Só escrevemos imagem: o áudio não é copiado.
            writer = cv2.VideoWriter(
                str(output_dir / "overlay.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                fps, (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError("Não foi possível criar o MP4 com o codec mp4v.")

            print("A processar em CPU; timestamps assumem vídeo CFR. MP4 de saída sem áudio.")
            with (output_dir / "pose.jsonl").open("x", encoding="utf-8") as output:
                # 4. CICLO POR FRAME — imagem → modelo → dados e desenho → vídeo.
                # O primeiro frame já foi lido acima; o seguinte é lido no fim.
                while success:
                    if frame.shape[:2] != (height, width):
                        raise ValueError("A resolução mudou durante o vídeo.")
                    # a) Preparar a entrada. BGR → RGB troca a ordem dos canais,
                    # sem mudar a geometria da imagem. mp.Image é o invólucro
                    # que a API MediaPipe aceita para esta matriz RGB.
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    # b) Aqui acontece a inferência. A biblioteca trata dos seus
                    # passos internos e devolve pontos, não um vídeo desenhado.
                    result = landmarker.detect_for_video(image, timestamp_ms(frame_count, fps))
                    # c) Guardar a resposta antes de filtrar qualquer desenho.
                    # JSONL = um objeto JSON por linha; \n separa os frames.
                    # Assim há uma linha até quando o modelo não encontra pose.
                    record = frame_record(result, frame_count, fps)
                    output.write(json.dumps(record, allow_nan=False) + "\n")
                    detected_count += int(record["pose_detected"])
                    # d) Usar os pontos do MESMO resultado para desenhar sobre
                    # o frame BGR original. Não relemos o JSON nem corremos o
                    # modelo outra vez para produzir o overlay.
                    landmarks = result.pose_landmarks[0] if result.pose_landmarks else []
                    draw_pose(cv2, frame, landmarks)
                    label = f"{record['timestamp_ms'] / 1000:.2f}s | pose: {record['pose_detected']}"
                    cv2.putText(frame, label, (16, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (255, 255, 255), 2)
                    # e) Acrescentar a imagem anotada ao novo vídeo. A entrada
                    # no disco mantém-se intacta; só alterámos a matriz em memória.
                    writer.write(frame)
                    frame_count += 1
                    if frame_count % 100 == 0:
                        print(f"  {frame_count} frames processados")
                    success, frame = capture.read()  # Sem próximo frame, termina o ciclo.

            # 5. FINALIZAÇÃO — release() termina a escrita do MP4. Só depois
            # marcamos o metadata como complete, com contagens e tempo de execução.
            writer.release()
            writer = None
            metadata.update({
                "status": "complete",
                "frames_processed": frame_count,
                "frames_with_pose": detected_count,
                "processing_seconds": perf_counter() - started,
            })
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    finally:
        # Libertar os ficheiros mesmo que tenha ocorrido um erro a meio.
        capture.release()
        if writer is not None:
            writer.release()

    print(f"Resultados: {output_dir}")
    print(f"Pose detetada em {detected_count}/{frame_count} frames; isto não mede precisão.")


def main():
    # Ponto de entrada: argparse lê os caminhos fornecidos no terminal.
    # Exemplo (cria uma pasta NOVA; não substitui os resultados já existentes):
    # .venv/bin/python extract_pose.py data/commons-boxer-focus.mp4 --output-dir outputs/exemplo-leitura
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Vídeo com uma pessoa, idealmente CFR")
    parser.add_argument("--model", type=Path, default=Path("models/pose_landmarker_full.task"))
    parser.add_argument("--output-dir", type=Path, help="Pasta nova para guardar os resultados")
    args = parser.parse_args()
    output_dir = args.output_dir or Path("outputs") / f"{args.video.stem}-mediapipe"
    try:
        extract(args.video, args.model, output_dir)
    except ImportError as error:
        parser.exit(1, f"Dependência em falta: {error}. Instala requirements.txt no ambiente .venv.\n")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Erro: {error}\n")


if __name__ == "__main__":
    main()

