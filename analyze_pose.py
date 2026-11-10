"""Primeiro gráfico temporal das coordenadas de imagem de um punho."""

import json
from pathlib import Path

import numpy as np


# Este script começa onde extract_pose.py acabou: lê números já guardados.
# Não abre o vídeo, não carrega o modelo e não volta a fazer inferência.
RESULTS_DIR = Path(__file__).resolve().parent / "outputs/offline-check-focus"
LEFT_WRIST = 15


def load_pose(pose_file):
    """Devolve índices, timestamps em ms e x/y, mantendo frames sem pose."""
    with Path(pose_file).open(encoding="utf-8") as file:
        # Cada linha de texto JSON torna-se um dicionário Python de um frame.
        records = [json.loads(line) for line in file]

    # Guardamos os tempos exportados; não os reconstruímos a partir da posição
    # na lista. Assim os valores continuam associados aos frames de origem.
    frame_indices = np.array([r["frame_index"] for r in records], dtype=int)
    timestamps_ms = np.array([r["timestamp_ms"] for r in records], dtype=float)
    # T frames × 33 pontos × 2 coordenadas (x, y), agora só valores numéricos.
    # Começamos com NaN (= ausência de valor). Se um frame não tiver pose,
    # a sua posição fica reservada; não encurtamos nem deslocamos a sequência.
    xy = np.full((len(records), 33, 2), np.nan)

    for t, record in enumerate(records):
        if record["pose_detected"]:
            # Transformar os 33 dicionários em 33 pares [x, y]. Não usamos z,
            # world_landmarks ou um limiar de visibilidade neste primeiro gráfico.
            xy[t] = [[point["x"], point["y"]] for point in record["landmarks"]]

    return frame_indices, timestamps_ms, xy


def main():
    import matplotlib.pyplot as plt

    with (RESULTS_DIR / "metadata.json").open(encoding="utf-8") as file:
        metadata = json.load(file)
    frame_indices, timestamps_ms, xy = load_pose(RESULTS_DIR / "pose.jsonl")
    if len(frame_indices) != metadata["frames_processed"]:
        raise ValueError("Número de registos diferente de frames_processed no metadata.")

    # Mudar apenas a unidade do tempo: milissegundos → segundos.
    time_s = timestamps_ms / 1000
    # `:` escolhe todos os frames; 15 escolhe o punho esquerdo; o último `:`
    # mantém x e y. Da forma (T, 33, 2) passamos para (T, 2).
    wrist_xy = xy[:, LEFT_WRIST, :]  # Forma (T, 2): x e y do punho esquerdo.

    fig, ax = plt.subplots(figsize=(11, 5))
    # Eixo horizontal = tempo; cada curva mostra UMA coordenada ao longo dele.
    # x/y são frações da largura/altura, respetivamente, não distâncias em metros.
    # Os NaN interrompem as linhas. Baixa visibilidade, por si só, não as interrompe.
    ax.plot(time_s, wrist_xy[:, 0], label="x — cresce para a direita na imagem")
    ax.plot(time_s, wrist_xy[:, 1], label="y — cresce para baixo na imagem")
    ax.set(
        xlabel="Tempo do vídeo (s)",
        ylabel="Coordenada normalizada (sem unidade)",
        title="Punho esquerdo — posição na imagem ao longo do tempo",
        xlim=(time_s[0], time_s[-1]),
    )
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    output_file = RESULTS_DIR / "left_wrist_position.png"
    fig.savefig(output_file, dpi=150)
    plt.close(fig)

    missing = np.isnan(wrist_xy).all(axis=1).sum()
    print(f"{len(frame_indices)} frames; {missing} sem pose; array x/y: {xy.shape}")
    print(f"Tempo: {time_s[0]:.2f}–{time_s[-1]:.2f} s")
    print(f"Imagem: {metadata['width']} × {metadata['height']} px")
    print(f"Gráfico guardado em {output_file}")


if __name__ == "__main__":
    main()
