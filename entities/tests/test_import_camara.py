import pytest
from django.core.management import call_command

from entities.models import (
    Legislature,
    PoliticalPerson,
    Proposition,
    Vote,
    VotingSession,
)
from entities.services.camara_api import CamaraClient
from tests.dummy_backends import DummyCamaraBackend


@pytest.fixture
def dummy_client():
    return CamaraClient(backend=DummyCamaraBackend())


@pytest.fixture
def patch_client(monkeypatch, dummy_client):
    monkeypatch.setattr(
        "entities.management.commands.import_camara.CamaraClient",
        lambda: dummy_client,
    )


@pytest.mark.django_db
class TestImportCamara:
    def test_full_import(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")

        assert Legislature.objects.count() == 1
        assert VotingSession.objects.count() == 1
        assert Proposition.objects.count() == 1
        assert Vote.objects.count() == 2

    def test_import_is_idempotent(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")
        call_command("import_camara", start_date="2026-04-01")

        assert VotingSession.objects.count() == 1
        assert Vote.objects.count() == 2
        assert Proposition.objects.count() == 1

    def test_voting_session_fields(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")

        session = VotingSession.objects.get()
        assert session.camara_id == "2162116-169"
        assert session.body == "PLEN"
        assert session.approved is True
        assert session.proposition is not None

    def test_proposition_parsed(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")

        proposition = Proposition.objects.get()
        assert proposition.camara_id == 2162116
        assert proposition.bill_type == "PL"
        assert proposition.number == 1234
        assert proposition.year == 2025

    def test_vote_types_mapped(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")

        votes = {v.camara_deputy_id: v.vote for v in Vote.objects.all()}
        assert votes[198783] == "sim"
        assert votes[198784] == "nao"

    def test_vote_matches_existing_tse_person(self, patch_client):
        existing = PoliticalPerson.objects.create(
            name="MARIA DA SILVA FERREIRA", cpf="12345678901"
        )
        call_command("import_camara", start_date="2026-04-01")

        vote = Vote.objects.get(camara_deputy_id=198783)
        assert vote.political_person == existing

    def test_vote_creates_person_when_no_match(self, patch_client):
        call_command("import_camara", start_date="2026-04-01")

        joao = PoliticalPerson.objects.get(name="JOAO PEDRO DE SOUZA")
        assert joao.cpf is None
