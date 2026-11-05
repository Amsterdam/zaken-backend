from textwrap import dedent

from apps.addresses.serializers import AddressSimplifiedSerializer
from apps.cases.models import Case, CaseReason, CaseState, CaseTheme, Subject
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

        theme = CaseTheme.objects.get(name="Leegstand")
        reason = CaseReason.objects.get(theme=theme, name="Leegstandsmelding eigenaar")

        subject_names = ["Administratieve leegstand", "Professionele eigenaar"]
        subjects = list(
            Subject.objects.filter(name__in=subject_names, theme_id=theme.id).values(
                "id", "name"
            )
        )
        subject_ids = [s["id"] for s in subjects]
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

        processed = 0
        created = 0

        for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
            adres = row[self.fields["adres"]["idx"]]
            if not adres:
                self.stdout.write(self.style.WARNING("Skipping row with empty adres"))
                continue

            row_data = {
                field_name: row[field_data["idx"]]
                for field_name, field_data in self.fields.items()
            }
            processed += 1

            bag_id = self._get_bag_id(
                row_data["adres"],
                row_data["huisnr."],
                row_data["toevoeging"],
                row_data["postcode"],
            )
            if bag_id is None:
                continue

            # a = {'response':
            #          {'numFound': 1, 'start': 0, 'maxScore': 8.632138, 'numFoundExact': True, 'docs':
            #              [
            #                  {'woonplaatsnaam': 'Amsterdam', 'weergavenaam': 'Hemonystraat 66-3, 1074BT Amsterdam',
            #                   'huisnummertoevoeging': '3', 'adrestype': 'hoofdadres', 'gemeentenaam': 'Amsterdam',
            #                   'postcode': '1074BT', 'nummeraanduiding_id': '0363200000124344',
            #                   'adresseerbaarobject_id': '0363010000662243', 'huisnummer': 66, 'straatnaam': 'Hemonystraat',
            #                   'score': 8.632138}
            #              ]
            #           },
            #      }

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
                    "id": reason.id,
                    "name": reason.name,
                },
                "reason_id": reason.id,
                "subject_ids": subject_ids,
                "subjects": subjects,
                "theme": {
                    "id": theme.id,
                    "name": theme.name,
                },
                "theme_id": theme.id,
            }

            # TODO: Voor de adressen zonder openstaande zaak in AZA moet automatisch een nieuwe zaak worden aangemaakt met het stadium “leegstandbeschikking verstuurd”.
            # TODO: Voor adressen met openstaande zaak voor nu alleen een warning printen.

            serializer = CaseCreateSerializer(
                data=data,
                context={"request": self.request},
            )
            serializer.is_valid(raise_exception=True)
            self.stdout.write(f"Creating case for bag_id={bag_id} ", ending="")
            case_exists = (
                Case.objects.filter(
                    theme=theme,
                    address__bag_id=bag_id,
                )
                .exclude(
                    case_states__status=CaseState.CaseStateChoice.AFGESLOTEN,
                )
                .exists()
            )
            if case_exists:
                self.stdout.write(self.style.WARNING("SKIPPED (case already exists)"))
                continue
            if not dry_run:
                serializer.save()
                created += 1

            self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={processed}, created={created}, dry_run={dry_run}"
            )
        )

    @staticmethod
    def _find_header_row_index(ws):
        for row_index, row in enumerate(
            ws.iter_rows(min_row=1, max_col=2, max_row=10, values_only=True), start=1
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

    def _get_bag_id(
        self, street_name: str, number: int, suffix: str | int, postal_code: str
    ):
        street_name = street_name.strip()
        number = number
        suffix = str(suffix).strip()
        postal_code = postal_code.replace(" ", "").replace("\xa0", "")
        search_string = f"{street_name} {number}-{suffix}, {postal_code}"

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
            self.stdout.write(
                self.style.WARNING(f"FOUT IN INVOERDATA: {search_string}: {e}")
            )
            return None

        response = do_bag_search_pdok_by_address(search_string).get("response", {})

        if response.get("numFound", 0) == 0:
            self.stdout.write(
                self.style.NOTICE(f"No such address found: {search_string} !")
            )
            return None
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
                self.stdout.write(
                    self.style.WARNING(
                        f"Found more than one address for {search_string} !"
                    )
                )
                for adres in response.get("docs", []):
                    self.stdout.write(f"    {adres['weergavenaam']} + {adres['score']}")
                return None

        found_address = response.get("docs")[0]
        bag_id = found_address["adresseerbaarobject_id"]
        self.stdout.write(self.style.SUCCESS(found_address["weergavenaam"]))
        return bag_id

    def get_description_text(self, reason: str, date_start, date_end, details):
        return dedent(
            f"""Leegstand gemeld: {"TODO"} op {"TODO"}.
            Leeg sinds: {date_start.strftime("%d-%m-%Y") if date_start else '-'}.
            Reden: {reason}.
            Opleverdatum: {date_end.strftime("%d-%m-%Y") if date_end else '-'}
            Bijzonderheden: {details}
        """
        ).strip()
