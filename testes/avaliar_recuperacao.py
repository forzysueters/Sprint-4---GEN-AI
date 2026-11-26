"""
avaliar_recuperacao.py — Avaliação quantitativa da etapa de recuperação (RAG).

Conjunto de 24 perguntas rotuladas manualmente pela equipe com os documentos/registros
relevantes. Compara três variantes do recuperador (palavras, caracteres, híbrido) e o
efeito do filtro por ativo. Métricas: Hit@1, Hit@3 e MRR@5.

Uso:
    python -m testes.avaliar_recuperacao
"""
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rag import recuperador
from rag.texto import normalizar

SAIDA = Path(__file__).resolve().parent.parent / "resultados"

# (pergunta, ativo para filtro, prefixos de ids relevantes)
GOLD = [
    ("quais os limites de vibração para base rígida", None, ["DOC-01"]),
    ("o que significa zona D de severidade", None, ["DOC-01"]),
    ("vibração alta com temperatura normal, o que pode ser", None, ["DOC-02"]),
    ("como fazer balanceamento do rotor", None, ["DOC-02"]),
    ("temperatura e corrente subindo juntas no motor", None, ["DOC-03"]),
    ("aletas sujas e ventilação obstruída", None, ["DOC-03"]),
    ("aceleração em g aumentando no mancal", None, ["DOC-04"]),
    ("ruído metálico e troca de rolamento", None, ["DOC-04"]),
    ("quais sensores estão instalados nas portas do IO-Link", "FZ-ATV-01", ["DOC-05"]),
    ("qual o período de dados disponível do ativo da Forzy", "FZ-ATV-01", ["DOC-05"]),
    ("o isolation forest e o autoencoder discordam, por quê", None, ["DOC-06"]),
    ("o classificador da sprint 2 serve para o ativo real", None, ["DOC-06"]),
    ("porta 2 mais quente que a porta 1 fora do normal", "FZ-ATV-01", ["DOC-07"]),
    ("diferença de temperatura entre os mancais", "FZ-ATV-01", ["DOC-07"]),
    ("posso continuar operando com alarme ativo", None, ["DOC-08"]),
    ("procedimento de bloqueio e etiquetagem antes da manutenção", None, ["DOC-08"]),
    ("qual o fabricante e a potência do motor", "MTR-05", ["DOC-09§Motor MTR-05"]),
    ("falha registrada de superaquecimento", "MTR-07", ["EVT-MTR-07"]),
    ("eventos de falha do motor", "MTR-12", ["EVT-MTR-12"]),
    ("ordem de serviço de balanceamento", "MTR-03", ["OS-20230005"]),
    ("histórico de manutenção preventiva lubrificação", "MTR-03", ["OS-20230033"]),
    ("ciclo de operação mais longo com temperatura alta", "FZ-ATV-01", ["CIC-6"]),
    ("percentual de leituras sinalizadas no ciclo 6", "FZ-ATV-01", ["CIC-6"]),
    ("houve histórico de manutenção do ativo da Forzy", "FZ-ATV-01", ["DOC-05§Histórico"]),
]


def ranking(consulta, modo, ativo, tipo_doc=None):
    idx = recuperador._indice()
    q = normalizar(consulta)
    s_pal = (idx["mat_pal"] @ idx["vec_pal"].transform([q]).T).toarray().ravel()
    s_car = (idx["mat_car"] @ idx["vec_car"].transform([q]).T).toarray().ravel()
    s = {"palavras": s_pal, "caracteres": s_car,
         "hibrido": recuperador.PESO_PALAVRAS * s_pal + recuperador.PESO_CARACTERES * s_car}[modo]
    ids = []
    for i in np.argsort(-s):
        c = idx["chunks"][i]
        if ativo and not recuperador._ativo_ok(c, ativo):
            continue
        if tipo_doc is not None and (c["tipo_fonte"] == "documento") != tipo_doc:
            continue
        ids.append(c["id"])
        if len(ids) == 5:
            break
    return ids


def metricas(modo, usar_filtro, roteamento=False):
    h1 = h3 = mrr = 0
    detalhes = []
    for q, ativo, rel in GOLD:
        # roteamento: como no assistente, documentos e registros são buscados separadamente
        tipo_doc = rel[0].startswith("DOC") if roteamento else None
        ids = ranking(q, modo, ativo if usar_filtro else None, tipo_doc)
        pos = next((i + 1 for i, x in enumerate(ids) if any(x.startswith(r) for r in rel)), None)
        h1 += pos == 1
        h3 += pos is not None and pos <= 3
        mrr += 1 / pos if pos else 0
        detalhes.append({"pergunta": q, "ativo": ativo, "relevante": rel, "top5": ids, "posicao": pos})
    n = len(GOLD)
    return {"hit@1": round(h1 / n, 3), "hit@3": round(h3 / n, 3), "mrr@5": round(mrr / n, 3)}, detalhes


def main():
    SAIDA.mkdir(exist_ok=True)
    tabela, todos = {}, {}
    for modo in ("palavras", "caracteres", "hibrido"):
        for filtro in (False, True):
            nome = f"{modo}{' + filtro' if filtro else ''}"
            tabela[nome], todos[nome] = metricas(modo, filtro)
            print(f"{nome:22s} {tabela[nome]}")
    nome = "hibrido + filtro + tipo"
    tabela[nome], todos[nome] = metricas("hibrido", True, roteamento=True)
    print(f"{nome:22s} {tabela[nome]}")
    (SAIDA / "avaliacao_recuperacao.json").write_text(
        json.dumps({"metricas": tabela, "detalhes_hibrido_filtro": todos["hibrido + filtro"],
                    "detalhes_hibrido_filtro_tipo": todos["hibrido + filtro + tipo"]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    erros = [d for d in todos["hibrido + filtro"] if d["posicao"] != 1]
    print(f"\nPerguntas fora do top-1 (híbrido + filtro): {len(erros)}")
    for d in erros:
        print(f"  - {d['pergunta']!r}: posição {d['posicao']} | top3 {d['top5'][:3]}")

    # Gráfico
    nomes = list(tabela)
    x = np.arange(len(nomes))
    fig, ax = plt.subplots(figsize=(10, 3.6))
    for i, (m, cor) in enumerate((("hit@1", "#2a6f97"), ("hit@3", "#61a5c2"), ("mrr@5", "#e09f3e"))):
        v = [tabela[n][m] for n in nomes]
        b = ax.bar(x + (i - 1) * 0.26, v, 0.26, label=m.upper(), color=cor)
        ax.bar_label(b, fmt="%.2f", fontsize=7, padding=1)
    ax.set_xticks(x, [n.replace(" + ", "\n+ ") for n in nomes], fontsize=7.5)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("métrica")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper left")
    ax.set_title("Recuperação: variantes do recuperador × filtro por ativo (24 perguntas)", fontsize=10)
    fig.tight_layout()
    fig.savefig(SAIDA / "grafico_recuperacao.png", dpi=180)
    print("Gráfico salvo em resultados/grafico_recuperacao.png")


if __name__ == "__main__":
    main()
