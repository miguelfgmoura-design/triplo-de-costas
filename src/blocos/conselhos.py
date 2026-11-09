"""D. Conselhos táticos: livres, lesões e calendário dos próximos 7 dias. Iguais para os 3."""
from comum import NOMES_LUGARES, melhor_alinhamento
from desenho import data_curta, dia_curto, e, nome_curto, num, quadro, tabela

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
    for t in ctx.equipas:
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
    for t in ctx.equipas:
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


LUGARES_CURTOS = {"Lesionados": "IR"}


def etiqueta_estado(estado):
    if not estado:
        return ""
    gravidade = "critico" if estado in ("Fora", "Suspenso") else "alerta"
    return f'<span class="etiqueta {gravidade}"><i aria-hidden="true"></i>{e(estado)}</span>'


def lista_livres(linhas):
    if not linhas:
        return '<p class="nota">Sem jogadores com jogos suficientes.</p>'
    colunas = [("Jogador", "e quebra"), ("NBA", "tx"), ("Pos.", "tx"), ("Próx.", ""), ("J", ""), ("Média", "")]
    corpo = []
    for x in linhas:
        estado = f' {etiqueta_estado(x["estado"])}' if x["estado"] else ""
        waiver = ' <span class="etiqueta">Waiver</span>' if x["em_waiver"] else ""
        corpo.append([
            f'{e(nome_curto(x["nome"]))}{estado}{waiver}',
            e(x["nba"]),
            e("/".join(x["posicoes"])),
            str(x["jogos_proximos_7_dias"]),
            str(x["jogos"]),
            f'<b>{num(x["media"])}</b>',
        ])
    return tabela(colunas, corpo)


def linhas_lesoes(linhas, v):
    if not linhas:
        return '<p class="nota">Ninguém lesionado nos plantéis.</p>'
    colunas = [("Jogador", "e"), ("Eq.", "eq"), ("Lugar", "tx"), ("Estado", "tx"), ("Regresso", "")]
    corpo = []
    for x in linhas:
        if x["fora_da_epoca"]:
            quando = "fim da época"
        elif x["regresso"]:
            quando = data_curta(x["regresso"])
        elif x["estado"] == "Fora":
            quando = "sem data"
        else:
            quando = "—"
        lugar = e(LUGARES_CURTOS.get(x["lugar"], x["lugar"]))
        if x["em_posicao_ativa"]:
            lugar = f'<i class="ponto-critico" role="img" aria-label="Numa posição ativa"></i>{lugar}'
        corpo.append([
            f'{e(nome_curto(x["nome"]))} <span class="mu">{e(x["nba"])}</span>',
            v.equipa_curta(x["equipa"]),
            lugar,
            etiqueta_estado(x["estado"]),
            quando,
        ])
    return tabela(colunas, corpo)


def intensidade(valor, cortes):
    return sum(1 for corte in cortes if valor >= corte)


def celulas(dias, chave, cortes):
    return "".join(
        f'<td><span class="q q{intensidade(d[chave], cortes)}">{d[chave]}</span></td>' for d in dias
    )


def quadro_calendario(c, v):
    titulo = "Jogos nos próximos 7 dias"
    if not c["dias"]:
        return quadro(titulo, '<p class="nota">A época regular já acabou.</p>')
    cabecalho = "".join(
        f'<th scope="col">{dia_curto(d["data"])}<b>{data_curta(d["data"]).split(chr(160))[0]}</b></th>' for d in c["dias"]
    )
    linhas = [f'<tr><th scope="row">NBA</th>{celulas(c["dias"], "jogos_nba", (1, 4, 7, 10))}<td></td><td></td></tr>']
    for t in c["equipas"]:
        linhas.append(
            f'<tr><th scope="row">{v.equipa_curta(t["nome"])}</th>{celulas(t["dias"], "jogos", (1, 4, 6, 8))}'
            f'<td>{t["total"]}</td><td><b>{t["utilizaveis"]}</b></td></tr>'
        )
    mais = ", ".join(
        f'{dia_curto(d["data"])} {data_curta(d["data"])} ({d["jogos_nba"]})'
        for d in c["dias_com_mais_jogos"] if d["jogos_nba"]
    )
    tabela_dias = (
        '<div class="t-caixa"><table class="t cal"><thead><tr><th scope="col"><span class="so-leitor">Equipa</span></th>'
        f'{cabecalho}<th scope="col">Tot.</th><th scope="col">Úteis</th></tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'
    )
    return quadro(
        titulo,
        tabela_dias,
        nota=f"Dias com mais jogos: {mais}. Úteis: os jogos que cabem nas posições. Quanto mais forte a cor, mais jogos.",
    )


def desenhar(d, v):
    return "".join([
        quadro("Melhores livres", lista_livres(d["livres"]["ultimos_7_dias"]), info="últimos 7 dias"),
        quadro(
            "Melhores livres",
            lista_livres(d["livres"]["ultimos_15_dias"]),
            info="últimos 15 dias",
            nota="Ordenados por pontos por jogo, porque com limite de jogos a qualidade pesa mais do que a quantidade. "
            "Próx.: jogos nos próximos 7 dias. J: jogos feitos nesse período.",
        ),
        quadro(
            "Lesões nos plantéis",
            linhas_lesoes(d["lesoes"], v),
            nota="Ponto vermelho no lugar: não joga e está a ocupar uma posição ativa.",
        ),
        quadro_calendario(d["calendario"], v),
    ])
