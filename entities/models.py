from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=20, unique=True)
    number = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        verbose_name_plural = "Parties"

    def __str__(self):
        return self.abbreviation


class Coalition(models.Model):
    name = models.CharField(max_length=200)
    election = models.ForeignKey(
        "elections.Election",
        on_delete=models.PROTECT,
        related_name="coalitions",
    )
    parties = models.ManyToManyField(Party, related_name="coalitions")

    def __str__(self):
        return self.name


class PoliticalPerson(models.Model):
    name = models.CharField(max_length=300)
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    race = models.CharField(max_length=40, blank=True)
    education_level = models.CharField(max_length=60, blank=True)
    occupation = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "Political people"

    def __str__(self):
        return self.name


class PartyMembership(models.Model):
    political_person = models.ForeignKey(
        PoliticalPerson,
        on_delete=models.CASCADE,
        related_name="party_memberships",
    )
    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.political_person} - {self.party} ({self.start_date})"


class Candidacy(models.Model):
    political_person = models.ForeignKey(
        PoliticalPerson,
        on_delete=models.CASCADE,
        related_name="candidacies",
    )
    election = models.ForeignKey(
        "elections.Election",
        on_delete=models.PROTECT,
        related_name="candidacies",
    )
    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="candidacies",
    )
    position = models.ForeignKey(
        "elections.Position",
        on_delete=models.PROTECT,
        related_name="candidacies",
    )
    coalition = models.ForeignKey(
        Coalition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidacies",
    )
    ballot_name = models.CharField(max_length=200)
    number = models.CharField(max_length=10)
    status = models.CharField(max_length=40)
    state = models.CharField(max_length=2)
    photo_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    tse_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name_plural = "Candidacies"

    def __str__(self):
        return f"{self.ballot_name} ({self.party}) - {self.election}"


class Proposal(models.Model):
    candidacy = models.ForeignKey(
        Candidacy,
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    raw_text = models.TextField(blank=True)
    pdf_url = models.URLField(blank=True)

    def __str__(self):
        return f"Proposal - {self.candidacy.ballot_name}"


class Promise(models.Model):
    CATEGORY_CHOICES = [
        ("education", "Educação"),
        ("health", "Saúde"),
        ("security", "Segurança"),
        ("economy", "Economia"),
        ("environment", "Meio Ambiente"),
        ("infrastructure", "Infraestrutura"),
        ("social", "Social"),
        ("children", "Crianças e Adolescentes"),
        ("other", "Outros"),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="promises",
    )
    text = models.TextField()
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )
    extracted_by = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.category}: {self.text[:80]}"


class Legislature(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return (
            f"{self.number}ª Legislatura "
            f"({self.start_date.year}-{self.end_date.year})"
        )


class Proposition(models.Model):
    camara_id = models.PositiveIntegerField(unique=True, db_index=True)
    bill_type = models.CharField(max_length=20)
    number = models.PositiveIntegerField()
    year = models.PositiveSmallIntegerField()
    summary = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.bill_type} {self.number}/{self.year}"


class VotingSession(models.Model):
    camara_id = models.CharField(max_length=30, unique=True, db_index=True)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    proposition = models.ForeignKey(
        Proposition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voting_sessions",
    )
    approved = models.BooleanField(null=True)
    body = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.camara_id} - {self.date.date()}"


class Vote(models.Model):
    VOTE_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
        ("abstencao", "Abstenção"),
        ("obstrucao", "Obstrução"),
        ("artigo17", "Art. 17"),
    ]

    voting_session = models.ForeignKey(
        VotingSession,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    political_person = models.ForeignKey(
        PoliticalPerson,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)
    camara_deputy_id = models.PositiveIntegerField(db_index=True)
    date = models.DateTimeField()

    class Meta:
        unique_together = ("voting_session", "camara_deputy_id")

    def __str__(self):
        return f"{self.political_person} - {self.vote} - {self.voting_session}"
