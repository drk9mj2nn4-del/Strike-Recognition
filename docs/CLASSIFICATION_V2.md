# Classificação v2 — experiências com regras e fases locais

Atualizado em 10 de novembro de 2026.

Avaliação consolidada no Passo 5, sem reajuste das regras:
[piloto, métricas, sensibilidade temporal e erros](EVALUATION_PILOT.md).

A pedido do Pedro, foram testadas alternativas à v1, que atribuía família a
12 dos 41 candidatos. Foram preservados os 41 candidatos, IDs, braços do
detetor, timestamps, 33 anotações, matching 1:1 e tolerância ±125 ms. As duas
gravações continuam a ser desenvolvimento, sem teste independente.

## O que foi experimentado

Seis variantes explícitas, sem treino de modelo ou pesquisa automática de
uma grelha. Os perfis e limiares foram escolhidos manualmente após explorar
os dois vídeos. A comparação não é uma avaliação independente da seleção.

| Variante | Pares tempo/família concordantes | Família discordante | Sem referência, mas classificado | Candidatos indeterminados |
| --- | ---: | ---: | ---: | ---: |
| V1 original | 12 | 0 | 0 | 29 |
| Relaxar só ângulos | 12 | 4 | 0 | 25 |
| Relaxar ângulos e geometria | 15 | 5 | 0 | 21 |
| Selecionar fases nos dois braços | 21 | 2 | 3 | 15 |
| Fases, conservando decisões estritas da v1 | 23 | 2 | 3 | 13 |
| **Fases + v1 + não reutilizar a mesma fase (v2)** | **23** | **1** | **2** | **15** |

Os valores de cada linha somam os 41 candidatos. Os dois golpes sem candidato
mantêm-se em todas as variantes. Os quatro hooks não foram excluídos nem
convertidos em outra classe manual. Resultados/configurações completos:
[resumo reproduzível](../outputs/step4/classification-experiments/summary.md),
[CSV](../outputs/step4/classification-experiments/summary.csv). Executar
`.venv/bin/python experiment_classification.py` para os reproduzir.

## Como funciona a v2

1. **Conservar as decisões da regra estrita da v1.** Mantemos os sinais de
   extensão/ângulo quando já satisfazem esse perfil. Evita perder diretos
   evidentes ao aplicar uma regra alternativa pensada para outros casos.
2. **Nos restantes candidatos, inspecionar os dois braços.** Perto do instante
   do candidato, procurar o ponto mais alto do punho relativamente ao ombro,
   numa vizinhança de −120 a +80 ms. Procurar o ponto mais baixo nos 320 ms
   anteriores a esse topo. É uma hipótese geométrica de fase, sem usar as
   âncoras ou a classe manual. Janelas não atravessam NaN ou saltos de frames.
3. **Classificar a trajetória dessa fase.** Usar deslocamento, linearidade,
   posição inicial/final relativa ao ombro e, quando útil, ângulo do cotovelo.
   Distâncias mantêm a normalização pela escala projetada do braço da v1.
4. **Comparar a evidência dos braços.** O score é movimento normalizado ×
   linearidade, penalizado pela distância temporal ao candidato. Não é uma
   probabilidade. Hipóteses de classes opostas com scores próximos originam
   indeterminado. O braço escolhido não é uma anatomia validada manualmente.
5. **Não usar a mesma fase para classificar dois candidatos.** Para o mesmo
   braço, se as janelas partilham ≥60% das amostras da menor janela e os seus
   extremos ficam a ≤200 ms, o candidato posterior fica indeterminado. Pode
   perder movimentos sobrepostos; neste conjunto reduz duas classificações
   do golpe vizinho ou de uma fase já usada.

Os novos campos `classification_model_arm`, `classification_start_frame` e
`classification_end_frame` registam a decisão. O `model_arm` original continua
a ser o braço do detetor. **O timestamp do candidato não é retocado**, mesmo
que a fase selecionada termine antes/depois dele. A classificação é offline
e pode olhar até 80 ms depois do candidato, além do contexto do próprio detetor.

## Perfis geométricos adicionais

Exigem pelo menos três frames válidos e movimento líquido ≥0.15 escalas do
braço. Candidatos sem recolha observada permanecem indeterminados.

- **Uppercut:** preparação escolhida a ≥0.4 escalas abaixo do ombro, subida
  ≥0.4 escalas e componente ascendente ≥65% do deslocamento líquido. O punho
  termina no máximo 0.15 escalas abaixo do ombro, o ângulo final é ≤110° e
  a abertura angular é ≤45°.
- **Direto:** preparação menos baixa (≤0.35 escalas), subida ≥0.1 escalas,
  linearidade ≥0.6 e punho a terminar no máximo 0.15 escalas abaixo do ombro.
  Exige ainda extensão radial ≥0.05 escalas ou abertura ≥15°, ou um perfil
  fortemente ascendente (≥80% do deslocamento e movimento ≥0.35 escalas).
  Há um filtro de cruzamento do eixo vertical do ombro, usando o sinal da
  componente horizontal mediana como referência da imagem.
- A banda entre preparações 0.35 e 0.4 fica sem classe por esta regra. As
  decisões estritas da v1 são conservadas antes de procurar estes perfis.

São perfis locais destes enquadramentos, não definições universais dos golpes.
Um uppercut não exige baixar previamente a mão. Um direto pode ser ao corpo
ou projetar-se noutra direção em outra câmara. A referência horizontal não
identifica a direção física «para a frente». O perfil ascendente que dispensa
grande abertura 2D também não demonstra que o ângulo pequeno veio da projeção;
pode haver erro de pose, como no cotovelo do frame 52 já documentado.

## Resultado escolhido e erros que permanecem

| Vídeo | Diretos previstos | Uppercuts previstos | Indeterminados | Pares concordantes | Família discordante | Classificado sem par |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Front view | 10 | 2 | 8 | 11 | 1 | 0 |
| Upper body | 9 | 5 | 7 | 12 | 0 | 2 |

Contabilizando todas as referências:

| Família manual | Direto previsto | Uppercut previsto | Indeterminado | Sem candidato |
| --- | ---: | ---: | ---: | ---: |
| Direto (21) | 16 | 0 | 4 | 1 |
| Uppercut (8) | 0 | 7 | 0 | 1 |
| Hook (4; fora do âmbito) | 1 | 0 | 3 | 0 |

Assim, há **23/29 diretos e uppercuts com concordância de tempo e família**,
contra 12/29 na v1; quatro ficam indeterminados e dois sem candidato. Das
26 atribuições de família, 23 são concordantes, uma corresponde a hook e
duas não têm referência temporal. A comparação não valida braço ou fase
física; continua a ser apenas diagnóstico nos exemplos usados para ajustar.

Casos concretos a rever:

- Upper body 54, 59, 106 e 113 passam de indeterminados a uppercut ao usar a
  fase ascendente do outro braço, em vez da fase descendente que o detetor marcou.
- Front view 162: hook anotado passa a direto, apoiado no movimento do outro
  braço. É um erro real do quadro de comparação e mostra o risco de usar
  movimento correlacionado da outra mão para atribuir família.
- Upper body 100 e 156: direto previsto sem par. O segundo está 160 ms depois
  do direto manual 152, fora da tolerância. Os tempos não foram movidos para
  transformar este caso num acerto.
- Upper body 84 e 120: a proteção contra reutilizar fases evita atribuir-lhes
  a classe baseada no golpe vizinho. Continuam como candidatos indeterminados.
- O uppercut manual 62 e o direto manual 152 continuam sem candidato dentro
  da tolerância. A classificação não cria novos eventos para os recuperar.
- Diretos manuais em front view 15/121/157 e upper body 69 ficam indeterminados.

Artefactos:

- [Front view — vídeo v2](../outputs/step4/front-view-classification-v2/classification-demo.mp4)
- [Upper body — vídeo v2](../outputs/step4/upper-body-classification-v2/classification-demo.mp4)
- [Front view — relatório por referência](../outputs/step4/front-view-classification-v2/classification-evaluation.md)
- [Upper body — relatório por referência](../outputs/step4/upper-body-classification-v2/classification-evaluation.md)
- [Comparação visual das seis variantes](../outputs/step4/classification-experiments/comparison.png)
- [Front view — melhorias e erro no hook](../outputs/step4/front-view-classification-v2/classification-examples.png)
- [Upper body — melhorias e falsos candidatos classificados](../outputs/step4/upper-body-classification-v2/classification-examples.png)

`classify_motion_phases.py` não lê anotações. `experiment_classification.py` e
`evaluate_classification.py` usam-nas exclusivamente para medir/selecionar no
desenvolvimento. A v1 e os seus artefactos foram preservados. Não há modelo
de reconhecimento treinado, teste independente ou alegação de generalização.
