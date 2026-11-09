"""Dependência da estrela: que parte dos pontos de cada equipa vem do melhor jogador."""
from collections import Counter

from desenho import e, num, plural

ESTADOS = {"OUT": "Fora", "DAY_TO_DAY": "Dia a dia", "QUESTIONABLE": "Em dúvida", "DOUBTFUL": "Improvável", "SUSPENSION": "Suspenso"}


def calcular(ctx):
    resultado = []
    for t in ctx.equipas:
        pontos = Counter()
        jogos = Counter()
        nomes = {}
        for dia in ctx.dias_com_jogos:
            for j in ctx.equipa_no_dia(dia, t["id"])["jogadores"]:
                if j["lugar"] in ctx.lugares_ativos and j["jogou"]:
                    pontos[j["id"]] += j["pontos"]
                    jogos[j["id"]] += 1
                    nomes[j["id"]] = j["nome"]
        total = sum(pontos.values())
        ordem = pontos.most_common()
        if not ordem or total <= 0:
            continue
        melhor, valor = ordem[0]
        no_plantel = next((j for j in t["plantel"] if j["id"] == melhor), None)
        resultado.append({
            "nome": t["nome"],
            "jogador": nomes[melhor],
            "pontos": round(valor, 1),
            "jogos": jogos[melhor],
            "pontos_por_jogo": round(valor / jogos[melhor], 1),
            "percentagem": round(100 * valor / total, 1),
            "percentagem_3_melhores": round(100 * sum(v for _, v in ordem[:3]) / total, 1),
            "estado": ESTADOS.get(no_plantel["estado"]) if no_plantel else None,
            "ainda_no_plantel": no_plantel is not None,
        })
    return {"equipas": sorted(resultado, key=lambda r: -r["percentagem"])}


def cartao_equipa(t, v):
    estado = f' · está {e(t["estado"].lower())}' if t["estado"] else ""
    saiu = " · já não está na equipa" if not t["ainda_no_plantel"] else ""
    return (
        f'<div class="cartao"><div class="barra-topo"><span class="nome">{e(t["jogador"])}</span>'
        f'<strong>{num(t["percentagem"])}%</strong></div>'
        f'<div class="medidor {v.classe(t["nome"])}"><div style="width:{t["percentagem"]:.1f}%"></div></div>'
        f'<div class="meta">{num(t["pontos"])} pontos em {plural(t["jogos"], "jogo", "jogos")}{estado}{saiu}. '
        f'Os 3 melhores valem {num(t["percentagem_3_melhores"])}%.</div></div>'
        '<p class="nota">Parte dos pontos da equipa que veio do seu melhor jogador. Quanto mais alta, mais uma lesão dele custa.</p>'
    )
