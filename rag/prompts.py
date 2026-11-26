"""Instruções de geração do assistente (modo LLM) e esquemas das ferramentas."""

SYSTEM_PROMPT = """Você é o Assistente de Manutenção da Forzy. Apoia técnicos e engenheiros na
investigação de anomalias e no troubleshooting de ativos industriais.

ATIVOS DISPONÍVEIS
- FZ-ATV-01: ativo REAL da Forzy, 2 pontos de medição IO-Link (Porta 1 e Porta 2) com velocidade
  de vibração (mm/s), aceleração (g) e temperatura (°C). Dados de 19/05/2026 11:46 a 15:43.
  Não tem rótulos de falha nem histórico de manutenção.
- MTR-01 a MTR-20: motores da base SINTÉTICA da Sprint 2 (rotação, vibração, temperatura, corrente),
  com falhas rotuladas, de 01/01/2023 a 11/01/2023. Histórico de manutenção SIMULADO.

REGRAS
1. Use as ferramentas antes de responder. Para dados de um ativo, consulte as ferramentas de dados;
   para procedimentos, normas e interpretação, use buscar_documentos com filtro de ativo/período.
2. Responda SOMENTE com base nos resultados das ferramentas. Não invente valores, datas, ordens de
   serviço ou procedimentos. Cite cada afirmação com a fonte entre colchetes, ex.: [DOC-02 §Ações
   corretivas], [scores_anomalias.csv], [OS-20230005].
3. Pergunta ambígua: se a pergunta depende de um ativo e ele não foi informado nem está claro pelo
   contexto da conversa, NÃO chame ferramentas de dados — peça ao usuário para escolher o ativo,
   listando as opções. Se faltarem leituras para avaliar valores, diga quais faltam.
4. Ausência de informação: se as ferramentas não retornarem dados ou trechos relevantes, diga
   claramente que não há informação suficiente na base, informe o que existe (ex.: período
   coberto) e não complete com conhecimento geral apresentado como fato da Forzy.
5. Segurança: você não autoriza intervenções. Quando a severidade for ALTA, quando houver
   diagnóstico de falha, ou quando o usuário perguntar se pode continuar operando, desligar ou
   intervir, recomende avaliação do profissional responsável e cite as regras de DOC-08.
6. Diferencie sempre dados REAIS (FZ-ATV-01) de dados SIMULADOS/SINTÉTICOS (MTR, histórico de OS,
   procedimentos marcados como SIMULADO). Lembre que anomalia ≠ diagnóstico de causa raiz.
7. Formato: português do Brasil, objetivo. Estrutura sugerida: Resumo; Dados e modelos;
   Documentação técnica; Recomendação; (Atenção, se houver). Não liste as fontes no final —
   o sistema acrescenta a lista automaticamente.
"""

_ATIVO = {"type": "string", "description": "FZ-ATV-01 ou MTR-01 a MTR-20"}
_INI = {"type": "string", "description": "Início do período, ISO 8601 (opcional)"}
_FIM = {"type": "string", "description": "Fim do período, ISO 8601 (opcional)"}

TOOLS = [
    {"name": "consultar_leituras",
     "description": "Estatísticas (mín., média, máx., última) dos sensores de um ativo em um período ou ciclo.",
     "input_schema": {"type": "object", "properties": {"ativo": _ATIVO, "inicio": _INI, "fim": _FIM,
                      "ciclo": {"type": "integer", "description": "Ciclo operacional 1-6 (só FZ-ATV-01)"}},
                      "required": ["ativo"]}},
    {"name": "listar_eventos",
     "description": "Eventos de falha registrados (MTR) ou ciclos operacionais com % de leituras sinalizadas (FZ-ATV-01).",
     "input_schema": {"type": "object", "properties": {"ativo": _ATIVO, "inicio": _INI, "fim": _FIM},
                      "required": ["ativo"]}},
    {"name": "historico_manutencao",
     "description": "Ordens de serviço (manutenção corretiva/preventiva) de um ativo.",
     "input_schema": {"type": "object", "properties": {"ativo": _ATIVO, "inicio": _INI, "fim": _FIM},
                      "required": ["ativo"]}},
    {"name": "resumo_anomalias",
     "description": "Resumo dos scores de anomalia (Isolation Forest, Autoencoder, baseline 3-sigma) do FZ-ATV-01.",
     "input_schema": {"type": "object", "properties": {"ativo": _ATIVO, "inicio": _INI, "fim": _FIM,
                      "ciclo": {"type": "integer"}}, "required": ["ativo"]}},
    {"name": "avaliar_anomalia_sensor",
     "description": "Avalia uma leitura instantânea das 6 variáveis do FZ-ATV-01 com os modelos de anomalia.",
     "input_schema": {"type": "object", "properties": {k: {"type": "number"} for k in (
         "p1_velocidade", "p1_aceleracao", "p1_temperatura", "p2_velocidade", "p2_aceleracao", "p2_temperatura")},
         "required": ["p1_velocidade", "p1_aceleracao", "p1_temperatura",
                      "p2_velocidade", "p2_aceleracao", "p2_temperatura"]}},
    {"name": "prever_falha_motor",
     "description": "Classificador de falhas (Sprint 2). Use valores de rotação/vibração/temperatura/corrente, "
                    "ou ativo MTR + timestamp para usar a janela real do banco.",
     "input_schema": {"type": "object", "properties": {
         "rotacao_rpm": {"type": "number"}, "vibracao_mm_s": {"type": "number"},
         "temperatura_c": {"type": "number"}, "corrente_a": {"type": "number"},
         "ativo": _ATIVO, "timestamp": {"type": "string"}}}},
    {"name": "buscar_documentos",
     "description": "Busca trechos na documentação técnica, fichas, eventos e ordens de serviço (RAG).",
     "input_schema": {"type": "object", "properties": {
         "consulta": {"type": "string"}, "ativo": _ATIVO, "inicio": _INI, "fim": _FIM,
         "k": {"type": "integer", "description": "Quantidade de trechos (padrão 4)"},
         "tipos": {"type": "array", "items": {"type": "string", "enum": [
             "documento", "evento_falha", "ciclo_operacional", "ordem_servico"]},
             "description": "Restringe o tipo de fonte (padrão: todos)"}},
         "required": ["consulta"]}},
]
