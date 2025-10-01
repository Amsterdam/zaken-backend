"""
Django management command to backup workflow data before migration

Usage:
    python manage.py backup_workflows
    python manage.py backup_workflows --output /path/to/backup.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backup workflow serialized states to JSON file before migration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path (default: workflow_backup_TIMESTAMP.json)",
        )
        parser.add_argument(
            "--workflow-ids",
            nargs="+",
            type=int,
            help="Specific workflow IDs to backup",
        )
        parser.add_argument(
            "--exclude-completed",
            action="store_true",
            help="Exclude completed workflows",
        )

    def handle(self, *args, **options):
        output_path = options.get("output")
        workflow_ids = options.get("workflow_ids")
        exclude_completed = options["exclude_completed"]

        # Generate default output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"workflow_backup_{timestamp}.json"

        # Query workflows
        queryset = CaseWorkflow.objects.exclude(serialized_workflow_state__isnull=True)

        if workflow_ids:
            queryset = queryset.filter(id__in=workflow_ids)

        if exclude_completed:
            queryset = queryset.filter(completed=False)

        self.stdout.write(f"📦 Backing up {queryset.count()} workflows...")

        # Create backup data
        backup_data = {
            "created_at": datetime.now().isoformat(),
            "total_workflows": queryset.count(),
            "workflows": [],
        }

        for workflow in queryset:
            backup_entry = {
                "id": workflow.id,
                "case_id": workflow.case_id,
                "workflow_type": workflow.workflow_type,
                "workflow_version": workflow.workflow_version,
                "workflow_theme_name": workflow.workflow_theme_name,
                "completed": workflow.completed,
                "serialized_workflow_state": workflow.serialized_workflow_state,
                "data": workflow.data,
            }
            backup_data["workflows"].append(backup_entry)

        # Write to file
        output_file = Path(output_path)
        with output_file.open("w") as f:
            json.dump(backup_data, f, indent=2)

        file_size = output_file.stat().st_size / (1024 * 1024)  # Size in MB

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Backup completed!\n"
                f"  File: {output_path}\n"
                f"  Size: {file_size:.2f} MB\n"
                f'  Workflows: {len(backup_data["workflows"])}'
            )
        )
