"""
ferramentas.py — Ferramentas que o assistente pode acionar.

Integra os artefatos das sprints anteriores:
  * Sprint 2: motor.db + classificador Random Forest (modelo_falhas.joblib)
  * Sprint 3: scores_anomalias.csv + Isolation Forest + Autoencoder + baseline operacional
  * Sprint 4: busca na base de conhecimento (RAG) e histórico de manutenção

Toda ferramenta devolve um dicionário serializável com a chave "fontes", usada
para montar a seção de fontes consultadas na resposta.
"""
import json
import sqlite3
import warnings
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from rag import config, recuperador

warnings.filterwarnings("ignore", category=UserWarning)


# ─── Carregamento preguiçoso dos artefatos ───────────────────────────────────
@lru_cache(maxsize=1)
def _leituras_mtr():
    con = sqlite3.connect(config.MOTOR_DB)
    df = pd.read_sql("SELECT l.*, m.fabricante, m.modelo FROM leituras l JOIN motores m ON m.id = l.motor_id", con)
    con.close()
    df["ativo"] = df["motor_id"].map(lambda i: f"MTR-{i:02d}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@lru_cache(maxsize=1)
def _leituras_fz():
    df = pd.read_csv(config.SCORES_FZ, parse_dates=["timestamp"])
    # cycle_id do CSV numera segmentos (repouso e operação); convertemos para ciclo operacional 1..6
    seg_run = df.loc[df["running"] == 1, "cycle_id"].drop_duplicates().tolist()
    df["ciclo"] = df["cycle_id"].map({s: i + 1 for i, s in enumerate(seg_run)})
    return df


@lru_cache(maxsize=1)
def _modelo_falhas():
    return joblib.load(config.MODELO_FALHAS)


@lru_cache(maxsize=1)
def _modelos_anomalia():
    import torch
    import torch.nn as nn

    class Autoencoder(nn.Module):  # mesma arquitetura da Sprint 3
        def __init__(self, n_features, bottleneck=6):
            super().__init__()
            self.encoder = nn.Sequential(nn.Linear(n_features, 16), nn.ReLU(), nn.Linear(16, bottleneck), nn.ReLU())
            self.decoder = nn.Sequential(nn.Linear(bottleneck, 16), nn.ReLU(), nn.Linear(16, n_features))

        def forward(self, x):
            return self.decoder(self.encoder(x))

    iso = joblib.load(config.MODELO_ISO)
    ck = torch.load(config.MODELO_AE, map_location="cpu", weights_only=False)
    ae = Autoencoder(ck["n_features"], ck["bottleneck"])
    ae.load_state_dict(ck["state_dict"])
    ae.eval()
    return iso, ae, ck["limiar_anomalia"]


def _filtrar_periodo(df, inicio, fim):
    if inicio:
        df = df[df["timestamp"] >= pd.Timestamp(inicio)]
    if fim:
        df = df[df["timestamp"] <= pd.Timestamp(fim)]
    return df


def cobertura(ativo):
    """Período disponível para o ativo."""
    df = _leituras_fz() if ativo == config.ID_FORZY else _leituras_mtr()
    if ativo != config.ID_FORZY:
        df = df[df["ativo"] == ativo]
    return df["timestamp"].min().isoformat(sep=" ", timespec="seconds"), \
        df["timestamp"].max().isoformat(sep=" ", timespec="seconds")


# ─── Ferramenta 1: leituras de sensores ──────────────────────────────────────
def consultar_leituras(ativo: str, inicio: str = None, fim: str = None, ciclo: int = None) -> dict:
    if ativo == config.ID_FORZY:
        df = _leituras_fz()
        if ciclo:
            df = df[df["ciclo"] == ciclo]
        cols = {"p1_velocidade": "mm/s", "p2_velocidade": "mm/s", "p1_aceleracao": "g",
                "p2_aceleracao": "g", "p1_temperatura": "°C", "p2_temperatura": "°C"}
        fonte = "sprint3/scores_anomalias.csv (dados reais Forzy)"
    elif ativo in config.IDS_MOTORES:
        df = _leituras_mtr()
        df = df[df["ativo"] == ativo]
        cols = {"rotacao_rpm": "RPM", "vibracao_mm_s": "mm/s", "temperatura_c": "°C", "corrente_a": "A"}
        fonte = "sprint2/motor.db, tabela leituras (dados sintéticos)"
    else:
        return {"erro": f"Ativo '{ativo}' não cadastrado.", "fontes": []}

    df = _filtrar_periodo(df, inicio, fim)
    cob = cobertura(ativo)
    if df.empty:
        return {"ativo": ativo, "sem_dados": True, "cobertura_disponivel": cob,
                "mensagem": "Nenhuma leitura no período solicitado.", "fontes": [fonte]}
    estat = {c: {"unidade": u, "min": round(float(df[c].min()), 3), "media": round(float(df[c].mean()), 3),
                 "max": round(float(df[c].max()), 3), "ultima": round(float(df[c].iloc[-1]), 3)}
             for c, u in cols.items()}
    out = {"ativo": ativo, "periodo_consultado": [df["timestamp"].min().isoformat(sep=" ", timespec="seconds"),
                                                  df["timestamp"].max().isoformat(sep=" ", timespec="seconds")],
           "n_leituras": int(len(df)), "estatisticas": estat, "cobertura_disponivel": cob, "fontes": [fonte]}
    if ativo == config.ID_FORZY:
        out["pct_em_operacao"] = round(float(100 * df["running"].mean()), 1)
    else:
        out["leituras_em_falha"] = int((df["falha"] != 0).sum())
    return out


# ─── Ferramenta 2: eventos de falha / ciclos ─────────────────────────────────
def listar_eventos(ativo: str, inicio: str = None, fim: str = None) -> dict:
    if ativo == config.ID_FORZY:
        cic = pd.read_csv(config.DIR_GERADO / "ciclos_fz.csv")
        if inicio:
            cic = cic[cic["fim"] >= inicio[:19]]
        if fim:
            cic = cic[cic["inicio"] <= fim[:19]]
        return {"ativo": ativo, "tipo": "ciclos_operacionais", "rotulos_de_falha_disponiveis": False,
                "ciclos": cic.to_dict("records"),
                "observacao": "Não há falhas confirmadas para este ativo; ciclos com alto percentual de "
                              "leituras sinalizadas pelos modelos são candidatos a anomalia.",
                "fontes": ["conhecimento/gerado/ciclos_fz.csv (derivado de scores_anomalias.csv)"]}
    ev = pd.read_csv(config.DIR_GERADO / "eventos_falha_mtr.csv")
    ev = ev[ev["ativo"] == ativo]
    if inicio:
        ev = ev[ev["fim"] >= inicio[:19]]
    if fim:
        ev = ev[ev["inicio"] <= fim[:19]]
    return {"ativo": ativo, "tipo": "eventos_de_falha", "eventos": ev.to_dict("records"),
            "fontes": ["conhecimento/gerado/eventos_falha_mtr.csv (derivado de motor.db)"]}


# ─── Ferramenta 3: histórico de manutenção ───────────────────────────────────
def historico_manutencao(ativo: str, inicio: str = None, fim: str = None) -> dict:
    h = pd.read_csv(config.HISTORICO_OS)
    h = h[h["ativo"] == ativo]
    if inicio:
        h = h[h["data_conclusao"] >= inicio[:19]]
    if fim:
        h = h[h["data_abertura"] <= fim[:19]]
    return {"ativo": ativo, "n_ordens": int(len(h)), "ordens": h.to_dict("records"),
            "origem": "SIMULADO" if len(h) else None,
            "fontes": ["conhecimento/historico_manutencao.csv (SIMULADO)"]}


# ─── Ferramenta 4: classificador da Sprint 2 ─────────────────────────────────
def prever_falha_motor(rotacao_rpm: float = None, vibracao_mm_s: float = None, temperatura_c: float = None,
                       corrente_a: float = None, ativo: str = None, timestamp: str = None) -> dict:
    """
    Dois modos:
      * ativo MTR + timestamp: usa a janela real das 5 últimas leituras do motor.db (features completas);
      * valores avulsos: aproxima mean5 pelo valor pontual e std5 por 0 (mesma simplificação da Sprint 2).
    """
    a = _modelo_falhas()
    modelo, cols, labels = a["modelo"], a["feature_cols"], a["label_map"]
    sensores = a["sensor_cols"]
    modo = "valores_avulsos"
    if ativo in config.IDS_MOTORES and timestamp:
        df = _leituras_mtr()
        df = df[(df["ativo"] == ativo) & (df["timestamp"] <= pd.Timestamp(timestamp))].tail(5)
        if df.empty:
            return {"erro": "Sem leituras do motor até o instante informado.", "fontes": []}
        linha = {s: float(df[s].iloc[-1]) for s in sensores}
        for s in sensores:
            linha[f"{s}_mean5"] = float(df[s].mean())
            linha[f"{s}_std5"] = float(df[s].std(ddof=1)) if len(df) > 1 else 0.0
        linha["fab_enc"] = int(a["le_fabricante"].transform([df["fabricante"].iloc[-1]])[0])
        linha["mod_enc"] = int(a["le_modelo"].transform([df["modelo"].iloc[-1]])[0])
        real = int(df["falha"].iloc[-1])
        modo = "janela_real_motor_db"
    else:
        vals = dict(rotacao_rpm=rotacao_rpm, vibracao_mm_s=vibracao_mm_s, temperatura_c=temperatura_c,
                    corrente_a=corrente_a)
        if any(v is None for v in vals.values()):
            return {"erro": "Informe rotação, vibração, temperatura e corrente.", "fontes": []}
        linha = dict(vals)
        for s in sensores:
            linha[f"{s}_mean5"] = vals[s]
            linha[f"{s}_std5"] = 0.0
        linha["fab_enc"] = linha["mod_enc"] = 0
        real = None
    x = pd.DataFrame([[linha[c] for c in cols]], columns=cols).values
    proba = modelo.predict_proba(x)[0]
    pred = int(np.argmax(proba))
    out = {"modo": modo, "diagnostico": labels[pred], "confianca": round(float(proba[pred]), 3),
           "probabilidades": {labels[i]: round(float(p), 3) for i, p in enumerate(proba)},
           "entrada": {s: round(linha[s], 2) for s in sensores},
           "aviso": "Modelo treinado em dados SINTÉTICOS (Sprint 2); F1-Macro 0,955 no teste.",
           "fontes": ["sprint2/modelo_falhas.joblib"]}
    if real is not None:
        out["rotulo_real_no_banco"] = labels[real]
        out["fontes"].append("sprint2/motor.db")
    return out


# ─── Ferramenta 5: detector de anomalias da Sprint 3 ─────────────────────────
def avaliar_anomalia_sensor(p1_velocidade, p1_aceleracao, p1_temperatura,
                            p2_velocidade, p2_aceleracao, p2_temperatura) -> dict:
    """Mesma lógica do agente_manutencao_v2.py (janelas aproximadas pelo valor pontual)."""
    import torch
    iso, ae, limiar = _modelos_anomalia()
    vals = dict(p1_velocidade=p1_velocidade, p1_aceleracao=p1_aceleracao, p1_temperatura=p1_temperatura,
                p2_velocidade=p2_velocidade, p2_aceleracao=p2_aceleracao, p2_temperatura=p2_temperatura)
    running = int(p1_velocidade > iso["thresh_running"] or p2_velocidade > iso["thresh_running"])
    estado = "running" if running else "idle"
    extra = {"diff_vel": p1_velocidade - p2_velocidade, "diff_temp": p1_temperatura - p2_temperatura,
             "diff_acel": p1_aceleracao - p2_aceleracao, "running": running, "dt_seg": 1.0}
    x = np.zeros((1, len(iso["feature_cols"])))
    for i, c in enumerate(iso["feature_cols"]):
        if c in vals:
            x[0, i] = vals[c]
        elif c.endswith("_mean5"):
            x[0, i] = vals[c.replace("_mean5", "")]
        elif c in extra:
            x[0, i] = extra[c]
    xs = iso["scaler"].transform(x)
    score_iso = float(-iso["modelo"].decision_function(xs)[0])
    flag_iso = bool(iso["modelo"].predict(xs)[0] == -1)
    with torch.no_grad():
        t = torch.tensor(xs, dtype=torch.float32)
        erro = float(torch.mean((ae(t) - t) ** 2))
    flag_ae = erro > limiar
    base = iso["baseline_operacional"][estado]
    z = {c: round((v - base[c]["media"]) / (base[c]["desvio_padrao"] or 1e-6), 2) for c, v in vals.items()}
    n = int(flag_iso) + int(flag_ae)
    return {"estado_operacional": "operação" if running else "repouso",
            "score_isolation_forest": round(score_iso, 4), "sinalizado_isolation_forest": flag_iso,
            "erro_autoencoder": round(erro, 4), "limiar_autoencoder": round(float(limiar), 4),
            "sinalizado_autoencoder": bool(flag_ae),
            "severidade": ["BAIXA", "MODERADA", "ALTA"][n],
            "concordancia": f"{n} de 2 modelos sinalizaram anomalia",
            "zscores_baseline": z, "sensores_fora_baseline": [c for c, v in z.items() if abs(v) > 3],
            "aviso": "Score de desvio estatístico, não diagnóstico de causa raiz (sem rótulos de falha).",
            "fontes": ["sprint3/modelo_anomalias_isoforest.joblib", "sprint3/modelo_autoencoder.pt",
                       "sprint3/baseline_operacional.json"]}


# ─── Ferramenta 6: resumo de anomalias por período (ativo Forzy) ─────────────
def resumo_anomalias(ativo: str, inicio: str = None, fim: str = None, ciclo: int = None) -> dict:
    if ativo != config.ID_FORZY:
        return {"erro": "Scores de anomalia só existem para o ativo FZ-ATV-01 (dados reais).",
                "fontes": []}
    df = _filtrar_periodo(_leituras_fz(), inicio, fim)
    if ciclo:
        df = df[df["ciclo"] == ciclo]
    if df.empty:
        return {"ativo": ativo, "sem_dados": True, "cobertura_disponivel": cobertura(ativo), "fontes": []}
    ambos = df[(df["flag_isoforest"] == 1) & (df["flag_autoencoder"] == 1)]
    por_ciclo = (df[df["ciclo"].notna()].groupby("ciclo")
                 .agg(pct_ae=("flag_autoencoder", "mean"), pct_iso=("flag_isoforest", "mean"),
                      erro_ae=("score_autoencoder", "mean")).round(3).reset_index())
    return {"ativo": ativo, "n_leituras": int(len(df)),
            "periodo": [str(df["timestamp"].min())[:19], str(df["timestamp"].max())[:19]],
            "pct_sinalizado_isolation_forest": round(float(100 * df["flag_isoforest"].mean()), 1),
            "pct_sinalizado_autoencoder": round(float(100 * df["flag_autoencoder"].mean()), 1),
            "pct_fora_baseline_3sigma": round(float(100 * df["flag_baseline"].mean()), 1),
            "leituras_sinalizadas_pelos_dois": int(len(ambos)),
            "por_ciclo": por_ciclo.to_dict("records"),
            "fontes": ["sprint3/scores_anomalias.csv"]}


# ─── Ferramenta 7: busca na documentação (RAG) ───────────────────────────────
def buscar_documentos(consulta: str, ativo=None, inicio: str = None, fim: str = None, k: int = None,
                      tipos: list = None) -> dict:
    """tipos: documento | evento_falha | ciclo_operacional | ordem_servico (padrão: todos)."""
    res = recuperador.buscar(consulta, ativo=ativo, inicio=inicio, fim=fim, k=k, tipos=tipos)
    return {"consulta": consulta, "filtros": {"ativo": ativo, "inicio": inicio, "fim": fim},
            "trechos": res, "fontes": [f"{r['doc_id']} — {r['titulo']} ({r['secao']})" for r in res]}


FUNCOES = {f.__name__: f for f in (consultar_leituras, listar_eventos, historico_manutencao,
                                    prever_falha_motor, avaliar_anomalia_sensor, resumo_anomalias,
                                    buscar_documentos)}


def executar(nome: str, argumentos: dict) -> dict:
    try:
        return FUNCOES[nome](**argumentos)
    except KeyError:
        return {"erro": f"Ferramenta '{nome}' inexistente.", "fontes": []}
    except Exception as e:  # erro da ferramenta é devolvido ao LLM em vez de derrubar a conversa
        return {"erro": f"{type(e).__name__}: {e}", "fontes": []}


def para_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
