# Golpes de boxe — referência para o projeto

Registado em **8 de novembro de 2026**, a pedido do Pedro. Síntese das descrições
que forneceu, com convenções para futuras anotações. Não são regras de deteção
implementadas nem capacidades já demonstradas pelo sistema.

## Âmbito pretendido

**Atualização de 9 de novembro de 2026 — Passo 3:** o Pedro propôs e ficou
acordado simplificar o primeiro reconhecimento, juntando jab e cross numa
única classe **direto**. A distinção jab/cross fica para depois de demonstrarmos
reconhecimento de diretos. Não é necessário conhecer a guarda para atribuir
esta classe; a mão anatómica pode continuar a ser anotada. Hook e uppercut
continuam como famílias candidatas, cuja cobertura e viabilidade falta verificar;
esta decisão não confirma reconhecimento de nenhuma família.

**Convenção de anotação refinada no mesmo dia:** o Pedro forneceu pares de
frames por família: saída ofensiva/extensão máxima para direto; ponto baixo/
culminar da fase ascendente para os uppercuts observados; preparação lateral/
final ofensivo para o hook observado. São âncoras de referência dos exemplos,
não fases obrigatórias nem regras universais de classificação. Detalhes e dados
atuais em `annotations/protocol.md` e `annotations/events.csv`. Lead/rear fica
num campo separado de esquerda/direita anatómicas; o direto ao corpo mantém
a família direto, com alvo adicional.

O Pedro propôs considerar quatro designações: **jab, cross, hook e uppercut**.
Podemos organizá-las em três famílias de movimento: **diretos, hooks e
uppercuts**, distinguindo jab/cross pelo papel da mão na guarda. Jab e cross
pertencem à mesma família, mas isso não significa que a execução seja idêntica.
Esta era a proposta anterior à simplificação acima. A cobertura dos dados e a
viabilidade das classes serão verificadas no Passo 3. Os moldes e o guia offline
preparados em 8 de novembro ainda usam jab/cross; o protocolo atual de referência
é `annotations/protocol.md` e usa `straight` (direto). Um futuro validador deve
seguir o protocolo atual, não o esquema antigo do guia.

## Descrições de trabalho

- **Jab:** direto executado pela mão da frente (*lead hand*), habitualmente
  rápido, partindo da guarda e regressando a ela. Para os rótulos do projeto,
  «jab» designa o direto da mão da frente.
- **Cross / rear straight:** direto executado pela mão de trás (*rear hand*),
  tipicamente acompanhado de rotação do tronco/ancas. Para os rótulos do projeto,
  um direto da mão de trás é cross, não jab.
- **Hook:** golpe com trajetória aproximadamente em arco e cotovelo fletido,
  dirigido à lateral da cabeça ou ao corpo. Pode ser da mão da frente
  (*lead hook*) ou da mão de trás (*rear hook*).
- **Uppercut:** golpe com trajetória ascendente, dirigido à cabeça ou ao corpo.
  Pode ser da mão da frente (*lead uppercut*) ou de trás (*rear uppercut*).
  Pode incluir uma descida preparatória, mas não tem de começar na cintura
  nem exige baixar a mão antes de subir.

São descrições qualitativas. Não fixam velocidades, ângulos ou amplitudes
universais e não implicam que determinado golpe seja sempre mais potente.

## Guarda, mão anatómica e papel da mão

- **Orthodox:** lado esquerdo à frente; mão esquerda é lead, direita é rear.
- **Southpaw:** lado direito à frente; mão direita é lead, esquerda é rear.
- A guarda usada não determina necessariamente a mão dominante do praticante.
- Esquerda/direita referem-se à pessoa, não aos lados do ecrã.
- Se o praticante trocar de guarda, a relação lead/rear muda. Para anotar,
  teremos de considerar a guarda nesse instante, não apenas uma guarda por vídeo.

| Designação | Família | Papel da mão | Orthodox | Southpaw |
| --- | --- | --- | --- | --- |
| Jab | Direto | Lead | Esquerda | Direita |
| Cross | Direto | Rear | Direita | Esquerda |
| Lead hook | Hook | Lead | Esquerda | Direita |
| Rear hook | Hook | Rear | Direita | Esquerda |
| Lead uppercut | Uppercut | Lead | Esquerda | Direita |
| Rear uppercut | Uppercut | Rear | Direita | Esquerda |

O âmbito proposto mantém quatro nomes principais, podendo conservar mão e papel
como informação adicional. Não foi decidido criar seis classes independentes.

## Relação com os sinais de pose explorados

O Pedro salientou o potencial de separar movimento horizontal e vertical:
uma extensão para a frente num jab versus uma trajetória ascendente num
uppercut, eventualmente precedida de descida. É uma hipótese útil para explorar
características temporais, ainda por validar com exemplos anotados.

«Para a frente», «lateral» e «para cima» descrevem o movimento físico. As
componentes Δx/Δy calculadas até agora usam os eixos da imagem, pelo que a sua
interpretação depende da câmara, da orientação do tronco e das oclusões. Não
assumir automaticamente que horizontal = jab ou vertical = uppercut.

A distinção entre guarda, preparação, golpe e regresso terá de considerar a
sequência temporal e movimentos sem golpe. As convenções de eventos, negativos
e casos incertos serão definidas no Passo 3.
