# Organização do repositório

10 de novembro de 2026 · Passo 6.

Repositório público criado, com autorização explícita do Pedro:
[Strike-Recognition](https://github.com/drk9mj2nn4-del/Strike-Recognition).

## Estrutura

```text
Strike Recognition/
├── README.md                     # Apresentação, resultados, limites e arranque
├── *.py                          # Pipeline e ferramentas, sem mudar imports
├── requirements.txt              # Dependências diretas
├── requirements-offline.lock.txt # Versões completas do ambiente verificado
├── annotations/                  # Referências manuais e protocolo atual
├── docs/                         # Documentação de entrega e técnica
│   ├── README.md                 # Índice
│   ├── CANDIDATURA.md             # Texto longo/curto e guião
│   ├── NEXT_STEPS.md              # Plano experimental fundamentado
│   ├── REPRODUCING.md             # Instalação, execução e reprodução
│   ├── REPOSITORY.md              # Este mapa
│   └── ...                       # Avaliação, pose, baseline, classificação v1/v2
├── results/pilot/                # Cópia numérica, sem imagens/vídeos
├── tests/                        # Verificações de software
├── data/                         # Local; vídeos excluídos do Git
├── models/                       # Local; pesos excluídos do Git
├── outputs/                      # Local; execuções completas excluídas do Git
├── offline/SOURCES.md            # Proveniência e condições dos recursos
└── strikes.md                    # Convenções de boxe
```

Mantiveram-se os scripts na raiz para preservar comandos/imports já usados.
A versão atual é `classify_motion_phases.py`; `classify_candidates.py` é a v1.
`annotations/protocol.md` prevalece sobre moldes offline antigos.

## Conteúdo selecionado para o GitHub

README, scripts, testes, dependências, anotações, documentação e a cópia numérica
do piloto. O `.gitignore` exclui vídeos/dados brutos, pesos, resultados completos,
ambientes, caches, wheels, livro e referências de terceiros guardadas offline.
`data/.gitkeep`, `models/.gitkeep` e `outputs/.gitkeep` mantêm as pastas vazias.

Os ficheiros pessoais de colaboração (`AGENTS.md`, `STATE.md`, `STEPS.md`),
`OFFLINE_GUIDE.md` e os restantes materiais em `offline/` ficam apenas locais.
Não integram o histórico público nem o conteúdo do commit de entrega.

`results/pilot/` foi criado porque `outputs/` é local: assim os resultados
continuam legíveis numa futura cópia do repositório. O JSON conserva os
diagnósticos por vídeo e tolerância, incluindo candidatos sem par; só os nomes
absolutos dos caminhos no mapa de hashes foram tornados relativos. Não inclui
imagens, vídeos, pesos ou sequências completas de pose.

## Demonstração visual existente, apenas local

| Material | Localização |
| --- | --- |
| Front view v2 | `outputs/step4/front-view-classification-v2/classification-demo.mp4` |
| Upper body v2 | `outputs/step4/upper-body-classification-v2/classification-demo.mp4` |
| Casos concordantes e erro no hook | `outputs/step4/front-view-classification-v2/classification-examples.png` |
| Casos concordantes e extras classificados | `outputs/step4/upper-body-classification-v2/classification-examples.png` |
| Aplicação sem anotações, original/2× | `outputs/step4/upper-body-3-classification-v2/` e `upper-body-3-x2-classification-v2/` |

Os dois primeiros vídeos são desenvolvimento. O exemplo upper body 3 não tem
métricas de acerto; original e 2× são a mesma gravação. Os exemplos visuais não
acompanham a cópia numérica. Links para `outputs/` nos documentos técnicos
destinam-se à consulta local.

## Publicação e limites de partilha

- Documentação, comandos e resultados numéricos preparados para o repositório público.
- Sem mudanças ao algoritmo, novas funcionalidades ou ajuste de resultados.
- Git inicializado com branch `main`; repositório público criado na conta do Pedro.
- A seleção pública exclui o contexto pessoal e o histórico de conversas.
- Publicação do código autorizada; não foi feita submissão da candidatura nem post no LinkedIn.
- A proveniência/condições dos vídeos `shbx` precisa de confirmação antes de
  partilhar vídeos ou frames/overlays. Podem permanecer excluídos e a demonstração
  futura usar uma gravação própria autorizada.
- Não foi escolhida licença para o código. Essa escolha é separada das condições
  das dependências e dados; não foi aplicada licença global aos recursos.
- Reconstrução integral do piloto requer dados locais; execução com vídeo próprio
  documentada. Instalação limpa noutro computador não testada.

A publicação do código não altera o alcance da avaliação nem demonstra
reconhecimento robusto. Os resultados continuam a ser de desenvolvimento.
