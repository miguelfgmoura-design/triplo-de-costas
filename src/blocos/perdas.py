"""B. Onde perdes pontos: volume, eficiência, banco, vagas, ausências e limite de jogos."""
import math
from collections import Counter

from comum import NOMES_LUGARES, melhor_alinhamento
from desenho import data_curta, e, num

TITULO = "Onde perdes pontos"
MENU = "Perdas"


def analisar_dia(equipa_do_dia, ctx):
    """O que aconteceu a uma equipa num dia, comparado com o melhor possível."""
    fora = [j for j in equipa_do_dia["jogadores"] if j["lugar"] not in ctx.lugares_ativos]
    jogaram = [j for j in equipa_do_dia["jogadores"] if j["jogou"] and j["posicoes"]]
    positivos = [j for j in jogaram if j["pontos"] > 0]
    melhores = melhor_alinhamento([(j["pontos"], set(j["posicoes"])) for j in positivos], ctx.lugares)
    maximo_pontos = sum(positivos[i]["pontos"] for i in melhores)
    maximo_jogos = len(melhor_alinhamento([(1, set(j["posicoes"])) for j in jogaram], ctx.lugares))
    return {
        "banco_bruto": sum(j["pontos"] for j in fora if j["jogou"]),
        "perdidos": max(0.0, maximo_pontos - equipa_do_dia["pontos"]),
        "vagas_sem_jogo": len(ctx.lugares) - equipa_do_dia["jogos"],
        "vagas_evitaveis": max(0, maximo_jogos - equipa_do_dia["jogos"]),
    }


def ritmo_do_limite(ctx, equipa, jogos_feitos, dias_jogados):
    usados = sum(equipa["jogos_por_lugar"].values())
    restantes = ctx.limite_total - usados
    dias_futuros = ctx.periodos_futuros
    por_dia = jogos_feitos / dias_jogados if dias_jogados else 0.0
    resultado = {
        "usados": usados, "limite": ctx.limite_total, "restantes": restantes,
        "dias_com_jogos_restantes": len(dias_futuros),
        "jogos_por_dia_ate_agora": round(por_dia, 2),
        "jogos_por_dia_para_chegar_ao_fim": round(restantes / len(dias_futuros), 2) if dias_futuros else None,
        "esgota_em": None,
        "sobram_no_fim": 0,
    }
    if por_dia and por_dia * len(dias_futuros) > restantes:
        indice = max(0, min(len(dias_futuros) - 1, math.ceil(restantes / por_dia) - 1))
        resultado["esgota_em"] = ctx.data_do_periodo(dias_futuros[indice]).isoformat()
    else:
        resultado["sobram_no_fim"] = round(restantes - por_dia * len(dias_futuros))
    resultado["por_posicao"] = [
        {"posicao": NOMES_LUGARES[k], "usados": equipa["jogos_por_lugar"].get(str(k), 0), "limite": v}
        for k, v in ctx.limites.items()
    ]
    return resultado


def calcular(ctx):
    resultado = []
    dias_jogados = len(ctx.dias_com_jogos)
    for t in ctx.reais:
        acumulado = Counter()
        falhas = Counter()
        pontos = jogos = 0
        for dia in ctx.dias_com_jogos:
            hoje = ctx.equipa_no_dia(dia, t["id"])
            pontos += hoje["pontos"]
            jogos += hoje["jogos"]
            analise = analisar_dia(hoje, ctx)
            acumulado.update(analise)
            for j in hoje["jogadores"]:
                if j["tinha_jogo"] and not j["jogou"]:
                    falhas[j["nome"]] += 1
        ontem = analisar_dia(ctx.equipa_no_dia(ctx.dia_ref, t["id"]), ctx)
        resultado.append({
            "id": t["id"], "nome": t["nome"],
            "jogos_feitos": jogos,
            "pontos_por_jogo": round(pontos / jogos, 1) if jogos else 0.0,
            "banco": {
                "ontem_no_banco": round(ontem["banco_bruto"], 1),
                "ontem_perdidos": round(ontem["perdidos"], 1),
                "epoca_no_banco": round(acumulado["banco_bruto"], 1),
                "epoca_perdidos": round(acumulado["perdidos"], 1),
            },
            "vagas": {
                "por_dia_sem_jogo": round(acumulado["vagas_sem_jogo"] / dias_jogados, 1),
                "epoca_evitaveis": acumulado["vagas_evitaveis"],
                "ontem_evitaveis": ontem["vagas_evitaveis"],
            },
            "jogos_falhados": {
                "total": sum(falhas.values()),
                "mais_falhou": [{"nome": n, "jogos": v} for n, v in falhas.most_common(3)],
            },
            "limite_de_jogos": ritmo_do_limite(ctx, t, jogos, dias_jogados),
        })
    return {"equipas": sorted(resultado, key=lambda t: -t["banco"]["epoca_perdidos"])}


def frase_limite(limite):
    if limite["esgota_em"]:
        return (
            f'A este ritmo ({num(limite["jogos_por_dia_ate_agora"])} por dia com jogos), o limite acaba a '
            f'{data_curta(limite["esgota_em"])}. Para chegar ao fim chegam '
            f'{num(limite["jogos_por_dia_para_chegar_ao_fim"])} por dia.'
        )
    return f'A este ritmo sobram {num(limite["sobram_no_fim"], 0)} jogos no fim da época.'


def desenhar(d, v):
    liga = v.stats["liga"]
    por_posicao = liga["jogos_por_posicao"]
    html = [
        f'<p class="nota">Cada equipa só pode usar {num(liga["limite_total_jogos"], 0)} jogos na época: '
        f'{por_posicao.get("PG")} em cada posição e {por_posicao.get("UT")} nas três UT. Por isso, depois de garantires '
        "que chegas ao limite, os pontos por jogo valem mais do que jogar todos os dias.</p>"
    ]
    for t in d["equipas"]:
        banco = t["banco"]
        vagas = t["vagas"]
        falhas = t["jogos_falhados"]
        limite = t["limite_de_jogos"]
        classe = v.classe(t["nome"])
        quem = ", ".join(f'{e(x["nome"])} ({x["jogos"]})' for x in falhas["mais_falhou"])
        posicoes = "".join(
            f'<span>{e(p["posicao"])} {p["usados"]}/{p["limite"]}</span>' for p in limite["por_posicao"]
        )
        largura = min(100.0, 100 * limite["usados"] / limite["limite"])
        html.append(
            f'<article class="cartao"><h3 class="nome">{v.ponto(t["nome"])}{e(t["nome"])}</h3>'
            f'<div class="grelha-2"><div class="tile"><span>Jogos feitos</span><strong>{num(t["jogos_feitos"], 0)}</strong></div>'
            f'<div class="tile"><span>Pontos por jogo</span><strong>{num(t["pontos_por_jogo"])}</strong></div></div>'
            '<dl class="dados-linhas">'
            f'<div><dt>Perdidos no banco</dt><dd><small>{v.ontem}: {num(banco["ontem_perdidos"])}</small>{num(banco["epoca_perdidos"])}</dd></div>'
            f'<div><dt>Marcados no banco</dt><dd><small>{v.ontem}: {num(banco["ontem_no_banco"])}</small>{num(banco["epoca_no_banco"])}</dd></div>'
            f'<div><dt>Posições sem jogo, por dia</dt><dd><small>evitáveis: {vagas["epoca_evitaveis"]}</small>{num(vagas["por_dia_sem_jogo"])}</dd></div>'
            f'<div><dt>Jogos falhados</dt><dd>{falhas["total"]}</dd><dd class="quem">{quem or "Ninguém falhou jogos."}</dd></div>'
            "</dl>"
            f'<div class="limite {classe}"><div class="limite-topo"><span>Limite de jogos</span>'
            f'<span>{limite["usados"]} de {num(limite["limite"], 0)}</span></div>'
            f'<div class="medidor"><div style="width:{largura:.1f}%"></div></div>'
            f'<div class="meta">{frase_limite(limite)}</div>'
            f'<details><summary>Jogos por posição</summary><div class="chips">{posicoes}</div></details></div>'
            "</article>"
        )
    html.append(
        '<p class="nota">Perdidos no banco: o que o melhor alinhamento possível teria somado a mais. '
        "Marcados no banco: tudo o que quem não estava a jogar marcou. "
        "Evitáveis: vezes na época em que havia uma posição livre e alguém do banco a jogar. "
        "Jogos falhados: a equipa da NBA jogou e o jogador não, por lesão ou outra ausência.</p>"
    )
    return "".join(html)
