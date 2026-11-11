import logging
from textwrap import dedent

from apps.addresses.serializers import AddressSimplifiedSerializer
from apps.cases.models import Case, CaseProject, CaseReason, CaseTheme, Subject
from apps.cases.serializers import CaseCreateSerializer
from openpyxl import load_workbook
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from utils.api_queries_bag import do_bag_search_pdok_by_address

LOGGER = logging.getLogger(__name__)

class BulkImportException(Exception):
    pass


class BulkLeegstandImporter:
    fields = {
        "straat": {"idx": 0},
        "postcode": {"idx": 0},
        "huisnr.": {"idx": 0},
        "toevoeging": {"idx": 0},
        "reden leegstand": {"idx": 0},
        "datum start werkzaamheden": {"idx": 0},
        "datum oplevering": {"idx": 0},
        "bijzonderheden": {"idx": 0},
    }
    first_header_item = 'straat'

    MAX_METADATA_ROWS = 10
    METADATA_MAPPING = { # label -> field
        "Datum melding": "melding_datum",
        "Naam bedrijf": "melding_naam"
    }

    def __init__(self, file, user, theme: CaseTheme, reason: CaseReason, subjects=None, project=None, jump_to=None, dry_run=True):
        self.file = file
        self.project = CaseProject.objects.get(pk=project) if isinstance(project, int) else project
        self.dry_run = dry_run
        self.theme = CaseTheme.objects.get(pk=theme) if isinstance(theme, int) else theme
        self.reason = CaseReason.objects.get(pk=reason) if isinstance(reason, int) else reason
        if subjects is not None:
            self.subjects = [Subject.objects.get(pk=subj) if isinstance(subj, int) else subj for subj in subjects]
        self.jump_to=jump_to

        self.worksheet = None
        self.header_row_idx = None
        self.metadata = {}

        # User is needed for CaseSerializer for author field
        factory = APIRequestFactory()
        self.request = factory.post("/")
        self.request.user = user

        # Case create defaults
        self.case_default_data = {}
        self._set_case_default_data()

    def _set_case_default_data(self):
        subject_ids = [s.pk for s in self.subjects]

        self.case_default_data = {
            "reason": {
                "id": self.reason.pk,
                "name": self.reason.name,
            },
            "reason_id": self.reason.pk,
            "subject_ids": subject_ids,
            "subjects": self.subjects,
            "theme": {
                "id": self.theme.pk,
                "name": self.theme.name,
            },
            "theme_id": self.theme.pk,
        }

        if self.project is not None:
            self.case_default_data.update({
                    "project": {
                        "id": self.project.pk,
                        "name": self.project.name,
                    },
                    "project_id": self.project.pk,
            })

        if self.jump_to is not None:
            self.case_default_data.update({"jump_to": self.jump_to})

    def import_from_file(self):
        self._inspect_excel_file()
        return self._process_rows()

    def _inspect_excel_file(self):
        try:
            wb = load_workbook(self.file)
            ws = self.worksheet = wb.active
        except Exception as e:
            raise BulkImportException(f"Kan bestand niet openen: {e}")

        self._find_metadata(ws)
        self.header_row_idx = self._find_header_row_index(ws)
        header_raw = [cell.value for cell in ws[self.header_row_idx]]
        header = self._clean_header(header_raw)

        for column_name, field in self.fields.items():
            try:
                field_idx = header.index(column_name)
                field["idx"] = field_idx
            except ValueError:
                raise BulkImportException(f"Bestand moet de volgende kolom bevatten: {column_name}")

    def _process_rows(self):
        num_processed = 0
        num_created = 0
        processed_cases = []

        for row in self.worksheet.iter_rows(
            min_row=self.header_row_idx + 1, values_only=True
        ):
            first_column = row[self.fields[self.first_header_item]["idx"]]
            if not first_column:
                LOGGER.warning("Skipping row with empty %s", self.first_header_item)
                continue

            row_data = {
                field_name: row[field_data["idx"]]
                for field_name, field_data in self.fields.items()
            }

            created, msg = self._import_case(row_data, self.dry_run)
            processed_cases.append({"success": created, "msg": msg})

            num_processed += 1
            if not self.dry_run:
                num_created += created

        processed_result = {
            "total_processed": num_processed,
            "total_created": num_created,
            "dry_run": self.dry_run,
            "case_data": processed_cases,
        }
        return processed_result

    def _find_metadata(self, ws):
        self.metadata = {}
        for row in ws.iter_rows(min_row=1, max_row=self.MAX_METADATA_ROWS):
            for cell in row:
                if not isinstance(cell.value, str):
                    continue
                key = cell.value.strip()
                if key in self.METADATA_MAPPING.keys():
                    value = ws.cell(
                        row=cell.row, column=cell.column + 1
                    ).value
                    LOGGER.info(f"Found metadata {key}: {value}")
                    self.metadata[self.METADATA_MAPPING[key]] = value

    def _find_header_row_index(self, ws):
        for row_index, row in enumerate(
            ws.iter_rows(min_row=1, max_col=5, max_row=self.MAX_METADATA_ROWS, values_only=True), start=1
        ):
            for cell_value in row:
                if isinstance(cell_value, str) and cell_value.lower() == self.first_header_item:
                    return row_index

        raise BulkImportException("Kan kolombeschrijving niet vinden!")

    @staticmethod
    def _clean_header(header: list):
        return [
            (
                item.lower().replace("(beknopt)", "").rstrip(" ")
                if isinstance(item, str)
                else item
            )
            for item in header
        ]

    def _get_bag_data(
        self, street_name: str, number: int, suffix: str | int, postal_code: str
    ):
        street_name = street_name.strip()
        number = number
        suffix = str(suffix).strip()
        postal_code = postal_code.replace(" ", "").replace("\xa0", "")
        search_string = f"{street_name} {number}-{suffix}, {postal_code}"

        result = {
            "bag_id": None,
            "search_address": search_string,
            "found_address": "",
            "error": "",
        }

        serializer = AddressSimplifiedSerializer(
            data={
                "street_name": street_name,
                "number": number,
                "suffix": suffix,
                "postal_code": postal_code,
            },
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            error_str = f"FOUT IN INVOERDATA: {search_string}: {e}"
            result["error"] = error_str
            return result

        response = do_bag_search_pdok_by_address(search_string).get("response", {})

        if response.get("numFound", 0) == 0:
            error_str = f"Adres niet gevonden: {search_string}"
            result["error"] = error_str
            return result
        elif response.get("numFound", 0) > 1:
            # Vaak als er meerdere adressen uitkomen, dan klopt het eerste adres, de rest heeft bijvoorbeeld een andere toevoeging.
            # Als de postcode, huisnr en toevoeging gelijk zijn, kunnen we aannemen dat het het juiste adres is.
            # Zo niet: Error teruggeven
            first_address = response.get("docs")[0]
            if not (
                first_address["postcode"] == postal_code
                and first_address["huisnummer"] == number
                and first_address["huisnummertoevoeging"] == suffix
            ):
                error_str = f"Meer dan één adres gevonden voor {search_string}"
                LOGGER.warning(error_str)
                for adres in response.get("docs", []):
                    LOGGER.warning(f"    {adres['weergavenaam']} + {adres['score']}")
                result["error"] = error_str
                return result

        found_address = response.get("docs")[0]
        result["bag_id"] = found_address["adresseerbaarobject_id"]
        result["found_address"] = found_address["weergavenaam"]
        return result

    def get_description_text(self, reason: str, date_start, date_end, details):
        datum_melding = self.metadata['melding_datum'].strftime("%d-%m-%Y") if 'melding_datum' in self.metadata else '-'
        return dedent(
            f"""Leegstand gemeld: {self.metadata.get('melding_naam', '-')} op {datum_melding}.
            Leeg sinds: {date_start.strftime("%d-%m-%Y") if date_start else '-'}.
            Reden: {reason}.
            Opleverdatum: {date_end.strftime("%d-%m-%Y") if date_end else '-'}
            Bijzonderheden: {details}
        """
        ).strip()

    def _import_case(self, row_data: dict, dry_run: bool):
        """Return True when a case can successfully be imported"""
        address_data = self._get_bag_data(
            row_data["straat"],
            row_data["huisnr."],
            row_data["toevoeging"],
            row_data["postcode"],
        )
        bag_id = address_data["bag_id"]
        if address_data["error"] or bag_id is None:
            return False, address_data["error"]

        msg = f"Adres: {address_data["search_address"]}: "
        description = self.get_description_text(
            row_data["reden leegstand"],
            row_data["datum start werkzaamheden"],
            row_data["datum oplevering"],
            row_data["bijzonderheden"],
        )

        case_data = {
            **self.case_default_data,
            "bag_id": bag_id,
            "description": description,
        }

        serializer = CaseCreateSerializer(
            data=case_data,
            context={"request": self.request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            error_str = f"CaseCreateSerializer: {e}"
            return False, error_str

        open_cases_at_address = Case.objects.filter(
            theme=self.theme, address__bag_id=bag_id, end_date=None
        )
        if open_cases_at_address.exists():
            return False, msg + "OVERGESLAGEN (Onafgeronde zaak gevonden voor dit adres)"

        if not dry_run:
            serializer.save()

        return True, msg + "OK"
