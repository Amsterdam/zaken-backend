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
                # "style": "width: 100%",
                # ""
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

    def clean_json_data(self):
        data = self.cleaned_data["json_data"]
        try:
            data = data.replace("null", "None")
            data = data.replace('"huisnummer": NaN', '"huisnummer": 0')
            data = data.replace('"situatie_schets": NaN', '"situatie_schets": ""')
            data = data.replace('"melder_naam": NaN', '"melder_naam": ""')
            data = data.replace('"melder_emailadres": NaN', '"melder_emailadres": ""')
            data = data.replace('"melder_telnr": NaN', '"melder_telnr": ""')
            data = data.replace("NaN", '""')
            data = data.replace("nan", "")

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
