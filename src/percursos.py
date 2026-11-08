"""Jogadores que entraram em cada plantel depois do draft, e o que somaram a jogar."""
from collections import defaultdict


def calcular_entradas(dias, draft, lugares_ativos):
    """Devolve, por equipa, os jogadores vindos dos livres ou de trocas.

    Compara o plantel de cada dia com o do dia anterior, a partir do draft.
    Cada entrada guarda, dia a dia, os pontos que o jogador somou em posições
    ativas enquanto esteve na equipa.
    """
    planteis = defaultdict(set)
    for escolha in draft:
        planteis[escolha["equipa"]].add(escolha["jogador"])

    entradas = defaultdict(list)
    abertas = defaultdict(dict)
    for dia in dias:
        periodo = dia["periodo"]
        for equipa in dia["equipas"]:
            id_equipa = equipa["id"]
            de_hoje = {j["id"]: j for j in equipa["jogadores"]}
            atuais = set(de_hoje)
            for id_jogador in atuais - planteis[id_equipa]:
                nova = {
                    "jogador": id_jogador, "nome": de_hoje[id_jogador]["nome"],
                    "inicio": periodo, "ativos_por_periodo": {},
                }
                abertas[id_equipa][id_jogador] = nova
                entradas[id_equipa].append(nova)
            for id_jogador in planteis[id_equipa] - atuais:
                abertas[id_equipa].pop(id_jogador, None)
            for id_jogador, entrada in abertas[id_equipa].items():
                j = de_hoje[id_jogador]
                if j["jogou"] and j["lugar"] in lugares_ativos:
                    entrada["ativos_por_periodo"][periodo] = j["pontos"]
            planteis[id_equipa] = atuais
    return entradas
