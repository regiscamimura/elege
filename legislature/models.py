from django.db import models


class Legislature(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.number}ª Legislatura ({self.start_year}-{self.end_year})"


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
        "entities.PoliticalPerson",
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
