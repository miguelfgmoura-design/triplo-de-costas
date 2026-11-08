"""Valor do draft: pontos de cada jogador contra a posição em que foi escolhido."""
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

    equipas = []
    for t in ctx.reais:
        deles = [l for l in linhas if l["equipa"] == t["nome"]]
        if deles:
            equipas.append({
                "nome": t["nome"],
                "valor": sum(l["valor"] for l in deles),
                "melhor": max(deles, key=lambda l: l["valor"]),
                "pior": min(deles, key=lambda l: l["valor"]),
            })
    return {
        "escolhas_consideradas": len(linhas),
        "equipas": sorted(equipas, key=lambda r: -r["valor"]),
        "pechinchas": [l for l in sorted(linhas, key=lambda l: -l["valor"]) if l["valor"] > 0][:QUANTOS],
        "desastres": [l for l in sorted(linhas, key=lambda l: l["valor"]) if l["valor"] < 0][:QUANTOS],
    }


def linha_jogador(x, v, sobe):
    classe = "sobe" if sobe else "desce"
    seta = "▲" if sobe else "▼"
    return (
        f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(x["equipa"])}{e(x["nome"])}</div>'
        f'<div class="meta">Escolha {x["escolha"]} · {x["lugar_pontos"]}.º em pontos · '
        f'{num(x["pontos"])} em {plural(x["jogos"], "jogo", "jogos")}</div></div>'
        f'<span class="{classe}"><span aria-hidden="true">{seta}</span> {num(x["valor"], 0, sinal=True)}</span></li>'
    )


def lista(linhas, v, sobe, vazio):
    if not linhas:
        return f'<p class="nota">{vazio}</p>'
    return f'<ul class="lista">{"".join(linha_jogador(x, v, sobe) for x in linhas)}</ul>'


def desenhar(d, v):
    equipas = "".join(
        f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(t["nome"])}{e(t["nome"])}</div>'
        f'<div class="meta">Melhor: {e(t["melhor"]["nome"])} ({num(t["melhor"]["valor"], 0, sinal=True)}) · '
        f'Pior: {e(t["pior"]["nome"])} ({num(t["pior"]["valor"], 0, sinal=True)})</div></div>'
        f'<strong class="grande">{num(t["valor"], 0, sinal=True)}</strong></li>'
        for t in d["equipas"]
    )
    return (
        f'<div class="cartao"><h3>Quem escolheu melhor</h3><ul class="lista">{equipas}</ul></div>'
        f'<div class="cartao"><h3>Pechinchas</h3>{lista(d["pechinchas"], v, True, "Ainda sem pechinchas.")}</div>'
        f'<div class="cartao"><h3>Desastres</h3>{lista(d["desastres"], v, False, "Ainda sem desastres.")}</div>'
        f'<p class="nota">Compara a ordem de escolha com a ordem em pontos, entre os {d["escolhas_consideradas"]} jogadores '
        "escolhidos pelas três equipas. +10 quer dizer que está 10 lugares acima do que a escolha prometia. "
        "Quem falhou muitos jogos por lesão também desce.</p>"
    )
