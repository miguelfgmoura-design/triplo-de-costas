"""Real vs. projeção da ESPN: quem está a surpreender e quem está a desiludir."""
from desenho import data_curta, e, nome_curto, num, quadro, tabela, variacao

MINIMO_JOGOS = 5
QUANTOS = 5


def calcular(ctx):
    linhas = []
    datas = []
    for t in ctx.equipas:
        for j in t["plantel"]:
            epoca = j["medias"].get("epoca")
            if not epoca or epoca["jogos"] < MINIMO_JOGOS:
                continue
            guardada = ctx.projecoes.get(str(j["id"])) or {}
            prevista = guardada.get("media") or (j["medias"].get("proj") or {}).get("media")
            if not prevista:
                continue
            if guardada.get("desde"):
                datas.append(guardada["desde"])
            linhas.append({
                "nome": j["nome"], "equipa": t["nome"], "nba": j["nba"],
                "media": round(epoca["media"], 1), "prevista": round(prevista, 1),
                "diferenca": round(epoca["media"] - prevista, 1), "jogos": epoca["jogos"],
            })
    equipas = []
    for t in ctx.equipas:
        deles = [l for l in linhas if l["equipa"] == t["nome"]]
        jogos = sum(l["jogos"] for l in deles)
        if jogos:
            equipas.append({
                "nome": t["nome"],
                "diferenca": round(sum(l["diferenca"] * l["jogos"] for l in deles) / jogos, 1),
            })
    ordem = sorted(linhas, key=lambda l: -l["diferenca"])
    return {
        "projecao_guardada_em": min(datas) if datas else None,
        "minimo_jogos": MINIMO_JOGOS,
        "equipas": sorted(equipas, key=lambda r: -r["diferenca"]),
        "surpresas": [l for l in ordem if l["diferenca"] > 0][:QUANTOS],
        "desilusoes": [l for l in reversed(ordem) if l["diferenca"] < 0][:QUANTOS],
    }


def tabela_jogadores(linhas, v, sobe, vazio):
    if not linhas:
        return f'<p class="nota">{vazio}</p>'
    colunas = [("Jogador", "e"), ("Eq.", "eq"), ("J", ""), ("Média", ""), ("Prev.", ""), ("Dif.", "")]
    corpo = [
        [
            e(nome_curto(x["nome"])),
            v.equipa_curta(x["equipa"]),
            str(x["jogos"]),
            num(x["media"]),
            num(x["prevista"]),
            variacao(x["diferenca"], sobe),
        ]
        for x in linhas
    ]
    return tabela(colunas, corpo)


def desenhar(d, v):
    equipas = [[v.equipa(t["nome"]), f'<b>{num(t["diferenca"], sinal=True)}</b>'] for t in d["equipas"]]
    desde = f' A previsão foi guardada a {data_curta(d["projecao_guardada_em"])}.' if d["projecao_guardada_em"] else ""
    return (
        quadro("Pontos por jogo face à previsão", tabela([("Equipa", "e"), ("Diferença", "")], equipas), info="ESPN")
        + quadro("Quem está a surpreender", tabela_jogadores(d["surpresas"], v, True, "Ainda ninguém acima da previsão."))
        + quadro(
            "Quem está a desiludir",
            tabela_jogadores(d["desilusoes"], v, False, "Ainda ninguém abaixo da previsão."),
            nota=f'Média de pontos por jogo contra a previsão da ESPN para a época, só para quem já fez pelo menos {d["minimo_jogos"]} jogos.{desde}',
        )
    )
