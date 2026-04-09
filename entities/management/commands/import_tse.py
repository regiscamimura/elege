from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from elections.models import Election, Position
from entities.models import Candidacy, Coalition, Party, PoliticalPerson
from entities.services.tse_api import TSEClient

SKIP_POSITIONS = {4, 9, 10}

SCOPE_MAP = {
    "Presidente": "national",
    "Governador": "state",
    "Vice-governador": "state",
    "Senador": "state",
    "Deputado Federal": "state",
    "Deputado Estadual": "state",
    "Deputado Distrital": "district",
}


class Command(BaseCommand):
    help = "Import candidates from TSE DivulgaCandContas API"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)
        parser.add_argument("--uf", type=str, required=True)
        parser.add_argument(
            "--skip-details",
            action="store_true",
            help="Skip fetching individual candidate details (faster, less data)",
        )

    def handle(self, *args, **options):
        year = options["year"]
        uf = options["uf"].upper()
        skip_details = options["skip_details"]

        client = TSEClient()

        self.stdout.write(f"Fetching election ID for {year}...")
        election_id = client.get_election_id(year)
        self.stdout.write(f"Election ID: {election_id}")

        election, _ = Election.objects.update_or_create(
            tse_election_id=election_id,
            defaults={"year": year, "round": 1, "description": f"Eleição Geral {year}"},
        )

        self.stdout.write(f"Fetching positions for {uf}...")
        tse_positions = client.list_positions(uf, election_id)

        for tse_pos in tse_positions:
            if tse_pos["codigo"] in SKIP_POSITIONS:
                continue

            position, _ = Position.objects.get_or_create(
                name=tse_pos["nome"],
                defaults={"scope": SCOPE_MAP.get(tse_pos["nome"], "state")},
            )

            self.stdout.write(
                f"\nFetching {tse_pos['nome']} candidates ({tse_pos['contagem']})..."
            )
            candidates = client.list_candidates(
                year, uf, election_id, tse_pos["codigo"]
            )

            for i, cand in enumerate(candidates, 1):
                if skip_details:
                    detail = cand
                else:
                    detail = client.get_candidate_detail(
                        year, uf, election_id, cand["id"]
                    )
                    if i % 25 == 0:
                        self.stdout.write(f"  {i}/{len(candidates)} processed...")

                self._import_candidate(detail, election, position, uf)

            self.stdout.write(
                self.style.SUCCESS(f"  {len(candidates)} candidates imported")
            )

        self._print_summary()

    @transaction.atomic
    def _import_candidate(self, data, election, position, uf):
        party = self._get_or_create_party(data)
        person = self._get_or_create_person(data)
        coalition = self._get_or_create_coalition(data, election)

        Candidacy.objects.update_or_create(
            tse_id=data["id"],
            defaults={
                "political_person": person,
                "election": election,
                "party": party,
                "position": position,
                "coalition": coalition,
                "ballot_name": data.get("nomeUrna", ""),
                "number": str(data.get("numero", "")),
                "status": data.get("descricaoSituacao", ""),
                "state": uf,
                "photo_url": data.get("fotoUrl") or "",
                "email": self._extract_email(data),
            },
        )

    def _get_or_create_party(self, data):
        partido = data.get("partido", {})
        sigla = partido.get("sigla", "")
        if not sigla:
            return None

        party, _ = Party.objects.update_or_create(
            abbreviation=sigla,
            defaults={
                "name": partido.get("nome") or sigla,
                "number": partido.get("numero", 0),
            },
        )
        return party

    def _get_or_create_person(self, data):
        name = data.get("nomeCompleto", data.get("nomeUrna", ""))
        cpf = data.get("cpf")
        dob = self._parse_date(data.get("dataDeNascimento"))

        if cpf:
            person, _ = PoliticalPerson.objects.update_or_create(
                cpf=cpf,
                defaults={
                    "name": name,
                    "date_of_birth": dob,
                    "gender": data.get("descricaoSexo", ""),
                    "race": data.get("descricaoCorRaca", ""),
                    "education_level": data.get("grauInstrucao", ""),
                    "occupation": data.get("ocupacao", ""),
                },
            )
        else:
            person, _ = PoliticalPerson.objects.get_or_create(
                name=name,
                date_of_birth=dob,
                defaults={
                    "gender": data.get("descricaoSexo", ""),
                    "race": data.get("descricaoCorRaca", ""),
                    "education_level": data.get("grauInstrucao", ""),
                    "occupation": data.get("ocupacao", ""),
                },
            )

        return person

    def _get_or_create_coalition(self, data, election):
        name = data.get("nomeColigacao")
        if not name or name == "**":
            return None

        coalition, _ = Coalition.objects.get_or_create(
            name=name,
            election=election,
        )

        party = self._get_or_create_party(data)
        if party and not coalition.parties.filter(pk=party.pk).exists():
            coalition.parties.add(party)

        return coalition

    def _extract_email(self, data):
        emails = data.get("emails")
        if emails and isinstance(emails, list) and emails:
            return emails[0] if isinstance(emails[0], str) else ""
        return ""

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            parts = date_str.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return None

    def _print_summary(self):
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write(self.style.SUCCESS("Import complete!"))
        self.stdout.write(f"  Parties: {Party.objects.count()}")
        self.stdout.write(f"  People: {PoliticalPerson.objects.count()}")
        self.stdout.write(f"  Candidacies: {Candidacy.objects.count()}")
        self.stdout.write(f"  Coalitions: {Coalition.objects.count()}")
        self.stdout.write(f"  Elections: {Election.objects.count()}")
        self.stdout.write(f"  Positions: {Position.objects.count()}")
