"""Diz se há trabalho a fazer agora (código 1) ou não (código 0).

O GitHub entrega as corridas agendadas com horas de atraso e sem hora certa.
Por isso o agendamento tenta de hora a hora, e é este ficheiro que decide:
só há trabalho depois das 9h de Lisboa e enquanto a atualização do dia faltar.
"""
import sys
from datetime import date, time, timedelta

from comum import DADOS, FICHEIRO_ATUAL, LISBOA, agora_utc, ler_json, ultimo_dia_fechado

# Antes desta hora a ESPN pode ainda não ter fechado os números da noite.
HORA_DE_ABRIR = time(9, 0)


def cedo_demais(agora=None):
    return (agora or agora_utc()).astimezone(LISBOA).time() < HORA_DE_ABRIR


def ja_atualizado(agora=None):
    liga = ler_json(FICHEIRO_ATUAL)["liga"]
    fim_da_epoca = date.fromisoformat(liga["primeiro_dia"]) + timedelta(days=liga["periodo_final"] - 1)
    dia = min(ultimo_dia_fechado(agora), fim_da_epoca).isoformat()
    return liga["ultimo_fechado"] == dia and (DADOS / "comentarios" / f"{dia}.md").exists()


if __name__ == "__main__":
    if cedo_demais():
        print("Ainda não são 9h em Lisboa. Fica para a próxima tentativa.")
        sys.exit(0)
    if ja_atualizado():
        print("A atualização deste dia já está feita.")
        sys.exit(0)
    print("A atualização deste dia ainda falta.")
    sys.exit(1)
