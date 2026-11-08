"""Valor do draft: as pechinchas, jogadores escolhidos tarde e a render muito."""
from desenho import e, num, plural

QUANTOS = 5


def calcular(ctx):
    nomes_equipas = {t["id"]: t["nome"] for t in ctx.reais}
    escolhas = sorted((x for x in ctx.draft if x["equipa"] in ctx.ids_reais), key=lambda x: x["escolha"])
    linhas = []
    for ordem, x in enumerate(escolhas, 1):
        j = ctx.jogadores.get(str(x["jogador"]), {})
        epoca = (j.get("medias") or {}).get("epoca") or {}
        linhas.append({
            "nome": j.get("nome", "?"), "nba": j.get("nba", "?"),
            "equipa": nomes_equipas[x["equipa"]],
            "escolha": x["escolha"], "ordem": ordem,
            "pontos": epoca.get("total", 0.0), "media": epoca.get("media", 0.0), "jogos": epoca.get("jogos", 0),
        })
    for lugar, l in enumerate(sorted(linhas, key=lambda l: (-l["pontos"], -l["media"])), 1):
        l["lugar_pontos"] = lugar
        l["valor"] = l["ordem"] - lugar
    return {
        "escolhas_consideradas": len(linhas),
        "pechinchas": [l for l in sorted(linhas, key=lambda l: -l["valor"]) if l["valor"] > 0][:QUANTOS],
    }


def linha_jogador(x, v):
    return (
        f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(x["equipa"])}{e(x["nome"])}</div>'
        f'<div class="meta">Escolha {x["escolha"]} · {x["lugar_pontos"]}.º em pontos · '
        f'{num(x["pontos"])} em {plural(x["jogos"], "jogo", "jogos")}</div></div>'
        f'<span class="sobe"><span aria-hidden="true">▲</span> {num(x["valor"], 0, sinal=True)}</span></li>'
    )


def desenhar(d, v):
    if d["pechinchas"]:
        corpo = f'<ul class="lista">{"".join(linha_jogador(x, v) for x in d["pechinchas"])}</ul>'
    else:
        corpo = '<p class="nota">Ainda sem pechinchas.</p>'
    return (
        f'<div class="cartao"><h3>Pechinchas</h3>{corpo}</div>'
        f'<p class="nota">Compara a ordem de escolha com a ordem em pontos, entre os {d["escolhas_consideradas"]} jogadores '
        "escolhidos pelas três equipas. +10 quer dizer que está 10 lugares acima do que a escolha prometia.</p>"
    )
