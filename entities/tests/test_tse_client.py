import pytest

from entities.services.tse_api import TSEClient
from tests.dummy_backends import DummyTSEBackend


@pytest.fixture
def backend():
    return DummyTSEBackend()


@pytest.fixture
def client(backend):
    return TSEClient(backend=backend)


def test_get_election_id(client):
    election_id = client.get_election_id(2022)
    assert election_id == 2040602022


def test_get_election_id_not_found(client):
    with pytest.raises(ValueError, match="No election found"):
        client.get_election_id(9999)


def test_list_positions(client):
    positions = client.list_positions("DF", 2040602022)
    assert len(positions) == 1
    assert positions[0]["nome"] == "Deputado Federal"


def test_list_candidates(client):
    candidates = client.list_candidates(2022, "DF", 2040602022, 6)
    assert len(candidates) == 2
    assert candidates[0]["nomeUrna"] == "MARIA SILVA"


def test_get_candidate_detail(client):
    detail = client.get_candidate_detail(2022, "DF", 2040602022, 70001000001)
    assert detail["cpf"] == "12345678901"
    assert detail["ocupacao"] == "Professora"


def test_backend_tracks_calls(client, backend):
    client.list_elections()
    client.list_positions("DF", 2040602022)
    assert len(backend.calls) == 2
    assert backend.calls[0] == "/eleicao/ordinarias"
