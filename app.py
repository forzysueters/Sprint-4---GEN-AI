"""
app.py — Interface web (Streamlit) do Assistente de Manutenção Forzy.

Uso:
    streamlit run app.py
"""
import pandas as pd
import streamlit as st

from rag import config
from rag.assistente import Assistente
from rag.ferramentas import _leituras_fz, _leituras_mtr

st.set_page_config(page_title="Assistente de Manutenção Forzy", page_icon="🔧", layout="wide")

if "assistente" not in st.session_state:
    st.session_state.assistente = Assistente()
    st.session_state.mensagens = []
ass: Assistente = st.session_state.assistente

# ─── Barra lateral: filtros e status ─────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    opcoes = ["(detectar na pergunta)", config.ID_FORZY] + config.IDS_MOTORES
    sel = st.selectbox("Ativo", opcoes, help="Usado quando a pergunta não cita um ativo.")
    ass.contexto["ativo"] = None if sel.startswith("(") else sel
    st.caption("Período: escreva as datas na pergunta (dd/mm/aaaa ou aaaa-mm-dd).")
    st.divider()
    st.markdown(f"**Modo de geração:** `{ass.modo}`")
    if ass.modo == "offline":
        st.caption("Sem ANTHROPIC_API_KEY: respostas montadas por regras a partir das mesmas ferramentas e fontes.")
    st.markdown("**Ativos**\n- `FZ-ATV-01` — dados reais Forzy\n- `MTR-01…20` — base sintética")
    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.session_state.assistente = Assistente()
        st.rerun()

aba_chat, aba_painel = st.tabs(["💬 Assistente", "📈 Painel do ativo"])

# ─── Chat ────────────────────────────────────────────────────────────────────
with aba_chat:
    st.title("Assistente de Manutenção Forzy")
    st.caption("Consulta sensores, falhas, anomalias, histórico de manutenção e procedimentos técnicos, "
               "sempre com as fontes consultadas. O assistente não autoriza intervenções.")
    for m in st.session_state.mensagens:
        with st.chat_message(m["papel"]):
            st.markdown(m["texto"])
            if m.get("fontes"):
                with st.expander(f"Fontes consultadas ({len(m['fontes'])})"):
                    for i, f in enumerate(m["fontes"], 1):
                        st.markdown(f"{i}. {f}")
            if m.get("ferramentas"):
                with st.expander("Ferramentas acionadas"):
                    st.json(m["ferramentas"])

    pergunta = st.chat_input("Ex.: O que aconteceu no ciclo 6 do FZ-ATV-01?")
    if pergunta:
        st.session_state.mensagens.append({"papel": "user", "texto": pergunta})
        with st.spinner("Consultando dados, modelos e documentação…"):
            r = ass.responder(pergunta)
        rotulo = {"esclarecimento": "❓ ", "sem_informacao": "ℹ️ "}.get(r.tipo, "")
        texto = rotulo + r.texto.replace("\n", "  \n")
        if r.escalonar:
            texto = "⚠️ " + texto
        st.session_state.mensagens.append({"papel": "assistant", "texto": texto, "fontes": r.fontes,
                                           "ferramentas": r.ferramentas})
        st.rerun()

# ─── Painel ──────────────────────────────────────────────────────────────────
with aba_painel:
    ativo = ass.contexto["ativo"] or config.ID_FORZY
    st.subheader(f"Série histórica — {ativo}")
    if ativo == config.ID_FORZY:
        df = _leituras_fz().set_index("timestamp")
        st.line_chart(df[["p1_velocidade", "p2_velocidade"]], height=220)
        st.line_chart(df[["p1_temperatura", "p2_temperatura"]], height=220)
        st.markdown("**Erro de reconstrução do Autoencoder** (acima do limiar = leitura sinalizada)")
        st.line_chart(df[["score_autoencoder"]], height=180)
    else:
        df = _leituras_mtr()
        df = df[df["ativo"] == ativo].set_index("timestamp")
        st.line_chart(df[["vibracao_mm_s", "corrente_a"]], height=220)
        st.line_chart(df[["temperatura_c"]], height=220)
        st.dataframe(pd.read_csv(config.DIR_GERADO / "eventos_falha_mtr.csv").query("ativo == @ativo"),
                     hide_index=True)
