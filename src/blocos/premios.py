"""Prémios do mês: MVP, pior decisão e melhor contratação de cada equipa."""
from collections import Counter, defaultdict
from datetime import date

from desenho import MESES, data_curta, e, num, plural

from .perdas import analisar_dia


def mvp_do_mes(ctx, id_equipa, dias):
    pontos = Counter()
    jogos = Counter()
    nomes = {}
    for dia in dias:
        for j in ctx.equipa_no_dia(dia, id_equipa)["jogadores"]:
            if j["lugar"] in ctx.lugares_ativos and j["jogou"]:
                pontos[j["id"]] += j["pontos"]
                jogos[j["id"]] += 1
                nomes[j["id"]] = j["nome"]
    if not pontos:
        return None
    melhor, valor = pontos.most_common(1)[0]
    return {"nome": nomes[melhor], "pontos": round(valor, 1), "jogos": jogos[melhor]}


def pior_decisao(ctx, id_equipa, dias):
    """O dia em que o melhor alinhamento possível teria somado mais do que o real."""
    pior = None
    for dia in dias:
        hoje = ctx.equipa_no_dia(dia, id_equipa)
        perdidos = analisar_dia(hoje, ctx)["perdidos"]
        if perdidos > (pior["perdidos"] if pior else 0):
            banco = sorted(
                (j for j in hoje["jogadores"] if j["lugar"] not in ctx.lugares_ativos and j["jogou"]),
                key=lambda j: -j["pontos"],
            )
            pior = {
                "data": dia["data"],
                "perdidos": round(perdidos, 1),
                "no_banco": [{"nome": j["nome"], "pontos": j["pontos"]} for j in banco[:2]],
            }
    return pior


def melhor_contratacao(ctx, id_equipa, periodos):
    """Quem veio dos livres ou de uma troca e mais pontos somou a jogar nesse mês."""
    melhor = None
    for m in ctx.entradas[id_equipa]:
        valores = [v for p, v in m["ativos_por_periodo"].items() if p in periodos]
        pontos = sum(valores)
        if valores and (melhor is None or pontos > melhor["pontos"]):
            melhor = {"nome": m["nome"], "pontos": round(pontos, 1), "jogos": len(valores)}
    return melhor


def calcular(ctx):
    por_mes = defaultdict(list)
    for dia in ctx.dias_com_jogos:
        por_mes[dia["data"][:7]].append(dia)
    mes_atual = ctx.dias[-1]["data"][:7]
    epoca_acabou = ctx.ultimo_periodo >= ctx.periodo_final

    meses = []
    for mes in sorted(por_mes, reverse=True):
        dias = por_mes[mes]
        periodos = {d["periodo"] for d in dias}
        meses.append({
            "mes": mes,
            "em_curso": mes == mes_atual and not epoca_acabou,
            "equipas": [
                {
                    "nome": t["nome"],
                    "mvp": mvp_do_mes(ctx, t["id"], dias),
                    "pior_decisao": pior_decisao(ctx, t["id"], dias),
                    "melhor_contratacao": melhor_contratacao(ctx, t["id"], periodos),
                }
                for t in ctx.reais
            ],
        })
    return {"meses": meses}


def nome_do_mes(mes):
    d = date.fromisoformat(f"{mes}-01")
    return f"{MESES[d.month - 1]} de {d.year}"


def texto_pior(p):
    if not p["no_banco"]:
        return f"A {data_curta(p['data'])}, um titular deu pontos negativos"
    banco = ", ".join(f"{e(b['nome'])} ({num(b['pontos'])})" for b in p["no_banco"])
    return f"A {data_curta(p['data'])}, no banco: {banco}"


def linhas_premio(equipas, chave, v, com_valor, com_texto, vazio):
    itens = []
    for t in equipas:
        p = t[chave]
        if p:
            detalhe = com_texto(p)
            valor = com_valor(p)
        else:
            detalhe = vazio
            valor = "—"
        itens.append(
            f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(t["nome"])}{e(t["nome"])}</div>'
            f'<div class="meta">{detalhe}</div></div><strong class="grande">{valor}</strong></li>'
        )
    return f'<ul class="lista">{"".join(itens)}</ul>'


def corpo_mes(m, v):
    def jogador(p):
        return f"{e(p['nome'])}, em {plural(p['jogos'], 'jogo', 'jogos')}"

    return (
        '<h4 class="subtitulo">MVP</h4>'
        + linhas_premio(m["equipas"], "mvp", v, lambda p: num(p["pontos"]), jogador, "Sem jogos neste mês.")
        + '<h4 class="subtitulo">Pior decisão</h4>'
        + linhas_premio(m["equipas"], "pior_decisao", v, lambda p: num(-p["perdidos"]), texto_pior, "Nenhum ponto deixado no banco.")
        + '<h4 class="subtitulo">Melhor contratação</h4>'
        + linhas_premio(m["equipas"], "melhor_contratacao", v, lambda p: num(p["pontos"]), jogador, "Nenhuma contratação jogou neste mês.")
    )


def desenhar(d, v):
    html = []
    for n, m in enumerate(d["meses"]):
        titulo = nome_do_mes(m["mes"]).capitalize() + (" (em curso)" if m["em_curso"] else "")
        if n == 0:
            html.append(f'<article class="cartao"><h3>{e(titulo)}</h3>{corpo_mes(m, v)}</article>')
        else:
            html.append(f'<details class="cartao"><summary>{e(titulo)}</summary>{corpo_mes(m, v)}</details>')
    html.append(
        '<p class="nota">Pior decisão: o dia em que o melhor alinhamento possível teria somado mais pontos do que o real. '
        "Melhor contratação: quem veio dos livres ou de uma troca e mais pontos somou a jogar nesse mês.</p>"
    )
    return "".join(html)
