"""Os menus do site e o que aparece em cada um.

Para mudar a organização do site, basta mexer nas listas MENUS e FICHA.
"""
import traceback

from blocos import conselhos, destaques, estrela, perdas, premios, previsao, titulo
from desenho import e

INDISPONIVEL = '<p class="nota">Este bloco não ficou disponível hoje.</p>'


def _simbolo(desenho):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{desenho}</svg>'


SIMBOLOS = {
    "hoje": _simbolo('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>'),
    "titulo": _simbolo('<path d="M8 4h8v7a4 4 0 0 1-8 0z"/><path d="M8 6H4v2a4 4 0 0 0 4 4M16 6h4v2a4 4 0 0 1-4 4M12 15v4M8 20h8"/>'),
    "equipa": _simbolo('<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6"/><path d="M16 4.8a3.5 3.5 0 0 1 0 6.4M17.5 14.5c2.1.8 3.5 2.9 3.5 5.5"/>'),
    "jogadores": _simbolo('<path d="M8 3 4 5v5l3 1v10h10V11l3-1V5l-4-2a4 4 0 0 1-8 0z"/>'),
    "conselhos": _simbolo('<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>'),
}

# Cada peça é: (bloco de dados, título, função que a desenha).
# O comentário entra no início de "hoje" e o menu "equipa" é construído pela FICHA.
MENUS = [
    {"id": "hoje", "nome": "Hoje", "pecas": [
        ("titulo", "Classificação", titulo.desenhar_classificacao),
        ("destaques", "Destaques do dia", destaques.desenhar_dia),
    ]},
    {"id": "titulo", "nome": "Título", "pecas": [
        ("titulo", "Quem vai ganhar", titulo.desenhar_projecao),
        ("titulo", "Evolução dos pontos", titulo.desenhar_evolucao),
        ("premios", "Prémios do mês", premios.desenhar),
    ]},
    {"id": "equipa", "nome": "Equipa", "pecas": []},
    {"id": "jogadores", "nome": "Jogadores", "pecas": [
        ("destaques", "Em alta e em baixa", destaques.desenhar_forma),
        ("previsao", "Real vs. projeção da ESPN", previsao.desenhar),
    ]},
    {"id": "conselhos", "nome": "Conselhos", "pecas": [
        ("conselhos", "Conselhos táticos", conselhos.desenhar),
    ]},
]

# Cada parte da ficha é: (título, bloco, lista de equipas, campo com o nome, função).
FICHA = [
    ("MVP e flop do dia", "destaques", "por_equipa", "equipa", destaques.cartao_equipa),
    ("Onde perde pontos", "perdas", "equipas", "nome", perdas.cartao_equipa),
    ("Dependência da estrela", "estrela", "equipas", "nome", estrela.cartao_equipa),
]


def _seccao(titulo_seccao, corpo):
    return f"<section><h2>{e(titulo_seccao)}</h2>{corpo}</section>"


def peca(stats, vista, bloco, titulo_seccao, desenhar):
    """Desenha uma peça. Se falhar, as outras continuam a aparecer."""
    dados = stats.get(bloco) or {"erro": True}
    try:
        if dados.get("erro"):
            raise ValueError(f"bloco {bloco} sem dados")
        corpo = desenhar(dados, vista)
    except Exception:
        traceback.print_exc()
        corpo = INDISPONIVEL
    return _seccao(titulo_seccao, corpo)


def _parte_da_ficha(stats, vista, nome, titulo_parte, bloco, lista, campo, desenhar):
    try:
        item = next(x for x in stats[bloco][lista] if x[campo] == nome)
        corpo = desenhar(item, vista)
    except Exception:
        traceback.print_exc()
        corpo = INDISPONIVEL
    return _seccao(titulo_parte, corpo)


def _nomes_das_equipas(stats):
    classificacao = (stats.get("titulo") or {}).get("classificacao")
    if classificacao:
        return [c["nome"] for c in classificacao]
    return [t["nome"] for t in (stats.get("perdas") or {}).get("equipas", [])]


def painel_equipa(stats, vista):
    """Uma ficha por equipa e uma lista para escolher qual ver, igual para todos."""
    nomes = _nomes_das_equipas(stats)
    if not nomes:
        return _seccao("Equipa", INDISPONIVEL)
    opcoes = "".join(
        f'<option value="{i}" data-classe="{vista.classe(n)}">{e(n)}</option>' for i, n in enumerate(nomes)
    )
    fichas = "".join(
        f'<div class="ficha" data-equipa="{i}"><h2 class="ficha-titulo">{e(n)}</h2>'
        + "".join(_parte_da_ficha(stats, vista, n, *parte) for parte in FICHA)
        + "</div>"
        for i, n in enumerate(nomes)
    )
    return (
        '<div class="escolha"><label for="escolha-equipa">Escolhe a equipa</label>'
        '<div class="escolha-caixa"><i id="escolha-ponto" class="ponto" aria-hidden="true"></i>'
        f'<select id="escolha-equipa">{opcoes}</select></div></div>{fichas}'
    )
