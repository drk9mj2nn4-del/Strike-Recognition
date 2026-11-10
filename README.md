# Strike Recognition

Protótipo de Computer Vision para analisar vídeos de shadowboxing com
**MediaPipe Pose Landmarker Full** e **regras geométricas temporais**.
Localiza movimentos candidatos e atribui **direto**, **uppercut** ou
**indeterminado**. Direto agrupa jab/cross; indeterminado é abstenção sobre a
família, não ausência de golpe. Hooks permanecem nas anotações e na avaliação,
mas não são uma classe prevista.

**Protótipo — 10/11/2026.** Pipeline executado, avaliação piloto consolidada
e documentação preparada para a candidatura. Repositório público:
[Strike-Recognition](https://github.com/drk9mj2nn4-del/Strike-Recognition). Não foi treinado um classificador
de golpes nem realizado teste independente. O modelo pré-treinado de pose é o
componente aprendido; a deteção e classificação de golpes usam regras.

## Resultado e alcance da análise

Dois vídeos de desenvolvimento, cerca de **17,18 s**, com **33 golpes anotados
manualmente**: 21 diretos, 8 uppercuts e 4 hooks. As regras foram ajustadas e
selecionadas nestes mesmos exemplos. O piloto permite estudar o comportamento
do protótipo; não estima generalização para novas pessoas ou câmaras.

| Diagnóstico a ±125 ms, correspondência temporal 1:1 | Resultado |
| --- | ---: |
| Movimentos candidatos / golpes anotados | 41 / 33 |
| Pares temporais, ignorando família | 31 / 33 referências |
| Tempo e família concordantes | **23 / 29 diretos e uppercuts** |
| Atribuições de família | 26: 23 concordantes, 1 hook como direto, 2 sem par |
| Golpes-alvo indeterminados / sem candidato | 4 / 2 |
| Precisão diagnóstica tempo/família | 23/26 = 88,5% |
| Recall nas famílias-alvo / F1 | 23/29 = 79,3% / 83,6% |

Estes valores incluem erros, abstenções e golpes perdidos nos denominadores
adequados. **Não são accuracy.** A tolerância é retrospectiva e provisória;
variando-a entre ±50 e ±200 ms, as concordâncias passam de 19 para 24.
Um par de tempo/família não valida o braço ou a fase física do golpe.

O relatório [EVALUATION_PILOT.md](docs/EVALUATION_PILOT.md) apresenta o protocolo,
a matriz, a sensibilidade temporal e exemplos de falhas. A cópia numérica em
[results/pilot/](results/pilot/README.md) permite consultar os resultados sem
vídeos, modelo ou ambiente Python.

## Limitações e próximos passos

Os principais limites são o volume reduzido de dados, o ajuste das regras aos
vídeos avaliados, os erros/oclusões da pose, a dependência da projeção 2D e a
fragilidade da segmentação temporal em combinações. Há falsos candidatos,
abstenções e golpes não detetados. O pipeline é offline e usa contexto futuro;
não foi demonstrado funcionamento em tempo real.

O trabalho seguinte está definido em [NEXT_STEPS.md](docs/NEXT_STEPS.md):

1. Recolher e anotar mais gravações, com diferentes pessoas, ângulos, sessões,
   velocidades e movimentos sem golpe; confirmar proveniência e condições de uso.
2. Reservar gravações independentes antes de novos ajustes, separando por
   sessão/pessoa e mantendo recortes e alterações de velocidade no mesmo grupo.
3. Avaliar a qualidade da pose e a deteção temporal separadamente da família.
4. Treinar e comparar um classificador de sequências de pose com este baseline,
   sob o mesmo protocolo; avaliar também os golpes sem candidato. A aprendizagem
   é uma hipótese a testar, sem melhoria garantida.

Texto para a candidatura e guião de apresentação:
[CANDIDATURA.md](docs/CANDIDATURA.md).

## Pipeline e organização

```text
Vídeo CFR → MediaPipe Full → pose e timestamps
          → características temporais dos braços → candidatos
          → regras v2 → direto / uppercut / indeterminado
          → CSV, JSON, gráficos e vídeo com previsões

Anotações manuais ──→ avaliação separada das previsões
```

| Local | Conteúdo |
| --- | --- |
| `extract_pose.py` | Extração, vídeo com pose e metadados |
| `analyze_pose.py`, `prepare_arm_features.py`, `temporal_motion.py` | Leitura, geometria e sinais temporais |
| `detect_candidates.py` | Segmentação de movimentos candidatos |
| `classify_motion_phases.py` | Classificador determinístico atual, v2 |
| `classify_candidates.py`, `experiment_classification.py` | V1 e comparação histórica das seis variantes |
| `compare_candidates.py`, `evaluate_classification.py`, `consolidate_evaluation.py` | Avaliação temporal, de família e consolidação |
| `render_candidates.py`, `render_wrist_inspection.py`, `analyze_wrist_distance.py` | Visualização e inspeção |
| `annotations/` | Eventos manuais, inventário de vídeos, protocolo e guarda |
| `docs/` | Candidatura, reprodução, resultados interpretados, limites e evolução |
| `results/pilot/` | Relatórios numéricos selecionados para acompanhar o código |
| `tests/` | Testes de software; não medem desempenho em boxe |
| `data/`, `models/`, `outputs/` | Vídeos, modelo e execuções locais; excluídos do Git |
| `offline/SOURCES.md` | Proveniência e condições dos recursos; restantes materiais offline apenas locais |
| `strikes.md` | Convenções de boxe e evolução do âmbito |

Contexto pessoal, histórico de colaboração e guias locais (`AGENTS.md`,
`STATE.md`, `STEPS.md`, `OFFLINE_GUIDE.md`) não acompanham o repositório público.

Os scripts mantêm-se na raiz para preservar imports e comandos já verificados.
O ponto de entrada da documentação técnica é [docs/README.md](docs/README.md).

## Executar com um vídeo próprio

Ambiente verificado: **macOS ARM64, Python 3.13.13**, MediaPipe 1.2.2, CPU.
As versões completas estão em `requirements-offline.lock.txt`; não foi testada
uma instalação limpa noutro computador. FFmpeg é necessário para renderizar
o vídeo final. Instruções completas: [REPRODUCING.md](docs/REPRODUCING.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p models
curl -fL --retry 2 \
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task' \
  -o models/pose_landmarker_full.task
```

Colocar um vídeo com frequência de frames constante em `data/meu-video.mp4`.
Executar na raiz, usando pastas de saída novas:

```bash
.venv/bin/python extract_pose.py data/meu-video.mp4 --output-dir outputs/meu-video-pose
.venv/bin/python detect_candidates.py outputs/meu-video-pose --output-dir outputs/meu-video-candidates
.venv/bin/python classify_motion_phases.py outputs/meu-video-candidates/candidates.json --output-dir outputs/meu-video-v2
.venv/bin/python render_candidates.py outputs/meu-video-v2/classifications.json
```

A saída final inclui `classifications.csv`, `classifications.json` e
`classification-demo.mp4`, com previsões, timestamps e razões das regras.
Não recebe anotações manuais como entrada. As condições de gravação afetam
o resultado; estas instruções não implicam reconhecimento fiável noutro vídeo.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Os 35 testes passaram no ambiente local. Verificam geometria, tempos, regras,
matching e contabilidade da avaliação; os casos artificiais não são métricas
de reconhecimento. O piloto existente é reproduzível localmente com
`.venv/bin/python consolidate_evaluation.py`, dependendo das extrações e
previsões locais descritas no guia de reprodução.

## Dados e partilha

Vídeos, overlays, imagens de inspeção, pesos, caches e pacotes offline ficam
fora do Git. As fontes/condições conhecidas estão em
[offline/SOURCES.md](offline/SOURCES.md); a origem e as condições de partilha
dos vídeos `shbx` continuam por confirmar. Não são disponibilizados como um
dataset público. A cópia de resultados inclui tabelas e diagnósticos numéricos,
sem frames, vídeos ou sequências completas de pose.

Referência do modelo: [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker).
Não foi escolhida uma licença para o código do projeto; as dependências e os
recursos de terceiros mantêm as respetivas condições.
