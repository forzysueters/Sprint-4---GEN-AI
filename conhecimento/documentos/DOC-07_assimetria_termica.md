---
id: DOC-07
titulo: Procedimento de troubleshooting — assimetria térmica entre pontos de medição
tipo: procedimento
ativos: FZ-ATV-01
origem: SIMULADO — procedimento elaborado pela equipe a partir do achado de explicabilidade da Sprint 3 (diff_temp). Validar com o responsável técnico da Forzy.
versao: 1.0
---

## Quando aplicar
Quando a diferença de temperatura entre a Porta 1 e a Porta 2 se afasta do offset histórico (Porta 2 cerca de 5,5 °C mais quente, desvio-padrão de 1,6 °C), especialmente durante ciclos longos de operação.

## Hipóteses a investigar
1. Lubrificação desigual entre os dois mancais.
2. Pré-carga ou desalinhamento afetando apenas um dos lados.
3. Diferença de ventilação ou exposição a fonte de calor externa em um dos pontos.
4. Problema de fixação do sensor (contato térmico ruim) em uma das portas.

## Passos de verificação
1. Medir a temperatura dos dois mancais com termômetro infravermelho para confirmar a leitura dos sensores.
2. Conferir torque e fixação dos dois sensores.
3. Verificar o histórico de lubrificação de cada mancal.
4. Repetir um ciclo longo de operação controlado e comparar a evolução de diff_temp.

## Critério de escalonamento
Se a assimetria persistir após confirmar a fixação dos sensores, programar inspeção do mancal mais quente com o responsável técnico.
