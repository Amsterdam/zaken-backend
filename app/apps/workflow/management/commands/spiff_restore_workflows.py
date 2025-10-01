"""
Django management command to restore workflow data from backup

Usage:
    python manage.py restore_workflows --input workflow_backup_20250101_120000.json --dry-run
    python manage.py restore_workflows --input workflow_backup_20250101_120000.json
"""

import json
import logging
from pathlib import Path

from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Restore workflow serialized states from backup JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Input backup file path",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview restore without making changes",
        )
        parser.add_argument(
            "--workflow-ids",
            nargs="+",
            type=int,
            help="Only restore specific workflow IDs",
        )

    def handle(self, *args, **options):
        input_path = options["input"]
        dry_run = options["dry_run"]
        workflow_ids = options.get("workflow_ids")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )

        # Load backup file
        backup_file = Path(input_path)
        if not backup_file.exists():
            raise CommandError(f"Backup file not found: {input_path}")

        with backup_file.open("r") as f:
            backup_data = json.load(f)

        self.stdout.write(
            f"\n📂 Loading backup from {input_path}\n"
            f'   Created: {backup_data.get("created_at")}\n'
            f'   Total workflows in backup: {backup_data.get("total_workflows")}'
        )

        # Filter workflows if specific IDs requested
        workflows_to_restore = backup_data["workflows"]
        if workflow_ids:
            workflows_to_restore = [
                wf for wf in workflows_to_restore if wf["id"] in workflow_ids
            ]

        self.stdout.write(f"\n🔄 Restoring {len(workflows_to_restore)} workflows...\n")

        success_count = 0
        error_count = 0
        not_found_count = 0

        for backup_entry in workflows_to_restore:
            workflow_id = backup_entry["id"]

            try:
                # Check if workflow exists
                workflow = CaseWorkflow.objects.filter(id=workflow_id).first()
                if not workflow:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Workflow {workflow_id} not found in database"
                        )
                    )
                    not_found_count += 1
                    continue

                # Restore serialized state
                if not dry_run:
                    with transaction.atomic():
                        workflow.serialized_workflow_state = backup_entry[
                            "serialized_workflow_state"
                        ]
                        workflow.data = backup_entry["data"]
                        workflow.save(
                            update_fields=["serialized_workflow_state", "data"]
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Restored workflow {workflow_id} "
                        f'({backup_entry["workflow_type"]})'
                    )
                )
                success_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Failed to restore workflow {workflow_id}: {e}"
                    )
                )
                logger.error(f"Restore error for workflow {workflow_id}", exc_info=True)

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 RESTORE SUMMARY\n"))
        self.stdout.write(f"Total in backup: {len(workflows_to_restore)}")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully restored: {success_count}")
        )

        if not_found_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠ Not found in database: {not_found_count}")
            )

        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  DRY RUN - No changes were made\n"
                    "Run without --dry-run to restore workflows"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ RESTORE COMPLETE"))

        self.stdout.write("=" * 60 + "\n")
