import uuid

from apps.users.models import User
from django.db import models
from utils.api_queries_bag import do_bag_search_id


class Address(models.Model):
    bag_id = models.CharField(max_length=255, null=False, unique=True)
    street_name = models.CharField(max_length=255, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    suffix_letter = models.CharField(max_length=1, null=True, blank=True)
    suffix = models.CharField(max_length=4, null=True, blank=True)
    postal_code = models.CharField(max_length=7, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    @property
    def full_address(self):
        full_address = f"{self.street_name} {self.number}"
        if self.suffix or self.suffix_letter:
            full_address = f"{full_address}-{self.suffix}{self.suffix_letter}"

        full_address = f"{full_address}, {self.postal_code}"

        return full_address

    def __str__(self):
        if self.street_name:
            return (
                f"{self.street_name}"
                f" {self.number}{self.suffix_letter}{self.suffix},"
                f" {self.postal_code}"
            )
        return self.bag_id

    def get(bag_id):
        return Address.objects.get_or_create(bag_id=bag_id)[0]

    def save(self, *args, **kwargs):
        bag_data = do_bag_search_id(self.bag_id)

        result = bag_data.get("results", [])

        if len(result):
            result = result[0]

            self.postal_code = result.get("postcode", "")
            self.street_name = result.get("straatnaam", "")
            self.number = result.get("huisnummer", "")
            self.suffix_letter = result.get("bag_huisletter", "")
            self.suffix = result.get("bag_toevoeging", "")

        return super().save(*args, **kwargs)


class CaseType(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True)

    def get(name):
        return CaseType.objects.get_or_create(name=name)[0]

    def __str__(self):
        return self.name


class Case(models.Model):
    class Meta:
        ordering = ["start_date"]

    identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    case_type = models.ForeignKey(
        to=CaseType, null=True, on_delete=models.CASCADE, related_name="cases"
    )
    address = models.ForeignKey(
        to=Address, null=True, on_delete=models.CASCADE, related_name="cases"
    )

    def get_current_state(self):
        if self.case_states.count() > 0:
            return self.case_states.all().order_by("-state_date").first()
        return None

    def __str__(self):
        if self.identification:
            return self.identification
        return ""

    def save(self, *args, **kwargs):
        if not self.identification:
            self.identification = str(uuid.uuid4())

        super().save(*args, **kwargs)


class CaseStateType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CaseState(models.Model):
    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.ForeignKey(CaseStateType, on_delete=models.PROTECT)
    state_date = models.DateField()
    users = models.ManyToManyField(
        User, related_name="case_states", related_query_name="users"
    )

    def __str__(self):
        return f"{self.state_date} - {self.case.identification} - {self.status.name}"


class OpenZaakStateType(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True)
    invoice_available = models.BooleanField(default=False, null=False, blank=False)

    def get(name):
        return OpenZaakStateType.objects.get_or_create(name=name)[0]

    def __str__(self):
        return self.name


class OpenZaakState(models.Model):
    state_type = models.ForeignKey(
        to=OpenZaakStateType,
        null=False,
        on_delete=models.CASCADE,
        related_name="states",
    )
    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.CASCADE, related_name="states"
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    gauge_date = models.DateField(null=True)
    # TODO: To make it more broadly applicable, we can probably just rename this to identification,
    invoice_identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )

    def __str__(self):
        return (
            f"{self.state_type}, {self.case.address}, {self.start_date} {self.end_date}"
            f" {self.gauge_date}"
        )


class CaseTimelineSubject(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)


class CaseTimelineThread(models.Model):
    # TODO Not sure if all authors are Users
    authors = models.ManyToManyField(to=User, related_name="authors")
    date = models.DateField(auto_now_add=True)
    subject = models.ForeignKey(CaseTimelineSubject, on_delete=models.CASCADE)
    parameters = models.JSONField(default={})
    notes = models.TextField(blank=True, null=True)


class CaseTimelineReaction(models.Model):
    timeline_item = models.ForeignKey(CaseTimelineThread, on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    comment = models.TextField()
    date = models.DateField(auto_now_add=True)
