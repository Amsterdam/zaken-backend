# SpiffWorkflow v1 to v3 Migration Guide

This guide explains how to migrate existing workflow data from SpiffWorkflow v1 format to v3 format.

## Overview

### What Changed?

**v1 Format:**
- Nested tree structure (`task_tree` with `children`)
- Pickled data fields (stored as `{"__bytes__": "base64_encoded_pickle"}`)
- UUID references as objects (`{"__uuid__": "abc-123"}`)
- Missing metadata fields

**v3 Format:**
- Flat dictionary of tasks (`tasks` dict with all tasks)
- Plain JSON data (no pickling)
- UUID references as strings (`"abc-123"`)
- Additional metadata: `typename`, `correlations`, `spec`, etc.

## Prerequisites

1. **Backup your database** before running any migration
2. Test on a staging environment first
3. Ensure you're on the correct branch with v3 SpiffWorkflow

## Migration Steps

### Step 1: Create Backup

```bash
# Backup the entire database
pg_dump your_database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# Or backup just the workflow table
pg_dump -t workflow_caseworkflow your_database_name > workflow_backup_$(date +%Y%m%d_%H%M%S).sql
```

Or use the provided SQL script:

```sql
-- Create backup table
CREATE TABLE workflow_caseworkflow_backup AS
SELECT * FROM workflow_caseworkflow
WHERE serialized_workflow_state IS NOT NULL;

-- Verify backup
SELECT COUNT(*) FROM workflow_caseworkflow_backup;
```

### Step 2: Test Migration (Dry Run)

First, test the migration without making changes:

```bash
# Test migration on all workflows
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run

# Test on specific workflows
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run --workflow-ids 123 456 789

# Test only non-completed workflows
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run --exclude-completed

# Test with verbose output
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run --verbose
```

### Step 3: Validate Migration

Validate that workflows can be migrated without actually saving:

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --validate-only
```

This will:
- Check that all v1 workflows can be converted to v3
- Verify the v3 structure is valid
- Test that SpiffWorkflow can deserialize the result
- Not save any changes

### Step 4: Migrate Small Batch

Start with a small batch to ensure everything works:

```bash
# Migrate first 10 workflows
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 1 2 3 4 5 6 7 8 9 10
```

### Step 5: Verify Migrated Workflows

After migrating a batch, verify in Django admin or shell:

```python
from apps.workflow.models import CaseWorkflow

# Check a migrated workflow
workflow = CaseWorkflow.objects.get(id=1)
wf = workflow.get_or_restore_workflow_state()

# Verify it loads correctly
print(f"Workflow loaded: {wf is not None}")
print(f"Tasks: {len(wf.get_tasks())}")

# Check data integrity
if wf.last_task:
    print(f"Data keys: {list(wf.last_task.data.keys())}")
```

### Step 6: Full Migration

Once you're confident, migrate all workflows:

```bash
# Migrate all v1 workflows
python manage.py spiff_migrate_workflows_v1_to_v3

# Or migrate in batches
python manage.py spiff_migrate_workflows_v1_to_v3 --batch-size 50
```

### Step 7: Verify All Workflows

```bash
# Check for any workflows that failed to migrate
python manage.py shell

from apps.workflow.models import CaseWorkflow
from apps.workflow.migration_v1_to_v3 import is_v1_format

# Find any remaining v1 workflows
v1_workflows = [
    wf for wf in CaseWorkflow.objects.exclude(serialized_workflow_state__isnull=True)
    if is_v1_format(wf.serialized_workflow_state)
]

print(f"Remaining v1 workflows: {len(v1_workflows)}")
```

## Command Line Options

### `migrate_workflows_v1_to_v3`

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview changes without saving to database |
| `--workflow-ids ID [ID ...]` | Migrate specific workflow IDs |
| `--exclude-completed` | Skip completed workflows |
| `--workflow-type TYPE` | Only migrate specific workflow type |
| `--batch-size N` | Process N workflows at a time (default: 100) |
| `--verbose` | Show detailed migration statistics |
| `--validate-only` | Only validate without saving |

## Troubleshooting

### Migration Fails for Specific Workflow

1. Check the error message in the output
2. Examine the workflow in Django admin
3. Try migrating just that workflow with verbose output:

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 123 --dry-run --verbose
```

### Data Field Not Unpickled

Some data fields may fail to unpickle if:
- The pickled data was created with a different Python version
- The original class is no longer available

The migration will log warnings but continue. Check logs:

```python
import logging
logging.basicConfig(level=logging.WARNING)
```

### Workflow Won't Deserialize After Migration

This likely means the typename inference was incorrect. Check the task types:

```python
from apps.workflow.migration_v1_to_v3 import migrate_v1_to_v3, get_migration_stats
import json

# Get workflow
workflow = CaseWorkflow.objects.get(id=123)
v1_data = json.dumps(workflow.serialized_workflow_state)

# Migrate and check stats
v3_data = migrate_v1_to_v3(v1_data)
stats = get_migration_stats(v1_data, v3_data)

print(stats['task_type_distribution'])
```

## Rollback

If you need to rollback the migration:

```sql
-- Restore from backup table
UPDATE workflow_caseworkflow wf
SET serialized_workflow_state = backup.serialized_workflow_state
FROM workflow_caseworkflow_backup backup
WHERE wf.id = backup.id;

-- Verify rollback
SELECT COUNT(*) FROM workflow_caseworkflow
WHERE serialized_workflow_state::text LIKE '%task_tree%';
```

Or restore from SQL dump:

```bash
psql your_database_name < workflow_backup_YYYYMMDD_HHMMSS.sql
```

## Migration Statistics

After migration, you can get statistics:

```python
from apps.workflow.models import CaseWorkflow
from apps.workflow.migration_v1_to_v3 import is_v1_format

total = CaseWorkflow.objects.exclude(serialized_workflow_state__isnull=True).count()
v1_count = sum(1 for wf in CaseWorkflow.objects.exclude(serialized_workflow_state__isnull=True)
               if is_v1_format(wf.serialized_workflow_state))
v3_count = total - v1_count

print(f"Total workflows: {total}")
print(f"v1 format: {v1_count}")
print(f"v3 format: {v3_count}")
print(f"Migration progress: {v3_count/total*100:.1f}%")
```

## Handling Subworkflows

Subworkflows are migrated along with their parent workflows. The migration preserves:

- Parent-child relationships
- Data inheritance
- Message passing state

To migrate a parent workflow with all subworkflows:

```bash
# The command automatically handles subworkflows
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids PARENT_ID
```

## Best Practices

1. **Always backup before migration**
2. **Test on staging first**
3. **Start with dry-run**
4. **Migrate in small batches**
5. **Verify each batch before continuing**
6. **Keep backups for at least 2 weeks**
7. **Monitor application logs after migration**

## FAQ

### Q: Will this affect running workflows?

A: The migration only updates the serialized state. Active workflows should continue to work, but it's recommended to:
- Run during low-traffic periods
- Migrate completed workflows first
- Test thoroughly on staging

### Q: Can I migrate back from v3 to v1?

A: No, the migration is one-way. v3 contains additional data that v1 doesn't support. Keep backups if you need to rollback.

### Q: What happens to workflow data?

A: All workflow data is preserved. Pickled fields are unpickled to plain JSON, making them more portable and debuggable.

### Q: How long does migration take?

A: Depends on the number of workflows:
- ~1-2 seconds per workflow for simple workflows
- ~3-5 seconds for complex workflows with many tasks

Estimate: 1000 workflows ≈ 30-60 minutes

### Q: Can I run the migration multiple times?

A: Yes, the migration detects v1 vs v3 format and skips already-migrated workflows.

## Support

If you encounter issues:

1. Check the error logs
2. Review the troubleshooting section
3. Test with `--validate-only` flag
4. Examine specific failing workflows with `--verbose`
5. Check that workflow specs are correctly loaded

## Technical Details

### Data Structure Changes

**v1 Task Structure:**
```json
{
  "id": {"__uuid__": "abc-123"},
  "parent": {"__uuid__": "parent-123"},
  "children": [
    {
      "id": {"__uuid__": "child-456"},
      "children": []
    }
  ],
  "data": {
    "field": {"__bytes__": "base64_pickle_data"}
  }
}
```

**v3 Task Structure:**
```json
{
  "tasks": {
    "abc-123": {
      "id": "abc-123",
      "parent": "parent-123",
      "children": ["child-456"],
      "data": {
        "field": {"value": "actual_value"}
      },
      "typename": "Task"
    },
    "child-456": {
      "id": "child-456",
      "parent": "abc-123",
      "children": [],
      "typename": "ScriptTask"
    }
  }
}
```

### Typename Mapping

The migration infers task typenames based on task_spec names:

- `script_*` → ScriptTask
- `task_*` → UserTask
- `gateway_*` → Task (generic gateway)
- `resume_*` → IntermediateCatchEvent
- `start_*` → StartEvent
- `end_*` → EndEvent

## Version History

- **v1.0** - Initial migration utility
- **v1.1** - Added typename inference
- **v1.2** - Added validation and rollback support
