"""A. Corrida ao título: classificação, ritmo, projeção e evolução."""
import math
import random
from collections import defaultdict
from datetime import date

from comum import melhor_alinhamento
from desenho import EB, data_curta, e, grafico_linhas, num, plural, tabela_numeros

TITULO = "Corrida ao título"
MENU = "Título"

SIMULACOES = 10000
PESO_DA_PREVISAO = 12  # a previsão da ESPN vale como 12 jogos já feitos
DISPONIBILIDADE_BASE = 0.85  # um jogador típico faz 85% dos jogos da equipa
PESO_DISPONIBILIDADE = 20
DIAS_FORA_SEM_DATA = 10  # lesionado sem data de regresso: assume 10 dias de fora


def media_esperada(j):
    """Pontos por jogo esperados: a época mistura-se com a previsão da ESPN."""
    m = j["medias"]
    epoca = m.get("epoca") or {}
    base = (m.get("proj") or m.get("anterior") or epoca or {}).get("media", 0.0)
    jogos = epoca.get("jogos", 0)
    if not jogos:
        return base
    return (jogos * epoca["media"] + PESO_DA_PREVISAO * base) / (jogos + PESO_DA_PREVISAO)


def disponibilidade(j, jogos_feitos_nba):
    feitos = (j["medias"].get("epoca") or {}).get("jogos", 0)
    possiveis = max(jogos_feitos_nba.get(j["nba"], 0), feitos)
    valor = (feitos + DISPONIBILIDADE_BASE * PESO_DISPONIBILIDADE) / (possiveis + PESO_DISPONIBILIDADE)
    return min(0.95, max(0.5, valor))


def periodo_de_regresso(j, ctx):
    if j.get("fora_epoca"):
        return math.inf
    if j["estado"] in ("OUT", "SUSPENSION"):
        if j.get("regresso"):
            return max(ctx.periodo_hoje, ctx.periodo_da_data(date.fromisoformat(j["regresso"])))
        return ctx.periodo_hoje + DIAS_FORA_SEM_DATA
    return ctx.periodo_hoje


def jogos_a_utilizar(ctx, equipa, jogos_feitos_nba):
    """Quantos jogos de cada jogador contarão até ao fim da época.

    Monta o melhor alinhamento de cada dia futuro e, como há um limite de
    jogos por posição, fica só com os jogos mais valiosos que couberem nos
    jogos que a equipa ainda tem disponíveis.
    """
    plantel = equipa["plantel"]
    info = [
        {
            "media": media_esperada(j),
            "disp": disponibilidade(j, jogos_feitos_nba),
            "regresso": periodo_de_regresso(j, ctx),
        }
        for j in plantel
    ]
    candidatos = []
    for periodo in ctx.periodos_futuros:
        hoje = [
            i for i, j in enumerate(plantel)
            if j["nba"] in ctx.calendario[periodo] and periodo >= info[i]["regresso"] and j["posicoes"]
        ]
        lista = [(info[i]["media"] * info[i]["disp"], set(plantel[i]["posicoes"])) for i in hoje]
        for n in melhor_alinhamento(lista, ctx.lugares):
            candidatos.append((lista[n][0], hoje[n]))
    candidatos.sort(reverse=True)

    restantes = sum(
        max(0, limite - equipa["jogos_por_lugar"].get(str(k), 0)) for k, limite in ctx.limites.items()
    )
    usados = 0.0
    contagem = defaultdict(int)
    for _, i in candidatos:
        if usados >= restantes:
            break
        contagem[i] += 1
        usados += info[i]["disp"]
    return [(info[i]["media"], info[i]["disp"], contagem[i]) for i in range(len(plantel)) if contagem[i]]


def simular(rng, pontos_atuais, linhas):
    total = pontos_atuais
    for media, disp, jogos in linhas:
        # Imprevisibilidade: lesões, forma do jogador na época, e variação de jogo para jogo.
        forca = disp * (1 - disp) / 0.0196 - 1
        fracao = rng.betavariate(disp * forca, (1 - disp) * forca)
        nivel = rng.gauss(media, 0.07 * media + 1.0)
        feitos = jogos * fracao
        total += feitos * nivel + rng.gauss(0, 0.28 * media * math.sqrt(feitos))
    return total


def calcular(ctx):
    totais = defaultdict(float)
    series = defaultdict(list)
    for dia in ctx.dias:
        for t in dia["equipas"]:
            totais[t["id"]] += t["pontos"]
            series[t["id"]].append(round(totais[t["id"]], 1))

    ultimos7 = ctx.dias_com_jogos[-7:]
    lider = max(totais.values())
    classificacao = []
    for t in ctx.equipas:
        hoje = ctx.equipa_no_dia(ctx.dia_ref, t["id"])
        classificacao.append({
            "id": t["id"], "nome": t["nome"], "abrev": t["abrev"], "fantasma": t["fantasma"],
            "pontos": round(totais[t["id"]], 1),
            "diferenca_lider": round(totais[t["id"]] - lider, 1),
            "pontos_ontem": hoje["pontos"],
            "jogos_ontem": hoje["jogos"],
            "ritmo_7_dias": round(
                sum(ctx.equipa_no_dia(d, t["id"])["pontos"] for d in ultimos7) / len(ultimos7), 1
            ),
        })
    classificacao.sort(key=lambda c: -c["pontos"])
    for n, c in enumerate(classificacao, 1):
        c["lugar"] = n

    jogos_feitos_nba = defaultdict(int)
    for periodo, siglas in ctx.calendario.items():
        if periodo <= ctx.ultimo_periodo:
            for s in siglas:
                jogos_feitos_nba[s] += 1

    rng = random.Random(ctx.dia_ref["data"])
    linhas = {t["id"]: jogos_a_utilizar(ctx, t, jogos_feitos_nba) for t in ctx.reais}
    resultados = defaultdict(list)
    vitorias = defaultdict(int)
    for _ in range(SIMULACOES):
        finais = {i: simular(rng, totais[i], linhas[i]) for i in ctx.ids_reais}
        vitorias[max(finais, key=finais.get)] += 1
        for i, v in finais.items():
            resultados[i].append(v)

    projecao = []
    for t in ctx.reais:
        valores = sorted(resultados[t["id"]])
        projecao.append({
            "id": t["id"], "nome": t["nome"],
            "total_previsto": round(sum(valores) / len(valores)),
            "intervalo_80": [round(valores[len(valores) // 10]), round(valores[9 * len(valores) // 10])],
            "probabilidade_titulo": round(100 * vitorias[t["id"]] / SIMULACOES, 1),
            "jogos_restantes_previstos": round(sum(d * g for _, d, g in linhas[t["id"]])),
        })
    projecao.sort(key=lambda p: -p["probabilidade_titulo"])

    return {
        "classificacao": classificacao,
        "projecao": projecao,
        "simulacoes": SIMULACOES,
        "evolucao": {
            "datas": [d["data"] for d in ctx.dias],
            "series": [
                {"id": t["id"], "nome": t["nome"], "abrev": t["abrev"], "fantasma": t["fantasma"], "pontos": series[t["id"]]}
                for t in ctx.equipas
            ],
        },
    }


def desenhar(d, v):
    linhas = []
    for c in d["classificacao"]:
        distancia = "Líder" if c["lugar"] == 1 else f'{num(c["diferenca_lider"])} do líder'
        fantasma = ' <span class="etiqueta">fantasma</span>' if c["fantasma"] else ""
        linhas.append(
            f'<li class="linha{" apagada" if c["fantasma"] else ""}"><span class="posto">{c["lugar"]}</span>'
            f'<div class="cresce"><div class="nome">{v.ponto(c["nome"])}{e(c["nome"])}{fantasma}</div>'
            f'<div class="meta">{v.Ontem}: {num(c["pontos_ontem"])} em {plural(c["jogos_ontem"], "jogo", "jogos")}'
            f' · ritmo{EB}{num(c["ritmo_7_dias"])}</div></div>'
            f'<div class="direita"><strong class="grande">{num(c["pontos"])}</strong>'
            f'<span class="meta">{distancia}</span></div></li>'
        )
    html = [
        f'<div class="cartao"><ol class="lista">{"".join(linhas)}</ol></div>',
        '<p class="nota">Ritmo: média de pontos nos últimos 7 dias com jogos.</p>',
    ]

    barras = "".join(
        f'<li><div class="barra-topo"><span class="nome">{v.ponto(p["nome"])}{e(p["nome"])}</span>'
        f'<strong>{num(p["probabilidade_titulo"])}%</strong></div>'
        f'<div class="barra {v.classe(p["nome"])}" style="width:{p["probabilidade_titulo"]:.1f}%"></div>'
        f'<div class="meta">Total previsto {num(p["total_previsto"], 0)}, '
        f'entre {num(p["intervalo_80"][0], 0)} e {num(p["intervalo_80"][1], 0)}</div></li>'
        for p in d["projecao"]
    )
    html.append(
        f'<div class="cartao"><h3>Quem vai ganhar</h3><ul class="barras">{barras}</ul></div>'
        f'<p class="nota">{num(d["simulacoes"], 0)} simulações com as médias, os jogos restantes de cada plantel '
        "e o limite de jogos. Assume que cada equipa gasta os jogos que lhe restam nos melhores jogadores. "
        "O intervalo cobre 8 em cada 10 simulações.</p>"
    )

    datas = [data_curta(x) for x in d["evolucao"]["datas"]]
    series = [
        {"nome": s["nome"], "abrev": s["abrev"], "classe": v.classe(s["nome"]), "valores": s["pontos"]}
        for s in d["evolucao"]["series"]
    ]
    reais = [s for s, o in zip(series, d["evolucao"]["series"]) if not o["fantasma"]]
    lideres = [max(s["valores"][i] for s in reais) for i in range(len(datas))]
    distancias = [
        {**s, "valores": [round(s["valores"][i] - lideres[i], 1) for i in range(len(datas))]} for s in reais
    ]
    html.append(
        '<div class="cartao"><h3>Evolução dos pontos</h3>'
        + grafico_linhas("Pontos acumulados de cada equipa ao longo da época", datas, series)
        + tabela_numeros("Ver os números, de semana a semana", datas, series)
        + '<h3 class="subtitulo">Distância para o líder</h3>'
        + grafico_linhas("Diferença de pontos de cada equipa para o líder de cada dia", datas, distancias, altura=170, rotulos_fim=True)
        + tabela_numeros("Ver os números, de semana a semana", datas, distancias)
        + "</div>"
    )
    return "".join(html)
