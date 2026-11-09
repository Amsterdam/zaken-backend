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
- `jump_to` is ignored on update; it only applies when a case is created.
- The allowed targets (value + label, e.g. for a select) are returned by
  `apps.workflow.jump_to.get_jump_to_targets()`.

## Allowed targets

Defined in `JUMP_TO_TARGETS` in `app/apps/workflow/jump_to.py`, the only place to add
or remove a target.

| Target | Label | First task | Director routing data |
|---|---|---|---|
| `summon` | Aanschrijving | Opstellen concept aanschrijving | `debrief_next_step=summon` |
| `unoccupied` | Leegstand | Opstellen aanschrijving eigenaar | `debrief_next_step=unoccupied` |
| `debrief` | Debrief | Verwerken debrief | none (default path) |

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
3. Add the target and its first task to `FIRST_TASKS` in
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

Not part of this feature. Points for whoever builds it:

- Create each case through `CaseCreateSerializer` (or `Case.objects.create(...,
  initial_workflow_data=...)`) and pass `jump_to`; one value for the whole upload.
- Validate first and show a preview (invalid `bag_id`, duplicates) before creating.
- Create the cases asynchronously (Celery): each case does a BAG lookup and starts a
  workflow, a large upload doesn't fit in one request.
- Consider a separate permission for bulk creating.
- An endpoint with the allowed targets is a thin wrapper around
  `get_jump_to_targets()`, e.g. `GET /cases/jump-to-targets/`.
