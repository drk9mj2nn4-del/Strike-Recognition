# Cópia numérica do piloto v2

Preparada no Passo 6, em 10/11/2026, a partir de `outputs/step5/`.
**Apenas desenvolvimento; sem teste independente.** Não houve novo ajuste,
inferência, anotação ou seleção de eventos para esta entrega.

| Ficheiro | Conteúdo |
| --- | --- |
| [summary.md](summary.md) | Resumo agregado e matriz |
| [evaluation.json](evaluation.json) | Contagens, diagnósticos por vídeo, extras e cinco tolerâncias |
| [references.csv](references.csv) | As 33 referências, incluindo abstenções e golpes sem candidato, a ±125 ms |
| [sensitivity.csv](sensitivity.csv) | Resultados agregados a ±50/100/125/167/200 ms |
| [SHA256SUMS](SHA256SUMS) | Integridade dos quatro ficheiros anteriores |

Resumo/CSV são cópias byte a byte dos originais. No JSON, somente as chaves com
caminhos absolutos em `input_sha256` foram convertidas para caminhos relativos
à raiz do projeto. Os digests e todos os resultados foram preservados. Esse mapa
identifica as entradas da execução histórica, incluindo ficheiros locais que
não acompanham o código. Alterações posteriores à documentação/inventário não
reescrevem a proveniência dessa execução. `SHA256SUMS` identifica esta cópia.

Não há vídeos, imagens, pesos ou sequências completas de pose nesta pasta.
Os diagnósticos incluem características numéricas dos candidatos sem par,
preservadas para não ocultar erros. `hand_scored: false` significa que o matching
não pontua a mão/ braço; as famílias de referência foram anotadas manualmente.

**Interpretação:** [avaliação piloto](../../docs/EVALUATION_PILOT.md).
**Reprodução e dados necessários:** [guia](../../docs/REPRODUCING.md).
A cópia pode ser lida sem dependências. Recalcular o matching ou reconstruir
o pipeline original requer os dados locais, excluídos do Git.
