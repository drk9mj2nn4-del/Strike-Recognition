# Observações da pose — Passo 2

## Atualização no Passo 3 — 9 de novembro

O Pedro inspecionou o frame 52 de `shbx-front view.mp4`, um direto anotado com
extensão máxima nesse instante, e identificou colocação incorreta do cotovelo
pelo MediaPipe. O ângulo 2D calculado a partir desses pontos foi 79.9°; não
representa a flexão real do braço e não prova, por si só, um efeito da projeção
frontal. Esta falha é uma observação do Pedro, não uma medição de erro de pose
pelo agente. Pontos brutos e exemplo foram preservados, sem correção manual
ou exclusão para facilitar o baseline. O ângulo projetado continua sujeito à
perspetiva e à qualidade das estimativas, como limitações distintas.

## Registo anterior do Passo 2

Registo em **8 de novembro de 2026** da inspeção visual do Pedro aos overlays
MediaPipe Full. Distinguir estas avaliações qualitativas das verificações de
exportação feitas pelo agente. Não há anotação de referência por frame, erro
medido em píxeis ou métricas de precisão. Os timestamps abaixo só são indicados
quando fornecidos ou já confirmados na inspeção anterior.

## Convenção de inspeção

- Amarelo: punho dentro da imagem com `visibility >= 0.5`.
- Anel roxo: coordenada estimada dentro da imagem, omitida pelo filtro original.
- Os anéis mostram previsões brutas, sem correção manual ou interpolação.
- A visibilidade física da mão na imagem e o valor `visibility` do modelo são
  conceitos distintos. Uma mão visível pode receber um valor baixo; uma
  estimativa com valor alto pode estar errada.

## Avaliação dos quatro vídeos pelo Pedro

### Front view

`data/shbx-front view.mp4` → `outputs/shbx-front-view-full/`

- Comportamento geral considerado muito bom e bastante aceitável.
- Na primeira inspeção, pareceu-lhe haver um ligeiro atraso dos pontos.
- **Revisão do Pedro em 8 de novembro:** voltou a analisar quase frame a frame
  e já não observa atraso aparente; considera que o modelo se comporta bem.
  A impressão inicial de lag foi retirada e não é uma falha confirmada.

### Full body

`data/shbx-full body.mp4` → `outputs/shbx-full-body-full/`

- A mão que permanece visível é acompanhada muito bem, segundo o Pedro.
- Distingue duas orientações laterais ao longo das mudanças de stance:
  quando conseguimos ver a barriga, com o pé mais próximo da câmara mais atrás
  do que o outro, considera o acompanhamento de ambas as mãos muito bom.
- Quando a stance muda e deixamos de ver a barriga, uma mão fica menos visível
  e o acompanhamento dessa mão piora bastante.
- Nessa orientação, observa repetidamente a estimativa do punho junto à cintura
  ou noutros locais errados, mesmo com parte da mão visível. Há também acertos
  apesar da pouca visibilidade; não é uma falha em todos os frames.
- O praticante não usa luvas, mas usa ligas. O Pedro considera que a repetição
  do problema enfraquece a hipótese inicial centrada nas luvas e reforça a
  relevância da orientação/oclusão. A mão mais oculta não foi identificada aqui
  por um índice anatómico nem foram fornecidos timestamps concretos.

### Upper body

`data/shbx- upper body.mp4` → `outputs/shbx-upper-body-full/`

- Avaliação semelhante a front view: considera que há boa visibilidade e que
  o modelo acompanha as posições muito bem ao longo da sua inspeção.
- Para o Pedro, reforça a relação entre boa visibilidade física e bom
  acompanhamento nestas condições.

### Upper view

`data/shbx- upper view.mp4` → `outputs/shbx-upper-view-full/`

- Comportamento considerado semelhante aos casos laterais mais difíceis.
- Quando as mãos estão visíveis, considera o acompanhamento bom.
- Quando ficam ocultas, observa erros suficientes para não confiar nas
  estimativas nesses trechos.

## Relação com as observações anteriores

- Focus: Pedro confirmou posições corretas do punho esquerdo nos frames 20 e
  28 (0,80 e 1,12 s), apesar da `visibility` abaixo de 0.5.
- Boxer: na inspeção de aproximadamente 6–12 s, relatou muitos erros. Por volta
  de 6–7 s, a luva esquerda está junto à cabeça, mas a estimativa por vezes fica
  junto à cintura. Em aproximadamente 7–9 s, relata erros frequentes no punho
  esquerdo durante movimentos rápidos, enquanto o direito parece melhor
  acompanhado. Identificou como desfavorável a orientação lateral/traseira.

## Interpretação provisória do agente

As observações do Pedro apoiam a orientação/oclusão como uma limitação prática
recorrente nestes exemplos. A mudança de orientação dentro de full body é
particularmente informativa, pois mantém a pessoa e o equipamento; ainda assim,
movimento e orientação variam em conjunto, sem controlo experimental.

As luvas não são necessárias para a falha observada: há erros semelhantes num
vídeo sem luvas. Isto não exclui que luvas ou ligas também possam contribuir.
Não foi verificada a composição dos dados de treino nem medido o efeito isolado
do equipamento. A expressão «modelo não reconhece a luva como corpo» permanece
uma hipótese explicativa, não um mecanismo demonstrado.

Não há fundamento para baixar globalmente o limiar com base nos dois acertos de
focus, pois as restantes inspeções encontraram erros relevantes com baixa
visibility. O limiar de desenho continua em 0.5. Também não foi demonstrado que
todos os pontos amarelos estejam corretos.

## Experiência sem equipamento adiada e continuação acordada

Um vídeo sem luvas nem ligas pode acrescentar evidência. Para investigar o efeito
do equipamento, a proposta é comparar a mesma pessoa, câmara, iluminação e
movimentos com e sem equipamento, incluindo a orientação lateral/traseira onde
o problema aparece. Um sucesso barehanded apenas de frente não isolaria a causa,
porque pessoa, perspetiva e outras condições poderiam explicar a diferença.
Gravações equivalentes com a mão visível e parcialmente oculta ajudariam a
separar os efeitos do equipamento e do ponto de vista.

O Pedro informou que não encontrou um vídeo adequado sem equipamento e poderá
gravar um posteriormente. Concordou em avançar para a distância punho–ombro,
adiando esta experiência. O agente não fez nova pesquisa ou extração para este
teste. Heavy e YOLO continuam fora do trabalho atual.

Já há uma primeira avaliação qualitativa da pose com acertos e falhas. A parte
seguinte do Passo 2, agora acordada pelo Pedro, é explorar a distância 2D
punho–ombro e relacioná-la com o movimento num trecho bem acompanhado. A primeira
exploração usa o lado esquerdo de upper body, com distância em píxeis calculada
após corrigir a escala de x/y pela largura/altura da imagem. A interpretação da
curva será discutida com ele; não foi iniciado reconhecimento de golpes.

O cálculo foi executado nos 165 frames de upper body e verificado pelo agente;
todos passam o filtro dos dois extremos. Curva completa e comparação dos frames
12/18/24 disponíveis em `outputs/shbx-upper-body-full/`, nos ficheiros
`left_wrist_shoulder_distance.png` e `left_wrist_shoulder_examples.png`.
As distâncias nesses três instantes são 159,85 / 389,39 / 78,10 px. O Pedro
reconheceu o sinal como distância/tempo e identificou a perda de informação de
direção: uma mão junto à cintura também pode estar afastada do ombro.

A seu pedido foram acrescentadas as componentes `Δx = width * (x_p - x_o)` e
`Δy = height * (y_p - y_o)`, com o mesmo filtro, em píxeis (direita/baixo positivos).
Não representam um plano físico 3D. Gráfico completo em
`left_wrist_shoulder_components.png` e comparação visual em
`left_wrist_shoulder_components_examples.png`, na mesma pasta de upper body.

O agente verificou e inspecionou dois exemplos reais de distância quase igual:
0,72 s, d=389,39 px, Δx=388,58 px, Δy=-25,20 px; e 4,28 s, d=384,94 px,
Δx=82,19 px, Δy=376,06 px. No segundo, o punho esquerdo está junto à cintura;
no primeiro, o vetor é quase horizontal. Ajuda a distinguir estas posições, sem
definir uma regra de golpe ou excluir golpes ao corpo. Detalhes e nove testes
em STATE.md.

## Potencial para distinguir trajetórias e encerramento do Passo 2

O Pedro salientou que separar componentes horizontais/verticais poderá ser útil
para distinguir golpes: por exemplo, uma trajetória que desce e depois sobe num
uppercut, comparada com uma extensão para a frente num jab. Esta intuição fica
registada como hipótese para a análise temporal posterior, não como capacidade
demonstrada. Não implica acrescentar uppercuts às classes iniciais.

A descida preparatória não é obrigatória num uppercut; a trajetória pode começar
da guarda. «Para a frente» é uma direção física relativa à pessoa, cuja projeção
nos eixos da imagem depende da câmara. As componentes 2D poderão fornecer sinais
discriminativos num cenário definido; ainda não há uma regra validada ou prova
de que distinguem classes por si só.

O Pedro concordou em encerrar o Passo 2 e passar ao Passo 3: definir um problema
pequeno, exemplos anotados e método inicial. Regras interpretáveis são a proposta
de primeiro baseline; aprendizagem com as sequências de pose fica como evolução
dependente de dados e avaliação, sem compromisso de treinar nesta primeira entrega.
