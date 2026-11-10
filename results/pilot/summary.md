# Avaliação piloto v2 — desenvolvimento

Gerado por `consolidate_evaluation.py`; regras e previsões preservadas.
Matching temporal 1:1 sem usar família/mão. ±125 ms é a referência histórica,
não uma tolerância escolhida num teste independente. Não valida braço/fase física.

- Candidatos/referências: 41/33.
- Pares temporais: 31; extras: 10; referências sem candidato: 2.
- Famílias atribuídas: 26; pares concordantes: 23.
- Precisão diagnóstica tempo/família: 88.5%; recall nas famílias-alvo: 79.3%; F1: 83.6%.
- Denominadores: precisão = concordantes / todas as atribuições de família;
  recall = concordantes / todos os diretos e uppercuts anotados.

| Família manual | Direto | Uppercut | Indeterminado | Sem candidato |
| --- | ---: | ---: | ---: | ---: |
| straight | 16 | 0 | 4 | 1 |
| uppercut | 0 | 7 | 0 | 1 |
| hook | 1 | 0 | 3 | 0 |

## Sensibilidade à tolerância, sem alterar previsões

| ±ms | Pares temporais /33 | Concordantes /29 | Família errada | Referências indeterminadas | Sem candidato | Classificados sem par |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 26 | 19 | 1 | 6 | 7 | 6 |
| 100 | 30 | 22 | 1 | 7 | 3 | 3 |
| 125 | 31 | 23 | 1 | 7 | 2 | 2 |
| 167 | 32 | 24 | 1 | 7 | 1 | 1 |
| 200 | 32 | 24 | 1 | 7 | 1 | 1 |

Hooks preservados: fora do classificador, incluídos nos erros e na matriz.
Indeterminado é abstenção; não significa ausência de golpe.
Candidatos sem recolha no fim do vídeo não foram excluídos.
Não inclui upper body 3 (original/2×), sem anotações e mesma gravação.
Inspeção e interpretação: ../../docs/EVALUATION_PILOT.md.
