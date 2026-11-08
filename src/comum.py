"""Coisas partilhadas: pastas, ficheiros, datas e a escolha do melhor alinhamento."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
DIAS = DADOS / "dias"
FICHEIRO_ATUAL = DADOS / "atual.json"
FICHEIRO_STATS = DADOS / "stats.json"
FICHEIRO_PROJECOES = DADOS / "projecoes.json"

NOVA_IORQUE = ZoneInfo("America/New_York")
LISBOA = ZoneInfo("Europe/Lisbon")

# Números que a ESPN usa para cada lugar do plantel.
NOMES_LUGARES = {
    0: "PG", 1: "SG", 2: "SF", 3: "PF", 4: "C",
    5: "G", 6: "F", 11: "UT", 12: "Banco", 13: "Lesionados",
}
BANCO = 12
LESIONADOS = 13
FORA_DO_CINCO = {BANCO, LESIONADOS}


def ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def escrever_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")


def ler_config():
    return ler_json(RAIZ / "config.json")


def agora_utc():
    return datetime.now(timezone.utc)


def ultimo_dia_fechado(agora=None):
    """Último dia da NBA com todos os jogos acabados, na data de Nova Iorque.

    Tira 4 horas ao relógio de Nova Iorque antes de recuar um dia, para que
    um jogo da costa oeste que acabe depois da meia-noite conte no dia certo.
    """
    agora = agora or agora_utc()
    return (agora.astimezone(NOVA_IORQUE) - timedelta(hours=4)).date() - timedelta(days=1)


def melhor_alinhamento(candidatos, lugares):
    """Escolhe quem joga para somar o máximo, respeitando as posições.

    candidatos: lista de (valor, posições_possíveis).
    lugares: lista de posições, com repetições (por exemplo UT três vezes).
    Devolve os índices dos candidatos escolhidos.
    """
    ordem = sorted(range(len(candidatos)), key=lambda i: -candidatos[i][0])
    ocupante = [None] * len(lugares)

    def colocar(i, vistos):
        for n, posicao in enumerate(lugares):
            if n in vistos or posicao not in candidatos[i][1]:
                continue
            vistos.add(n)
            if ocupante[n] is None or colocar(ocupante[n], vistos):
                ocupante[n] = i
                return True
        return False

    for i in ordem:
        colocar(i, set())
    return [i for i in ocupante if i is not None]
