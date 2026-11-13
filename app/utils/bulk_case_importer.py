import logging
import re

from apps.addresses.serializers import AddressSimplifiedSerializer
from apps.cases.models import Case, CaseProject, CaseReason, CaseTheme, Subject
from apps.cases.serializers import CaseCreateSerializer
from openpyxl import load_workbook
from rest_framework.test import APIRequestFactory
from utils.api_queries_bag import do_bag_search_pdok_by_address

LOGGER = logging.getLogger(__name__)


class BulkImportException(Exception):
    pass


# The address fields in words, for the user.
FIELD_LABELS = {
    "street_name": "straatnaam",
    "number": "huisnummer",
    "suffix": "toevoeging",
    "postal_code": "postcode",
}


def _error_messages(errors, field=None):
    """The messages of a serializer's errors as text, with the field they are of."""
    if isinstance(errors, dict):
        return [
            message
            for key, value in errors.items()
            for message in _error_messages(value, key)
        ]
    if isinstance(errors, list):
        return [message for item in errors for message in _error_messages(item, field)]
    return [f"{field}: {errors}" if field else str(errors)]


class BulkCaseImporter:
    fields = [
        "straat",
        "postcode",
        "huisnr",
        "toevoeging",
        "toelichting",
    ]
    first_header_item = "straat"

    MAX_METADATA_ROWS = 10
    METADATA_MAPPING = {  # label -> field
        "Datum melding": "melding_datum",
        "Naam bedrijf": "melding_naam",
    }

    def __init__(
        self,
        file,
        user,
        theme: CaseTheme,
        reason: CaseReason | int | None = None,
        subjects: list | None = None,
        project: CaseProject | int | None = None,
        jump_to: str | None = None,
        description: str | None = None,
        dry_run: bool = True,
    ):
        self.file = file
        # The explanation for all cases, above the one of the row.
        self.description = (description or "").strip() or None
        self.project = (
            CaseProject.objects.get(pk=project) if isinstance(project, int) else project
        )
        self.dry_run = dry_run
        self.theme = (
            CaseTheme.objects.get(pk=theme) if isinstance(theme, int) else theme
        )
        self.reason = (
            CaseReason.objects.get(pk=reason) if isinstance(reason, int) else reason
        )
        if subjects is not None:
            self.subjects = [
                Subject.objects.get(pk=subj) if isinstance(subj, int) else subj
                for subj in subjects
            ]
        else:
            self.subjects = []
        self.jump_to = jump_to

        self.worksheet = None
        self.field_index = {field_name: 0 for field_name in self.fields}
        self.header_row_idx = None
        self.metadata = {}

        # User is needed for CaseSerializer for author field
        factory = APIRequestFactory()
        self.request = factory.post("/")
        self.request.user = user

        # Case create defaults
        self.case_default_data = {}
        self._set_case_default_data()

    def import_from_file(self):
        self._inspect_excel_file()
        return self._process_rows()

    def _set_case_default_data(self):
        subject_ids = [s.pk for s in self.subjects]

        self.case_default_data = {
            "subject_ids": subject_ids,
            "subjects": self.subjects,
            "theme": {
                "id": self.theme.pk,
                "name": self.theme.name,
            },
            "theme_id": self.theme.pk,
        }

        if self.reason is not None:
            self.case_default_data.update(
                {
                    "reason": {
                        "id": self.reason.pk,
                        "name": self.reason.name,
                    },
                    "reason_id": self.reason.pk,
                }
            )

        if self.project is not None:
            self.case_default_data.update(
                {
                    "project": {
                        "id": self.project.pk,
                        "name": self.project.name,
                    },
                    "project_id": self.project.pk,
                }
            )

        if self.jump_to is not None:
            self.case_default_data.update({"jump_to": self.jump_to})

    def _inspect_excel_file(self):
        try:
            wb = load_workbook(self.file, read_only=True, data_only=True)
            ws = self.worksheet = wb.active
        except Exception as e:
            raise BulkImportException(f"Kan bestand niet openen: {e}")

        self._find_metadata(
            ws
        )  # Metadata fields might be needed for adding to the description
        self.header_row_idx = self._find_header_row_index(ws)
        header_raw = [cell.value for cell in ws[self.header_row_idx]]
        header = self._clean_header(header_raw)

        for field_name in self.fields:
            try:
                self.field_index[field_name] = header.index(field_name)
            except ValueError:
                raise BulkImportException(
                    f"Bestand moet de volgende kolom bevatten: {field_name}"
                )

    def _process_rows(self):
        num_processed = 0
        num_created = 0
        processed_cases = []

        # The row number as in Excel: the header and empty rows count.
        for row_number, row in enumerate(
            self.worksheet.iter_rows(min_row=self.header_row_idx + 1, values_only=True),
            start=self.header_row_idx + 1,
        ):
            # Check a field that should be filled, otherwise skip row
            mandatory_field_content = row[self.field_index[self.first_header_item]]
            if not mandatory_field_content:
                LOGGER.warning("Skipping row with empty %s", self.first_header_item)
                continue

            row_data = {
                field_name: row[self.field_index[field_name]]
                for field_name in self.fields
            }
            created, case_id, error, bag_id = self._import_case(row_data, self.dry_run)
            processed_cases.append(
                {
                    "row_number": row_number,
                    "address": self._format_address(row_data),
                    "bag_id": bag_id,
                    "success": created,
                    "error": error,
                    "case_id": case_id,
                }
            )

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
                    value = ws.cell(row=cell.row, column=cell.column + 1).value
                    LOGGER.info(f"Found metadata {key}: {value}")
                    self.metadata[self.METADATA_MAPPING[key]] = value

    def _find_header_row_index(self, ws):
        for row_index, row in enumerate(
            ws.iter_rows(
                min_row=1, max_col=5, max_row=self.MAX_METADATA_ROWS, values_only=True
            ),
            start=1,
        ):
            for cell_value in row:
                if (
                    isinstance(cell_value, str)
                    and cell_value.lower() == self.first_header_item
                ):
                    return row_index

        raise BulkImportException("Kan kolombeschrijving niet vinden!")

    @staticmethod
    def _clean_header(header: list):
        return [
            (
                item.lower().replace("(beknopt)", "").rstrip(" .")
                if isinstance(item, str)
                else item
            )
            for item in header
        ]

    @staticmethod
    def _format_address(row_data: dict):
        """
        The address as in the file, with the postal code written the same way
        for every row: "Straat 1-A, 1234 AB".
        """

        def text(value):
            return "" if value is None else str(value).strip()

        number = text(row_data["huisnr"])
        suffix = text(row_data["toevoeging"])
        street = " ".join(
            part
            for part in (
                text(row_data["straat"]),
                f"{number}-{suffix}" if suffix else number,
            )
            if part
        )
        postal_code = text(row_data["postcode"])
        # A Dutch postal code ("1234ab", "1234 AB") as "1234 AB"; else as given.
        match = re.fullmatch(r"(\d{4})\s*([A-Za-z]{2})", postal_code)
        if match:
            postal_code = f"{match[1]} {match[2].upper()}"
        return f"{street}, {postal_code}" if postal_code else street

    @staticmethod
    def _get_bag_data(
        street_name: str, number: int, suffix: str | int, postal_code: str
    ):
        # Do basic field validation first, before cleaning the fields.
        search_string = f"{street_name} {number}-{suffix}, {postal_code}"
        serializer = AddressSimplifiedSerializer(
            data={
                "street_name": street_name,
                "number": number,
                "suffix": suffix,
                "postal_code": postal_code,
            }
        )
        if not serializer.is_valid():
            fields = [FIELD_LABELS.get(field, field) for field in serializer.errors]
            return {
                "error": (
                    f"Het adres is niet goed ingevuld. Controleer: {', '.join(fields)}."
                ),
            }

        street_name = serializer.validated_data["street_name"]
        number = serializer.validated_data["number"]
        suffix = serializer.validated_data["suffix"]
        postal_code = serializer.validated_data["postal_code"].replace(" ", "")
        if not all([street_name, number, postal_code]):
            return {"error": "Straat, huisnummer of postcode ontbreekt."}

        if suffix:
            search_string = f"{street_name} {number}-{suffix}, {postal_code}"
        else:
            search_string = f"{street_name} {number}, {postal_code}"

        result = {
            "bag_id": None,
            "search_address": search_string,
            "found_address": "",
            "error": "",
        }

        response = do_bag_search_pdok_by_address(search_string).get("response", {})

        if response.get("numFound", 0) == 0:
            result["error"] = "Adres niet gevonden."
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
                LOGGER.warning(f"Meer dan één adres gevonden voor {search_string}")
                for adres in response.get("docs", []):
                    LOGGER.warning(f"    {adres['weergavenaam']} + {adres['score']}")
                result["error"] = (
                    "Meerdere adressen gevonden. Controleer de toevoeging."
                )
                return result

        found_address = response.get("docs")[0]
        result["bag_id"] = found_address["adresseerbaarobject_id"]
        result["found_address"] = found_address["weergavenaam"]
        return result

    def _get_description(self, toelichting):
        """
        The explanation for all cases, with the one of the row below it. Only
        the one there is, or None without either.
        """
        row_description = "" if toelichting is None else str(toelichting).strip()
        parts = [part for part in (self.description, row_description) if part]
        return "\n\n".join(parts) or None

    def _import_case(self, row_data: dict, dry_run: bool):
        """
        Return whether a case can be (and, without dry run, is) imported, its
        id, else the error in words for the user, and the BAG id of the address
        (None when it was not found).
        """
        case_id = None
        address_data = self._get_bag_data(
            row_data["straat"],
            row_data["huisnr"],
            row_data["toevoeging"],
            row_data["postcode"],
        )
        bag_id = address_data.get("bag_id")
        if address_data["error"] or bag_id is None:
            return False, case_id, address_data["error"], bag_id

        toelichting = row_data["toelichting"]
        if isinstance(toelichting, str) and toelichting.startswith("#"):
            return (
                False,
                case_id,
                f"De toelichting bevat een foute formule ({toelichting}).",
                bag_id,
            )
        case_data = {
            **self.case_default_data,
            "bag_id": bag_id,
            "description": self._get_description(toelichting),
        }

        serializer = CaseCreateSerializer(
            data=case_data,
            context={"request": self.request},
            # Checking the addresses (a dry run) needs only the theme: the
            # reason may be missing. Creating the cases needs what creating
            # one case needs.
            partial=self.dry_run and self.reason is None,
        )
        if not serializer.is_valid():
            messages = "; ".join(_error_messages(serializer.errors))
            return (
                False,
                case_id,
                f"De zaakgegevens zijn niet geldig: {messages}",
                bag_id,
            )

        open_cases_at_address = Case.objects.filter(
            theme=self.theme, address__bag_id=bag_id, end_date=None
        )
        if open_cases_at_address.exists():
            return (
                False,
                case_id,
                "Er bestaat al een open zaak met dit thema op dit adres.",
                bag_id,
            )

        if not dry_run:
            case_obj = serializer.save()
            case_id = case_obj.pk

        return True, case_id, None, bag_id
