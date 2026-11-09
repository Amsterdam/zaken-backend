"""
Jump a new case to the start of a subworkflow ("doorzetten").

A case created with `jump_to` does not start at the beginning of the director, but the
director is fast-forwarded until it starts the chosen subworkflow. That subworkflow then
starts normally at its first task, with only its configured initial data. The director
waits for `resume_after_<subworkflow>` and continues as usual afterwards.

Only subworkflows listed in JUMP_TO_TARGETS are allowed. A target needs no data from
earlier steps; e.g. `decision` is excluded because it depends on a summon (summon_id).
See docs/jump_to.md.
"""

import copy

JUMP_TO_KEY = "jump_to"

# One-off marker passed by the director to the subworkflow it started via jump_to.
JUMPED_TO_SUBWORKFLOW_KEY = "jumped_to_subworkflow"

# Timeline event created when the jumped-to subworkflow has started.
JUMP_EVENT_TASK_NAME = "bulk_jump_to"
JUMP_EVENT_DESCRIPTION = "Doorgezet via bulk"
JUMP_EVENT_LABEL = "Doorgezet naar"

# Allowed targets. `routing_data` holds only the director gateway values (*_next_step)
# needed to reach start_subworkflow("<target>"), never form data of subworkflows.
JUMP_TO_TARGETS = {
    "summon": {
        "label": "Aanschrijving",
        "routing_data": {"debrief_next_step": {"value": "summon"}},
    },
    "unoccupied": {
        "label": "Leegstand",
        "routing_data": {"debrief_next_step": {"value": "unoccupied"}},
    },
    "debrief": {
        "label": "Debrief",
        # Default director path: visit -> debrief
        "routing_data": {},
    },
}


def get_jump_to_targets():
    """Allowed targets, e.g. for a choice field or a select in the frontend."""
    return [
        {"value": name, "label": target["label"]}
        for name, target in JUMP_TO_TARGETS.items()
    ]


def is_jump_to_target(name):
    return name in JUMP_TO_TARGETS


def get_jump_to_routing_data(name):
    return copy.deepcopy(JUMP_TO_TARGETS[name]["routing_data"])
