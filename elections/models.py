from django.db import models


class Election(models.Model):
    year = models.PositiveSmallIntegerField()
    round = models.PositiveSmallIntegerField(default=1)
    description = models.CharField(max_length=200, blank=True)
    tse_election_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    class Meta:
        unique_together = ("year", "round")

    def __str__(self):
        return f"{self.description or self.year} - Round {self.round}"


class Position(models.Model):
    SCOPE_CHOICES = [
        ("national", "National"),
        ("state", "State"),
        ("district", "District"),
    ]

    name = models.CharField(max_length=100, unique=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)

    def __str__(self):
        return self.name
