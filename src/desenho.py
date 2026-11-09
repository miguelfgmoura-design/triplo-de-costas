"""Peças para desenhar o site: números e datas em português, cores das equipas e gráficos."""
import json
import math
from datetime import date, datetime
from html import escape

from comum import LISBOA

EB = " "  # espaço que não deixa partir a linha
MENOS = "−"

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


def momento_curto(iso):
    m = datetime.fromisoformat(iso).astimezone(LISBOA)
    return f"{m.day}{EB}{MESES_CURTOS[m.month - 1]}, {m:%H:%M}"


class Vista:
    """O que todos os blocos precisam para se desenharem de forma coerente."""

    def __init__(self, stats):
        self.stats = stats
        referencia = stats["dia_de_referencia"]
        e_ontem = stats["dia_de_referencia_e_ontem"]
        self.ontem = "ontem" if e_ontem else f"a {data_curta(referencia)}"
        self.Ontem = "Ontem" if e_ontem else data_curta(referencia)
        series = stats.get("titulo", {}).get("evolucao", {}).get("series", [])
        self.classes = {s["nome"]: f"e{i}" for i, s in enumerate(sorted(series, key=lambda s: s["id"]), 1)}
        self.abrevs = {s["nome"]: s["abrev"] for s in series}

    def classe(self, nome):
        return self.classes.get(nome, "e0")  # a cor segue a equipa, nunca o lugar na tabela

    def ponto(self, nome):
        return f'<i class="ponto {self.classe(nome)}" aria-hidden="true"></i>'

    def equipa(self, nome):
        return f"{self.ponto(nome)}{e(nome)}"

    def equipa_curta(self, nome):
        return f"{self.ponto(nome)}{e(self.abrevs.get(nome, nome))}"


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


def tabela(colunas, linhas):
    """Tabela de um quadro. colunas: (título, classe); linhas: listas de HTML já protegido."""

    def atributo(classe):
        return f' class="{classe}"' if classe else ""

    cabecalho = "".join(f'<th scope="col"{atributo(c)}>{t}</th>' for t, c in colunas)
    corpo = "".join(
        "<tr>" + "".join(f"<td{atributo(c)}>{v}</td>" for (_, c), v in zip(colunas, linha)) + "</tr>"
        for linha in linhas
    )
    return f'<div class="t-caixa"><table class="t"><thead><tr>{cabecalho}</tr></thead><tbody>{corpo}</tbody></table></div>'


def tabela_numeros(titulo, datas, series, passo=7):
    """A versão em números de um gráfico, de semana a semana."""
    indices = list(range(len(datas) - 1, -1, -passo))
    colunas = [("Dia", "tx")] + [(f'<i class="ponto {s["classe"]}" aria-hidden="true"></i>{e(s["abrev"])}', "") for s in series]
    linhas = [[e(datas[i])] + [num(s["valores"][i], 0) for s in series] for i in indices]
    return f'<details class="q-mais"><summary>{e(titulo)}</summary>{tabela(colunas, linhas)}</details>'


def quadro(titulo, corpo, info="", nota=""):
    """Um quadro do site: título em cima, conteúdo e, se houver, uma nota por baixo."""
    extra = f'<span class="q-info">{info}</span>' if info else ""
    rodape = f'<p class="q-nota">{nota}</p>' if nota else ""
    return f'<section class="quadro"><header class="q-cab"><h2>{e(titulo)}</h2>{extra}</header>{corpo}{rodape}</section>'


def tile(rotulo, valor, detalhe=""):
    """Um número em destaque dentro de um quadro."""
    baixo = f'<span class="tile-s">{detalhe}</span>' if detalhe else ""
    return f'<div class="tile"><span class="tile-k">{rotulo}</span><span class="tile-v">{valor}</span>{baixo}</div>'


def nome_curto(nome):
    """Karl-Anthony Towns passa a K. Towns, como nas fichas de jogo."""
    primeiro, _, resto = nome.partition(" ")
    return f"{primeiro[0]}.{EB}{resto}" if resto else nome


def variacao(valor, sobe):
    """Diferença com seta e cor, para nunca depender só da cor."""
    classe, seta = ("sobe", "▲") if sobe else ("desce", "▼")
    return f'<span class="{classe}"><span class="seta" aria-hidden="true">{seta}</span>{num(valor, sinal=True)}</span>'
