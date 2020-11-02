from apps.cases.models import Case
from apps.events.models import Event, ModelEventEmitter
from apps.users.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Visit(ModelEventEmitter):
    EVENT_TYPE = Event.TYPE_VISIT

    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    situation = models.CharField(max_length=255)
    observations = ArrayField(models.CharField(max_length=255), blank=True, null=False)
    authors = models.ManyToManyField(User)
    notes = models.TextField()

    def __str__(self):
        return f"Case: {self.case.id} - {self.id}"

    def __get_event_values__(self):
        json_obj = {
            "start_time": self.start_time,
            "authors": [],
            "situation": self.situation,
            "observations": self.observations,
            "notes": self.notes,
        }
        if self.authors:
            json_obj["authors"] = [author.full_name for author in self.authors.all()]

        return json_obj

    def create_from_top(self, data):
        try:
            case = Case.objects.get(identification=data["case_identification"])
        except Case.DoesNotExist:
            return False

        self.case = case
        self.start_time = data["start_time"]
        self.observations = data["observations"]
        self.situation = data["situation"]
        self.notes = data["notes"]
        self.save()

        for author in data["authors"]:
            (user, _) = User.objects.get_or_create(email=author)
            self.authors.add(user)

        return self
