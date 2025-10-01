# SpiffWorkflow v1 to v3 Migration - Quick Start

## 🚀 Quick Migration Guide (5 Steps)

### 1️⃣ Check Current Status

```bash
python manage.py workflow_migration_status
```

This shows how many workflows need migration.

### 2️⃣ Create Backup

```bash
python manage.py backup_workflows
```

This creates `workflow_backup_YYYYMMDD_HHMMSS.json` in your current directory.

### 3️⃣ Test Migration (Dry Run)

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run
```

This previews the migration without making changes.

### 4️⃣ Run Migration

```bash
python manage.py spiff_migrate_workflows_v1_to_v3
```

This performs the actual migration.

### 5️⃣ Verify Success

```bash
python manage.py spiff_workflow_migration_status
```

Should show 100% v3 format.

## 🆘 If Something Goes Wrong

### Restore from Backup

```bash
python manage.py restore_workflows --input workflow_backup_YYYYMMDD_HHMMSS.json
```

## 📊 Common Use Cases

### Migrate Only Active Workflows

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --exclude-completed
```

### Migrate Specific Workflows

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 123 456 789
```

### Migrate by Type

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-type director
```

### Validate Without Saving

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --validate-only
```

## 🔍 Check Migration Details

### Verbose Output

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run --verbose
```

### Detailed Status

```bash
python manage.py workflow_migration_status --detailed
```

## ⚡ Best Practices

1. **Always backup first** - Use `backup_workflows` command
2. **Test on staging** - Run the full process on staging environment
3. **Start small** - Migrate a few workflows first with `--workflow-ids`
4. **Use dry-run** - Always preview with `--dry-run` first
5. **Check status** - Use `workflow_migration_status` before and after
6. **Keep backups** - Don't delete backup files for at least 2 weeks

## 🐛 Troubleshooting

### Check Logs

```python
# In Django shell
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run migration
```

### Test Single Workflow

```bash
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 123 --dry-run --verbose
```

### Verify Workflow Loads

```python
# In Django shell
from apps.workflow.models import CaseWorkflow

workflow = CaseWorkflow.objects.get(id=123)
wf = workflow.get_or_restore_workflow_state()
print(f"Loaded: {wf is not None}")
```

## 📝 Full Documentation

See [MIGRATION_V1_TO_V3.md](MIGRATION_V1_TO_V3.md) for complete documentation.

## 🎯 Example Migration Session

```bash
# 1. Check status
$ python manage.py workflow_migration_status
Found 150 workflows (120 v1, 30 v3)

# 2. Backup
$ python manage.py backup_workflows
✓ Backup completed! File: workflow_backup_20250101_120000.json

# 3. Test first 10
$ python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 1 2 3 4 5 6 7 8 9 10 --dry-run
✓ 10/10 workflows can be migrated

# 4. Migrate first 10
$ python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 1 2 3 4 5 6 7 8 9 10
✓ Migration complete: 10 succeeded, 0 failed

# 5. Verify
$ python manage.py workflow_migration_status
Found 150 workflows (110 v1, 40 v3)

# 6. Migrate all remaining
$ python manage.py spiff_migrate_workflows_v1_to_v3
✓ Migration complete: 110 succeeded, 0 failed

# 7. Final check
$ python manage.py workflow_migration_status
Found 150 workflows (0 v1, 150 v3)
✓ All workflows are in v3 format!
```

## ⏱️ Estimated Time

- Small (< 100 workflows): 5-10 minutes
- Medium (100-1000 workflows): 30-60 minutes
- Large (> 1000 workflows): 1-3 hours

Use `--batch-size` to control memory usage for large migrations.
