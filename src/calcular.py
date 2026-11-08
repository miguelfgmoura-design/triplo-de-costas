"""Lê os dados guardados, calcula as estatísticas e escreve dados/stats.json."""
import traceback
from datetime import date, timedelta

from blocos import BLOCOS
from comum import (
    DIAS, FICHEIRO_ATUAL, FICHEIRO_PROJECOES, FICHEIRO_STATS, FORA_DO_CINCO, NOMES_LUGARES,
    escrever_json, ler_json,
)
from percursos import calcular_entradas


class Contexto:
    """Tudo o que os blocos precisam de saber, já arrumado."""

    def __init__(self):
        self.atual = ler_json(FICHEIRO_ATUAL)
        self.dias = [ler_json(f) for f in sorted(DIAS.glob("*.json"))]
        liga = self.atual["liga"]
        self.primeiro_dia = date.fromisoformat(liga["primeiro_dia"])
        self.periodo_final = liga["periodo_final"]
        self.calendario = {int(k): set(v) for k, v in self.atual["calendario"].items()}

        self.equipas = self.atual["equipas"]
        self.reais = [t for t in self.equipas if not t["fantasma"]]
        self.ids_reais = {t["id"] for t in self.reais}
        self.fantasmas = [t for t in self.equipas if t["fantasma"]]

        contagem = {int(k): v for k, v in self.atual["lugares"]["contagem"].items()}
        self.lugares_ativos = {k for k in contagem if k not in FORA_DO_CINCO}
        self.lugares = [k for k in sorted(self.lugares_ativos) for _ in range(contagem[k])]
        self.limites = {
            int(k): int(v) for k, v in self.atual["lugares"]["limites_jogos"].items() if v
        }
        self.limite_total = sum(self.limites.values())

        self.dias_com_jogos = [d for d in self.dias if self.calendario.get(d["periodo"])]
        self.dia_ref = self.dias_com_jogos[-1]
        self.ultimo_periodo = self.dias[-1]["periodo"]
        self.periodo_hoje = self.ultimo_periodo + 1
        self.periodos_futuros = [
            p for p in range(self.periodo_hoje, self.periodo_final + 1) if self.calendario.get(p)
        ]

        self.draft = self.atual.get("draft", [])
        self.jogadores = self.atual.get("jogadores", {})
        self.projecoes = ler_json(FICHEIRO_PROJECOES) if FICHEIRO_PROJECOES.exists() else {}
        self.entradas = calcular_entradas(self.dias, self.draft, self.lugares_ativos)

    def data_do_periodo(self, periodo):
        return self.primeiro_dia + timedelta(days=periodo - 1)

    def periodo_da_data(self, dia):
        return (dia - self.primeiro_dia).days + 1

    def equipa_no_dia(self, dia, id_equipa):
        return next(t for t in dia["equipas"] if t["id"] == id_equipa)

    def jogadores_nos_planteis(self):
        return {j["id"]: j for t in self.equipas for j in t["plantel"]}


def principal():
    ctx = Contexto()
    ref = ctx.dia_ref
    stats = {
        "atualizado_em": ctx.atual["atualizado_em"],
        "liga": {
            "nome": ctx.atual["liga"]["nome"],
            "formato": "Pontos acumulados na época, sem confrontos semanais",
            "jogos_por_posicao": {NOMES_LUGARES[k]: v for k, v in ctx.limites.items()},
            "limite_total_jogos": ctx.limite_total,
        },
        "ultimo_dia_fechado": ctx.dias[-1]["data"],
        "dia_de_referencia": ref["data"],
        "dia_de_referencia_e_ontem": ref["periodo"] == ctx.ultimo_periodo,
        "verificacao": ctx.atual.get("verificacao"),
        "fantasma": [t["nome"] for t in ctx.fantasmas],
    }
    falhas = 0
    for nome, modulo in BLOCOS.items():
        try:
            stats[nome] = modulo.calcular(ctx)
        except Exception:  # um bloco com problemas não pode deitar os outros abaixo
            falhas += 1
            traceback.print_exc()
            stats[nome] = {"erro": True}
    escrever_json(FICHEIRO_STATS, stats)
    print(f"stats.json escrito: {len(BLOCOS) - falhas} blocos bem, {falhas} com erro.")


if __name__ == "__main__":
    principal()
