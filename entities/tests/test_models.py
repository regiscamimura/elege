from datetime import date

import pytest

from elections.models import Election, Position
from entities.models import (
    Candidacy,
    Coalition,
    Party,
    PoliticalPerson,
    Promise,
    Proposal,
)


@pytest.fixture
def election(db):
    return Election.objects.create(year=2022, round=1, tse_election_id=2040602022)


@pytest.fixture
def position(db):
    return Position.objects.create(name="Deputado Federal", scope="state")


@pytest.fixture
def party(db):
    return Party.objects.create(
        name="Partido dos Trabalhadores", abbreviation="PT", number=13
    )


@pytest.fixture
def person(db):
    return PoliticalPerson.objects.create(
        name="MARIA DA SILVA FERREIRA",
        cpf="12345678901",
        date_of_birth=date(1980, 5, 15),
        gender="FEM.",
    )


@pytest.fixture
def candidacy(db, person, election, party, position):
    return Candidacy.objects.create(
        political_person=person,
        election=election,
        party=party,
        position=position,
        ballot_name="MARIA SILVA",
        number="1301",
        status="Deferido",
        state="DF",
    )


class TestParty:
    def test_str(self, party):
        assert str(party) == "PT"

    def test_unique_abbreviation(self, party, db):
        with pytest.raises(Exception):
            Party.objects.create(name="Outro", abbreviation="PT", number=99)


class TestPoliticalPerson:
    def test_str(self, person):
        assert str(person) == "MARIA DA SILVA FERREIRA"

    def test_nullable_cpf(self, db):
        person = PoliticalPerson.objects.create(name="SEM CPF", cpf=None)
        assert person.cpf is None


class TestCandidacy:
    def test_str(self, candidacy):
        assert "MARIA SILVA" in str(candidacy)
        assert "PT" in str(candidacy)

    def test_person_cascade(self, candidacy, person):
        person_id = person.pk
        person.delete()
        assert not Candidacy.objects.filter(political_person_id=person_id).exists()

    def test_party_protect(self, candidacy, party):
        with pytest.raises(Exception):
            party.delete()

    def test_coalition_set_null(self, candidacy, election, db):
        coalition = Coalition.objects.create(name="Test Coalition", election=election)
        candidacy.coalition = coalition
        candidacy.save()
        coalition.delete()
        candidacy.refresh_from_db()
        assert candidacy.coalition is None


class TestPromiseChain:
    def test_proposal_to_promise(self, candidacy, db):
        proposal = Proposal.objects.create(
            candidacy=candidacy,
            raw_text="Vamos investir em educação infantil e creches.",
            pdf_url="https://example.com/proposal.pdf",
        )
        promise = Promise.objects.create(
            proposal=proposal,
            text="Investir em educação infantil e creches",
            category="education",
            extracted_by="claude",
        )
        assert candidacy.proposals.count() == 1
        assert proposal.promises.count() == 1
        assert promise.category == "education"

    def test_candidacy_cascade_deletes_proposals(self, candidacy, db):
        proposal = Proposal.objects.create(candidacy=candidacy, raw_text="test")
        Promise.objects.create(proposal=proposal, text="test promise")
        candidacy.delete()
        assert Proposal.objects.count() == 0
        assert Promise.objects.count() == 0
