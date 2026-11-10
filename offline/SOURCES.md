# Proveniência e condições dos recursos offline

Consultado em 6 de novembro de 2026. Os ficheiros binários de vídeos, modelos,
wheels e livro não devem ser adicionados automaticamente ao GitHub. Os recursos
têm condições próprias; a licença do nosso código não as substitui.

## Modelo Full e referências técnicas

- Distribuidor: Google / MediaPipe.
- Ficheiro: `models/pose_landmarker_full.task`.
- URL: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task
- Ficha oficial local: `offline/references/blazepose-ghum-model-card.pdf`.
- Origem da ficha: https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf
- A ficha identifica a licença Apache 2.0. O pacote Tasks inclui deteção e
  estimação de pontos; os tamanhos do bundle e da rede descrita na ficha diferem.
- `pose_landmarker.py` e `base_options.py` foram copiados do MediaPipe 1.2.2
  instalado, para consultar a API offline. Cabeçalhos, LICENSE e NOTICE preservados.
- Documentação online: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

## Wikimedia Commons — dois vídeos

Autor declarado: **Evworo**, 15 de março de 2019. Licença **CC BY-SA 3.0 Unported**,
conforme as páginas dos ficheiros. Preservar crédito, ligação à licença e
indicação de alterações; derivados partilhados ficam sujeitos a share-alike.
Licença: https://creativecommons.org/licenses/by-sa/3.0/.
Cópia do texto legal: `offline/references/cc-by-sa-3.0.txt`.

### Boxing training

- Página: https://commons.wikimedia.org/wiki/File:Boxing_training.webm
- Download: https://upload.wikimedia.org/wikipedia/commons/5/5a/Boxing_training.webm
- Local original: `data/commons-boxing-training-original.webm`.
- Derivado: `data/commons-boxing-training.mp4`, 1280 × 720, 25 FPS CFR, sem áudio,
  H.264. Redimensionamento e conversão por FFmpeg, sem alteração da ordem temporal.
- Várias pessoas a treinar; exemplo de dificuldade para o pipeline de uma pose.

### Boxer

- Página: https://commons.wikimedia.org/wiki/File:Boxer.webm
- Download: https://upload.wikimedia.org/wikipedia/commons/a/a9/Boxer.webm
- Local original: `data/commons-boxer-original.webm`.
- Derivado: `data/commons-boxer.mp4`, 1280 × 720, 25 FPS CFR, sem áudio, H.264.
- Derivado adicional: `data/commons-boxer-focus.mp4`, recorte fixo do anterior:
  `crop=800:720:166:0`. Favorece o praticante principal; não é tracking nem
  isolamento perfeito da pessoa, nem uma gravação independente.
- Créditos sugeridos para os vídeos derivados e overlays: «Evworo, Boxer / Boxing
  training, Wikimedia Commons, CC BY-SA 3.0. Conversão, recorte e/ou sobreposição
  de pose pelo projeto Strike Recognition; sem endosso do autor.»

## KTH Human Actions — duas amostras oficiais

- Fonte: https://www.csc.kth.se/cvap/actions/.
- Condições declaradas: disponível para uso não comercial; citar a publicação
  indicada quando usado em publicações. Não confundir com licença CC ou autorização
  geral de redistribuição/comercialização. Página guardada em
  `offline/references/kth-dataset-page.html`.
- Publicação: Christian Schuldt, Ivan Laptev e Barbara Caputo, «Recognizing Human
  Actions: A Local SVM Approach», ICPR 2004.
- Downloads diretos oficiais:
  https://www.csc.kth.se/cvap/actions/person15_boxing_d1_uncomp.avi e
  https://www.csc.kth.se/cvap/actions/person15_handwaving_d1_uncomp.avi.
- Locais: `data/kth-person15-boxing.avi`, `data/kth-person15-handwaving.avi`.
- Ficheiros mantidos como descarregados, apenas com nomes locais mais curtos.
  160 × 120, 25 FPS. Uma pessoa isolada; baixa resolução é uma limitação importante.
- Os rótulos são de ação geral, não de cada golpe. Handwaving é um negativo
  para experiências futuras; não fornece anotações de eventos de boxe.

## Vídeos shbx — proveniência por confirmar

As gravações locais `shbx-*` foram selecionadas posteriormente pelo Pedro.
As respetivas fontes, autoria, condições de uso e independência entre gravações
ainda não estão confirmadas; o inventário atual é `annotations/videos.csv`.
Não se atribuem a estas gravações as licenças Commons ou condições KTH acima.
Os vídeos, recortes, frames e overlays ficam locais e excluídos do Git.
A versão upper body 3 a 2× é um derivado da mesma gravação, não dado independente.
Os resultados numéricos do piloto estão em `results/pilot/`, sem imagens ou
sequências completas de pose. Esta preparação não verifica novas permissões
de redistribuição dos vídeos.

## Recursos Python

`requirements-offline.lock.txt` regista as versões instaladas. `offline/wheels/`
contém os 19 pacotes e dependências descarregados do PyPI, para Python 3.13/macOS
ARM deste Mac. As licenças de cada pacote estão incluídas nas respetivas
distribuições. Não foram descarregados PyTorch, YOLO ou outro LLM.

## Livro de leitura alternativa

**Foundations of Computer Vision**, Antonio Torralba, Phillip Isola e William
Freeman, MIT Press, 2024. Fonte oficial: https://visionbook.mit.edu/.

O site declara CC BY-NC-ND. Foram guardadas páginas para consulta pessoal
offline, preservando conteúdo e créditos; links locais podem ter sido reescritos
pelo wget. Não traduzir, adaptar ou republicar o livro como material do projeto.

Seleção: prefácio/índice; capítulo 1, `taxonomy.html`; capítulo 2,
`simplesystem.html`; capítulo 3, `visionscience.html`; capítulo 46,
`motion_estimation_intro.html`. Não é uma cópia completa do livro e ligações
externas ou capítulos não guardados continuam a necessitar de rede.

## Fonte investigada mas não incluída

Pexels: foram encontrados e descarregados temporariamente dois vídeos. Após ler
https://www.pexels.com/terms-of-service/, que inclui restrições à recolha
automática para ML, foram retirados do pacote. Não foram usados na inferência.
Preferimos as condições explícitas das fontes acima para estes exercícios.
