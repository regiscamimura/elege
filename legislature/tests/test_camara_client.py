import pytest

from legislature.services.camara_api import CamaraClient
from tests.dummy_backends import DummyCamaraBackend


@pytest.fixture
def backend():
    return DummyCamaraBackend()


@pytest.fixture
def client(backend):
    return CamaraClient(backend=backend)


def test_list_voting_sessions(client):
    sessions = client.list_voting_sessions(start_date="2026-04-01")
    assert len(sessions) == 1
    assert sessions[0]["id"] == "2162116-169"


def test_get_votes(client):
    votes = client.get_votes("2162116-169")
    assert len(votes) == 2
    assert votes[0]["tipoVoto"] == "Sim"
    assert votes[1]["deputado_"]["siglaUf"] == "DF"


def test_backend_tracks_calls(client, backend):
    client.list_deputies(uf="DF")
    assert len(backend.calls) == 1
    path, params = backend.calls[0]
    assert path == "/deputados"
    assert params["siglaUf"] == "DF"
