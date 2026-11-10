"""Diferenças temporais na imagem, sem atravessar observações em falta."""

import numpy as np


def vector_velocity(frames, timestamps_ms, vectors_px):
    """Velocidade média em px/s entre frames consecutivos, alinhada no segundo.

    O primeiro valor é NaN. Se falta um dos vetores ou há um salto nos índices,
    o intervalo é NaN; não liga pontos separados por observações em falta.
    """
    frames = np.asarray(frames)
    times = np.asarray(timestamps_ms, dtype=float)
    vectors = np.asarray(vectors_px, dtype=float)
    if vectors.shape != (len(frames), 2) or times.shape != (len(frames),):
        raise ValueError("Esperados frames/tempos (T,) e vetores (T, 2).")
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("Timestamps devem ser finitos e estritamente crescentes.")
    if not np.isfinite(frames).all() or np.any(np.diff(frames) <= 0):
        raise ValueError("Índices devem ser finitos e estritamente crescentes.")
    velocity = np.full(vectors.shape, np.nan)
    valid = (np.isfinite(vectors[:-1]).all(axis=1)
             & np.isfinite(vectors[1:]).all(axis=1)
             & (np.diff(frames) == 1))
    indices = np.flatnonzero(valid) + 1
    velocity[indices] = ((vectors[indices] - vectors[indices - 1])
                         / ((times[indices] - times[indices - 1]) / 1000)[:, None])
    return velocity
