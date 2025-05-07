import uuid
from itertools import chain
from re import sub
from time import sleep

from apps.addresses.models import Address
from apps.events.models import CaseEvent, ModelEventEmitter, TaskModelEventEmitter
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone


def snake_case(s):
    return "_".join(
        sub(
            r"(\s|_|-)+",
            " ",
            sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: " " + mo.group(0).lower(),
                s,
            ),
        ).split()
    )


class CaseTheme(models.Model):
    name = models.CharField(max_length=255, unique=True)
    case_type_url = models.URLField(
        null=True,
        help_text="This is the case type that can be found in openzaak. This way all the case types can be linked within the systems.",
    )
    sensitive = models.BooleanField(default=False)

    @property
    def snake_case_name(self):
        return snake_case(self.name)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class CaseReason(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(
        to=CaseTheme, related_name="reasons", on_delete=models.CASCADE
    )

    @property
    def snake_case_name(self):
        return snake_case(self.name)

    def __str__(self):
        return f"{self.name} ({self.theme.name})"

    class Meta:
        ordering = ["name"]


class CaseProject(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(to=CaseTheme, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["theme", "name"]

    def __str__(self):
        return f"{self.name} ({self.theme.name})"


class Subject(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(CaseTheme, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.theme.name}: {self.name}"

    class Meta:
        ordering = ["name"]


class Tag(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(CaseTheme, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.theme.name}: {self.name}"

    class Meta:
        ordering = ["name"]


class Case(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_CASE

    identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    address = models.ForeignKey(
        to=Address, null=True, on_delete=models.CASCADE, related_name="cases"
    )
    sensitive = models.BooleanField(default=False)
    is_legacy_bwv = models.BooleanField(default=False)
    is_legacy_camunda = models.BooleanField(default=False)
    legacy_bwv_case_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    previous_case = models.ForeignKey(
        to="cases.Case",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    mma_number = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    theme = models.ForeignKey(to=CaseTheme, on_delete=models.PROTECT)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    reason = models.ForeignKey(to=CaseReason, on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(
        to=CaseProject, null=True, blank=True, on_delete=models.PROTECT
    )
    subjects = models.ManyToManyField(Subject, related_name="cases", blank=True)
    tags = models.ManyToManyField(Tag, related_name="cases", blank=True)
    ton_ids = ArrayField(
        models.CharField(max_length=255), default=list, null=True, blank=True
    )
    last_updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    case_created_advertisements = GenericRelation(
        "Advertisement",
        object_id_field="related_object_id",
        content_type_field="related_object_type",
        related_query_name="cases",
    )
    is_enforcement_request = models.BooleanField(default=False)
    case_url = models.URLField(
        null=True,
        blank=True,
        help_text="This is the case that can be found in openzaak.",
    )
    case_deleted = models.BooleanField(
        default=False,
        blank=True,
        help_text="This field determines if the case is deleted in openzaak.",
    )

    def __get_event_values__(self):
        reason = self.reason.name
        if self.is_legacy_bwv:
            reason = "Deze zaak bestond al voor het nieuwe zaaksysteem. Zie BWV voor de aanleiding(en)."

        if self.author:
            author = self.author.full_name
        else:
            author = "Medewerker onbekend"

        event_values = {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": reason,
            "description": self.description,
            "author": author,
            "subjects": map(lambda subject: subject.name, self.subjects.all()),
            "mma_number": self.mma_number,
            "previous_case": self.previous_case.id if self.previous_case else None,
        }

        # TODO better way for db reason with python logic
        if reason == settings.DEFAULT_REASON:
            citizen_report = (
                CitizenReport.objects.filter(case=self).order_by("date_added").first()
            )
            if citizen_report:
                event_values.update(
                    {"advertisement_linklist": citizen_report.advertisement_linklist}
                )

        if self.case_created_advertisements.all():
            event_values.update(
                {
                    "advertisement_linklist": [
                        a.link for a in self.case_created_advertisements.all()
                    ]
                }
            )

        if reason == "Project":
            event_values.update({"project": self.project.name})

        return event_values

    def __get_case__(self):
        return self

    def __generate_identification__(self):
        return str(uuid.uuid4())

    def __str__(self):
        return f"Case: {self.id}"

    def get_workflows(self):
        return (
            self.workflows.all()
            .filter(tasks__isnull=False, tasks__completed=False)
            .distinct()
        )

    def get_state(self):
        # Return last added case_state
        casestates = self.case_states.all().order_by("created").last()
        if casestates:
            return casestates.status
        else:
            return CaseState.CaseStateChoice.TOEZICHT

    def force_citizen_report_feedback(self, instance=None) -> bool:
        from apps.cases.tasks import task_update_citizen_report_feedback_workflows
        from apps.debriefings.models import Debriefing
        from apps.workflow.models import CaseUserTask

        force = False
        if instance is None:
            instance = self.debriefings.order_by("date_modified").last()

        if isinstance(instance, CaseUserTask):
            if instance.task_name == "task_set_next_step":
                force = True
        elif isinstance(instance, Debriefing):
            force = bool(
                instance.violation.value
                in [
                    "NO",
                    "YES",
                    "SEND_TO_OTHER_THEME",
                ]
            )
        if force:
            task_update_citizen_report_feedback_workflows.delay(self.id, force)
            sleep(1)
        return force

    def get_schedules(self):
        qs = self.schedules.all().order_by("-date_added")
        if qs:
            qs = [qs.first()]
        return qs

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now().date()

        if self.identification in (None, ""):
            self.identification = self.__generate_identification__()
        if self.legacy_bwv_case_id in (None, ""):
            self.legacy_bwv_case_id = self.__generate_identification__()

        super().save(*args, **kwargs)

    def close_case(self):
        # delete all processes and tasks
        with transaction.atomic():
            self.workflows.all().delete()
            self.end_date = timezone.now().date()
            self.save()

    class Meta:
        ordering = ["-id"]


class CaseDocument(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    document_url = models.URLField()
    document_content = models.URLField()
    case_document_connection_url = models.URLField(default=False, blank=True)
    connected = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f"Document van {self.case}"


class CaseStateType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["name"]


class CaseState(models.Model):
    class CaseStateChoice(models.TextChoices):
        # For new statusses there should be created a new setting.
        TOEZICHT = "TOEZICHT", "Toezicht"
        HANDHAVING = "HANDHAVING", "Handhaving"
        AFGESLOTEN = "AFGESLOTEN", "Afgesloten"

    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=50,
        choices=CaseStateChoice.choices,
        default=CaseStateChoice.TOEZICHT,
    )
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    system_build = models.BooleanField(default=False, blank=True)
    set_in_open_zaak = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f"{self.status} - {self.case}"

    class Meta:
        ordering = ["-last_updated"]


class CaseCloseResult(models.Model):
    """
    If a Case is closed and reason is a result
    these are result types that need to be dynamic
    """

    name = models.CharField(max_length=255)
    case_theme = models.ForeignKey(CaseTheme, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} - {self.case_theme}"

    class Meta:
        ordering = ["name"]


class CaseCloseReason(models.Model):
    result = models.BooleanField()
    name = models.CharField(max_length=255)
    case_theme = models.ForeignKey(CaseTheme, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} - {self.case_theme}"

    class Meta:
        ordering = ["case_theme", "name"]


class CaseClose(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_CASE_CLOSE

    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    reason = models.ForeignKey(CaseCloseReason, on_delete=models.PROTECT)
    result = models.ForeignKey(
        CaseCloseResult, null=True, blank=True, on_delete=models.PROTECT
    )
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return f"CASE: {self.case.__str__()} - REASON {self.reason.__str__()}"

    def __get_event_values__(self):
        event_values = {
            "date_added": self.date_added,
            "author": self.author.full_name if self.author else "Medewerker onbekend",
            "reason": self.reason.name,
            "description": self.description,
        }
        if self.result:
            event_values.update({"result": self.result.name})
        return event_values


class CitizenReport(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_CITIZEN_REPORT

    case = models.ForeignKey(
        Case, related_name="case_citizen_reports", on_delete=models.CASCADE
    )
    reporter_name = models.CharField(max_length=50, null=True, blank=True)
    reporter_phone = models.CharField(max_length=50, null=True, blank=True)
    reporter_email = models.CharField(max_length=50, null=True, blank=True)
    identification = models.PositiveIntegerField()
    advertisement_linklist = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        null=True,
        blank=True,
    )
    related_advertisements = GenericRelation(
        "Advertisement",
        object_id_field="related_object_id",
        content_type_field="related_object_type",
        related_query_name="advertisements_citizen_reports",
    )
    description_citizenreport = models.TextField(
        null=True,
        blank=True,
    )
    nuisance = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def get_status_information(self):
        reporter = ", ".join(
            [
                str(getattr(self, f))
                for f in [
                    "identification",
                    "reporter_name",
                    "reporter_phone",
                    "reporter_email",
                ]
                if getattr(self, f) is not None
            ]
        )
        return f"SIG-nummer: {reporter}"

    def __str__(self):
        return f"CitizenReport: {self.date_added} - {self.case}"

    def __get_event_values__(self):
        advertisement_linklist = self.advertisement_linklist

        if self.author:
            author = self.author.full_name
        else:
            author = "Medewerker onbekend"

        event_values = {
            "identification": self.identification,
            "reporter_name": self.reporter_name,
            "reporter_phone": self.reporter_phone,
            "reporter_email": self.reporter_email,
            "description_citizenreport": self.description_citizenreport,
            "author": author,
        }
        if self.case.theme.id == 2:
            event_values.update(
                {
                    "nuisance": self.nuisance,
                }
            )

        if self.case_user_task_id != "-1":
            # report not created with case create
            event_values.update(
                {
                    "date_added": self.date_added,
                }
            )
        else:
            advertisement_linklist = []

        advertisement_linklist = list(
            chain(
                *[
                    [a.link for a in self.related_advertisements.all()],
                    advertisement_linklist,
                ]
            )
        )
        event_values.update(
            {
                "advertisement_linklist": advertisement_linklist,
            }
        )

        return event_values


class Advertisement(models.Model):
    case = models.ForeignKey(
        to=Case,
        related_name="advertisements",
        on_delete=models.CASCADE,
    )
    link = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    related_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    related_object = GenericForeignKey("related_object_type", "related_object_id")
