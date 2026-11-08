"""Pedidos à ESPN. Só leitura e sem credenciais, porque a liga está visível ao público."""
import json
import time

import requests

RAIZ_API = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{ano}"
CABECALHOS = {"User-Agent": "liga-fantasy-nba"}


class ErroESPN(Exception):
    """A ESPN não respondeu como devia."""


class ESPN:
    def __init__(self, id_liga, ano):
        self.ano = ano
        self.url_epoca = RAIZ_API.format(ano=ano)
        self.url_liga = f"{self.url_epoca}/segments/0/leagues/{id_liga}"
        self.sessao = requests.Session()

    def _pedir(self, url, parametros, cabecalhos=None, tentativas=4):
        erro = None
        for tentativa in range(tentativas):
            if tentativa:
                time.sleep(3 * 2 ** tentativa)
            try:
                resposta = self.sessao.get(
                    url, params=parametros, timeout=60,
                    headers={**CABECALHOS, **(cabecalhos or {})},
                )
            except requests.RequestException as e:
                erro = str(e)
                continue
            if resposta.status_code in (401, 403, 404):
                raise ErroESPN(f"HTTP {resposta.status_code}: {resposta.text[:200]}")
            if resposta.status_code != 200:
                erro = f"HTTP {resposta.status_code}"
                continue
            try:
                return resposta.json()
            except ValueError:
                erro = "resposta que não é JSON"
        raise ErroESPN(f"Sem resposta da ESPN após {tentativas} tentativas: {erro}")

    def liga(self, vistas, periodo=None):
        parametros = [("view", v) for v in vistas]
        if periodo is not None:
            parametros.append(("scoringPeriodId", periodo))
        return self._pedir(self.url_liga, parametros)

    def calendario_nba(self):
        return self._pedir(self.url_epoca, [("view", "proTeamSchedules_wl")])

    def jogadores_por_id(self, periodo, ids, por_pedido=50):
        """Totais e médias de uma lista de jogadores, estejam onde estiverem."""
        a = self.ano
        resultado = []
        for inicio in range(0, len(ids), por_pedido):
            filtro = {"players": {
                "filterIds": {"value": ids[inicio:inicio + por_pedido]},
                "filterStatsForTopScoringPeriodIds": {
                    "value": 1,
                    "additionalValue": [f"00{a}", f"01{a}", f"02{a}", f"03{a}", f"10{a}"],
                },
            }}
            resultado += self._pedir(
                self.url_liga,
                [("view", "kona_player_info"), ("scoringPeriodId", periodo)],
                {"x-fantasy-filter": json.dumps(filtro)},
            ).get("players", [])
        return resultado

    def jogadores_livres(self, periodo, janela, limite=40):
        """Jogadores sem equipa, do melhor para o pior na janela pedida.

        janela: "01" são os últimos 7 dias e "02" os últimos 15.
        """
        a = self.ano
        filtro = {"players": {
            "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
            "limit": limite,
            "sortAppliedStatTotal": {"sortAsc": False, "sortPriority": 1, "value": f"{janela}{a}"},
            "filterStatsForTopScoringPeriodIds": {
                "value": 5,
                "additionalValue": [f"00{a}", f"01{a}", f"02{a}", f"03{a}", f"10{a}"],
            },
        }}
        return self._pedir(
            self.url_liga,
            [("view", "kona_player_info"), ("scoringPeriodId", periodo)],
            {"x-fantasy-filter": json.dumps(filtro)},
        ).get("players", [])
