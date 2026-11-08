"""C. Forma e destaques: MVP, flop, top 5, em alta e em baixa. Sem a equipa fantasma."""
from desenho import EB, data_curta, e, num

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
    for t in ctx.reais:
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
        if t["id"] not in ctx.ids_reais:
            continue
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
    return {
        "dia": ctx.dia_ref["data"],
        "mvp": max(todos, key=lambda r: r["pontos"]) if todos else None,
        "flop": flop_de(todos),
        "por_equipa": por_equipa,
        "top5": sorted(todos, key=lambda r: -r["pontos"])[:5],
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
        return f'<div class="cartao heroi"><span class="rotulo">{rotulo}</span><span class="meta">Sem dados</span></div>'
    if r["diferenca_media"] is None:
        comparacao = ""
    else:
        comparacao = f'<span class="meta">{num(r["diferenca_media"], sinal=True)} face à média ({num(r["media_epoca"])})</span>'
    return (
        f'<div class="cartao heroi"><span class="rotulo">{rotulo}</span>'
        f'<span class="h-pontos">{num(r["pontos"])}</span><span class="h-nome">{e(r["nome"])}</span>'
        f'<span class="nome meta">{v.ponto(r["equipa"])}{e(r["equipa"])}</span>'
        f'<span class="meta">{linha_de_jogo(r)}</span>{comparacao}</div>'
    )


def linhas_forma(lista, v, sobe):
    if not lista:
        return '<p class="nota">Ainda sem jogos suficientes para comparar.</p>'
    itens = []
    for x in lista:
        seta = "▲" if sobe else "▼"
        classe = "sobe" if sobe else "desce"
        itens.append(
            f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(x["equipa"])}{e(x["nome"])}</div>'
            f'<div class="meta">{num(x["media_7_dias"])} nos últimos 7 dias, {num(x["media_referencia"])} antes</div></div>'
            f'<span class="{classe}"><span aria-hidden="true">{seta}</span> {num(x["variacao"], sinal=True)}</span></li>'
        )
    return f'<ul class="lista">{"".join(itens)}</ul>'


def desenhar_dia(d, v):
    dia = data_curta(d["dia"])
    top = "".join(
        f'<li class="linha"><span class="posto">{i}</span><div class="cresce"><div class="nome">{e(x["nome"])}</div>'
        f'<div class="nome meta">{v.ponto(x["equipa"])}{e(x["equipa"])}</div></div>'
        f'<strong class="grande">{num(x["pontos"])}</strong></li>'
        for i, x in enumerate(d["top5"], 1)
    )
    return (
        f'<div class="grelha-herois">{heroi(f"MVP de {dia}", d["mvp"], v)}{heroi(f"Flop de {dia}", d["flop"], v)}</div>'
        f'<div class="cartao"><h3>Top 5 de {dia}</h3><ol class="lista">{top}</ol></div>'
        '<p class="nota">O flop é quem mais ficou abaixo da sua própria média.</p>'
    )


def desenhar_forma(d, v):
    return (
        f'<div class="cartao"><h3>Em alta</h3>{linhas_forma(d["em_alta"], v, True)}</div>'
        f'<div class="cartao"><h3>Em baixa</h3>{linhas_forma(d["em_baixa"], v, False)}</div>'
        '<p class="nota">Média dos últimos 7 dias contra a dos últimos 30 dias.</p>'
    )


def cartao_equipa(t, v):
    mvp = t["mvp"]
    flop = t["flop"]
    linha_mvp = (
        f'<li class="linha"><div class="cresce"><div class="meta">MVP</div><div class="nome">{e(mvp["nome"])}</div></div>'
        f'<strong class="grande">{num(mvp["pontos"])}</strong></li>'
        if mvp else '<li class="linha"><div class="cresce"><div class="meta">MVP</div><div class="nome">Ninguém jogou</div></div></li>'
    )
    linha_flop = (
        f'<li class="linha"><div class="cresce"><div class="meta">Flop</div><div class="nome">{e(flop["nome"])}</div>'
        f'<div class="meta">média {num(flop["media_epoca"])}</div></div>'
        f'<strong class="grande">{num(flop["pontos"])}</strong></li>'
        if flop else '<li class="linha"><div class="cresce"><div class="meta">Flop</div><div class="nome">Ninguém abaixo da média</div></div></li>'
    )
    return f'<div class="cartao"><ul class="lista">{linha_mvp}{linha_flop}</ul></div>'
