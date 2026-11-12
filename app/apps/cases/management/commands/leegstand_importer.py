from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory
from utils.bulk_leegstand_importer import BulkLeegstandImporter


class Command(BaseCommand):
    help = (
        "Import Leegstand cases from an Excel file\n\n"
        "Example:\n"
        "  python manage.py case_importer cases.xlsx \\\n"
        "    --username import_user@amsterdam.nl \\\n"
        "    --project 5 \\\n"
        "    --dry-run"
    )

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

        parser.add_argument(
            "--project",
            nargs=1,
            metavar=("ID",),
        )

    def handle(self, *args, **options):
        excel_file = options["file"]
        dry_run = options["dry_run"]
        username = options["username"]

        project_id = int(options["project"]) if options["project"] else None

        ### Section var init
        User = get_user_model()
        user = User.objects.get(username=username)

        importer = BulkLeegstandImporter(excel_file, user, dry_run, project_id)
        processed_result = importer.import_from_file()

        for res in processed_result["case_data"]:
            if res["success"]:
                self.stdout.write(self.style.SUCCESS(res["msg"]))
            else:
                self.stdout.write(self.style.NOTICE(res["msg"]))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={processed_result["total_processed"]}, created={processed_result["total_created"]}, dry_run={dry_run}"
            )
        )
