from apps.cases.models import Case, CaseTeam
from apps.summons.models import Summon
from django.db import models


class DecisionType(models.Model):
    camunda_option = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_sanction = models.BooleanField(default=False)
    team = models.ForeignKey(
        to=CaseTeam, related_name="decision_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.team.name} - {self.name}"


class Decision(models.Model):
    """
    Model is used to repesent the decision after a summon
    """

    case = models.ForeignKey(
        to=Case, on_delete=models.CASCADE, related_name="decisions"
    )
    summon = models.OneToOneField(
        to=Summon, on_delete=models.CASCADE, related_name="decision"
    )
    decision_type = models.ForeignKey(to=DecisionType, on_delete=models.RESTRICT)
    description = models.TextField(blank=True, null=True)
