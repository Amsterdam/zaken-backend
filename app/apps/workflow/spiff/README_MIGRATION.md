# 🔄 SpiffWorkflow v1 → v3 Migration Package

Complete migration solution for upgrading SpiffWorkflow serialized data from v1 to v3 format.

## 📁 Files Created

```
app/apps/workflow/
├── migration_v1_to_v3.py                    # Core migration utilities
├── management/commands/
│   ├── spiff_migrate_workflows_v1_to_v3.py        # Main migration command
│   ├── backup_workflows.py                   # Backup command
│   ├── restore_workflows.py                  # Restore command
│   └── workflow_migration_status.py          # Status checker
├── tests/
│   └── test_migration_v1_to_v3.py           # Comprehensive tests (32 tests)
└── docs/
    ├── MIGRATION_QUICK_START.md             # Quick start guide
    ├── MIGRATION_V1_TO_V3.md                # Complete guide
    ├── MIGRATION_SUMMARY.md                  # Technical summary
    └── README_MIGRATION.md                   # This file
```

## 🚀 Quick Start (30 seconds)

```bash
# 1. Check status
python manage.py workflow_migration_status

# 2. Backup
python manage.py backup_workflows

# 3. Test
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run

# 4. Migrate
python manage.py spiff_migrate_workflows_v1_to_v3

# 5. Verify
python manage.py workflow_migration_status
```

## 📖 Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [MIGRATION_QUICK_START.md](MIGRATION_QUICK_START.md) | Fast migration guide | Start here! |
| [MIGRATION_V1_TO_V3.md](MIGRATION_V1_TO_V3.md) | Complete documentation | For detailed info |
| [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) | Technical details | For developers |

## 🎯 What Does It Do?

### Converts v1 Format:
```json
{
  "data": {},
  "task_tree": {
    "id": {"__uuid__": "abc-123"},
    "children": [...],
    "data": {"field": {"__bytes__": "pickled_data"}}
  },
  "last_task": {"__uuid__": "xyz-789"}
}
```

### To v3 Format:
```json
{
  "data": {},
  "tasks": {
    "abc-123": {
      "id": "abc-123",
      "parent": null,
      "children": ["child-1", "child-2"],
      "data": {"field": "actual_value"},
      "typename": "Task"
    }
  },
  "last_task": "xyz-789",
  "typename": "BpmnWorkflow",
  "correlations": {},
  "spec": {...}
}
```

## ✨ Key Features

- ✅ **Automatic Detection** - Identifies v1 vs v3 format
- ✅ **Data Unpickling** - Converts `__bytes__` to plain JSON
- ✅ **Type Inference** - Infers 30+ task typenames
- ✅ **Safe Migration** - Dry-run, validation, atomic transactions
- ✅ **Backup/Restore** - One-command backup and rollback
- ✅ **Progress Tracking** - Visual progress bars and statistics
- ✅ **Comprehensive Tests** - 32 unit tests
- ✅ **Full Documentation** - 3 detailed guides

## 🧪 Running Tests

```bash
# Run all migration tests
python manage.py test apps.workflow.tests.test_migration_v1_to_v3

# Run specific test class
python manage.py test apps.workflow.tests.test_migration_v1_to_v3.FullMigrationTests

# Run with verbose output
python manage.py test apps.workflow.tests.test_migration_v1_to_v3 --verbosity=2
```

## 📊 Migration Commands

### Check Status
```bash
python manage.py workflow_migration_status
python manage.py workflow_migration_status --detailed
```

### Backup Workflows
```bash
python manage.py backup_workflows
python manage.py backup_workflows --output my_backup.json
python manage.py backup_workflows --exclude-completed
```

### Migrate Workflows
```bash
# Dry run
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run

# Validate only
python manage.py spiff_migrate_workflows_v1_to_v3 --validate-only

# Migrate all
python manage.py spiff_migrate_workflows_v1_to_v3

# Migrate specific
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 1 2 3

# Migrate by type
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-type director

# Exclude completed
python manage.py spiff_migrate_workflows_v1_to_v3 --exclude-completed

# Verbose output
python manage.py spiff_migrate_workflows_v1_to_v3 --verbose

# Custom batch size
python manage.py spiff_migrate_workflows_v1_to_v3 --batch-size 50
```

### Restore Workflows
```bash
python manage.py restore_workflows --input workflow_backup_20250101_120000.json
python manage.py restore_workflows --input backup.json --dry-run
python manage.py restore_workflows --input backup.json --workflow-ids 1 2 3
```

## 🔧 Programmatic Usage

### Check Format
```python
from apps.workflow.migration_v1_to_v3 import is_v1_format

workflow = CaseWorkflow.objects.get(id=123)
if is_v1_format(workflow.serialized_workflow_state):
    print("Needs migration")
```

### Migrate Single Workflow
```python
from apps.workflow.migration_v1_to_v3 import migrate_v1_to_v3
import json

workflow = CaseWorkflow.objects.get(id=123)
v1_data = json.dumps(workflow.serialized_workflow_state)
v3_data = migrate_v1_to_v3(v1_data)

# Save
workflow.serialized_workflow_state = json.loads(v3_data)
workflow.save()
```

### Get Statistics
```python
from apps.workflow.migration_v1_to_v3 import get_migration_stats

stats = get_migration_stats(v1_data, v3_data)
print(f"Tasks: {stats['v3_task_count']}")
print(f"Unpickled fields: {stats['unpickled_fields']}")
print(f"Task types: {stats['task_type_distribution']}")
```

## ⚠️ Important Notes

1. **Always backup** before migrating
2. **Test on staging** before production
3. **Use dry-run** first
4. **Migration is one-way** - v3 cannot convert back to v1
5. **Keep backups** for at least 2 weeks

## 🐛 Troubleshooting

### Issue: Migration fails for specific workflow
```bash
# Get detailed error
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 123 --dry-run --verbose
```

### Issue: Workflow won't load after migration
```python
# Check if it can be deserialized
workflow = CaseWorkflow.objects.get(id=123)
wf = workflow.get_or_restore_workflow_state()
print(f"Loaded: {wf is not None}")
```

### Issue: Need to rollback
```bash
# Restore from backup
python manage.py restore_workflows --input workflow_backup_TIMESTAMP.json
```

## 📈 Performance

| Workflows | Estimated Time |
|-----------|----------------|
| 10        | ~20 seconds    |
| 100       | ~3 minutes     |
| 1,000     | ~30 minutes    |
| 10,000    | ~5 hours       |

## 🎓 How It Works

1. **Detection** - Identifies v1 format (has `task_tree`)
2. **Conversion** - Transforms tree to flat structure
3. **Unpickling** - Decodes `__bytes__` fields
4. **Type Inference** - Assigns task typenames
5. **Validation** - Verifies v3 structure
6. **Deserialization** - Tests with SpiffWorkflow
7. **Save** - Atomic database update

## 📞 Support

- **Quick Start**: [MIGRATION_QUICK_START.md](MIGRATION_QUICK_START.md)
- **Full Guide**: [MIGRATION_V1_TO_V3.md](MIGRATION_V1_TO_V3.md)
- **Technical Details**: [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)

## ✅ Migration Checklist

### Before Migration
- [ ] Backup database
- [ ] Test on staging
- [ ] Run `workflow_migration_status`
- [ ] Run `backup_workflows`
- [ ] Test with `--dry-run`
- [ ] Run `--validate-only`

### During Migration
- [ ] Run migration command
- [ ] Monitor for errors
- [ ] Check logs

### After Migration
- [ ] Verify with `workflow_migration_status`
- [ ] Test workflow loading
- [ ] Test workflow execution
- [ ] Monitor application
- [ ] Keep backups

## 🎉 Success!

Migration is complete when:
- ✅ Status shows 100% v3 format
- ✅ Workflows load without errors
- ✅ Application functions normally

---

**Ready to migrate?** Start with [MIGRATION_QUICK_START.md](MIGRATION_QUICK_START.md)!
