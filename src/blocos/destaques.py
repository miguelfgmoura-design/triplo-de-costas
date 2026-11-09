"""C. Forma e destaques: MVP, flop, top 5, em alta e em baixa."""
from desenho import EB, data_curta, e, nome_curto, num, quadro, tabela, tile, variacao

MINIMO_JOGOS_RECENTES = 2
MINIMO_JOGOS_COMPARACAO = 5
QUANTOS_EM_ALTA = 4


def resumo(j, equipa, media):
    return {
        "nome": j["nome"], "equipa": equipa, "nba": j["nba"], "pontos": j["pontos"],
        "media_epoca": media, "diferenca_media": round(j["pontos"] - media, 1) if media else None,
        "linha": j.get("linha"),
    }


def flop_de(lista):
    """O flop é quem mais ficou abaixo da sua própria média."""
    com_media = [r for r in lista if r["diferenca_media"] is not None and r["diferenca_media"] < 0]
    return min(com_media, key=lambda r: r["diferenca_media"]) if com_media else None


def forma(ctx):
    linhas = []
    for t in ctx.equipas:
        for j in t["plantel"]:
            m = j["medias"]
            recente = m.get("u7")
            referencia = m.get("u30") or m.get("epoca")
            if not recente or not referencia:
                continue
            if recente["jogos"] < MINIMO_JOGOS_RECENTES or referencia["jogos"] < MINIMO_JOGOS_COMPARACAO:
                continue
            if referencia["jogos"] <= recente["jogos"]:
                continue
            linhas.append({
                "nome": j["nome"], "equipa": t["nome"], "nba": j["nba"],
                "media_7_dias": round(recente["media"], 1), "jogos_7_dias": recente["jogos"],
                "media_referencia": round(referencia["media"], 1),
                "variacao": round(recente["media"] - referencia["media"], 1),
            })
    linhas.sort(key=lambda l: -l["variacao"])
    alta = [l for l in linhas if l["variacao"] > 0][:QUANTOS_EM_ALTA]
    baixa = [l for l in reversed(linhas) if l["variacao"] < 0][:QUANTOS_EM_ALTA]
    return alta, baixa


def calcular(ctx):
    medias = {i: (j["medias"].get("epoca") or {}).get("media", 0.0) for i, j in ctx.jogadores_nos_planteis().items()}
    por_equipa = []
    todos = []
    for t in ctx.dia_ref["equipas"]:
        lista = [
            resumo(j, t["nome"], medias.get(j["id"], 0.0))
            for j in t["jogadores"] if j["lugar"] in ctx.lugares_ativos and j["jogou"]
        ]
        todos.extend(lista)
        por_equipa.append({
            "equipa": t["nome"],
            "mvp": max(lista, key=lambda r: r["pontos"]) if lista else None,
            "flop": flop_de(lista),
        })
    em_alta, em_baixa = forma(ctx)
    abaixo_da_media = [r for r in todos if r["diferenca_media"] is not None and r["diferenca_media"] < 0]
    return {
        "dia": ctx.dia_ref["data"],
        "mvp": max(todos, key=lambda r: r["pontos"]) if todos else None,
        "flop": flop_de(todos),
        "por_equipa": por_equipa,
        "top5": sorted(todos, key=lambda r: -r["pontos"])[:5],
        "flops": sorted(abaixo_da_media, key=lambda r: r["diferenca_media"])[:5],
        "em_alta": em_alta,
        "em_baixa": em_baixa,
    }


def linha_de_jogo(r):
    l = r.get("linha") or {}
    partes = [f'{l.get("pts", 0)}{EB}pts', f'{l.get("res", 0)}{EB}res', f'{l.get("ast", 0)}{EB}ast']
    if l.get("rb"):
        partes.append(f'{l["rb"]}{EB}rb')
    if l.get("dl"):
        partes.append(f'{l["dl"]}{EB}dl')
    partes.append(f'{l.get("min", 0)}{EB}min')
    return " · ".join(partes)


def heroi(rotulo, r, v):
    if not r:
        return tile(rotulo, "—", "Sem dados")
    comparacao = (
        ""
        if r["diferenca_media"] is None
        else f'<span class="tile-s">{num(r["diferenca_media"], sinal=True)} face à média ({num(r["media_epoca"])})</span>'
    )
    return (
        f'<div class="tile"><span class="tile-k">{rotulo}</span><span class="tile-v">{num(r["pontos"])}</span>'
        f'<span class="tile-n">{e(r["nome"])}</span><span class="tile-s">{v.equipa(r["equipa"])}</span>'
        f'<span class="tile-s">{linha_de_jogo(r)}</span>{comparacao}</div>'
    )


def tabela_jogos(linhas, v, vazio):
    if not linhas:
        return f'<p class="nota">{vazio}</p>'
    colunas = [("#", "p"), ("Jogador", "e"), ("Eq.", "eq"), ("P/R/A", "pra"), ("Méd.", ""), ("Fant.", "")]
    corpo = []
    for i, x in enumerate(linhas, 1):
        l = x.get("linha") or {}
        corpo.append([
            str(i),
            e(nome_curto(x["nome"])),
            v.equipa_curta(x["equipa"]),
            f'{l.get("pts", 0)}/{l.get("res", 0)}/{l.get("ast", 0)}',
            num(x["media_epoca"]) if x["media_epoca"] else "—",
            f'<b>{num(x["pontos"])}</b>',
        ])
    return tabela(colunas, corpo)


def tabela_forma(lista, v, sobe):
    if not lista:
        return '<p class="nota">Ainda sem jogos suficientes para comparar.</p>'
    colunas = [("Jogador", "e"), ("Eq.", "eq"), ("7 dias", ""), ("Antes", ""), ("Var.", "")]
    corpo = [
        [
            e(nome_curto(x["nome"])),
            v.equipa_curta(x["equipa"]),
            num(x["media_7_dias"]),
            num(x["media_referencia"]),
            variacao(x["variacao"], sobe),
        ]
        for x in lista
    ]
    return tabela(colunas, corpo)


def desenhar_dia(d, v):
    dia = data_curta(d["dia"])
    herois = f'<div class="tiles">{heroi("MVP", d["mvp"], v)}{heroi("Flop", d["flop"], v)}</div>'
    return (
        quadro("Destaques do dia", herois, info=dia)
        + quadro(
            "Top 5",
            tabela_jogos(d["top5"], v, "Ninguém jogou neste dia."),
            info=dia,
            nota="Os cinco jogadores com mais pontos, entre os que estavam em posições ativas. "
            "P/R/A: pontos, ressaltos e assistências no jogo. Fant.: pontos na liga.",
        )
        + quadro(
            "Flops",
            tabela_jogos(d["flops"], v, "Ninguém ficou abaixo da sua média."),
            info=dia,
            nota="Os cinco que mais ficaram abaixo da sua própria média da época, entre os que estavam em posições ativas.",
        )
    )


def desenhar_forma(d, v):
    return (
        quadro("Em alta", tabela_forma(d["em_alta"], v, True))
        + quadro(
            "Em baixa",
            tabela_forma(d["em_baixa"], v, False),
            nota="Média dos últimos 7 dias contra a dos últimos 30 dias.",
        )
    )


def cartao_equipa(t, v):
    mvp = t["mvp"]
    flop = t["flop"]
    lado_mvp = (
        f'<div class="tile"><span class="tile-k">MVP</span><span class="tile-v">{num(mvp["pontos"])}</span>'
        f'<span class="tile-n">{e(mvp["nome"])}</span></div>'
        if mvp
        else tile("MVP", "—", "Ninguém jogou")
    )
    lado_flop = (
        f'<div class="tile"><span class="tile-k">Flop</span><span class="tile-v">{num(flop["pontos"])}</span>'
        f'<span class="tile-n">{e(flop["nome"])}</span><span class="tile-s">Média {num(flop["media_epoca"])}</span></div>'
        if flop
        else tile("Flop", "—", "Ninguém abaixo da média")
    )
    return quadro("MVP e flop do dia", f'<div class="tiles">{lado_mvp}{lado_flop}</div>')
