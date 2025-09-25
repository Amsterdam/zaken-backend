"""
Management command to migrate SpiffWorkflow serialization from v1.1 to v3.1.1 format.

This command can be used during deployment to batch migrate workflow serialization
without using the Django admin interface.
"""

import logging
from typing import Any, Dict, List

from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate SpiffWorkflow serialization from v1.1 to v3.1.1 format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )
        parser.add_argument(
            "--workflow-type",
            type=str,
            help="Only migrate workflows of this type (e.g., director, visit, etc.)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of workflows to process in each batch (default: 100)",
        )
        parser.add_argument(
            "--case-id",
            type=int,
            help="Only migrate workflows for this specific case ID",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        workflow_type = options["workflow_type"]
        batch_size = options["batch_size"]
        case_id = options["case_id"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting SpiffWorkflow serialization migration (dry_run={dry_run})"
            )
        )

        # Build queryset
        queryset = CaseWorkflow.objects.filter(
            serialized_workflow_state__isnull=False,
            completed=False,  # Only migrate active workflows
        )

        if workflow_type:
            queryset = queryset.filter(workflow_type=workflow_type)

        if case_id:
            queryset = queryset.filter(case__id=case_id)

        total_workflows = queryset.count()
        self.stdout.write(f"Found {total_workflows} workflows to analyze")

        if total_workflows == 0:
            self.stdout.write(self.style.WARNING("No workflows found to migrate"))
            return

        # Process in batches
        results = {
            "total": 0,
            "compatible": 0,
            "migrated": 0,
            "failed": 0,
            "errors": [],
        }

        for i in range(0, total_workflows, batch_size):
            batch = queryset[i : i + batch_size]
            self.stdout.write(
                f"Processing batch {i // batch_size + 1} ({len(batch)} workflows)"
            )

            batch_results = self._process_batch(batch, dry_run)
            self._update_results(results, batch_results)

        # Show summary
        self._show_summary(results, dry_run)

    def _process_batch(
        self, workflows: List[CaseWorkflow], dry_run: bool
    ) -> Dict[str, Any]:
        batch_results = {
            "total": 0,
            "compatible": 0,
            "migrated": 0,
            "failed": 0,
            "errors": [],
        }

        for workflow in workflows:
            batch_results["total"] += 1
            result = self._migrate_workflow(workflow, dry_run)

            if result["status"] == "compatible":
                batch_results["compatible"] += 1
            elif result["status"] == "migrated":
                batch_results["migrated"] += 1
            elif result["status"] == "failed":
                batch_results["failed"] += 1
                batch_results["errors"].append(
                    {
                        "workflow_id": workflow.id,
                        "case_id": workflow.case.id if workflow.case else None,
                        "error": result["message"],
                    }
                )

        return batch_results

    def _migrate_workflow(
        self, workflow: CaseWorkflow, dry_run: bool
    ) -> Dict[str, str]:
        """Migrate a single workflow's serialization format."""

        if not workflow.serialized_workflow_state:
            return {"status": "failed", "message": "No serialized state found"}

        # Check if migration is needed using the model method
        if not workflow.needs_spiff_migration():
            return {"status": "compatible", "message": "Already compatible with v3.1.1"}

        if dry_run:
            return {"status": "needs_migration", "message": "Would be migrated"}

        # Perform the migration using the model method
        success, message = workflow.migrate_spiff_serialization()

        if success:
            return {"status": "migrated", "message": message}
        else:
            logger.error(f"Workflow {workflow.id} migration failed: {message}")
            return {"status": "failed", "message": message}

    def _update_results(self, total_results: Dict, batch_results: Dict):
        for key in ["total", "compatible", "migrated", "failed"]:
            total_results[key] += batch_results[key]
        total_results["errors"].extend(batch_results["errors"])

    def _show_summary(self, results: Dict, dry_run: bool):
        self.stdout.write(self.style.SUCCESS("\n=== Migration Summary ==="))
        self.stdout.write(f"Total workflows processed: {results['total']}")
        self.stdout.write(f"Already compatible: {results['compatible']}")
        self.stdout.write(f"Successfully migrated: {results['migrated']}")
        self.stdout.write(f"Failed migrations: {results['failed']}")

        if results["errors"]:
            self.stdout.write(
                self.style.ERROR(f"\n=== Errors ({len(results['errors'])}) ===")
            )
            for error in results["errors"][:10]:  # Show first 10 errors
                self.stdout.write(
                    f"Workflow {error['workflow_id']} (Case {error['case_id']}): {error['error']}"
                )
            if len(results["errors"]) > 10:
                self.stdout.write(f"... and {len(results['errors']) - 10} more errors")

        if (
            dry_run
            and (results["total"] - results["compatible"] - results["failed"]) > 0
        ):
            migratable = results["total"] - results["compatible"] - results["failed"]
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run complete. {migratable} workflows can be migrated. "
                    "Run without --dry-run to perform the migration."
                )
            )
        elif not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nMigration complete! {results['migrated']} workflows migrated successfully."
                )
            )
