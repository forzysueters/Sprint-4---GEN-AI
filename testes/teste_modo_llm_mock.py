"""
teste_modo_llm_mock.py — Verifica o laço de tool use do modo LLM sem chamar a API.

Substitui o cliente Anthropic por um dublê que devolve, em sequência:
  1) duas chamadas de ferramenta no MESMO turno (resumo_anomalias + buscar_documentos),
  2) uma resposta final em texto.
Confere que as duas ferramentas foram executadas, que os resultados voltaram ao
modelo e que as fontes foram coletadas pelo sistema.

Observação: este teste valida a integração (código), não a qualidade do texto do LLM.

Uso:
    python -m testes.teste_modo_llm_mock
"""
import sys
import types
from types import SimpleNamespace as NS

chamadas = []


class FakeMessages:
    def __init__(self):
        self.n = 0

    def create(self, **kw):
        chamadas.append(kw)
        self.n += 1
        if self.n == 1:
            return NS(stop_reason="tool_use", content=[
                NS(type="text", text="Vou consultar os dados."),
                NS(type="tool_use", id="t1", name="resumo_anomalias", input={"ativo": "FZ-ATV-01", "ciclo": 6}),
                NS(type="tool_use", id="t2", name="buscar_documentos",
                   input={"consulta": "divergência isolation forest autoencoder", "ativo": "FZ-ATV-01"}),
            ])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="Resumo: o Ciclo 6 ... [DOC-06]")])


class FakeAnthropic:
    def __init__(self, *a, **k):
        self.messages = FakeMessages()


sys.modules["anthropic"] = types.SimpleNamespace(Anthropic=FakeAnthropic)

from rag.assistente import Assistente  # noqa: E402


def main():
    r = Assistente(modo="llm").responder("O ciclo 6 do FZ-ATV-01 foi anômalo?")
    usadas = [f["ferramenta"] for f in r.ferramentas]
    retorno = next(m["content"] for m in chamadas[1]["messages"]
                   if m["role"] == "user" and isinstance(m["content"], list))
    checks = {
        "modo llm": r.modo == "llm",
        "duas ferramentas executadas no mesmo turno": usadas == ["resumo_anomalias", "buscar_documentos"],
        "dois tool_result devolvidos ao modelo": [b["tool_use_id"] for b in retorno] == ["t1", "t2"],
        "fontes coletadas pelo sistema": any("scores_anomalias" in f for f in r.fontes)
        and any("DOC-" in f for f in r.fontes),
        "system prompt e tools enviados": "Assistente de Manutenção da Forzy" in chamadas[0]["system"]
        and len(chamadas[0]["tools"]) == 7,
    }
    for k, v in checks.items():
        print(f"[{'OK' if v else 'FALHA'}] {k}")
    print("\nResposta formatada:\n" + r.formatada())
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
