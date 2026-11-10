# Baseline de candidatos temporais — 9/11/2026

Este documento descreve a fase inicial de deteção sem família. Foi depois
acrescentado um [classificador experimental por regras](CLASSIFICATION.md)
para direto/uppercut/indeterminado, mantendo este detetor e os seus resultados.

O protótipo transforma pose de uma pessoa em movimentos candidatos a golpes.
Não atribui famílias, jab/cross ou combinações. O modelo pré-treinado é apenas
o extrator de pose MediaPipe Full; não foi treinado um reconhecedor de golpes.

## Método

1. Ler a pose já exportada, preservando todos os índices e timestamps.
2. Para cada braço do modelo (11/13/15 e 12/14/16), calcular o vetor
   `r = ((x_punho − x_ombro) × largura, (y_punho − y_ombro) × altura)`.
   Ombro e punho exigem coordenadas finitas, dentro da imagem e visibility ≥0.5.
   Falhas ficam como NaN, sem interpolação ou suavização adicional.
3. Calcular `v[t] = (r[t] − r[t−1]) / Δtempo`, em px/s, só entre observações
   válidas de frames consecutivos. O resultado fica associado ao segundo frame
   do intervalo; não é uma medição instantânea ou velocidade física em m/s.
4. Calcular a mediana de cada componente do vetor nos frames válidos do vídeo.
   É uma referência computacional aproximada; não é uma guarda detetada.
5. Usar a distância entre o vetor atual e essa referência como excursão.
   Procurar um máximo local com subida rápida e afastamento suficiente, seguido
   de diminuição parcial dentro de uma janela local. Não exige voltar à guarda.
6. Juntar candidatos quase simultâneos dos dois braços, preferindo maior
   proeminência. O braço exportado é o que sustentou a regra; não certifica
   qual mão executou o golpe.

O ângulo do cotovelo continua disponível na análise de características, mas
não decide candidaturas ou famílias nesta versão. O erro de cotovelo no frame
52 e a pouca extensão estimada noutros diretos desaconselham um limiar angular
obrigatório sem validação adicional. As anotações originais foram mantidas.

## Parâmetros desta execução

| Parâmetro | Valor | Interpretação |
| --- | ---: | --- |
| `min_excursion_px` | 100 px | Afastamento mínimo da referência mediana |
| `min_prominence_px` | 60 px | Subida e descida parcial mínimas da excursão |
| `min_speed_px_s` | 1200 px/s | Máxima rapidez na subida da excursão |
| `context_s` | 0.25 s | Contexto antes e depois do pico |
| `min_separation_s` | 0.16 s | Separação mínima entre candidatos selecionados |

Os parâmetros iniciais foram escolhidos durante a exploração dos dois vídeos;
não houve treino, pesquisa automática de parâmetros ou teste independente.
Os mesmos valores foram executados nos dois. Estão no JSON de cada execução e
podem ser alterados por argumentos CLI; `detect_candidates.py --help` mostra-os.
Limiar em píxeis depende da resolução, enquadramento e distância da pessoa.

Um pico perto do fim de uma sequência válida sem descida suficiente fica como
`unconfirmed_end`: pode ser fim do vídeo ou perda de observação. Não se inventa
recolha através de uma lacuna. Nos dois vídeos atuais existe um destes casos,
no frame final. As contagens abaixo incluem-os.

## Diagnóstico nos vídeos de desenvolvimento

O Pedro anotou 33 golpes e confirmou a cobertura dos dois vídeos: 15 em front
view e 18 em upper body. Há ainda um intervalo negativo explícito, frames
24–35 de front view. As duas âncoras de cada golpe não delimitam toda a ação.
Convenções e dados em [protocolo](../annotations/protocol.md) e
[events.csv](../annotations/events.csv).

Escolhida **provisoriamente** tolerância de ±125 ms para comparar o instante
principal manual com o pico de excursão previsto. A tolerância ainda deve ser
discutida com o Pedro. O algoritmo maximiza o número de pares um-para-um e
depois minimiza o erro temporal absoluto; duplicações não contam duas vezes.
Família e mão são ignoradas nesta comparação.

| Desenvolvimento | Candidatos | Referências | Pares | Sem par (candidato) | Sem par (referência) | Precisão temporal | Recall temporal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Front view | 20 | 15 | 15 | 5 | 0 | 75.0% | 100.0% |
| Upper body | 21 | 18 | 16 | 5 | 2 | 76.2% | 88.9% |

São números de diagnóstico sobre os dados usados para desenvolver o método,
sem demonstração de generalização. Um candidato perto de uma anotação pode
ser de outro braço ou de uma fase vizinha; correspondência temporal não prova
que foi encontrado o movimento físico correto. Por exemplo, front-009 é um
direto curto no frame 121, mas o seu par temporal é candidato do braço direito
no 123, que também está na preparação do uppercut seguinte. Este caso exige
inspeção manual e impede chamar a este quadro uma precisão de reconhecimento.

Resultados completos, incluindo cada par/erro, estão em:

- [Front view — relatório](../outputs/step4/front-view-candidates/comparison.md)
- [Upper body — relatório](../outputs/step4/upper-body-candidates/comparison.md)
- [Front view — vídeo](../outputs/step4/front-view-candidates/candidate-demo.mp4)
- [Upper body — vídeo](../outputs/step4/upper-body-candidates/candidate-demo.mp4)
- [Front view — exemplos de inspeção](../outputs/step4/front-view-candidates/inspection-examples.png)
- [Upper body — exemplos de inspeção](../outputs/step4/upper-body-candidates/inspection-examples.png)

Estes artefactos dependem dos dados locais; não são fornecidos por si só por
clonar o código. Fontes/licenças dos vídeos shbx ainda estão por confirmar.

## Falhas que já conseguimos localizar

- Front view: candidatos sem par em 91, 172, 189, 238 e 253. O último não tem
  recolha observada. No negativo explícito 24–35 não há instantes de candidato.
  Isso não prova ausência de falsos candidatos noutros trechos.
- Upper body: referências sem par em 62 (uppercut) e 152 (direto), a ±125 ms.
  Candidatos sem par em 84, 100, 129, 134 e 156. O pico em 156 fica a 160 ms
  do direto anotado em 152, fora da tolerância usada; pode ser outra fase.
- Upper body: o par do uppercut em 51 é candidato em 54 (+120 ms). Precisamos
  de observar se a regra está a selecionar a recolha ou a preparação seguinte.
- O hook no último frame 164 de upper body é exportado como candidato sem
  recolha observada; a anotação manual foi preservada.
- O uso de mediana pode confundir preparação baixa, recolha e ajustes com
  saídas ofensivas. Supressão temporal pode fundir golpes próximos. Oclusões,
  erro de pose, perspetiva e movimentos de câmara/tronco continuam a afetar tudo.

## O que é defensável mencionar na candidatura

> Desenvolvimento de um protótipo de análise de shadowboxing com estimação de
> pose pré-treinada, extração de características temporais dos braços e um
> baseline geométrico para localizar movimentos candidatos a golpes, com
> visualização e diagnóstico em vídeos anotados manualmente.

A classificação experimental por regras foi acrescentada depois e está descrita
em [CLASSIFICATION.md](CLASSIFICATION.md), com baixa cobertura e abstenções.
A avaliação em gravações independentes continua por fazer. O objetivo imediato
é apresentar um pipeline reproduzível e conseguir explicar o método e as
limitações, sem prometer reconhecimento robusto.
