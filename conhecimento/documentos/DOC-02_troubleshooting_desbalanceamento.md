---
id: DOC-02
titulo: Procedimento de troubleshooting — desbalanceamento de rotor
tipo: procedimento
ativos: todos
origem: SIMULADO — procedimento elaborado pela equipe para fins acadêmicos, baseado em práticas usuais de manutenção. Validar com o responsável técnico da Forzy antes do uso.
versao: 1.0
---

## Sintomas típicos
- Vibração elevada em velocidade (mm/s), predominante na frequência de 1x a rotação.
- Temperatura e corrente próximas do nominal.
- No modelo da Sprint 2, corresponde à classe 1 (Desbalanceamento): vibração acima de 7 mm/s com rotação instável.

## Verificações iniciais (sem desmontagem)
1. Confirmar a leitura em mais de um ponto de medição e descartar falha do sensor (cabo, fixação magnética, porta IO-Link).
2. Comparar a vibração atual com o histórico do próprio ativo no mesmo estado operacional.
3. Verificar acúmulo de sujeira ou material no rotor, ventilador ou acoplamento.
4. Inspecionar visualmente parafusos de fixação da base e do acoplamento.

## Ações corretivas
1. Limpeza do rotor/ventilador quando houver acúmulo de material.
2. Balanceamento dinâmico em campo ou em bancada, executado por técnico qualificado.
3. Após a intervenção, registrar nova medição de referência e atualizar o baseline do ativo.

## Critério de escalonamento
Vibração na zona D (ver DOC-01) ou crescimento rápido em menos de 24 horas: comunicar o responsável técnico e avaliar parada programada imediata.
