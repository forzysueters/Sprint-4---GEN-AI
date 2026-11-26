# FORZY.md — Documentação dos Dados Históricos da Forzy

## Origem

Arquivo `forzy_history.csv`, exportado de um sistema de aquisição IO-Link Master
(formato padrão de exportação "History" com três linhas de cabeçalho técnico).
Registra leituras de **dois sensores de vibração e temperatura** conectados às
Portas 1 e 2 de um IO-Link Master, monitorando dois pontos de medição do mesmo
ativo industrial (compatível com o padrão de instalação em rolamento do lado
acionado / não-acionado de um motor ou máquina rotativa).

## Formato do Arquivo Bruto

- Separador: `;` (ponto e vírgula)
- Codificação: UTF-8
- 3 linhas de cabeçalho técnico (nome do canal IO-Link, descrição do parâmetro, tipo de dado)
- 1 coluna de timestamp (sem nome, primeira coluna) em formato ISO 8601 com milissegundos
- 2 colunas de array de bytes brutos (`PDI Data Byte Array`) — payload IO-Link não decodificado,
  redundante com as colunas numéricas já decodificadas; não utilizado na modelagem
- 6 colunas numéricas (`Double`) já decodificadas pelo IO-Link Master

## Schema (após parsing)

| Coluna            | Origem IO-Link         | Unidade | Descrição                                  |
|--------------------|------------------------|---------|---------------------------------------------|
| `timestamp`        | —                       | —       | Data/hora da leitura (ISO 8601, ms)          |
| `p1_velocidade`     | Porta 1 / Canal 1.1     | mm/s    | Velocidade de vibração RMS — Ponto 1         |
| `p1_aceleracao`     | Porta 1 / Canal 1.2     | g       | Aceleração de vibração RMS — Ponto 1         |
| `p1_temperatura`    | Porta 1 / Canal 1.3     | °C      | Temperatura do sensor — Ponto 1              |
| `p2_velocidade`     | Porta 2 / Canal 2.1     | mm/s    | Velocidade de vibração RMS — Ponto 2         |
| `p2_aceleracao`     | Porta 2 / Canal 2.2     | g       | Aceleração de vibração RMS — Ponto 2         |
| `p2_temperatura`    | Porta 2 / Canal 2.3     | °C      | Temperatura do sensor — Ponto 2              |

Velocidade de vibração RMS (mm/s) é a métrica padrão de severidade de vibração
usada na norma **ISO 10816** para diagnóstico de desbalanceamento, desalinhamento
e folgas mecânicas em baixa/média frequência. Aceleração RMS (g) é mais sensível
a defeitos de rolamento em alta frequência. Ambas as métricas, quando cruzadas,
permitem diferenciar o tipo de anomalia mecânica.

## Volume e Período Histórico

- **7.183 leituras** no total
- **Período coberto:** 2026-05-19, 11:46:10 até 15:43:14 (aproximadamente 3h57min)
- **Frequência de amostragem:** irregular, no padrão *report-on-change* típico de
  dispositivos IO-Link — o sensor reporta com maior frequência quando o valor
  varia (durante operação) e com menor frequência quando o valor está estável
  (durante repouso). Intervalo mediano entre leituras: 0,59 segundos;
  intervalo máximo observado: 228 segundos (durante longos períodos de repouso).

## Estados Operacionais Identificados

A análise exploratória identificou dois estados operacionais claros a partir do
limiar de velocidade de vibração (0,5 mm/s):

- **Repouso (idle):** vibração residual de ruído de fundo (~0,03–0,10 mm/s),
  representando 47,2% das leituras.
- **Operação (running):** vibração elevada (pico de até 7,7 mm/s), representando
  52,8% das leituras, distribuídas em **6 ciclos operacionais distintos**
  (liga/desliga) ao longo do período monitorado.

O sexto e último ciclo se destaca por ser significativamente mais longo
(17,4 minutos, contra 2–4,4 minutos dos demais) e atingir a temperatura mais alta
registrada em todo o histórico (39°C no Ponto 1 / 43°C no Ponto 2 durante a
operação, com pico posterior de até 46–47°C no resfriamento). Esse ciclo é o
principal caso de interesse para a análise de anomalias.

## Variáveis Utilizadas no Modelo

Não há rótulos de falha no conjunto de dados — nenhuma coluna indica se uma
leitura corresponde a uma condição normal ou anômala. Todas as seis colunas
numéricas (`p1_velocidade`, `p1_aceleracao`, `p1_temperatura`, `p2_velocidade`,
`p2_aceleracao`, `p2_temperatura`) são utilizadas como variáveis de entrada do
modelo de detecção de anomalias. As colunas de array de bytes brutos
(`port1_raw`, `port2_raw`) são descartadas por serem redundantes com os canais
já decodificados.

## Limitações do Recorte de Dados

Este extrato representa **um único ativo físico** (ou par de pontos de medição
do mesmo ativo) observado em uma janela de aproximadamente 4 horas — um recorte
bem mais restrito do que os 20 motores e 30.000 leituras utilizados na Sprint 2
(base sintética `motor.db`). Por esse motivo, análises que dependem de múltiplos
ativos (ex.: ranking de "quais equipamentos" desviam mais) são adaptadas neste
projeto para operar na granularidade disponível: os 6 ciclos operacionais e os
2 pontos de medição (Porta 1 / Porta 2). A metodologia desenvolvida generaliza
diretamente para múltiplos ativos assim que mais dados históricos da Forzy
estiverem disponíveis.
