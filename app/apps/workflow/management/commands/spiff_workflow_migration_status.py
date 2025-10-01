"""
Django management command to check workflow migration status

Usage:
    python manage.py workflow_migration_status
    python manage.py workflow_migration_status --detailed
"""

import logging
from collections import defaultdict

from apps.workflow.migration_v1_to_v3 import is_v1_format
from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check migration status of workflows from v1 to v3 format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed breakdown by workflow type",
        )

    def handle(self, *args, **options):
        detailed = options["detailed"]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 WORKFLOW MIGRATION STATUS\n"))
        self.stdout.write("=" * 60 + "\n")

        # Get all workflows with serialized state
        all_workflows = CaseWorkflow.objects.exclude(
            serialized_workflow_state__isnull=True
        )

        total_count = all_workflows.count()

        if total_count == 0:
            self.stdout.write(
                self.style.WARNING("No workflows with serialized state found.")
            )
            return

        # Count v1 and v3 workflows
        v1_count = 0
        v3_count = 0
        v1_workflows = []

        self.stdout.write("🔍 Analyzing workflows...\n")

        for workflow in all_workflows:
            if is_v1_format(workflow.serialized_workflow_state):
                v1_count += 1
                v1_workflows.append(workflow)
            else:
                v3_count += 1

        # Calculate percentages
        v1_percent = (v1_count / total_count * 100) if total_count > 0 else 0
        v3_percent = (v3_count / total_count * 100) if total_count > 0 else 0

        # Overall statistics
        self.stdout.write("📈 Overall Statistics:\n")
        self.stdout.write(f"   Total workflows: {total_count}")
        self.stdout.write(
            self.style.WARNING(f"   v1 format: {v1_count} ({v1_percent:.1f}%)")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   v3 format: {v3_count} ({v3_percent:.1f}%)")
        )

        # Migration progress bar
        self.print_progress_bar(v3_percent)

        if detailed and v1_workflows:
            self.print_detailed_breakdown(v1_workflows)

        # Recommendations
        self.stdout.write("\n💡 Recommendations:\n")

        if v1_count > 0:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  {v1_count} workflows need migration")
            )
            self.stdout.write("\n   Next steps:")
            self.stdout.write("   1. Create backup: python manage.py backup_workflows")
            self.stdout.write(
                "   2. Test migration: python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run"
            )
            self.stdout.write(
                "   3. Run migration: python manage.py spiff_migrate_workflows_v1_to_v3"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("   ✓ All workflows are in v3 format!")
            )

        self.stdout.write("\n" + "=" * 60 + "\n")

    def print_progress_bar(self, percent):
        """Print a visual progress bar"""
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        self.stdout.write("\n   Migration Progress:")
        self.stdout.write(f"   [{bar}] {percent:.1f}%\n")

    def print_detailed_breakdown(self, v1_workflows):
        """Print detailed breakdown by workflow type"""
        self.stdout.write("\n📋 Detailed Breakdown (v1 workflows only):\n")

        # Group by workflow type
        by_type = defaultdict(list)
        for workflow in v1_workflows:
            by_type[workflow.workflow_type].append(workflow)

        self.stdout.write("   By Workflow Type:")
        for workflow_type, workflows in sorted(by_type.items()):
            completed_count = sum(1 for wf in workflows if wf.completed)
            active_count = len(workflows) - completed_count

            self.stdout.write(
                f"      {workflow_type}: {len(workflows)} total "
                f"({active_count} active, {completed_count} completed)"
            )

        # Group by completion status
        completed = sum(1 for wf in v1_workflows if wf.completed)
        active = len(v1_workflows) - completed

        self.stdout.write("\n   By Status:")
        self.stdout.write(f"      Active: {active}")
        self.stdout.write(f"      Completed: {completed}")

        # Show sample workflow IDs
        self.stdout.write("\n   Sample workflow IDs to migrate:")
        sample_ids = [wf.id for wf in v1_workflows[:10]]
        self.stdout.write(f'      {", ".join(map(str, sample_ids))}')

        if len(v1_workflows) > 10:
            self.stdout.write(f"      ... and {len(v1_workflows) - 10} more")
