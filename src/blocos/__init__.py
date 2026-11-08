"""Blocos de estatísticas. Para acrescentar um, cria o ficheiro e junta-o aqui."""
from . import conselhos, destaques, perdas, titulo

BLOCOS = {
    "titulo": titulo,
    "perdas": perdas,
    "destaques": destaques,
    "conselhos": conselhos,
}
