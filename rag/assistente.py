"""
assistente.py — Orquestrador do Assistente de Manutenção Forzy (Sprint 4).

Dois modos de geração:
  * llm     — Claude (API Anthropic) com tool use; as ferramentas incluem a busca RAG.
  * offline — pipeline determinístico (regras + templates) com as MESMAS ferramentas.
              Usado quando não há ANTHROPIC_API_KEY e nos testes reprodutíveis.

Em ambos os modos a lista de fontes é montada pelo sistema a partir do que as
ferramentas efetivamente retornaram (o LLM não consegue inventar uma fonte).
"""
import os
import re
from dataclasses import dataclass, field

from rag import config, ferramentas as fx
from rag.prompts import SYSTEM_PROMPT, TOOLS
from rag.texto import extrair_ativo, extrair_ciclo, extrair_numeros, extrair_periodo, normalizar

INTENCOES = {
    "leituras": r"leitura|sensores|como (esta|estao|se comport)|situacao|status|resum|valores medidos|"
                r"media d|maxim|temperatura atingiu|quanto",
    "eventos": r"falha|evento|alarme|ocorr|problema",
    "anomalia": r"anomal|score|desvio|incomum|ciclo|autoencoder|isolation|fora do padrao",
    "manutencao": r"manutenc|ordem de servico|\bos\b|intervenc|troca|substitu|lubrific|reparo|ultima vez",
    "procedimento": r"como (corrigir|resolver|investigar|verificar|tratar|proceder|interpret)|procediment|"
                    r"o que (fazer|verificar|devo|significa)|causa|recomend|troubleshoot|passos|zona|norma|iso|"
                    r"limite|investig|por que|porque",
    "diagnostico": r"diagnost|classific|qual (a|o) (falha|estado|condicao)",
    "fora_escopo": r"preco|custo|fornecedor|comprar|estoque|orcamento|salario|prazo de entrega",
    "seguranca": r"posso (continuar|manter|religar|liberar|operar|seguir)|continuar operando|seguro|"
                 r"desligar|parar (a|o) (maquina|equipamento|motor)",
}
EXIGE_ATIVO = {"leituras", "eventos", "anomalia", "manutencao", "diagnostico"}
REF_ESCALONAMENTO = "situações que exigem avaliação de profissional responsável segurança escalonamento"


@dataclass
class Resposta:
    texto: str
    tipo: str = "resposta"            # resposta | esclarecimento | sem_informacao
    modo: str = "offline"
    ativo: object = None
    periodo: tuple = (None, None)
    ferramentas: list = field(default_factory=list)
    fontes: list = field(default_factory=list)
    escalonar: bool = False

    def formatada(self) -> str:
        txt = self.texto.rstrip()
        if self.fontes:
            txt += "\n\nFontes consultadas:\n" + "\n".join(f"  [{i}] {f}" for i, f in enumerate(self.fontes, 1))
        return txt


class Assistente:
    def __init__(self, modo: str = None):
        modo = modo or config.USAR_LLM
        tem_chave = bool(os.getenv("ANTHROPIC_API_KEY"))
        self.modo = "llm" if (modo == "llm" or (modo == "auto" and tem_chave)) else "offline"
        self.contexto = {"ativo": None}
        self.historico_llm = []

    # ─── API pública ──────────────────────────────────────────────────────
    def responder(self, pergunta: str) -> Resposta:
        if self.modo == "llm":
            try:
                return self._responder_llm(pergunta)
            except Exception as e:  # falha de rede/chave: degrada para o modo offline
                r = self._responder_offline(pergunta)
                r.texto = f"(Modo LLM indisponível: {type(e).__name__}. Resposta gerada no modo offline.)\n\n" + r.texto
                return r
        return self._responder_offline(pergunta)

    # ─── Modo offline ─────────────────────────────────────────────────────
    def _registrar(self, r: Resposta, nome: str, args: dict, com_fontes: bool = True) -> dict:
        res = fx.executar(nome, {k: v for k, v in args.items() if v is not None})
        r.ferramentas.append({"ferramenta": nome, "argumentos": {k: v for k, v in args.items() if v is not None}})
        for f in (res.get("fontes", []) if com_fontes else []):
            if f not in r.fontes:
                r.fontes.append(f)
        return res

    def _responder_offline(self, pergunta: str) -> Resposta:
        p = normalizar(pergunta)
        intencoes = {k for k, rx in INTENCOES.items() if re.search(rx, p)}
        ativo, _ = extrair_ativo(pergunta)
        inicio, fim = extrair_periodo(pergunta)
        ciclo = extrair_ciclo(pergunta)
        nums = extrair_numeros(pergunta)
        r = Resposta(texto="", periodo=(inicio, fim))
        nota_contexto = ""

        if isinstance(ativo, list):
            return self._esclarecer(r, "A pergunta cita mais de um ativo (" + ", ".join(ativo) +
                                    "). Faça uma pergunta por ativo para que eu filtre os dados corretamente.")
        if ativo is None and self.contexto["ativo"] and intencoes & EXIGE_ATIVO and len(nums) < 4:
            ativo = self.contexto["ativo"]
            nota_contexto = f"(Considerando o ativo {ativo}, citado na pergunta anterior.)\n\n"

        if "fora_escopo" in intencoes and not (intencoes & (EXIGE_ATIVO | {"procedimento"}) - {"eventos"}):
            r.tipo = "sem_informacao"
            r.texto = ("Não tenho informações para responder a isso: a base do assistente não contém dados comerciais "
                       "(preços, fornecedores, estoque ou prazos). Ela cobre dados de sensores, resultados dos modelos, "
                       "histórico de manutenção e procedimentos técnicos. Consulte a área de suprimentos.")
            return r

        # Leituras numéricas avulsas → modelos
        quer_avaliar = len(nums) >= 4 and re.search(r"mm/s|rpm|rotac|corrente|temperatura|vibrac|porta|p1|acelera", p)
        if quer_avaliar:
            return self._avaliar_valores(r, pergunta, p, nums, ativo, intencoes)
        if 1 <= len(nums) <= 3 and re.search(r"mm/s|vibrac", p) and not ativo and not inicio:
            return self._valor_isolado(r, pergunta, nums)

        # Pergunta dependente de ativo sem ativo → esclarecimento
        if ativo is None and intencoes & EXIGE_ATIVO and "procedimento" not in intencoes:
            return self._esclarecer(r, "Para responder preciso saber de qual ativo se trata. Ativos disponíveis:\n"
                                       "  • FZ-ATV-01 — ativo real da Forzy (vibração e temperatura, 19/05/2026)\n"
                                       "  • MTR-01 a MTR-20 — motores da base sintética (01/01 a 11/01/2023)\n"
                                       "Exemplo: \"Quais falhas o MTR-07 apresentou?\"")
        r.ativo = ativo
        self.contexto["ativo"] = ativo or self.contexto["ativo"]
        partes, termos_busca = [], []

        if ativo and (inicio or fim):
            cob = fx.cobertura(ativo)
            if (fim and fim[:19] < cob[0].replace(" ", "T")) or (inicio and inicio[:19] > cob[1].replace(" ", "T")):
                r.tipo = "sem_informacao"
                r.texto = (nota_contexto + f"Não há dados do {ativo} no período solicitado "
                           f"({_fmt_periodo(inicio, fim)}). O período disponível na base vai de {cob[0]} a {cob[1]}. "
                           "Não é possível afirmar como o ativo se comportou fora desse intervalo.")
                r.fontes.append("Cobertura temporal da base (" +
                                ("scores_anomalias.csv" if ativo == config.ID_FORZY else "motor.db") + ")")
                return r

        # Dados operacionais e resultados dos modelos
        if ativo in config.IDS_MOTORES and "diagnostico" in intencoes:
            if inicio:
                res = self._registrar(r, "prever_falha_motor", dict(ativo=ativo, timestamp=fim or inicio))
                partes.append(_fmt_classificacao(res))
                if res.get("diagnostico") not in (None, "Normal"):
                    termos_busca.append(f"troubleshooting {res['diagnostico']} verificações")
                    r.escalonar = res.get("confianca", 0) >= 0.5
            else:
                return self._esclarecer(r, f"Para classificar o estado do {ativo} informe o instante desejado "
                                           "(ex.: 2023-01-04 06:00) ou as leituras de rotação, vibração, "
                                           "temperatura e corrente.")
        elif ativo == config.ID_FORZY and "diagnostico" in intencoes:
            intencoes.add("anomalia")
        if ativo and "leituras" in intencoes:
            partes.append(_fmt_leituras(self._registrar(r, "consultar_leituras",
                                                        dict(ativo=ativo, inicio=inicio, fim=fim, ciclo=ciclo))))
        if ativo and ("eventos" in intencoes or ("anomalia" in intencoes and ativo == config.ID_FORZY)):
            ev = self._registrar(r, "listar_eventos", dict(ativo=ativo, inicio=inicio, fim=fim))
            partes.append(_fmt_eventos(ev, ciclo))
            termos_busca += _termos_de_eventos(ev, ciclo)
        if ativo == config.ID_FORZY and "anomalia" in intencoes:
            ra = self._registrar(r, "resumo_anomalias", dict(ativo=ativo, inicio=inicio, fim=fim, ciclo=ciclo))
            partes.append(_fmt_resumo_anomalias(ra))
            if ra.get("pct_sinalizado_autoencoder", 0) > 30:
                termos_busca.append("assimetria térmica diferença de temperatura entre portas")
            termos_busca.append("interpretar divergência isolation forest autoencoder severidade")
        if ativo and "manutencao" in intencoes:
            hm = self._registrar(r, "historico_manutencao", dict(ativo=ativo, inicio=inicio, fim=fim))
            partes.append(_fmt_manutencao(hm))
            if hm["n_ordens"] == 0:
                r.tipo = "sem_informacao"
                termos_busca.append("histórico de manutenção")

        # Recuperação na documentação (RAG)
        consulta = " ".join([pergunta] + termos_busca)
        docs = self._registrar(r, "buscar_documentos", dict(consulta=consulta, ativo=ativo, k=config.TOP_K,
                                                            tipos=["documento"]), com_fontes=False)
        trechos = docs["trechos"]
        tem_dados = bool(partes)
        registros = []
        if not tem_dados:  # sem ferramenta de dados acionada: busca também eventos, ciclos e OS
            registros = self._registrar(r, "buscar_documentos", dict(
                consulta=consulta, ativo=ativo, inicio=inicio, fim=fim, k=3,
                tipos=["evento_falha", "ciclo_operacional", "ordem_servico"]), com_fontes=False)["trechos"]
        if trechos:
            partes.append(_fmt_trechos(trechos))
            _citar(r, trechos)
        if registros and not tem_dados:
            partes.append(_fmt_registros(registros))
            _citar(r, registros)

        if not partes:
            r.tipo = "sem_informacao"
            r.fontes = []
            r.texto = (nota_contexto + "Não encontrei informações suficientes na base de conhecimento para responder "
                       "a essa pergunta com segurança. A base cobre: dados de sensores do FZ-ATV-01 e dos motores "
                       "MTR-01 a MTR-20, resultados dos modelos de falha e de anomalia, histórico de manutenção "
                       "(simulado, apenas MTR) e procedimentos de troubleshooting de vibração, desbalanceamento, "
                       "superaquecimento, rolamentos e assimetria térmica. Reformule a pergunta ou consulte o "
                       "responsável técnico.")
            return r

        if "seguranca" in intencoes:
            r.escalonar = True
        self._anexar_escalonamento(r, partes)
        r.texto = nota_contexto + "\n\n".join(partes)
        return r

    def _avaliar_valores(self, r, pergunta, p, nums, ativo, intencoes):
        e_forzy = ativo == config.ID_FORZY or re.search(r"porta|p1|p2|acelera", p) or len(nums) >= 6
        partes = []
        if e_forzy:
            if len(nums) < 6:
                return self._esclarecer(r, "Para avaliar uma leitura do FZ-ATV-01 preciso das 6 variáveis, na ordem: "
                                           "velocidade P1 (mm/s), aceleração P1 (g), temperatura P1 (°C), velocidade "
                                           "P2 (mm/s), aceleração P2 (g), temperatura P2 (°C). Recebi "
                                           f"{len(nums)} valor(es).")
            r.ativo = config.ID_FORZY
            res = self._registrar(r, "avaliar_anomalia_sensor", dict(zip(
                ["p1_velocidade", "p1_aceleracao", "p1_temperatura", "p2_velocidade", "p2_aceleracao",
                 "p2_temperatura"], nums[:6])))
            partes.append(_fmt_anomalia(res))
            termos = "interpretar severidade autoencoder isolation forest"
            if res["severidade"] != "BAIXA":
                termos += " assimetria térmica diferença de temperatura entre portas"
            if res["severidade"] == "ALTA":
                r.escalonar = True
        else:
            if len(nums) < 4:
                return self._esclarecer(r, "Para o classificador de falhas preciso de rotação (RPM), vibração (mm/s), "
                                           "temperatura (°C) e corrente (A).")
            vals = _mapear_motor(p, nums)
            res = self._registrar(r, "prever_falha_motor", vals)
            r.ativo = ativo
            partes.append(_fmt_classificacao(res))
            termos = f"troubleshooting {res['diagnostico']} sintomas verificações ações corretivas"
            if res["diagnostico"] != "Normal" and res["confianca"] >= 0.5:
                r.escalonar = True
            if res["confianca"] < 0.6:
                partes.append("Confiança abaixo de 60%: as probabilidades estão divididas entre classes. "
                              "Trate o resultado como hipótese e confirme com inspeção em campo.")
        docs = self._registrar(r, "buscar_documentos", dict(consulta=termos, ativo=r.ativo, k=3, tipos=["documento"]),
                               com_fontes=False)
        trechos = [t for t in docs["trechos"] if t["tipo_fonte"] == "documento"]
        if trechos:
            partes.append(_fmt_trechos(trechos))
            _citar(r, trechos)
        if "seguranca" in intencoes:
            r.escalonar = True
        self._anexar_escalonamento(r, partes)
        r.texto = "\n\n".join(partes)
        return r

    def _valor_isolado(self, r, pergunta, nums):
        docs = self._registrar(r, "buscar_documentos", dict(consulta="zonas de severidade limites de referência "
                                                                     "base rígida base flexível", k=1), com_fontes=False)
        _citar(r, docs["trechos"])
        v = nums[0]
        zona = lambda lims: next((z for z, l in zip("ABC", lims) if v <= l), "D")
        r.tipo = "esclarecimento"
        r.texto = (f"Uma vibração de {v:g} mm/s, isoladamente, não permite um diagnóstico. Pela referência ISO 10816-3 "
                   f"(máquinas de 15 a 300 kW) ela ficaria na zona {zona((1.4, 2.8, 4.5))} se a base for rígida e na "
                   f"zona {zona((2.3, 4.5, 7.1))} se a base for flexível [DOC-01 §Limites de referência para máquinas de 15 kW a 300 kW (grupo 2)]. "
                   "Os limites valem para regime permanente, não para partidas e paradas.\n\n"
                   "Para uma avaliação com os modelos, informe:\n"
                   "  • o ativo (FZ-ATV-01 ou MTR-01 a MTR-20), e\n"
                   "  • as demais leituras: para FZ-ATV-01, velocidade/aceleração/temperatura das Portas 1 e 2; "
                   "para motores MTR, rotação, vibração, temperatura e corrente.")
        return r

    def _esclarecer(self, r, msg):
        r.tipo, r.texto = "esclarecimento", msg
        return r

    def _anexar_escalonamento(self, r, partes):
        if not r.escalonar:
            return
        seg = self._registrar(r, "buscar_documentos", dict(consulta=REF_ESCALONAMENTO, k=1, tipos=["documento"]),
                              com_fontes=False)
        ref = seg["trechos"][0] if seg["trechos"] else None
        _citar(r, seg["trechos"])
        partes.append("ATENÇÃO — avaliação de profissional responsável: o assistente apoia a investigação, mas não "
                      "autoriza intervenções. Decisões de parada, desmontagem, troca de componentes ou continuidade "
                      "da operação devem ser tomadas pelo responsável técnico, com bloqueio e etiquetagem (LOTO) antes "
                      "de qualquer intervenção" + (f" [{ref['doc_id']} §{ref['secao']}]." if ref else "."))

    # ─── Modo LLM (Anthropic tool use) ────────────────────────────────────
    def _responder_llm(self, pergunta: str) -> Resposta:
        import anthropic
        cliente = anthropic.Anthropic()
        r = Resposta(texto="", modo="llm")
        msgs = self.historico_llm + [{"role": "user", "content": pergunta}]
        for _ in range(8):  # limite de rodadas de ferramentas
            resp = cliente.messages.create(model=config.LLM_MODEL, max_tokens=1500, system=SYSTEM_PROMPT,
                                           tools=TOOLS, messages=msgs)
            msgs.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                break
            resultados = []
            for bloco in resp.content:  # trata TODAS as chamadas do turno (correção do agente v2)
                if bloco.type == "tool_use":
                    res = self._registrar(r, bloco.name, dict(bloco.input))
                    if bloco.name == "avaliar_anomalia_sensor" and res.get("severidade") == "ALTA":
                        r.escalonar = True
                    resultados.append({"type": "tool_result", "tool_use_id": bloco.id, "content": fx.para_json(res)})
            msgs.append({"role": "user", "content": resultados})
        r.texto = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        self.historico_llm = msgs[-12:] if msgs[0]["role"] == "user" else msgs
        if not r.ferramentas:
            r.tipo = "esclarecimento"
        return r


# ─── Formatação (modo offline) ───────────────────────────────────────────────
def _citar(r, trechos):
    for t in trechos:
        ref = f"{t['doc_id']} §{t['secao']} — {t['titulo']} [{t['origem']}] (score {t['score']})" \
            if t["tipo_fonte"] == "documento" else f"{t['id']} — {t['arquivo']} [{t['origem']}]"
        if ref not in r.fontes:
            r.fontes.append(ref)


def _fmt_periodo(ini, fim):
    f = lambda s: s.replace("T", " ")[:16] if s else "…"
    return f"{f(ini)} a {f(fim)}"


def _fmt_leituras(d):
    if d.get("sem_dados") or d.get("erro"):
        return d.get("erro") or f"Sem leituras no período. Cobertura disponível: {d['cobertura_disponivel'][0]} a {d['cobertura_disponivel'][1]}."
    linhas = [f"Leituras do {d['ativo']} — {d['n_leituras']} registros de {d['periodo_consultado'][0]} a "
              f"{d['periodo_consultado'][1]}:"]
    for c, e in d["estatisticas"].items():
        linhas.append(f"  • {c}: mín. {e['min']} | média {e['media']} | máx. {e['max']} {e['unidade']}")
    if "leituras_em_falha" in d:
        linhas.append(f"  • Leituras rotuladas como falha no período: {d['leituras_em_falha']}")
    if "pct_em_operacao" in d:
        linhas.append(f"  • Tempo em operação no período: {d['pct_em_operacao']}% das leituras")
    return "\n".join(linhas)


def _fmt_eventos(d, ciclo=None):
    if d["tipo"] == "ciclos_operacionais":
        cic = [c for c in d["ciclos"] if not ciclo or c["ciclo"] == ciclo]
        linhas = [f"Ciclos operacionais do {d['ativo']} (dados reais, sem rótulos de falha):"]
        for c in cic:
            linhas.append(f"  • Ciclo {c['ciclo']}: {c['inicio'][11:16]}–{c['fim'][11:16]}, {c['duracao_min']} min, "
                          f"temp. máx. P1/P2 {c['temp_max_p1']}/{c['temp_max_p2']} °C, leituras sinalizadas pelo "
                          f"Autoencoder {c['pct_flag_ae']}% e pelo Isolation Forest {c['pct_flag_iso']}%")
        destaque = max(cic, key=lambda c: c["pct_flag_ae"]) if cic else None
        if destaque and destaque["pct_flag_ae"] > 30:
            linhas.append(f"  → O Ciclo {destaque['ciclo']} concentra o maior percentual de leituras anômalas segundo o "
                          "Autoencoder. Não há falha confirmada: é um candidato a investigação.")
        return "\n".join(linhas)
    if not d["eventos"]:
        return f"Nenhum evento de falha registrado para o {d['ativo']} no período consultado."
    linhas = [f"Eventos de falha do {d['ativo']} (base sintética):"]
    for e in d["eventos"]:
        linhas.append(f"  • {e['tipo_falha']}: {e['inicio'].replace('T', ' ')[:16]} a {e['fim'].replace('T', ' ')[:16]} "
                      f"— vibração máx. {e['vib_max']} mm/s, temperatura máx. {e['temp_max']} °C, "
                      f"corrente máx. {e['corrente_max']} A, rotação mín. {e['rpm_min']:.0f} RPM")
    return "\n".join(linhas)


def _termos_de_eventos(d, ciclo):
    if d["tipo"] == "eventos_de_falha":
        return [f"troubleshooting {e['tipo_falha']}" for e in d["eventos"][:2]]
    return []


def _fmt_resumo_anomalias(d):
    if d.get("erro") or d.get("sem_dados"):
        return d.get("erro") or "Sem leituras no período para calcular anomalias."
    return (f"Resultado dos modelos de anomalia ({d['n_leituras']} leituras, {d['periodo'][0]} a {d['periodo'][1]}):\n"
            f"  • Autoencoder (semissupervisionado) sinalizou {d['pct_sinalizado_autoencoder']}% das leituras\n"
            f"  • Isolation Forest (não supervisionado) sinalizou {d['pct_sinalizado_isolation_forest']}%\n"
            f"  • Baseline estatístico 3-sigma: {d['pct_fora_baseline_3sigma']}%\n"
            f"  • Leituras sinalizadas pelos dois modelos: {d['leituras_sinalizadas_pelos_dois']}\n"
            "  A divergência entre os modelos é esperada em anomalias longas e coesas: o Isolation Forest treinado "
            "com todo o histórico tende a tratá-las como normais [DOC-06].")


def _fmt_manutencao(d):
    if d["n_ordens"] == 0:
        return (f"Não há registros de manutenção (ordens de serviço) para o {d['ativo']} na base disponível. "
                "Por isso não é possível informar datas de intervenções, trocas de componentes ou lubrificações "
                "desse ativo.")
    linhas = [f"Histórico de manutenção do {d['ativo']} — {d['n_ordens']} ordem(ns) de serviço (dados SIMULADOS):"]
    for o in d["ordens"]:
        linhas.append(f"  • {o['os_id']} ({o['tipo']}), {o['data_abertura'].replace('T', ' ')[:16]}: "
                      f"{o['acao_executada']} — {o['responsavel']} [proc. {o['procedimento']}]")
    return "\n".join(linhas)


def _fmt_anomalia(d):
    z = ", ".join(f"{k} z={v}" for k, v in d["zscores_baseline"].items() if abs(v) > 2) or "nenhum sensor com |z| > 2"
    return (f"Avaliação da leitura (FZ-ATV-01) — estado inferido: {d['estado_operacional']}\n"
            f"  • Severidade: {d['severidade']} ({d['concordancia']})\n"
            f"  • Isolation Forest: score {d['score_isolation_forest']} — "
            f"{'sinalizado' if d['sinalizado_isolation_forest'] else 'não sinalizado'}\n"
            f"  • Autoencoder: erro {d['erro_autoencoder']} (limiar {d['limiar_autoencoder']}) — "
            f"{'sinalizado' if d['sinalizado_autoencoder'] else 'não sinalizado'}\n"
            f"  • Desvios em relação ao baseline: {z}\n"
            f"  {d['aviso']}")


def _fmt_classificacao(d):
    if d.get("erro"):
        return d["erro"]
    prob = ", ".join(f"{k} {v:.0%}" for k, v in d["probabilidades"].items())
    txt = (f"Classificador de falhas (Sprint 2): {d['diagnostico']} com confiança de {d['confianca']:.0%}\n"
           f"  • Probabilidades: {prob}\n  • Entrada: {d['entrada']}\n  • {d['aviso']}")
    if "rotulo_real_no_banco" in d:
        txt += f"\n  • Rótulo registrado no banco para esse instante: {d['rotulo_real_no_banco']}"
    return txt


def _fmt_trechos(trechos):
    linhas = ["Documentação técnica relacionada:"]
    for t in trechos:
        frases = re.split(r"(?<=[.!?])\s+|\n", t["texto"])
        resumo = " ".join(f.strip() for f in frases if f.strip())
        if len(resumo) > 420:
            resumo = resumo[:420].rsplit(" ", 1)[0] + " …"
        aviso = " (documento SIMULADO)" if t["origem"].startswith("SIMULADO") else ""
        linhas.append(f"  • [{t['doc_id']} §{t['secao']}]{aviso}: {resumo}")
    return "\n".join(linhas)


def _fmt_registros(regs):
    return "Registros relacionados:\n" + "\n".join(f"  • [{t['id']}] {t['texto']}" for t in regs)


def _mapear_motor(p, nums):
    """Associa números a sensores pela unidade mais próxima; senão usa a ordem rpm, vib, temp, corrente."""
    vals = {}
    for n, rx in ((r"(\d+(?:[.,]\d+)?)\s*rpm", "rotacao_rpm"), (r"(\d+(?:[.,]\d+)?)\s*mm/s", "vibracao_mm_s"),
                  (r"(\d+(?:[.,]\d+)?)\s*(?:°|graus|c\b)", "temperatura_c"), (r"(\d+(?:[.,]\d+)?)\s*a\b", "corrente_a")):
        m = re.search(n, p)
        if m:
            vals[rx] = float(m.group(1).replace(",", "."))
    if len(vals) < 4:
        ordem = ["rotacao_rpm", "vibracao_mm_s", "temperatura_c", "corrente_a"]
        resto = [x for x in nums if x not in vals.values()]
        for k in ordem:
            if k not in vals and resto:
                vals[k] = resto.pop(0)
    return vals
