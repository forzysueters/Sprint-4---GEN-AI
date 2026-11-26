---
id: DOC-06
titulo: Como interpretar os resultados dos modelos de IA
tipo: guia_modelos
ativos: todos
origem: PROJETO — síntese dos relatórios técnicos das Sprints 2 e 3.
versao: 1.0
---

## Classificador de falhas (Sprint 2)
- Random Forest treinado em dados SINTÉTICOS (motor.db) com quatro classes: Normal, Desbalanceamento, Superaquecimento e Falha Mecânica.
- F1-Macro de 0,955 no conjunto de teste temporal. Os erros se concentram no início da rampa de deterioração.
- Só se aplica aos motores MTR-01 a MTR-20 ou a leituras com rotação, vibração, temperatura e corrente. Não se aplica ao ativo FZ-ATV-01, que não mede rotação nem corrente.

## Detecção de anomalias (Sprint 3)
- Isolation Forest (não supervisionado, treinado com 100% do histórico) e Autoencoder (semissupervisionado, treinado sem o Ciclo 6).
- O resultado é um score de desvio em relação ao comportamento histórico, não um diagnóstico de causa raiz.
- Severidade combinada: ALTA quando os dois modelos sinalizam, MODERADA quando apenas um sinaliza, BAIXA quando nenhum sinaliza.
- Divergência esperada: em anomalias longas e coesas (como o Ciclo 6) o Isolation Forest original tende a não sinalizar, enquanto o Autoencoder sinaliza.

## Baseline operacional
- Limites de 3 desvios-padrão calculados separadamente para repouso e operação.
- Um z-score acima de 3 em qualquer sensor indica leitura fora do padrão histórico daquele estado.
- A feature de maior contribuição para as anomalias do Ciclo 6 foi a diferença de temperatura entre as portas (diff_temp).

## Uso responsável
Os resultados servem para priorizar inspeções. Qualquer decisão de parada, desmontagem ou troca de componente deve ser validada por profissional responsável.
