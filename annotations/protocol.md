# Protocolo de anotação — Passo 3

**Atualização no Passo 5 (10/11):** avaliação consolidada, sem alterar eventos,
em [EVALUATION_PILOT.md](../docs/EVALUATION_PILOT.md). Mantido matching temporal
1:1 sem classe/mão e ±125 ms como referência histórica retrospectiva, com
sensibilidade a ±50/100/167/200 ms. Não é margem validada num teste independente
nem confirmação do Pedro de um protocolo final. As pendências de tolerância
nos registos históricos abaixo devem ser lidas com esta atualização.

Convenção refinada em 9 de novembro de 2026; documentação atualizada em 10/11.
O Pedro refinou a convenção: dois instantes
com significado dependente da família, sem exigir regresso à guarda. Ainda não
é um protocolo completo de avaliação. Este ficheiro prevalece sobre as
propostas anteriores do guia offline de 8/11 e sobre a versão só com pico.

**Passo 3 fechado com concordância explícita do Pedro em 9/11.** Método inicial:
regras geométricas temporais, combinando trajetória do punho relativa ao ombro,
evolução da flexão projetada do cotovelo e sequência ofensiva/recolha, sem
exigir regresso completo à guarda. É uma hipótese de baseline, ainda sem
reconhecimento demonstrado. Implementação e parâmetros ficam para o Passo 4.

## Cenário e dados

- Primeiro vídeo de desenvolvimento: `shbx-front-view`, uma pessoa a fazer
  shadowboxing. Extração MediaPipe Full já existente, sem nova inferência.
- Segundo vídeo de desenvolvimento: `shbx-upper-body`, com 18 golpes anotados
  pelo Pedro durante o Passo 4 (9 diretos, 6 uppercuts e 3 hooks). Lead/rear
  foram fornecidos explicitamente; não se inferiu mão anatómica ou guarda.
  A mensagem completa substitui a mensagem inicial com os primeiros cinco
  golpes: esses cinco foram registados apenas uma vez.
- O Pedro descreveu essencialmente diretos e uppercuts, com somente um hook,
  e confirmou depois a cobertura completa da sua lista de eventos. A revisão
  completa é dele; o agente inspecionou apenas exemplos pontuais.
- Não foi escolhido um vídeo de avaliação. Grupos de origem e relações entre
  gravações continuam por confirmar. Recortes da mesma gravação devem ficar
  no mesmo split; grupos desconhecidos não provam independência.
- O Pedro confirmou que os vídeos shbx foram obtidos na Internet. Isso não
  confirma origens independentes; URLs/licenças e relações ainda por verificar.

## Rótulos e unidade de anotação

- Uma linha por golpe, com uma âncora anterior (`reference_frame`), o seu
  significado (`reference_kind`), um instante principal (`peak_frame`) e família.
- `straight` = direto, agrupando jab/cross; `hook`; `uppercut`.
- `uncertain` permite registar uma dúvida sem forçar uma família.
- Jab/cross ficam para depois de demonstrarmos reconhecimento de diretos.
- `hand` é opcional: `left`, `right` ou `unknown`, sempre anatómica.
- `hand_role`: `lead`, `rear` ou `unknown`, separado da mão anatómica. O Pedro
  indicou em front view direita=lead e esquerda=rear; os lados que escreveu foram
  convertidos segundo essa indicação, preservando o relato em `notes`.
  Não inferimos se o vídeo está espelhado nem atribuímos uma guarda a partir
  disso. `hand` continua `unknown` até conferir a relação com os índices
  anatómicos do MediaPipe. Nos dois primeiros diretos há discrepâncias no
  relato dos lados/papel, registadas nas notas; não usar os papéis desses dois
  eventos como referência validada sem revisão.
- Guarda não é exigida nesta fase; `stance` pode ser `unknown`.
- `target`: `body` quando explicitamente indicado, senão `unknown` nesta
  anotação. O direto ao corpo continua `straight`, sem criar outra classe.
- `certainty`: `clear` ou `uncertain`; dúvidas podem ser explicadas em `notes`.
  Aqui refere-se à identificação da família; não certifica anatomia ou papel.

## Tempo

- Frames originais, primeiro índice 0. Front view tem 254 frames, a 24 FPS.
  Upper body tem 165 frames (0–164), a 25 FPS; os números da nova lista são
  índices de frames, não timestamps em segundos.
- Instante principal: culminar da fase ofensiva, próximo da transição para
  recolha/continuação; nos diretos, normalmente perto da extensão máxima.
- Convenções por família:

  | Família | `reference_kind` | `reference_frame` | `peak_frame` |
  | --- | --- | --- | --- |
  | Direto | `offensive_onset` | Começo do movimento ofensivo, saindo da guarda quando identificável | Maior extensão observada |
  | Uppercut | `lowest_preparation` | Ponto baixo da preparação escolhido neste exemplo | Culminar da fase ascendente ofensiva |
  | Hook | `lateral_preparation` | Afastamento lateral preparatório escolhido neste exemplo | Final da fase ofensiva |

- Ponto baixo/lateral não são início universal do golpe nem fases obrigatórias.
  As convenções de uppercut e hook descrevem as âncoras escolhidas nestes
  exemplos; não impõem preparação ampla a toda a técnica. Front view tem só
  um hook; upper body acrescenta três, ainda sem revisão visual pelo agente.
- Os dois instantes não representam a mesma fase em todas as famílias. Não
  comparar a sua diferença como se fosse uma duração total de golpe comum.
  `peak_frame` é um nome de campo; não implica pico de velocidade/distância.
- No uppercut descrito pelo Pedro, frame 16 é preparação baixa; a referência
  ofensiva escolhida é frame 20. Não usar altura máxima como regra universal.
- `start_frame` e `end_frame` são campos opcionais anteriores, mantidos vazios
  nos golpes desta versão; a âncora não é copiada para `start_frame`.
  Não exigir regresso à guarda nem eventos sem sobreposição.
- Incerteza de alguns frames é registada sem inventar precisão. Tolerância
  temporal e correspondência um-para-um na avaliação ainda por definir.

## Cobertura e negativos

- Em front view há 15 golpes fornecidos pelo Pedro: 12 diretos, 2 uppercuts e
  1 hook. As últimas 11 anotações chegam ao par 222–224. O frame 119–121 é
  mantido como direto com pouca extensão, conforme o relato; não foi excluído
  para facilitar a regra. Há um direto explicitamente ao corpo em 77–79.
- O Pedro confirmou que a lista inclui todos os golpes que observou até ao
  fim do vídeo. Cobertura revista por ele: frames 0–253. Esta é confirmação
  manual do Pedro; não foi afirmado que o agente reviu todos os eventos.
- Intervalos claramente sem golpe podem ser anotados como `non_punch`, com
  início/fim e instante principal vazio. Outros golpes não são `non_punch`.
- O Pedro confirmou especificamente o intervalo inclusivo 24–35 como apenas
  guarda/movimentos sem golpe. Guardado como `front-negative-001`, sem âncora
  ou instante principal. O frame 20 do uppercut não está neste intervalo.
- Em upper body há 18 eventos (`upper-001` a `upper-018`), com pares entre
  3–6 e 159–164: 9 diretos, 6 uppercuts e 3 hooks; 10 lead e 8 rear. Seguem
  as mesmas convenções por família, com `start_frame`/`end_frame` vazios.
  O Pedro confirmou explicitamente que a lista inclui todos os golpes que
  observou no vídeo completo (frames 0–164). Esta é confirmação manual dele,
  não uma revisão visual integral pelo agente. Não foram indicados intervalos
  negativos específicos; não converter lacunas entre âncoras em negativos
  automaticamente, pois as âncoras não delimitam todo o movimento do golpe.
- O hook `upper-018` tem instante principal no frame final 164. Preservado
  conforme fornecido, sem excluir ou mudar a certeza da família; a continuação
  posterior ao instante principal não é observável neste vídeo.
- Total atual: 33 golpes (21 diretos, 8 uppercuts, 4 hooks) e 1 intervalo
  negativo, em 34 linhas de dados. São referências manuais, não previsões.
- Casos incertos/cortados exigem registo explícito e não exclusão silenciosa.

## Pendências para implementação e avaliação

Conferir a correspondência dos braços e discrepâncias iniciais; confirmar
grupos de origem e reservar avaliação se possível. Por agora só há dados
designados para desenvolvimento: resultados neste vídeo são verificações de
desenvolvimento, não desempenho independente. Escolher regras/parâmetros no
desenvolvimento durante o Passo 4. Não usar eventos de referência como entrada
do detetor. Não avaliar famílias com um único exemplo como se houvesse
evidência robusta. A limitação de separação permanece explícita ao fechar o 3;
não foi inventado um split independente nem acordada tolerância de avaliação.

**Diagnóstico inicial do Passo 4:** o agente implementou candidatos sem família
e uma comparação temporal um-para-um a ±125 ms nos dois vídeos. Esta tolerância
é provisória para diagnóstico de desenvolvimento, ainda por discutir com o
Pedro; não altera a convenção manual das âncoras. Método/resultados/limitações
em `docs/BASELINE.md`. Não é teste independente nem avaliação de classes/mãos.

**Extensão seguinte do Passo 4 autorizada pelo Pedro:** classificador por regras
direto/uppercut/indeterminado. Avaliação separada em `docs/CLASSIFICATION.md`,
mantendo o matching temporal sem usar a classe para escolher pares. Hooks
continuam com rótulo manual `hook` e visíveis como fora do âmbito; abstenções
do classificador não foram copiadas para o ground truth. Não houve alteração
das anotações ou exclusão de golpes para facilitar as regras.

**Experiências v2 (10/11):** comparação de relaxamentos e seleção de fases nos
dois braços em `docs/CLASSIFICATION_V2.md`. Mantidos todos os candidatos,
timestamps, referências e pares temporais usados na v1. Limiar de tempo igual
e matching sem classe; 1 hook mal classificado e 2 candidatos classificados
sem referência estão incluídos nos resultados. Não é teste independente.

## Verificações exploratórias do agente

- Em 11/15/39/52/121/126 foram comparados os pontos 11–13–15 e 12–14–16
  com os frames originais. Nos exemplos recentes 52/126, o braço descrito como
  lead pelo Pedro corresponde ao braço 12–14–16. Isto não resolve as
  discrepâncias dos relatos iniciais nem demonstra estabilidade em todo o vídeo.
- Comparação pontual do vetor ombro 12 → punho 16, com filtro 0.5 e conversão
  em píxeis antes da norma: direto 50→52, d=181.1→271.4 px; uppercut 123→126,
  d=388.4→364.7 px; hook 160→162, d=237.6→464.8 px. No negativo 24–35,
  d varia entre 181.3 e 315.4 px nesse braço. Logo, um limiar superior de
  distância isolado não separa estes exemplos: a guarda sobrepõe o direto e
  o hook também produz distância elevada. Não são métricas de reconhecimento.
- O Pedro concordou em analisar o ângulo do cotovelo para fundamentar a escolha
  do primeiro método. Calculado o ângulo interior entre ombro−cotovelo e
  punho−cotovelo após conversão x/y para píxeis: arccos do produto escalar
  dividido pelas normas, com cos limitado a [−1,1]. Filtrar os três pontos
  por visibility ≥ 0.5, coordenadas finitas e dentro da imagem. Segmento
  nulo produz NaN. Sem suavização ou interpolação.
- Exportados 254 frames preservando índices e timestamps, com ângulos de ambos
  os cotovelos; todos passam o filtro neste vídeo, o que não prova precisão.
  Verificações numéricas: 0/90/180°, segmento nulo e proporção retangular da
  imagem. CSV em `outputs/step3/front-view-elbow-angles.csv`; comparação em
  `front-view-elbow-angle-examples.png` na mesma pasta, inspecionada pelo agente.
- Braço 12–14–16: direto 50→52, 30.5→79.9°; uppercut 123→126,
  100.2→67.4°; hook 160→162, 38.1→131.0°; guarda 24–35, 30.2–58.8°.
  No braço 11–13–15, direto de pouca extensão 119→121, 11.8→9.5°.
  Ângulo próximo de 180° não é um critério fiável de direto nestes exemplos.
  O escalar mede flexão projetada; não identifica plano físico horizontal/
  vertical. Sequência/direção poderão ajudar, ainda sem regra demonstrada.
- **Correção após inspeção do Pedro:** no frame 52 identificou uma colocação
  errada do cotovelo pelo MediaPipe. Os 79.9° são o ângulo das estimativas
  incorretas nesse instante, não uma medição da flexão real. Este exemplo
  não demonstra, por si só, que a projeção frontal causa esse valor. A projeção
  continua a ser uma limitação geral, distinta do erro de pose identificado.
  Mantidos os pontos brutos, o valor calculado e o evento anotado; sem correção
  manual ou exclusão do caso. A informação vem da inspeção do Pedro.
- Não foi implementado o detetor nem ajustados limiares nesta verificação.
  O método geral acordado é regras geométricas temporais; Passo 3 fechado,
  implementação e ajuste das regras no Passo 4. Não é obrigatório um treino
  aprendido posterior; depende de dados e benefício experimental.
