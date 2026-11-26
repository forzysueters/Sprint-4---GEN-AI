"""
cenarios.py — Testes funcionais ponta a ponta do assistente (modo offline, reprodutível).

Cada cenário define entrada, resultado esperado e verificações automáticas.
Saídas: resultados/cenarios.json e resultados/cenarios_log.md

Uso:
    python -m testes.cenarios
"""
import json
import time
import warnings
from pathlib import Path

from rag.assistente import Assistente

warnings.filterwarnings("ignore")
SAIDA = Path(__file__).resolve().parent.parent / "resultados"

CENARIOS = [
    {"id": "C1", "categoria": "Falha ou anomalia (obrigatório)",
     "turnos": ["O que aconteceu no ciclo 6 do FZ-ATV-01? Houve anomalia?"],
     "esperado": "Identificar o Ciclo 6 (17,4 min), mostrar o percentual de leituras sinalizadas por cada modelo, "
                 "explicar a divergência Autoencoder × Isolation Forest e citar documentação de interpretação.",
     "checks": {"tipo": "resposta", "ferramentas": ["resumo_anomalias", "buscar_documentos"],
                "contem": ["Ciclo 6", "53.5%", "Isolation Forest"], "fontes_contem": ["scores_anomalias.csv", "DOC-06"]}},
    {"id": "C2", "categoria": "Dados operacionais + documentação técnica (obrigatório)",
     "turnos": ["Quais falhas o MTR-07 apresentou e como devo investigar?"],
     "esperado": "Listar o evento de superaquecimento do MTR-07 com valores máximos e trazer verificações do "
                 "procedimento de superaquecimento (DOC-03), citando as fontes.",
     "checks": {"tipo": "resposta", "ferramentas": ["listar_eventos", "buscar_documentos"],
                "contem": ["Superaquecimento", "113.4"], "fontes_contem": ["eventos_falha_mtr.csv", "DOC-03"]}},
    {"id": "C3", "categoria": "Informação insuficiente (obrigatório)",
     "turnos": ["Quando foi feita a última troca de rolamento do FZ-ATV-01?"],
     "esperado": "Informar que não há registros de manutenção para o ativo e não inventar data.",
     "checks": {"tipo": "sem_informacao", "ferramentas": ["historico_manutencao"],
                "contem": ["Não há registros de manutenção"], "nao_contem": ["OS-2023"], "fontes_contem": ["DOC-05"]}},
    {"id": "C4", "categoria": "Pergunta ambígua + continuação",
     "turnos": ["Como está o motor?", "É o MTR-12. Quais foram as leituras e as falhas dele?"],
     "esperado": "1º turno: pedir o ativo listando opções, sem consultar dados. 2º turno: responder com leituras e "
                 "eventos do MTR-12.",
     "checks": {"tipo_por_turno": ["esclarecimento", "resposta"], "ferramentas": ["consultar_leituras", "listar_eventos"],
                "contem": ["MTR-12"]}},
    {"id": "C5", "categoria": "Diagnóstico por leitura + situação que exige profissional",
     "turnos": ["Motor com vibração 8.2 mm/s, temperatura 92 C, corrente 15.5 A, rotação 1720 RPM. "
                "Posso continuar operando?"],
     "esperado": "Classificar com o modelo da Sprint 2, sinalizar baixa confiança e recomendar avaliação do "
                 "profissional responsável (DOC-08), sem autorizar a operação.",
     "checks": {"tipo": "resposta", "ferramentas": ["prever_falha_motor"], "escalonar": True,
                "contem": ["ATENÇÃO", "responsável técnico"], "fontes_contem": ["DOC-08"]}},
    {"id": "C6", "categoria": "Filtro de período fora da cobertura",
     "turnos": ["Como estavam as leituras do FZ-ATV-01 em 10/03/2025?"],
     "esperado": "Informar que não há dados no período e qual é a cobertura disponível.",
     "checks": {"tipo": "sem_informacao", "contem": ["2026-05-19 11:46:10"]}},
    {"id": "C7", "categoria": "Avaliação de leitura do ativo real (padrão do Ciclo 6)",
     "turnos": ["Leitura do FZ-ATV-01: P1 6,9 mm/s 0,50 g 38 °C; P2 7,1 mm/s 0,52 g 42 °C. Isso é anômalo?"],
     "esperado": "Severidade MODERADA (Autoencoder sinaliza, Isolation Forest não), como na Sprint 3, e indicar o "
                 "procedimento de assimetria térmica.",
     "checks": {"tipo": "resposta", "ferramentas": ["avaliar_anomalia_sensor"], "contem": ["MODERADA"],
                "fontes_contem": ["DOC-07"]}},
    {"id": "C8", "categoria": "Diagnóstico com janela real do banco (integração Sprint 2)",
     "turnos": ["Qual o diagnóstico do MTR-07 em 2023-01-04 06:00?"],
     "esperado": "Usar as 5 últimas leituras reais do motor.db, prever Superaquecimento e comparar com o rótulo.",
     "checks": {"tipo": "resposta", "ferramentas": ["prever_falha_motor"],
                "contem": ["Superaquecimento", "Rótulo registrado"]}},
    {"id": "C9", "categoria": "Histórico de manutenção",
     "turnos": ["Qual o histórico de manutenção do MTR-03?"],
     "esperado": "Listar as ordens de serviço do MTR-03, identificadas como SIMULADAS.",
     "checks": {"tipo": "resposta", "ferramentas": ["historico_manutencao"], "contem": ["SIMULADOS", "OS-2023"]}},
    {"id": "C10", "categoria": "Procedimento técnico sem ativo",
     "turnos": ["Quais são os limites de vibração da ISO 10816 para base rígida?"],
     "esperado": "Responder com a tabela de zonas do DOC-01 sem pedir ativo.",
     "checks": {"tipo": "resposta", "contem": ["1,4 mm/s"], "fontes_contem": ["DOC-01"]}},
    {"id": "C11", "categoria": "Valor isolado (ambiguidade de contexto)",
     "turnos": ["Uma vibração de 5,2 mm/s é problema?"],
     "esperado": "Explicar a zona para base rígida e flexível e pedir ativo e demais leituras.",
     "checks": {"tipo": "esclarecimento", "contem": ["zona D", "zona C"]}},
    {"id": "C12", "categoria": "Fora do escopo",
     "turnos": ["Qual o preço do rolamento 6205 no fornecedor?"],
     "esperado": "Informar que a base não contém dados comerciais.",
     "checks": {"tipo": "sem_informacao", "contem": ["não contém dados comerciais"]}},
    {"id": "C13", "categoria": "Comparação entre ativos (limitação conhecida)",
     "turnos": ["Compare as falhas do MTR-01 e do MTR-02."],
     "esperado": "Comparação multiativo não implementada: o assistente deve pedir uma pergunta por ativo.",
     "checks": {"tipo": "esclarecimento"}},
]


def verificar(cen, respostas):
    ch, ult = cen["checks"], respostas[-1]
    falhas = []
    if "tipo" in ch and ult.tipo != ch["tipo"]:
        falhas.append(f"tipo={ult.tipo} (esperado {ch['tipo']})")
    if "tipo_por_turno" in ch:
        got = [r.tipo for r in respostas]
        if got != ch["tipo_por_turno"]:
            falhas.append(f"tipos por turno={got}")
    usadas = {f["ferramenta"] for r in respostas for f in r.ferramentas}
    for f in ch.get("ferramentas", []):
        if f not in usadas:
            falhas.append(f"ferramenta ausente: {f}")
    for t in ch.get("contem", []):
        if t not in ult.texto:
            falhas.append(f"texto não contém '{t}'")
    for t in ch.get("nao_contem", []):
        if t in ult.texto:
            falhas.append(f"texto contém '{t}'")
    fontes = " ".join(ult.fontes)
    for t in ch.get("fontes_contem", []):
        if t not in fontes:
            falhas.append(f"fonte ausente: {t}")
    if ch.get("escalonar") and not ult.escalonar:
        falhas.append("não escalonou para profissional responsável")
    return falhas


def main():
    SAIDA.mkdir(exist_ok=True)
    resultados, log = [], ["# Registro de execução — cenários de teste (modo offline)\n"]
    for cen in CENARIOS:
        ass = Assistente(modo="offline")
        respostas, tempos = [], []
        for t in cen["turnos"]:
            t0 = time.perf_counter()
            respostas.append(ass.responder(t))
            tempos.append(round((time.perf_counter() - t0) * 1000, 1))
        falhas = verificar(cen, respostas)
        status = "APROVADO" if not falhas else "REPROVADO"
        resultados.append({"id": cen["id"], "categoria": cen["categoria"], "turnos": cen["turnos"],
                           "esperado": cen["esperado"], "status": status, "falhas": falhas, "tempo_ms": tempos,
                           "respostas": [{"tipo": r.tipo, "texto": r.texto, "fontes": r.fontes,
                                          "ferramentas": r.ferramentas, "escalonar": r.escalonar} for r in respostas]})
        log.append(f"## {cen['id']} — {cen['categoria']}  [{status}]\n")
        for t, r, ms in zip(cen["turnos"], respostas, tempos):
            log.append(f"**Entrada:** {t}\n\n**Saída ({r.tipo}, {ms} ms):**\n\n```\n{r.formatada()}\n```\n")
            log.append("Ferramentas: " + "; ".join(f"`{f['ferramenta']}`" for f in r.ferramentas) + "\n")
        if falhas:
            log.append("Falhas: " + "; ".join(falhas) + "\n")
        print(f"{cen['id']:4s} {status:10s} {max(tempos):7.1f} ms  {cen['categoria']}" +
              (f"  -> {falhas}" if falhas else ""))
    (SAIDA / "cenarios.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=str),
                                         encoding="utf-8")
    (SAIDA / "cenarios_log.md").write_text("\n".join(log), encoding="utf-8")
    ok = sum(r["status"] == "APROVADO" for r in resultados)
    print(f"\n{ok}/{len(resultados)} cenários aprovados. Log em resultados/cenarios_log.md")


if __name__ == "__main__":
    main()
