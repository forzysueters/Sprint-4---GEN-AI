---
id: DOC-05
titulo: Ficha técnica e instalação dos sensores — ativo FZ-ATV-01
tipo: ficha_tecnica
ativos: FZ-ATV-01
origem: REAL (dados de aquisição fornecidos pela Forzy) + campos marcados como "não informado" onde a Forzy não forneceu dados. O identificador FZ-ATV-01 foi atribuído pela equipe.
versao: 1.0
---

## Identificação
- Identificador no projeto: FZ-ATV-01 (atribuído pela equipe, pois o extrato não traz identificador de ativo).
- Tipo de equipamento: não informado pela Forzy. O padrão de medição é compatível com máquina rotativa monitorada em dois mancais (lado acionado e lado não acionado).
- Fabricante, modelo, potência e tipo de base: não informados.

## Pontos de medição
- Porta 1 do IO-Link Master: canais 1.1 velocidade RMS (mm/s), 1.2 aceleração RMS (g), 1.3 temperatura (°C).
- Porta 2 do IO-Link Master: canais 2.1 velocidade RMS (mm/s), 2.2 aceleração RMS (g), 2.3 temperatura (°C).
- A Porta 2 é sistematicamente cerca de 5,5 °C mais quente que a Porta 1 (offset físico constante, não anomalia).

## Período de dados disponível
- 19/05/2026, das 11:46:10 às 15:43:14 (cerca de 3h57min), 7.183 leituras.
- Amostragem irregular (report-on-change), intervalo mediano de 0,59 s.

## Estados e ciclos operacionais
- Limiar de operação: velocidade acima de 0,5 mm/s em qualquer porta.
- Seis ciclos operacionais identificados; os ciclos 1 a 5 duram entre 1,8 e 4,4 minutos.
- O Ciclo 6 (13:44 às 14:01) durou 17,4 minutos e atingiu a maior temperatura do período.

## Histórico de manutenção
Nenhum registro de manutenção, falha confirmada ou ordem de serviço foi fornecido para este ativo.
