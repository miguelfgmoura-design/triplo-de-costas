"""Prémios do mês: MVP, pior decisão e melhor contratação de cada equipa."""
from collections import Counter, defaultdict
from datetime import date

from desenho import MESES, data_curta, e, nome_curto, num, quadro, tabela

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
                for t in ctx.equipas
            ],
        })
    return {"meses": meses}


def nome_do_mes(mes):
    d = date.fromisoformat(f"{mes}-01")
    return f"{MESES[d.month - 1]} de {d.year}"


def tabela_jogador(equipas, chave, vazio, v):
    colunas = [("Eq.", "eq"), ("Jogador", "e"), ("J", ""), ("Pontos", "")]
    corpo = []
    for t in equipas:
        p = t[chave]
        if p:
            corpo.append([v.equipa_curta(t["nome"]), e(nome_curto(p["nome"])), str(p["jogos"]), f'<b>{num(p["pontos"])}</b>'])
        else:
            corpo.append([v.equipa_curta(t["nome"]), vazio, "—", "—"])
    return tabela(colunas, corpo)


def texto_banco(p):
    if not p["no_banco"]:
        return "Um titular deu pontos negativos"
    return ", ".join(f"{e(nome_curto(b['nome']))} ({num(b['pontos'])})" for b in p["no_banco"])


def tabela_pior(equipas, v):
    colunas = [("Eq.", "eq"), ("No banco", "e quebra"), ("Dia", ""), ("Perdeu", "")]
    corpo = []
    for t in equipas:
        p = t["pior_decisao"]
        if p:
            corpo.append([v.equipa_curta(t["nome"]), texto_banco(p), data_curta(p["data"]), f'<b>{num(-p["perdidos"])}</b>'])
        else:
            corpo.append([v.equipa_curta(t["nome"]), "Nenhum ponto deixado no banco.", "—", "—"])
    return tabela(colunas, corpo)


def corpo_mes(m, v):
    return (
        '<h3 class="q-sub">MVP</h3>'
        + tabela_jogador(m["equipas"], "mvp", "Sem jogos neste mês.", v)
        + '<h3 class="q-sub">Pior decisão</h3>'
        + tabela_pior(m["equipas"], v)
        + '<h3 class="q-sub">Melhor contratação</h3>'
        + tabela_jogador(m["equipas"], "melhor_contratacao", "Nenhuma jogou neste mês.", v)
    )


def desenhar(d, v):
    nota = (
        "Pior decisão: o dia em que o melhor alinhamento possível teria somado mais pontos do que o real. "
        "Melhor contratação: quem veio dos livres ou de uma troca e mais pontos somou a jogar nesse mês."
    )
    html = []
    for n, m in enumerate(d["meses"]):
        titulo = f'Prémios de {nome_do_mes(m["mes"])}'
        if n == 0:
            html.append(quadro(titulo, corpo_mes(m, v), info="em curso" if m["em_curso"] else "", nota=nota))
        else:
            html.append(f'<details class="quadro"><summary>{e(titulo)}</summary>{corpo_mes(m, v)}</details>')
    return "".join(html)
