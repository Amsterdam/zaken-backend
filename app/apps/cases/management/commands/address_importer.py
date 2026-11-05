from textwrap import dedent

from apps.addresses.serializers import AddressSimplifiedSerializer
from apps.cases.models import Case, CaseReason, CaseTheme, Subject
from apps.cases.serializers import CaseCreateSerializer
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from openpyxl import load_workbook
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from utils.api_queries_bag import do_bag_search_pdok_by_address


class Command(BaseCommand):
    help = (
        "Import Leegstand cases from an Excel file\n\n"
        "Example:\n"
        "  python manage.py case_importer cases.xlsx \\\n"
        "    --username import_user@amsterdam.nl \\\n"
        '    --project 5 "Project"\\\n'
        "    --dry-run"
    )

    fields = {
        "adres": {"idx": 0},
        "postcode": {"idx": 0},
        "huisnr.": {"idx": 0},
        "toevoeging": {"idx": 0},
        "reden leegstand": {"idx": 0},
        "datum start werkzaamheden": {"idx": 0},
        "datum oplevering": {"idx": 0},
        "bijzonderheden": {"idx": 0},
    }

    def __init__(self):
        super().__init__()
        factory = APIRequestFactory()
        self.request = factory.post("/")

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("--username", type=str, required=True)

        parser.set_defaults(dry_run=True)
        parser.add_argument(
            "--no-dry-run",
            action="store_false",
            dest="dry_run",
        )

        # parser.add_argument(
        #     "--project",
        #     nargs=2,
        #     metavar=("ID", "NAME"),
        #     required=True,
        # )

    def handle(self, *args, **options):
        excel_file = options["file"]
        dry_run = options["dry_run"]
        username = options["username"]
        #
        # project_id, project_name = options["project"]
        # project_id = int(project_id)

        ### Section var init
        User = get_user_model()
        user = User.objects.get(username=username)

        self.theme_leegstand = CaseTheme.objects.get(name="Leegstand")
        self.reason = CaseReason.objects.get(
            theme=self.theme_leegstand, name="Leegstandsmelding eigenaar"
        )

        subject_names = ["Administratieve leegstand", "Professionele eigenaar"]
        self.subjects = list(
            Subject.objects.filter(
                name__in=subject_names, theme_id=self.theme_leegstand.id
            ).values("id", "name")
        )
        self.subject_ids = [s["id"] for s in self.subjects]
        self.request.user = user

        ### Section read Excel
        try:
            wb = load_workbook(excel_file)
            ws = wb.active
        except Exception as e:
            raise CommandError(f"Failed to read Excel file: {e}")

        header_row_idx = self._find_header_row_index(ws)
        header_raw = [cell.value for cell in ws[header_row_idx]]
        header = self._clean_header(header_raw)

        for column_name, field in self.fields.items():
            try:
                field_idx = header.index(column_name)
                field["idx"] = field_idx
            except ValueError:
                raise CommandError(f"Excel file must contain {column_name} column")

        num_processed = 0
        num_created = 0
        processed_result = []

        for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
            adres = row[self.fields["adres"]["idx"]]
            if not adres:
                self.stdout.write(self.style.WARNING("Skipping row with empty adres"))
                continue

            row_data = {
                field_name: row[field_data["idx"]]
                for field_name, field_data in self.fields.items()
            }

            created, msg = self._import_case(row_data, dry_run)
            processed_result.append({"success": created, "msg": msg})

            num_processed += 1
            num_created += created
            if created:
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                self.stdout.write(self.style.NOTICE(msg))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={num_processed}, created={num_created}, dry_run={dry_run}"
            )
        )

    @staticmethod
    def _find_header_row_index(ws):
        for row_index, row in enumerate(
            ws.iter_rows(min_row=1, max_col=5, max_row=10, values_only=True), start=1
        ):
            for cell_value in row:
                if isinstance(cell_value, str) and cell_value.lower() == "adres":
                    return row_index

        raise CommandError("Cannot locate header!")

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
            context={"request": self.request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            error_str = f"FOUT IN INVOERDATA: {search_string}: {e}"
            result["error"] = error_str
            return result

        response = do_bag_search_pdok_by_address(search_string).get("response", {})

        if response.get("numFound", 0) == 0:
            error_str = f"No such address found: {search_string} !"
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
                error_str = f"Found more than one address for {search_string} !"
                for adres in response.get("docs", []):
                    self.stdout.write(f"    {adres['weergavenaam']} + {adres['score']}")
                result["error"] = error_str
                return result

        found_address = response.get("docs")[0]
        result["bag_id"] = found_address["adresseerbaarobject_id"]
        result["found_address"] = found_address["weergavenaam"]
        return result

    def get_description_text(self, reason: str, date_start, date_end, details):
        return dedent(
            f"""Leegstand gemeld: {"TODO"} op {"TODO"}.
            Leeg sinds: {date_start.strftime("%d-%m-%Y") if date_start else '-'}.
            Reden: {reason}.
            Opleverdatum: {date_end.strftime("%d-%m-%Y") if date_end else '-'}
            Bijzonderheden: {details}
        """
        ).strip()

    def _import_case(self, row_data, dry_run):
        success = False
        msg = ""

        address_data = self._get_bag_data(
            row_data["adres"],
            row_data["huisnr."],
            row_data["toevoeging"],
            row_data["postcode"],
        )
        bag_id = address_data["bag_id"]
        if address_data["error"] or bag_id is None:
            return False, address_data["error"]

        description = self.get_description_text(
            row_data["reden leegstand"],
            row_data["datum start werkzaamheden"],
            row_data["datum oplevering"],
            row_data["bijzonderheden"],
        )

        data = {
            "bag_id": bag_id,
            "description": description,
            "reason": {
                "id": self.reason.id,
                "name": self.reason.name,
            },
            "reason_id": self.reason.id,
            "subject_ids": self.subject_ids,
            "subjects": self.subjects,
            "theme": {
                "id": self.theme_leegstand.id,
                "name": self.theme_leegstand.name,
            },
            "theme_id": self.theme_leegstand.id,
        }

        serializer = CaseCreateSerializer(
            data=data,
            context={"request": self.request},
        )
        serializer.is_valid(raise_exception=True)

        msg = f"Creating case for address={address_data["search_address"]} "

        open_cases_at_address = Case.objects.filter(
            theme=self.theme_leegstand, address__bag_id=bag_id, end_date=None
        )
        if open_cases_at_address.exists():
            return False, msg + "SKIPPED (Open cases for address found!)"
        if not dry_run:
            serializer.save()
            success = True

        return success, msg + "OK"
