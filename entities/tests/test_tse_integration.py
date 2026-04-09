import os

import pytest
import vcr

from entities.services.tse_api import HTTPBackend, TSEClient

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")

tse_vcr = vcr.VCR(
    cassette_library_dir=CASSETTES_DIR,
    record_mode="once",
    match_on=["uri", "method"],
    decode_compressed_response=True,
)


@pytest.fixture
def live_client():
    return TSEClient(backend=HTTPBackend(delay=0.1))


class TestTSEIntegration:
    @tse_vcr.use_cassette("elections.yaml")
    def test_list_elections(self, live_client):
        elections = live_client.list_elections()
        assert isinstance(elections, list)
        assert len(elections) > 0
        assert all("ano" in e for e in elections)

    @tse_vcr.use_cassette("election_id_2022.yaml")
    def test_get_election_id_2022(self, live_client):
        election_id = live_client.get_election_id(2022)
        assert election_id == 2040602022

    @tse_vcr.use_cassette("positions_df_2022.yaml")
    def test_list_positions_df(self, live_client):
        positions = live_client.list_positions("DF", 2040602022)
        assert len(positions) > 0
        names = [p["nome"] for p in positions]
        assert "Deputado Federal" in names
        assert "Governador" in names

    @tse_vcr.use_cassette("candidates_df_depfed_2022.yaml")
    def test_list_candidates_df_dep_federal(self, live_client):
        candidates = live_client.list_candidates(2022, "DF", 2040602022, 6)
        assert len(candidates) > 100
        assert all("nomeUrna" in c for c in candidates)
        assert all("partido" in c for c in candidates)

    @tse_vcr.use_cassette("candidate_detail_2022.yaml")
    def test_get_candidate_detail(self, live_client):
        candidates = live_client.list_candidates(2022, "DF", 2040602022, 6)
        first_id = candidates[0]["id"]
        detail = live_client.get_candidate_detail(2022, "DF", 2040602022, first_id)
        assert detail["id"] == first_id
        assert "nomeCompleto" in detail
        assert "partido" in detail
        assert "descricaoSexo" in detail
