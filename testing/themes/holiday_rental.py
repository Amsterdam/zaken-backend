from api import (
    API,
    CloseCaseTask,
    CreateCase,
    DebriefUserTask,
    Flow,
    NoMoreTasks,
    ScheduleUserTask,
    UserTask,
    VisitUserTask,
)
from faker import Faker

Theme = 1
DaySegments = {"DAYTIME": 1, "AT_NIGHT": 2}
WeekSegments = {"WEEKDAY": 1, "WEEKEND": 2}
Actions = {"HOUSE_VISIT": 1, "RECHECK": 2}
Priorities = {"HIGH": 1, "NORMAL": 2}
Reasons = {"NOTIFICATION": 1}

Variables = {"next_step": {"RECHECK": "hercontrole", "CLOSE": "sluiten"}}

CaseCloseReasonNames = {
    "DIFFERENT": "Anders, vermeld in toelichting",
    "FORWARDED_TO_ANOTHER_TEAM": "Doorgezet naar ander team",
    "NO_REASON_TO_VISIT_AGAIN": "Geen aanleiding adres opnieuw te bezoeken",
    "NO_FROUD": "Geen woonfraude",
    "NOT_ENOUGH_PROOF": "Onvoldoende bewijs",
    "RESULT_AFTER_RECHECK": "Resultaat na hercontrole",
}
Address = {"bag_id": "234"}

fake = Faker()
profile = fake.profile(fields=["username", "mail", "name"])
author = {
    "id": fake.uuid4(),
    "email": profile["mail"],
    "username": profile["username"],
    "first_name": profile["name"].split(" ")[0],
    "last_name": " ".join(profile["name"].split(" ")[1:]),
    "full_name": profile["name"],
}

case_mock = {
    "theme": Theme,
    "reason": Reasons["NOTIFICATION"],
    "address": Address,
}


def get_flows(api):
    # Fetch some usefull data from API
    CaseCloseReasons = api.call("get", f"/themes/{Theme}/case-close-reasons/")[
        "results"
    ]

    return [
        # Flow(),...
        Flow(
            "Visit happy flow",
            [
                CreateCase(case_mock),
                ScheduleUserTask(
                    "task_create_schedule",
                    action=Actions["HOUSE_VISIT"],
                    week_segment=WeekSegments["WEEKDAY"],
                    day_segment=DaySegments["DAYTIME"],
                    priority=Priorities["HIGH"],
                ),
                VisitUserTask(  # TODO: should be Top-Task?
                    "task_create_visit",
                    authors=[author],
                    start_time="2021-09-14T14:39:19.009Z",
                ),
                DebriefUserTask("task_create_debrief", feedback="Some feedback"),
                UserTask("Activity_0bc2n3t"),  # terugkoppelen melders
                UserTask(  # opstellen verkorte rapportage huisbezoek
                    "Activity_02t4qsu"
                ),
                UserTask(  # uitzetten vervolgstap
                    "Activity_0id7dcf",
                    variables={"next_step": {"value": Variables["next_step"]["CLOSE"]}},
                ),
                CloseCaseTask(
                    "task_close_case",
                    reason=next(
                        r
                        for r in CaseCloseReasons
                        if r["name"] == CaseCloseReasonNames["NO_FROUD"]
                    )["id"],
                    description="Some description",
                ),
                NoMoreTasks(),
            ],
        ),
    ]
