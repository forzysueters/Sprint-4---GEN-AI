"""
gerar_documento.py — Gera docs/Documentacao_Final_Sprint4_Forzy.pdf.

Os resultados de testes (cenários e recuperação) são lidos diretamente de resultados/,
para que o documento reflita a última execução.

Uso:
    python docs/gerar_documento.py
"""
import html
import json
from pathlib import Path

import pandas as pd
from weasyprint import HTML

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
FIG = RAIZ / "docs" / "figuras"

cen = {c["id"]: c for c in json.loads((RES / "cenarios.json").read_text(encoding="utf-8"))}
rec = json.loads((RES / "avaliacao_recuperacao.json").read_text(encoding="utf-8"))["metricas"]
ciclos = pd.read_csv(RAIZ / "conhecimento" / "gerado" / "ciclos_fz.csv")
eventos = pd.read_csv(RAIZ / "conhecimento" / "gerado" / "eventos_falha_mtr.csv")
os_ = pd.read_csv(RAIZ / "conhecimento" / "historico_manutencao.csv")
e = html.escape


def br(v):
    return f"{v:.3f}".replace(".", ",")


def saida(cid, turno=-1):
    r = cen[cid]["respostas"][turno]
    txt = r["texto"]
    if r["fontes"]:
        txt += "\n\nFontes consultadas:\n" + "\n".join(f"  [{i}] {f}" for i, f in enumerate(r["fontes"], 1))
    return f"<pre class='saida'>{e(txt)}</pre>"


def ferramentas(cid):
    fs = [f["ferramenta"] for r in cen[cid]["respostas"] for f in r["ferramentas"]]
    return ", ".join(f"<code>{x}</code>" for x in dict.fromkeys(fs)) or "nenhuma (pedido de esclarecimento)"


def cenario(cid, titulo, analise):
    c = cen[cid]
    turnos = "".join(f"<p class='entrada'><b>Entrada{'' if len(c['turnos']) == 1 else f' (turno {i})'}:</b> "
                     f"“{e(t)}”</p>" for i, t in enumerate(c["turnos"], 1))
    corpo = "".join(saida(cid, i) for i in range(len(c["respostas"])))
    return f"""
    <h3>{titulo}</h3>
    {turnos}
    <p><b>Resultado esperado:</b> {e(c['esperado'])}</p>
    <p><b>Resultado obtido</b> (modo offline, {max(c['tempo_ms']):.0f} ms; ferramentas: {ferramentas(cid)}):</p>
    {corpo}
    <p><b>Verificação automática:</b> <span class='ok'>{c['status']}</span>.
    <b>Análise da equipe:</b> {analise}</p>"""


tab_cen = "".join(
    f"<tr><td>{c['id']}</td><td>{e(c['categoria'])}</td><td>{e(c['turnos'][-1][:70])}{'…' if len(c['turnos'][-1]) > 70 else ''}</td>"
    f"<td>{'/'.join(r['tipo'] for r in c['respostas'])}</td><td class='ok'>{c['status']}</td></tr>"
    for c in cen.values())
tab_rec = "".join(f"<tr><td>{e(k)}</td><td>{br(v['hit@1'])}</td><td>{br(v['hit@3'])}</td><td>{br(v['mrr@5'])}</td></tr>"
                  for k, v in rec.items())
tab_ciclos = "".join(
    f"<tr{' class=destaque' if r.ciclo == 6 else ''}><td>{r.ciclo}</td><td>{r.inicio[11:16]}–{r.fim[11:16]}</td>"
    f"<td>{str(r.duracao_min).replace('.', ',')}</td><td>{r.n_leituras}</td><td>{r.vel_max_p1:g} / {r.vel_max_p2:g}</td>"
    f"<td>{r.temp_max_p1} / {r.temp_max_p2}</td><td>{str(r.pct_flag_iso).replace('.', ',')}%</td>"
    f"<td>{str(r.pct_flag_ae).replace('.', ',')}%</td></tr>" for r in ciclos.itertuples())
n_ev = eventos["tipo_falha"].value_counts()
n_corr, n_prev = (os_["tipo"] == "corretiva").sum(), (os_["tipo"] == "preventiva").sum()

CSS = """
@page { size: A4; margin: 2.1cm 2cm 2.2cm 2cm;
  @bottom-right { content: "Página " counter(page) " de " counter(pages); font-size: 8.5pt; color: #777; }
  @bottom-left { content: "Sprint 4 — Documentação Final · Assistente de Manutenção Forzy"; font-size: 8.5pt; color: #777; } }
@page capa { margin: 0; @bottom-right { content: none; } @bottom-left { content: none; } }
body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 10.3pt; line-height: 1.45; color: #1d2733; }
h1 { font-size: 17pt; color: #12355b; border-bottom: 2px solid #2a6f97; padding-bottom: 4px; margin-top: 0;
     page-break-before: always; string-set: cap content(); }
h2 { font-size: 12.5pt; color: #2a6f97; margin: 16px 0 6px; }
h3 { font-size: 11pt; color: #12355b; margin: 14px 0 4px; }
p { margin: 5px 0 7px; text-align: justify; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 8.8pt; page-break-inside: avoid; }
th { background: #12355b; color: white; text-align: left; padding: 4px 6px; font-weight: 600; }
td { border-bottom: 1px solid #d5dde5; padding: 3.5px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f5f8fb; }
tr.destaque td { background: #fde8e8; font-weight: 600; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.6pt; background: #eef2f6; padding: 0 3px; border-radius: 2px; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.6pt; line-height: 1.35; background: #f4f6f8;
      border-left: 3px solid #2a6f97; padding: 7px 9px; white-space: pre-wrap; word-wrap: break-word; margin: 5px 0 8px; }
pre.saida { border-left-color: #e09f3e; background: #fffaf2; }
.ok { color: #1b7a3a; font-weight: 700; }
.nota { background: #eef4f8; border: 1px solid #c4d7e5; border-radius: 4px; padding: 7px 10px; margin: 8px 0; font-size: 9.4pt; }
.alerta { background: #fdf3e7; border: 1px solid #ecd0a6; border-radius: 4px; padding: 7px 10px; margin: 8px 0; font-size: 9.4pt; }
figure { margin: 8px 0 12px; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; border: 1px solid #e0e6ec; }
figcaption { font-size: 8.6pt; color: #555; margin-top: 3px; font-style: italic; }
ul, ol { margin: 4px 0 8px; padding-left: 20px; } li { margin: 2px 0; }
.capa { page: capa; height: 29.7cm; background: #12355b; color: white; padding: 3.2cm 2.4cm; box-sizing: border-box; position: relative; }
.capa .sup { font-size: 11pt; letter-spacing: 2px; color: #9cc3dd; }
.capa h0 { display: block; font-size: 27pt; font-weight: 700; line-height: 1.15; margin: 14px 0 10px; }
.capa .sub { font-size: 13pt; color: #d5e6f2; margin-bottom: 40px; }
.capa .bloco { border-top: 1px solid #5d84a8; padding-top: 14px; font-size: 10.5pt; line-height: 1.7; color: #e8f1f8; }
.capa .rod { position: absolute; bottom: 2.4cm; left: 2.4cm; font-size: 9.5pt; color: #9cc3dd; }
.sumario { page-break-before: always; }
.sumario a { color: #1d2733; text-decoration: none; }
.sumario li { margin: 5px 0; font-size: 10.5pt; }
.sumario a::after { content: leader('.') target-counter(attr(href), page); }
.duas { display: flex; gap: 10px; } .duas figure { flex: 1; }
"""

secoes = []

# ─── CAPA E SUMÁRIO ──────────────────────────────────────────────────────────
secoes.append("""
<div class="capa">
  <div class="sup">SPRINT 4 · GENERATIVE IA &amp; ADVANCED NET</div>
  <h0>Assistente de Manutenção Forzy</h0>
  <div class="sub">Documentação final da solução de IA: dados, modelos, arquitetura RAG,
  assistente conversacional, testes e manual de execução</div>
  <div class="bloco">
    <b>Integrantes</b><br>
    Matheus Mikio — RM 561864<br>Henry Gimenez — RM 563217<br>Ian Nobres — RM 561681<br>
    Gustavo Balbo — RM 561711<br>Vinicius Araujo — RM 564504
  </div>
  <div class="rod">Projeto de Manutenção Preditiva — IA Aplicada · Novembro de 2026<br>
  Código-fonte: pasta <b>forzy-assistente/</b> entregue junto a este documento (ver README.md)</div>
</div>
<div class="sumario">
<h2 style="font-size:16pt;color:#12355b">Sumário</h2>
<ol>
<li><a href="#s1">Visão geral da solução</a></li>
<li><a href="#s2">Documentação dos dados</a></li>
<li><a href="#s3">Arquitetura da solução</a></li>
<li><a href="#s4">Modelos de inteligência artificial</a></li>
<li><a href="#s5">Arquitetura RAG</a></li>
<li><a href="#s6">Documentação funcional do assistente</a></li>
<li><a href="#s7">Testes e resultados</a></li>
<li><a href="#s8">Manual de instalação e execução</a></li>
<li><a href="#s9">Limitações e continuidade</a></li>
<li><a href="#s10">Organização da entrega final</a></li>
</ol>
<div class="nota" style="margin-top:24px"><b>Convenção de rótulos usada em todo o documento.</b>
<b>REAL</b> = dados fornecidos pela Forzy (ativo FZ-ATV-01). <b>SINTÉTICO</b> = base gerada por script na Sprint 2
(motores MTR-01 a MTR-20). <b>SIMULADO</b> = conteúdo elaborado pela equipe para viabilizar o protótipo
(procedimentos técnicos, histórico de ordens de serviço), que deve ser substituído por material oficial da Forzy.
<b>PROJETO</b> = síntese dos relatórios técnicos das sprints anteriores.</div>
<div class="nota"><b>Estado real do projeto.</b> Cada capítulo distingue o que está <b>implementado e validado</b>,
o que está <b>implementado mas não validado</b> (geração com LLM, que depende de chave de API) e o que é
<b>melhoria futura</b>. Os números das seções 7 e 9 foram gerados pelos scripts de teste do repositório
(<code>resultados/</code>) e podem ser reproduzidos com os comandos do capítulo 8.</div>
</div>
""")

# ─── 1. VISÃO GERAL ──────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s1">1. Visão geral da solução</h1>
<h2>1.1 Problema</h2>
<p>Paradas não planejadas de equipamentos rotativos são caras e, muitas vezes, precedidas por sinais nos sensores
— vibração, temperatura, corrente — que passam despercebidos. Mesmo quando um desvio é percebido, o técnico precisa
juntar informações espalhadas: leituras recentes, histórico de falhas e de manutenção, e procedimentos técnicos.
Ao longo do projeto a equipe construiu peças separadas para esse problema (classificador de falhas na Sprint 2,
baseline e detecção de anomalias com dados reais da Forzy na Sprint 3). A Sprint 4 integra essas peças em um
<b>assistente conversacional com recuperação de contexto (RAG)</b> e consolida a documentação.</p>
<h2>1.2 Público-alvo</h2>
<ul>
<li><b>Técnicos de manutenção</b>: consultam rapidamente o estado de um ativo e o procedimento de verificação.</li>
<li><b>Engenheiros de confiabilidade</b>: investigam anomalias, comparam ciclos e interpretam os scores dos modelos.</li>
<li><b>Equipe de dados da Forzy</b>: mantém a base de conhecimento, os modelos e a integração.</li>
</ul>
<h2>1.3 Benefícios esperados para a Forzy</h2>
<ul>
<li>Triagem mais rápida: uma pergunta em linguagem natural retorna dados, resultado dos modelos e procedimento, com fontes.</li>
<li>Monitoramento possível já com dados sem rótulo, por detecção de anomalias (abordagem da Sprint 3).</li>
<li>Rastreabilidade: toda resposta lista as fontes consultadas e diferencia dados reais de simulados.</li>
<li>Segurança: o assistente não autoriza intervenções e encaminha casos críticos ao profissional responsável.</li>
</ul>
<h2>1.4 Escopo e funcionalidades entregues</h2>
<table><tr><th>Funcionalidade</th><th>Componente</th><th>Status</th></tr>
<tr><td>Consulta de leituras por ativo, período e ciclo operacional</td><td><code>consultar_leituras</code></td><td>Implementado e testado</td></tr>
<tr><td>Eventos de falha (MTR) e ciclos operacionais com scores (FZ-ATV-01)</td><td><code>listar_eventos</code></td><td>Implementado e testado</td></tr>
<tr><td>Histórico de manutenção (ordens de serviço)</td><td><code>historico_manutencao</code></td><td>Implementado e testado (dados SIMULADOS)</td></tr>
<tr><td>Classificação de falhas — valores avulsos ou janela real do banco</td><td><code>prever_falha_motor</code> (Sprint 2)</td><td>Implementado e testado</td></tr>
<tr><td>Avaliação de anomalia de uma leitura do ativo real</td><td><code>avaliar_anomalia_sensor</code> (Sprint 3)</td><td>Implementado e testado</td></tr>
<tr><td>Resumo de anomalias por período/ciclo</td><td><code>resumo_anomalias</code></td><td>Implementado e testado</td></tr>
<tr><td>Busca na documentação técnica com filtros (RAG)</td><td><code>buscar_documentos</code></td><td>Implementado e avaliado (seção 7.3)</td></tr>
<tr><td>Ambiguidade, falta de informação e escalonamento</td><td>Orquestrador</td><td>Implementado e testado</td></tr>
<tr><td>Interface web e linha de comando</td><td><code>app.py</code>, <code>cli.py</code></td><td>Implementado</td></tr>
<tr><td>Geração de texto com LLM (Claude, tool use)</td><td>Orquestrador — modo <code>llm</code></td><td>Implementado; laço validado com dublê; qualidade não avaliada</td></tr>
<tr><td>Comparação entre vários ativos; streaming em tempo real; alertas automáticos</td><td>—</td><td>Pendente (capítulo 9)</td></tr>
</table>
<h2>1.5 Principais casos de uso</h2>
<ol>
<li><b>Investigar uma anomalia</b> — “O que aconteceu no ciclo 6 do FZ-ATV-01?”</li>
<li><b>Diagnosticar a partir de leituras</b> — “Motor com vibração 8,2 mm/s, 92 °C, 15,5 A, 1720 RPM. Posso continuar operando?”</li>
<li><b>Consultar o histórico</b> — “Quais falhas o MTR-07 apresentou?” / “Qual o histórico de manutenção do MTR-03?”</li>
<li><b>Obter o procedimento</b> — “Quais são os limites de vibração da ISO 10816 para base rígida?”</li>
</ol>
""")

# ─── 2. DADOS ────────────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s2">2. Documentação dos dados</h1>
<p>A solução usa cinco fontes. A tabela resume a natureza de cada uma; as subseções detalham formato, período,
variáveis, unidades, identificação dos ativos, tratamentos e limitações.</p>
<table><tr><th>Fonte</th><th>Arquivo</th><th>Natureza</th><th>Volume</th><th>Período</th></tr>
<tr><td>Sensores do ativo Forzy</td><td><code>sprint3/scores_anomalias.csv</code></td><td>REAL</td><td>7.183 leituras, 1 ativo, 2 pontos</td><td>19/05/2026 11:46:10 – 15:43:14</td></tr>
<tr><td>Sensores dos motores</td><td><code>sprint2/motor.db</code></td><td>SINTÉTICO</td><td>30.000 leituras, 20 motores</td><td>01/01/2023 00:00 – 11/01/2023 09:50</td></tr>
<tr><td>Registros de falhas</td><td>tabela <code>leituras.falha</code> → <code>eventos_falha_mtr.csv</code></td><td>SINTÉTICO</td><td>{len(eventos)} eventos</td><td>idem motores</td></tr>
<tr><td>Histórico de manutenção</td><td><code>conhecimento/historico_manutencao.csv</code></td><td>SIMULADO</td><td>{len(os_)} OS ({n_corr} corretivas, {n_prev} preventivas)</td><td>idem motores</td></tr>
<tr><td>Documentação técnica</td><td><code>conhecimento/documentos/DOC-01…09.md</code></td><td>SIMULADO / REAL / PROJETO</td><td>9 documentos, 54 seções</td><td>—</td></tr>
</table>

<h2>2.1 Dados de sensores do ativo real (FZ-ATV-01)</h2>
<p><b>Origem e formato.</b> Exportação “History” de um IO-Link Master: CSV separado por ponto e vírgula, três linhas
de cabeçalho técnico, timestamp ISO 8601 com milissegundos, duas colunas de bytes brutos (descartadas por serem
redundantes) e seis canais numéricos já decodificados. O arquivo bruto <code>forzy_history.csv</code> foi tratado na
Sprint 3; o assistente consome <code>scores_anomalias.csv</code>, que contém as mesmas 7.183 leituras, a segmentação
em ciclos e os scores dos modelos.</p>
<p><b>Identificação do ativo.</b> O extrato não traz identificador; a equipe atribuiu <code>FZ-ATV-01</code>.
Tipo de máquina, fabricante, potência e tipo de base não foram informados (ver DOC-05).</p>
<table><tr><th>Variável</th><th>Canal IO-Link</th><th>Unidade</th><th>Descrição</th></tr>
<tr><td><code>p1_velocidade</code> / <code>p2_velocidade</code></td><td>1.1 / 2.1</td><td>mm/s</td><td>Velocidade de vibração RMS (severidade, ISO 10816)</td></tr>
<tr><td><code>p1_aceleracao</code> / <code>p2_aceleracao</code></td><td>1.2 / 2.2</td><td>g</td><td>Aceleração de vibração RMS (sensível a defeitos de rolamento)</td></tr>
<tr><td><code>p1_temperatura</code> / <code>p2_temperatura</code></td><td>1.3 / 2.3</td><td>°C</td><td>Temperatura no ponto de medição</td></tr>
<tr><td><code>running</code>, <code>cycle_id</code></td><td>derivadas</td><td>—</td><td>Estado (operação se velocidade &gt; 0,5 mm/s) e segmento</td></tr>
<tr><td><code>score_*</code>, <code>flag_*</code></td><td>derivadas</td><td>—</td><td>Scores e sinalizações do Isolation Forest, Autoencoder e baseline 3σ</td></tr>
</table>
<p><b>Tratamentos.</b> Sem valores nulos; ruído de repouso preservado; amostragem irregular (report-on-change,
mediana 0,59 s, máximo 228 s) mantida com o intervalo <code>dt_seg</code> como feature; piso de 0,1 s no denominador
da taxa de variação para neutralizar registros duplicados do IO-Link; 28 features padronizadas (StandardScaler).
Na Sprint 4, o <code>cycle_id</code> do CSV (13 segmentos alternando repouso e operação) foi convertido para os
<b>6 ciclos operacionais</b> usados nos relatórios.</p>
<table><tr><th>Ciclo</th><th>Horário</th><th>Duração (min)</th><th>Leituras</th><th>Vel. máx. P1/P2 (mm/s)</th><th>Temp. máx. P1/P2 (°C)</th><th>% IF</th><th>% AE</th></tr>
{tab_ciclos}</table>
<p style="font-size:8.8pt">% IF / % AE: percentual das leituras do ciclo sinalizadas pelo Isolation Forest e pelo Autoencoder.
Fonte: <code>conhecimento/gerado/ciclos_fz.csv</code>, gerado por <code>rag/preparar_base.py</code>.</p>
<figure><img src="{FIG / 'fz_ciclos_scores.png'}" style="width:96%">
<figcaption>Figura 1 — Série real do FZ-ATV-01: os seis ciclos operacionais (cinza) e o Ciclo 6 (vermelho),
em que o erro de reconstrução do Autoencoder permanece acima do limiar de forma persistente.</figcaption></figure>

<h2>2.2 Dados de sensores dos motores (MTR-01 a MTR-20) — SINTÉTICO</h2>
<p><b>Origem e formato.</b> Banco SQLite <code>motor.db</code> gerado por <code>gerar_banco.py</code> (seed 42) com as
tabelas <code>motores</code> (cadastro: fabricante, modelo, potência em kW, data de instalação), <code>leituras</code>
e <code>tipos_falha</code>. 1.500 leituras por motor a cada 10 minutos. Os motores são identificados no assistente
como <code>MTR-01</code> a <code>MTR-20</code> (id 1 a 20 do banco).</p>
<table><tr><th>Variável</th><th>Unidade</th><th>Nominal</th><th>Comportamento em falha</th></tr>
<tr><td><code>rotacao_rpm</code></td><td>RPM</td><td>~1750</td><td>Cai 30–80 RPM na falha mecânica</td></tr>
<tr><td><code>vibracao_mm_s</code></td><td>mm/s</td><td>~2,5</td><td>+5–10 (desbalanceamento); +3–7 (falha mecânica)</td></tr>
<tr><td><code>temperatura_c</code></td><td>°C</td><td>~65</td><td>+20–40 (superaquecimento); +10–20 (falha mecânica)</td></tr>
<tr><td><code>corrente_a</code></td><td>A</td><td>~12</td><td>+3–7 (superaquecimento)</td></tr>
<tr><td><code>falha</code></td><td>código</td><td>0</td><td>0 Normal (91,4%), 1 Desbalanceamento (2,3%), 2 Superaquecimento (2,6%), 3 Falha mecânica (3,7%)</td></tr>
</table>
<p>Cada falha entra com rampa de 30 leituras (5 h). Tratamentos na Sprint 2: codificação de fabricante e modelo,
médias e desvios móveis de 5 leituras, divisão temporal (últimas 300 leituras de cada motor para teste).</p>

<h2>2.3 Registros de falhas e histórico de manutenção</h2>
<p><b>Eventos de falha</b> ({len(eventos)}): blocos contíguos de <code>falha ≠ 0</code> extraídos de <code>motor.db</code>
— {', '.join(f'{v} de {k.lower()}' for k, v in n_ev.items())} — com início, fim e valores extremos dos sensores.</p>
<p><b>Histórico de manutenção — SIMULADO.</b> A Forzy não forneceu ordens de serviço. Para demonstrar a consulta
de histórico, <code>preparar_base.py</code> gera (seed 42) uma OS corretiva 1–6 h após cada evento de falha, com a ação
correspondente ao procedimento (DOC-02, DOC-03 ou DOC-04), e 10 OS preventivas de lubrificação. Todas têm
<code>origem = SIMULADO</code>, e o assistente informa isso ao exibi-las. <b>O ativo real FZ-ATV-01 não tem nenhuma
OS</b>, de propósito: a ausência é usada para testar o comportamento sem informação (cenário C3).</p>

<h2>2.4 Documentação técnica</h2>
<table><tr><th>ID</th><th>Documento</th><th>Ativos</th><th>Origem</th></tr>
<tr><td>DOC-01</td><td>Guia de severidade de vibração (referência ISO 10816-3)</td><td>todos</td><td>SIMULADO (resumo da equipe)</td></tr>
<tr><td>DOC-02</td><td>Troubleshooting — desbalanceamento de rotor</td><td>todos</td><td>SIMULADO</td></tr>
<tr><td>DOC-03</td><td>Troubleshooting — superaquecimento</td><td>todos</td><td>SIMULADO</td></tr>
<tr><td>DOC-04</td><td>Troubleshooting — falha mecânica e rolamentos</td><td>todos</td><td>SIMULADO</td></tr>
<tr><td>DOC-05</td><td>Ficha técnica e instalação dos sensores do FZ-ATV-01</td><td>FZ-ATV-01</td><td>REAL + campos “não informado”</td></tr>
<tr><td>DOC-06</td><td>Como interpretar os resultados dos modelos</td><td>todos</td><td>PROJETO</td></tr>
<tr><td>DOC-07</td><td>Troubleshooting — assimetria térmica entre pontos de medição</td><td>FZ-ATV-01</td><td>SIMULADO (baseado no achado <code>diff_temp</code>)</td></tr>
<tr><td>DOC-08</td><td>Regras de segurança e escalonamento</td><td>todos</td><td>SIMULADO</td></tr>
<tr><td>DOC-09</td><td>Ficha técnica dos motores MTR (gerada do cadastro do <code>motor.db</code>)</td><td>MTR-01…20</td><td>SINTÉTICO</td></tr>
</table>
<p>Cada documento é um Markdown com cabeçalho de metadados (<code>id</code>, <code>titulo</code>, <code>tipo</code>,
<code>ativos</code>, <code>origem</code>, <code>versao</code>) e seções <code>##</code>, que são a unidade de indexação.</p>

<h2>2.5 Limitações dos dados</h2>
<ul>
<li>Ativo real: um único ativo, ~4 horas, sem rótulos de falha, sem metadados (tipo, potência, base), sem rotação e corrente.</li>
<li>Motores: dados sintéticos com separabilidade elevada; métricas de classificação não se transferem para dados reais.</li>
<li>Inconsistências da base sintética: fabricante grafado como “WEG” e “Weg”; 6 dos 20 motores (MTR-01, 03, 04, 06, 09 e 17) têm data de
instalação posterior a 01/01/2023, início das leituras (ex.: MTR-01, 2023-05-16).</li>
<li>Procedimentos e histórico de OS são simulados; os períodos dos dois conjuntos (2023 e 2026) não se sobrepõem.</li>
</ul>
""")

# ─── 3. ARQUITETURA ──────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s3">3. Arquitetura da solução</h1>
<figure><img src="{FIG / 'arquitetura.png'}" style="width:78%">
<figcaption>Figura 2 — Arquitetura: fontes de dados, modelos das sprints anteriores, camada RAG e assistente
(fonte editável em <code>docs/arquitetura.dot</code>).</figcaption></figure>
<h2>3.1 Componentes e responsabilidades</h2>
<table><tr><th>Componente</th><th>Arquivo</th><th>Responsabilidade</th></tr>
<tr><td>Configuração</td><td><code>rag/config.py</code></td><td>Caminhos dos artefatos, leitura do <code>.env</code>, parâmetros (top-k, score mínimo, modelo LLM, modo).</td></tr>
<tr><td>Preparação e indexação</td><td><code>rag/preparar_base.py</code></td><td>Extrai eventos (MTR) e ciclos (FZ), gera OS simuladas e DOC-09, divide em trechos com metadados e ajusta o índice.</td></tr>
<tr><td>Processamento de texto</td><td><code>rag/texto.py</code></td><td>Normaliza (minúsculas, sem acentos) e extrai ativo, período, ciclo e valores numéricos da pergunta.</td></tr>
<tr><td>Recuperador</td><td><code>rag/recuperador.py</code></td><td>Similaridade TF-IDF híbrida com filtros por ativo, período e tipo de fonte; score mínimo.</td></tr>
<tr><td>Ferramentas</td><td><code>rag/ferramentas.py</code></td><td>Sete funções que acessam os dados e executam os modelos; cada uma devolve suas fontes.</td></tr>
<tr><td>Orquestrador</td><td><code>rag/assistente.py</code></td><td>Interpreta a pergunta, decide esclarecer, consultar ou recusar; aciona ferramentas; gera a resposta (LLM ou offline); monta fontes e alerta de segurança.</td></tr>
<tr><td>Instruções do LLM</td><td><code>rag/prompts.py</code></td><td>Prompt de sistema e esquemas JSON das ferramentas.</td></tr>
<tr><td>Interfaces</td><td><code>app.py</code>, <code>cli.py</code></td><td>Chat web com filtros, fontes e painel; linha de comando com modo debug.</td></tr>
</table>
<h2>3.2 Fluxo de informações (da entrada à resposta)</h2>
<ol>
<li><b>Entrada</b>: o usuário escreve a pergunta na interface (opcionalmente escolhe o ativo na barra lateral).</li>
<li><b>Interpretação</b>: extração de ativo (<code>MTR-07</code>, “motor 7”, “Forzy”, “ciclo 6”), período
(dd/mm/aaaa ou aaaa-mm-dd), ciclo, números e intenções (leituras, falhas, anomalia, manutenção, diagnóstico,
procedimento, segurança, fora do escopo). O ativo da pergunta anterior é reaproveitado quando a nova pergunta não cita outro.</li>
<li><b>Decisão</b>: se a pergunta depende de um ativo que não foi informado, o assistente pede esclarecimento;
se o período está fora da cobertura, informa a cobertura disponível; se é fora do escopo, recusa.</li>
<li><b>Dados e modelos</b>: as ferramentas consultam <code>motor.db</code>, <code>scores_anomalias.csv</code> e o
histórico de OS, e executam o Random Forest, o Isolation Forest, o Autoencoder e o baseline.</li>
<li><b>Recuperação</b>: a pergunta é enriquecida com termos derivados dos resultados (ex.: diagnóstico
“Superaquecimento” → “troubleshooting superaquecimento”) e enviada ao recuperador com filtro de ativo.</li>
<li><b>Geração</b>: no modo <code>llm</code>, o Claude recebe o prompt de sistema e as ferramentas e escreve a resposta
citando as fontes; no modo <code>offline</code>, templates montam a resposta com os mesmos resultados.</li>
<li><b>Saída</b>: o sistema anexa a lista de fontes efetivamente retornadas pelas ferramentas e, quando aplicável, o alerta de
avaliação por profissional responsável (DOC-08).</li>
</ol>
<h2>3.3 Tecnologias</h2>
<table><tr><th>Camada</th><th>Tecnologia</th><th>Motivo</th></tr>
<tr><td>Dados</td><td>SQLite, CSV, Markdown, pandas</td><td>Formatos já usados nas sprints anteriores; sem servidor.</td></tr>
<tr><td>Modelos</td><td>scikit-learn 1.8 (Random Forest, Isolation Forest, StandardScaler), PyTorch (Autoencoder)</td><td>Reuso dos artefatos serializados das Sprints 2 e 3.</td></tr>
<tr><td>Recuperação</td><td>scikit-learn <code>TfidfVectorizer</code> (palavras 1–2-gramas + caracteres 3–5-gramas)</td><td>Roda offline, sem download de modelos; adequado a uma base pequena em português.</td></tr>
<tr><td>Geração</td><td>API Anthropic (Claude, tool use), modelo configurável por <code>ANTHROPIC_MODEL</code></td><td>Continuidade com o agente das Sprints 2 e 3.</td></tr>
<tr><td>Interface</td><td>Streamlit; CLI em Python</td><td>Prototipação rápida com chat e gráficos.</td></tr>
</table>
<h2>3.4 Integração entre os modelos das sprints anteriores e o assistente</h2>
<p>O agente da Sprint 3 (<code>agente_manutencao_v2.py</code>) já expunha os modelos como ferramentas, mas carregava
artefatos por caminho relativo na importação, tratava só a primeira chamada de ferramenta de cada turno e, no
classificador, zerava fabricante e modelo. Na Sprint 4 a integração foi reescrita em <code>ferramentas.py</code>:</p>
<ul>
<li>Carregamento preguiçoso e em cache dos artefatos, por caminho absoluto configurável.</li>
<li><b>Classificador com janela real</b>: dado um motor MTR e um instante, a ferramenta usa as 5 últimas leituras reais
do banco para calcular médias e desvios móveis e codifica fabricante e modelo — eliminando a aproximação “valor
pontual” quando há histórico (cenário C8). Para valores avulsos, mantém a aproximação da Sprint 2.</li>
<li><b>Detector de anomalias</b>: mesma lógica do agente da Sprint 3 (features de janela aproximadas pelo valor
pontual; impacto quantificado na Sprint 3: Spearman 0,89–0,92), mesmos limiares e mesma regra de severidade.</li>
<li><b>Resultados históricos</b>: para períodos e ciclos do FZ-ATV-01, o assistente usa os scores calculados com
features completas em <code>scores_anomalias.csv</code>, e não a aproximação.</li>
<li>O laço do modo LLM processa <b>todas</b> as chamadas de ferramenta de um turno (validado no teste com dublê, seção 7.4).</li>
</ul>
""")

# ─── 4. MODELOS ──────────────────────────────────────────────────────────────
secoes.append("""
<h1 id="s4">4. Modelos de inteligência artificial</h1>
<p>Os modelos foram desenvolvidos e avaliados nas Sprints 2 e 3 (relatórios e notebooks em <code>sprint2/</code> e
<code>sprint3/</code>). Esta seção consolida variáveis, preparação, treinamento, métricas e justificativas. Na Sprint 4
os modelos <b>não foram retreinados</b>; foram integrados ao assistente.</p>

<h2>4.1 Classificação de falhas — Random Forest (Sprint 2, dados SINTÉTICOS)</h2>
<table><tr><th>Item</th><th>Descrição</th></tr>
<tr><td>Tarefa</td><td>Classificação multiclasse: Normal, Desbalanceamento, Superaquecimento, Falha mecânica.</td></tr>
<tr><td>Variáveis (14)</td><td>4 sensores + 4 médias móveis (5 leituras) + 4 desvios móveis (5 leituras) + fabricante e modelo codificados.</td></tr>
<tr><td>Preparação</td><td>Sem nulos; outliers preservados (são o sinal de falha); <code>class_weight='balanced'</code> em vez de SMOTE para não cruzar fronteiras temporais.</td></tr>
<tr><td>Divisão</td><td>Temporal por motor: 1.200 primeiras leituras para treino (24.000) e 300 últimas para teste (6.000).</td></tr>
<tr><td>Hiperparâmetros</td><td>200 árvores, <code>max_depth=20</code>, <code>min_samples_leaf=5</code>, <code>random_state=42</code>.</td></tr>
<tr><td>Comparação</td><td>Regressão Logística (baseline linear): F1-Macro 0,808 contra 0,955 do Random Forest.</td></tr>
</table>
<table><tr><th>Classe</th><th>Precisão</th><th>Recall</th><th>F1</th><th>Suporte</th></tr>
<tr><td>Normal</td><td>0,994</td><td>0,999</td><td>0,997</td><td>5.357</td></tr>
<tr><td>Desbalanceamento</td><td>0,968</td><td>0,882</td><td>0,923</td><td>203</td></tr>
<tr><td>Superaquecimento</td><td>1,000</td><td>0,947</td><td>0,973</td><td>131</td></tr>
<tr><td>Falha mecânica</td><td>0,934</td><td>0,922</td><td>0,928</td><td>309</td></tr>
<tr><td><b>F1-Macro / Acurácia</b></td><td colspan="4"><b>0,955 / 0,990</b> · AUC-ROC macro 0,983 · gap treino–teste 4,2 p.p.</td></tr>
</table>
<p><b>Justificativa.</b> Robusto a escalas, lida bem com ruído tabular, oferece importância das features (as médias
móveis dominam, confirmando o valor do sinal temporal). <b>Erros</b>: 59 de 6.000, concentrados no início da rampa de
deterioração e na confusão Desbalanceamento × Falha mecânica (17 casos). <b>Restrição de uso</b>: não se aplica ao
FZ-ATV-01, que não mede rotação nem corrente e não tem rótulos.</p>

<h2>4.2 Baseline operacional (Sprint 3, dados REAIS)</h2>
<ul>
<li><b>Limites por estado</b>: média e desvio de cada sensor calculados separadamente para repouso e operação
(limiar 0,5 mm/s, validado por K-Means e GMM com 90–91% de concordância); alerta acima de 3σ.</li>
<li><b>Consistência cruzada</b>: diferença P1−P2 de −0,119 ± 0,211 mm/s em velocidade e −5,46 ± 1,58 °C em temperatura.</li>
<li><b>Perfil de ciclo</b> (ciclos 1–5): duração 2,95 ± 1,31 min; o Ciclo 6 (17,4 min) desvia cerca de 11σ.</li>
</ul>

<h2>4.3 Detecção de anomalias — Isolation Forest e Autoencoder (Sprint 3, dados REAIS)</h2>
<table><tr><th>Item</th><th>Isolation Forest</th><th>Autoencoder</th></tr>
<tr><td>Paradigma</td><td>Não supervisionado, 100% do histórico</td><td>Semissupervisionado, treinado sem o Ciclo 6</td></tr>
<tr><td>Entrada</td><td colspan="2">28 features padronizadas: 6 sensores, médias e desvios móveis (5), taxas de variação, diferenças P1−P2, estado e intervalo entre leituras</td></tr>
<tr><td>Configuração</td><td><code>contamination=0,05</code></td><td>28 → 16 → 6 → 16 → 28, ReLU, 200 épocas; limiar = P95 do erro de treino (0,229)</td></tr>
<tr><td>Score</td><td>−decision_function</td><td>Erro quadrático médio de reconstrução</td></tr>
</table>
<p><b>Avaliação sem rótulos.</b> Como não há falhas confirmadas, a Sprint 3 usou o Ciclo 6 como pseudo-rótulo fraco
(2.028 de 7.183 leituras), além de análise visual, ranking de ciclos e concordância entre métodos.</p>
<table><tr><th>Método</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
<tr><td>Isolation Forest sem o Ciclo 6 no treino</td><td>0,975</td><td>0,865</td></tr>
<tr><td>Autoencoder sem o Ciclo 6 no treino</td><td>0,942</td><td>0,769</td></tr>
<tr><td>Isolation Forest com 100% dos dados</td><td>0,673</td><td>0,357</td></tr>
<tr><td>Baseline estatístico 3σ</td><td>0,527</td><td>0,303</td></tr>
</table>
<p><b>Achado central.</b> Treinado com todo o histórico, o Isolation Forest não isola o Ciclo 6: suas 2.028 leituras
semelhantes formam um agrupamento denso próprio (anomalia coletiva). O teste <i>leave-one-cycle-out</i> mostrou que só o
Ciclo 6, o de maior volume, é mascarado. A curadoria do conjunto de treino é tão determinante quanto o algoritmo.
<b>Explicabilidade</b>: <code>diff_temp</code> (diferença de temperatura entre portas) é a feature dominante nos dois
métodos de atribuição — base do procedimento DOC-07. <b>Robustez</b>: ROC-AUC do Autoencoder entre 0,877 e 0,960 para
gargalos de 3 a 14 neurônios; razão perda validação/treino de 0,87.</p>
<p><b>Severidade no assistente</b>: ALTA quando os dois modelos sinalizam, MODERADA quando um sinaliza, BAIXA quando nenhum.
A divergência (MODERADA com só o Autoencoder) é esperada em padrões como o do Ciclo 6.</p>
""")

# ─── 5. RAG ──────────────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s5">5. Arquitetura RAG</h1>
<p>A camada RAG fornece ao assistente o contexto que os modelos não têm: procedimentos, fichas técnicas, regras de
segurança, eventos e ordens de serviço. Ela combina <b>recuperação textual</b> (documentos e registros indexados) com
<b>consultas estruturadas</b> (ferramentas que leem dados e executam modelos).</p>
<h2>5.1 Preparação e indexação dos documentos</h2>
<ol>
<li><b>Leitura</b>: cada <code>DOC-*.md</code> é separado em cabeçalho de metadados e corpo.</li>
<li><b>Divisão em trechos (chunking) por seção</b>: cada seção <code>##</code> vira um trecho (54 no total). Seções são
curtas e autocontidas (sintomas, verificações, ações, critério de escalonamento), o que evita cortar procedimentos ao
meio. O texto indexado recebe o título do documento e da seção como prefixo, para dar contexto à busca.</li>
<li><b>Registros como trechos</b>: cada evento de falha (30), ciclo operacional (6) e ordem de serviço (40) vira um trecho
em linguagem natural, com ativo e intervalo de tempo como metadados — total de <b>130 trechos</b>.</li>
<li><b>Metadados</b> de cada trecho: <code>id</code>, <code>tipo_fonte</code> (documento, evento_falha, ciclo_operacional,
ordem_servico), <code>doc_id</code>, <code>titulo</code>, <code>secao</code>, <code>ativos</code>, <code>inicio</code>,
<code>fim</code>, <code>origem</code> e <code>arquivo</code>.</li>
<li><b>Vetorização</b>: texto normalizado (minúsculas, sem acentos); dois índices TF-IDF — palavras (uni e bigramas,
3.019 termos) e caracteres (3 a 5-gramas dentro de palavras, 9.973 termos) — salvos em <code>indice/indice_rag.joblib</code>.</li>
</ol>
<h2>5.2 Recuperação do contexto</h2>
<p>Score = 0,3 × cosseno(palavras) + 0,7 × cosseno(caracteres). Os n-gramas de caracteres toleram flexões e erros
(“rolamento/rolamentos”, “superaquecimento/superaquecer”); os de palavras preservam termos técnicos exatos (ISO, LOTO).
Os pesos foram escolhidos por busca em grade (0 a 0,6) no conjunto de avaliação; variações entre 0,1 e 0,5 diferem em
no máximo uma pergunta (seção 7.3). Trechos abaixo do score mínimo (0,12) são descartados — é isso que permite ao
assistente reconhecer quando não há contexto.</p>
<h2>5.3 Filtros por ativo, período e tipo</h2>
<ul>
<li><b>Ativo</b>: só passam trechos cujo campo <code>ativos</code> contém o ativo da pergunta ou “todos”. Assim, a ficha do
MTR-05 nunca aparece numa pergunta sobre o MTR-07, e eventos de outros motores não competem.</li>
<li><b>Período</b>: registros com intervalo de tempo precisam sobrepor o período pedido; documentos (atemporais) sempre passam.
Antes da busca, o orquestrador verifica a cobertura temporal do ativo e responde que não há dados se o período estiver fora dela.</li>
<li><b>Tipo</b>: documentos e registros são buscados separadamente, para que dezenas de OS parecidas não tirem espaço dos
procedimentos (efeito medido na seção 7.3).</li>
</ul>
<h2>5.4 Como dados operacionais e resultados dos modelos chegam ao assistente</h2>
<p>Dados numéricos não são recuperados por similaridade textual — seriam imprecisos (ex.: “ciclo 6” é lexicalmente quase
igual a “ciclo 3”). Eles chegam por <b>ferramentas determinísticas</b> que devolvem JSON estruturado:</p>
<table><tr><th>Ferramenta</th><th>Entrada</th><th>Saída principal</th></tr>
<tr><td><code>consultar_leituras</code></td><td>ativo, período, ciclo</td><td>mín./média/máx./última por sensor, leituras em falha, % em operação, cobertura</td></tr>
<tr><td><code>listar_eventos</code></td><td>ativo, período</td><td>eventos de falha (MTR) ou ciclos com % sinalizado (FZ)</td></tr>
<tr><td><code>historico_manutencao</code></td><td>ativo, período</td><td>ordens de serviço</td></tr>
<tr><td><code>resumo_anomalias</code></td><td>ativo FZ, período, ciclo</td><td>% sinalizado por modelo, leituras sinalizadas pelos dois, resumo por ciclo</td></tr>
<tr><td><code>avaliar_anomalia_sensor</code></td><td>6 leituras do FZ</td><td>estado, scores, severidade, z-scores vs. baseline</td></tr>
<tr><td><code>prever_falha_motor</code></td><td>4 leituras ou ativo MTR + instante</td><td>classe, confiança, probabilidades, rótulo real (se houver)</td></tr>
<tr><td><code>buscar_documentos</code></td><td>consulta, ativo, período, k, tipos</td><td>trechos com score e metadados</td></tr>
</table>
<p>No modo LLM o próprio modelo escolhe e encadeia as ferramentas (tool use); no modo offline o orquestrador as aciona
por regras. Em ambos, os resultados dos modelos também <b>direcionam a recuperação</b>: o diagnóstico ou a severidade são
acrescentados à consulta, trazendo o procedimento adequado.</p>
<h2>5.5 Modelos utilizados</h2>
<ul>
<li><b>Recuperação</b>: TF-IDF (scikit-learn) — sem modelo de embeddings, por rodar 100% local e pelo tamanho da base.</li>
<li><b>Geração (modo llm)</b>: Claude via API Anthropic; padrão <code>claude-sonnet-5-5</code>, configurável em
<code>ANTHROPIC_MODEL</code>; <code>max_tokens=1500</code>; até 8 rodadas de ferramentas por pergunta.</li>
<li><b>Geração (modo offline)</b>: templates em Python, determinísticos, usados nos testes.</li>
</ul>
<h2>5.6 Instruções de geração das respostas</h2>
<p>O prompt de sistema (<code>rag/prompts.py</code>) descreve os ativos e a natureza dos dados e impõe sete regras:</p>
<ol>
<li>Usar as ferramentas antes de responder (dados por ferramentas de dados; procedimentos por busca com filtro).</li>
<li>Responder somente com base nos resultados; não inventar valores, datas, OS ou procedimentos; citar fontes entre colchetes.</li>
<li>Pergunta ambígua: não chamar ferramentas de dados e pedir o ativo, listando as opções; indicar leituras faltantes.</li>
<li>Ausência de informação: dizer claramente, informar o que existe (ex.: cobertura) e não completar com conhecimento geral.</li>
<li>Segurança: não autorizar intervenções; recomendar o profissional responsável e citar DOC-08 em casos críticos.</li>
<li>Diferenciar dados reais de sintéticos/simulados; lembrar que anomalia não é diagnóstico de causa raiz.</li>
<li>Formato: português, objetivo; Resumo → Dados e modelos → Documentação → Recomendação → Atenção.</li>
</ol>
<h2>5.7 Apresentação das fontes</h2>
<p>A lista “Fontes consultadas” é montada <b>pelo sistema</b>, não pelo LLM: cada ferramenta devolve as fontes que usou
(arquivo de dados, modelo serializado ou trecho de documento com seção, origem e score). Assim o modelo de linguagem
não consegue citar uma fonte que não foi consultada. No texto, as citações seguem o padrão
<code>[DOC-03 §Verificações recomendadas]</code>; documentos simulados são marcados como tal. Na interface web, as
fontes ficam em um painel expansível sob cada resposta, junto com as ferramentas acionadas e seus argumentos.</p>
""")

# ─── 6. FUNCIONAL ────────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s6">6. Documentação funcional do assistente</h1>
<h2>6.1 Funcionalidades disponíveis</h2>
<table><tr><th>Tema</th><th>Exemplos de pergunta</th></tr>
<tr><td>Sensores</td><td>“Quais foram as leituras do MTR-12?” · “Como estavam as leituras do FZ-ATV-01 no ciclo 4?”</td></tr>
<tr><td>Falhas</td><td>“Quais falhas o MTR-07 apresentou?” · “Qual o diagnóstico do MTR-07 em 2023-01-04 06:00?”</td></tr>
<tr><td>Anomalias</td><td>“O que aconteceu no ciclo 6 do FZ-ATV-01?” · “Leitura do FZ-ATV-01: P1 6,9 mm/s 0,50 g 38 °C; P2 7,1 mm/s 0,52 g 42 °C. Isso é anômalo?”</td></tr>
<tr><td>Histórico de manutenção</td><td>“Qual o histórico de manutenção do MTR-03?”</td></tr>
<tr><td>Procedimentos técnicos</td><td>“Quais são os limites de vibração da ISO 10816 para base rígida?” · “Como investigar superaquecimento?”</td></tr>
</table>
<h2>6.2 Etapas de utilização da interface</h2>
<ol>
<li>Executar <code>streamlit run app.py</code> e abrir <code>http://localhost:8501</code>.</li>
<li>(Opcional) Escolher o ativo na barra lateral — usado quando a pergunta não cita um ativo. A barra também mostra o modo de geração.</li>
<li>Digitar a pergunta no campo de chat. Datas podem ser escritas como dd/mm/aaaa ou aaaa-mm-dd (com hora opcional).</li>
<li>Ler a resposta: ❓ indica pedido de esclarecimento, ℹ️ ausência de informação, ⚠️ necessidade de avaliação profissional.</li>
<li>Abrir “Fontes consultadas” e “Ferramentas acionadas” para auditar a resposta.</li>
<li>Usar a aba “Painel do ativo” para ver as séries de sensores e o erro do Autoencoder (FZ-ATV-01) ou os eventos (MTR).</li>
<li>“Limpar conversa” reinicia o contexto (inclusive o ativo lembrado).</li>
</ol>
<div class="duas">
<figure><img src="{RES / 'tela_ambigua.png'}"><figcaption>Figura 3 — Pergunta ambígua: o assistente pede o ativo.</figcaption></figure>
<figure><img src="{RES / 'tela_c3.png'}"><figcaption>Figura 4 — Sem informação: não há OS para o FZ-ATV-01.</figcaption></figure>
</div>
<h2>6.3 Tratamento de perguntas ambíguas</h2>
<ul>
<li><b>Ativo não informado</b> em pergunta que depende de dados → pede o ativo e lista as opções (sem consultar dados).
Se a conversa já citou um ativo, ele é reaproveitado e a resposta avisa: “Considerando o ativo X, citado na pergunta anterior”.</li>
<li><b>Mais de um ativo</b> na mesma pergunta → pede uma pergunta por ativo (comparação ainda não implementada).</li>
<li><b>Leituras incompletas</b> → informa quais variáveis faltam (6 para o FZ-ATV-01; 4 para motores).</li>
<li><b>Valor isolado</b> (“5,2 mm/s é problema?”) → apresenta a zona ISO para base rígida e flexível e pede ativo e demais leituras.</li>
<li><b>Diagnóstico sem instante</b> (“diagnóstico do MTR-07”) → pede o instante ou as leituras.</li>
</ul>
<h2>6.4 Tratamento de ausência de informações</h2>
<ul>
<li><b>Ferramenta sem dados</b> (ex.: nenhuma OS para o ativo) → declara a ausência e não infere datas ou ações.</li>
<li><b>Período fora da cobertura</b> → informa o intervalo disponível e não extrapola.</li>
<li><b>Nenhum trecho acima do score mínimo</b> e nenhum dado → mensagem padrão de informação insuficiente, com o escopo da base.</li>
<li><b>Fora do escopo</b> (preços, fornecedores, estoque) → informa que a base não contém dados comerciais.</li>
</ul>
<h2>6.5 Situações que exigem avaliação de profissional responsável</h2>
<p>O assistente acrescenta um bloco “ATENÇÃO — avaliação de profissional responsável”, citando DOC-08, quando:
a severidade de anomalia é ALTA; o classificador indica falha com confiança ≥ 50%; ou o usuário pergunta se pode continuar
operando, desligar, religar ou intervir. O bloco lembra que o assistente não autoriza intervenções e que é obrigatório o
bloqueio e etiquetagem (LOTO) antes de qualquer intervenção. Com confiança abaixo de 60%, a resposta também avisa que as
probabilidades estão divididas e que o resultado é uma hipótese a confirmar em campo.</p>
""")

# ─── 7. TESTES ───────────────────────────────────────────────────────────────
secoes.append(f"""
<h1 id="s7">7. Testes e resultados</h1>
<h2>7.1 Estratégia</h2>
<table><tr><th>Teste</th><th>Script</th><th>O que verifica</th><th>Resultado</th></tr>
<tr><td>Cenários ponta a ponta</td><td><code>testes/cenarios.py</code></td><td>13 cenários com verificação automática de tipo de resposta, ferramentas, conteúdo e fontes</td><td class="ok">13/13 aprovados</td></tr>
<tr><td>Qualidade da recuperação</td><td><code>testes/avaliar_recuperacao.py</code></td><td>24 perguntas rotuladas; Hit@1, Hit@3, MRR@5</td><td>Hit@1 {br(rec['hibrido + filtro + tipo']['hit@1'])} na configuração do assistente</td></tr>
<tr><td>Laço do modo LLM</td><td><code>testes/teste_modo_llm_mock.py</code></td><td>Tool use com chamadas múltiplas, retorno dos resultados, coleta de fontes (cliente simulado)</td><td class="ok">5/5 verificações</td></tr>
<tr><td>Interface</td><td>execução manual + capturas</td><td>Chat, fontes expansíveis, esclarecimento</td><td>Figuras 3–5</td></tr>
</table>
<div class="alerta"><b>Modo de execução dos testes.</b> Todos os cenários rodaram no modo <b>offline</b>
(sem chave de API), o que os torna reprodutíveis. As saídas abaixo são cópias literais de
<code>resultados/cenarios.json</code>. A qualidade do texto gerado pelo LLM não foi avaliada nesta entrega
(pendência P2, capítulo 9). Tempos medidos em um único processo: o primeiro uso de cada modelo inclui o carregamento
dos artefatos (≈0,5 s para os scores; ≈1,2 s para o PyTorch); consultas seguintes levam poucos milissegundos.</div>

<h2>7.2 Cenários completos</h2>
{cenario("C1", "Cenário 1 — Consulta sobre falha ou anomalia (obrigatório)",
         "Correto. O assistente filtrou o ativo e o Ciclo 6 a partir do texto da pergunta, usou os scores calculados com features completas e explicou a divergência entre modelos "
         "(53,5% das leituras sinalizadas pelo Autoencoder contra 5,8% pelo Isolation Forest), reproduzindo o achado da "
         "Sprint 3. A recuperação trouxe DOC-06 (interpretação) e DOC-07 (assimetria térmica), coerente com a "
         "explicabilidade por <code>diff_temp</code>. Ponto de atenção: DOC-07 é simulado — a resposta marca isso.")}
<figure><img src="{RES / 'tela_c1.png'}" style="width:88%"><figcaption>Figura 5 — Cenário 1 na interface web; fontes e ferramentas ficam em painéis expansíveis sob a resposta.</figcaption></figure>
{cenario("C2", "Cenário 2 — Consulta que combina dados operacionais e documentação técnica (obrigatório)",
         "Correto. O evento do banco (Superaquecimento, 03/01 20:10 a 04/01 07:30, 113,4 °C, 20,58 A) direcionou a "
         "consulta à documentação: o termo “troubleshooting Superaquecimento” foi acrescentado automaticamente e os "
         "quatro trechos recuperados são do procedimento DOC-03. Os valores do evento confirmam a assinatura descrita "
         "no documento (temperatura e corrente altas, vibração baixa — 2,63 mm/s).")}
{cenario("C3", "Cenário 3 — Consulta sem informações suficientes (obrigatório)",
         "Correto. A ferramenta de histórico retornou zero ordens para o FZ-ATV-01 e o assistente declarou a ausência sem "
         "inventar data. A busca recuperou a seção da ficha técnica que registra que nenhum histórico foi fornecido "
         "(DOC-05). Ressalva: os trechos de DOC-04 que aparecem em seguida são procedimentos genéricos de troca de "
         "rolamento — úteis, mas poderiam confundir um leitor apressado; o rótulo “documento SIMULADO” ajuda a separar.")}

<h2>7.3 Demais cenários</h2>
<table><tr><th>ID</th><th>Categoria</th><th>Entrada (último turno)</th><th>Tipo de resposta</th><th>Status</th></tr>{tab_cen}</table>
<p>Destaques: <b>C4</b> pede o ativo e, no turno seguinte, responde com leituras e o evento de falha mecânica do MTR-12;
<b>C5</b> classifica “Falha Mecanica” com 58% de confiança (Superaquecimento 35%), avisa a baixa confiança e escalona
para o responsável técnico em vez de responder se é possível continuar operando; <b>C7</b> reproduz o resultado da
Sprint 3 para o padrão do Ciclo 6 (severidade MODERADA — Autoencoder com erro 0,759 acima do limiar 0,229 e Isolation Forest não
sinalizando); <b>C8</b> usa a janela real do banco e acerta o rótulo (Superaquecimento, confiança 100%); <b>C13</b>
registra uma limitação conhecida (comparação entre ativos).</p>

<h2>7.4 Avaliação da recuperação</h2>
<p>Conjunto de 24 perguntas escritas e rotuladas pela equipe (procedimentos, fichas, eventos, OS e ciclos). Hit@k indica se
um trecho relevante está entre os k primeiros; MRR@5 é a média do inverso da posição do primeiro relevante.</p>
<table><tr><th>Configuração</th><th>Hit@1</th><th>Hit@3</th><th>MRR@5</th></tr>{tab_rec}</table>
<figure><img src="{RES / 'grafico_recuperacao.png'}" style="width:92%"><figcaption>Figura 6 — Efeito do tipo de
representação e dos filtros sobre a recuperação.</figcaption></figure>
<p><b>Análise.</b> (1) O <b>filtro por ativo</b> é a decisão de maior impacto: +17 p.p. de Hit@1 no híbrido. (2) A
<b>separação por tipo de fonte</b>, usada pelo assistente, acrescenta +8 p.p., porque 40 ordens de serviço com texto
parecido (“balanceamento dinâmico”) deslocavam o procedimento DOC-02. (3) N-gramas de caracteres superam palavras isoladas
em português; o híbrido (0,3/0,7) fica uma pergunta abaixo do só-caracteres com filtro — diferença dentro do ruído
de 24 perguntas, mantida para preservar termos exatos. (4) Erros remanescentes na configuração final: “vibração alta com temperatura
normal” (exige raciocínio sobre sintomas, não sobreposição lexical — típico caso para embeddings), “Porta 2 mais quente”
(DOC-07 em 2º lugar, após a ficha que descreve o offset) e “ciclo mais longo com temperatura alta” (TF-IDF não ordena
valores numéricos; no assistente essa pergunta é atendida pela ferramenta de ciclos). <b>Ressalva</b>: o conjunto
é pequeno e foi usado também para escolher os pesos; os números indicam tendência, não desempenho em produção.</p>

<h2>7.5 Teste do modo LLM com cliente simulado</h2>
<pre>{e((RES / 'teste_modo_llm_mock.txt').read_text(encoding='utf-8').split(chr(10) + chr(10) + 'Resposta')[0])}</pre>
<p>O teste substitui o SDK da Anthropic por um dublê que pede duas ferramentas no mesmo turno e confirma que ambas são
executadas, que os dois resultados voltam ao modelo e que as fontes são coletadas. Ele valida a integração, não a qualidade
do texto do LLM.</p>

<h2>7.6 Pendências identificadas nos testes</h2>
<ul>
<li>Comparação entre ativos em uma única pergunta (C13) — não implementada.</li>
<li>Avaliação do modo LLM com a API real (fidelidade às fontes, taxa de alucinação) — não executada.</li>
<li>Recuperação semântica para perguntas descritas por sintomas — pior caso da avaliação.</li>
</ul>
""")

# ─── 8. MANUAL ───────────────────────────────────────────────────────────────
secoes.append("""
<h1 id="s8">8. Manual de instalação e execução</h1>
<h2>8.1 Pré-requisitos</h2>
<ul>
<li>Python 3.11 ou superior (testado em 3.13.18), pip e cerca de 2 GB livres (PyTorch).</li>
<li>Sistema operacional: Linux, macOS ou Windows. Não exige GPU.</li>
<li>Opcional: chave da API Anthropic para o modo LLM. Sem ela, tudo funciona no modo offline.</li>
</ul>
<h2>8.2 Dependências</h2>
<table><tr><th>Pacote</th><th>Versão</th><th>Uso</th></tr>
<tr><td>scikit-learn</td><td>1.8.0 (fixa)</td><td>Random Forest, Isolation Forest, scaler e TF-IDF; os <code>.joblib</code> foram serializados nesta versão</td></tr>
<tr><td>numpy, pandas, joblib</td><td>≥ 2.0 / 2.2 / 1.4</td><td>Dados e serialização</td></tr>
<tr><td>torch</td><td>≥ 2.2 (CPU)</td><td>Autoencoder</td></tr>
<tr><td>anthropic</td><td>≥ 0.40</td><td>Modo LLM</td></tr>
<tr><td>streamlit</td><td>≥ 1.40</td><td>Interface web</td></tr>
<tr><td>matplotlib</td><td>≥ 3.8</td><td>Gráficos da avaliação</td></tr>
</table>
<h2>8.3 Instalação</h2>
<pre>git clone &lt;url-do-repositorio&gt; forzy-assistente     # ou descompacte forzy-assistente.zip
cd forzy-assistente
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt</pre>
<h2>8.4 Variáveis de ambiente</h2>
<p>Copie <code>.env.example</code> para <code>.env</code> (lido automaticamente por <code>rag/config.py</code>) ou exporte as
variáveis no terminal. O arquivo <code>.env</code> está no <code>.gitignore</code> — <b>nunca versione a chave</b>.</p>
<table><tr><th>Variável</th><th>Padrão</th><th>Descrição</th></tr>
<tr><td><code>ANTHROPIC_API_KEY</code></td><td>vazio</td><td>Chave da API. Vazia = modo offline.</td></tr>
<tr><td><code>ANTHROPIC_MODEL</code></td><td><code>claude-sonnet-5-5</code></td><td>Modelo usado no modo LLM.</td></tr>
<tr><td><code>FORZY_MODO</code></td><td><code>auto</code></td><td><code>auto</code> (LLM se houver chave), <code>llm</code> ou <code>offline</code>.</td></tr>
<tr><td><code>RAG_TOP_K</code></td><td>4</td><td>Trechos de documentação por resposta.</td></tr>
<tr><td><code>RAG_MIN_SCORE</code></td><td>0,12</td><td>Similaridade mínima para aceitar um trecho.</td></tr>
<tr><td><code>FORZY_BASE_DIR</code></td><td>raiz do repositório</td><td>Para executar com os dados em outro diretório.</td></tr>
</table>
<p><b>Serviço externo (API Anthropic).</b> Crie a chave no console da Anthropic, defina-a em <code>ANTHROPIC_API_KEY</code>
e confirme que a rede permite HTTPS para <code>api.anthropic.com</code>. Os dados enviados à API são a pergunta e os
resultados das ferramentas (estatísticas e trechos), não os arquivos completos. Se a chamada falhar, o assistente responde
no modo offline e avisa.</p>
<h2>8.5 Preparação dos dados</h2>
<pre>python -m rag.preparar_base</pre>
<p>Gera <code>conhecimento/gerado/eventos_falha_mtr.csv</code>, <code>ciclos_fz.csv</code>,
<code>conhecimento/historico_manutencao.csv</code>, <code>DOC-09</code> e <code>indice/indice_rag.joblib</code>
(saída esperada: 30 eventos, 6 ciclos, 40 OS, 130 trechos). Repita sempre que alterar documentos.
Para recriar a base sintética: <code>cd sprint2 &amp;&amp; python gerar_banco.py</code>. Para reprocessar os dados reais é
necessário o arquivo bruto <code>forzy_history.csv</code> e os notebooks da Sprint 3.</p>
<h2>8.6 Inicialização</h2>
<pre>streamlit run app.py                                    # interface web → http://localhost:8501
python cli.py                                           # conversa no terminal
python cli.py --debug "Quais falhas o MTR-07 apresentou?" # pergunta única, mostrando as ferramentas
python cli.py --modo offline "..."                      # força o modo offline</pre>
<h2>8.7 Reprodução dos testes</h2>
<pre>python -m testes.cenarios              # → resultados/cenarios.json e cenarios_log.md
python -m testes.avaliar_recuperacao   # → resultados/avaliacao_recuperacao.json e grafico_recuperacao.png
python -m testes.teste_modo_llm_mock   # valida o laço de tool use
python docs/gerar_documento.py         # regenera este PDF com os resultados mais recentes (requer weasyprint)</pre>
<h2>8.8 Problemas comuns</h2>
<table><tr><th>Sintoma</th><th>Causa / solução</th></tr>
<tr><td><code>Índice não encontrado</code></td><td>Execute <code>python -m rag.preparar_base</code>.</td></tr>
<tr><td><code>InconsistentVersionWarning</code> do scikit-learn</td><td>Versão diferente de 1.8.0; reinstale com <code>pip install scikit-learn==1.8.0</code>.</td></tr>
<tr><td>Resposta com “(Modo LLM indisponível …)”</td><td>Chave inválida, sem rede ou modelo inexistente; verifique <code>ANTHROPIC_API_KEY</code> e <code>ANTHROPIC_MODEL</code>.</td></tr>
<tr><td>Primeira resposta lenta (~1–2 s)</td><td>Carregamento do PyTorch e dos artefatos; as seguintes são rápidas.</td></tr>
</table>
""")

# ─── 9. LIMITAÇÕES ───────────────────────────────────────────────────────────
secoes.append("""
<h1 id="s9">9. Limitações e continuidade</h1>
<h2>9.1 Limitações</h2>
<table><tr><th>Área</th><th>Limitação</th><th>Consequência</th></tr>
<tr><td rowspan="3">Dados</td><td>Um único ativo real, ~4 h, sem rótulos de falha nem metadados</td><td>Baseline e limiares refletem poucas condições de operação; nenhuma métrica contra falha confirmada</td></tr>
<tr><td>Motores, falhas e OS sintéticos/simulados</td><td>Respostas sobre MTR demonstram o fluxo, não a realidade da Forzy</td></tr>
<tr><td>Procedimentos simulados (DOC-01 a DOC-04, DOC-07, DOC-08)</td><td>Não devem ser usados em campo sem validação técnica</td></tr>
<tr><td rowspan="3">Modelos</td><td>Classificador treinado em dados sintéticos e incompatível com o schema do ativo real</td><td>Não há classificação de tipo de falha para o FZ-ATV-01</td></tr>
<tr><td>Consulta avulsa de anomalia aproxima janelas móveis pelo valor pontual</td><td>Reduz o sinal (ex.: −27,6% no erro do Ciclo 6); leituras perto do limiar podem mudar de decisão</td></tr>
<tr><td>Autoencoder e IF semissupervisionado dependem da curadoria do treino (Ciclo 6 excluído)</td><td>Retreinar sem curadoria pode mascarar anomalias longas</td></tr>
<tr><td rowspan="3">Recuperação</td><td>TF-IDF lexical, sem embeddings</td><td>Falha em perguntas descritas por sintomas ou sinônimos (seção 7.4)</td></tr>
<tr><td>Avaliação com 24 perguntas, também usadas para ajustar pesos</td><td>Métricas otimistas; precisam de conjunto independente</td></tr>
<tr><td>Extração de ativo e período por regras (regex)</td><td>Formatos não previstos (“semana passada”, “ontem”) não são reconhecidos</td></tr>
<tr><td rowspan="3">Assistente</td><td>Modo LLM não avaliado com a API real</td><td>Fidelidade e taxa de alucinação desconhecidas</td></tr>
<tr><td>Modo offline baseado em palavras-chave</td><td>Intenções fora do vocabulário podem não ser detectadas</td></tr>
<tr><td>Sem comparação entre ativos, sem autenticação, sem dados em tempo real</td><td>Uso restrito a protótipo/consulta histórica</td></tr>
</table>
<h2>9.2 Problemas conhecidos</h2>
<ul>
<li>Números são exibidos com ponto decimal (padrão Python) no modo offline.</li>
<li>Inconsistências da base sintética (WEG/Weg; datas de instalação posteriores ao início das leituras) aparecem nas fichas.</li>
<li>Perguntas com um único número sobre vibração e sem ativo são sempre tratadas pela tabela ISO, mesmo que o usuário cite outro contexto.</li>
<li>O histórico de conversa do modo LLM é truncado nas últimas 12 mensagens.</li>
</ul>
<h2>9.3 Condições de uso</h2>
<ul>
<li>Ferramenta de <b>apoio à investigação e priorização</b>; não substitui inspeção nem autoriza intervenções.</li>
<li>Scores de anomalia indicam desvio estatístico do histórico, não causa raiz.</li>
<li>Resultados sobre motores MTR e procedimentos simulados servem apenas para demonstração.</li>
<li>Toda intervenção segue as regras de segurança da Forzy (NR-10, NR-12, bloqueio e etiquetagem).</li>
</ul>
<h2>9.4 Melhorias propostas e prioridades</h2>
<table><tr><th>Prioridade</th><th>Ação</th><th>Justificativa</th></tr>
<tr><td><b>P1 — imediata</b></td><td>Substituir documentos simulados por manuais, POPs e normas oficiais da Forzy; validar DOC-08 com segurança do trabalho</td><td>Requisito para qualquer uso real</td></tr>
<tr><td><b>P1</b></td><td>Obter mais histórico real (vários ativos, semanas) e ordens de serviço reais com causa confirmada</td><td>Base para recalibrar o baseline e criar os primeiros rótulos</td></tr>
<tr><td><b>P2</b></td><td>Avaliar o modo LLM com a API: fidelidade às fontes, citações corretas, recusa em perguntas sem informação</td><td>Única parte implementada ainda sem evidência de qualidade</td></tr>
<tr><td><b>P2</b></td><td>Recuperação híbrida com embeddings multilíngues + reranqueamento; conjunto de avaliação independente (≥100 perguntas)</td><td>Corrige o pior tipo de erro observado</td></tr>
<tr><td><b>P2</b></td><td>Pipeline de streaming com janelas móveis reais para o detector de anomalias</td><td>Elimina a aproximação da consulta avulsa</td></tr>
<tr><td><b>P3</b></td><td>Retreinar um classificador supervisionado no schema real quando houver rótulos (pipeline proposto na Sprint 3)</td><td>Diagnóstico de tipo de falha para ativos reais</td></tr>
<tr><td><b>P3</b></td><td>Comparação entre ativos, alertas proativos, autenticação e registro de feedback dos técnicos</td><td>Evolução de produto</td></tr>
</table>
""")

# ─── 10. ORGANIZAÇÃO ─────────────────────────────────────────────────────────
secoes.append("""
<h1 id="s10">10. Organização da entrega final</h1>
<p>A entrega é composta por este documento em PDF e pelo código-fonte na pasta <code>forzy-assistente/</code>
(arquivo <code>forzy-assistente.zip</code>), que contém o <code>README.md</code> com visão geral, estrutura e instruções.</p>
<pre>forzy-assistente/
├── README.md · requirements.txt · .env.example · .gitignore
├── app.py · cli.py
├── rag/            config · preparar_base · texto · recuperador · ferramentas · prompts · assistente
├── conhecimento/   documentos/DOC-01…09.md · historico_manutencao.csv · gerado/
├── indice/         indice_rag.joblib
├── sprint2/        motor.db · gerar_banco.py · modelo_falhas.joblib · notebooks · BANCO.md · agente original
├── sprint3/        modelos de anomalia · baseline · scores · notebooks · FORZY.md · agente v2 original
├── testes/         cenarios.py · avaliar_recuperacao.py · teste_modo_llm_mock.py
├── resultados/     cenarios.json · cenarios_log.md · avaliacao_recuperacao.json · gráficos · capturas de tela
└── docs/           Documentacao_Final_Sprint4_Forzy.pdf · gerar_documento.py · arquitetura.dot · figuras/</pre>
<table><tr><th>Material citado</th><th>Onde está</th></tr>
<tr><td>Registros completos dos 13 cenários</td><td><code>resultados/cenarios_log.md</code> e <code>cenarios.json</code></td></tr>
<tr><td>Detalhe da avaliação de recuperação (top-5 por pergunta)</td><td><code>resultados/avaliacao_recuperacao.json</code></td></tr>
<tr><td>Capturas de tela da interface</td><td><code>resultados/tela_*.png</code></td></tr>
<tr><td>Relatórios das Sprints 2 e 3 e notebooks</td><td><code>sprint2/</code>, <code>sprint3/</code> (notebooks executados)</td></tr>
<tr><td>Diagrama de arquitetura editável</td><td><code>docs/arquitetura.dot</code> (Graphviz)</td></tr>
</table>
<div class="nota"><b>Pendente para a equipe antes do envio:</b> publicar a pasta em um repositório (GitHub) acessível aos
avaliadores e substituir <code>&lt;url-do-repositorio&gt;</code> no README e na seção 8.3; o arquivo bruto
<code>forzy_history.csv</code> não estava no pacote da Sprint 3 recebido e deve ser incluído no repositório se a Forzy autorizar.</div>
""")

doc = f"<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(secoes)}</body></html>"
saida_pdf = RAIZ / "docs" / "Documentacao_Final_Sprint4_Forzy.pdf"
HTML(string=doc, base_url=str(RAIZ)).write_pdf(saida_pdf)
print(f"PDF gerado: {saida_pdf}")
