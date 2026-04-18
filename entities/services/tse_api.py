import time
from typing import Any, Protocol

import requests

BASE_URL = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1"
REQUEST_DELAY = 0.5


class TSEBackend(Protocol):
    def get(self, path: str) -> Any: ...


class HTTPBackend:
    def __init__(self, base_url: str = BASE_URL, delay: float = REQUEST_DELAY) -> None:
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()

    def get(self, path: str) -> Any:
        time.sleep(self.delay)
        response = self.session.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()


class TSEClient:
    def __init__(self, backend: TSEBackend | None = None) -> None:
        self.backend: TSEBackend = backend or HTTPBackend()

    def list_elections(self) -> list[dict[str, Any]]:
        return self.backend.get("/eleicao/ordinarias")

    def get_election_id(self, year: int) -> int:
        elections = self.list_elections()
        federal = [
            e for e in elections if e["ano"] == year and e["tipoAbrangencia"] == "F"
        ]
        if federal:
            return federal[0]["id"]
        matching = [e for e in elections if e["ano"] == year]
        if matching:
            return matching[0]["id"]
        raise ValueError(f"No election found for year {year}")

    def list_positions(self, uf: str, election_id: int) -> list[dict[str, Any]]:
        data = self.backend.get(f"/eleicao/listar/municipios/{election_id}/{uf}/cargos")
        return data.get("cargos", [])

    def list_candidates(
        self, year: int, uf: str, election_id: int, position_code: int
    ) -> list[dict[str, Any]]:
        data = self.backend.get(
            f"/candidatura/listar/{year}/{uf}/{election_id}/{position_code}/candidatos"
        )
        return data.get("candidatos", [])

    def get_candidate_detail(
        self, year: int, uf: str, election_id: int, candidate_id: int
    ) -> dict[str, Any]:
        return self.backend.get(
            f"/candidatura/buscar/{year}/{uf}/{election_id}/candidato/{candidate_id}"
        )
