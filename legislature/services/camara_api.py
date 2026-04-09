import time
from typing import Any, Protocol

import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
REQUEST_DELAY = 0.3


class CamaraBackend(Protocol):
    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


class HTTPBackend:
    def __init__(self, base_url: str = BASE_URL, delay: float = REQUEST_DELAY) -> None:
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        time.sleep(self.delay)
        response = self.session.get(f"{self.base_url}{path}", params=params)
        response.raise_for_status()
        return response.json()


class CamaraClient:
    def __init__(self, backend: CamaraBackend | None = None) -> None:
        self.backend: CamaraBackend = backend or HTTPBackend()

    def list_deputies(
        self, uf: str | None = None, legislature_id: int | None = None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "ordem": "ASC",
            "ordenarPor": "nome",
            "itens": 100,
        }
        if uf:
            params["siglaUf"] = uf
        if legislature_id:
            params["idLegislatura"] = legislature_id
        data = self.backend.get("/deputados", params)
        return data.get("dados", [])

    def list_voting_sessions(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "ordem": "DESC",
            "ordenarPor": "dataHoraRegistro",
            "itens": 100,
        }
        if start_date:
            params["dataInicio"] = start_date
        if end_date:
            params["dataFim"] = end_date
        data = self.backend.get("/votacoes", params)
        return data.get("dados", [])

    def get_voting_session_detail(self, session_id: str) -> dict[str, Any]:
        data = self.backend.get(f"/votacoes/{session_id}")
        return data.get("dados", {})

    def get_votes(self, session_id: str) -> list[dict[str, Any]]:
        data = self.backend.get(f"/votacoes/{session_id}/votos")
        return data.get("dados", [])

    def get_proposition(self, proposition_id: int) -> dict[str, Any]:
        data = self.backend.get(f"/proposicoes/{proposition_id}")
        return data.get("dados", {})

    def list_voting_sessions_paginated(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        page = 1
        all_sessions: list[dict[str, Any]] = []
        while True:
            params: dict[str, Any] = {
                "ordem": "DESC",
                "ordenarPor": "dataHoraRegistro",
                "itens": 100,
                "pagina": page,
            }
            if start_date:
                params["dataInicio"] = start_date
            if end_date:
                params["dataFim"] = end_date
            data = self.backend.get("/votacoes", params)
            sessions = data.get("dados", [])
            if not sessions:
                break
            all_sessions.extend(sessions)
            page += 1
        return all_sessions
