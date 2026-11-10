# Projeto para a candidatura

Preparado em 10 de novembro de 2026. Texto para o Pedro rever e adaptar ao
formato da candidatura; não foi submetido à candidatura.

## Texto sugerido

Desenvolvi um protótipo de análise de shadowboxing para aplicar os meus
conhecimentos de Machine Learning a Computer Vision. O pipeline combina
estimação de pose com MediaPipe, características temporais dos braços e regras
geométricas para localizar movimentos candidatos e classificá-los como direto
ou uppercut, com possibilidade de abstenção. Produz timestamps, tabelas e vídeos
com previsões, permitindo inspecionar a relação entre movimento e decisão.

Num piloto com dois vídeos de desenvolvimento e 33 golpes anotados manualmente,
23 dos 29 diretos/uppercuts tiveram correspondência temporal e de família a
±125 ms. A análise contabiliza também falsos candidatos, abstenções, golpes
perdidos e hooks, que estão fora das classes previstas. Estes resultados não
demonstram generalização: as regras foram ajustadas nos mesmos vídeos, a amostra
é pequena, a pose pode falhar e a geometria 2D depende do ponto de vista.
A correspondência temporal também não garante que o sistema tenha identificado
o braço e a fase física corretos.

Os próximos passos são recolher e anotar mais gravações, incluindo diferentes
praticantes, sessões, ângulos de câmara e movimentos sem golpe; reservar um
conjunto independente antes de novos ajustes; e comparar este baseline com um
classificador aprendido a partir de sequências de pose. A comparação deverá
avaliar separadamente a deteção temporal e a classificação, preservando os
golpes sem candidato e as abstenções. Um classificador aprendido poderá reduzir
a dependência de regras específicas, mas essa melhoria terá de ser demonstrada
experimentalmente, com separação por gravação/sessão e análise dos erros.

## Versão curta

Protótipo de análise de shadowboxing com MediaPipe e regras geométricas
temporais, com timestamps e abstenção em casos ambíguos. Num piloto de
desenvolvimento, 23 dos 29 diretos/uppercuts anotados tiveram correspondência
temporal e de família a ±125 ms. As regras foram ajustadas nesses vídeos;
não há teste independente. O trabalho seguinte é avaliar mais pessoas,
sessões e ângulos de câmara e comparar o baseline com um classificador aprendido
de sequências de pose, medindo também falsos positivos e golpes perdidos.

## Como apresentar e discutir o projeto

1. **Problema:** identificar eventos num vídeo contínuo exige localizar o
   movimento no tempo e depois atribuir família; classificar um excerto já
   segmentado resolve apenas parte do problema.
2. **Método:** o MediaPipe fornece pontos corporais; calculamos trajetória do
   punho relativamente ao ombro, ângulo projetado do cotovelo e evolução temporal.
   O modelo de pose é pré-treinado; o classificador de golpes atual é determinístico.
3. **Evidência:** mostrar o resultado agregado e um erro, como o hook rotulado
   como direto. Explicar por que indeterminado é uma abstenção e por que um golpe
   sem candidato também conta contra a cobertura.
4. **Limite decisivo:** ajustar regras sem treino também adapta o método aos
   dados. Os números atuais são um diagnóstico de desenvolvimento, sem estimativa
   de desempenho fora destes exemplos.
5. **Experiência seguinte:** congelar a v2, recolher gravações independentes e
   comparar regras e aprendizagem com o mesmo protocolo. Investigar se a falha
   vem da pose, da deteção temporal ou da família antes de mudar o componente.

Se for usada uma demonstração visual, escolher um caso concordante e uma falha,
identificar ambos como desenvolvimento e apresentar os denominadores completos.
As localizações dos vídeos locais estão em [REPOSITORY.md](REPOSITORY.md).
Confirmar a proveniência/condições antes de os anexar ou partilhar externamente.

O projeto exercita leitura de vídeo, estimação de pose, análise temporal,
anotação e avaliação experimental. É uma base de aprendizagem relevante para
análise de ações em desporto. Tracking de múltiplos jogadores, calibração,
integração entre câmaras e deteção de faltas/penáltis não foram implementados.

## Valores que sustentam o texto

| Quantidade | Valor e interpretação |
| --- | --- |
| Dados anotados | 2 vídeos de desenvolvimento, 33 golpes, cerca de 17,18 s |
| Famílias-alvo | 21 diretos + 8 uppercuts = 29 |
| Concordâncias tempo/família | 23; matching 1:1 a ±125 ms |
| Outras atribuições | 1 hook como direto + 2 diretos sem par temporal |
| Alvos não reconhecidos | 4 abstenções + 2 sem candidato |
| Precisão / recall / F1 diagnósticos | 88,5% / 79,3% / 83,6%, apenas desenvolvimento |

Não escrever «88,5% de accuracy», «validado em vídeos independentes»,
«reconhece jab/cross/hooks» ou «funciona em tempo real». A aplicação a upper
body 3, incluindo a versão a 2×, não tem anotações para demonstrar acertos.
Relatório de referência: [EVALUATION_PILOT.md](EVALUATION_PILOT.md).
