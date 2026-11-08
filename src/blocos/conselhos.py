"""D. Conselhos táticos: livres, lesões e calendário dos próximos 7 dias. Iguais para os 3."""
from comum import NOMES_LUGARES, melhor_alinhamento
from desenho import data_curta, dia_curto, e, num, plural

TITULO = "Conselhos táticos"
MENU = "Conselhos"

JANELAS = {"ultimos_7_dias": ("u7", 2), "ultimos_15_dias": ("u15", 4)}  # janela e mínimo de jogos
QUANTOS_LIVRES = 5
DIAS_A_OLHAR = 7

ESTADOS = {
    "OUT": "Fora", "DAY_TO_DAY": "Dia a dia", "QUESTIONABLE": "Em dúvida",
    "DOUBTFUL": "Improvável", "PROBABLE": "Provável", "SUSPENSION": "Suspenso",
}


def melhores_livres(ctx, janela, minimo, periodos):
    linhas = []
    for j in ctx.atual["livres"]:
        m = j["medias"].get(janela)
        if not m or m["jogos"] < minimo or j["estado"] == "OUT" or j.get("fora_epoca"):
            continue
        linhas.append({
            "nome": j["nome"], "nba": j["nba"],
            "posicoes": [NOMES_LUGARES[p] for p in j["posicoes"] if p not in (5, 6, 11)],
            "media": round(m["media"], 1), "jogos": m["jogos"], "total": m["total"],
            "estado": ESTADOS.get(j["estado"]),
            "em_waiver": j.get("situacao") == "WAIVERS",
            "jogos_proximos_7_dias": sum(1 for p in periodos if j["nba"] in ctx.calendario.get(p, ())),
        })
    return sorted(linhas, key=lambda l: -l["media"])[:QUANTOS_LIVRES]


def lesoes(ctx):
    linhas = []
    for t in ctx.reais:
        for j in t["plantel"]:
            if j["estado"] in ESTADOS:
                linhas.append({
                    "nome": j["nome"], "equipa": t["nome"], "nba": j["nba"],
                    "estado": ESTADOS[j["estado"]],
                    "lugar": NOMES_LUGARES.get(j["lugar"], "?"),
                    "em_posicao_ativa": j["lugar"] in ctx.lugares_ativos and j["estado"] in ("OUT", "SUSPENSION"),
                    "regresso": j.get("regresso"), "fora_da_epoca": j.get("fora_epoca", False),
                })
    return sorted(linhas, key=lambda l: (l["equipa"], l["nome"]))


def calendario(ctx, periodos):
    por_dia = [
        {"data": ctx.data_do_periodo(p).isoformat(), "jogos_nba": len(ctx.calendario.get(p, ())) // 2}
        for p in periodos
    ]
    equipas = []
    for t in ctx.reais:
        dias = []
        for p in periodos:
            hoje = [
                j for j in t["plantel"]
                if j["nba"] in ctx.calendario.get(p, ()) and j["estado"] != "OUT" and j["posicoes"]
            ]
            usaveis = len(melhor_alinhamento([(1, set(j["posicoes"])) for j in hoje], ctx.lugares))
            dias.append({"data": ctx.data_do_periodo(p).isoformat(), "jogos": len(hoje), "utilizaveis": usaveis})
        equipas.append({
            "nome": t["nome"],
            "total": sum(d["jogos"] for d in dias),
            "utilizaveis": sum(d["utilizaveis"] for d in dias),
            "dias": dias,
        })
    return {
        "dias": por_dia,
        "dias_com_mais_jogos": sorted(por_dia, key=lambda d: (-d["jogos_nba"], d["data"]))[:3],
        "equipas": sorted(equipas, key=lambda e: -e["utilizaveis"]),
    }


def calcular(ctx):
    periodos = [p for p in range(ctx.periodo_hoje, ctx.periodo_hoje + DIAS_A_OLHAR) if p <= ctx.periodo_final]
    return {
        "livres": {
            nome: melhores_livres(ctx, janela, minimo, periodos)
            for nome, (janela, minimo) in JANELAS.items()
        },
        "lesoes": lesoes(ctx),
        "calendario": calendario(ctx, periodos),
    }


def etiqueta_estado(estado):
    if not estado:
        return ""
    gravidade = "critico" if estado in ("Fora", "Suspenso") else "alerta"
    return f'<span class="etiqueta {gravidade}"><i aria-hidden="true"></i>{e(estado)}</span>'


def lista_livres(linhas):
    if not linhas:
        return '<p class="nota">Sem jogadores com jogos suficientes.</p>'
    itens = []
    for x in linhas:
        waiver = ' <span class="etiqueta">Em waiver</span>' if x["em_waiver"] else ""
        itens.append(
            f'<li class="linha"><div class="cresce"><div class="nome">{e(x["nome"])}{etiqueta_estado(x["estado"])}{waiver}</div>'
            f'<div class="meta">{e(x["nba"])} · {e(", ".join(x["posicoes"]))} · '
            f'{plural(x["jogos_proximos_7_dias"], "jogo", "jogos")} em 7 dias</div></div>'
            f'<div class="direita"><strong class="grande">{num(x["media"])}</strong>'
            f'<span class="meta">por jogo, em {x["jogos"]}</span></div></li>'
        )
    return f'<ul class="lista">{"".join(itens)}</ul>'


def linhas_lesoes(linhas, v):
    if not linhas:
        return '<p class="nota">Ninguém lesionado nos plantéis.</p>'
    itens = []
    for x in linhas:
        if x["fora_da_epoca"]:
            quando = "fora até ao fim da época"
        elif x["regresso"]:
            quando = f'regresso previsto a {data_curta(x["regresso"])}'
        elif x["estado"] == "Fora":
            quando = "sem data de regresso"
        else:
            quando = ""
        detalhe = " · ".join(p for p in (e(x["nba"]), f'em {e(x["lugar"])}', quando) if p)
        ativa = ' <span class="etiqueta critico"><i aria-hidden="true"></i>Numa posição ativa</span>' if x["em_posicao_ativa"] else ""
        itens.append(
            f'<li class="linha"><div class="cresce"><div class="nome">{v.ponto(x["equipa"])}{e(x["nome"])}</div>'
            f'<div class="meta">{detalhe}</div>{ativa}</div>{etiqueta_estado(x["estado"])}</li>'
        )
    return f'<ul class="lista">{"".join(itens)}</ul>'


def intensidade(valor, cortes):
    return sum(1 for corte in cortes if valor >= corte)


def bloco_calendario(c, v):
    if not c["dias"]:
        return '<p class="nota">A época regular já acabou.</p>'
    cabecalho = "".join(
        f'<div class="cal-dia">{dia_curto(d["data"])}<b>{data_curta(d["data"]).split(chr(160))[0]}</b></div>' for d in c["dias"]
    )
    celulas_nba = "".join(
        f'<div class="q q{intensidade(d["jogos_nba"], (1, 4, 7, 10))}">{d["jogos_nba"]}</div>' for d in c["dias"]
    )
    equipas = []
    for t in c["equipas"]:
        celulas = "".join(
            f'<div class="q q{intensidade(d["jogos"], (1, 4, 6, 8))}">{d["jogos"]}</div>' for d in t["dias"]
        )
        nota = f' <small>só {t["utilizaveis"]} cabem nas posições</small>' if t["utilizaveis"] < t["total"] else ""
        equipas.append(
            f'<div class="cal-nome"><span>{v.ponto(t["nome"])}{e(t["nome"])}</span>'
            f'<span>{plural(t["total"], "jogo", "jogos")}{nota}</span></div>{celulas}'
        )
    mais = ", ".join(
        f'{dia_curto(d["data"])} {data_curta(d["data"])} ({d["jogos_nba"]})'
        for d in c["dias_com_mais_jogos"] if d["jogos_nba"]
    )
    return (
        f'<div class="calendario">{cabecalho}<div class="cal-nome"><span>Jogos na NBA</span></div>{celulas_nba}'
        f'{"".join(equipas)}</div><p class="nota" style="margin:10px 0 0">Dias com mais jogos: {mais}. Quanto mais forte a cor, mais jogos.</p>'
    )


def desenhar(d, v):
    return "".join([
        '<p class="nota">Ordenados por pontos por jogo, porque com limite de jogos a qualidade pesa mais do que a quantidade.</p>',
        f'<div class="cartao"><h3>Melhores livres, últimos 7 dias</h3>{lista_livres(d["livres"]["ultimos_7_dias"])}</div>',
        f'<div class="cartao"><h3>Melhores livres, últimos 15 dias</h3>{lista_livres(d["livres"]["ultimos_15_dias"])}</div>',
        f'<div class="cartao"><h3>Lesões nos plantéis</h3>{linhas_lesoes(d["lesoes"], v)}</div>',
        f'<div class="cartao"><h3>Jogos nos próximos 7 dias</h3>{bloco_calendario(d["calendario"], v)}</div>',
    ])
