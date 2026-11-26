"""
cli.py — Interface de linha de comando do Assistente de Manutenção Forzy.

Uso:
    python cli.py                      # conversa interativa
    python cli.py "pergunta"           # pergunta única
    python cli.py --modo offline ...   # força o modo sem LLM
"""
import argparse

from rag.assistente import Assistente


def main():
    ap = argparse.ArgumentParser(description="Assistente de Manutenção Forzy")
    ap.add_argument("pergunta", nargs="*", help="Pergunta única (opcional)")
    ap.add_argument("--modo", choices=["auto", "llm", "offline"], default=None)
    ap.add_argument("--debug", action="store_true", help="Mostra as ferramentas acionadas")
    args = ap.parse_args()
    assistente = Assistente(modo=args.modo)

    def perguntar(q):
        r = assistente.responder(q)
        print(f"\nAssistente [{r.modo} | {r.tipo}]:\n{r.formatada()}\n")
        if args.debug:
            for f in r.ferramentas:
                print(f"   ↳ {f['ferramenta']}({f['argumentos']})")
        print("-" * 70)

    if args.pergunta:
        perguntar(" ".join(args.pergunta))
        return
    print(f"Assistente de Manutenção Forzy — modo {assistente.modo}. Digite 'sair' para encerrar.\n")
    while True:
        try:
            q = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"sair", "exit", "quit"}:
            break
        if q:
            perguntar(q)


if __name__ == "__main__":
    main()
