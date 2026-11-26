"""
preparar_base.py — Prepara e indexa a base de conhecimento do RAG.

Etapas:
  1. Extrai eventos de falha dos motores MTR (motor.db, Sprint 2).
  2. Extrai os ciclos operacionais do ativo FZ-ATV-01 com os scores de anomalia (Sprint 3).
  3. Gera o histórico de manutenção SIMULADO dos motores MTR (seed fixa).
  4. Gera a ficha técnica dos motores MTR (DOC-09) a partir do cadastro do motor.db.
  5. Divide documentos e registros em trechos (chunks) com metadados de ativo e período.
  6. Ajusta os vetorizadores TF-IDF e salva o índice em indice/indice_rag.joblib.

Uso:
    python -m rag.preparar_base
"""
import re
import sqlite3

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from rag import config
from rag.texto import normalizar

SEED = 42


# ─── 1. Eventos de falha dos motores MTR ─────────────────────────────────────
def extrair_eventos_mtr() -> pd.DataFrame:
    con = sqlite3.connect(config.MOTOR_DB)
    lt = pd.read_sql("SELECT * FROM leituras ORDER BY motor_id, timestamp", con)
    tipos = dict(pd.read_sql("SELECT id, nome FROM tipos_falha", con).values)
    con.close()
    eventos = []
    for mid, g in lt.groupby("motor_id"):
        g = g.reset_index(drop=True)
        bloco = (g["falha"] != g["falha"].shift()).cumsum()
        for _, seg in g.groupby(bloco):
            tipo = int(seg["falha"].iloc[0])
            if tipo == 0:
                continue
            eventos.append({
                "ativo": f"MTR-{mid:02d}",
                "inicio": seg["timestamp"].iloc[0],
                "fim": seg["timestamp"].iloc[-1],
                "tipo_falha": tipos[tipo],
                "n_leituras": len(seg),
                "vib_max": round(seg["vibracao_mm_s"].max(), 2),
                "temp_max": round(seg["temperatura_c"].max(), 1),
                "corrente_max": round(seg["corrente_a"].max(), 2),
                "rpm_min": round(seg["rotacao_rpm"].min(), 0),
            })
    return pd.DataFrame(eventos)


# ─── 2. Ciclos operacionais do ativo Forzy ───────────────────────────────────
def extrair_ciclos_fz() -> pd.DataFrame:
    s = pd.read_csv(config.SCORES_FZ, parse_dates=["timestamp"])
    linhas = []
    n = 0
    for seg_id, g in s.groupby("cycle_id"):
        if g["running"].iloc[0] != 1:
            continue
        n += 1
        dur = (g["timestamp"].max() - g["timestamp"].min()).total_seconds() / 60
        linhas.append({
            "ativo": config.ID_FORZY,
            "ciclo": n,
            "inicio": g["timestamp"].min().isoformat(timespec="seconds"),
            "fim": g["timestamp"].max().isoformat(timespec="seconds"),
            "duracao_min": round(dur, 1),
            "n_leituras": len(g),
            "vel_max_p1": g["p1_velocidade"].max(), "vel_max_p2": g["p2_velocidade"].max(),
            "temp_max_p1": g["p1_temperatura"].max(), "temp_max_p2": g["p2_temperatura"].max(),
            "pct_flag_iso": round(100 * g["flag_isoforest"].mean(), 1),
            "pct_flag_ae": round(100 * g["flag_autoencoder"].mean(), 1),
            "erro_ae_medio": round(g["score_autoencoder"].mean(), 3),
        })
    return pd.DataFrame(linhas)


# ─── 3. Histórico de manutenção SIMULADO ─────────────────────────────────────
ACOES = {
    "desbalanceamento": ("Limpeza do rotor e balanceamento dinâmico em campo", "DOC-02"),
    "superaquecimento": ("Limpeza das aletas, verificação de corrente nas 3 fases e reaperto de bornes", "DOC-03"),
    "falha mecanica": ("Substituição do rolamento do lado acionado e realinhamento do acoplamento", "DOC-04"),
}


def gerar_historico_os(eventos: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    os_ = []
    for i, ev in eventos.iterrows():
        abertura = pd.Timestamp(ev["fim"]) + pd.Timedelta(hours=int(rng.integers(1, 7)))
        acao, doc = ACOES[normalizar(ev["tipo_falha"])]
        os_.append({
            "os_id": f"OS-{2023}{len(os_) + 1:04d}",
            "ativo": ev["ativo"], "tipo": "corretiva",
            "data_abertura": abertura.isoformat(),
            "data_conclusao": (abertura + pd.Timedelta(hours=int(rng.integers(2, 9)))).isoformat(),
            "sintoma": f"Alarme de {ev['tipo_falha'].lower()} (vibração máx. {ev['vib_max']} mm/s, "
                       f"temperatura máx. {ev['temp_max']} °C)",
            "acao_executada": acao, "procedimento": doc,
            "responsavel": f"Técnico {chr(65 + int(rng.integers(0, 4)))}",
            "origem": "SIMULADO",
        })
    # Preventivas de lubrificação em metade dos motores
    for mid in rng.choice(range(1, 21), size=10, replace=False):
        data = pd.Timestamp("2023-01-01") + pd.Timedelta(hours=int(rng.integers(12, 240)))
        os_.append({
            "os_id": f"OS-{2023}{len(os_) + 1:04d}", "ativo": f"MTR-{mid:02d}", "tipo": "preventiva",
            "data_abertura": data.isoformat(), "data_conclusao": (data + pd.Timedelta(hours=1)).isoformat(),
            "sintoma": "Rotina de lubrificação programada", "acao_executada": "Relubrificação dos mancais",
            "procedimento": "DOC-04", "responsavel": f"Técnico {chr(65 + int(rng.integers(0, 4)))}",
            "origem": "SIMULADO",
        })
    return pd.DataFrame(os_).sort_values(["ativo", "data_abertura"]).reset_index(drop=True)


# ─── 4. Ficha técnica dos motores MTR ────────────────────────────────────────
def gerar_doc_motores() -> None:
    con = sqlite3.connect(config.MOTOR_DB)
    m = pd.read_sql("SELECT * FROM motores", con)
    con.close()
    linhas = [
        "---", "id: DOC-09", "titulo: Ficha técnica dos motores MTR-01 a MTR-20 (base sintética)",
        "tipo: ficha_tecnica", "ativos: " + ",".join(config.IDS_MOTORES),
        "origem: SIMULADO — gerado automaticamente a partir da tabela motores do motor.db (Sprint 2).",
        "versao: 1.0", "---", "",
        "## Visão geral",
        "Os motores MTR-01 a MTR-20 pertencem à base sintética da Sprint 2 (motor.db, seed 42). "
        "Valores nominais: rotação ~1750 RPM, vibração ~2,5 mm/s, temperatura ~65 °C, corrente ~12 A. "
        "Período de leituras: 01/01/2023 00:00 a 11/01/2023 09:50, intervalo de 10 minutos.", "",
    ]
    for _, r in m.iterrows():
        linhas += [f"## Motor MTR-{r['id']:02d}",
                   f"Motor MTR-{r['id']:02d}: fabricante {r['fabricante']}, modelo {r['modelo']}, "
                   f"potência nominal {r['potencia_kw']} kW, data de instalação cadastrada {r['data_instalacao']}.", ""]
    (config.DIR_DOCS / "DOC-09_ficha_tecnica_motores_MTR.md").write_text("\n".join(linhas), encoding="utf-8")


# ─── 5. Chunking ─────────────────────────────────────────────────────────────
def ler_documento(caminho):
    txt = caminho.read_text(encoding="utf-8")
    _, cab, corpo = txt.split("---", 2)
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", cab, flags=re.M))
    return meta, corpo


def chunks_documentos():
    chunks = []
    for caminho in sorted(config.DIR_DOCS.glob("DOC-*.md")):
        meta, corpo = ler_documento(caminho)
        ativos = [a.strip() for a in meta["ativos"].split(",")]
        for secao in re.split(r"^## ", corpo, flags=re.M)[1:]:
            titulo_sec, _, texto = secao.partition("\n")
            texto = texto.strip()
            # Cada trecho carrega o título do documento para dar contexto à busca
            ativos_chunk = ativos
            m = re.match(r"Motor (MTR-\d{2})", titulo_sec)
            if m:
                ativos_chunk = [m.group(1)]
            chunks.append({
                "id": f"{meta['id']}§{titulo_sec.strip()}",
                "tipo_fonte": "documento", "doc_id": meta["id"], "titulo": meta["titulo"],
                "secao": titulo_sec.strip(), "texto": texto,
                "texto_busca": f"{meta['titulo']}. {titulo_sec}. {texto}",
                "ativos": ativos_chunk, "inicio": None, "fim": None,
                "origem": meta["origem"].split(" ")[0].rstrip(" —"),
                "arquivo": caminho.name,
            })
    return chunks


def chunks_registros(eventos, ciclos, historico):
    chunks = []
    for _, e in eventos.iterrows():
        t = (f"Evento de falha registrado no {e['ativo']}: {e['tipo_falha']} entre {e['inicio']} e {e['fim']} "
             f"({e['n_leituras']} leituras). Vibração máxima {e['vib_max']} mm/s, temperatura máxima "
             f"{e['temp_max']} °C, corrente máxima {e['corrente_max']} A, rotação mínima {e['rpm_min']:.0f} RPM.")
        chunks.append({"id": f"EVT-{e['ativo']}-{e['inicio']}", "tipo_fonte": "evento_falha",
                       "doc_id": "motor.db/leituras", "titulo": f"Evento de falha — {e['ativo']}",
                       "secao": e["inicio"], "texto": t, "texto_busca": t + " histórico de falhas falha registrada",
                       "ativos": [e["ativo"]], "inicio": e["inicio"], "fim": e["fim"], "origem": "SIMULADO",
                       "arquivo": "sprint2/motor.db"})
    for _, c in ciclos.iterrows():
        t = (f"Ciclo operacional {c['ciclo']} do ativo {c['ativo']}: de {c['inicio']} a {c['fim']} "
             f"({c['duracao_min']} min, {c['n_leituras']} leituras). Velocidade máxima P1/P2 "
             f"{c['vel_max_p1']}/{c['vel_max_p2']} mm/s; temperatura máxima P1/P2 {c['temp_max_p1']}/"
             f"{c['temp_max_p2']} °C. Leituras sinalizadas: Isolation Forest {c['pct_flag_iso']}%, "
             f"Autoencoder {c['pct_flag_ae']}% (erro médio {c['erro_ae_medio']}).")
        chunks.append({"id": f"CIC-{c['ciclo']}", "tipo_fonte": "ciclo_operacional",
                       "doc_id": "scores_anomalias.csv", "titulo": f"Ciclo {c['ciclo']} — {c['ativo']}",
                       "secao": f"Ciclo {c['ciclo']}", "texto": t,
                       "texto_busca": t + " anomalia ciclo operacao score", "ativos": [c["ativo"]],
                       "inicio": c["inicio"], "fim": c["fim"], "origem": "REAL",
                       "arquivo": "sprint3/scores_anomalias.csv"})
    for _, o in historico.iterrows():
        t = (f"Ordem de serviço {o['os_id']} ({o['tipo']}) do {o['ativo']}, aberta em {o['data_abertura']} e "
             f"concluída em {o['data_conclusao']}. Sintoma: {o['sintoma']}. Ação executada: "
             f"{o['acao_executada']} (procedimento {o['procedimento']}). Responsável: {o['responsavel']}.")
        chunks.append({"id": o["os_id"], "tipo_fonte": "ordem_servico", "doc_id": "historico_manutencao.csv",
                       "titulo": f"{o['os_id']} — {o['ativo']}", "secao": o["tipo"], "texto": t,
                       "texto_busca": t + " histórico de manutenção ordem de serviço intervenção",
                       "ativos": [o["ativo"]], "inicio": o["data_abertura"], "fim": o["data_conclusao"],
                       "origem": "SIMULADO", "arquivo": "conhecimento/historico_manutencao.csv"})
    return chunks


# ─── 6. Indexação ────────────────────────────────────────────────────────────
def indexar(chunks):
    corpus = [normalizar(c["texto_busca"]) for c in chunks]
    vec_pal = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    vec_car = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)
    mat_pal = vec_pal.fit_transform(corpus)
    mat_car = vec_car.fit_transform(corpus)
    config.INDICE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"chunks": chunks, "vec_pal": vec_pal, "vec_car": vec_car,
                 "mat_pal": mat_pal, "mat_car": mat_car}, config.INDICE)
    return mat_pal.shape, mat_car.shape


def main():
    config.DIR_GERADO.mkdir(parents=True, exist_ok=True)
    eventos = extrair_eventos_mtr()
    eventos.to_csv(config.DIR_GERADO / "eventos_falha_mtr.csv", index=False)
    ciclos = extrair_ciclos_fz()
    ciclos.to_csv(config.DIR_GERADO / "ciclos_fz.csv", index=False)
    historico = gerar_historico_os(eventos)
    historico.to_csv(config.HISTORICO_OS, index=False)
    gerar_doc_motores()

    chunks = chunks_documentos() + chunks_registros(eventos, ciclos, historico)
    shp_pal, shp_car = indexar(chunks)

    tipos = pd.Series([c["tipo_fonte"] for c in chunks]).value_counts()
    print("Base de conhecimento preparada")
    print(f"  Eventos de falha MTR ........ {len(eventos)}")
    print(f"  Ciclos operacionais FZ ...... {len(ciclos)}")
    print(f"  Ordens de serviço (simul.) .. {len(historico)}")
    print(f"  Trechos indexados ........... {len(chunks)}")
    for t, n in tipos.items():
        print(f"     - {t:20s} {n}")
    print(f"  Vocabulário palavras/char ... {shp_pal[1]} / {shp_car[1]}")
    print(f"  Índice salvo em {config.INDICE.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
