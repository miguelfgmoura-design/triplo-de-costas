"""Diz se a atualização do último dia fechado já foi feita (código 0) ou se falta (código 1).

As corridas de reserva da manhã usam isto para não repetirem o trabalho.
"""
import sys
from datetime import date, timedelta

from comum import DADOS, FICHEIRO_ATUAL, ler_json, ultimo_dia_fechado


def ja_atualizado():
    liga = ler_json(FICHEIRO_ATUAL)["liga"]
    fim_da_epoca = date.fromisoformat(liga["primeiro_dia"]) + timedelta(days=liga["periodo_final"] - 1)
    dia = min(ultimo_dia_fechado(), fim_da_epoca).isoformat()
    return liga["ultimo_fechado"] == dia and (DADOS / "comentarios" / f"{dia}.md").exists()


if __name__ == "__main__":
    sys.exit(0 if ja_atualizado() else 1)
