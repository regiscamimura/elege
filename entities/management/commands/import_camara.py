import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction

from entities.models import (
    Legislature,
    PoliticalPerson,
    Proposition,
    Vote,
    VotingSession,
)
from entities.services.camara_api import CamaraClient

VOTE_MAP = {
    "Sim": "sim",
    "Não": "nao",
    "Abstenção": "abstencao",
    "Obstrução": "obstrucao",
    "Art. 17": "artigo17",
}


PROPOSITION_RE = re.compile(r"^([A-Z]+)\s+(\d+)/(\d{4})$")
PROPOSITION_URL_RE = re.compile(r"/proposicoes/(\d+)$")

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


class Command(BaseCommand):
    help = "Import voting sessions and votes from Câmara dos Deputados"

    def add_arguments(self, parser):
        parser.add_argument("--start-date", type=str, default=None)
        parser.add_argument("--end-date", type=str, default=None)
        parser.add_argument("--legislature", type=int, default=57)

    def handle(self, *args, **options):
        client = CamaraClient()
        legislature = self._ensure_legislature(client, options["legislature"])

        start = (
            date.fromisoformat(options["start_date"])
            if options["start_date"]
            else legislature.start_date
        )
        end = (
            date.fromisoformat(options["end_date"])
            if options["end_date"]
            else min(date.today(), legislature.end_date)
        )

        chunks = self._month_chunks(start, end)
        self.stdout.write(
            f"Legislature {legislature.number}: importing {len(chunks)} months "
            f"{start.isoformat()} → {end.isoformat()}"
        )

        for chunk_start, chunk_end in chunks:
            label = chunk_start.strftime("%Y-%m")
            try:
                sessions = client.list_voting_sessions_paginated(
                    start_date=chunk_start.isoformat(),
                    end_date=chunk_end.isoformat(),
                )
            except Exception as exc:
                self.stderr.write(f"  {label}: skipped, {exc}")
                continue
            self.stdout.write(f"  {label}: {len(sessions)} sessions")

            for i, session_data in enumerate(sessions, 1):
                try:
                    self._import_session(client, session_data)
                except Exception as exc:
                    self.stderr.write(f"    skipped {session_data.get('id')}: {exc}")
                if i % 50 == 0:
                    self.stdout.write(f"    {i}/{len(sessions)}")

        self._print_summary()

    def _month_chunks(self, start, end):
        chunks = []
        cur = start.replace(day=1)
        while cur <= end:
            next_month = (cur + timedelta(days=32)).replace(day=1)
            chunk_end = min(next_month - timedelta(days=1), end)
            chunk_start = max(cur, start)
            chunks.append((chunk_start, chunk_end))
            cur = next_month
        return chunks

    def _ensure_legislature(self, client, number):
        cached = Legislature.objects.filter(number=number).first()
        if cached:
            return cached

        data = client.get_legislature(number)
        return Legislature.objects.create(
            number=number,
            start_date=date.fromisoformat(data["dataInicio"]),
            end_date=date.fromisoformat(data["dataFim"]),
        )

    @transaction.atomic
    def _import_session(self, client, data):
        proposition = self._get_or_create_proposition(data)
        approved = data.get("aprovacao")

        session, _ = VotingSession.objects.update_or_create(
            camara_id=data["id"],
            defaults={
                "date": self._parse_datetime(
                    data.get("dataHoraRegistro") or data.get("data")
                ),
                "description": data.get("descricao", ""),
                "proposition": proposition,
                "approved": bool(approved) if approved is not None else None,
                "body": data.get("siglaOrgao", ""),
            },
        )

        for vote_data in client.get_votes(data["id"]):
            self._import_vote(session, vote_data)

    def _get_or_create_proposition(self, session_data):
        prop_str = session_data.get("proposicaoObjeto")
        prop_url = session_data.get("uriProposicaoObjeto") or ""

        if not prop_str:
            return None

        url_match = PROPOSITION_URL_RE.search(prop_url)
        bill_match = PROPOSITION_RE.match(prop_str.strip())
        if not url_match or not bill_match:
            return None

        bill_type, number, year = bill_match.groups()
        proposition, _ = Proposition.objects.get_or_create(
            camara_id=int(url_match.group(1)),
            defaults={
                "bill_type": bill_type,
                "number": int(number),
                "year": int(year),
                "url": prop_url,
            },
        )
        return proposition

    def _import_vote(self, session, data):
        deputy = data.get("deputado_", {})
        camara_deputy_id = deputy.get("id")
        vote_value = VOTE_MAP.get(data.get("tipoVoto", ""))
        if not camara_deputy_id or not vote_value:
            return

        Vote.objects.update_or_create(
            voting_session=session,
            camara_deputy_id=camara_deputy_id,
            defaults={
                "political_person": self._match_or_create_person(deputy),
                "vote": vote_value,
                "date": self._parse_datetime(data.get("dataRegistroVoto")),
            },
        )

    def _match_or_create_person(self, deputy):
        name = deputy.get("nome", "")
        match = PoliticalPerson.objects.filter(name__iexact=name).first()
        if match:
            return match
        return PoliticalPerson.objects.create(name=name)

    def _parse_datetime(self, value):
        if not value:
            return None
        raw = value if "T" in value else f"{value}T00:00:00"
        return datetime.fromisoformat(raw).replace(tzinfo=BRASILIA_TZ)

    def _print_summary(self):
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write(self.style.SUCCESS("Import complete!"))
        self.stdout.write(f"  Legislatures: {Legislature.objects.count()}")
        self.stdout.write(f"  Propositions: {Proposition.objects.count()}")
        self.stdout.write(f"  Voting sessions: {VotingSession.objects.count()}")
        self.stdout.write(f"  Votes: {Vote.objects.count()}")
