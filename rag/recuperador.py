"""Recuperador híbrido (TF-IDF de palavras + TF-IDF de caracteres) com filtros por ativo e período."""
from functools import lru_cache

import joblib
import numpy as np

from rag import config
from rag.texto import normalizar

# Pesos escolhidos por busca em grade no conjunto de avaliação (testes/avaliar_recuperacao.py)
PESO_PALAVRAS = 0.3
PESO_CARACTERES = 0.7


@lru_cache(maxsize=1)
def _indice():
    if not config.INDICE.exists():
        raise FileNotFoundError("Índice não encontrado. Execute: python -m rag.preparar_base")
    return joblib.load(config.INDICE)


def _sobrepoe(c, inicio, fim):
    """Trechos sem período (documentos) sempre passam; registros precisam sobrepor o intervalo."""
    if c["inicio"] is None or (inicio is None and fim is None):
        return True
    ini_c, fim_c = c["inicio"][:19], (c["fim"] or c["inicio"])[:19]
    return not ((fim and ini_c > fim[:19]) or (inicio and fim_c < inicio[:19]))


def _ativo_ok(c, ativo):
    if ativo is None:
        return True
    alvo = ativo if isinstance(ativo, list) else [ativo]
    return "todos" in c["ativos"] or any(a in c["ativos"] for a in alvo)


def buscar(consulta: str, ativo=None, inicio=None, fim=None, k=None, tipos=None, min_score=None):
    """Retorna os k trechos mais similares que respeitam os filtros, com score em [0, 1]."""
    idx = _indice()
    k = k or config.TOP_K
    min_score = config.MIN_SCORE if min_score is None else min_score
    q = normalizar(consulta)
    s_pal = (idx["mat_pal"] @ idx["vec_pal"].transform([q]).T).toarray().ravel()
    s_car = (idx["mat_car"] @ idx["vec_car"].transform([q]).T).toarray().ravel()
    scores = PESO_PALAVRAS * s_pal + PESO_CARACTERES * s_car

    resultados = []
    for i in np.argsort(-scores):
        c = idx["chunks"][i]
        if scores[i] < min_score:
            break
        if tipos and c["tipo_fonte"] not in tipos:
            continue
        if not (_ativo_ok(c, ativo) and _sobrepoe(c, inicio, fim)):
            continue
        resultados.append({**{key: c[key] for key in ("id", "tipo_fonte", "doc_id", "titulo", "secao",
                                                        "texto", "ativos", "inicio", "fim", "origem", "arquivo")},
                           "score": round(float(scores[i]), 3)})
        if len(resultados) >= k:
            break
    return resultados
