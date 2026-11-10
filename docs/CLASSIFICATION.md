# Primeiro protótipo de classificação por regras

Esta é a **v1**, preservada para comparação. A versão atual, após experiências
com relaxamento e seleção de fases dos dois braços, está em
[CLASSIFICATION_V2.md](CLASSIFICATION_V2.md).

Implementado em 9/11/2026, após autorização do Pedro para experimentar
**direto / uppercut / indeterminado** antes da candidatura. Sem treino de modelo.
É uma primeira experiência de classificação em vídeos de desenvolvimento,
com abstenção frequente, ainda sem validação em gravação independente.

## Entrada, janela e saída

`classify_candidates.py` recebe o JSON do detetor e a pose da mesma extração.
Não lê `events.csv`, papéis lead/rear, IDs de eventos manuais ou famílias reais.
Cada candidato mantém o seu timestamp, braço e janela do mínimo local de
excursão (`onset_frame`) ao pico do candidato (`frame_index`). Essa janela é
geométrica; não certifica início/fim da fase ofensiva. O detetor não foi
reajustado para melhorar os resultados da classificação.

Por braço, calculamos como escala a mediana da soma dos comprimentos 2D
ombro–cotovelo e cotovelo–punho nos frames válidos. Distâncias divididas por
essa escala deixam de depender diretamente do número de píxeis, mas continuam
dependentes da perspetiva e dos erros da pose. Não são unidades físicas.

As características incluem deslocamento horizontal/vertical, aumento da
distância punho–ombro, ângulo inicial/final do cotovelo, abertura angular,
linearidade do trajeto e movimento do cotovelo relativamente ao do punho.
Linearidade é deslocamento líquido dividido pelo comprimento do trajeto 2D.
Todos os valores e a razão da decisão ficam em `classifications.csv/.json`.

## Regras desta versão

Todas exigem pelo menos três frames contínuos e deslocamento líquido de pelo
menos 0.2 escalas do braço. Os três pontos têm de passar o filtro 0.5 e ser
finitos/dentro da imagem durante toda a janela. Não se interpola por NaN.
Candidatos sem recolha parcial observada ficam indeterminados.

**Direto:** ângulo final ≥80°, abertura ≥35°, aumento da distância punho–ombro
≥0.15 escalas, linearidade ≥0.7, deslocamento do cotovelo no máximo 1.25 vezes
o deslocamento do punho. O movimento não pode ser predominantemente descendente:
componente descendente líquida no máximo 20% do deslocamento líquido.

**Uppercut:** subida ≥0.25 escalas, componente ascendente pelo menos 80% do
deslocamento líquido, ângulo final ≤80° e abertura angular no máximo 20°.
Exige ainda ângulo inicial ≥45° ou punho a terminar quase sobre o ombro na
imagem (separação horizontal ≤0.15 escalas e punho acima do ombro).
Esta alternativa vertical depende particularmente da câmara.

**Indeterminado:** nenhum padrão é satisfeito, há conflito, movimento insuficiente,
dados em falta ou recolha não observável. Não quer dizer `non_punch` nem que o
golpe físico não aconteceu. Hooks continuam anotados como hook e não passam
a ser referências de classe indeterminada.

Os limiares constam em `ClassificationConfig` e no JSON da execução. Foram
escolhidos manualmente após explorar ambos os vídeos; não são regras universais,
parâmetros aprendidos ou uma pesquisa validada em teste separado. Ainda podem
confundir hooks e outros movimentos em vídeos novos.

## Resultados, incluindo todos os golpes e abstenções

Mantida a comparação temporal 1:1 a ±125 ms, provisória, com os timestamps
originais. O matching ignora a classe para não favorecer previsões certas.

| Vídeo | Diretos previstos | Uppercuts previstos | Indeterminados | Pares com família concordante | Pares com família discordante |
| --- | ---: | ---: | ---: | ---: | ---: |
| Front view | 3 | 2 | 15 | 5 | 0 |
| Upper body | 6 | 1 | 14 | 7 | 0 |

São **12 previsões de família em 41 candidatos**. As outras 29 são abstenções.
As 12 têm par temporal com a mesma família manual nesta experiência, mas o
conjunto foi usado para desenvolver as regras e o matching não valida braço
ou fase física. Não apresentar este subconjunto como 100% de precisão.

Considerando todos os golpes anotados nos dois vídeos:

| Família manual | Direto previsto | Uppercut previsto | Indeterminado | Sem candidato |
| --- | ---: | ---: | ---: | ---: |
| Direto (21) | 9 | 0 | 11 | 1 |
| Uppercut (8) | 0 | 3 | 4 | 1 |
| Hook (4; fora do âmbito) | 0 | 0 | 4 | 0 |

Assim, apenas **12 dos 29 diretos/uppercuts anotados** têm atribuição de família
concordante com a referência; 15 têm candidato indeterminado e 2 não têm
candidato temporal dentro da tolerância. Os 10 candidatos sem referência
ficaram todos indeterminados. Os quatro hooks também ficaram indeterminados
neste conjunto; isto não demonstra rejeição robusta de hooks desconhecidos.

Relatórios por referência, matrizes e previsões:

- [Front view — relatório](../outputs/step4/front-view-classification/classification-evaluation.md)
- [Upper body — relatório](../outputs/step4/upper-body-classification/classification-evaluation.md)
- [Front view — vídeo com previsões](../outputs/step4/front-view-classification/classification-demo.mp4)
- [Upper body — vídeo com previsões](../outputs/step4/upper-body-classification/classification-demo.mp4)
- [Front view — exemplos das três saídas](../outputs/step4/front-view-classification/classification-examples.png)
- [Upper body — matriz com abstenções e golpes perdidos](../outputs/step4/upper-body-classification/classification-confusion.png)

## Limitações observadas

- Em front view, só 3 dos 12 diretos recebem esse rótulo. Os ângulos pequenos,
  as janelas que incluem preparação/recolha e trajetos pouco retilíneos na
  projeção fazem a regra abster-se em muitos golpes reais.
- Em upper body, só 1 dos 6 uppercuts recebe esse rótulo. Alguns candidatos
  estão no braço que recolhe ou prepara o golpe seguinte; a classificação
  mantém o braço do detetor e não escolhe outro com ajuda dos rótulos manuais.
- O direto curto manual 121 de front view, com par temporal no 123, fica
  indeterminado. O erro de cotovelo no 52 continua nos dados e não foi corrigido.
- A regra exige qualidade dos três pontos; visibility alta não garante acerto.
- A distinção física entre trajetórias depende da perspetiva. Estes perfis 2D
  não garantem identificação de técnicas fora dos exemplos explorados.

## Frase possível para a candidatura

> Desenvolvi um protótipo de análise de shadowboxing com estimação de pose,
> deteção temporal de movimentos e regras geométricas experimentais para
> distinguir alguns diretos e uppercuts, com abstenção em casos ambíguos e
> diagnóstico em vídeos anotados manualmente.

Revisão visual pelo Pedro ainda pendente. O contributo demonstrado é um pipeline
executável, interpretável e inspecionável; a cobertura da classificação ainda
é baixa e exige trabalho posterior.
