class Event:
    pass


class CaseEvent(Event):
    """
    The CaseEvent is not bound to a User task because creating a case is not
    a user task in our workflow engine.
    """

    type = "CASE"


class CitizenReportEvent(Event):
    """
    CitizenReport event is only added to the timeline when a citizen report
    (description_citizenreport) is added to the create-case endpoint.
    """

    type = "CITIZEN_REPORT"


class DebriefingEvent(Event):
    type = "DEBRIEFING"


class VisitEvent(Event):
    type = "VISIT"


class CloseEvent(Event):
    type = "CASE_CLOSE"


class SummonEvent(Event):
    type = "SUMMON"


class DecisionEvent(Event):
    type = "DECISION"


class ScheduleEvent(Event):
    type = "SCHEDULE"


class GenericTaskEvent(Event):
    type = "GENERIC_TASK"
