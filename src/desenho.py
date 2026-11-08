"""Peças para desenhar o site: números e datas em português, cores das equipas e gráficos."""
import json
import math
from datetime import date, datetime
from html import escape

from comum import LISBOA

EB = " "  # espaço que não deixa partir a linha
MENOS = "−"

DIAS_SEMANA = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]
DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
]
MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def e(texto):
    """Torna seguro qualquer texto que venha de fora (nomes de equipas e jogadores)."""
    return escape(str(texto), quote=True)


def num(valor, casas=1, sinal=False):
    """Número à portuguesa: 5 488,5 (sem o ,0 quando é redondo)."""
    if valor is None:
        return "—"
    arredondado = round(valor, casas)
    texto = f"{abs(arredondado):,.{casas}f}".replace(",", EB).replace(".", ",")
    if casas and texto.endswith("," + "0" * casas):
        texto = texto[:-(casas + 1)]
    if arredondado < 0:
        return MENOS + texto
    return ("+" + texto) if sinal and arredondado > 0 else texto


def plural(n, um, varios):
    return f"{num(n, 0)}{EB}{um if n == 1 else varios}"


def data_curta(iso):
    d = date.fromisoformat(iso)
    return f"{d.day}{EB}{MESES_CURTOS[d.month - 1]}"


def dia_curto(iso):
    return DIAS_CURTOS[date.fromisoformat(iso).weekday()]


def data_longa(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} de {MESES[d.month - 1]}"


def momento_longo(iso):
    m = datetime.fromisoformat(iso).astimezone(LISBOA)
    return f"{DIAS_SEMANA[m.weekday()]}, {m.day} de {MESES[m.month - 1]}, às{EB}{m:%H:%M}"


class Vista:
    """O que todos os blocos precisam para se desenharem de forma coerente."""

    def __init__(self, stats):
        self.stats = stats
        referencia = stats["dia_de_referencia"]
        e_ontem = stats["dia_de_referencia_e_ontem"]
        self.ontem = "ontem" if e_ontem else f"a {data_curta(referencia)}"
        self.Ontem = "Ontem" if e_ontem else f"A {data_curta(referencia)}"
        series = stats.get("titulo", {}).get("evolucao", {}).get("series", [])
        reais = sorted((s for s in series if not s["fantasma"]), key=lambda s: s["id"])
        self.classes = {s["nome"]: f"e{i}" for i, s in enumerate(reais, 1)}

    def classe(self, nome):
        return self.classes.get(nome, "ef")  # a cor segue a equipa, nunca o lugar na tabela

    def ponto(self, nome):
        return f'<i class="ponto {self.classe(nome)}" aria-hidden="true"></i>'


def marcas_redondas(minimo, maximo, quantas=4):
    if maximo <= minimo:
        maximo = minimo + 1
    bruto = (maximo - minimo) / quantas
    base = 10 ** math.floor(math.log10(bruto))
    passo = next(m * base for m in (1, 2, 2.5, 5, 10) if m * base >= bruto)
    inicio = math.floor(minimo / passo) * passo
    fim = math.ceil(maximo / passo) * passo
    return [inicio + i * passo for i in range(round((fim - inicio) / passo) + 1)]


def legenda(series):
    itens = "".join(
        f'<span><i class="chave {s["classe"]}" aria-hidden="true"></i>{e(s["nome"])}</span>' for s in series
    )
    return f'<div class="legenda">{itens}</div>'


def grafico_linhas(descricao, datas, series, altura=190, rotulos_fim=False):
    """Gráfico de linhas em SVG. series: lista de {nome, classe, valores}."""
    largura = 340
    esquerda, direita, topo, baixo = 46, (50 if rotulos_fim else 12), 10, 24
    n = len(datas)
    todos = [v for s in series for v in s["valores"]] + [0]
    marcas = marcas_redondas(min(todos), max(todos))
    y_min, y_max = marcas[0], marcas[-1]
    compacto = max(abs(y_min), abs(y_max)) >= 10000

    def x(i):
        return esquerda + (largura - esquerda - direita) * (i / (n - 1) if n > 1 else 0.5)

    def y(v):
        return topo + (altura - topo - baixo) * (y_max - v) / (y_max - y_min)

    partes = []
    for marca in marcas:
        ym = y(marca)
        texto = f"{num(marca / 1000, 1)}{EB}mil" if compacto and marca else num(marca, 0)
        classe = "eixo" if marca == 0 else "grelha"
        partes.append(f'<line class="{classe}" x1="{esquerda}" x2="{largura - direita}" y1="{ym:.1f}" y2="{ym:.1f}"/>')
        partes.append(f'<text class="eixo-t" x="{esquerda - 6}" y="{ym + 4:.1f}" text-anchor="end">{texto}</text>')

    indices = sorted({round(i * (n - 1) / 3) for i in range(4)}) if n > 1 else [0]
    for i in indices:
        ancora = "start" if i == 0 and n > 1 else ("end" if i == n - 1 and n > 1 else "middle")
        partes.append(
            f'<text class="eixo-t" x="{x(i):.1f}" y="{altura - 6}" text-anchor="{ancora}">{e(datas[i])}</text>'
        )

    for s in series:
        caminho = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f} {y(v):.1f}" for i, v in enumerate(s["valores"]))
        partes.append(f'<path class="linha-g {s["classe"]}" d="{caminho}"/>')

    # Valores na ponta da linha, só quando não se atropelam.
    pontas = sorted(y(s["valores"][-1]) for s in series)
    cabem = rotulos_fim and all(b - a >= 13 for a, b in zip(pontas, pontas[1:]))
    for s in series:
        yf = y(s["valores"][-1])
        partes.append(f'<circle class="fim {s["classe"]}" cx="{x(n - 1):.1f}" cy="{yf:.1f}" r="4"/>')
        if cabem:
            partes.append(f'<text class="fim-t" x="{x(n - 1) + 9:.1f}" y="{yf + 4:.1f}">{num(s["valores"][-1], 0)}</text>')

    partes.append(f'<line class="mira" x1="0" x2="0" y1="{topo}" y2="{altura - baixo}"/>')
    dados = {
        "n": n, "x0": esquerda, "x1": largura - direita, "largura": largura, "datas": datas,
        "series": [{"nome": s["nome"], "classe": s["classe"], "v": s["valores"]} for s in series],
    }
    return (
        f'<figure class="grafico" data-d="{e(json.dumps(dados, ensure_ascii=False, separators=(",", ":")))}">'
        f"{legenda(series)}"
        f'<div class="area"><svg viewBox="0 0 {largura} {altura}" role="img" tabindex="0" '
        f'aria-label="{e(descricao)}">{"".join(partes)}</svg><div class="dica" hidden></div></div>'
        f"</figure>"
    )


def tabela_numeros(titulo, datas, series, passo=7):
    """A versão em números de um gráfico, de semana a semana."""
    indices = list(range(len(datas) - 1, -1, -passo))
    cabecalho = "".join(
        f'<th scope="col"><i class="ponto {s["classe"]}" aria-hidden="true"></i>{e(s["abrev"])}</th>' for s in series
    )
    linhas = "".join(
        f'<tr><th scope="row">{e(datas[i])}</th>'
        + "".join(f'<td>{num(s["valores"][i], 0)}</td>' for s in series)
        + "</tr>"
        for i in indices
    )
    return (
        f'<details><summary>{e(titulo)}</summary><table class="numeros"><thead><tr><th scope="col">Dia</th>'
        f"{cabecalho}</tr></thead><tbody>{linhas}</tbody></table></details>"
    )
