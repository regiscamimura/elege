import os

import pytest
import vcr

from legislature.services.camara_api import CamaraClient, HTTPBackend

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")

camara_vcr = vcr.VCR(
    cassette_library_dir=CASSETTES_DIR,
    record_mode="once",
    match_on=["uri", "method"],
    decode_compressed_response=True,
)


@pytest.fixture
def live_client():
    return CamaraClient(backend=HTTPBackend(delay=0.1))


class TestCamaraIntegration:
    @camara_vcr.use_cassette("deputies_df.yaml")
    def test_list_deputies_df(self, live_client):
        deputies = live_client.list_deputies(uf="DF", legislature_id=57)
        assert len(deputies) > 0
        assert all("nome" in d for d in deputies)
        assert all(d["siglaUf"] == "DF" for d in deputies)

    @camara_vcr.use_cassette("voting_sessions.yaml")
    def test_list_voting_sessions(self, live_client):
        sessions = live_client.list_voting_sessions(start_date="2026-04-01")
        assert isinstance(sessions, list)
        assert len(sessions) > 0
        assert all("id" in s for s in sessions)

    @camara_vcr.use_cassette("votes_for_session.yaml")
    def test_get_votes_for_session(self, live_client):
        sessions = live_client.list_voting_sessions(start_date="2026-04-01")
        for session in sessions:
            votes = live_client.get_votes(session["id"])
            if votes:
                assert "tipoVoto" in votes[0]
                assert "deputado_" in votes[0]
                break
