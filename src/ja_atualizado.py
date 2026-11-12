"""Decide se uma tentativa agendada tem trabalho para fazer.

O GitHub não cumpre as horas marcadas: cada tentativa chega horas depois e a
horas diferentes de dia para dia. Por isso há muitas tentativas por dia, e é
este ficheiro que decide o que cada uma faz. Só há trabalho depois das 9h de
Lisboa, enquanto a atualização do dia faltar e sem repetir logo a seguir uma
tentativa que falhou.

Códigos de saída: 0 = nada a fazer agora, 10 = há trabalho, outro = avaria.
Com --registar, aponta que começou uma tentativa.
"""
import sys
from datetime import date, datetime, time, timedelta

from comum import DADOS, FICHEIRO_ATUAL, LISBOA, agora_utc, escrever_json, ler_json, ultimo_dia_fechado

# Antes desta hora a ESPN pode ainda não ter fechado os números da noite.
HORA_DE_ABRIR = time(9, 0)
# Depois de uma tentativa que não chegou ao fim, a seguinte espera 1 hora, e as
# outras 2, 3 e 4 horas. Assim um dia mau não gasta dezenas de tentativas.
ESPERA_MAXIMA_HORAS = 4
FICHEIRO_TENTATIVA = DADOS / "tentativa.json"
HA_TRABALHO = 10


def dia_a_atualizar(agora):
    liga = ler_json(FICHEIRO_ATUAL)["liga"]
    fim_da_epoca = date.fromisoformat(liga["primeiro_dia"]) + timedelta(days=liga["periodo_final"] - 1)
    return min(ultimo_dia_fechado(agora), fim_da_epoca).isoformat()


def ja_atualizado(dia):
    """Os números desse dia estão guardados e o comentário também."""
    guardado = ler_json(FICHEIRO_ATUAL)["liga"]["ultimo_fechado"] == dia
    return guardado and (DADOS / "comentarios" / f"{dia}.md").exists()


def ler_tentativa():
    try:
        return ler_json(FICHEIRO_TENTATIVA)
    except (OSError, ValueError):
        return {}


def proxima_tentativa(dia):
    """A partir de quando se pode voltar a tentar este dia. None se ainda ninguém tentou."""
    apontado = ler_tentativa()
    try:
        if apontado.get("dia") != dia:
            return None
        espera = min(int(apontado["tentativas"]), ESPERA_MAXIMA_HORAS)
        return datetime.fromisoformat(apontado["ultima"]) + timedelta(hours=espera)
    except (AttributeError, KeyError, TypeError, ValueError):
        return None  # apontamento estragado: é como se não existisse


def decidir(agora=None):
    """Devolve (há trabalho?, explicação)."""
    agora = agora or agora_utc()
    if agora.astimezone(LISBOA).time() < HORA_DE_ABRIR:
        return False, "Ainda não são 9h em Lisboa. Fica para a próxima tentativa."
    dia = dia_a_atualizar(agora)
    if ja_atualizado(dia):
        return False, "A atualização deste dia já está feita."
    proxima = proxima_tentativa(dia)
    if proxima and agora < proxima:
        return False, f"A última tentativa não chegou ao fim. Volta a tentar depois das {proxima.astimezone(LISBOA):%H:%M}."
    return True, "A atualização deste dia ainda falta."


def registar_tentativa(agora=None):
    agora = agora or agora_utc()
    dia = dia_a_atualizar(agora)
    apontado = ler_tentativa()
    try:
        numero = int(apontado["tentativas"]) + 1 if apontado.get("dia") == dia else 1
    except (AttributeError, KeyError, TypeError, ValueError):
        numero = 1
    escrever_json(FICHEIRO_TENTATIVA, {"dia": dia, "tentativas": numero, "ultima": agora.isoformat(timespec="seconds")})
    return numero


if __name__ == "__main__":
    if sys.argv[1:] == ["--registar"]:
        print(f"Tentativa número {registar_tentativa()} para este dia.")
        sys.exit(0)
    trabalho, explicacao = decidir()
    print(explicacao)
    sys.exit(HA_TRABALHO if trabalho else 0)
