from apps.cases.models import CaseTheme
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from utils.bulk_case_importer import BulkCaseImporter, BulkImportException

THEME_NAME = "Leegstand"


class Command(BaseCommand):
    help = (
        "Import Leegstand cases from an Excel file. Without --no-dry-run it only\n"
        "checks the rows, as the dry run of POST /cases/process-file/.\n\n"
        "Example:\n"
        "  python manage.py leegstand_importer cases.xlsx \\\n"
        "    --username import_user@amsterdam.nl \\\n"
        "    --reason 12 --subject 3 --subject 4 \\\n"
        "    --no-dry-run"
    )

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("--username", type=str, required=True)

        parser.set_defaults(dry_run=True)
        parser.add_argument(
            "--no-dry-run",
            action="store_false",
            dest="dry_run",
        )

        parser.add_argument("--reason", type=int, metavar="ID")
        parser.add_argument(
            "--subject", type=int, action="append", default=[], metavar="ID"
        )
        parser.add_argument("--project", type=int, metavar="ID")
        parser.add_argument("--jump-to", type=str, metavar="TARGET")
        parser.add_argument("--description", type=str)

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if not dry_run and options["reason"] is None:
            raise CommandError("--reason is required with --no-dry-run.")

        user = get_user_model().objects.get(username=options["username"])
        theme = CaseTheme.objects.get(name=THEME_NAME)

        with open(options["file"], "rb") as file:
            try:
                processed_result = BulkCaseImporter(
                    file,
                    user,
                    theme=theme,
                    reason=options["reason"],
                    subjects=options["subject"],
                    project=options["project"],
                    jump_to=options["jump_to"],
                    description=options["description"],
                    dry_run=dry_run,
                ).import_from_file()
            except BulkImportException as exc:
                raise CommandError(str(exc))

        for row in processed_result["case_data"]:
            line = f"Rij {row['row_number']}: {row['address']}: "
            if row["success"]:
                case = f"zaak {row['case_id']}" if row["case_id"] else "OK"
                self.stdout.write(self.style.SUCCESS(line + case))
            else:
                self.stdout.write(self.style.NOTICE(line + row["error"]))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={processed_result['total_processed']}, "
                f"created={processed_result['total_created']}, dry_run={dry_run}"
            )
        )
