"""Vai buscar os dados à ESPN e guarda-os na pasta dados/.

dados/dias/AAAA-MM-DD.json  retrato de cada dia da época (alinhamentos e pontos)
dados/atual.json            situação de hoje (plantéis, lesões, livres, calendário)

Só guarda nomes de equipas e de jogadores. Os dados pessoais dos donos das
equipas nunca são gravados, porque o repositório é público.
"""
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from comum import (
    DIAS, FICHEIRO_ATUAL, NOVA_IORQUE, agora_utc, escrever_json, ler_config,
    ler_json, ultimo_dia_fechado,
)
from espn import ESPN, ErroESPN

DIAS_A_RELER = 7  # a ESPN às vezes corrige estatísticas nos dias seguintes
PAUSA = 0.3  # segundos entre pedidos, para não sobrecarregar a ESPN

# (fonte, tipo de período) -> nome que usamos
JANELAS = {(0, 0): "epoca", (0, 1): "u7", (0, 2): "u15", (0, 3): "u30", (1, 0): "proj"}


def ler_calendario(api):
    bruto = api.calendario_nba()
    siglas = {}
    por_periodo = defaultdict(set)
    primeiro_dia = None
    for equipa in bruto["settings"]["proTeams"]:
        sigla = equipa["abbrev"].upper()
        siglas[equipa["id"]] = sigla
        for periodo, jogos in equipa.get("proGamesByScoringPeriod", {}).items():
            for jogo in jogos:
                por_periodo[int(periodo)].add(sigla)
                if int(periodo) == 1:
                    dia = datetime.fromtimestamp(jogo["date"] / 1000, tz=timezone.utc)
                    dia = dia.astimezone(NOVA_IORQUE).date()
                    primeiro_dia = min(primeiro_dia or dia, dia)
    if primeiro_dia is None:
        raise ErroESPN("Calendário da NBA sem o primeiro dia da época.")
    return siglas, por_periodo, primeiro_dia


def base_jogador(entrada, siglas, lugares_ativos):
    p = entrada["playerPoolEntry"]["player"]
    return {
        "id": p["id"],
        "nome": p["fullName"],
        "nba": siglas.get(p.get("proTeamId"), "?"),
        "lugar": entrada["lineupSlotId"],
        "posicoes": [s for s in p.get("eligibleSlots", []) if s in lugares_ativos],
    }


def retrato_do_dia(api, periodo, dia, siglas, equipas_com_jogo, lugares_ativos):
    bruto = api.liga(["mRoster", "mTeam"], periodo)
    equipas = []
    for t in bruto["teams"]:
        jogadores = []
        pontos_equipa = 0.0
        jogos_equipa = 0
        for entrada in t["roster"]["entries"]:
            j = base_jogador(entrada, siglas, lugares_ativos)
            jogo = next((
                s for s in entrada["playerPoolEntry"]["player"].get("stats", [])
                if s.get("statSplitTypeId") == 5 and s.get("statSourceId") == 0
                and s.get("scoringPeriodId") == periodo
            ), None)
            jogou = bool(jogo and jogo.get("stats", {}).get("42"))
            pontos = round(jogo.get("appliedTotal", 0.0), 1) if jogo else 0.0
            j.update(pontos=pontos, jogou=jogou, tinha_jogo=j["nba"] in equipas_com_jogo)
            if jogou:
                e = jogo["stats"]
                j["linha"] = {
                    "min": int(e.get("40", 0)), "pts": int(e.get("0", 0)),
                    "res": int(e.get("6", 0)), "ast": int(e.get("3", 0)),
                    "rb": int(e.get("2", 0)), "dl": int(e.get("1", 0)),
                    "per": int(e.get("11", 0)),
                }
            if j["lugar"] in lugares_ativos:
                pontos_equipa += pontos
                jogos_equipa += 1 if jogou else 0
            jogadores.append(j)
        equipas.append({
            "id": t["id"], "nome": t["name"], "abrev": t["abbrev"],
            "pontos": round(pontos_equipa, 1), "jogos": jogos_equipa,
            "jogadores": jogadores,
        })
    return {"data": dia.isoformat(), "periodo": periodo, "equipas": equipas}


def ler_medias(jogador, ano):
    medias = {}
    for s in jogador.get("stats", []):
        if s.get("seasonId") == ano:
            nome = JANELAS.get((s.get("statSourceId"), s.get("statSplitTypeId")))
        elif s.get("seasonId") == ano - 1 and s.get("statSourceId") == 0 and s.get("statSplitTypeId") == 0:
            nome = "anterior"
        else:
            nome = None
        if not nome:
            continue
        total = s.get("appliedTotal") or 0.0
        media = s.get("appliedAverage") or 0.0
        jogos = s.get("stats", {}).get("42")
        if jogos is None:
            jogos = round(total / media) if media else 0
        medias[nome] = {"total": round(total, 1), "media": round(media, 2), "jogos": int(jogos)}
    return medias


def dados_de_lesao(jogador):
    detalhes = jogador.get("injuryDetails") or {}
    regresso = detalhes.get("expectedReturnDate")
    return {
        "estado": jogador.get("injuryStatus") or "ACTIVE",
        "regresso": "%04d-%02d-%02d" % tuple(regresso) if regresso else None,
        "fora_epoca": bool(detalhes.get("outForSeason")),
    }


def ler_livres(api, periodo, siglas, lugares_ativos):
    escolhidos = {}
    for janela in ("01", "02"):
        for bruto in api.jogadores_livres(periodo, janela):
            p = bruto["player"]
            escolhidos[p["id"]] = {
                "id": p["id"], "nome": p["fullName"],
                "nba": siglas.get(p.get("proTeamId"), "?"),
                "posicoes": [s for s in p.get("eligibleSlots", []) if s in lugares_ativos],
                "situacao": bruto.get("status"),
                "medias": ler_medias(p, api.ano),
                **dados_de_lesao(p),
            }
        time.sleep(PAUSA)
    return list(escolhidos.values())


def ler_situacao_atual(api, cfg, definicoes, estado, siglas, por_periodo, primeiro_dia, ultimo_fechado):
    regras = definicoes["settings"]["rosterSettings"]
    contagem = {int(k): v for k, v in regras["lineupSlotCounts"].items() if v}
    lugares_ativos = {k for k in contagem if k not in (12, 13)}
    limites = {
        k: regras.get("lineupSlotStatLimits", {}).get(str(k), {}).get("limitValue")
        for k in sorted(lugares_ativos)
    }
    periodo_atual = estado["latestScoringPeriod"]
    bruto = api.liga(["mRoster", "mTeam"], periodo_atual)
    time.sleep(PAUSA)
    marcador = api.liga(["mBoxscore", "mMatchupScore"], periodo_atual)
    por_lugar = {}
    for jogo in marcador.get("schedule", []):
        for t in jogo.get("teams", []):
            por_lugar[t["teamId"]] = {
                int(k): int(v.get("value", 0))
                for k, v in (t.get("cumulativeScore", {}).get("statBySlot") or {}).items()
            }
    equipas = []
    for t in bruto["teams"]:
        plantel = []
        for entrada in t["roster"]["entries"]:
            j = base_jogador(entrada, siglas, lugares_ativos)
            p = entrada["playerPoolEntry"]["player"]
            j.update(medias=ler_medias(p, api.ano), **dados_de_lesao(p))
            plantel.append(j)
        equipas.append({
            "id": t["id"], "nome": t["name"], "abrev": t["abbrev"],
            "pontos_oficiais": t.get("points", 0.0),
            "fantasma": t["id"] in cfg["equipas_fantasma"],
            "aquisicoes": t.get("transactionCounter", {}).get("acquisitions", 0),
            "jogos_por_lugar": {str(k): por_lugar.get(t["id"], {}).get(k, 0) for k in sorted(lugares_ativos)},
            "plantel": plantel,
        })
    return {
        "atualizado_em": agora_utc().isoformat(timespec="seconds"),
        "liga": {
            "nome": definicoes["settings"]["name"],
            "periodo_atual": periodo_atual,
            "periodo_final": estado["finalScoringPeriod"],
            "primeiro_dia": primeiro_dia.isoformat(),
            "ultimo_fechado": ultimo_fechado.isoformat(),
        },
        "lugares": {
            "contagem": {str(k): v for k, v in contagem.items()},
            "limites_jogos": {str(k): v for k, v in limites.items()},
        },
        "equipas": equipas,
        "livres": ler_livres(api, periodo_atual, siglas, lugares_ativos),
        "calendario": {str(k): sorted(v) for k, v in sorted(por_periodo.items())},
    }


def somar_dias():
    soma = defaultdict(float)
    for ficheiro in DIAS.glob("*.json"):
        for t in ler_json(ficheiro)["equipas"]:
            soma[t["id"]] += t["pontos"]
    return soma


def principal():
    cfg = ler_config()
    api = ESPN(cfg["id_liga"], cfg["ano_api"])

    definicoes = api.liga(["mSettings", "mStatus"])
    estado = definicoes["status"]
    regras = definicoes["settings"]["rosterSettings"]
    lugares_ativos = {
        int(k) for k, v in regras["lineupSlotCounts"].items() if v and int(k) not in (12, 13)
    }
    siglas, por_periodo, primeiro_dia = ler_calendario(api)

    ultimo_fechado = ultimo_dia_fechado()
    ultimo_periodo = min((ultimo_fechado - primeiro_dia).days + 1, estado["finalScoringPeriod"])
    ultimo_fechado = primeiro_dia + timedelta(days=ultimo_periodo - 1)

    def guardar_dia(periodo):
        dia = primeiro_dia + timedelta(days=periodo - 1)
        retrato = retrato_do_dia(api, periodo, dia, siglas, por_periodo.get(periodo, set()), lugares_ativos)
        escrever_json(DIAS / f"{dia.isoformat()}.json", retrato)
        time.sleep(PAUSA)

    for periodo in range(1, ultimo_periodo + 1):
        dia = primeiro_dia + timedelta(days=periodo - 1)
        recente = periodo > ultimo_periodo - DIAS_A_RELER
        if recente or not (DIAS / f"{dia.isoformat()}.json").exists():
            guardar_dia(periodo)

    atual = ler_situacao_atual(api, cfg, definicoes, estado, siglas, por_periodo, primeiro_dia, ultimo_fechado)

    # Prova dos nove: a soma dos dias tem de dar o total oficial da ESPN.
    def diferencas():
        soma = somar_dias()
        return {
            str(t["id"]): round(t["pontos_oficiais"] - soma.get(t["id"], 0.0), 1)
            for t in atual["equipas"]
            if abs(t["pontos_oficiais"] - soma.get(t["id"], 0.0)) > 0.05
        }

    dif = diferencas()
    if dif:
        print("A soma dos dias não bate certo; a reler a época toda:", dif)
        for periodo in range(1, ultimo_periodo + 1):
            guardar_dia(periodo)
        dif = diferencas()
    atual["verificacao"] = {"bate_certo": not dif, "diferencas": dif}

    escrever_json(FICHEIRO_ATUAL, atual)
    print(f"Recolha feita até {ultimo_fechado} (dia {ultimo_periodo}). Verificação: {atual['verificacao']}")


if __name__ == "__main__":
    try:
        principal()
    except ErroESPN as e:
        print(f"ERRO ESPN: {e}", file=sys.stderr)
        sys.exit(2)
