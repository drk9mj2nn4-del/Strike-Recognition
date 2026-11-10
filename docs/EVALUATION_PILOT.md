# Avaliação piloto — protótipo v2

10 de novembro de 2026 · Passo 5 · diagnóstico de desenvolvimento.

Preparação da entrega no Passo 6: [cópia numérica consultável sem vídeos](../results/pilot/README.md),
[texto para a candidatura](CANDIDATURA.md) e [próximas experiências](NEXT_STEPS.md).
Links para imagens/vídeos em `outputs/` neste relatório são apenas locais.

**Resultado principal:** a ±125 ms, 23 dos 29 diretos/uppercuts anotados têm
par temporal com família concordante. Das 26 atribuições de família, 23 são
concordantes; uma corresponde a hook e duas não têm referência dentro da
tolerância. Quatro golpes-alvo têm abstenção e dois não têm candidato.
As regras foram ajustadas nestes exemplos: estes números não estimam
desempenho em pessoas, câmaras ou gravações novas.

## Dados e condições

| Vídeo | Frames / FPS | Diretos | Uppercuts | Hooks | Utilização |
| --- | --- | ---: | ---: | ---: | --- |
| Front view | 254 / 24 | 12 | 2 | 1 | Desenvolvimento |
| Upper body | 165 / 25 | 9 | 6 | 3 | Desenvolvimento |
| Total | 419 frames, cerca de 17,18 s | 21 | 8 | 4 | Sem teste independente |

Anotações em [events.csv](../annotations/events.csv), com convenções em
[protocol.md](../annotations/protocol.md). Pedro forneceu as famílias/âncoras
e confirmou a cobertura dos golpes nos dois vídeos completos. O agente
verificou a contabilidade e exemplos pontuais; não realizou nova anotação
integral nem revisão independente das referências. Lead/rear e mão anatómica
não são pontuados.

As duas gravações foram exploradas para definir e selecionar regras. Não há
treino de classificador, mas há ajuste manual aos dados; isso também exige
um teste separado para medir generalização. Origens/grupos de gravação ainda
por confirmar; não se presume independência. Upper body 3 e a cópia a 2×
não entram nas métricas: não têm anotações e são a mesma gravação.

## Procedimento preservado

1. Ler as previsões v2 guardadas, sem executar/ajustar as regras.
2. Comparar o timestamp do candidato com o timestamp do `peak_frame` manual
   no JSONL de pose. São tempos na reprodução arredondados ao milissegundo,
   não medições calibradas da velocidade física.
3. Matching um-para-um: maximizar pares dentro da tolerância inclusiva e
   depois minimizar a soma dos erros absolutos, sem usar família ou braço.
4. Comparar famílias depois do matching. Duplicações não contam duas vezes
   para a mesma referência; candidatos adicionais sem par permanecem extras.
5. Manter hooks, abstenções, referências sem candidato e candidatos sem
   recolha no fim. Não deslocar tempos nem excluir erros.

±125 ms mantém a referência histórica dos relatórios do Passo 4: cerca de
três frames nestes vídeos. É uma convenção nominal retrospectiva deste
piloto, não uma margem validada com incerteza de anotação medida ou escolhida
previamente num teste. Pedro ainda não confirmou esta margem como protocolo
final. A análise de sensibilidade abaixo evita depender apenas dela.

## Contabilidade a ±125 ms

| Vídeo | Candidatos | Pares temporais / referências | Tempo e família concordantes / alvos | Família errada | Classificados sem par |
| --- | ---: | ---: | ---: | ---: | ---: |
| Front view | 20 | 15/15 | 11/14 | 1 hook → direto | 0 |
| Upper body | 21 | 16/18 | 12/15 | 0 | 2 |
| Total | 41 | 31/33 | 23/29 | 1 | 2 |

| Família manual | Direto previsto | Uppercut previsto | Indeterminado | Sem candidato |
| --- | ---: | ---: | ---: | ---: |
| Direto (21) | 16 | 0 | 4 | 1 |
| Uppercut (8) | 0 | 7 | 0 | 1 |
| Hook (4; fora do classificador) | 1 | 0 | 3 | 0 |

Há 26 atribuições de família (19 diretos, 7 uppercuts) e 15 candidatos
indeterminados. Destes 15, sete têm par manual (quatro diretos e três hooks)
e oito não têm par. Os dez candidatos sem par são oito indeterminados e dois
diretos previstos. As 33 referências e os 41 candidatos ficam contabilizados.

Métricas agregadas por contagem de eventos (*micro*), condicionadas a este matching:

- **Precisão tempo/família = 23/26 = 88,5%:** concordâncias entre todas as
  atribuições de família, incluindo nos erros o hook e os dois extras.
- **Recall nas famílias-alvo = 23/29 = 79,3%:** inclui no denominador os
  quatro diretos indeterminados e os dois golpes-alvo sem candidato.
- **F1 = 2×23/(26+29) = 83,6%.** Não é accuracy por frame ou em três classes.
- Deteção temporal, ignorando família: 31/41 = 75,6% de precisão e
  31/33 = 93,9% de cobertura. Inclui hooks e abstenções.

Uma concordância de tempo/família pode apoiar-se numa fase ou braço vizinho.
Estas métricas são diagnósticos do procedimento, não certificação de
correspondência física de cada golpe. Indeterminado é abstenção de família,
não ausência de golpe.

A v1 tinha 12/29 concordâncias e 12 atribuições, sem discordâncias ou extras
classificados nestes dados. A v2 passa a 23/29 com três atribuições não
concordantes. É uma troca observada entre cobertura e erros no desenvolvimento;
a seleção entre variantes não tem avaliação independente.

## Sensibilidade à tolerância

Mesmas previsões, anotações e algoritmo; só muda a tolerância do avaliador.

| Tolerância | Pares temporais /33 | Concordantes /29 | Família errada | Referências indeterminadas | Sem candidato | Classificados sem par |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ±50 ms | 26 | 19 | 1 | 6 | 7 | 6 |
| ±100 ms | 30 | 22 | 1 | 7 | 3 | 3 |
| **±125 ms** | **31** | **23** | **1** | **7** | **2** | **2** |
| ±167 ms | 32 | 24 | 1 | 7 | 1 | 1 |
| ±200 ms | 32 | 24 | 1 | 7 | 1 | 1 |

O uppercut manual de upper body 51 tem candidato em 54 (+120 ms), aceite a
125 ms e excluído a 100 ms. O direto manual 152 passa a ter par em 156
(+160 ms) a partir de 167 ms. Não adotámos essa margem para o contar como
acerto nominal. Margens largas podem associar movimentos vizinhos em
combinações rápidas; mais pares não demonstram melhor deteção física.

## Erros e limites de interpretação

| Caso | Observação nos artefactos existentes | Implicação |
| --- | --- | --- |
| Front 162 | Hook manual, direto previsto; regra usa movimento correlato do outro braço | Erro de família preservado |
| Upper 100 | Direto previsto sem par temporal | Extra classificado, incluído contra a precisão |
| Upper 152 → candidato 156 | Atraso de 160 ms | Sem candidato e extra a ±125 ms; par só com margem maior |
| Upper 62 | Uppercut sem candidato mesmo a ±200 ms | Falha temporal; classificação não cria eventos |
| Front 15/121/157; upper 69 | Diretos com candidato indeterminado | Quatro abstenções, não acertos |
| Front 121 → candidato 123 | Próximo da preparação do uppercut seguinte | Par temporal não prova deteção física desse direto |
| Upper 51 → candidato 54 | Concordante a +120 ms, fase selecionada no outro braço | Sensível à margem; braço/fase não validados |
| Front 52 | Cotovelo incorreto identificado anteriormente pelo Pedro | Não atribuir ângulo pequeno apenas à projeção; dados preservados |
| Front 253 e upper 164 | Recolha não observável; indeterminados | Incluídos; hook manual final não removido |

O negativo explícito de front, frames 24–35 inclusive, não contém instantes
de candidatos. São só 12 frames, cerca de 0,5 s; não demonstra rejeição robusta
de movimentos sem golpe. Upper body não tem negativos específicos anotados.
Não há base para accuracy/especificidade por frame; lacunas entre âncoras não
foram convertidas em negativos.

Montagens existentes reinspecionadas pelo agente neste passo, sem novos rótulos:
[front view](../outputs/step4/front-view-classification-v2/classification-examples.png)
e [upper body](../outputs/step4/upper-body-classification-v2/classification-examples.png).
Mostram exemplos concordantes e os três erros classificados. Imagens estáticas
não substituem revisão temporal completa. Vídeos e relatórios por evento em
[CLASSIFICATION_V2.md](CLASSIFICATION_V2.md).

## Reprodução e verificação

Na raiz do projeto, com o ambiente e resultados do Passo 4 existentes:

```sh
.venv/bin/python consolidate_evaluation.py
.venv/bin/python -m unittest discover -s tests -v
```

Saídas em [outputs/step5](../outputs/step5/summary.md): resumo, `evaluation.json`
com resultados por vídeo/tolerância e hashes SHA-256 das entradas,
`references.csv` com as 33 referências na margem nominal e `sensitivity.csv`
com as cinco margens. Só esta pasta é regenerada. O script confirma igualdade
integral com os dois relatórios v2 a ±125 ms e que as entradas não mudam.

**Verificado pelo agente:** consolidação executada; igualdade com os relatórios
preservados; 35 testes passados, incluindo hooks/extras, abstenções/perdas nos
denominadores e ausência de taxas quando o denominador é zero. Testes de
geometria usam dados artificiais e não medem desempenho em boxe. Sem nova
extração de pose, ajuste de regras, alteração de anotações de eventos,
publicação ou teste independente.

**Continuidade no Passo 6:** Pedro pediu preparar a candidatura com estes
resultados, dando destaque aos limites e às experiências seguintes, sem novas
funcionalidades ou publicação. Isso não equivale a nova validação manual
integral dos eventos nem a confirmação de ±125 ms como protocolo final.

## Formulação curta para a candidatura

> Desenvolvi um protótipo de análise de shadowboxing que combina estimação de
> pose com MediaPipe e regras geométricas temporais para identificar candidatos
> a diretos e uppercuts, com possibilidade de abstenção. Num piloto de
> desenvolvimento com dois vídeos e 33 golpes anotados manualmente, 23 dos 29
> diretos/uppercuts tiveram correspondência temporal e de família a ±125 ms.
> A análise inclui abstenções, golpes perdidos e falsos positivos; a avaliação
> em gravações independentes fica como trabalho seguinte.
