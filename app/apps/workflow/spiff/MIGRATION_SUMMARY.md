# SpiffWorkflow v1 to v3 Migration - Complete Package

This package provides a complete solution for migrating SpiffWorkflow data from v1 to v3 format.

## 📦 What's Included

### Core Migration Module
- **`migration_v1_to_v3.py`** - Core migration logic with sophisticated typename inference

### Management Commands
1. **`migrate_workflows_v1_to_v3.py`** - Main migration command
2. **`backup_workflows.py`** - Create workflow backups
3. **`restore_workflows.py`** - Restore from backups
4. **`workflow_migration_status.py`** - Check migration progress

### Documentation
- **`MIGRATION_V1_TO_V3.md`** - Complete migration guide
- **`MIGRATION_QUICK_START.md`** - Quick start guide
- **`MIGRATION_SUMMARY.md`** - This file

### Tests
- **`tests/test_migration_v1_to_v3.py`** - Comprehensive unit tests (11 test classes, 30+ tests)

## 🎯 Key Features

### ✅ Complete Data Conversion
- ✓ Tree structure → Flat dictionary
- ✓ Unpickle `__bytes__` data → Plain JSON
- ✓ UUID format conversion
- ✓ Typename inference (30+ task type patterns)
- ✓ Metadata injection (correlations, spec, etc.)

### ✅ Safe Migration Process
- ✓ Dry-run mode
- ✓ Validation-only mode
- ✓ Batch processing
- ✓ Automatic rollback on errors
- ✓ Comprehensive logging

### ✅ Backup & Recovery
- ✓ JSON backup export
- ✓ One-command restore
- ✓ Selective backup/restore
- ✓ Backup integrity validation

### ✅ Monitoring & Reporting
- ✓ Migration status dashboard
- ✓ Detailed statistics
- ✓ Progress tracking
- ✓ Error reporting

## 📊 Migration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Migration Flow                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Load v1 Data                                            │
│     └─> Parse JSON                                          │
│     └─> Validate v1 format                                  │
│                                                              │
│  2. Convert Structure                                       │
│     └─> Tree → Flat (recursive)                            │
│     └─> Extract task relationships                         │
│                                                              │
│  3. Transform Data                                          │
│     └─> Unpickle __bytes__ fields                          │
│     └─> Convert UUID objects                                │
│     └─> Infer typenames                                     │
│                                                              │
│  4. Build v3 Structure                                      │
│     └─> Create flat tasks dict                             │
│     └─> Add metadata fields                                 │
│     └─> Set root/last_task refs                            │
│                                                              │
│  5. Validate                                                │
│     └─> Check required fields                              │
│     └─> Validate task references                           │
│     └─> Test deserialization                               │
│                                                              │
│  6. Save (if not dry-run)                                   │
│     └─> Atomic transaction                                  │
│     └─> Update workflow state                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Technical Implementation

### Typename Inference System

The migration uses pattern-based typename inference:

```python
PATTERNS = {
    'script_*': 'ScriptTask',
    'task_*': 'UserTask',
    'gateway_*': 'Task',
    'resume_*': 'IntermediateCatchEvent',
    'message_*': 'IntermediateCatchEvent',
    'start_*': 'StartEvent',
    'end_*': 'EndEvent',
    # ... 30+ patterns total
}
```

### Data Unpickling

Handles Python pickled data stored as base64:

```python
{"__bytes__": "gAWVEQAAAAAAAAB9lIwFdmFsdWWUjAJOb5RzLg=="}
        ↓
{"value": "No"}
```

### Validation Layers

1. **Structure Validation** - Required fields present
2. **Reference Validation** - All task IDs exist
3. **Deserialization Validation** - SpiffWorkflow can load
4. **Data Integrity** - Critical fields preserved

## 📈 Performance Characteristics

| Workflows | Time (est.) | Memory |
|-----------|-------------|--------|
| 10        | ~20 sec     | < 50MB |
| 100       | ~3 min      | < 200MB|
| 1,000     | ~30 min     | < 1GB  |
| 10,000    | ~5 hours    | < 5GB  |

*Use `--batch-size` to control memory usage*

## 🧪 Test Coverage

### Test Categories
- **Unpickling Tests** (4 tests) - Data conversion
- **Typename Inference** (8 tests) - Task type detection
- **UUID Conversion** (3 tests) - ID format changes
- **Tree Conversion** (2 tests) - Structure transformation
- **Format Detection** (3 tests) - Version identification
- **Validation** (3 tests) - v3 structure validation
- **Full Migration** (3 tests) - End-to-end workflow
- **Statistics** (1 test) - Migration reporting
- **Integration** (2 tests) - CaseWorkflow model
- **Edge Cases** (3 tests) - Error handling

**Total: 32 tests across 11 test classes**

## 🔒 Safety Features

### Before Migration
- ✓ Automatic v1 format detection
- ✓ Pre-migration validation
- ✓ Workflow spec verification
- ✓ Dry-run preview

### During Migration
- ✓ Atomic transactions
- ✓ Error isolation (per-workflow)
- ✓ Batch processing
- ✓ Progress tracking

### After Migration
- ✓ Deserialization testing
- ✓ Data integrity checks
- ✓ Automatic rollback on failure
- ✓ Detailed error logging

## 📚 Usage Examples

### Basic Migration
```bash
# Check what needs migration
python manage.py workflow_migration_status

# Create backup
python manage.py backup_workflows

# Test migration
python manage.py spiff_migrate_workflows_v1_to_v3 --dry-run

# Run migration
python manage.py spiff_migrate_workflows_v1_to_v3

# Verify success
python manage.py workflow_migration_status
```

### Advanced Migration
```bash
# Migrate specific workflows
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-ids 1 2 3

# Migrate by type
python manage.py spiff_migrate_workflows_v1_to_v3 --workflow-type director

# Exclude completed
python manage.py spiff_migrate_workflows_v1_to_v3 --exclude-completed

# Custom batch size
python manage.py spiff_migrate_workflows_v1_to_v3 --batch-size 50

# Verbose output
python manage.py spiff_migrate_workflows_v1_to_v3 --verbose
```

### Backup & Restore
```bash
# Create backup
python manage.py backup_workflows --output my_backup.json

# Restore all
python manage.py restore_workflows --input my_backup.json

# Restore specific workflows
python manage.py restore_workflows --input my_backup.json --workflow-ids 1 2 3

# Test restore
python manage.py restore_workflows --input my_backup.json --dry-run
```

## 🎓 How It Works

### Example: Task Tree Conversion

**v1 Input:**
```json
{
  "task_tree": {
    "id": {"__uuid__": "parent"},
    "children": [
      {"id": {"__uuid__": "child-1"}, "children": []},
      {"id": {"__uuid__": "child-2"}, "children": []}
    ]
  }
}
```

**v3 Output:**
```json
{
  "tasks": {
    "parent": {
      "id": "parent",
      "parent": null,
      "children": ["child-1", "child-2"],
      "typename": "Task"
    },
    "child-1": {
      "id": "child-1",
      "parent": "parent",
      "children": [],
      "typename": "ScriptTask"
    },
    "child-2": {
      "id": "child-2",
      "parent": "parent",
      "children": [],
      "typename": "UserTask"
    }
  }
}
```

## 🐛 Common Issues & Solutions

### Issue: Workflow won't deserialize after migration
**Solution:** Check typename inference - may need to add pattern

### Issue: Data field is null after migration
**Solution:** Original pickle data may be corrupted - check logs

### Issue: Migration is slow
**Solution:** Reduce batch size or migrate in smaller chunks

### Issue: Out of memory
**Solution:** Use `--batch-size 10` or smaller

## 📞 Support & Troubleshooting

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Single Workflow
```python
from apps.workflow.migration_v1_to_v3 import migrate_v1_to_v3
import json

# Get workflow
workflow = CaseWorkflow.objects.get(id=123)

# Try migration
v1_data = json.dumps(workflow.serialized_workflow_state)
try:
    v3_data = migrate_v1_to_v3(v1_data)
    print("✓ Migration successful")
except Exception as e:
    print(f"✗ Migration failed: {e}")
```

### View Migration Stats
```python
from apps.workflow.migration_v1_to_v3 import get_migration_stats
stats = get_migration_stats(v1_data, v3_data)
print(json.dumps(stats, indent=2))
```

## 📋 Pre-Migration Checklist

- [ ] Backup database
- [ ] Test on staging environment
- [ ] Run `workflow_migration_status`
- [ ] Create workflow backup with `backup_workflows`
- [ ] Test with `--dry-run`
- [ ] Validate with `--validate-only`
- [ ] Review error logs
- [ ] Plan maintenance window
- [ ] Notify team

## ✅ Post-Migration Checklist

- [ ] Run `workflow_migration_status` (should show 100% v3)
- [ ] Test workflow loading in application
- [ ] Verify user tasks still work
- [ ] Check workflow execution
- [ ] Monitor error logs
- [ ] Keep backup for 2 weeks
- [ ] Document any issues
- [ ] Update team

## 🎉 Success Criteria

Migration is successful when:
1. ✅ `workflow_migration_status` shows 100% v3 format
2. ✅ Workflows load without errors
3. ✅ User tasks are accessible
4. ✅ Workflow execution works normally
5. ✅ No data loss detected
6. ✅ Application functions normally

## 📝 Version History

- **v1.0.0** (2025-10-01) - Initial release
  - Core migration utilities
  - Management commands
  - Comprehensive tests
  - Full documentation

## 🤝 Contributing

When adding new task type patterns:
1. Add to `TASK_SPEC_TO_TYPENAME_MAP` in `migration_v1_to_v3.py`
2. Add test case to `TypenameInferenceTests`
3. Update documentation

## 📄 License

Same as parent project.

## 🙏 Credits

Created to facilitate SpiffWorkflow v1 → v3 upgrade for the zaken-backend project.

---

**Questions?** See [MIGRATION_V1_TO_V3.md](MIGRATION_V1_TO_V3.md) for detailed documentation.

**Quick Start?** See [MIGRATION_QUICK_START.md](MIGRATION_QUICK_START.md) for fast migration guide.
