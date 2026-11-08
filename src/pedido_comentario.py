"""Prepara o texto que o Claude recebe: as instruções e os números do dia.

O Claude não lê ficheiros. Recebe só este texto e devolve o comentário, por
isso não consegue chegar a mais nada no computador onde corre.
"""
import json
import sys

from comum import FICHEIRO_STATS, RAIZ, ler_json


def principal():
    stats = ler_json(FICHEIRO_STATS)
    stats.get("titulo", {}).pop("evolucao", None)  # o histórico dia a dia não faz falta ao comentário
    instrucoes = (RAIZ / "prompts" / "comentario.md").read_text(encoding="utf-8").strip()
    # Impede que um nome vindo da ESPN consiga fechar a zona dos dados.
    dados = json.dumps(stats, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{instrucoes}\n\n<dados>\n{dados}\n</dados>")


if __name__ == "__main__":
    principal()
