import pytest
from django.core.management import call_command

from elections.models import Election, Position
from entities.models import Candidacy, Coalition, Party, PoliticalPerson
from entities.services.tse_api import TSEClient
from tests.dummy_backends import DummyTSEBackend


@pytest.fixture
def dummy_client():
    return TSEClient(backend=DummyTSEBackend())


@pytest.mark.django_db
class TestImportTSE:
    def test_full_import(self, dummy_client, monkeypatch):
        monkeypatch.setattr(
            "entities.management.commands.import_tse.TSEClient",
            lambda: dummy_client,
        )
        call_command("import_tse", year=2022, uf="DF")

        assert Election.objects.count() == 1
        assert Position.objects.count() == 1
        assert Party.objects.count() == 2
        assert PoliticalPerson.objects.count() == 2
        assert Candidacy.objects.count() == 2

    def test_import_is_idempotent(self, dummy_client, monkeypatch):
        monkeypatch.setattr(
            "entities.management.commands.import_tse.TSEClient",
            lambda: dummy_client,
        )
        call_command("import_tse", year=2022, uf="DF")
        call_command("import_tse", year=2022, uf="DF")

        assert PoliticalPerson.objects.count() == 2
        assert Candidacy.objects.count() == 2

    def test_coalition_created_for_valid_name(self, dummy_client, monkeypatch):
        monkeypatch.setattr(
            "entities.management.commands.import_tse.TSEClient",
            lambda: dummy_client,
        )
        call_command("import_tse", year=2022, uf="DF")

        assert Coalition.objects.count() == 1
        coalition = Coalition.objects.first()
        assert coalition.name == "Brasil da Esperança"

    def test_no_coalition_for_isolated_party(self, dummy_client, monkeypatch):
        monkeypatch.setattr(
            "entities.management.commands.import_tse.TSEClient",
            lambda: dummy_client,
        )
        call_command("import_tse", year=2022, uf="DF")

        pl_candidacy = Candidacy.objects.get(tse_id=70001000002)
        assert pl_candidacy.coalition is None

    def test_person_fields_populated(self, dummy_client, monkeypatch):
        monkeypatch.setattr(
            "entities.management.commands.import_tse.TSEClient",
            lambda: dummy_client,
        )
        call_command("import_tse", year=2022, uf="DF")

        maria = PoliticalPerson.objects.get(cpf="12345678901")
        assert maria.name == "MARIA DA SILVA FERREIRA"
        assert maria.gender == "FEM."
        assert maria.occupation == "Professora"
        assert str(maria.date_of_birth) == "1980-05-15"
