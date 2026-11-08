"""Blocos de estatísticas. Para acrescentar um, cria o ficheiro, junta-o aqui e põe-no num menu em seccoes.py."""
from . import conselhos, destaques, estrela, perdas, premios, previsao, titulo

BLOCOS = {
    "titulo": titulo,
    "perdas": perdas,
    "destaques": destaques,
    "conselhos": conselhos,
    "premios": premios,
    "estrela": estrela,
    "previsao": previsao,
}
