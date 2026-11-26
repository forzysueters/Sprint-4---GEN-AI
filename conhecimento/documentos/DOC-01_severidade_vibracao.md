---
id: DOC-01
titulo: Guia de severidade de vibração (referência ISO 10816-3)
tipo: referencia_tecnica
ativos: todos
origem: SIMULADO — resumo elaborado pela equipe a partir de valores amplamente difundidos da ISO 10816-3. Não substitui a norma original.
versao: 1.0
---

## Objetivo
Orientar a interpretação da velocidade de vibração RMS (mm/s) medida nos mancais de máquinas rotativas, classificando a condição em zonas de severidade. A velocidade RMS é a grandeza usada pelos sensores IO-Link do ativo FZ-ATV-01 (canais 1.1 e 2.1) e pela coluna vibracao_mm_s dos motores MTR.

## Zonas de severidade
A norma classifica a vibração em quatro zonas:
- Zona A: máquinas recém-comissionadas; condição boa.
- Zona B: aceitável para operação contínua sem restrição.
- Zona C: insatisfatória para operação contínua prolongada; programar intervenção.
- Zona D: severidade suficiente para causar danos; ação imediata.

## Limites de referência para máquinas de 15 kW a 300 kW (grupo 2)
Base rígida: A até 1,4 mm/s; B até 2,8 mm/s; C até 4,5 mm/s; D acima de 4,5 mm/s.
Base flexível: A até 2,3 mm/s; B até 4,5 mm/s; C até 7,1 mm/s; D acima de 7,1 mm/s.
O tipo de base do ativo FZ-ATV-01 não foi informado pela Forzy; por isso o assistente apresenta as duas faixas e não emite classificação definitiva de zona para esse ativo.

## Cuidados de interpretação
- Os limites valem para medição em regime permanente. Picos durante partida e parada (ramp-up/ramp-down) não devem ser classificados por esta tabela.
- A tendência ao longo do tempo é mais informativa do que um valor isolado: um aumento de 25% em relação ao histórico do próprio ativo merece investigação mesmo dentro da zona B.
- Aceleração RMS (g) é mais sensível a defeitos de rolamento em alta frequência e deve ser analisada em conjunto com a velocidade.
