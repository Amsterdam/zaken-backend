import json
import logging
from json.decoder import JSONDecodeError

from apps.cases.models import CaseTheme
from apps.users.models import User
from django import forms

from .serializers import BWVCaseImportValidSerializer

logger = logging.getLogger(__name__)


class ImportBWVCaseDataForm(forms.Form):
    json_data = forms.CharField(
        label="json data",
        widget=forms.Textarea(
            attrs={
                "placeholder": 'format: {"123bwv_id": {"postcode": "1234ab", "field": "value", ...}} --',
                "class": "vLargeTextField",
            }
        ),
        required=True,
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Kies een gebruiker",
        to_field_name="pk",
        required=True,
    )
    status_name = forms.ChoiceField(
        choices=(
            ("Huisbezoek", "Huisbezoek"),
            ("Hercontrole", "Hercontrole"),
        ),
        label="Kies een de status van de zaak",
        required=True,
    )
    theme = forms.ModelChoiceField(
        queryset=CaseTheme.objects.all(),
        label="Kies een thema",
        to_field_name="pk",
        required=True,
    )
    SUBWORKFLOWS_CHOICES = (
        ("", " - begin taak van het gekozen thema - "),
        ("visit", "visit (taak: Bepalen processtap)"),
        ("debrief", "debrief (taak: Verwerken debrief)"),
        ("summon", "summon (taak: Opstellen concept aanschrijving)"),
        ("decision", "decision (taak: Opstellen concept besluit)"),
    )
    subworkflow = forms.ChoiceField(
        choices=SUBWORKFLOWS_CHOICES,
        label="Kies in welke fase deze zaken moeten starten",
        required=False,
    )

    def clean_json_data(self):
        data = self.cleaned_data["json_data"]
        try:
            data = data.replace('"NaN"', "null")
            data = data.replace('"nan"', "null")
            data = data.replace('"NaT"', "null")

            data = json.loads(data)

            data = [
                {
                    "legacy_bwv_case_id": k,
                    **v,
                }
                for k, v in data.items()
            ]
            logger.info("BWV import cases: raw json count")
            logger.info(len(data))

            def strip_value(value):
                value = value.strip() if isinstance(value, str) else value
                return value

            data = [dict((k, strip_value(v)) for k, v in d.items()) for d in data]
            serializer = BWVCaseImportValidSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            return serializer.data
        except JSONDecodeError as e:
            self.add_error("json_data", f"JSONDecodeError: {e}")
        except Exception as e:
            self.add_error("json_data", f"Serializer error: {e}")
