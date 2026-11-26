# Assistente de Manutenção Forzy — Sprint 4 (Generative AI & Advanced Net)

Solução de IA para apoiar o monitoramento de ativos e o troubleshooting de equipamentos da Forzy.
Combina **dados de sensores**, **histórico operacional**, **modelos de IA** (Sprints 2 e 3) e
**documentação técnica** (RAG — Retrieval-Augmented Generation) em um assistente conversacional
que sempre apresenta as fontes consultadas.

> Documentação completa: `docs/Documentacao_Final_Sprint4_Forzy.pdf`

## O que a solução faz

| Funcionalidade | Status |
|---|---|
| Consulta de leituras de sensores por ativo, período e ciclo | Implementado |
| Classificação de falhas (Random Forest, Sprint 2) — por valores avulsos ou pela janela real do banco | Implementado |
| Detecção de anomalias (Isolation Forest + Autoencoder + baseline 3σ, Sprint 3) | Implementado |
| Busca em documentação técnica, eventos, ciclos e ordens de serviço com filtros por ativo/período (RAG) | Implementado |
| Tratamento de perguntas ambíguas, ausência de informação e escalonamento para profissional | Implementado |
| Geração com LLM (Claude via API Anthropic, tool use) | Implementado — requer chave; não avaliado nos testes |
| Modo offline (sem LLM, determinístico) | Implementado — usado nos testes |
| Comparação entre vários ativos na mesma pergunta | Pendente |

## Ativos e natureza dos dados

| Ativo | Dados | Origem |
|---|---|---|
| `FZ-ATV-01` | 7.183 leituras IO-Link (vibração e temperatura, Portas 1 e 2), 19/05/2026 11:46–15:43 | **REAL** (Forzy) |
| `MTR-01` … `MTR-20` | 30.000 leituras (rotação, vibração, temperatura, corrente) com falhas rotuladas | **SINTÉTICO** (Sprint 2) |
| Histórico de manutenção | 40 ordens de serviço, apenas motores MTR | **SIMULADO** |
| Documentos DOC-01 a DOC-09 | Procedimentos, fichas técnicas e políticas | Ver campo `origem` de cada arquivo |

## Estrutura

```
forzy-assistente/
├── app.py                     # Interface web (Streamlit)
├── cli.py                     # Interface de linha de comando
├── rag/
│   ├── config.py              # Caminhos e variáveis de ambiente
│   ├── preparar_base.py       # Extração de eventos/ciclos, geração do histórico simulado, chunking e indexação
│   ├── texto.py               # Normalização e extração de ativo, período, ciclo e números da pergunta
│   ├── recuperador.py         # Busca TF-IDF híbrida com filtros por ativo, período e tipo de fonte
│   ├── ferramentas.py         # 7 ferramentas: leituras, eventos, OS, classificador, anomalias, resumo, busca
│   ├── prompts.py             # Instruções do LLM e esquemas das ferramentas
│   └── assistente.py          # Orquestrador (modo LLM e modo offline) + montagem de fontes
├── conhecimento/
│   ├── documentos/            # DOC-01 … DOC-09 (Markdown com metadados)
│   ├── historico_manutencao.csv   # gerado (SIMULADO)
│   └── gerado/                # eventos_falha_mtr.csv, ciclos_fz.csv
├── indice/indice_rag.joblib   # gerado por preparar_base
├── sprint2/                   # motor.db, gerar_banco.py, modelo_falhas.joblib, notebooks, BANCO.md
├── sprint3/                   # modelos de anomalia, baseline, scores, notebooks, FORZY.md
├── testes/
│   ├── cenarios.py            # 13 cenários ponta a ponta com verificações automáticas
│   ├── avaliar_recuperacao.py # Hit@1, Hit@3, MRR@5 em 24 perguntas rotuladas
│   └── teste_modo_llm_mock.py # valida o laço de tool use do modo LLM sem chamar a API
├── resultados/                # logs, JSON, gráficos e capturas de tela
└── docs/                      # documento final (PDF), diagrama de arquitetura e figuras
```

## Instalação

Pré-requisitos: Python 3.11+ (testado em 3.13), ~2 GB livres (PyTorch).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # opcional: preencha ANTHROPIC_API_KEY para o modo LLM
```

## Execução

```bash
# 1. Preparar e indexar a base de conhecimento (≈ 5 s)
python -m rag.preparar_base

# 2a. Interface web
streamlit run app.py               # abre em http://localhost:8501

# 2b. Linha de comando
python cli.py                                            # conversa
python cli.py --debug "O que aconteceu no ciclo 6 do FZ-ATV-01?"
python cli.py --modo offline "Quais falhas o MTR-07 apresentou?"

# 3. Testes e evidências (geram arquivos em resultados/)
python -m testes.cenarios
python -m testes.avaliar_recuperacao
python -m testes.teste_modo_llm_mock
```

Sem `ANTHROPIC_API_KEY` o assistente roda em **modo offline**: as respostas são montadas por regras a
partir das mesmas ferramentas e fontes. Com a chave, o modo `auto` usa o Claude com *tool use*; se a API
falhar, a resposta é gerada no modo offline e o fato é informado ao usuário.

Para recriar o banco sintético da Sprint 2: `cd sprint2 && python gerar_banco.py` (seed 42).
O CSV bruto da Forzy (`forzy_history.csv`) não acompanha este repositório; o assistente usa
`sprint3/scores_anomalias.csv`, que contém as 7.183 leituras já processadas e os scores.

## Exemplos de perguntas

- `O que aconteceu no ciclo 6 do FZ-ATV-01? Houve anomalia?`
- `Quais falhas o MTR-07 apresentou e como devo investigar?`
- `Qual o diagnóstico do MTR-07 em 2023-01-04 06:00?`
- `Leitura do FZ-ATV-01: P1 6,9 mm/s 0,50 g 38 °C; P2 7,1 mm/s 0,52 g 42 °C. Isso é anômalo?`
- `Qual o histórico de manutenção do MTR-03?`
- `Quais são os limites de vibração da ISO 10816 para base rígida?`

## Resultados principais

- 13/13 cenários funcionais aprovados (modo offline), incluindo os 3 obrigatórios.
- Recuperação (24 perguntas): configuração do assistente (híbrido + filtro por ativo + separação por tipo
  de fonte) — Hit@1 0,88 · Hit@3 0,92 · MRR@5 0,90; sem nenhum filtro: 0,63 · 0,67 · 0,67.
- Modelos herdados: Random Forest F1-Macro 0,955 (dados sintéticos); Autoencoder ROC-AUC 0,942 e
  Isolation Forest semissupervisionado 0,975 contra o pseudo-rótulo do Ciclo 6.

## Limitações

Dados reais de um único ativo em ~4 h, sem rótulos de falha; classificador treinado em dados sintéticos;
documentos técnicos e histórico de OS simulados; recuperação lexical (sem embeddings); modo LLM não
avaliado com a API real. Detalhes e plano de evolução no capítulo 9 da documentação.

## Equipe

Matheus Mikio (RM 561864) · Henry Gimenez (RM 563217) · Ian Nobres (RM 561681) ·
Gustavo Balbo (RM 561711) · Vinicius Araujo (RM 564504)
