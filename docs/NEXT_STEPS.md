# Próximos passos experimentais

Plano de evolução após a entrega de 10/11/2026. Nenhuma das experiências abaixo
foi executada no Passo 6. O baseline atual permanece congelado para permitir
comparações. O objetivo é descobrir em que condições o método funciona e qual
componente limita o resultado, antes de ampliar as capacidades anunciadas.

## 1. Dados mais diversos e teste independente

Recolher vídeos de mais praticantes e de várias sessões por praticante, com
câmara frontal, oblíqua e lateral. Variar enquadramento, distância, iluminação,
velocidade, guarda e orientação do corpo. Incluir golpes isolados, combinações,
pausas, deslocações, ajustes de guarda, fintas e outros movimentos sem golpe.
Registar condições de captura, FPS/timestamps, origem e condições de utilização.
As primeiras comparações de ângulo podem usar o mesmo exercício em condições
controladas; vídeos de outras sessões/pessoas são necessários para estudar
generalização.

Anotar os vídeos completos: família, âncoras temporais, intervalos sem golpe e
casos incertos. Rever exemplos difíceis e, quando possível, obter uma segunda
anotação para medir desacordo temporal e de família. Isso permitirá justificar
a tolerância de matching, hoje apenas provisória. Não transformar todos os
intervalos entre golpes em negativos sem os rever.

**Separação antes de ajustar:** desenvolvimento/treino, validação para escolher
regras ou hiperparâmetros e teste reservado. Manter todos os recortes, versões
a outra velocidade e vistas sincronizadas da mesma gravação no mesmo grupo.
Não dividir frames vizinhos aleatoriamente. Para testar novas pessoas, separar
também por pessoa; reportar esse cenário separadamente de novas sessões da mesma
pessoa. Os dois vídeos já usados permanecem desenvolvimento.

**Evidência procurada:** resultados em gravações que não influenciaram escolhas,
com contagens por pessoa, sessão e ângulo. O número necessário de gravações
depende da diversidade e estabilidade observadas; ainda não foi fixado um tamanho
de dataset nem uma meta de desempenho.

## 2. Separar erros de pose, deteção e família

| Limitação observada | Experiência proposta | O que permite concluir |
| --- | --- | --- |
| Cotovelo incorreto e lacunas nos braços | Inspeção estratificada de punhos/cotovelos durante golpes e oclusões; anotações de pontos numa amostra | Distinguir disponibilidade de pose de precisão dos pontos |
| Dependência da projeção 2D | Aplicar a v2 congelada às várias vistas e comparar erros por ângulo | Medir sensibilidade à câmara, sem a presumir resolvida por normalização |
| Golpes sem candidato e candidatos extras | Avaliar apenas a deteção temporal, incluindo negativos prolongados e combinações | Saber quanto se perde antes de classificar |
| Par temporal apoiado no outro braço/fase | Rever vídeo e anotar braço/fase nos casos ambíguos | Distinguir concordância do avaliador de correspondência física |
| Sensibilidade à tolerância e câmara lenta | Quantificar incerteza das âncoras e verificar timestamps/velocidade de captura | Fixar protocolo e separar reprodução de velocidade física |

Comparar outro modelo de pose só se a inspeção mostrar que a pose é o fator
limitante, usando as mesmas gravações e medindo qualidade, custo e latência.
Não atribuir melhoria à troca de modelo sem uma comparação controlada.

## 3. Comparar regras com classificação aprendida

Primeiro construir exemplos temporais anotados em quantidade e diversidade
suficientes. A entrada pode ser uma sequência de pose normalizada ou
características temporais calculadas dessa sequência; a saída é a família,
com tratamento explícito de negativos e incerteza. Não usar apenas um frame
nem pressupor que os 33 eventos atuais são suficientes para treinar e avaliar.

Uma primeira comparação pode usar um classificador simples sobre características
temporais; um modelo de sequências, como TCN ou LSTM, é uma experiência posterior
se os dados justificarem. Arquitetura e treino ainda não estão decididos. O
modelo pré-treinado de pose pode ser mantido para isolar o efeito de aprender a
classificação de golpes.

Fazer duas avaliações complementares:

- **Classificação com segmentação manual:** mede se as famílias são separáveis
  quando o intervalo correto já é conhecido. É um diagnóstico, não o desempenho
  do sistema completo.
- **Pipeline em vídeo contínuo:** mede deteção e família em conjunto, com extras,
  duplicações, abstenções e golpes sem candidato. Mantendo o detetor atual,
  nenhum classificador recupera um evento que ele não propôs; melhorar a deteção
  ou aprender a segmentação será uma experiência distinta se essa perda dominar.

Usar as mesmas divisões e protocolo para regras e modelo aprendido. Escolher
hiperparâmetros e limiar de abstenção na validação; usar o teste reservado para
a comparação final. Aprender os padrões pode reduzir fragilidade das regras,
mas também pode aprender a pessoa/câmara e repetir erros da pose. A vantagem
tem de aparecer fora dos dados usados nas escolhas.

## 4. Medir a melhoria e só depois ampliar o âmbito

Reportar precisão, recall e F1 por evento, matriz por família com abstenções e
golpes perdidos, cobertura de classificação, falsos positivos em negativos e
sensibilidade temporal. Desagregar por ângulo, pessoa e sessão, com números de
eventos e incerteza ao nível das gravações; 419 frames vizinhos não equivalem
a 419 observações independentes. Incluir casos de falha e as condições em que
o método se abstém. Medir latência apenas se tempo real passar a ser objetivo.

Hooks, distinção jab/cross e combinações ficam para depois de uma avaliação
independente das famílias atuais. Jab/cross exigirá explicitar guarda e papel
lead/rear; hooks precisam de mais exemplos próprios e de negativos confundíveis.
Reconhecimento direto de imagens/vídeo pode ser uma comparação futura se a pose
perder informação decisiva e existirem dados/recursos adequados. Sparring,
contacto e pontuação continuam fora do âmbito deste protótipo.
