# Jump to a subworkflow (`jump_to`)

A new case normally starts at the beginning of the director (`director.bpmn`). With
`jump_to`, a new case starts at the **first task of a chosen subworkflow** instead,
e.g. straight to "Opstellen concept aanschrijving" (summon). This is the building block
for bulk creating cases (Excel upload) that should skip the first steps.

## Usage

Add `jump_to` when creating a case:

```
POST /api/v1/cases/
{
  "bag_id": "0363010000874274",
  "theme_id": 3,
  "reason_id": 32,
  "description": "...",
  "jump_to": "summon"
}
```

Or in Python, e.g. per row of a bulk import:

```python
serializer = CaseCreateSerializer(data={..., "jump_to": "summon"}, context=...)
serializer.is_valid(raise_exception=True)
serializer.save()

# or without the serializer
Case.objects.create(..., initial_workflow_data={"jump_to": "summon"})
```

- `jump_to` is optional. Without it nothing changes.
- A value that is not an allowed target gives a validation error (400).
- A target that belongs to other themes (see `themes` below) gives a validation error
  (400) too, when creating a case and when importing cases in bulk.
- `jump_to` is ignored on update; it only applies when a case is created.
- The allowed targets (`value`, `label` and `themes`, e.g. for a select) are returned
  by `apps.workflow.jump_to.get_jump_to_targets()` and by
  `GET /cases/allowed-jump-workflows/`.

## Allowed targets

Defined in `JUMP_TO_TARGETS` in `app/apps/workflow/jump_to.py`, the only place to add
or remove a target.

| Target | Label | Themes | Director routing data |
|---|---|---|---|
| `summon` | Aanschrijving | all | `debrief_next_step=summon` |
| `unoccupied` | Leegstandsmelding | Leegstand | `debrief_next_step=unoccupied` |
| `debrief` | Debrief | all | none (default path) |

`themes` limits a target to the themes (names) it belongs to; `None` is every theme.

Tested for Kamerverhuur, Leegstand, Onderhuur and reason Digitaal toezicht: the
theme specific first steps (housing_corporation, digital_surveillance) are skipped
along with visit and debrief, the routing data is the same for every theme.

### Not allowed, and why

A target must be able to start without data or objects from earlier steps.

| Subworkflow | Reason |
|---|---|
| `decision`, `renounce_decision` | Needs a summon: the decision is linked to it via `summon_id` (persons, names). Without one the decision is saved without persons. |
| `closing_procedure` | Follows a summon of type "sluiting". |
| `close_case` | Closing a case is a different use case. Uses `decision_count`/`next_step` collected from the summons. |
| `visit`, `housing_corporation`, `omzettingsvergunning`, `digital_surveillance` | Already the first step of the director (for a theme / reason / project), no jump needed. For digital surveillance create the case with reason "Digitaal toezicht". |

### Adding a target

1. Find in `director.bpmn` the gateway values (`*_next_step`) that lead to
   `start_subworkflow("<target>")` and add them as `routing_data`. Never add form data
   of a subworkflow: the subworkflow must start at its first task.
2. Check that the first task of the target doesn't depend on earlier steps.
3. Set `themes` when the target only makes sense for some themes (e.g. `unoccupied`
   for Leegstand), else `None`.
4. Add the target and its first task to `FIRST_TASKS` in
   `app/apps/workflow/tests/test_jump_to.py`.

## How it works

```
POST /cases/ {jump_to}          CaseCreateSerializer: validates jump_to
        │                        -> Case(initial_workflow_data={"jump_to": ...})
        ▼
start_workflow_for_case          signal: passes initial_workflow_data once
        ▼
director CaseWorkflow.start()    pops jump_to, adds the routing data and
        │                        fast-forwards (ff_to_subworkflow) to
        │                        start_subworkflow("<target>"); the skipped
        │                        steps are completed without side effects
        ▼
<target> CaseWorkflow.start()    starts normally at its first task with the
                                 real script engine (set_status, timers) and
                                 creates the timeline event
```

- The director waits for `resume_after_<target>` and continues as usual afterwards.
- `jump_to` and the one-off marker `jumped_to_subworkflow` are never kept in the
  workflow data.
- Timeline: a `GENERIC_TASK` event "Doorgezet via bulk", with "Doorgezet naar: <first
  task>", authored by the case author (no event when the case has no author).
- If jumping fails anyway (e.g. after a BPMN change) an error is logged and the
  director starts at the beginning. The tests per target guard against this.

## Bulk import (Excel upload)

`POST /cases/process-file/` creates a case per row of an Excel file, with one
`jump_to` for the whole upload (`app/utils/bulk_case_importer.py`):

- With `dry_run=true` (the default) it only checks the rows and returns the result
  per row. It needs only the theme.
- With `dry_run=false` it needs what creating one case needs (the reason, a project for
  the reason "Project", a `jump_to` of the theme) and creates the cases in a Celery
  task. Reasons that ask for something of one case (MMA, SIG melding, Digitaal
  toezicht) cannot be used.
- `GET /cases/process-file/<task_id>/status/` gives the state and the result of that
  task, for 24 hours and only to the user who started it.
