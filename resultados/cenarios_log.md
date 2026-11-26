# Registro de execução — cenários de teste (modo offline)

## C1 — Falha ou anomalia (obrigatório)  [APROVADO]

**Entrada:** O que aconteceu no ciclo 6 do FZ-ATV-01? Houve anomalia?

**Saída (resposta, 605.2 ms):**

```
Ciclos operacionais do FZ-ATV-01 (dados reais, sem rótulos de falha):
  • Ciclo 6: 13:44–14:01, 17.4 min, temp. máx. P1/P2 39/43 °C, leituras sinalizadas pelo Autoencoder 53.5% e pelo Isolation Forest 5.8%
  → O Ciclo 6 concentra o maior percentual de leituras anômalas segundo o Autoencoder. Não há falha confirmada: é um candidato a investigação.

Resultado dos modelos de anomalia (2028 leituras, 2026-05-19 13:44:28 a 2026-05-19 14:01:53):
  • Autoencoder (semissupervisionado) sinalizou 53.5% das leituras
  • Isolation Forest (não supervisionado) sinalizou 5.8%
  • Baseline estatístico 3-sigma: 0.3%
  • Leituras sinalizadas pelos dois modelos: 101
  A divergência entre os modelos é esperada em anomalias longas e coesas: o Isolation Forest treinado com todo o histórico tende a tratá-las como normais [DOC-06].

Documentação técnica relacionada:
  • [DOC-06 §Detecção de anomalias (Sprint 3)]: - Isolation Forest (não supervisionado, treinado com 100% do histórico) e Autoencoder (semissupervisionado, treinado sem o Ciclo 6). - O resultado é um score de desvio em relação ao comportamento histórico, não um diagnóstico de causa raiz. - Severidade combinada: ALTA quando os dois modelos sinalizam, MODERADA quando apenas um sinaliza, BAIXA quando nenhum sinaliza. - Divergência esperada: em anomalias longas e …
  • [DOC-07 §Quando aplicar] (documento SIMULADO): Quando a diferença de temperatura entre a Porta 1 e a Porta 2 se afasta do offset histórico (Porta 2 cerca de 5,5 °C mais quente, desvio-padrão de 1,6 °C), especialmente durante ciclos longos de operação.
  • [DOC-06 §Baseline operacional]: - Limites de 3 desvios-padrão calculados separadamente para repouso e operação. - Um z-score acima de 3 em qualquer sensor indica leitura fora do padrão histórico daquele estado. - A feature de maior contribuição para as anomalias do Ciclo 6 foi a diferença de temperatura entre as portas (diff_temp).
  • [DOC-07 §Hipóteses a investigar] (documento SIMULADO): 1. Lubrificação desigual entre os dois mancais. 2. Pré-carga ou desalinhamento afetando apenas um dos lados. 3. Diferença de ventilação ou exposição a fonte de calor externa em um dos pontos. 4. Problema de fixação do sensor (contato térmico ruim) em uma das portas.

Fontes consultadas:
  [1] conhecimento/gerado/ciclos_fz.csv (derivado de scores_anomalias.csv)
  [2] sprint3/scores_anomalias.csv
  [3] DOC-06 §Detecção de anomalias (Sprint 3) — Como interpretar os resultados dos modelos de IA [PROJETO] (score 0.291)
  [4] DOC-07 §Quando aplicar — Procedimento de troubleshooting — assimetria térmica entre pontos de medição [SIMULADO] (score 0.247)
  [5] DOC-06 §Baseline operacional — Como interpretar os resultados dos modelos de IA [PROJETO] (score 0.211)
  [6] DOC-07 §Hipóteses a investigar — Procedimento de troubleshooting — assimetria térmica entre pontos de medição [SIMULADO] (score 0.199)
```

Ferramentas: `listar_eventos`; `resumo_anomalias`; `buscar_documentos`

## C2 — Dados operacionais + documentação técnica (obrigatório)  [APROVADO]

**Entrada:** Quais falhas o MTR-07 apresentou e como devo investigar?

**Saída (resposta, 4.8 ms):**

```
Eventos de falha do MTR-07 (base sintética):
  • Superaquecimento: 2023-01-03 20:10 a 2023-01-04 07:30 — vibração máx. 2.63 mm/s, temperatura máx. 113.4 °C, corrente máx. 20.58 A, rotação mín. 1704 RPM

Documentação técnica relacionada:
  • [DOC-03 §Sintomas típicos] (documento SIMULADO): - Temperatura de carcaça ou mancal acima do histórico do ativo. - Em motores elétricos, aumento simultâneo de corrente (efeito Joule). - No modelo da Sprint 2, corresponde à classe 2 (Superaquecimento): temperatura acima de 85 °C e corrente acima de 15 A, com vibração baixa.
  • [DOC-03 §Critério de escalonamento] (documento SIMULADO): Temperatura subindo de forma contínua sem estabilizar, ou cheiro de isolamento queimado: desligar com segurança conforme DOC-08 e acionar o responsável técnico. Intervenções elétricas exigem profissional habilitado.
  • [DOC-03 §Verificações recomendadas] (documento SIMULADO): 1. Medir a corrente nas três fases e comparar com a corrente nominal de placa. 2. Verificar limpeza das aletas e funcionamento do ventilador. 3. Conferir temperatura ambiente e ventilação do local. 4. Verificar o plano de lubrificação e a última relubrificação registrada.
  • [DOC-03 §Possíveis causas] (documento SIMULADO): - Sobrecarga mecânica do equipamento acionado. - Ventilação obstruída (tampa defletora, aletas sujas, ambiente quente). - Desequilíbrio ou subtensão na alimentação elétrica. - Lubrificação inadequada dos mancais (excesso ou falta de graxa).

Fontes consultadas:
  [1] conhecimento/gerado/eventos_falha_mtr.csv (derivado de motor.db)
  [2] DOC-03 §Sintomas típicos — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.185)
  [3] DOC-03 §Critério de escalonamento — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.168)
  [4] DOC-03 §Verificações recomendadas — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.153)
  [5] DOC-03 §Possíveis causas — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.148)
```

Ferramentas: `listar_eventos`; `buscar_documentos`

## C3 — Informação insuficiente (obrigatório)  [APROVADO]

**Entrada:** Quando foi feita a última troca de rolamento do FZ-ATV-01?

**Saída (sem_informacao, 3.4 ms):**

```
Não há registros de manutenção (ordens de serviço) para o FZ-ATV-01 na base disponível. Por isso não é possível informar datas de intervenções, trocas de componentes ou lubrificações desse ativo.

Documentação técnica relacionada:
  • [DOC-05 §Histórico de manutenção]: Nenhum registro de manutenção, falha confirmada ou ordem de serviço foi fornecido para este ativo.
  • [DOC-04 §Ações corretivas] (documento SIMULADO): 1. Relubrificação conforme plano do fabricante. 2. Substituição do rolamento quando confirmado defeito, com registro do número do componente. 3. Alinhamento do acoplamento após a troca.
  • [DOC-04 §Critério de escalonamento] (documento SIMULADO): Crescimento contínuo da aceleração ou ruído metálico audível: programar parada e acionar o responsável técnico. A troca de rolamentos deve ser feita com o equipamento bloqueado (DOC-08).
  • [DOC-07 §Quando aplicar] (documento SIMULADO): Quando a diferença de temperatura entre a Porta 1 e a Porta 2 se afasta do offset histórico (Porta 2 cerca de 5,5 °C mais quente, desvio-padrão de 1,6 °C), especialmente durante ciclos longos de operação.

Fontes consultadas:
  [1] conhecimento/historico_manutencao.csv (SIMULADO)
  [2] DOC-05 §Histórico de manutenção — Ficha técnica e instalação dos sensores — ativo FZ-ATV-01 [REAL] (score 0.246)
  [3] DOC-04 §Ações corretivas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.184)
  [4] DOC-04 §Critério de escalonamento — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.181)
  [5] DOC-07 §Quando aplicar — Procedimento de troubleshooting — assimetria térmica entre pontos de medição [SIMULADO] (score 0.124)
```

Ferramentas: `historico_manutencao`; `buscar_documentos`

## C4 — Pergunta ambígua + continuação  [APROVADO]

**Entrada:** Como está o motor?

**Saída (esclarecimento, 0.1 ms):**

```
Para responder preciso saber de qual ativo se trata. Ativos disponíveis:
  • FZ-ATV-01 — ativo real da Forzy (vibração e temperatura, 19/05/2026)
  • MTR-01 a MTR-20 — motores da base sintética (01/01 a 11/01/2023)
Exemplo: "Quais falhas o MTR-07 apresentou?"
```

Ferramentas: 

**Entrada:** É o MTR-12. Quais foram as leituras e as falhas dele?

**Saída (resposta, 122.9 ms):**

```
Leituras do MTR-12 — 1500 registros de 2023-01-01 00:00:00 a 2023-01-11 09:50:00:
  • rotacao_rpm: mín. 1653.43 | média 1740.449 | máx. 1793.32 RPM
  • vibracao_mm_s: mín. 1.707 | média 2.494 | máx. 9.567 mm/s
  • temperatura_c: mín. 55.89 | média 62.345 | máx. 83.21 °C
  • corrente_a: mín. 10.442 | média 12.025 | máx. 13.816 A
  • Leituras rotuladas como falha no período: 66

Eventos de falha do MTR-12 (base sintética):
  • Falha mecânica: 2023-01-05 12:00 a 2023-01-05 22:50 — vibração máx. 9.57 mm/s, temperatura máx. 83.2 °C, corrente máx. 13.28 A, rotação mín. 1653 RPM

Documentação técnica relacionada:
  • [DOC-04 §Ações corretivas] (documento SIMULADO): 1. Relubrificação conforme plano do fabricante. 2. Substituição do rolamento quando confirmado defeito, com registro do número do componente. 3. Alinhamento do acoplamento após a troca.
  • [DOC-04 §Critério de escalonamento] (documento SIMULADO): Crescimento contínuo da aceleração ou ruído metálico audível: programar parada e acionar o responsável técnico. A troca de rolamentos deve ser feita com o equipamento bloqueado (DOC-08).
  • [DOC-04 §Sintomas típicos] (documento SIMULADO): - Aumento de aceleração RMS (g), sensível a impactos de alta frequência gerados por defeitos em pistas e esferas. - Aumento combinado de vibração e temperatura no mancal afetado. - Queda gradual de rotação sob carga constante, por aumento de atrito. - No modelo da Sprint 2, corresponde à classe 3 (Falha Mecânica): é o padrão de sinal mais gradual.
  • [DOC-04 §Verificações recomendadas] (documento SIMULADO): 1. Comparar aceleração e velocidade entre os dois pontos de medição: o mancal com maior aceleração é o suspeito principal. 2. Verificar ruído anormal (ronco, chiado) com estetoscópio mecânico. 3. Conferir o intervalo de relubrificação e o tipo de graxa. 4. Verificar folgas e desalinhamento do acoplamento.

Fontes consultadas:
  [1] sprint2/motor.db, tabela leituras (dados sintéticos)
  [2] conhecimento/gerado/eventos_falha_mtr.csv (derivado de motor.db)
  [3] DOC-04 §Ações corretivas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.195)
  [4] DOC-04 §Critério de escalonamento — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.178)
  [5] DOC-04 §Sintomas típicos — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.163)
  [6] DOC-04 §Verificações recomendadas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.156)
```

Ferramentas: `consultar_leituras`; `listar_eventos`; `buscar_documentos`

## C5 — Diagnóstico por leitura + situação que exige profissional  [APROVADO]

**Entrada:** Motor com vibração 8.2 mm/s, temperatura 92 C, corrente 15.5 A, rotação 1720 RPM. Posso continuar operando?

**Saída (resposta, 176.5 ms):**

```
Classificador de falhas (Sprint 2): Falha Mecanica com confiança de 58%
  • Probabilidades: Normal 5%, Desbalanceamento 2%, Superaquecimento 35%, Falha Mecanica 58%
  • Entrada: {'rotacao_rpm': 1720.0, 'vibracao_mm_s': 8.2, 'temperatura_c': 92.0, 'corrente_a': 15.5}
  • Modelo treinado em dados SINTÉTICOS (Sprint 2); F1-Macro 0,955 no teste.

Confiança abaixo de 60%: as probabilidades estão divididas entre classes. Trate o resultado como hipótese e confirme com inspeção em campo.

Documentação técnica relacionada:
  • [DOC-04 §Ações corretivas] (documento SIMULADO): 1. Relubrificação conforme plano do fabricante. 2. Substituição do rolamento quando confirmado defeito, com registro do número do componente. 3. Alinhamento do acoplamento após a troca.
  • [DOC-04 §Verificações recomendadas] (documento SIMULADO): 1. Comparar aceleração e velocidade entre os dois pontos de medição: o mancal com maior aceleração é o suspeito principal. 2. Verificar ruído anormal (ronco, chiado) com estetoscópio mecânico. 3. Conferir o intervalo de relubrificação e o tipo de graxa. 4. Verificar folgas e desalinhamento do acoplamento.
  • [DOC-03 §Verificações recomendadas] (documento SIMULADO): 1. Medir a corrente nas três fases e comparar com a corrente nominal de placa. 2. Verificar limpeza das aletas e funcionamento do ventilador. 3. Conferir temperatura ambiente e ventilação do local. 4. Verificar o plano de lubrificação e a última relubrificação registrada.

ATENÇÃO — avaliação de profissional responsável: o assistente apoia a investigação, mas não autoriza intervenções. Decisões de parada, desmontagem, troca de componentes ou continuidade da operação devem ser tomadas pelo responsável técnico, com bloqueio e etiquetagem (LOTO) antes de qualquer intervenção [DOC-08 §Situações que exigem avaliação de profissional responsável].

Fontes consultadas:
  [1] sprint2/modelo_falhas.joblib
  [2] DOC-04 §Ações corretivas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.327)
  [3] DOC-04 §Verificações recomendadas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.248)
  [4] DOC-03 §Verificações recomendadas — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.236)
  [5] DOC-08 §Situações que exigem avaliação de profissional responsável — Regras de segurança e escalonamento para intervenções [SIMULADO] (score 0.471)
```

Ferramentas: `prever_falha_motor`; `buscar_documentos`; `buscar_documentos`

## C6 — Filtro de período fora da cobertura  [APROVADO]

**Entrada:** Como estavam as leituras do FZ-ATV-01 em 10/03/2025?

**Saída (sem_informacao, 0.6 ms):**

```
Não há dados do FZ-ATV-01 no período solicitado (2025-03-10 00:00 a 2025-03-10 23:59). O período disponível na base vai de 2026-05-19 11:46:10 a 2026-05-19 15:43:14. Não é possível afirmar como o ativo se comportou fora desse intervalo.

Fontes consultadas:
  [1] Cobertura temporal da base (scores_anomalias.csv)
```

Ferramentas: 

## C7 — Avaliação de leitura do ativo real (padrão do Ciclo 6)  [APROVADO]

**Entrada:** Leitura do FZ-ATV-01: P1 6,9 mm/s 0,50 g 38 °C; P2 7,1 mm/s 0,52 g 42 °C. Isso é anômalo?

**Saída (resposta, 1718.5 ms):**

```
Avaliação da leitura (FZ-ATV-01) — estado inferido: operação
  • Severidade: MODERADA (1 de 2 modelos sinalizaram anomalia)
  • Isolation Forest: score -0.0349 — não sinalizado
  • Autoencoder: erro 0.7594 (limiar 0.2287) — sinalizado
  • Desvios em relação ao baseline: p1_temperatura z=2.13, p2_temperatura z=2.84
  Score de desvio estatístico, não diagnóstico de causa raiz (sem rótulos de falha).

Documentação técnica relacionada:
  • [DOC-07 §Quando aplicar] (documento SIMULADO): Quando a diferença de temperatura entre a Porta 1 e a Porta 2 se afasta do offset histórico (Porta 2 cerca de 5,5 °C mais quente, desvio-padrão de 1,6 °C), especialmente durante ciclos longos de operação.
  • [DOC-06 §Detecção de anomalias (Sprint 3)]: - Isolation Forest (não supervisionado, treinado com 100% do histórico) e Autoencoder (semissupervisionado, treinado sem o Ciclo 6). - O resultado é um score de desvio em relação ao comportamento histórico, não um diagnóstico de causa raiz. - Severidade combinada: ALTA quando os dois modelos sinalizam, MODERADA quando apenas um sinaliza, BAIXA quando nenhum sinaliza. - Divergência esperada: em anomalias longas e …
  • [DOC-07 §Hipóteses a investigar] (documento SIMULADO): 1. Lubrificação desigual entre os dois mancais. 2. Pré-carga ou desalinhamento afetando apenas um dos lados. 3. Diferença de ventilação ou exposição a fonte de calor externa em um dos pontos. 4. Problema de fixação do sensor (contato térmico ruim) em uma das portas.

Fontes consultadas:
  [1] sprint3/modelo_anomalias_isoforest.joblib
  [2] sprint3/modelo_autoencoder.pt
  [3] sprint3/baseline_operacional.json
  [4] DOC-07 §Quando aplicar — Procedimento de troubleshooting — assimetria térmica entre pontos de medição [SIMULADO] (score 0.28)
  [5] DOC-06 §Detecção de anomalias (Sprint 3) — Como interpretar os resultados dos modelos de IA [PROJETO] (score 0.243)
  [6] DOC-07 §Hipóteses a investigar — Procedimento de troubleshooting — assimetria térmica entre pontos de medição [SIMULADO] (score 0.236)
```

Ferramentas: `avaliar_anomalia_sensor`; `buscar_documentos`

## C8 — Diagnóstico com janela real do banco (integração Sprint 2)  [APROVADO]

**Entrada:** Qual o diagnóstico do MTR-07 em 2023-01-04 06:00?

**Saída (resposta, 42.0 ms):**

```
Classificador de falhas (Sprint 2): Superaquecimento com confiança de 100%
  • Probabilidades: Normal 0%, Desbalanceamento 0%, Superaquecimento 100%, Falha Mecanica 0%
  • Entrada: {'rotacao_rpm': 1724.57, 'vibracao_mm_s': 2.32, 'temperatura_c': 97.74, 'corrente_a': 17.42}
  • Modelo treinado em dados SINTÉTICOS (Sprint 2); F1-Macro 0,955 no teste.
  • Rótulo registrado no banco para esse instante: Superaquecimento

Documentação técnica relacionada:
  • [DOC-03 §Verificações recomendadas] (documento SIMULADO): 1. Medir a corrente nas três fases e comparar com a corrente nominal de placa. 2. Verificar limpeza das aletas e funcionamento do ventilador. 3. Conferir temperatura ambiente e ventilação do local. 4. Verificar o plano de lubrificação e a última relubrificação registrada.
  • [DOC-03 §Sintomas típicos] (documento SIMULADO): - Temperatura de carcaça ou mancal acima do histórico do ativo. - Em motores elétricos, aumento simultâneo de corrente (efeito Joule). - No modelo da Sprint 2, corresponde à classe 2 (Superaquecimento): temperatura acima de 85 °C e corrente acima de 15 A, com vibração baixa.
  • [DOC-04 §Verificações recomendadas] (documento SIMULADO): 1. Comparar aceleração e velocidade entre os dois pontos de medição: o mancal com maior aceleração é o suspeito principal. 2. Verificar ruído anormal (ronco, chiado) com estetoscópio mecânico. 3. Conferir o intervalo de relubrificação e o tipo de graxa. 4. Verificar folgas e desalinhamento do acoplamento.
  • [DOC-03 §Critério de escalonamento] (documento SIMULADO): Temperatura subindo de forma contínua sem estabilizar, ou cheiro de isolamento queimado: desligar com segurança conforme DOC-08 e acionar o responsável técnico. Intervenções elétricas exigem profissional habilitado.

ATENÇÃO — avaliação de profissional responsável: o assistente apoia a investigação, mas não autoriza intervenções. Decisões de parada, desmontagem, troca de componentes ou continuidade da operação devem ser tomadas pelo responsável técnico, com bloqueio e etiquetagem (LOTO) antes de qualquer intervenção [DOC-08 §Situações que exigem avaliação de profissional responsável].

Fontes consultadas:
  [1] sprint2/modelo_falhas.joblib
  [2] sprint2/motor.db
  [3] DOC-03 §Verificações recomendadas — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.258)
  [4] DOC-03 §Sintomas típicos — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.18)
  [5] DOC-04 §Verificações recomendadas — Procedimento de troubleshooting — falha mecânica e rolamentos [SIMULADO] (score 0.163)
  [6] DOC-03 §Critério de escalonamento — Procedimento de troubleshooting — superaquecimento [SIMULADO] (score 0.155)
  [7] DOC-08 §Situações que exigem avaliação de profissional responsável — Regras de segurança e escalonamento para intervenções [SIMULADO] (score 0.471)
```

Ferramentas: `prever_falha_motor`; `buscar_documentos`; `buscar_documentos`

## C9 — Histórico de manutenção  [APROVADO]

**Entrada:** Qual o histórico de manutenção do MTR-03?

**Saída (resposta, 3.7 ms):**

```
Histórico de manutenção do MTR-03 — 2 ordem(ns) de serviço (dados SIMULADOS):
  • OS-20230033 (preventiva), 2023-01-05 20:00: Relubrificação dos mancais — Técnico C [proc. DOC-04]
  • OS-20230005 (corretiva), 2023-01-08 01:10: Limpeza do rotor e balanceamento dinâmico em campo — Técnico C [proc. DOC-02]

Documentação técnica relacionada:
  • [DOC-09 §Motor MTR-03] (documento SIMULADO): Motor MTR-03: fabricante ABB, modelo X100, potência nominal 72.9 kW, data de instalação cadastrada 2023-06-15.

Fontes consultadas:
  [1] conhecimento/historico_manutencao.csv (SIMULADO)
  [2] DOC-09 §Motor MTR-03 — Ficha técnica dos motores MTR-01 a MTR-20 (base sintética) [SIMULADO] (score 0.188)
```

Ferramentas: `historico_manutencao`; `buscar_documentos`

## C10 — Procedimento técnico sem ativo  [APROVADO]

**Entrada:** Quais são os limites de vibração da ISO 10816 para base rígida?

**Saída (resposta, 2.1 ms):**

```
Documentação técnica relacionada:
  • [DOC-01 §Limites de referência para máquinas de 15 kW a 300 kW (grupo 2)] (documento SIMULADO): Base rígida: A até 1,4 mm/s; B até 2,8 mm/s; C até 4,5 mm/s; D acima de 4,5 mm/s. Base flexível: A até 2,3 mm/s; B até 4,5 mm/s; C até 7,1 mm/s; D acima de 7,1 mm/s. O tipo de base do ativo FZ-ATV-01 não foi informado pela Forzy; por isso o assistente apresenta as duas faixas e não emite classificação definitiva de zona para esse ativo.
  • [DOC-01 §Cuidados de interpretação] (documento SIMULADO): - Os limites valem para medição em regime permanente. Picos durante partida e parada (ramp-up/ramp-down) não devem ser classificados por esta tabela. - A tendência ao longo do tempo é mais informativa do que um valor isolado: um aumento de 25% em relação ao histórico do próprio ativo merece investigação mesmo dentro da zona B. - Aceleração RMS (g) é mais sensível a defeitos de rolamento em alta frequência e deve ser …
  • [DOC-06 §Baseline operacional]: - Limites de 3 desvios-padrão calculados separadamente para repouso e operação. - Um z-score acima de 3 em qualquer sensor indica leitura fora do padrão histórico daquele estado. - A feature de maior contribuição para as anomalias do Ciclo 6 foi a diferença de temperatura entre as portas (diff_temp).
  • [DOC-01 §Zonas de severidade] (documento SIMULADO): A norma classifica a vibração em quatro zonas: - Zona A: máquinas recém-comissionadas; condição boa. - Zona B: aceitável para operação contínua sem restrição. - Zona C: insatisfatória para operação contínua prolongada; programar intervenção. - Zona D: severidade suficiente para causar danos; ação imediata.

Fontes consultadas:
  [1] DOC-01 §Limites de referência para máquinas de 15 kW a 300 kW (grupo 2) — Guia de severidade de vibração (referência ISO 10816-3) [SIMULADO] (score 0.278)
  [2] DOC-01 §Cuidados de interpretação — Guia de severidade de vibração (referência ISO 10816-3) [SIMULADO] (score 0.181)
  [3] DOC-06 §Baseline operacional — Como interpretar os resultados dos modelos de IA [PROJETO] (score 0.143)
  [4] DOC-01 §Zonas de severidade — Guia de severidade de vibração (referência ISO 10816-3) [SIMULADO] (score 0.138)
```

Ferramentas: `buscar_documentos`; `buscar_documentos`

## C11 — Valor isolado (ambiguidade de contexto)  [APROVADO]

**Entrada:** Uma vibração de 5,2 mm/s é problema?

**Saída (esclarecimento, 1.5 ms):**

```
Uma vibração de 5.2 mm/s, isoladamente, não permite um diagnóstico. Pela referência ISO 10816-3 (máquinas de 15 a 300 kW) ela ficaria na zona D se a base for rígida e na zona C se a base for flexível [DOC-01 §Limites de referência para máquinas de 15 kW a 300 kW (grupo 2)]. Os limites valem para regime permanente, não para partidas e paradas.

Para uma avaliação com os modelos, informe:
  • o ativo (FZ-ATV-01 ou MTR-01 a MTR-20), e
  • as demais leituras: para FZ-ATV-01, velocidade/aceleração/temperatura das Portas 1 e 2; para motores MTR, rotação, vibração, temperatura e corrente.

Fontes consultadas:
  [1] DOC-01 §Limites de referência para máquinas de 15 kW a 300 kW (grupo 2) — Guia de severidade de vibração (referência ISO 10816-3) [SIMULADO] (score 0.374)
```

Ferramentas: `buscar_documentos`

## C12 — Fora do escopo  [APROVADO]

**Entrada:** Qual o preço do rolamento 6205 no fornecedor?

**Saída (sem_informacao, 0.1 ms):**

```
Não tenho informações para responder a isso: a base do assistente não contém dados comerciais (preços, fornecedores, estoque ou prazos). Ela cobre dados de sensores, resultados dos modelos, histórico de manutenção e procedimentos técnicos. Consulte a área de suprimentos.
```

Ferramentas: 

## C13 — Comparação entre ativos (limitação conhecida)  [APROVADO]

**Entrada:** Compare as falhas do MTR-01 e do MTR-02.

**Saída (esclarecimento, 0.0 ms):**

```
A pergunta cita mais de um ativo (MTR-01, MTR-02). Faça uma pergunta por ativo para que eu filtre os dados corretamente.
```

Ferramentas: 
