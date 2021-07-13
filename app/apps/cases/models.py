import uuid

from apps.addresses.models import Address
from apps.events.models import CaseEvent, ModelEventEmitter, TaskModelEventEmitter
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone


class CaseTheme(models.Model):
    name = models.CharField(max_length=255, unique=True)
    case_state_types_top = models.ManyToManyField(
        to="CaseStateType",
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class CaseReason(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(
        to=CaseTheme, related_name="reasons", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class CaseProject(models.Model):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(to=CaseTheme, on_delete=models.PROTECT)

    class Meta:
        ordering = ["theme", "name"]

    def __str__(self):
        return self.name


class Case(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_CASE

    # RESULT_NOT_COMPLETED = "ACTIVE"
    # RESULT_ACHIEVED = "RESULT"
    # RESULT_MISSED
    # RESULTS = ()

    identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    address = models.ForeignKey(
        to=Address, null=True, on_delete=models.CASCADE, related_name="cases"
    )
    is_legacy_bwv = models.BooleanField(default=False)
    legacy_bwv_case_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    directing_process = models.CharField(max_length=255, null=True, blank=True)
    camunda_ids = ArrayField(
        models.CharField(max_length=255), default=list, null=True, blank=True
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

        if reason == "Project":
            event_values.update({"project": self.project.name})

        return event_values

    def __get_case__(self):
        return self

    def __generate_identification__(self):
        return str(uuid.uuid4())

    def __str__(self):
        if self.identification:
            return f"{self.id} Case - {self.identification}"
        return f"{self.id} Case"

    def get_current_states(self):
        return self.case_states.filter(end_date__isnull=True)

    def get_schedules(self):
        qs = self.schedules.all().order_by("-date_added")
        if qs:
            qs = [qs.first()]
        return qs

    def set_state(self, state_name, case_process_id, information="", *args, **kwargs):
        state_type, _ = CaseStateType.objects.get_or_create(
            name=state_name, theme=self.theme
        )
        state = CaseState.objects.create(
            case=self,
            status=state_type,
            information=information,
            case_process_id=case_process_id,
        )

        return state

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        if self.identification in (None, ""):
            self.identification = self.__generate_identification__()
        if self.legacy_bwv_case_id in (None, ""):
            self.legacy_bwv_case_id = self.__generate_identification__()

        super().save(*args, **kwargs)

    def add_camunda_id(self, camunda_id, *args, **kwargs):
        if self.camunda_ids:
            self.camunda_ids.append(camunda_id)
        else:
            self.camunda_ids = [camunda_id]

        self.save()
        return self

    def close_case(self):
        # close all states just in case
        for state in self.case_states.filter(end_date__isnull=True):
            state.end_date = timezone.now().date()
            state.save()

        for camunda_id in self.camunda_ids:
            from apps.camunda.services import CamundaService

            CamundaService().delete_instance(camunda_id)
            self.camunda_ids = []

        self.end_date = timezone.now().date()
        self.save()

    class Meta:
        ordering = ["-start_date"]


class CaseStateType(models.Model):
    def default_theme():
        theme, _ = CaseTheme.objects.get_or_create(name=settings.DEFAULT_THEME)
        return theme.id

    name = models.CharField(max_length=255, unique=True)
    theme = models.ForeignKey(
        to=CaseTheme,
        related_name="state_types",
        on_delete=models.CASCADE,
        default=default_theme,
    )

    def __str__(self):
        return self.name


class CaseState(models.Model):
    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.ForeignKey(CaseStateType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="case_states", related_query_name="users"
    )
    information = models.CharField(max_length=255, null=True, blank=True)
    case_process_id = models.CharField(max_length=255, null=True, default="")

    def __str__(self):
        return f"{self.start_date} - {self.end_date} - {self.case.identification} - {self.status.name}"

    def end_state(self):
        if not self.end_date:
            self.end_date = timezone.now().date()

        else:
            raise AttributeError("End date is already set")

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["start_date"]


class CaseProcessInstance(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    process_id = models.CharField(max_length=255, default=uuid.uuid4, unique=True)
    camunda_process_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )

    def __str__(self):
        return f"Case {self.case.id} - {self.process_id}"


class CaseCloseResult(models.Model):
    """
    If a Case is closed and reason is a result
    these are result types that need to be dynamic
    """

    name = models.CharField(max_length=255)
    case_theme = models.ForeignKey(CaseTheme, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} - {self.case_theme}"


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
    identification = models.PositiveIntegerField()
    advertisement_linklist = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        null=True,
        blank=True,
    )
    description_citizenreport = models.TextField(
        null=True,
        blank=True,
    )
    date_added = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.date_added} - {self.case.identification} - {self.identification}"

    def __get_event_values__(self):
        if self.author:
            author = self.author.full_name
        else:
            author = "Medewerker onbekend"
        event_values = {
            "identification": self.identification,
            "reporter_name": self.reporter_name,
            "reporter_phone": self.reporter_phone,
            "advertisement_linklist": self.advertisement_linklist,
            "description_citizenreport": self.description_citizenreport,
            "author": author,
        }
        if self.camunda_task_id != "-1":
            event_values.update(
                {
                    "date_added": self.date_added,
                }
            )
        else:
            del event_values["advertisement_linklist"]
        return event_values
