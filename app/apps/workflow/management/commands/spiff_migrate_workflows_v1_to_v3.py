"""
Django management command to migrate workflows from v1 to v3 format

Usage:
    # Dry run (preview changes)
    python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run

    # Migrate specific workflows
    python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 123 456 789

    # Migrate all non-completed workflows
    python manage.py spiff_migrate_workflows_v1_to_v3 --exclude-completed

    # Actually perform migration
    python manage.py spiff_migrate_workflows_v1_to_v3
"""

import json
import logging

from apps.workflow.models import CaseWorkflow
from apps.workflow.spiff.spiff_migration_v1_to_v3 import (
    get_migration_stats,
    is_v1_format,
    migrate_v1_to_v3,
    validate_v3_structure,
)
from django.core.management.base import BaseCommand
from django.db import transaction
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate SpiffWorkflow data from v1 to v3 format"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            "total": 0,
            "success": 0,
            "error": 0,
            "skipped": 0,
            "already_v3": 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform migration without saving to database",
        )
        parser.add_argument(
            "--workflow-ids",
            nargs="+",
            type=int,
            help="Specific workflow IDs to migrate",
        )
        parser.add_argument(
            "--exclude-completed",
            action="store_true",
            help="Skip completed workflows",
        )
        parser.add_argument(
            "--workflow-type",
            type=str,
            help="Only migrate workflows of specific type (e.g., director, visit)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of workflows to process in each batch (default: 100)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed migration statistics for each workflow",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate migrated data without saving",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"] or options["validate_only"]
        workflow_ids = options.get("workflow_ids")
        exclude_completed = options["exclude_completed"]
        workflow_type = options.get("workflow_type")
        batch_size = options["batch_size"]
        verbose = options["verbose"]
        validate_only = options["validate_only"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be saved")
            )

        # Query workflows
        queryset = CaseWorkflow.objects.all()

        if workflow_ids:
            queryset = queryset.filter(id__in=workflow_ids)

        if exclude_completed:
            queryset = queryset.filter(completed=False)

        if workflow_type:
            queryset = queryset.filter(workflow_type=workflow_type)

        # Filter only workflows with serialized state
        queryset = queryset.exclude(serialized_workflow_state__isnull=True)

        # Filter for v1 format
        workflows_to_migrate = []
        for workflow in queryset:
            if is_v1_format(workflow.serialized_workflow_state):
                workflows_to_migrate.append(workflow)
            else:
                self.stats["already_v3"] += 1

        self.stats["total"] = len(workflows_to_migrate)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Found {self.stats["total"]} workflows in v1 format to migrate'
            )
        )

        if self.stats["already_v3"] > 0:
            self.stdout.write(
                f'   ({self.stats["already_v3"]} workflows already in v3 format)'
            )

        if not workflows_to_migrate:
            self.stdout.write(self.style.WARNING("\n✓ No workflows to migrate"))
            return

        # Process in batches
        for i in range(0, len(workflows_to_migrate), batch_size):
            batch = workflows_to_migrate[i : i + batch_size]
            self.stdout.write(
                f"\n📦 Processing batch {i // batch_size + 1} "
                f"({len(batch)} workflows)..."
            )

            for workflow in batch:
                try:
                    migration_stats = self.migrate_workflow(
                        workflow,
                        dry_run=dry_run,
                        verbose=verbose,
                        validate_only=validate_only,
                    )
                    self.stats["success"] += 1

                    status_icon = "✓" if not dry_run else "🔍"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  {status_icon} Workflow {workflow.id} "
                            f"({workflow.workflow_type})"
                        )
                    )

                    if verbose:
                        self.print_migration_stats(migration_stats)

                except Exception as e:
                    self.stats["error"] += 1
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Workflow {workflow.id}: {str(e)}")
                    )
                    logger.error(
                        f"Migration error for workflow {workflow.id}", exc_info=True
                    )

        # Print summary
        self.print_summary(dry_run, validate_only)

    def migrate_workflow(
        self,
        workflow: CaseWorkflow,
        dry_run: bool = True,
        verbose: bool = False,
        validate_only: bool = False,
    ) -> dict:
        """
        Migrate a single workflow from v1 to v3 format

        Args:
            workflow: CaseWorkflow instance to migrate
            dry_run: If True, don't save changes
            verbose: If True, return detailed statistics
            validate_only: If True, only validate without attempting save

        Returns:
            Dictionary with migration statistics

        Raises:
            ValueError: If migration or validation fails
        """
        # Get workflow spec
        spec = workflow.get_workflow_spec()
        if not spec:
            raise ValueError("Could not load workflow spec")

        # Perform migration
        v1_data = json.dumps(workflow.serialized_workflow_state)
        v3_data_str = migrate_v1_to_v3(v1_data, spec)
        v3_data = json.loads(v3_data_str)

        # Validate structure
        is_valid, errors = validate_v3_structure(v3_data)
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        # Validate by deserializing with SpiffWorkflow
        reg = BpmnWorkflowSerializer.configure(CAMUNDA_CONFIG)
        serializer = BpmnWorkflowSerializer(registry=reg)

        try:
            wf = serializer.deserialize_json(v3_data_str)
            # Add script engine
            wf = workflow.get_script_engine(wf)

            # Verify we can access tasks
            tasks = wf.get_tasks()
            if not tasks:
                raise ValueError("No tasks found in deserialized workflow")

            # Verify data integrity
            if wf.last_task and workflow.data:
                # Check that critical data fields are preserved
                for key in workflow.data.keys():
                    if key not in wf.last_task.data:
                        logger.warning(
                            f"Data field '{key}' missing from last_task.data "
                            f"for workflow {workflow.id}"
                        )

        except Exception as e:
            raise ValueError(f"Deserialization validation failed: {e}")

        # Get migration statistics
        migration_stats = get_migration_stats(v1_data, v3_data_str)

        # Save if not dry run
        if not dry_run and not validate_only:
            with transaction.atomic():
                workflow.serialized_workflow_state = v3_data
                workflow.save(update_fields=["serialized_workflow_state"])

                # Update related user tasks if needed
                if workflow.tasks.exists():
                    logger.info(
                        f"Workflow {workflow.id} has {workflow.tasks.count()} "
                        f"user tasks - consider updating them"
                    )

        return migration_stats

    def print_migration_stats(self, stats: dict):
        """Print detailed migration statistics"""
        self.stdout.write(f'    📈 Tasks: {stats["v3_task_count"]}')
        self.stdout.write(f'    🔓 Unpickled fields: {stats["unpickled_fields"]}')

        if stats.get("task_type_distribution"):
            self.stdout.write("    📋 Task types:")
            for typename, count in stats["task_type_distribution"].items():
                self.stdout.write(f"       - {typename}: {count}")

    def print_summary(self, dry_run: bool, validate_only: bool):
        """Print migration summary statistics"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 MIGRATION SUMMARY\n"))

        self.stdout.write(f'Total workflows processed: {self.stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'✓ Successful: {self.stats["success"]}'))

        if self.stats["error"] > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {self.stats["error"]}'))

        if self.stats["already_v3"] > 0:
            self.stdout.write(f'ℹ Already v3 format: {self.stats["already_v3"]}')

        success_rate = (
            (self.stats["success"] / self.stats["total"] * 100)
            if self.stats["total"] > 0
            else 0
        )
        self.stdout.write(f"\nSuccess rate: {success_rate:.1f}%")

        if dry_run and not validate_only:
            self.stdout.write(
                self.style.WARNING("\n⚠️  DRY RUN - No changes were saved to database")
            )
            self.stdout.write("Run without --dry-run to apply changes")
        elif validate_only:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✓ VALIDATION COMPLETE - All workflows can be migrated"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✓ MIGRATION COMPLETE - All changes saved to database"
                )
            )

        self.stdout.write("=" * 60 + "\n")
