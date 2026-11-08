"""Real vs. projeção da ESPN: quem está a surpreender e quem está a desiludir."""
from desenho import data_curta, e, num, plural

MINIMO_JOGOS = 5
QUANTOS = 5


def calcular(ctx):
    linhas = []
    datas = []
    for t in ctx.reais:
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
    for t in ctx.reais:
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


def lista(linhas, v, sobe, vazio):
    if not linhas:
        return f'<p class="nota">{vazio}</p>'
    classe = "sobe" if sobe else "desce"
    seta = "▲" if sobe else "▼"
    itens = "".join(
        f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(x["equipa"])}{e(x["nome"])}</div>'
        f'<div class="meta">Média {num(x["media"])} · previsão {num(x["prevista"])} · {plural(x["jogos"], "jogo", "jogos")}</div></div>'
        f'<span class="{classe}"><span aria-hidden="true">{seta}</span> {num(x["diferenca"], sinal=True)}</span></li>'
        for x in linhas
    )
    return f'<ul class="lista">{itens}</ul>'


def desenhar(d, v):
    equipas = "".join(
        f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(t["nome"])}{e(t["nome"])}</div></div>'
        f'<strong class="grande">{num(t["diferenca"], sinal=True)}</strong></li>'
        for t in d["equipas"]
    )
    desde = f' A previsão foi guardada a {data_curta(d["projecao_guardada_em"])}.' if d["projecao_guardada_em"] else ""
    return (
        f'<div class="cartao"><h3>Pontos por jogo face à previsão</h3><ul class="lista">{equipas}</ul></div>'
        f'<div class="cartao"><h3>Quem está a surpreender</h3>{lista(d["surpresas"], v, True, "Ainda ninguém acima da previsão.")}</div>'
        f'<div class="cartao"><h3>Quem está a desiludir</h3>{lista(d["desilusoes"], v, False, "Ainda ninguém abaixo da previsão.")}</div>'
        f'<p class="nota">Média de pontos por jogo contra a previsão da ESPN para a época, só para quem já fez pelo menos {d["minimo_jogos"]} jogos.{desde}</p>'
    )
