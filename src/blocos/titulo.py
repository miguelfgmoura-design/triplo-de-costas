"""A. Corrida ao título: classificação, ritmo, projeção e evolução."""
import math
import random
from collections import defaultdict
from datetime import date

from comum import melhor_alinhamento
from desenho import data_curta, e, grafico_linhas, num, quadro, tabela, tabela_numeros

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
            "id": t["id"], "nome": t["nome"], "abrev": t["abrev"],
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
    linhas = {t["id"]: jogos_a_utilizar(ctx, t, jogos_feitos_nba) for t in ctx.equipas}
    resultados = defaultdict(list)
    vitorias = defaultdict(int)
    for _ in range(SIMULACOES):
        finais = {i: simular(rng, totais[i], linhas[i]) for i in linhas}
        vitorias[max(finais, key=finais.get)] += 1
        for i, v in finais.items():
            resultados[i].append(v)

    projecao = []
    for t in ctx.equipas:
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
                {"id": t["id"], "nome": t["nome"], "abrev": t["abrev"], "pontos": series[t["id"]]}
                for t in ctx.equipas
            ],
        },
    }


def desenhar_classificacao(d, v):
    colunas = [("#", "p"), ("Equipa", "e"), ("Pontos", ""), ("Dif.", ""), (v.Ontem, ""), ("J", "so-largo"), ("Ritmo", "")]
    linhas = [
        [
            str(c["lugar"]),
            v.equipa(c["nome"]),
            f'<b>{num(c["pontos"])}</b>',
            "—" if c["lugar"] == 1 else num(c["diferenca_lider"]),
            num(c["pontos_ontem"]),
            str(c["jogos_ontem"]),
            num(c["ritmo_7_dias"]),
        ]
        for c in d["classificacao"]
    ]
    return quadro(
        "Classificação",
        tabela(colunas, linhas),
        nota=f"Dif.: distância para o líder. J: jogos feitos {v.ontem}. Ritmo: média de pontos nos últimos 7 dias com jogos.",
    )


def desenhar_projecao(d, v):
    partes = [p for p in d["projecao"] if p["probabilidade_titulo"] > 0]
    descricao = ", ".join(f'{p["nome"]} {num(p["probabilidade_titulo"])}%' for p in partes)
    barra = "".join(
        f'<i class="{v.classe(p["nome"])}" style="flex:{p["probabilidade_titulo"]:.1f} 1 0"></i>' for p in partes
    )
    linhas = [
        [
            v.equipa(p["nome"]),
            f'<b>{num(p["probabilidade_titulo"])}%</b>',
            num(p["total_previsto"], 0),
            f'{num(p["intervalo_80"][0], 0)}–{num(p["intervalo_80"][1], 0)}',
        ]
        for p in d["projecao"]
    ]
    corpo = (
        f'<div class="segmentos" role="img" aria-label="Probabilidade de ganhar o título: {e(descricao)}">{barra}</div>'
        + tabela([("Equipa", "e"), ("Título", ""), ("Previsto", ""), ("Intervalo", "")], linhas)
    )
    return quadro(
        "Quem vai ganhar",
        corpo,
        info=f'{num(d["simulacoes"], 0)} simulações',
        nota="Usa as médias, os jogos restantes de cada plantel e o limite de jogos, e assume que cada equipa gasta "
        "os jogos que lhe restam nos melhores jogadores. O intervalo cobre 8 em cada 10 simulações.",
    )


def desenhar_evolucao(d, v):
    datas = [data_curta(x) for x in d["evolucao"]["datas"]]
    series = [
        {"nome": s["nome"], "abrev": s["abrev"], "classe": v.classe(s["nome"]), "valores": s["pontos"]}
        for s in d["evolucao"]["series"]
    ]
    lideres = [max(s["valores"][i] for s in series) for i in range(len(datas))]
    distancias = [
        {**s, "valores": [round(s["valores"][i] - lideres[i], 1) for i in range(len(datas))]} for s in series
    ]
    grafico = grafico_linhas("Pontos acumulados de cada equipa ao longo da época", datas, series, altura=165)
    grafico_distancia = grafico_linhas(
        "Diferença de pontos de cada equipa para o líder de cada dia", datas, distancias, altura=150, rotulos_fim=True
    )
    return (
        quadro(
            "Evolução dos pontos",
            f'<div class="q-grafico">{grafico}</div>' + tabela_numeros("Ver os números, de semana a semana", datas, series),
        )
        + quadro(
            "Distância para o líder",
            f'<div class="q-grafico">{grafico_distancia}</div>' + tabela_numeros("Ver os números, de semana a semana", datas, distancias),
        )
    )
