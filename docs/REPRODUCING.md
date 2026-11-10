# Reprodução e execução

Executar na raiz do projeto. Consultar resultados, analisar um vídeo próprio
e reconstruir o piloto original exigem conjuntos de ficheiros diferentes.

## Consultar o piloto sem instalar dependências

[EVALUATION_PILOT.md](EVALUATION_PILOT.md) contém a interpretação.
[results/pilot](../results/pilot/README.md) guarda resumo, relatório JSON,
33 linhas por referência e sensibilidade às cinco tolerâncias. Não é necessário
ter acesso aos vídeos para ler estes resultados. Esta cópia documenta uma
execução histórica; não permite recalcular o matching sem os dados locais.

## Preparar o ambiente

Ambiente executado: Mac ARM64, Python 3.13.13, MediaPipe 1.2.2,
OpenCV contrib 4.14.0.94, NumPy 2.5.4 e Matplotlib 3.11.2. Inferência em CPU.
Não foi verificada instalação limpa noutro sistema.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.txt` fixa MediaPipe e intervalos das restantes dependências diretas.
`requirements-offline.lock.txt` regista o ambiente completo verificado,
sem garantir compatibilidade entre sistemas. Para tentar replicar essas versões
no mesmo tipo de ambiente, usar esse ficheiro em vez de `requirements.txt`.
Não instalar dois pacotes OpenCV em paralelo.

FFmpeg/ffprobe são ferramentas externas ao pip. O renderer chama FFmpeg pelo
PATH. Verificar disponibilidade antes de gerar o vídeo final e obter o modelo:

```bash
ffmpeg -version
ffprobe -version
mkdir -p models
curl -fL --retry 2 \
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task' \
  -o models/pose_landmarker_full.task
```

O download requer rede; a execução usa ficheiros locais. O modelo e os vídeos
não acompanham o código. Proveniência em [SOURCES.md](../offline/SOURCES.md).

## Analisar um vídeo próprio

Inicialmente usar uma pessoa, boa iluminação e câmara fixa. Isto facilita a
inspeção, sem garantir reconhecimento. Colocar o vídeo em `data/meu-video.mp4`.
Confirmar que é **CFR**: o extrator calcula timestamps por índice/FPS e não
implementa leitura temporal VFR. Um FPS médio não prova CFR e a reprodução
em câmara lenta não representa necessariamente a velocidade física.

```bash
.venv/bin/python extract_pose.py data/meu-video.mp4 --output-dir outputs/meu-video-pose
.venv/bin/python detect_candidates.py outputs/meu-video-pose --output-dir outputs/meu-video-candidates
.venv/bin/python classify_motion_phases.py outputs/meu-video-candidates/candidates.json --output-dir outputs/meu-video-v2
.venv/bin/python render_candidates.py outputs/meu-video-v2/classifications.json
```

| Saída | Conteúdo |
| --- | --- |
| `outputs/meu-video-pose/pose.jsonl` | Um registo por frame, incluindo frames sem pose |
| `outputs/meu-video-pose/metadata.json` | Modelo/hash, versões, dimensões, FPS, contagens e estado |
| `outputs/meu-video-pose/overlay.mp4` | Sobreposição parcial da pose, sem áudio |
| `outputs/meu-video-candidates/` | Candidatos CSV/JSON, sinais e gráfico |
| `outputs/meu-video-v2/classifications.csv` e `.json` | Previsões, tempos, fases e razões das regras |
| `outputs/meu-video-v2/classification-demo.mp4` | Vídeo final com previsões, H.264, sem áudio |

O extrator e o renderer recusam sobrescrever os seus destinos; escolher nomes
novos para repetir. Outros programas podem regenerar tabelas/gráficos no destino.
Os JSON de candidatos guardam `pose_dir` absoluto: ao mover o projeto ou copiar
execuções entre computadores, regenerar candidatos e classificações a partir
da pose no novo local. A cópia histórica numérica não depende desses caminhos.

Verificar `status: complete`, contagens, timestamps, orientação e duração do
vídeo e observar os pontos nos braços. `complete` significa que terminou o ciclo
de leitura; uma falha intermédia de descodificação pode parecer fim de vídeo
ao OpenCV. `visibility`/`presence` e pose em todos os frames não certificam
punhos ou cotovelos corretos.

As coordenadas `x/y` são normalizadas pela largura/altura; `y` cresce para baixo.
A geometria considera a proporção da imagem. Os pontos 3D estimados não são
medição calibrada. A análise é offline e usa o vídeo completo/contexto posterior.
Os scores das regras não são probabilidades.

## Reproduzir o piloto original no ambiente local

São necessários os vídeos `shbx` originais, as extrações e os resultados dos
Passos 4–5. Não estão incluídos na futura entrega de código. A origem e as
condições de redistribuição dessas gravações ainda não estão confirmadas;
não existe download público preparado pelo projeto para reconstruir o piloto.

Com os resultados locais preservados, consolidar sem executar novamente regras:

```bash
.venv/bin/python consolidate_evaluation.py
```

O programa lê as previsões v1/v2 em `outputs/step4/`, os JSONL/metadados de pose
e `annotations/events.csv` e `videos.csv`. Calcula cinco tolerâncias, confirma
igualdade com as avaliações v2 nominais preservadas, verifica hashes das entradas
antes/depois e escreve em `outputs/step5/`.

Para reconstruir desde os vídeos, usar uma cópia de trabalho sem essas pastas
de saída, preservando a execução histórica. Exemplo para front view:

```bash
.venv/bin/python extract_pose.py 'data/shbx-front view.mp4' --output-dir outputs/shbx-front-view-full
.venv/bin/python detect_candidates.py outputs/shbx-front-view-full --output-dir outputs/step4/front-view-candidates
.venv/bin/python classify_candidates.py outputs/step4/front-view-candidates/candidates.json --output-dir outputs/step4/front-view-classification
.venv/bin/python classify_motion_phases.py outputs/step4/front-view-candidates/candidates.json --output-dir outputs/step4/front-view-classification-v2
.venv/bin/python evaluate_classification.py outputs/step4/front-view-classification-v2/classifications.json --video-id shbx-front-view --tolerance-ms 125
.venv/bin/python render_candidates.py outputs/step4/front-view-classification-v2/classifications.json
```

Repetir para `data/shbx- upper body.mp4`, substituindo `front-view` por
`upper-body` em todos os destinos e no ID `shbx-upper-body`. Os destinos de pose
devem corresponder aos do inventário `annotations/videos.csv`. Só depois
executar a consolidação. A comparação histórica das seis variantes é opcional:
`experiment_classification.py`; não é necessária para aplicar a v2.

As anotações são usadas pelos avaliadores e pela seleção de variantes durante
o desenvolvimento; não entram na extração, deteção ou classificação de um vídeo.
Reexecutar inferência pode variar com ambiente/versão. Os hashes identificam a
execução original, sem garantir resultados bit a bit numa instalação nova.

## Verificações e limites da reprodução

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python extract_pose.py --help
.venv/bin/python detect_candidates.py --help
.venv/bin/python classify_motion_phases.py --help
.venv/bin/python evaluate_classification.py --help
.venv/bin/python render_candidates.py --help
```

No Passo 6 foram verificados os 35 testes, as ajudas das CLI documentadas e a
igualdade da consolidação com os resultados preservados. Não houve nova
inferência, treino, ajuste de regras ou instalação limpa. Testes de software
não substituem avaliação em vídeos independentes.
