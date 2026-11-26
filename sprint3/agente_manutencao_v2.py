"""
agente_manutencao_v2.py
Agente conversacional com function calling — Sprint 3
Estende o agente da Sprint 2 com uma segunda tool de deteccao de anomalias,
que utiliza os modelos treinados sobre os dados reais da Forzy (Isolation
Forest + Autoencoder) para avaliar leituras de sensores de vibracao e
temperatura em linguagem natural.

Duas tools ficam disponiveis ao LLM:
  1. prever_falha_motor       -> classificador supervisionado (Sprint 2, dados sinteticos)
  2. avaliar_anomalia_sensor  -> detector de anomalias (Sprint 3, dados reais da Forzy)

Uso:
    python agente_manutencao_v2.py --demo
    python agente_manutencao_v2.py            (modo interativo, requer ANTHROPIC_API_KEY)
"""

import json
import re
import joblib
import numpy as np
import torch
import torch.nn as nn


# ─── Carregamento dos modelos ─────────────────────────────────────────────────
ARTEFATOS_ISO = joblib.load("modelo_anomalias_isoforest.joblib")
ISO_MODEL      = ARTEFATOS_ISO["modelo"]
SCALER         = ARTEFATOS_ISO["scaler"]
FEATURE_COLS   = ARTEFATOS_ISO["feature_cols"]
SENSOR_COLS    = ARTEFATOS_ISO["sensor_cols"]
WINDOW         = ARTEFATOS_ISO["window"]
THRESH_RUNNING = ARTEFATOS_ISO["thresh_running"]
BASELINE       = ARTEFATOS_ISO["baseline_operacional"]


class Autoencoder(nn.Module):
    def __init__(self, n_features, bottleneck=6):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, 16), nn.ReLU(),
            nn.Linear(16, bottleneck), nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, 16), nn.ReLU(),
            nn.Linear(16, n_features)
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)


_ckpt = torch.load("modelo_autoencoder.pt", map_location="cpu", weights_only=False)
AE_MODEL = Autoencoder(_ckpt["n_features"], _ckpt["bottleneck"])
AE_MODEL.load_state_dict(_ckpt["state_dict"])
AE_MODEL.eval()
LIMIAR_AE = _ckpt["limiar_anomalia"]


# ─── Definição das Tools ──────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "avaliar_anomalia_sensor",
        "description": (
            "Recebe uma leitura instantanea dos sensores de vibracao (velocidade e "
            "aceleracao) e temperatura de dois pontos de medicao (Porta 1 e Porta 2) "
            "de um ativo monitorado pela Forzy, e retorna um score de anomalia "
            "calculado por dois modelos independentes (Isolation Forest e "
            "Autoencoder), o nivel de severidade e quais sensores mais contribuiram "
            "para o desvio em relacao ao baseline operacional historico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "p1_velocidade":  {"type": "number", "description": "Velocidade de vibracao RMS, Porta 1 (mm/s)"},
                "p1_aceleracao":  {"type": "number", "description": "Aceleracao de vibracao RMS, Porta 1 (g)"},
                "p1_temperatura": {"type": "number", "description": "Temperatura, Porta 1 (graus C)"},
                "p2_velocidade":  {"type": "number", "description": "Velocidade de vibracao RMS, Porta 2 (mm/s)"},
                "p2_aceleracao":  {"type": "number", "description": "Aceleracao de vibracao RMS, Porta 2 (g)"},
                "p2_temperatura": {"type": "number", "description": "Temperatura, Porta 2 (graus C)"},
            },
            "required": ["p1_velocidade", "p1_aceleracao", "p1_temperatura",
                         "p2_velocidade", "p2_aceleracao", "p2_temperatura"]
        }
    },
    {
        "name": "prever_falha_motor",
        "description": (
            "Classificador supervisionado da Sprint 2 (treinado em dados sinteticos "
            "de motores industriais). Recebe rotacao, vibracao, temperatura e "
            "corrente e retorna a classe de falha prevista: Normal, "
            "Desbalanceamento, Superaquecimento ou Falha Mecanica."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rotacao_rpm":   {"type": "number", "description": "Rotacao em RPM"},
                "vibracao_mm_s": {"type": "number", "description": "Vibracao em mm/s"},
                "temperatura_c": {"type": "number", "description": "Temperatura em C"},
                "corrente_a":    {"type": "number", "description": "Corrente em A"},
            },
            "required": ["rotacao_rpm", "vibracao_mm_s", "temperatura_c", "corrente_a"]
        }
    },
]


# ─── Implementação da tool de anomalias ──────────────────────────────────────
def avaliar_anomalia_sensor(p1_velocidade: float, p1_aceleracao: float, p1_temperatura: float,
                             p2_velocidade: float, p2_aceleracao: float, p2_temperatura: float) -> dict:
    """
    Avalia uma leitura instantanea contra os modelos de anomalia treinados sobre
    o historico real da Forzy.

    Limitacao importante: os modelos foram treinados com features de janela
    movel (media/desvio das ultimas 5 leituras) e taxa de variacao, que exigem
    contexto historico indisponivel para uma consulta avulsa via chat. Nesta
    implementacao, os valores de janela movel e taxa sao aproximados pelo
    proprio valor pontual informado (equivalente a assumir que a leitura atual
    e representativa das ultimas leituras) -- uma simplificacao adequada para
    uma primeira triagem conversacional, mas nao um substituto do pipeline
    completo de streaming em producao.
    """
    vals = {
        "p1_velocidade": p1_velocidade, "p1_aceleracao": p1_aceleracao, "p1_temperatura": p1_temperatura,
        "p2_velocidade": p2_velocidade, "p2_aceleracao": p2_aceleracao, "p2_temperatura": p2_temperatura,
    }

    running = int((p1_velocidade > THRESH_RUNNING) or (p2_velocidade > THRESH_RUNNING))
    estado = "running" if running else "idle"

    diff_vel  = p1_velocidade - p2_velocidade
    diff_temp = p1_temperatura - p2_temperatura
    diff_acel = p1_aceleracao - p2_aceleracao

    # Construcao do vetor de features na mesma ordem do treinamento.
    # mean5 <- valor pontual (sem historico disponivel); std5 <- 0; taxa <- 0
    x = np.zeros((1, len(FEATURE_COLS)))
    for i, col in enumerate(FEATURE_COLS):
        if col in vals:
            x[0, i] = vals[col]
        elif col.endswith("_mean5"):
            base = col.replace("_mean5", "")
            x[0, i] = vals.get(base, 0)
        elif col.endswith("_std5"):
            x[0, i] = 0.0
        elif col.endswith("_taxa"):
            x[0, i] = 0.0
        elif col == "diff_vel":
            x[0, i] = diff_vel
        elif col == "diff_temp":
            x[0, i] = diff_temp
        elif col == "diff_acel":
            x[0, i] = diff_acel
        elif col == "running":
            x[0, i] = running
        elif col == "dt_seg":
            x[0, i] = 1.0  # valor tipico de intervalo entre leituras

    x_scaled = SCALER.transform(x)

    score_iso = float(-ISO_MODEL.decision_function(x_scaled)[0])
    flag_iso  = bool(ISO_MODEL.predict(x_scaled)[0] == -1)

    with torch.no_grad():
        x_t = torch.tensor(x_scaled, dtype=torch.float32)
        recon = AE_MODEL(x_t)
        erro_ae = float(torch.mean((recon - x_t) ** 2).item())
    flag_ae = bool(erro_ae > LIMIAR_AE)

    # Desvio em relacao ao baseline operacional (z-score condicionado ao estado)
    desvios = {}
    alertas = []
    for col, valor in vals.items():
        mu = BASELINE[estado][col]["media"]
        sigma = BASELINE[estado][col]["desvio_padrao"] or 1e-6
        z = (valor - mu) / sigma
        desvios[col] = round(z, 2)
        if abs(z) > 3:
            alertas.append(f"{col}={valor} (z-score={z:.1f}, fora do baseline de {estado})")

    # Severidade combinada
    n_alertas_modelo = int(flag_iso) + int(flag_ae)
    if n_alertas_modelo == 2:
        severidade = "ALTA"
    elif n_alertas_modelo == 1:
        severidade = "MODERADA"
    else:
        severidade = "BAIXA"

    return {
        "estado_operacional": estado,
        "score_isolation_forest": round(score_iso, 4),
        "sinalizado_isolation_forest": flag_iso,
        "erro_reconstrucao_autoencoder": round(erro_ae, 5),
        "limiar_autoencoder": round(LIMIAR_AE, 5),
        "sinalizado_autoencoder": flag_ae,
        "severidade": severidade,
        "concordancia_modelos": f"{n_alertas_modelo} de 2 modelos sinalizaram anomalia",
        "desvios_zscore": desvios,
        "alertas_sensores": alertas,
        "valores_entrada": vals,
    }


def prever_falha_motor(rotacao_rpm: float, vibracao_mm_s: float,
                        temperatura_c: float, corrente_a: float) -> dict:
    """Wrapper simplificado do classificador da Sprint 2 (referencia de comparacao)."""
    try:
        arts = joblib.load("modelo_falhas.joblib")
    except FileNotFoundError:
        return {"erro": "modelo_falhas.joblib (Sprint 2) nao encontrado neste ambiente."}

    modelo = arts["modelo"]
    feature_cols = arts["feature_cols"]
    label_map = arts["label_map"]

    vals = {"rotacao_rpm": rotacao_rpm, "vibracao_mm_s": vibracao_mm_s,
            "temperatura_c": temperatura_c, "corrente_a": corrente_a}

    x = np.zeros((1, len(feature_cols)))
    for i, col in enumerate(feature_cols):
        for base in vals:
            if col.startswith(base):
                x[0, i] = vals[base]
                break

    pred = int(modelo.predict(x)[0])
    proba = modelo.predict_proba(x)[0]
    return {
        "classe_prevista": pred,
        "diagnostico": label_map[pred],
        "probabilidades": {label_map[i]: round(float(p), 4) for i, p in enumerate(proba)},
        "confianca": round(float(proba[pred]), 4),
    }


# ─── Motor do Agente ─────────────────────────────────────────────────────────
def processar_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "avaliar_anomalia_sensor":
        resultado = avaliar_anomalia_sensor(**tool_input)
    elif tool_name == "prever_falha_motor":
        resultado = prever_falha_motor(**tool_input)
    else:
        resultado = {"erro": f"Tool '{tool_name}' nao reconhecida."}
    return json.dumps(resultado, ensure_ascii=False, indent=2)


SYSTEM = """Voce e um especialista em manutencao preditiva e deteccao de anomalias
industriais da Forzy.

Voce tem acesso a duas ferramentas:

1. avaliar_anomalia_sensor -- para leituras de sensores de VIBRACAO (velocidade,
   aceleracao) e TEMPERATURA de dois pontos de medicao (Porta 1 / Porta 2). Use
   esta ferramenta sempre que o usuario descrever leituras nesse formato.
   Os modelos foram treinados sobre o historico real de um ativo da Forzy, SEM
   rotulos de falha -- portanto o resultado e um SCORE DE ANOMALIA relativo ao
   comportamento historico, nao uma classificacao de tipo de falha conhecida.

2. prever_falha_motor -- classificador da Sprint 2, treinado em dados sinteticos
   de motores com rotacao/vibracao/temperatura/corrente e categorias de falha
   conhecidas (Desbalanceamento, Superaquecimento, Falha Mecanica). Use apenas
   se o usuario fornecer esse conjunto especifico de variaveis.

Ao responder com base em avaliar_anomalia_sensor, explique:
- O estado operacional inferido (repouso ou operacao).
- Se os dois modelos concordam ou divergem, e o que isso significa em termos
  de confianca da deteccao.
- Quais sensores mais desviam do baseline historico (cite os z-scores).
- Um nivel de severidade e uma recomendacao pratica.
- Deixe claro que, por nao haver rotulos de falha confirmados nesta base, o
  resultado indica uma leitura estatisticamente incomum -- nao um diagnostico
  de causa raiz confirmado -- e recomende validacao por um tecnico quando a
  severidade for ALTA.
"""


def chat(historico: list, mensagem_usuario: str) -> tuple:
    try:
        import anthropic
        client = anthropic.Anthropic()

        historico.append({"role": "user", "content": mensagem_usuario})

        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1500,
            system=SYSTEM, tools=TOOLS, messages=historico,
        )

        while response.stop_reason == "tool_use":
            tool_block = next(b for b in response.content if b.type == "tool_use")
            tool_result = processar_tool_call(tool_block.name, tool_block.input)

            historico.append({"role": "assistant", "content": response.content})
            historico.append({"role": "user", "content": [{
                "type": "tool_result", "tool_use_id": tool_block.id, "content": tool_result
            }]})

            response = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=1500,
                system=SYSTEM, tools=TOOLS, messages=historico,
            )

        resposta_final = "".join(b.text for b in response.content if hasattr(b, "text"))
        historico.append({"role": "assistant", "content": resposta_final})
        return resposta_final, historico

    except ImportError:
        return _chat_offline(historico, mensagem_usuario)


def _chat_offline(historico: list, mensagem_usuario: str) -> tuple:
    """Fallback offline: extrai 6 numeros (P1 vel/acel/temp, P2 vel/acel/temp) e chama a tool direto."""
    historico.append({"role": "user", "content": mensagem_usuario})
    nums = re.findall(r"[-+]?\d*\.?\d+", mensagem_usuario)
    nums = [float(n) for n in nums]

    if len(nums) < 6:
        resp = ("Nao consegui identificar as 6 leituras necessarias. Informe, na ordem: "
                "velocidade P1 (mm/s), aceleracao P1 (g), temperatura P1 (C), "
                "velocidade P2 (mm/s), aceleracao P2 (g), temperatura P2 (C).")
        historico.append({"role": "assistant", "content": resp})
        return resp, historico

    resultado = avaliar_anomalia_sensor(*nums[:6])

    linhas = [
        f"Estado operacional inferido: {resultado['estado_operacional'].upper()}",
        f"Severidade: {resultado['severidade']} ({resultado['concordancia_modelos']})",
        "",
        f"Isolation Forest — score: {resultado['score_isolation_forest']}  "
        f"| sinalizado: {'SIM' if resultado['sinalizado_isolation_forest'] else 'nao'}",
        f"Autoencoder     — erro reconstrucao: {resultado['erro_reconstrucao_autoencoder']}  "
        f"(limiar: {resultado['limiar_autoencoder']})  "
        f"| sinalizado: {'SIM' if resultado['sinalizado_autoencoder'] else 'nao'}",
    ]
    if resultado["alertas_sensores"]:
        linhas += ["", "Sensores fora do baseline (|z-score| > 3):"]
        for a in resultado["alertas_sensores"]:
            linhas.append(f"  ! {a}")
    else:
        linhas += ["", "Nenhum sensor individual excede 3 desvios-padrao do baseline historico."]

    linhas += ["", "Nota: sem rotulos de falha confirmados nesta base — resultado indica",
               "desvio estatistico do padrao historico, recomenda-se validacao tecnica",
               "presencial quando a severidade for ALTA."]

    resp = "\n".join(linhas)
    historico.append({"role": "assistant", "content": resp})
    return resp, historico


# ─── Demonstração ─────────────────────────────────────────────────────────────
def demo_cenarios():
    cenarios = [
        {
            "nome": "Cenario 1 — Repouso normal",
            "params": (0.05, 0.00, 33, 0.05, 0.00, 39),
        },
        {
            "nome": "Cenario 2 — Operacao tipica (ciclo curto, dentro do padrao)",
            "params": (5.80, 0.47, 28, 6.00, 0.47, 35),
        },
        {
            "nome": "Cenario 3 — Padrao do Ciclo 6 (operacao prolongada, alta temperatura)",
            "params": (6.90, 0.50, 38, 7.10, 0.52, 42),
        },
    ]

    print("=" * 62)
    print("  DEMONSTRACAO — AGENTE DE ANOMALIAS (Sprint 3)")
    print("=" * 62)

    for cen in cenarios:
        print(f"\n{'-'*62}\n  {cen['nome']}\n{'-'*62}")
        resultado = avaliar_anomalia_sensor(*cen["params"])
        print(f"Entrada (P1 vel/acel/temp, P2 vel/acel/temp): {cen['params']}")
        print(f"\nEstado operacional : {resultado['estado_operacional']}")
        print(f"Severidade         : {resultado['severidade']}  "
              f"({resultado['concordancia_modelos']})")
        print(f"Score IsoForest    : {resultado['score_isolation_forest']}  "
              f"(sinalizado: {resultado['sinalizado_isolation_forest']})")
        print(f"Erro Autoencoder   : {resultado['erro_reconstrucao_autoencoder']}  "
              f"(limiar: {resultado['limiar_autoencoder']}, "
              f"sinalizado: {resultado['sinalizado_autoencoder']})")
        if resultado["alertas_sensores"]:
            print("Alertas:")
            for a in resultado["alertas_sensores"]:
                print(f"  ! {a}")
        else:
            print("Nenhum sensor excede 3 desvios-padrao do baseline.")

    print("\n" + "=" * 62)


def main():
    print("Agente de Manutencao Preditiva + Deteccao de Anomalias (Sprint 3)")
    print("Digite leituras de sensores ou 'sair' para encerrar.\n")
    historico = []
    while True:
        try:
            entrada = input("Voce: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if entrada.lower() in ("sair", "exit", "quit"):
            break
        if not entrada:
            continue
        resposta, historico = chat(historico, entrada)
        print(f"\nAgente:\n{resposta}\n")
        print("-" * 50)


if __name__ == "__main__":
    import sys
    demo_cenarios()
    if "--demo" not in sys.argv:
        print()
        try:
            main()
        except Exception as e:
            print(f"Modo interativo indisponivel ({e}). Use --demo para so a demonstracao.")
